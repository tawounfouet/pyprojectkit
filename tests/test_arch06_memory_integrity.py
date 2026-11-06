"""ARCH-06 : caractérisation des invariants UoW au point de commit.

Ces tests ne qualifient ni la durabilité SQLite ni les gates G1/G2.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pyprojectkit_next import (
    ClosureBlocked, DomainEvent, InMemoryDatabase, InvalidStateTransition,
    Project, ProjectId, ProjectStatus, Task, TaskId, TaskStatus,
)

NOW = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)


def active_project(pid: str = "P") -> Project:
    return Project(ProjectId(pid), "Projet", "owner", "scope").plan().start(NOW)


def record(name: str, aggregate: str, version: int) -> DomainEvent:
    return DomainEvent(name, aggregate, version, "owner", NOW)


def seed(db: InMemoryDatabase, *, task_count: int = 1) -> Project:
    project = active_project()
    with db.unit_of_work() as unit:
        unit.add_project(project)
        for n in range(task_count):
            unit.add_task(Task(TaskId(f"T-{n}"), project.id, "Étape"))
        unit.commit()
    return project


def test_uow_rejects_task_creation_on_completed_parent() -> None:
    db = InMemoryDatabase()
    project = seed(db, task_count=0)
    with db.unit_of_work() as unit:
        unit.save_project(project.complete(NOW))
        unit.commit()
    with db.unit_of_work() as unit:
        with pytest.raises(InvalidStateTransition, match="projet terminal"):
            unit.add_task(Task(TaskId("late"), project.id, "Tardive"))
    with db.unit_of_work() as unit:
        assert unit.list_tasks(project.id) == ()
        assert unit.get_project(project.id).status == ProjectStatus.COMPLETED


def test_uow_rejects_task_creation_on_cancelled_parent() -> None:
    db = InMemoryDatabase()
    project = seed(db, task_count=0)
    with db.unit_of_work() as unit:
        unit.save_project(project.cancel())
        unit.commit()
    with db.unit_of_work() as unit:
        with pytest.raises(InvalidStateTransition, match="projet terminal"):
            unit.add_task(Task(TaskId("late"), project.id, "Tardive"))


def test_commit_blocks_open_task_and_discards_pending_event() -> None:
    db = InMemoryDatabase()
    project = seed(db)
    with db.unit_of_work() as unit:
        unit.save_project(project.complete(NOW))
        unit.record(record("ProjectCompleted", project.id.value, project.version + 1))
        with pytest.raises(ClosureBlocked, match="tâches ouvertes"):
            unit.commit()
    with db.unit_of_work() as unit:
        assert unit.get_project(project.id).status == ProjectStatus.ACTIVE
        assert unit.get_task(TaskId("T-0")).status == TaskStatus.TODO
    assert db.events == ()


def test_commit_allows_coordinated_task_and_project_completion() -> None:
    db = InMemoryDatabase()
    project = seed(db)
    with db.unit_of_work() as unit:
        task = unit.get_task(TaskId("T-0"))
        unit.save_task(task.ready())
        unit.save_task(unit.get_task(task.id).start(NOW))
        finished = unit.get_task(task.id).complete(NOW)
        unit.save_task(finished)
        unit.save_project(project.complete(NOW))
        unit.record(record("TaskCompleted", task.id.value, finished.version))
        unit.record(record("ProjectCompleted", project.id.value, project.version + 1))
        events = unit.commit()
    assert [e.name for e in events] == ["TaskCompleted", "ProjectCompleted"]
    assert db.events == events
    with db.unit_of_work() as unit:
        assert unit.get_task(TaskId("T-0")).status == TaskStatus.DONE
        assert unit.get_project(project.id).status == ProjectStatus.COMPLETED


def test_completed_and_cancelled_tasks_both_allow_closure() -> None:
    db = InMemoryDatabase()
    project = seed(db, task_count=2)
    with db.unit_of_work() as unit:
        first = unit.get_task(TaskId("T-0"))
        unit.save_task(first.ready())
        unit.save_task(unit.get_task(first.id).start(NOW))
        unit.save_task(unit.get_task(first.id).complete(NOW))
        unit.save_task(unit.get_task(TaskId("T-1")).cancel())
        unit.save_project(project.complete(NOW))
        unit.commit()
    with db.unit_of_work() as unit:
        assert unit.get_project(project.id).status == ProjectStatus.COMPLETED
        assert {t.status for t in unit.list_tasks(project.id)} == {
            TaskStatus.DONE, TaskStatus.CANCELLED,
        }


def test_failed_commit_is_atomic_across_other_project_and_journal() -> None:
    db = InMemoryDatabase()
    p1 = seed(db)
    p2 = active_project("Q")
    with db.unit_of_work() as unit:
        unit.add_project(p2)
        unit.record(record("ProjectCreated", "Q", 3))
        unit.commit()
    baseline = db.events
    with db.unit_of_work() as unit:
        unit.save_project(p1.complete(NOW))
        unit.save_project(p2.pause())
        unit.record(record("ProjectPaused", "Q", 4))
        with pytest.raises(ClosureBlocked):
            unit.commit()
    with db.unit_of_work() as unit:
        assert unit.get_project(p1.id).status == ProjectStatus.ACTIVE
        assert unit.get_project(p2.id).status == ProjectStatus.ACTIVE
    assert db.events == baseline


def test_commit_validates_final_snapshot_not_intermediate_state() -> None:
    db = InMemoryDatabase()
    project = seed(db)
    with db.unit_of_work() as unit:
        unit.save_project(project.complete(NOW))
        unit.save_task(unit.get_task(TaskId("T-0")).cancel())
        unit.commit()
    with db.unit_of_work() as unit:
        assert unit.get_project(project.id).status == ProjectStatus.COMPLETED
        assert unit.get_task(TaskId("T-0")).status == TaskStatus.CANCELLED
