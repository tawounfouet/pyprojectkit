"""Noyau de domaine M0, sans dépendance aux adaptateurs (DDD)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID


class DomainError(Exception):
    """Erreur métier stable, sans détails sensibles."""


class InvalidStateTransition(DomainError):
    pass


class InvalidValue(DomainError):
    pass


class DependencyViolation(DomainError):
    pass


class Conflict(DomainError):
    pass


class NotFound(DomainError):
    pass


class AccessDenied(DomainError):
    pass


class CommitOutcomeUnknown(DomainError):
    pass


@dataclass(frozen=True, slots=True)
class ProjectId:
    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidValue("ProjectId attend un UUID")


@dataclass(frozen=True, slots=True)
class TaskId:
    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidValue("TaskId attend un UUID")


@dataclass(frozen=True, slots=True)
class MilestoneId:
    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise InvalidValue("MilestoneId attend un UUID")


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskStatus(StrEnum):
    TODO = "TODO"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


@dataclass(slots=True)
class Milestone:
    id: MilestoneId
    name: str
    target_date: date
    reached_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name.strip() or not isinstance(self.target_date, date):
            raise InvalidValue("Jalon : nom et date cible requis")
        if self.reached_at is not None:
            _aware(self.reached_at)

    def reach(self, at: datetime) -> None:
        _aware(at)
        if self.reached_at is not None:
            raise InvalidStateTransition("Jalon déjà atteint")
        self.reached_at = at


def _aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidValue("Horodatage avec timezone requis")


@dataclass(slots=True)
class Project:
    id: ProjectId
    name: str
    owner_id: str
    scope: str
    status: ProjectStatus = ProjectStatus.DRAFT
    version: int = 0
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    milestones: dict[MilestoneId, Milestone] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.owner_id.strip() or not self.scope.strip():
            raise InvalidValue("Project exige un nom, un owner et un scope")

    def transition(self, target: ProjectStatus, at: datetime) -> None:
        _aware(at)
        allowed = {
            ProjectStatus.DRAFT: {ProjectStatus.PLANNED, ProjectStatus.CANCELLED},
            ProjectStatus.PLANNED: {ProjectStatus.ACTIVE, ProjectStatus.CANCELLED},
            ProjectStatus.ACTIVE: {ProjectStatus.ON_HOLD, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED},
            ProjectStatus.ON_HOLD: {ProjectStatus.ACTIVE, ProjectStatus.CANCELLED},
        }
        if target not in allowed.get(self.status, set()):
            raise InvalidStateTransition(f"Transition Project {self.status} -> {target} interdite")
        if target is ProjectStatus.ACTIVE and self.actual_start_at is None:
            self.actual_start_at = at
        if target is ProjectStatus.COMPLETED:
            self.actual_end_at = at
        self.status = target

    def add_milestone(self, item: Milestone) -> None:
        if self.status in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED):
            raise InvalidStateTransition("Projet terminal")
        if item.id in self.milestones:
            raise Conflict("Jalon déjà présent")
        self.milestones[item.id] = item


@dataclass(slots=True)
class Task:
    id: TaskId
    project_id: ProjectId
    title: str
    status: TaskStatus = TaskStatus.TODO
    version: int = 0
    assignee_id: str | None = None
    block_reason: str | None = None
    actual_start_at: datetime | None = None
    actual_end_at: datetime | None = None
    progress: int = 0

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise InvalidValue("Titre de tâche vide")
        if not (0 <= self.progress <= 100):
            raise InvalidValue("Progression hors de 0..100")

    def transition(self, target: TaskStatus, at: datetime, *, reason: str | None = None) -> None:
        _aware(at)
        allowed = {
            TaskStatus.TODO: {TaskStatus.READY, TaskStatus.CANCELLED},
            TaskStatus.READY: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.IN_PROGRESS: {TaskStatus.BLOCKED, TaskStatus.IN_REVIEW, TaskStatus.DONE, TaskStatus.CANCELLED},
            TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.IN_REVIEW: {TaskStatus.DONE, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
        }
        if target not in allowed.get(self.status, set()):
            raise InvalidStateTransition(f"Transition Task {self.status} -> {target} interdite")
        if target is TaskStatus.BLOCKED:
            if not reason or not reason.strip():
                raise InvalidValue("Motif de blocage requis")
            self.block_reason = reason.strip()
        elif self.status is TaskStatus.BLOCKED:
            self.block_reason = None
        if target is TaskStatus.IN_PROGRESS and self.actual_start_at is None:
            self.actual_start_at = at
        if target is TaskStatus.DONE:
            self.actual_end_at = at
            self.progress = 100
        self.status = target


@dataclass(frozen=True, slots=True)
class Dependency:
    successor: TaskId
    predecessor: TaskId

    def __post_init__(self) -> None:
        if self.successor == self.predecessor:
            raise DependencyViolation("Auto-dépendance interdite")


def assert_acyclic(edges: set[Dependency]) -> None:
    """Les arcs successor -> predecessor expriment 'A dépend de B'."""
    adjacency: dict[TaskId, set[TaskId]] = {}
    for edge in edges:
        adjacency.setdefault(edge.successor, set()).add(edge.predecessor)
    visited: set[TaskId] = set()
    stack: set[TaskId] = set()

    def visit(node: TaskId) -> None:
        if node in stack:
            raise DependencyViolation("Cycle de dépendances interdit")
        if node in visited:
            return
        stack.add(node)
        for dep in adjacency.get(node, set()):
            visit(dep)
        stack.remove(node)
        visited.add(node)

    for node in list(adjacency):
        visit(node)


@dataclass(frozen=True, slots=True)
class DomainEvent:
    name: str
    aggregate_id: str
    occurred_at: datetime
    actor_id: str

    def __post_init__(self) -> None:
        _aware(self.occurred_at)