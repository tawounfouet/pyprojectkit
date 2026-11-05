"""Parité M0 ciblée : affectation, progression, retour de revue et isolement des écrits."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from pyprojectkit_next import (
    AccessDenied, ActorContext, Conflict, InMemoryDatabase, InvalidStateTransition,
    InvalidValue, MilestoneId, NotFound, OwnerScopePolicy, Project, ProjectId, ProjectService, Task, TaskId,
    TaskStatus,
)

NOW = datetime(2026, 11, 5, 18, tzinfo=timezone.utc)


class Clock:
    def now(self) -> datetime:
        return NOW


class Ids:
    def __init__(self) -> None:
        self.p = 0
        self.t = 0
        self.m = 0

    def project_id(self) -> ProjectId:
        self.p += 1
        return ProjectId(f"p{self.p}")

    def task_id(self) -> TaskId:
        self.t += 1
        return TaskId(f"t{self.t}")

    def milestone_id(self) -> MilestoneId:
        self.m += 1
        return MilestoneId(f"m{self.m}")


@pytest.fixture
def env() -> tuple[ProjectService, InMemoryDatabase, ActorContext]:
    db = InMemoryDatabase()
    service = ProjectService(db.unit_of_work, clock=Clock(), ids=Ids(), authorization=OwnerScopePolicy())
    return service, db, ActorContext("owner", frozenset({"scope"}))


def active_task(env: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> Task:
    svc, _, actor = env
    project = svc.create_project(actor, "Projet", "scope")
    svc.plan_project(actor, project.id)
    svc.start_project(actor, project.id)
    return svc.create_task(actor, project.id, "Tâche")


def test_assign_task_records_event_and_increments_version(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    assigned = svc.assign_task(actor, task.id, "collaborateur")
    assert assigned.assignee_id == "collaborateur"
    assert assigned.version == task.version + 1
    assert task.assignee_id is None
    assert db.events[-1].name == "TaskAssigned"
    assert db.events[-1].aggregate_version == assigned.version


def test_reassign_changes_assignee_without_mutating_previous_snapshot(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, _, actor = env
    task = active_task(env)
    initial = svc.assign_task(actor, task.id, "alice")
    latest = svc.assign_task(actor, task.id, "bob")
    assert initial.assignee_id == "alice"
    assert latest.assignee_id == "bob"
    assert latest.version == initial.version + 1


@pytest.mark.parametrize("invalid", ["", " ", " alice", "alice "])
def test_reject_invalid_assignee_atomically(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext], invalid: str,
) -> None:
    svc, db, actor = env
    task = active_task(env)
    before = db.events
    with pytest.raises(InvalidValue):
        svc.assign_task(actor, task.id, invalid)
    assert svc.get_task(actor, task.id) == task
    assert db.events == before


def test_reject_redundant_assignment_without_new_event(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    assigned = svc.assign_task(actor, task.id, "alice")
    before = db.events
    with pytest.raises(Conflict):
        svc.assign_task(actor, task.id, "alice")
    assert db.events == before
    assert svc.get_task(actor, task.id) == assigned


def test_assignment_allowed_in_review_but_not_after_completion(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    svc.ready_task(actor, task.id)
    svc.start_task(actor, task.id)
    svc.submit_task_review(actor, task.id)
    assert svc.assign_task(actor, task.id, "bob").assignee_id == "bob"
    svc.complete_task(actor, task.id)
    before = db.events
    with pytest.raises(InvalidStateTransition):
        svc.assign_task(actor, task.id, "carol")
    assert db.events == before


def test_assignment_rejected_on_cancelled_task_and_terminal_project(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    svc.cancel_task(actor, task.id)
    before = db.events
    with pytest.raises(InvalidStateTransition):
        svc.assign_task(actor, task.id, "alice")
    assert db.events == before
    # Le projet actif peut être annulé ; aucune nouvelle mutation des tâches ensuite.
    svc.cancel_project(actor, task.project_id)
    with pytest.raises(InvalidStateTransition):
        svc.assign_task(actor, task.id, "alice")


def test_progress_only_on_started_task_and_active_project(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    before = db.events
    with pytest.raises(InvalidStateTransition):
        svc.update_task_progress(actor, task.id, 5)
    assert db.events == before
    svc.ready_task(actor, task.id)
    svc.start_task(actor, task.id)
    updated = svc.update_task_progress(actor, task.id, 35)
    assert updated.progress == 35
    assert updated.actual_start_at == NOW
    assert db.events[-1].name == "TaskProgressUpdated"
    svc.pause_project(actor, task.project_id)
    before = db.events
    with pytest.raises(InvalidStateTransition):
        svc.update_task_progress(actor, task.id, 55)
    assert db.events == before
    svc.resume_project(actor, task.project_id)
    assert svc.update_task_progress(actor, task.id, 55).progress == 55


@pytest.mark.parametrize("value", [-1, 101, 12.5, True, "50", None])
def test_progress_invalid_values_are_atomic(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext], value: object,
) -> None:
    svc, db, actor = env
    task = active_task(env)
    svc.ready_task(actor, task.id)
    svc.start_task(actor, task.id)
    before = db.events
    with pytest.raises(InvalidValue):
        svc.update_task_progress(actor, task.id, value)  # type: ignore[arg-type]
    assert db.events == before
    assert svc.get_task(actor, task.id).progress == 0


def test_progress_in_review_then_completion_sets_100(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    svc.ready_task(actor, task.id)
    started = svc.start_task(actor, task.id)
    assert started.actual_start_at == NOW
    svc.update_task_progress(actor, task.id, 60)
    svc.submit_task_review(actor, task.id)
    assert svc.update_task_progress(actor, task.id, 90).progress == 90
    completed = svc.complete_task(actor, task.id)
    assert completed.progress == 100
    assert completed.actual_end_at == NOW
    assert completed.actual_start_at == NOW
    before = db.events
    with pytest.raises(InvalidStateTransition):
        svc.update_task_progress(actor, task.id, 85)
    assert db.events == before


def test_redundant_progress_rejected_without_event(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    svc.ready_task(actor, task.id)
    svc.start_task(actor, task.id)
    updated = svc.update_task_progress(actor, task.id, 10)
    before = db.events
    with pytest.raises(Conflict):
        svc.update_task_progress(actor, task.id, 10)
    assert db.events == before
    assert svc.get_task(actor, task.id) == updated


def test_review_return_to_work_preserves_progress_and_start(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    svc.ready_task(actor, task.id)
    svc.start_task(actor, task.id)
    svc.update_task_progress(actor, task.id, 50)
    svc.submit_task_review(actor, task.id)
    returned = svc.return_task_to_work(actor, task.id)
    assert returned.status == TaskStatus.IN_PROGRESS
    assert returned.progress == 50
    assert returned.actual_start_at == NOW
    assert db.events[-1].name == "TaskReturnedToWork"
    svc.submit_task_review(actor, task.id)
    assert svc.complete_task(actor, task.id).status == TaskStatus.DONE


def test_review_return_requires_review_state_and_active_project(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    before = db.events
    with pytest.raises(InvalidStateTransition):
        svc.return_task_to_work(actor, task.id)
    assert db.events == before
    svc.ready_task(actor, task.id)
    svc.start_task(actor, task.id)
    svc.submit_task_review(actor, task.id)
    svc.pause_project(actor, task.project_id)
    before = db.events
    with pytest.raises(InvalidStateTransition):
        svc.return_task_to_work(actor, task.id)
    assert db.events == before


def test_auth_denies_assignment_progress_review_return_without_event(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    svc.ready_task(actor, task.id)
    svc.start_task(actor, task.id)
    svc.submit_task_review(actor, task.id)
    before = db.events
    for outsider in (ActorContext("other", frozenset({"scope"})),
                     ActorContext("owner", frozenset({"other-scope"}))):
        with pytest.raises(NotFound, match="ressource indisponible"):
            svc.assign_task(outsider, task.id, "someone")
        with pytest.raises(NotFound, match="ressource indisponible"):
            svc.update_task_progress(outsider, task.id, 10)
        with pytest.raises(NotFound, match="ressource indisponible"):
            svc.return_task_to_work(outsider, task.id)
    assert db.events == before


def test_concurrent_assignment_and_progress_conflict_without_partial_write(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    task = active_task(env)
    svc.ready_task(actor, task.id)
    svc.start_task(actor, task.id)
    before = db.events
    with db.unit_of_work() as left:
        old = left.get_task(task.id)
        left.save_task(old.assign("alice"))
        left.record(svc._event("TaskAssigned", task.id.value, old.version + 1, actor))
        with db.unit_of_work() as right:
            newer = right.get_task(task.id)
            right.save_task(newer.set_progress(40))
            right.record(svc._event("TaskProgressUpdated", task.id.value, newer.version + 1, actor))
            right.commit()
        with pytest.raises(Conflict):
            left.commit()
    current = svc.get_task(actor, task.id)
    assert current.assignee_id is None
    assert current.progress == 40
    assert len(db.events) == len(before) + 1
    assert db.events[-1].name == "TaskProgressUpdated"


def test_task_is_immutable_and_bad_date_rejected() -> None:
    task = Task(TaskId("t"), ProjectId("p"), "T")
    with pytest.raises(FrozenInstanceError):
        task.progress = 50  # type: ignore[misc]
    with pytest.raises(InvalidValue):
        Task(TaskId("t"), ProjectId("p"), "T", actual_start_at=datetime(2026, 11, 5))
    with pytest.raises(InvalidValue):
        Task(TaskId("t"), ProjectId("p"), "T", assignee_id="  ")
    with pytest.raises(InvalidValue):
        Task(TaskId("t"), ProjectId("p"), "T", progress=True)
    assert Project(ProjectId("p"), "P", "owner", "scope").version == 1
