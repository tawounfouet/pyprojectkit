"""Parité comportementale M0 ciblée : AC-004/005/006, transaction et sécurité."""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from pyprojectkit_next import (
    AccessDenied, ActorContext, Conflict, Dependency, DependencyViolation,
    DomainEvent, InMemoryDatabase, InvalidStateTransition, InvalidValue,
    Milestone, MilestoneId, NotFound, OwnerScopePolicy, Project,
    ProjectId, ProjectService, ProjectStatus, Task, TaskId, TaskStatus,
    assert_acyclic,
)

NOW = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FakeIds:
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
def env() -> tuple[ProjectService, InMemoryDatabase, ActorContext]:
    db = InMemoryDatabase()
    service = ProjectService(db.unit_of_work, clock=FixedClock(), ids=FakeIds(), authorization=OwnerScopePolicy())
    return service, db, ActorContext("owner", frozenset({"INTERNAL"}))


def active(env: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> ProjectId:
    svc, _, actor = env
    p = svc.create_project(actor, "P", "INTERNAL")
    svc.plan_project(actor, p.id)
    svc.start_project(actor, p.id)
    return p.id


def test_ac006_create_reach_and_no_repeat(env: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    svc, db, actor = env
    p = svc.create_project(actor, "P", "INTERNAL")
    m = svc.add_milestone(actor, p.id, "Release", date(2027, 1, 1))
    assert m.id == MilestoneId("M-1")
    assert svc.get_milestone(actor, p.id, m.id) == m
    assert svc.list_milestones(actor, p.id) == (m,)
    reached = svc.reach_milestone(actor, p.id, m.id)
    assert reached.reached_at == NOW
    assert svc.get_project(actor, p.id).version == 3
    assert [(e.name, e.aggregate_id, e.aggregate_version) for e in db.events][-2:] == [
        ("MilestoneCreated", "M-1", 2), ("MilestoneReached", "M-1", 3)]
    before = db.events
    with pytest.raises(InvalidStateTransition):
        svc.reach_milestone(actor, p.id, m.id)
    assert db.events == before


@pytest.mark.parametrize("name,when", [
    ("", date(2027, 1, 1)), ("  X", date(2027, 1, 1)),
    ("X  ", date(2027, 1, 1)), ("X", None),
    ("X", datetime(2027, 1, 1, tzinfo=timezone.utc)),
])
def test_ac006_invalid_milestones_are_atomic(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext], name: str, when: object,
) -> None:
    svc, db, actor = env
    p = svc.create_project(actor, "P", "INTERNAL")
    events = db.events
    with pytest.raises(InvalidValue):
        svc.add_milestone(actor, p.id, name, when)  # type: ignore[arg-type]
    assert svc.list_milestones(actor, p.id) == ()
    assert db.events == events


def test_ac006_milestone_dates_require_aware_reach() -> None:
    milestone = Milestone(MilestoneId("M"), "Jalon", date(2027, 1, 1))
    with pytest.raises(InvalidValue):
        milestone.reach(datetime(2026, 1, 1))
    assert milestone.reached_at is None


def test_ac006_terminal_project_cannot_add_or_reach_milestone(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    p = svc.create_project(actor, "P", "INTERNAL")
    milestone = svc.add_milestone(actor, p.id, "Release", date(2027, 1, 1))
    svc.cancel_project(actor, p.id)
    events = db.events
    with pytest.raises(InvalidStateTransition):
        svc.add_milestone(actor, p.id, "Later", date(2028, 1, 1))
    with pytest.raises(InvalidStateTransition):
        svc.reach_milestone(actor, p.id, milestone.id)
    assert db.events == events


def test_ac006_missing_milestone_and_conflicting_id(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    p = svc.create_project(actor, "P", "INTERNAL")
    with pytest.raises(NotFound):
        svc.get_milestone(actor, p.id, MilestoneId("missing"))
    with pytest.raises(NotFound):
        svc.reach_milestone(actor, p.id, MilestoneId("missing"))
    m = Milestone(MilestoneId("X"), "x", date(2027, 1, 1))
    with db.unit_of_work() as uow:
        proj = uow.get_project(p.id)
        v2 = proj.add_milestone(m)
        with pytest.raises(Conflict):
            v2.add_milestone(m)
        uow.save_project(v2)
        uow.commit()
    assert svc.get_project(actor, p.id).milestones == (m,)


def test_ac006_milestone_immutability_and_snapshot_copy(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, _, actor = env
    p = svc.create_project(actor, "P", "INTERNAL")
    m = svc.add_milestone(actor, p.id, "Release", date(2027, 1, 1))
    read = svc.get_project(actor, p.id)
    with pytest.raises(FrozenInstanceError):
        m.name = "Changed"  # type: ignore[misc]
    reached = svc.reach_milestone(actor, p.id, m.id)
    assert m.reached_at is None
    assert read.milestones[0].reached_at is None
    assert reached.reached_at == NOW


def test_milestone_owner_and_scope_denied_without_event(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    p = svc.create_project(actor, "P", "INTERNAL")
    m = svc.add_milestone(actor, p.id, "X", date(2027, 1, 1))
    before = db.events
    for outsider in (ActorContext("other", frozenset({"INTERNAL"})),
                     ActorContext("owner", frozenset({"PRIVATE"}))):
        for call in (lambda: svc.list_milestones(outsider, p.id),
                     lambda: svc.get_milestone(outsider, p.id, m.id),
                     lambda: svc.reach_milestone(outsider, p.id, m.id),
                     lambda: svc.add_milestone(outsider, p.id, "X", date(2027, 1, 1))):
            with pytest.raises(NotFound, match="ressource indisponible"):
                call()
    assert db.events == before


def test_ac004_ac005_ordered_prerequisites_and_atomic_cycle_guard(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    pid = active(env)
    a, b, c = [svc.create_task(actor, pid, name) for name in ("A", "B", "C")]
    svc.add_dependency(actor, b.id, a.id)
    svc.add_dependency(actor, c.id, b.id)
    assert len(svc.list_dependencies(actor, pid)) == 2
    before = db.events
    for child, parent in ((a.id, c.id), (a.id, a.id)):
        with pytest.raises(DependencyViolation):
            svc.add_dependency(actor, child, parent)
    assert db.events == before
    svc.ready_task(actor, c.id)
    with pytest.raises(DependencyViolation):
        svc.start_task(actor, c.id)
    svc.ready_task(actor, a.id)
    svc.start_task(actor, a.id)
    svc.complete_task(actor, a.id)
    svc.ready_task(actor, b.id)
    svc.start_task(actor, b.id)
    svc.complete_task(actor, b.id)
    assert svc.start_task(actor, c.id).status == TaskStatus.IN_PROGRESS


def test_duplicate_edge_conflicts_without_new_event(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    pid = active(env)
    a, b = [svc.create_task(actor, pid, name) for name in ("A", "B")]
    edge = svc.add_dependency(actor, b.id, a.id)
    before = db.events
    with pytest.raises(Conflict):
        svc.add_dependency(actor, b.id, a.id)
    assert svc.list_dependencies(actor, pid) == (edge,)
    assert db.events == before


def test_cross_project_and_scope_edges_rejected(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    first = svc.create_project(actor, "P", "INTERNAL")
    second = svc.create_project(actor, "Q", "INTERNAL")
    a = svc.create_task(actor, first.id, "A")
    b = svc.create_task(actor, second.id, "B")
    before = db.events
    with pytest.raises(DependencyViolation):
        svc.add_dependency(actor, a.id, b.id)
    other_scope = ActorContext("outsider", frozenset({"PRIVATE"}))
    third = svc.create_project(other_scope, "Secret", "PRIVATE")
    secret = svc.create_task(other_scope, third.id, "Private")
    before = db.events
    with pytest.raises(NotFound, match="ressource indisponible"):
        svc.add_dependency(actor, a.id, secret.id)
    assert db.events == before
    assert svc.list_dependencies(actor, first.id) == ()


def test_graph_reads_are_scoped_and_stable(env: tuple[ProjectService, InMemoryDatabase, ActorContext]) -> None:
    svc, db, actor = env
    pid = active(env)
    a, b = [svc.create_task(actor, pid, name) for name in ("A", "B")]
    svc.add_dependency(actor, b.id, a.id)
    before = db.events
    outsider = ActorContext("outsider", frozenset({"INTERNAL"}))
    with pytest.raises(NotFound, match="ressource indisponible"):
        svc.list_dependencies(outsider, pid)
    assert svc.list_dependencies(actor, pid) == (Dependency(b.id, a.id),)
    assert svc.list_dependencies(actor, pid) == svc.list_dependencies(actor, pid)
    assert db.events == before


def test_missing_task_and_terminal_project_reject_graph_write(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    pid = active(env)
    a = svc.create_task(actor, pid, "A")
    with pytest.raises(NotFound):
        svc.add_dependency(actor, a.id, TaskId("unknown"))
    svc.cancel_project(actor, pid)
    before = db.events
    with pytest.raises(InvalidStateTransition):
        svc.add_dependency(actor, a.id, a.id)
    assert db.events == before


def test_predecessor_cancelled_is_not_done(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    pid = active(env)
    a, b = [svc.create_task(actor, pid, name) for name in ("A", "B")]
    svc.add_dependency(actor, b.id, a.id)
    svc.cancel_task(actor, a.id)
    svc.ready_task(actor, b.id)
    before = db.events
    with pytest.raises(DependencyViolation):
        svc.start_task(actor, b.id)
    assert db.events == before


def test_dependency_added_during_in_progress_must_already_be_satisfied(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    pid = active(env)
    a, b = [svc.create_task(actor, pid, name) for name in ("A", "B")]
    svc.ready_task(actor, b.id)
    svc.start_task(actor, b.id)
    before = db.events
    with pytest.raises(DependencyViolation):
        svc.add_dependency(actor, b.id, a.id)
    assert db.events == before
    assert svc.list_dependencies(actor, pid) == ()


def test_unblock_rechecks_dependency_and_project_activity(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    pid = active(env)
    a, b = [svc.create_task(actor, pid, name) for name in ("A", "B")]
    svc.ready_task(actor, b.id)
    svc.start_task(actor, b.id)
    svc.block_task(actor, b.id, "Wait")
    svc.add_dependency(actor, b.id, a.id)
    before = db.events
    with pytest.raises(DependencyViolation):
        svc.unblock_task(actor, b.id)
    svc.pause_project(actor, pid)
    with pytest.raises(InvalidStateTransition):
        svc.unblock_task(actor, b.id)
    assert len(db.events) == len(before) + 1


def test_graph_uow_conflict_cannot_create_concurrent_cycle(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    pid = active(env)
    a, b = [svc.create_task(actor, pid, name) for name in ("A", "B")]
    with db.unit_of_work() as old:
        old.add_dependency(pid, Dependency(a.id, b.id))
        with db.unit_of_work() as new:
            new.add_dependency(pid, Dependency(b.id, a.id))
            new.commit()
        with pytest.raises(Conflict):
            old.commit()
    with db.unit_of_work() as reader:
        assert reader.list_dependencies(pid) == (Dependency(b.id, a.id),)
    assert svc.list_dependencies(actor, pid) == (Dependency(b.id, a.id),)


def test_graph_and_project_writes_conflict_on_old_snapshot(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    pid = active(env)
    a, b = [svc.create_task(actor, pid, name) for name in ("A", "B")]
    with db.unit_of_work() as old:
        old.add_dependency(pid, Dependency(b.id, a.id))
        svc.pause_project(actor, pid)
        with pytest.raises(Conflict):
            old.commit()
    assert svc.list_dependencies(actor, pid) == ()


def test_graph_milestone_transaction_rollback_and_events_atomic(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    pid = active(env)
    a, b = [svc.create_task(actor, pid, name) for name in ("A", "B")]
    before = db.events
    with pytest.raises(RuntimeError):
        with db.unit_of_work() as tx:
            tx.add_dependency(pid, Dependency(b.id, a.id))
            proj = tx.get_project(pid)
            tx.save_project(proj.add_milestone(Milestone(MilestoneId("M-x"), "X", date(2027, 1, 1))))
            tx.record(DomainEvent("Test", pid.value, 1, actor.subject_id, NOW))
            raise RuntimeError("before commit")
    assert db.events == before
    assert svc.list_dependencies(actor, pid) == ()
    assert svc.list_milestones(actor, pid) == ()


def test_adapter_rejects_cross_project_edge_even_if_service_bypassed(
    env: tuple[ProjectService, InMemoryDatabase, ActorContext],
) -> None:
    svc, db, actor = env
    a = svc.create_project(actor, "P", "INTERNAL")
    b = svc.create_project(actor, "Q", "INTERNAL")
    t1 = svc.create_task(actor, a.id, "A")
    t2 = svc.create_task(actor, b.id, "B")
    with db.unit_of_work() as tx:
        with pytest.raises(DependencyViolation):
            tx.add_dependency(a.id, Dependency(t1.id, t2.id))
    assert db.events[-1].name == "TaskCreated"


def test_iterative_acyclic_validation_handles_long_chain() -> None:
    edges = {Dependency(TaskId(str(i + 1)), TaskId(str(i))) for i in range(1500)}
    assert_acyclic(edges)
    edges.add(Dependency(TaskId("0"), TaskId("1500")))
    with pytest.raises(DependencyViolation):
        assert_acyclic(edges)


def test_scope_unknown_permission_remains_fail_closed() -> None:
    with pytest.raises(AccessDenied):
        OwnerScopePolicy().require(ActorContext("owner", frozenset({"INTERNAL"})),
                                   "milestone:delete", scope="INTERNAL", owner_id="owner")


def test_no_sqlite_or_legacy_dependency_in_new_graph() -> None:
    root = Path(__file__).resolve().parents[1]/"src/pyprojectkit_next"
    contents = "\n".join(p.read_text() for p in root.glob("*.py"))
    assert "import sqlite3" not in contents
    assert "from pyprojectkit." not in contents
