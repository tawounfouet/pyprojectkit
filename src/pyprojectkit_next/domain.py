"""Noyau expérimental VS-REBOOT-01 - valeurs et transitions pures (sans I/O)."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from datetime import date, datetime
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


class DependencyViolation(DomainError):
    code = "DEPENDENCY_VIOLATION"


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


@dataclass(frozen=True, slots=True)
class MilestoneId:
    value: str

    def __post_init__(self) -> None:
        _required(self.value, "MilestoneId")


@dataclass(frozen=True, slots=True)
class Milestone:
    id: MilestoneId
    name: str
    target_date: date
    reached_at: datetime | None = None

    def __post_init__(self) -> None:
        _required(self.name, "milestone.name")
        if not isinstance(self.target_date, date) or isinstance(self.target_date, datetime):
            raise InvalidValue("target_date doit être une date civile")
        _aware(self.reached_at, "reached_at")

    def reach(self, at: datetime) -> Milestone:
        _aware(at, "at")
        if self.reached_at is not None:
            raise InvalidStateTransition("jalon déjà atteint")
        return replace(self, reached_at=at)


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
    milestones: tuple[Milestone, ...] = ()

    def __post_init__(self) -> None:
        _required(self.name, "name")
        _required(self.owner_id, "owner_id")
        _required(self.scope, "scope")
        if not isinstance(self.status, ProjectStatus) or self.version < 1:
            raise InvalidValue("statut ou version de projet invalide")
        _aware(self.actual_start_at, "actual_start_at")
        _aware(self.actual_end_at, "actual_end_at")
        if any(not isinstance(m, Milestone) for m in self.milestones):
            raise InvalidValue("liste de jalons non conforme")
        if len({m.id for m in self.milestones}) != len(self.milestones):
            raise Conflict("identifiants de jalons dupliqués")
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

    def add_milestone(self, milestone: Milestone) -> Project:
        if self.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
            raise InvalidStateTransition("projet terminal")
        if any(m.id == milestone.id for m in self.milestones):
            raise Conflict("jalon déjà présent")
        return replace(self, milestones=self.milestones + (milestone,), version=self.version + 1)

    def get_milestone(self, milestone_id: MilestoneId) -> Milestone:
        for milestone in self.milestones:
            if milestone.id == milestone_id:
                return milestone
        raise NotFound("jalon introuvable")

    def reach_milestone(self, milestone_id: MilestoneId, at: datetime) -> Project:
        if self.status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED}:
            raise InvalidStateTransition("projet terminal")
        milestone = self.get_milestone(milestone_id)
        reached = milestone.reach(at)
        return replace(self,
                       milestones=tuple(reached if m.id == milestone_id else m for m in self.milestones),
                       version=self.version + 1)

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
    assignee_id: str | None = None
    actual_start_at: datetime | None = None
    progress: int = 0

    def __post_init__(self) -> None:
        _required(self.title, "title")
        if not isinstance(self.status, TaskStatus) or self.version < 1:
            raise InvalidValue("statut ou version de tâche invalide")
        _aware(self.actual_start_at, "actual_start_at")
        _aware(self.actual_end_at, "actual_end_at")
        if self.assignee_id is not None:
            _required(self.assignee_id, "assignee_id")
        if type(self.progress) is not int or not 0 <= self.progress <= 100:
            raise InvalidValue("progress doit être un entier entre 0 et 100")
        if (self.actual_end_at is not None and self.actual_start_at is not None
                and self.actual_end_at < self.actual_start_at):
            raise InvalidValue("fin de tâche antérieure au démarrage")
        if self.status == TaskStatus.BLOCKED:
            _required(self.blocked_reason or "", "blocked_reason")
        elif self.blocked_reason is not None:
            raise InvalidValue("une tâche non bloquée ne doit pas conserver de cause active")
        if self.status == TaskStatus.DONE and (self.actual_end_at is None or self.progress != 100):
            raise InvalidValue("une tâche terminée exige date de fin et progression 100")

    def _transition(self, expected: tuple[TaskStatus, ...], target: TaskStatus, *,
                    blocked_reason: str | None = None, start_at: datetime | None = None,
                    end_at: datetime | None = None, progress: int | None = None) -> Task:
        if self.status not in expected:
            raise InvalidStateTransition(f"transition {self.status.value} vers {target.value} interdite")
        return replace(self, status=target, version=self.version + 1,
                       blocked_reason=blocked_reason,
                       actual_start_at=(start_at if self.actual_start_at is None and start_at is not None
                                        else self.actual_start_at),
                       actual_end_at=end_at if end_at is not None else self.actual_end_at,
                       progress=progress if progress is not None else self.progress)

    def assign(self, assignee_id: str) -> Task:
        if self.status in {TaskStatus.DONE, TaskStatus.CANCELLED}:
            raise InvalidStateTransition("affectation interdite sur une tâche terminale")
        _required(assignee_id, "assignee_id")
        if assignee_id == self.assignee_id:
            raise Conflict("affectation inchangée")
        return replace(self, assignee_id=assignee_id, version=self.version + 1)

    def set_progress(self, progress: int) -> Task:
        if self.status not in {TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW}:
            raise InvalidStateTransition("progression réservée à une tâche démarrée ou en revue")
        if type(progress) is not int or not 0 <= progress <= 100:
            raise InvalidValue("progress doit être un entier entre 0 et 100")
        if progress == self.progress:
            raise Conflict("progression inchangée")
        return replace(self, progress=progress, version=self.version + 1)

    def ready(self) -> Task:
        return self._transition((TaskStatus.TODO,), TaskStatus.READY)

    def start(self, at: datetime | None = None) -> Task:
        _aware(at, "at")
        return self._transition((TaskStatus.READY,), TaskStatus.IN_PROGRESS, start_at=at)

    def block(self, reason: str) -> Task:
        _required(reason, "reason")
        return self._transition((TaskStatus.IN_PROGRESS,), TaskStatus.BLOCKED, blocked_reason=reason)

    def unblock(self, at: datetime | None = None) -> Task:
        _aware(at, "at")
        return self._transition((TaskStatus.BLOCKED,), TaskStatus.IN_PROGRESS,
                                blocked_reason=None, start_at=at)

    def submit_review(self) -> Task:
        return self._transition((TaskStatus.IN_PROGRESS,), TaskStatus.IN_REVIEW)

    def return_to_work(self) -> Task:
        return self._transition((TaskStatus.IN_REVIEW,), TaskStatus.IN_PROGRESS)

    def complete(self, at: datetime) -> Task:
        _aware(at, "at")
        return self._transition((TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW), TaskStatus.DONE,
                                end_at=at, progress=100)

    def cancel(self) -> Task:
        if self.status in {TaskStatus.DONE, TaskStatus.CANCELLED}:
            raise InvalidStateTransition("une tâche terminale ne peut être annulée à nouveau")
        return replace(self, status=TaskStatus.CANCELLED, version=self.version + 1, blocked_reason=None)


@dataclass(frozen=True, slots=True)
class Dependency:
    """Orientation : successor dépend de predecessor."""
    successor: TaskId
    predecessor: TaskId

    def __post_init__(self) -> None:
        if not isinstance(self.successor, TaskId) or not isinstance(self.predecessor, TaskId):
            raise InvalidValue("identifiants de dépendance invalides")
        if self.successor == self.predecessor:
            raise DependencyViolation("auto-dépendance interdite")


def assert_acyclic(edges: frozenset[Dependency] | set[Dependency]) -> None:
    """Kahn itératif : O(V+E), sans profondeur de récursion bornante."""
    successors: dict[TaskId, set[TaskId]] = {}
    prerequisites: dict[TaskId, int] = {}
    for edge in edges:
        successors.setdefault(edge.predecessor, set()).add(edge.successor)
        prerequisites.setdefault(edge.predecessor, 0)
        prerequisites[edge.successor] = prerequisites.get(edge.successor, 0) + 1
    frontier = deque(node for node, count in prerequisites.items() if count == 0)
    visited = 0
    while frontier:
        node = frontier.popleft()
        visited += 1
        for successor in successors.get(node, ()):
            prerequisites[successor] -= 1
            if prerequisites[successor] == 0:
                frontier.append(successor)
    if visited != len(prerequisites):
        raise DependencyViolation("cycle de dépendances interdit")


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
