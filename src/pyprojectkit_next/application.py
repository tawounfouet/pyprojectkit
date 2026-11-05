"""Use cases M0 bornés du VS-REBOOT-01, indépendant de M1/M2."""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from .domain import (
    AccessDenied, ClosureBlocked, Dependency, DependencyViolation, DomainEvent,
    InvalidStateTransition, InvalidValue, Milestone, MilestoneId, NotFound,
    Project, ProjectId, ProjectStatus, Task, TaskId, TaskStatus,
)
from .ports import ActorContext, AuthorizationPolicy, Clock, IdFactory, UnitOfWork, UnitOfWorkFactory


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class UUIDFactory:
    def project_id(self) -> ProjectId:
        return ProjectId(str(uuid4()))

    def task_id(self) -> TaskId:
        return TaskId(str(uuid4()))

    def milestone_id(self) -> MilestoneId:
        return MilestoneId(str(uuid4()))


class OwnerScopePolicy:
    """Policy minimale fail-closed : actor fourni par hôte fiable uniquement."""
    _actions = frozenset({"project:create", "project:read", "project:write",
                          "task:read", "task:write", "milestone:read", "milestone:write"})

    def require(self, actor: ActorContext, action: str, *, scope: str, owner_id: str) -> None:
        if (action not in self._actions or not actor.subject_id or
                not actor.allowed_scopes or owner_id != actor.subject_id or
                scope not in actor.allowed_scopes):
            raise AccessDenied("accès refusé")


class ProjectService:
    def __init__(self, uow_factory: UnitOfWorkFactory, *, clock: Clock,
                 ids: IdFactory, authorization: AuthorizationPolicy) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._ids = ids
        self._auth = authorization

    def _event(self, name: str, id: str, version: int, actor: ActorContext) -> DomainEvent:
        return DomainEvent(name, id, version, actor.subject_id, self._clock.now())

    def _project(self, uow: UnitOfWork, actor: ActorContext, id: ProjectId,
                 action: str = "project:write") -> Project:
        """Masquer uniformément l'existence des projets absents ou invisibles.

        Cette frontière applicative n'authentifie pas l'acteur : le host doit
        construire ActorContext à partir d'une identité vérifiée.
        """
        try:
            project = uow.get_project(id)
            self._auth.require(actor, action, scope=project.scope, owner_id=project.owner_id)
            return project
        except (NotFound, AccessDenied):
            raise NotFound("ressource indisponible") from None

    def _task(self, uow: UnitOfWork, actor: ActorContext, id: TaskId,
              action: str) -> Task:
        """Résoudre une tâche sans exposer si son parent est absent ou caché."""
        try:
            task = uow.get_task(id)
            self._project(uow, actor, task.project_id, action)
            return task
        except NotFound:
            raise NotFound("ressource indisponible") from None

    def create_project(self, actor: ActorContext, name: str, scope: str) -> Project:
        self._auth.require(actor, "project:create", scope=scope, owner_id=actor.subject_id)
        project = Project(self._ids.project_id(), name, actor.subject_id, scope)
        with self._uow_factory() as uow:
            uow.add_project(project)
            uow.record(self._event("ProjectCreated", project.id.value, project.version, actor))
            uow.commit()
        return project

    def get_project(self, actor: ActorContext, id: ProjectId) -> Project:
        with self._uow_factory() as uow:
            return self._project(uow, actor, id, "project:read")

    def list_projects(self, actor: ActorContext) -> tuple[Project, ...]:
        """Lecture fail-closed : ne révèle jamais les projets hors owner/scope."""
        if not actor.subject_id or not actor.allowed_scopes:
            raise AccessDenied("acteur non authentifié ou scope absent")
        with self._uow_factory() as uow:
            visible = []
            for project in uow.list_projects():
                if project.owner_id == actor.subject_id and project.scope in actor.allowed_scopes:
                    self._auth.require(actor, "project:read", scope=project.scope,
                                       owner_id=project.owner_id)
                    visible.append(project)
            return tuple(sorted(visible, key=lambda project: project.id.value))

    def _change_project(self, actor: ActorContext, id: ProjectId, command: str) -> Project:
        with self._uow_factory() as uow:
            project = self._project(uow, actor, id)
            if command == "plan":
                updated = project.plan()
            elif command == "start":
                updated = project.start(self._clock.now())
            elif command == "pause":
                updated = project.pause()
            elif command == "resume":
                updated = project.resume()
            elif command == "complete":
                outstanding = [t for t in uow.list_tasks(id)
                               if t.status not in {TaskStatus.DONE, TaskStatus.CANCELLED}]
                if outstanding:
                    raise ClosureBlocked("tâches encore ouvertes")
                updated = project.complete(self._clock.now())
            elif command == "cancel":
                updated = project.cancel()
            else:
                raise InvalidValue("commande projet non reconnue")
            uow.save_project(updated)
            names = {"plan": "ProjectPlanned", "start": "ProjectStarted", "pause": "ProjectPaused",
                     "resume": "ProjectResumed", "complete": "ProjectCompleted", "cancel": "ProjectCancelled"}
            uow.record(self._event(names[command], id.value, updated.version, actor))
            uow.commit()
            return updated

    def plan_project(self, actor: ActorContext, id: ProjectId) -> Project:
        return self._change_project(actor, id, "plan")

    def start_project(self, actor: ActorContext, id: ProjectId) -> Project:
        return self._change_project(actor, id, "start")

    def pause_project(self, actor: ActorContext, id: ProjectId) -> Project:
        return self._change_project(actor, id, "pause")

    def resume_project(self, actor: ActorContext, id: ProjectId) -> Project:
        return self._change_project(actor, id, "resume")

    def complete_project(self, actor: ActorContext, id: ProjectId) -> Project:
        return self._change_project(actor, id, "complete")

    def cancel_project(self, actor: ActorContext, id: ProjectId) -> Project:
        return self._change_project(actor, id, "cancel")

    def add_milestone(self, actor: ActorContext, project_id: ProjectId,
                      name: str, target_date: date) -> Milestone:
        with self._uow_factory() as uow:
            project = self._project(uow, actor, project_id, "milestone:write")
            milestone = Milestone(self._ids.milestone_id(), name, target_date)
            updated = project.add_milestone(milestone)
            uow.save_project(updated)
            uow.record(self._event("MilestoneCreated", milestone.id.value, updated.version, actor))
            uow.commit()
            return milestone

    def reach_milestone(self, actor: ActorContext, project_id: ProjectId,
                        milestone_id: MilestoneId) -> Milestone:
        with self._uow_factory() as uow:
            project = self._project(uow, actor, project_id, "milestone:write")
            updated = project.reach_milestone(milestone_id, self._clock.now())
            uow.save_project(updated)
            uow.record(self._event("MilestoneReached", milestone_id.value, updated.version, actor))
            uow.commit()
            return updated.get_milestone(milestone_id)

    def get_milestone(self, actor: ActorContext, project_id: ProjectId,
                      milestone_id: MilestoneId) -> Milestone:
        with self._uow_factory() as uow:
            return self._project(uow, actor, project_id, "milestone:read").get_milestone(milestone_id)

    def list_milestones(self, actor: ActorContext, project_id: ProjectId) -> tuple[Milestone, ...]:
        with self._uow_factory() as uow:
            return self._project(uow, actor, project_id, "milestone:read").milestones

    def create_task(self, actor: ActorContext, project_id: ProjectId, title: str) -> Task:
        with self._uow_factory() as uow:
            project = self._project(uow, actor, project_id, "task:write")
            if project.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
                raise InvalidStateTransition("projet terminal")
            task = Task(self._ids.task_id(), project_id, title)
            uow.add_task(task)
            uow.record(self._event("TaskCreated", task.id.value, task.version, actor))
            uow.commit()
            return task

    def assign_task(self, actor: ActorContext, id: TaskId, assignee_id: str) -> Task:
        with self._uow_factory() as uow:
            task = self._task(uow, actor, id, "task:write")
            project = uow.get_project(task.project_id)
            if project.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
                raise InvalidStateTransition("projet terminal")
            updated = task.assign(assignee_id)
            uow.save_task(updated)
            uow.record(self._event("TaskAssigned", id.value, updated.version, actor))
            uow.commit()
            return updated

    def update_task_progress(self, actor: ActorContext, id: TaskId, progress: int) -> Task:
        with self._uow_factory() as uow:
            task = self._task(uow, actor, id, "task:write")
            project = uow.get_project(task.project_id)
            if project.status != ProjectStatus.ACTIVE:
                raise InvalidStateTransition("progression exige un projet actif")
            updated = task.set_progress(progress)
            uow.save_task(updated)
            uow.record(self._event("TaskProgressUpdated", id.value, updated.version, actor))
            uow.commit()
            return updated

    def add_dependency(self, actor: ActorContext, successor: TaskId, predecessor: TaskId) -> Dependency:
        with self._uow_factory() as uow:
            child = self._task(uow, actor, successor, "task:write")
            parent = self._task(uow, actor, predecessor, "task:write")
            project = uow.get_project(child.project_id)
            if child.project_id != parent.project_id:
                raise DependencyViolation("dépendance inter-projets interdite")
            if project.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
                raise InvalidStateTransition("projet terminal")
            if child.status in {TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW, TaskStatus.DONE} and parent.status != TaskStatus.DONE:
                raise DependencyViolation("ne pas rendre une tâche en cours incohérente")
            edge = Dependency(successor, predecessor)
            uow.add_dependency(project.id, edge)
            uow.record(self._event("TaskDependencyAdded", successor.value, child.version, actor))
            uow.commit()
            return edge

    def list_dependencies(self, actor: ActorContext, project_id: ProjectId) -> tuple[Dependency, ...]:
        with self._uow_factory() as uow:
            self._project(uow, actor, project_id, "task:read")
            return uow.list_dependencies(project_id)

    @staticmethod
    def _check_predecessors(uow: UnitOfWork, task: Task) -> None:
        for edge in uow.list_dependencies(task.project_id):
            if edge.successor == task.id and uow.get_task(edge.predecessor).status != TaskStatus.DONE:
                raise DependencyViolation("prérequis non terminé")

    def get_task(self, actor: ActorContext, id: TaskId) -> Task:
        with self._uow_factory() as uow:
            return self._task(uow, actor, id, "task:read")

    def list_tasks(self, actor: ActorContext, project_id: ProjectId) -> tuple[Task, ...]:
        with self._uow_factory() as uow:
            self._project(uow, actor, project_id, "task:read")
            return uow.list_tasks(project_id)

    def _change_task(self, actor: ActorContext, id: TaskId, command: str,
                     reason: str | None = None) -> Task:
        with self._uow_factory() as uow:
            task = self._task(uow, actor, id, "task:write")
            project = uow.get_project(task.project_id)
            if project.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
                raise InvalidStateTransition("projet terminal")
            if command == "ready":
                updated = task.ready()
            elif command == "start":
                if project.status != ProjectStatus.ACTIVE:
                    raise InvalidStateTransition("le projet doit être actif")
                self._check_predecessors(uow, task)
                updated = task.start(self._clock.now())
            elif command == "block":
                updated = task.block(reason or "")
            elif command == "unblock":
                if project.status != ProjectStatus.ACTIVE:
                    raise InvalidStateTransition("le projet doit être actif")
                self._check_predecessors(uow, task)
                updated = task.unblock(self._clock.now())
            elif command == "review":
                updated = task.submit_review()
            elif command == "return":
                if project.status != ProjectStatus.ACTIVE:
                    raise InvalidStateTransition("le projet doit être actif")
                self._check_predecessors(uow, task)
                updated = task.return_to_work()
            elif command == "complete":
                updated = task.complete(self._clock.now())
            elif command == "cancel":
                updated = task.cancel()
            else:
                raise InvalidValue("commande tâche non reconnue")
            uow.save_task(updated)
            names = {"ready": "TaskReady", "start": "TaskStarted", "block": "TaskBlocked",
                     "unblock": "TaskUnblocked", "review": "TaskSubmittedForReview",
                     "return": "TaskReturnedToWork", "complete": "TaskCompleted", "cancel": "TaskCancelled"}
            uow.record(self._event(names[command], id.value, updated.version, actor))
            uow.commit()
            return updated

    def ready_task(self, actor: ActorContext, id: TaskId) -> Task:
        return self._change_task(actor, id, "ready")

    def start_task(self, actor: ActorContext, id: TaskId) -> Task:
        return self._change_task(actor, id, "start")

    def block_task(self, actor: ActorContext, id: TaskId, reason: str) -> Task:
        return self._change_task(actor, id, "block", reason)

    def unblock_task(self, actor: ActorContext, id: TaskId) -> Task:
        return self._change_task(actor, id, "unblock")

    def submit_task_review(self, actor: ActorContext, id: TaskId) -> Task:
        return self._change_task(actor, id, "review")

    def return_task_to_work(self, actor: ActorContext, id: TaskId) -> Task:
        return self._change_task(actor, id, "return")

    def complete_task(self, actor: ActorContext, id: TaskId) -> Task:
        return self._change_task(actor, id, "complete")

    def cancel_task(self, actor: ActorContext, id: TaskId) -> Task:
        return self._change_task(actor, id, "cancel")
