"""ARCH-06 / A06-02 : oracles du contrat de persistance sur Memory uniquement.

Ces tests sont executables avant G1/G2 pour caracteriser la baseline.
Ils ne qualifient aucun adaptateur SQLite et ne constituent pas le gate G3.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pyprojectkit_next import (
    ActorContext, Conflict, Dependency, DependencyViolation, DomainEvent,
    InMemoryDatabase, MilestoneId, NotFound, OwnerScopePolicy, Project, ProjectId,
    ProjectService, ProjectStatus, Task, TaskId,
)

NOW = datetime(2026, 11, 6, 9, tzinfo=timezone.utc)


class FrozenClock:
    def now(self) -> datetime:
        return NOW


class SequenceIds:
    def __init__(self) -> None:
        self._value = 0

    def project_id(self) -> ProjectId:
        self._value += 1
        return ProjectId(f"PROJECT-{self._value}")

    def task_id(self) -> TaskId:
        self._value += 1
        return TaskId(f"TASK-{self._value}")

    def milestone_id(self) -> MilestoneId:
        self._value += 1
        return MilestoneId(f"MILESTONE-{self._value}")


def event(name: str, aggregate: str, version: int = 1) -> DomainEvent:
    return DomainEvent(name, aggregate, version, "synthetic-actor", NOW)


def seed_active(db: InMemoryDatabase, label: str = "P") -> Project:
    project = Project(ProjectId(label), "Projet synthétique", "alice", "alpha").plan().start(NOW)
    with db.unit_of_work() as unit:
        unit.add_project(project)
        unit.commit()
    return project


def test_arch06_rsac02_rollback_is_atomic_across_project_task_and_events() -> None:
    db = InMemoryDatabase()
    project = Project(ProjectId("P"), "Projet synthétique", "alice", "alpha")
    task = Task(TaskId("T"), project.id, "Tâche synthétique")
    with pytest.raises(RuntimeError, match="échec simulé"):
        with db.unit_of_work() as unit:
            unit.add_project(project)
            unit.add_task(task)
            unit.record(event("ProjectCreated", project.id.value))
            unit.record(event("TaskCreated", task.id.value))
            raise RuntimeError("échec simulé")
    with db.unit_of_work() as unit:
        assert unit.list_projects() == ()
        assert unit.list_tasks(project.id) == ()
    assert db.events == ()


def test_arch06_rsac02_implicit_exit_does_not_commit() -> None:
    db = InMemoryDatabase()
    with db.unit_of_work() as unit:
        unit.add_project(Project(ProjectId("P"), "Projet", "alice", "alpha"))
    with db.unit_of_work() as unit:
        assert unit.list_projects() == ()
    assert not db.events


def test_arch06_rsac03_stale_writes_fail_without_lost_update() -> None:
    db = InMemoryDatabase()
    seed_active(db)
    with db.unit_of_work() as first:
        with db.unit_of_work() as stale:
            first.save_project(first.get_project(ProjectId("P")).pause())
            first.record(event("ProjectPaused", "P", 4))
            first.commit()
            stale.save_project(stale.get_project(ProjectId("P")).complete(NOW))
            stale.record(event("ProjectCompleted", "P", 4))
            with pytest.raises(Conflict):
                stale.commit()
    with db.unit_of_work() as verify:
        result = verify.get_project(ProjectId("P"))
        assert result.status == ProjectStatus.ON_HOLD
        assert result.version == 4
    assert [x.name for x in db.events] == ["ProjectPaused"]


def test_arch06_rsac04_create_task_wins_over_stale_project_closure() -> None:
    db = InMemoryDatabase()
    project = seed_active(db)
    with db.unit_of_work() as closing:
        with db.unit_of_work() as creating:
            closing.save_project(closing.get_project(project.id).complete(NOW))
            closing.record(event("ProjectCompleted", "P", 4))
            creating.add_task(Task(TaskId("T"), project.id, "Concurrent"))
            creating.record(event("TaskCreated", "T"))
            creating.commit()
            with pytest.raises(Conflict):
                closing.commit()
    with db.unit_of_work() as verify:
        assert verify.get_project(project.id).status == ProjectStatus.ACTIVE
        assert len(verify.list_tasks(project.id)) == 1
    assert [x.name for x in db.events] == ["TaskCreated"]


def test_arch06_rsac04_project_closure_wins_over_stale_task_creation() -> None:
    db = InMemoryDatabase()
    project = seed_active(db)
    with db.unit_of_work() as creating:
        with db.unit_of_work() as closing:
            creating.add_task(Task(TaskId("T"), project.id, "Concurrent"))
            creating.record(event("TaskCreated", "T"))
            closing.save_project(closing.get_project(project.id).complete(NOW))
            closing.record(event("ProjectCompleted", "P", 4))
            closing.commit()
            with pytest.raises(Conflict):
                creating.commit()
    with db.unit_of_work() as verify:
        assert verify.get_project(project.id).status == ProjectStatus.COMPLETED
        assert verify.list_tasks(project.id) == ()
    assert [x.name for x in db.events] == ["ProjectCompleted"]


def test_arch06_rsac05_dependency_graph_remains_acyclic_after_refusal() -> None:
    db = InMemoryDatabase()
    project = seed_active(db)
    a, b, c = (TaskId("A"), TaskId("B"), TaskId("C"))
    with db.unit_of_work() as unit:
        for tid in (a, b, c):
            unit.add_task(Task(tid, project.id, "Étape " + tid.value))
        unit.add_dependency(project.id, Dependency(b, a))
        unit.add_dependency(project.id, Dependency(c, b))
        unit.commit()
    with pytest.raises(DependencyViolation):
        with db.unit_of_work() as unit:
            unit.add_dependency(project.id, Dependency(a, c))
    with db.unit_of_work() as unit:
        assert unit.list_dependencies(project.id) == (Dependency(b, a), Dependency(c, b))
    assert not db.events


def test_arch06_rsac05_cross_project_dependency_is_rejected_atomically() -> None:
    db = InMemoryDatabase()
    p1 = seed_active(db)
    p2 = seed_active(db, "SECOND")
    with db.unit_of_work() as unit:
        unit.add_task(Task(TaskId("A"), p1.id, "A"))
        unit.add_task(Task(TaskId("B"), p2.id, "B"))
        unit.commit()
    with pytest.raises(DependencyViolation):
        with db.unit_of_work() as unit:
            unit.add_dependency(p1.id, Dependency(TaskId("A"), TaskId("B")))
    with db.unit_of_work() as unit:
        assert unit.list_dependencies(p1.id) == ()
        assert unit.list_dependencies(p2.id) == ()


def test_arch06_rsac02_events_become_visible_only_after_confirmed_commit() -> None:
    db = InMemoryDatabase()
    with db.unit_of_work() as unit:
        unit.add_project(Project(ProjectId("P"), "Projet", "alice", "alpha"))
        unit.record(event("ProjectCreated", "P"))
        assert db.events == ()
        emitted = unit.commit()
        assert [x.name for x in emitted] == ["ProjectCreated"]
    assert [x.name for x in db.events] == ["ProjectCreated"]


def test_arch06_rsac02_second_commit_is_not_a_second_success() -> None:
    db = InMemoryDatabase()
    with db.unit_of_work() as unit:
        unit.add_project(Project(ProjectId("P"), "Projet", "alice", "alpha"))
        unit.record(event("ProjectCreated", "P"))
        unit.commit()
        with pytest.raises(Conflict):
            unit.commit()
    assert len(db.events) == 1


def test_arch06_rsac02_unrelated_event_without_mutation_is_refused() -> None:
    db = InMemoryDatabase()
    with db.unit_of_work() as unit:
        unit.record(event("PhantomSuccess", "P"))
        with pytest.raises(Conflict):
            unit.commit()
    assert db.events == ()


def test_arch06_rsac04_snapshot_does_not_observe_uncommitted_change() -> None:
    db = InMemoryDatabase()
    initial = Project(ProjectId("P"), "Projet", "alice", "alpha")
    with db.unit_of_work() as viewer:
        with db.unit_of_work() as editor:
            editor.add_project(initial)
            assert viewer.list_projects() == ()
            editor.commit()
        assert viewer.list_projects() == ()
    with db.unit_of_work() as fresh:
        assert fresh.get_project(initial.id) == initial


def test_arch06_rsac10_visibility_is_stable_when_hidden_projects_are_added() -> None:
    db = InMemoryDatabase()
    ids = SequenceIds()
    service = ProjectService(db.unit_of_work, clock=FrozenClock(), ids=ids,
                             authorization=OwnerScopePolicy())
    alice = ActorContext("alice", frozenset({"alpha"}))
    bob = ActorContext("bob", frozenset({"alpha", "beta"}))
    known = service.create_project(alice, "Visible", "alpha")
    before = service.list_projects(alice)
    outsider = service.create_project(bob, "Hidden same scope", "alpha")
    service.create_project(bob, "Hidden different scope", "beta")
    assert service.list_projects(alice) == before == (known,)
    with pytest.raises(NotFound, match="ressource indisponible"):
        service.get_project(alice, outsider.id)
    assert service.list_projects(bob) != before
