"""Use cases M0 bornés du VS-REBOOT-01, indépendant de M1/M2."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .domain import (
    AccessDenied, ClosureBlocked, DomainEvent, InvalidStateTransition, InvalidValue,
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


class OwnerScopePolicy:
    """Policy minimale fail-closed : actor fourni par hôte fiable uniquement."""
    _actions = frozenset({"project:create", "project:read", "project:write", "task:read", "task:write"})

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
        project = uow.get_project(id)
        self._auth.require(actor, action, scope=project.scope, owner_id=project.owner_id)
        return project

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

    def get_task(self, actor: ActorContext, id: TaskId) -> Task:
        with self._uow_factory() as uow:
            task = uow.get_task(id)
            self._project(uow, actor, task.project_id, "task:read")
            return task

    def list_tasks(self, actor: ActorContext, project_id: ProjectId) -> tuple[Task, ...]:
        with self._uow_factory() as uow:
            self._project(uow, actor, project_id, "task:read")
            return uow.list_tasks(project_id)

    def _change_task(self, actor: ActorContext, id: TaskId, command: str,
                     reason: str | None = None) -> Task:
        with self._uow_factory() as uow:
            task = uow.get_task(id)
            project = self._project(uow, actor, task.project_id, "task:write")
            if project.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
                raise InvalidStateTransition("projet terminal")
            if command == "ready":
                updated = task.ready()
            elif command == "start":
                if project.status != ProjectStatus.ACTIVE:
                    raise InvalidStateTransition("le projet doit être actif")
                updated = task.start()
            elif command == "block":
                updated = task.block(reason or "")
            elif command == "unblock":
                updated = task.unblock()
            elif command == "review":
                updated = task.submit_review()
            elif command == "complete":
                updated = task.complete(self._clock.now())
            elif command == "cancel":
                updated = task.cancel()
            else:
                raise InvalidValue("commande tâche non reconnue")
            uow.save_task(updated)
            names = {"ready": "TaskReady", "start": "TaskStarted", "block": "TaskBlocked",
                     "unblock": "TaskUnblocked", "review": "TaskSubmittedForReview",
                     "complete": "TaskCompleted", "cancel": "TaskCancelled"}
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

    def complete_task(self, actor: ActorContext, id: TaskId) -> Task:
        return self._change_task(actor, id, "complete")

    def cancel_task(self, actor: ActorContext, id: TaskId) -> Task:
        return self._change_task(actor, id, "cancel")
