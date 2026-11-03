"""Frontière Application M0 : Commands/Queries avec autorisation explicite."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Callable
from uuid import UUID, uuid4

from .domain import (
    AccessDenied, Conflict, Dependency, DependencyViolation, DomainEvent, InvalidStateTransition,
    Milestone, MilestoneId, NotFound, Project, ProjectId, ProjectStatus, Task, TaskId, TaskStatus,
)
from .ports import ActorContext, AuthorizationPolicy, Clock, IdFactory, UnitOfWork


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FixedClock:
    def __init__(self, value: datetime):
        self.value = value

    def now(self) -> datetime:
        return self.value


class UUIDFactory:
    def new(self) -> UUID:
        return uuid4()


class ExplicitPolicy:
    """Policy d'exemple ; ne pas prendre l'ActorContext d'un payload client non vérifié."""
    def __init__(self, grants: dict[str, set[str]]):
        self._grants = grants

    def require(self, actor: ActorContext, permission: str) -> None:
        if not actor.actor_id or not actor.scope or permission not in self._grants.get(actor.actor_id, set()):
            raise AccessDenied("Action non autorisée")


class ProjectService:
    def __init__(
        self, uow_factory: Callable[[], UnitOfWork], policy: AuthorizationPolicy,
        clock: Clock | None = None, ids: IdFactory | None = None,
    ):
        self._uow = uow_factory
        self._policy = policy
        self._clock = clock or SystemClock()
        self._ids = ids or UUIDFactory()

    def _event(self, name: str, entity_id: object, actor: ActorContext) -> DomainEvent:
        return DomainEvent(name, str(getattr(entity_id, "value", entity_id)), self._clock.now(), actor.actor_id)

    def _project(self, uow: UnitOfWork, project_id: ProjectId, actor: ActorContext, permission: str) -> Project:
        self._policy.require(actor, permission)
        obj = uow.projects.get(project_id)
        if obj is None or obj.scope != actor.scope:
            raise NotFound("Ressource indisponible")
        return obj

    def _task(self, uow: UnitOfWork, task_id: TaskId, actor: ActorContext, permission: str) -> Task:
        self._policy.require(actor, permission)
        item = uow.tasks.get(task_id)
        if item is None:
            raise NotFound("Ressource indisponible")
        self._project(uow, item.project_id, actor, "PROJECT_VIEW")
        return item

    def create_project(self, actor: ActorContext, name: str, owner_id: str) -> ProjectId:
        self._policy.require(actor, "PROJECT_CREATE")
        with self._uow() as uow:
            project = Project(ProjectId(self._ids.new()), name, owner_id, actor.scope)
            uow.projects.add(project)
            uow.record(self._event("ProjectCreated", project.id, actor))
            uow.commit()
            return project.id

    def get_project(self, actor: ActorContext, project_id: ProjectId) -> Project:
        with self._uow() as uow:
            return self._project(uow, project_id, actor, "PROJECT_VIEW")

    def list_projects(self, actor: ActorContext) -> list[Project]:
        self._policy.require(actor, "PROJECT_VIEW")
        with self._uow() as uow:
            return [p for p in uow.projects.list_all() if p.scope == actor.scope]

    def transition_project(self, actor: ActorContext, project_id: ProjectId, target: ProjectStatus) -> None:
        permission = {
            ProjectStatus.PLANNED: "PROJECT_PLAN", ProjectStatus.ACTIVE: "PROJECT_START",
            ProjectStatus.ON_HOLD: "PROJECT_EDIT", ProjectStatus.COMPLETED: "PROJECT_COMPLETE",
            ProjectStatus.CANCELLED: "PROJECT_CANCEL",
        }[target]
        names = {
            ProjectStatus.PLANNED: "ProjectPlanned", ProjectStatus.ON_HOLD: "ProjectPutOnHold",
            ProjectStatus.COMPLETED: "ProjectCompleted", ProjectStatus.CANCELLED: "ProjectCancelled",
        }
        with self._uow() as uow:
            project = self._project(uow, project_id, actor, permission)
            previous = project.status
            if target is ProjectStatus.COMPLETED:
                self._policy.require(actor, "PROJECT_VIEW")
                if any(t.project_id == project_id and t.status not in (TaskStatus.DONE, TaskStatus.CANCELLED) for t in uow.tasks.list_all()):
                    raise InvalidStateTransition("Clôture refusée : tâches ouvertes")
            project.transition(target, self._clock.now())
            uow.projects.save(project, expected_version=project.version)
            name = "ProjectResumed" if previous is ProjectStatus.ON_HOLD and target is ProjectStatus.ACTIVE else ("ProjectStarted" if target is ProjectStatus.ACTIVE else names[target])
            uow.record(self._event(name, project.id, actor))
            uow.commit()

    def add_milestone(self, actor: ActorContext, project_id: ProjectId, name: str, target_date: date) -> MilestoneId:
        with self._uow() as uow:
            project = self._project(uow, project_id, actor, "MILESTONE_CREATE")
            mid = MilestoneId(self._ids.new())
            project.add_milestone(Milestone(mid, name, target_date))
            uow.projects.save(project, expected_version=project.version)
            uow.record(self._event("MilestoneCreated", mid, actor))
            uow.commit()
            return mid

    def reach_milestone(self, actor: ActorContext, project_id: ProjectId, milestone_id: MilestoneId) -> None:
        with self._uow() as uow:
            project = self._project(uow, project_id, actor, "MILESTONE_EDIT")
            if milestone_id not in project.milestones:
                raise NotFound("Ressource indisponible")
            project.milestones[milestone_id].reach(self._clock.now())
            uow.projects.save(project, expected_version=project.version)
            uow.record(self._event("MilestoneReached", milestone_id, actor))
            uow.commit()

    def create_task(self, actor: ActorContext, project_id: ProjectId, title: str) -> TaskId:
        with self._uow() as uow:
            parent = self._project(uow, project_id, actor, "PROJECT_VIEW")
            self._policy.require(actor, "TASK_CREATE")
            if parent.status in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED):
                raise InvalidStateTransition("Projet terminal")
            task = Task(TaskId(self._ids.new()), project_id, title)
            uow.projects.save(parent, expected_version=parent.version)  # Serialize task creation with project closure.
            uow.tasks.add(task)
            uow.record(self._event("TaskCreated", task.id, actor))
            uow.commit()
            return task.id

    def get_task(self, actor: ActorContext, task_id: TaskId) -> Task:
        with self._uow() as uow:
            return self._task(uow, task_id, actor, "TASK_VIEW")

    def list_tasks(self, actor: ActorContext, project_id: ProjectId) -> list[Task]:
        with self._uow() as uow:
            self._project(uow, project_id, actor, "PROJECT_VIEW")
            self._policy.require(actor, "TASK_VIEW")
            return [t for t in uow.tasks.list_all() if t.project_id == project_id]

    def assign_task(self, actor: ActorContext, task_id: TaskId, assignee_id: str) -> None:
        with self._uow() as uow:
            task = self._task(uow, task_id, actor, "TASK_ASSIGN")
            if task.status in (TaskStatus.DONE, TaskStatus.CANCELLED):
                raise InvalidStateTransition("Tâche terminale")
            if not assignee_id.strip():
                raise Conflict("Assignee invalide")
            task.assignee_id = assignee_id
            uow.tasks.save(task, expected_version=task.version)
            uow.record(self._event("TaskAssigned", task.id, actor))
            uow.commit()

    def transition_task(self, actor: ActorContext, task_id: TaskId, target: TaskStatus, *, reason: str | None = None) -> None:
        perm = {
            TaskStatus.READY: "TASK_EDIT", TaskStatus.IN_PROGRESS: "TASK_START",
            TaskStatus.BLOCKED: "TASK_EDIT", TaskStatus.IN_REVIEW: "TASK_EDIT",
            TaskStatus.DONE: "TASK_COMPLETE", TaskStatus.CANCELLED: "TASK_EDIT",
        }[target]
        names = {
            TaskStatus.READY: "TaskMarkedReady", TaskStatus.IN_PROGRESS: "TaskStarted",
            TaskStatus.BLOCKED: "TaskBlocked", TaskStatus.IN_REVIEW: "TaskSubmittedForReview",
            TaskStatus.DONE: "TaskCompleted", TaskStatus.CANCELLED: "TaskCancelled",
        }
        with self._uow() as uow:
            task = self._task(uow, task_id, actor, perm)
            if target is TaskStatus.IN_PROGRESS:
                project = self._project(uow, task.project_id, actor, "PROJECT_VIEW")
                if project.status is not ProjectStatus.ACTIVE:
                    raise InvalidStateTransition("Projet non actif")
                _, edges = uow.dependencies.snapshot(task.project_id)
                for edge in edges:
                    if edge.successor == task.id:
                        predecessor = uow.tasks.get(edge.predecessor)
                        if predecessor is None or predecessor.status is not TaskStatus.DONE:
                            raise DependencyViolation("Prérequis non terminé")
            old = task.status
            task.transition(target, self._clock.now(), reason=reason)
            uow.tasks.save(task, expected_version=task.version)
            name = "TaskUnblocked" if old is TaskStatus.BLOCKED and target is TaskStatus.IN_PROGRESS else names[target]
            uow.record(self._event(name, task.id, actor))
            uow.commit()

    def add_dependency(self, actor: ActorContext, successor: TaskId, predecessor: TaskId) -> None:
        with self._uow() as uow:
            child = self._task(uow, successor, actor, "TASK_EDIT")
            parent = self._task(uow, predecessor, actor, "TASK_EDIT")
            if child.project_id != parent.project_id:
                raise DependencyViolation("Dépendance entre projets interdite")
            project = self._project(uow, child.project_id, actor, "PROJECT_VIEW")
            if project.status in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED):
                raise InvalidStateTransition("Projet terminal")
            version, edges = uow.dependencies.snapshot(child.project_id)
            edge = Dependency(successor, predecessor)
            if edge in edges:
                raise Conflict("Dépendance déjà présente")
            edges.add(edge)
            uow.dependencies.replace_if_version(child.project_id, expected_version=version, edges=edges)
            uow.record(self._event("TaskDependencyAdded", successor, actor))
            uow.commit()