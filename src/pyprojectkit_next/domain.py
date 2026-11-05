"""Noyau expérimental VS-REBOOT-01 - valeurs et transitions pures (sans I/O)."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum


class DomainError(Exception):
    """Erreur métier avec code stable, sans détail d'infrastructure."""
    code = "DOMAIN_ERROR"


class InvalidValue(DomainError):
    code = "INVALID_VALUE"


class InvalidStateTransition(DomainError):
    code = "INVALID_STATE_TRANSITION"


class AccessDenied(DomainError):
    code = "ACCESS_DENIED"


class NotFound(DomainError):
    code = "NOT_FOUND"


class Conflict(DomainError):
    code = "CONFLICT"


class ClosureBlocked(DomainError):
    code = "CLOSURE_BLOCKED"


def _required(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise InvalidValue(f"{field} doit être une chaîne non vide sans bordures blanches")


def _aware(value: datetime | None, field: str) -> None:
    if value is not None and (value.tzinfo is None or value.utcoffset() is None):
        raise InvalidValue(f"{field} doit avoir un fuseau horaire")


@dataclass(frozen=True, slots=True)
class ProjectId:
    value: str

    def __post_init__(self) -> None:
        _required(self.value, "ProjectId")


@dataclass(frozen=True, slots=True)
class TaskId:
    value: str

    def __post_init__(self) -> None:
        _required(self.value, "TaskId")


class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskStatus(str, Enum):
    TODO = "TODO"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class Project:
    id: ProjectId
    name: str
    owner_id: str
    scope: str
    status: ProjectStatus = ProjectStatus.DRAFT
    version: int = 1
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None

    def __post_init__(self) -> None:
        _required(self.name, "name")
        _required(self.owner_id, "owner_id")
        _required(self.scope, "scope")
        if not isinstance(self.status, ProjectStatus) or self.version < 1:
            raise InvalidValue("statut ou version de projet invalide")
        _aware(self.actual_start_at, "actual_start_at")
        _aware(self.actual_end_at, "actual_end_at")
        if self.status in {ProjectStatus.ACTIVE, ProjectStatus.ON_HOLD, ProjectStatus.COMPLETED} and self.actual_start_at is None:
            raise InvalidValue("un projet démarré exige une date de démarrage")
        if self.status == ProjectStatus.COMPLETED and self.actual_end_at is None:
            raise InvalidValue("un projet terminé exige une date de clôture")
        if self.actual_end_at is not None and self.actual_start_at is not None and self.actual_end_at < self.actual_start_at:
            raise InvalidValue("la clôture précède le démarrage")

    def _transition(self, expected: ProjectStatus, target: ProjectStatus, *,
                    start_at: datetime | None = None, end_at: datetime | None = None) -> Project:
        if self.status != expected:
            raise InvalidStateTransition(f"{expected.value} requis pour {target.value}")
        return replace(self, status=target, version=self.version + 1,
                       actual_start_at=start_at if start_at is not None else self.actual_start_at,
                       actual_end_at=end_at if end_at is not None else self.actual_end_at)

    def plan(self) -> Project:
        return self._transition(ProjectStatus.DRAFT, ProjectStatus.PLANNED)

    def start(self, at: datetime) -> Project:
        _aware(at, "at")
        return self._transition(ProjectStatus.PLANNED, ProjectStatus.ACTIVE, start_at=at)

    def pause(self) -> Project:
        return self._transition(ProjectStatus.ACTIVE, ProjectStatus.ON_HOLD)

    def resume(self) -> Project:
        return self._transition(ProjectStatus.ON_HOLD, ProjectStatus.ACTIVE)

    def complete(self, at: datetime) -> Project:
        _aware(at, "at")
        return self._transition(ProjectStatus.ACTIVE, ProjectStatus.COMPLETED, end_at=at)

    def cancel(self) -> Project:
        if self.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
            raise InvalidStateTransition("un projet terminal ne peut être annulé à nouveau")
        return replace(self, status=ProjectStatus.CANCELLED, version=self.version + 1)


@dataclass(frozen=True, slots=True)
class Task:
    id: TaskId
    project_id: ProjectId
    title: str
    status: TaskStatus = TaskStatus.TODO
    version: int = 1
    blocked_reason: str | None = None
    actual_end_at: datetime | None = None

    def __post_init__(self) -> None:
        _required(self.title, "title")
        if not isinstance(self.status, TaskStatus) or self.version < 1:
            raise InvalidValue("statut ou version de tâche invalide")
        _aware(self.actual_end_at, "actual_end_at")
        if self.status == TaskStatus.BLOCKED:
            _required(self.blocked_reason or "", "blocked_reason")
        elif self.blocked_reason is not None:
            raise InvalidValue("une tâche non bloquée ne doit pas conserver de cause active")
        if self.status == TaskStatus.DONE and self.actual_end_at is None:
            raise InvalidValue("une tâche terminée exige une date de fin")

    def _transition(self, expected: tuple[TaskStatus, ...], target: TaskStatus, *,
                    blocked_reason: str | None = None, end_at: datetime | None = None) -> Task:
        if self.status not in expected:
            raise InvalidStateTransition(f"transition {self.status.value} vers {target.value} interdite")
        return replace(self, status=target, version=self.version + 1,
                       blocked_reason=blocked_reason,
                       actual_end_at=end_at if end_at is not None else self.actual_end_at)

    def ready(self) -> Task:
        return self._transition((TaskStatus.TODO,), TaskStatus.READY)

    def start(self) -> Task:
        return self._transition((TaskStatus.READY,), TaskStatus.IN_PROGRESS)

    def block(self, reason: str) -> Task:
        _required(reason, "reason")
        return self._transition((TaskStatus.IN_PROGRESS,), TaskStatus.BLOCKED, blocked_reason=reason)

    def unblock(self) -> Task:
        return self._transition((TaskStatus.BLOCKED,), TaskStatus.IN_PROGRESS, blocked_reason=None)

    def submit_review(self) -> Task:
        return self._transition((TaskStatus.IN_PROGRESS,), TaskStatus.IN_REVIEW)

    def complete(self, at: datetime) -> Task:
        _aware(at, "at")
        return self._transition((TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW), TaskStatus.DONE, end_at=at)

    def cancel(self) -> Task:
        if self.status in {TaskStatus.DONE, TaskStatus.CANCELLED}:
            raise InvalidStateTransition("une tâche terminale ne peut être annulée à nouveau")
        return replace(self, status=TaskStatus.CANCELLED, version=self.version + 1, blocked_reason=None)


@dataclass(frozen=True, slots=True)
class DomainEvent:
    name: str
    aggregate_id: str
    aggregate_version: int
    actor_id: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        for f in ("name", "aggregate_id", "actor_id"):
            _required(getattr(self, f), f)
        if self.aggregate_version < 1:
            raise InvalidValue("version d'événement invalide")
        _aware(self.occurred_at, "occurred_at")
