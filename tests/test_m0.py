from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from functools import partial
from uuid import UUID

import pytest

from pyprojectkit import (
    AccessDenied, ActorContext, Conflict, DependencyViolation, ExplicitPolicy, FixedClock,
    InMemoryDatabase, InMemoryUnitOfWork, InvalidStateTransition, InvalidValue,
    NotFound, Project, ProjectId, ProjectService, ProjectStatus, Task, TaskId, TaskStatus,
)


NOW = datetime(2026, 11, 3, 12, tzinfo=timezone.utc)
ALL = {
    "PROJECT_CREATE", "PROJECT_VIEW", "PROJECT_PLAN", "PROJECT_START", "PROJECT_EDIT",
    "PROJECT_COMPLETE", "PROJECT_CANCEL", "TASK_CREATE", "TASK_VIEW", "TASK_EDIT",
    "TASK_ASSIGN", "TASK_START", "TASK_COMPLETE", "MILESTONE_CREATE", "MILESTONE_EDIT",
}


class FakeIDs:
    def __init__(self):
        self.i = 0

    def new(self) -> UUID:
        self.i += 1
        return UUID(int=self.i)


@pytest.fixture
def env():
    db = InMemoryDatabase()
    ids = FakeIDs()
    actor = ActorContext("owner", "team")
    policy = ExplicitPolicy({"owner": ALL, "reader": {"PROJECT_VIEW", "TASK_VIEW"}, "other": ALL})
    service = ProjectService(partial(InMemoryUnitOfWork, db), policy, FixedClock(NOW), ids)
    return db, actor, service


def project_active(env):
    db, actor, service = env
    pid = service.create_project(actor, "Projet", "owner")
    service.transition_project(actor, pid, ProjectStatus.PLANNED)
    service.transition_project(actor, pid, ProjectStatus.ACTIVE)
    return pid


def test_ac001_project_creation_without_tasks(env):
    db, actor, service = env
    pid = service.create_project(actor, "Projet", "owner")
    assert service.get_project(actor, pid).status == ProjectStatus.DRAFT
    assert service.list_tasks(actor, pid) == []
    assert db.events[-1].name == "ProjectCreated"


def test_ac002_invalid_project_state_and_complete_policy(env):
    db, actor, service = env
    pid = service.create_project(actor, "Projet", "owner")
    before = len(db.events)
    with pytest.raises(InvalidStateTransition):
        service.transition_project(actor, pid, ProjectStatus.COMPLETED)
    assert len(db.events) == before
    service.transition_project(actor, pid, ProjectStatus.PLANNED)
    service.transition_project(actor, pid, ProjectStatus.ACTIVE)
    tid = service.create_task(actor, pid, "Ouverte")
    with pytest.raises(InvalidStateTransition):
        service.transition_project(actor, pid, ProjectStatus.COMPLETED)
    service.transition_task(actor, tid, TaskStatus.READY)
    service.transition_task(actor, tid, TaskStatus.IN_PROGRESS)
    service.transition_task(actor, tid, TaskStatus.DONE)
    service.transition_project(actor, pid, ProjectStatus.COMPLETED)
    assert service.get_project(actor, pid).actual_end_at == NOW


def test_ac003_lifecycle_assign_block_unblock_review_and_done(env):
    db, actor, service = env
    pid = project_active(env)
    tid = service.create_task(actor, pid, "Développer")
    service.assign_task(actor, tid, "dev")
    service.transition_task(actor, tid, TaskStatus.READY)
    service.transition_task(actor, tid, TaskStatus.IN_PROGRESS)
    service.transition_task(actor, tid, TaskStatus.BLOCKED, reason="Attente")
    assert service.get_task(actor, tid).block_reason == "Attente"
    with pytest.raises(InvalidStateTransition):
        service.transition_task(actor, tid, TaskStatus.DONE)
    service.transition_task(actor, tid, TaskStatus.IN_PROGRESS)
    service.transition_task(actor, tid, TaskStatus.IN_REVIEW)
    service.transition_task(actor, tid, TaskStatus.DONE)
    assert service.get_task(actor, tid).progress == 100
    assert service.get_task(actor, tid).actual_end_at == NOW
    before = len(db.events)
    with pytest.raises(InvalidStateTransition):
        service.transition_task(actor, tid, TaskStatus.DONE)
    assert len(db.events) == before


def test_ac004_ac005_dependency_guards_and_cycles(env):
    db, actor, service = env
    pid = project_active(env)
    a, b, c = [service.create_task(actor, pid, name) for name in ("A", "B", "C")]
    service.add_dependency(actor, b, a)
    service.add_dependency(actor, c, b)
    before_events = len(db.events)
    with pytest.raises(DependencyViolation):
        service.add_dependency(actor, a, c)
    with pytest.raises(DependencyViolation):
        service.add_dependency(actor, a, a)
    assert len(db.events) == before_events
    service.transition_task(actor, c, TaskStatus.READY)
    with pytest.raises(DependencyViolation):
        service.transition_task(actor, c, TaskStatus.IN_PROGRESS)
    service.transition_task(actor, a, TaskStatus.READY)
    service.transition_task(actor, a, TaskStatus.IN_PROGRESS)
    service.transition_task(actor, a, TaskStatus.DONE)
    service.transition_task(actor, b, TaskStatus.READY)
    service.transition_task(actor, b, TaskStatus.IN_PROGRESS)
    service.transition_task(actor, b, TaskStatus.DONE)
    service.transition_task(actor, c, TaskStatus.IN_PROGRESS)
    assert service.get_task(actor, c).status == TaskStatus.IN_PROGRESS


def test_ac006_milestones_and_dates(env):
    db, actor, service = env
    pid = service.create_project(actor, "Avec jalon", "owner")
    mid = service.add_milestone(actor, pid, "Release", date(2027, 1, 1))
    service.reach_milestone(actor, pid, mid)
    assert service.get_project(actor, pid).milestones[mid].reached_at == NOW
    with pytest.raises(InvalidStateTransition):
        service.reach_milestone(actor, pid, mid)
    with pytest.raises(InvalidValue):
        service.add_milestone(actor, pid, "", date(2027, 1, 1))


def test_ac007_ids_clock_determinism(env):
    db, actor, service = env
    pid = service.create_project(actor, "X", "owner")
    tid = service.create_task(actor, pid, "T")
    assert pid.value == UUID(int=1)
    assert tid.value == UUID(int=2)
    assert db.events[0].occurred_at == NOW


def test_ac008_repository_copy_isolation_rollback_and_atomicity(env):
    db, actor, service = env
    pid = service.create_project(actor, "Initial", "owner")
    with InMemoryUnitOfWork(db) as tx:
        item = tx.projects.get(pid)
        assert item is not None
        item.name = "Muté sans save"
    assert service.get_project(actor, pid).name == "Initial"
    with InMemoryUnitOfWork(db) as tx:
        item = tx.projects.get(pid)
        assert item is not None
        item.name = "Muté avec save sans commit"
        tx.projects.save(item, expected_version=item.version)
    assert service.get_project(actor, pid).name == "Initial"
    tid = TaskId(UUID(int=500))
    with pytest.raises(RuntimeError):
        with InMemoryUnitOfWork(db) as tx:
            tx.projects.add(Project(ProjectId(UUID(int=600)), "Autre", "owner", "team"))
            tx.tasks.add(Task(tid, pid, "T"))
            raise RuntimeError("panne simulée")
    assert tid not in db.tasks
    assert ProjectId(UUID(int=600)) not in db.projects
    with InMemoryUnitOfWork(db) as tx:
        item = tx.projects.get(pid)
        assert item is not None
        item.name = "Enregistré"
        tx.projects.save(item, expected_version=item.version)
        tx.commit()
    assert service.get_project(actor, pid).name == "Enregistré"


def test_ac008_optimistic_conflict_preserves_global_state(env):
    db, actor, service = env
    pid = service.create_project(actor, "Projet", "owner")
    with InMemoryUnitOfWork(db) as left:
        l = left.projects.get(pid)
        with InMemoryUnitOfWork(db) as right:
            r = right.projects.get(pid)
            assert r is not None
            r.name = "Right"
            right.projects.save(r, expected_version=r.version)
            right.commit()
        assert l is not None
        l.name = "Left"
        left.projects.save(l, expected_version=l.version)
        with pytest.raises(Conflict):
            left.commit()
    assert service.get_project(actor, pid).name == "Right"


def test_ac008_graph_concurrent_writes_cannot_create_cycle(env):
    db, actor, service = env
    pid = project_active(env)
    a = service.create_task(actor, pid, "A")
    b = service.create_task(actor, pid, "B")
    from pyprojectkit import Dependency
    with InMemoryUnitOfWork(db) as left:
        vl, gl = left.dependencies.snapshot(pid)
        left.dependencies.replace_if_version(pid, expected_version=vl, edges=gl | {Dependency(a, b)})
        with InMemoryUnitOfWork(db) as right:
            vr, gr = right.dependencies.snapshot(pid)
            right.dependencies.replace_if_version(pid, expected_version=vr, edges=gr | {Dependency(b, a)})
            right.commit()
        with pytest.raises(Conflict):
            left.commit()
    _, result = db.graphs[pid]
    assert result == {Dependency(b, a)}


def test_ac009_events_only_after_confirmed_commit(env):
    db, actor, service = env
    with InMemoryUnitOfWork(db) as tx:
        tx.record(service._event("TestPending", "1", actor))
        assert db.events == []
    assert db.events == []
    with InMemoryUnitOfWork(db) as tx:
        tx.record(service._event("TestCommitted", "1", actor))
        tx.commit()
        assert db.events[-1].name == "TestCommitted"


def test_ac010_architecture_imports_without_infrastructure():
    from pathlib import Path
    package_dir = Path(__file__).parents[1] / "src" / "pyprojectkit"
    for path in package_dir.glob("*.py"):
        text = path.read_text()
        for forbidden in ("import fastapi", "import django", "import sqlalchemy", "import psycopg", "import pyagentskit", "import pythos"):
            assert forbidden not in text.lower(), (path, forbidden)


def test_security_denies_commands_queries_and_scope(env):
    db, actor, service = env
    pid = service.create_project(actor, "Secret", "owner")
    tid = service.create_task(actor, pid, "Secret Task")
    reader = ActorContext("reader", "team")
    assert service.get_project(reader, pid).id == pid
    with pytest.raises(AccessDenied):
        service.create_project(reader, "Inconnu", "reader")
    with pytest.raises(AccessDenied):
        service.assign_task(reader, tid, "reader")
    outsider = ActorContext("other", "another-scope")
    assert service.list_projects(outsider) == []
    with pytest.raises(NotFound):
        service.get_project(outsider, pid)
    with pytest.raises(NotFound):
        service.get_task(outsider, tid)
    with pytest.raises(AccessDenied):
        service.get_project(ActorContext("unknown", "team"), pid)


def test_scope_prevents_cross_project_dependency(env):
    db, actor, service = env
    a = service.create_project(actor, "A", "owner")
    b = service.create_project(actor, "B", "owner")
    ta = service.create_task(actor, a, "a")
    tb = service.create_task(actor, b, "b")
    with pytest.raises(DependencyViolation):
        service.add_dependency(actor, ta, tb)


def test_concurrent_create_task_conflicts_with_project_closure(env):
    db, actor, service = env
    pid = project_active(env)
    # Force both transactions to observe the same Project state.
    with InMemoryUnitOfWork(db) as create_tx:
        parent = create_tx.projects.get(pid)
        assert parent is not None
        child = Task(TaskId(UUID(int=900)), pid, "Concurrent")
        create_tx.projects.save(parent, expected_version=parent.version)
        create_tx.tasks.add(child)
        with InMemoryUnitOfWork(db) as close_tx:
            p = close_tx.projects.get(pid)
            assert p is not None
            p.transition(ProjectStatus.COMPLETED, NOW)
            close_tx.projects.save(p, expected_version=p.version)
            close_tx.commit()
        with pytest.raises(Conflict):
            create_tx.commit()
    assert service.get_project(actor, pid).status == ProjectStatus.COMPLETED
    assert TaskId(UUID(int=900)) not in db.tasks


def test_project_completion_detects_concurrent_task_change(env):
    db, actor, service = env
    pid = project_active(env)
    tid = service.create_task(actor, pid, "Déjà terminée")
    service.transition_task(actor, tid, TaskStatus.READY)
    service.transition_task(actor, tid, TaskStatus.IN_PROGRESS)
    service.transition_task(actor, tid, TaskStatus.DONE)
    with InMemoryUnitOfWork(db) as left:
        p = left.projects.get(pid)
        seen_tasks = left.tasks.list_all()
        assert len(seen_tasks) == 1
        assert p is not None
        p.transition(ProjectStatus.COMPLETED, NOW)
        left.projects.save(p, expected_version=p.version)
        with InMemoryUnitOfWork(db) as right:
            t = right.tasks.get(tid)
            assert t is not None
            # Simulate concurrent service that changes task metadata.
            t.title = "Modifiée"
            right.tasks.save(t, expected_version=t.version)
            right.commit()
        with pytest.raises(Conflict):
            left.commit()
    assert service.get_project(actor, pid).status == ProjectStatus.ACTIVE


def test_manual_store_mutation_isolation(env):
    db, actor, service = env
    pid = service.create_project(actor, "P", "owner")
    fetched = service.get_project(actor, pid)
    fetched.name = "Surprise"
    assert service.get_project(actor, pid).name == "P"
    task = service.create_task(actor, pid, "T")
    fetched_task = service.get_task(actor, task)
    fetched_task.title = "Surprise"
    assert service.get_task(actor, task).title == "T"


def test_graph_cross_scope_no_event_or_edge(env):
    db, actor, service = env
    a = service.create_project(actor, "Team A", "owner")
    t_a = service.create_task(actor, a, "Ta")
    outsider = ActorContext("other", "other-scope")
    b = service.create_project(outsider, "Team B", "other")
    t_b = service.create_task(outsider, b, "Tb")
    start = len(db.events)
    with pytest.raises(NotFound):
        service.add_dependency(actor, t_a, t_b)
    assert len(db.events) == start
    assert db.graphs == {}