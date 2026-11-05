"""Contrats fonctionnels et négatifs de la première tranche Clean Reboot."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from pyprojectkit_next import (
    AccessDenied, ActorContext, ClosureBlocked, Conflict, DomainEvent, MilestoneId,
    InMemoryDatabase, InvalidStateTransition, InvalidValue, NotFound,
    OwnerScopePolicy, Project, ProjectId, ProjectService, ProjectStatus,
    Task, TaskId, TaskStatus,
)


NOW = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class CountingIds:
    def __init__(self) -> None:
        self.p = 0
        self.t = 0
        self.m = 0

    def project_id(self) -> ProjectId:
        self.p += 1
        return ProjectId(f"P-{self.p}")

    def task_id(self) -> TaskId:
        self.t += 1
        return TaskId(f"T-{self.t}")

    def milestone_id(self) -> MilestoneId:
        self.m += 1
        return MilestoneId(f"M-{self.m}")


@pytest.fixture
def harness() -> tuple[ProjectService, InMemoryDatabase, ActorContext]:
    db = InMemoryDatabase()
    service = ProjectService(db.unit_of_work, clock=FixedClock(),
                             ids=CountingIds(), authorization=OwnerScopePolicy())
    return service, db, ActorContext("owner-a", frozenset({"INTERNAL"}))


def test_create_and_read_project(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "Exemple", "INTERNAL")
    assert p.id == ProjectId("P-1")
    assert p.owner_id == "owner-a" and p.status == ProjectStatus.DRAFT
    assert s.get_project(actor, p.id) == p
    assert [(e.name, e.aggregate_version) for e in db.events] == [("ProjectCreated", 1)]


@pytest.mark.parametrize("bad", ["", " ", "  nom", "nom  "])
def test_blank_and_noncanonical_names_rejected(harness: tuple[ProjectService, InMemoryDatabase, ActorContext], bad: str) -> None:
    s, db, actor = harness
    with pytest.raises(InvalidValue):
        s.create_project(actor, bad, "INTERNAL")
    assert not db.events


def test_invalid_ids_and_naive_time() -> None:
    with pytest.raises(InvalidValue):
        ProjectId(" ")
    with pytest.raises(InvalidValue):
        TaskId("")
    with pytest.raises(InvalidValue):
        Project(ProjectId("P"), "P", "o", "s", status=ProjectStatus.ACTIVE)
    with pytest.raises(InvalidValue):
        Project(ProjectId("P"), "P", "o", "s", actual_start_at=datetime(2026, 1, 1))
    with pytest.raises(InvalidValue):
        Task(TaskId("T"), ProjectId("P"), "T", status=TaskStatus.DONE)


def test_project_lifecycle_pause_resume_keeps_original_start(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    p = s.plan_project(actor, p.id)
    p = s.start_project(actor, p.id)
    assert p.status == ProjectStatus.ACTIVE and p.actual_start_at == NOW
    p = s.pause_project(actor, p.id)
    assert p.status == ProjectStatus.ON_HOLD
    p = s.resume_project(actor, p.id)
    assert p.actual_start_at == NOW and p.status == ProjectStatus.ACTIVE
    p = s.complete_project(actor, p.id)
    assert p.status == ProjectStatus.COMPLETED and p.actual_end_at == NOW and p.version == 6
    assert len(db.events) == 6


def test_invalid_project_transition_does_not_write(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    with pytest.raises(InvalidStateTransition):
        s.start_project(actor, p.id)
    assert s.get_project(actor, p.id) == p
    assert len(db.events) == 1


def test_cancel_is_terminal_and_not_idempotent_success(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    s.cancel_project(actor, p.id)
    with pytest.raises(InvalidStateTransition):
        s.start_project(actor, p.id)
    with pytest.raises(InvalidStateTransition):
        s.cancel_project(actor, p.id)
    assert len(db.events) == 2


def test_task_happy_path_and_project_closure(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    s.plan_project(actor, p.id)
    s.start_project(actor, p.id)
    t = s.create_task(actor, p.id, "T")
    t = s.ready_task(actor, t.id)
    t = s.start_task(actor, t.id)
    t = s.submit_task_review(actor, t.id)
    assert t.status == TaskStatus.IN_REVIEW
    t = s.complete_task(actor, t.id)
    assert t.status == TaskStatus.DONE and t.actual_end_at == NOW
    assert s.list_tasks(actor, p.id) == (t,)
    assert s.complete_project(actor, p.id).status == ProjectStatus.COMPLETED
    assert db.events[-1].name == "ProjectCompleted"


def test_block_unblock_preserves_no_stale_reason(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    s.plan_project(actor, p.id)
    s.start_project(actor, p.id)
    t = s.create_task(actor, p.id, "T")
    s.ready_task(actor, t.id)
    s.start_task(actor, t.id)
    t = s.block_task(actor, t.id, "En attente")
    assert t.status == TaskStatus.BLOCKED and t.blocked_reason == "En attente"
    with pytest.raises(InvalidStateTransition):
        s.complete_task(actor, t.id)
    t = s.unblock_task(actor, t.id)
    assert t.status == TaskStatus.IN_PROGRESS and t.blocked_reason is None
    s.complete_task(actor, t.id)
    assert len(db.events) == 9


def test_task_double_completion_rejected_without_second_event(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    s.plan_project(actor, p.id)
    s.start_project(actor, p.id)
    t = s.create_task(actor, p.id, "T")
    s.ready_task(actor, t.id)
    s.start_task(actor, t.id)
    s.complete_task(actor, t.id)
    before = db.events
    with pytest.raises(InvalidStateTransition):
        s.complete_task(actor, t.id)
    assert db.events == before


def test_start_task_requires_active_project(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    t = s.create_task(actor, p.id, "T")
    s.ready_task(actor, t.id)
    with pytest.raises(InvalidStateTransition):
        s.start_task(actor, t.id)
    assert s.get_task(actor, t.id).status == TaskStatus.READY
    assert db.events[-1].name == "TaskReady"


def test_closure_refuses_open_task_and_does_not_emit_event(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    s.plan_project(actor, p.id)
    s.start_project(actor, p.id)
    s.create_task(actor, p.id, "T")
    baseline = db.events
    with pytest.raises(ClosureBlocked):
        s.complete_project(actor, p.id)
    assert s.get_project(actor, p.id).status == ProjectStatus.ACTIVE
    assert db.events == baseline


def test_cancelled_task_does_not_block_project_completion(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, _, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    s.plan_project(actor, p.id)
    s.start_project(actor, p.id)
    t = s.create_task(actor, p.id, "T")
    s.cancel_task(actor, t.id)
    assert s.complete_project(actor, p.id).status == ProjectStatus.COMPLETED


def test_terminal_project_refuses_new_task(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, _, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    s.cancel_project(actor, p.id)
    with pytest.raises(InvalidStateTransition):
        s.create_task(actor, p.id, "T")


def test_owner_denied_on_commands_and_reads(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, owner = harness
    p = s.create_project(owner, "P", "INTERNAL")
    intruder = ActorContext("other-owner", frozenset({"INTERNAL"}))
    before = db.events
    for op in (lambda: s.get_project(intruder, p.id),
               lambda: s.plan_project(intruder, p.id),
               lambda: s.list_tasks(intruder, p.id),
               lambda: s.create_task(intruder, p.id, "T")):
        with pytest.raises(NotFound, match="ressource indisponible"):
            op()
    assert before == db.events


def test_scope_denied_on_commands_and_reads(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, owner = harness
    with pytest.raises(AccessDenied):
        s.create_project(owner, "P", "PRIVATE")
    assert not db.events
    p = s.create_project(owner, "P", "INTERNAL")
    wrong_scope = ActorContext("owner-a", frozenset({"PRIVATE"}))
    with pytest.raises(NotFound, match="ressource indisponible"):
        s.get_project(wrong_scope, p.id)
    with pytest.raises(NotFound, match="ressource indisponible"):
        s.create_task(wrong_scope, p.id, "T")


def test_unknown_permission_fail_closed() -> None:
    with pytest.raises(AccessDenied):
        OwnerScopePolicy().require(ActorContext("o", frozenset({"s"})), "project:admin", scope="s", owner_id="o")


def test_missing_entities_do_not_mutate(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    with pytest.raises(NotFound):
        s.get_project(actor, ProjectId("missing"))
    with pytest.raises(NotFound):
        s.get_task(actor, TaskId("missing"))
    assert db.events == ()


def test_uow_rollback_isolation_and_atomicity() -> None:
    db = InMemoryDatabase()
    try:
        with db.unit_of_work() as uow:
            p = Project(ProjectId("P"), "P", "o", "s")
            uow.add_project(p)
            uow.record(DomainEvent("ProjectCreated", "P", 1, "o", NOW))
            raise RuntimeError("simulate")
    except RuntimeError:
        pass
    with db.unit_of_work() as verify:
        with pytest.raises(NotFound):
            verify.get_project(ProjectId("P"))
    assert db.events == ()


def test_uow_optimistic_conflict_preserves_state_and_events() -> None:
    db = InMemoryDatabase()
    with db.unit_of_work() as old:
        with db.unit_of_work() as new:
            new.add_project(Project(ProjectId("P-new"), "New", "o", "s"))
            new.record(DomainEvent("ProjectCreated", "P-new", 1, "o", NOW))
            new.commit()
        old.add_project(Project(ProjectId("P-old"), "Old", "o", "s"))
        old.record(DomainEvent("ProjectCreated", "P-old", 1, "o", NOW))
        with pytest.raises(Conflict):
            old.commit()
    with db.unit_of_work() as verify:
        assert verify.get_project(ProjectId("P-new")).name == "New"
        with pytest.raises(NotFound):
            verify.get_project(ProjectId("P-old"))
    assert len(db.events) == 1


def test_uow_rejects_duplicate_ids_and_wrong_versions() -> None:
    db = InMemoryDatabase()
    p = Project(ProjectId("P"), "P", "o", "s")
    with db.unit_of_work() as uow:
        uow.add_project(p)
        with pytest.raises(Conflict):
            uow.add_project(p)
        with pytest.raises(Conflict):
            uow.save_project(p)
        uow.commit()
    assert db.events == ()


def test_uow_event_without_mutation_rejected() -> None:
    db = InMemoryDatabase()
    with db.unit_of_work() as uow:
        uow.record(DomainEvent("Fake", "P", 1, "o", NOW))
        with pytest.raises(Conflict):
            uow.commit()
    assert not db.events


def test_read_only_uow_does_not_advance_revision() -> None:
    db = InMemoryDatabase()
    with db.unit_of_work() as u1:
        with db.unit_of_work() as reader:
            assert reader.list_tasks(ProjectId("P")) == ()
            assert reader.commit() == ()
        u1.add_project(Project(ProjectId("P"), "P", "o", "s"))
        u1.commit()
    with db.unit_of_work() as verify:
        assert verify.get_project(ProjectId("P")).name == "P"


def test_local_events_not_claimed_as_external_delivery(harness: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    s, db, actor = harness
    p = s.create_project(actor, "P", "INTERNAL")
    assert db.events == (DomainEvent("ProjectCreated", p.id.value, 1, actor.subject_id, NOW),)
    assert isinstance(db.events, tuple)


def test_no_legacy_import_required() -> None:
    # Contrôle structurel du package isolé : aucun import pyprojectkit/m1/m2.
    root = Path(__file__).resolve().parents[1] / "src" / "pyprojectkit_next"
    content = "\n".join(p.read_text(encoding="utf-8") for p in root.glob("*.py"))
    assert "from pyprojectkit." not in content
    assert "import sqlite3" not in content
