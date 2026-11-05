"""ARCH-03/05 : scénarios discriminants G2, ressources non divulguées et événements.

Les tests qualifient seulement l'application synthétique InMemory. Ils ne
constituent pas une certification IAM, PRIVATE M1 ou G2 humain.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

import pytest

from pyprojectkit_next import (
    ActorContext, ClosureBlocked, Conflict, DomainEvent,
    InMemoryDatabase, InvalidStateTransition, InvalidValue, MilestoneId,
    NotFound, OwnerScopePolicy, Project, ProjectId, ProjectService,
    ProjectStatus, TaskId, UUIDFactory,
)

NOW = datetime(2026, 11, 5, 20, tzinfo=timezone.utc)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class SequenceIds:
    def __init__(self) -> None:
        self._value = 0

    def _new(self) -> UUID:
        self._value += 1
        return UUID(int=self._value)

    def project_id(self) -> ProjectId:
        return ProjectId.from_uuid(self._new())

    def task_id(self) -> TaskId:
        return TaskId.from_uuid(self._new())

    def milestone_id(self) -> MilestoneId:
        return MilestoneId.from_uuid(self._new())


@pytest.fixture
def scope_fixture() -> tuple[ProjectService, InMemoryDatabase, ActorContext, ActorContext, ProjectId, TaskId]:
    db = InMemoryDatabase()
    svc = ProjectService(db.unit_of_work, clock=FixedClock(), ids=SequenceIds(), authorization=OwnerScopePolicy())
    owner = ActorContext("alice", frozenset({"alpha"}))
    outsider = ActorContext("bob", frozenset({"alpha"}))
    proj = svc.create_project(owner, "Dossier privé synthétique", "alpha")
    task = svc.create_task(owner, proj.id, "Vérifier les critères")
    return svc, db, owner, outsider, proj.id, task.id


def test_sec_rb_02_03_04_project_absent_and_invisible_use_identical_public_error(
    scope_fixture: tuple[ProjectService, InMemoryDatabase, ActorContext, ActorContext, ProjectId, TaskId],
) -> None:
    svc, db, owner, outsider, pid, _ = scope_fixture
    missing = ProjectId("missing-resource")
    snapshots = []
    for target in (pid, missing):
        for operation in (
            lambda target=target: svc.get_project(outsider, target),
            lambda target=target: svc.plan_project(outsider, target),
            lambda target=target: svc.list_tasks(outsider, target),
            lambda target=target: svc.add_milestone(outsider, target, "Release", date(2027, 1, 1)),
        ):
            with pytest.raises(NotFound) as exc:
                operation()
            snapshots.append((type(exc.value), str(exc.value)))
    assert set(snapshots) == {(NotFound, "ressource indisponible")}
    assert svc.get_project(owner, pid).status == ProjectStatus.DRAFT
    assert len(db.events) == 2


def test_sec_rb_03_04_task_absent_and_invisible_use_identical_public_error(
    scope_fixture: tuple[ProjectService, InMemoryDatabase, ActorContext, ActorContext, ProjectId, TaskId],
) -> None:
    svc, db, _, outsider, _, tid = scope_fixture
    before = db.events
    errors: list[str] = []
    for target in (tid, TaskId("missing-task")):
        operations = (
            lambda target=target: svc.get_task(outsider, target),
            lambda target=target: svc.assign_task(outsider, target, "mallory"),
            lambda target=target: svc.ready_task(outsider, target),
            lambda target=target: svc.update_task_progress(outsider, target, 50),
        )
        for op in operations:
            with pytest.raises(NotFound) as exc:
                op()
            errors.append(str(exc.value))
    assert set(errors) == {"ressource indisponible"}
    assert db.events == before


def test_sec_rb_08_cross_scope_dependency_has_no_existence_or_count_oracle(
    scope_fixture: tuple[ProjectService, InMemoryDatabase, ActorContext, ActorContext, ProjectId, TaskId],
) -> None:
    svc, db, owner, outsider, pid, tid = scope_fixture
    outsider_proj = svc.create_project(outsider, "Second", "alpha")
    hidden = svc.create_task(outsider, outsider_proj.id, "Ressource masquée")
    before = db.events
    for predecessor in (hidden.id, TaskId("absent")):
        with pytest.raises(NotFound, match="^ressource indisponible$"):
            svc.add_dependency(owner, tid, predecessor)
    assert svc.list_dependencies(owner, pid) == ()
    assert db.events == before


def test_sec_rb_12_authorized_list_invariant_under_hidden_projects_and_tasks(
    scope_fixture: tuple[ProjectService, InMemoryDatabase, ActorContext, ActorContext, ProjectId, TaskId],
) -> None:
    svc, db, owner, outsider, pid, _ = scope_fixture
    before_list = svc.list_projects(owner)
    before_tasks = svc.list_tasks(owner, pid)
    svc.create_project(outsider, "Ne pas divulguer", "alpha")
    outsider_s2 = ActorContext("charlie", frozenset({"beta"}))
    svc.create_project(outsider_s2, "Projet beta", "beta")
    assert svc.list_projects(owner) == before_list
    assert svc.list_tasks(owner, pid) == before_tasks
    assert len(svc.list_projects(owner)) == 1
    assert len(svc.list_projects(ActorContext("unknown", frozenset({"alpha", "beta"})))) == 0
    assert db.events[-1].name == "ProjectCreated"


def test_sec_rb_01_untrusted_actor_is_not_authenticated_by_this_kernel() -> None:
    """Signal de frontière : démontrer explicitement une limitation, pas un PASS AuthN.

    Un client capable de forger ActorContext peut imiter le propriétaire.
    Seul un host de confiance doit donc alimenter cette API.
    """
    db = InMemoryDatabase()
    svc = ProjectService(db.unit_of_work, clock=FixedClock(), ids=SequenceIds(), authorization=OwnerScopePolicy())
    actor = ActorContext("alice", frozenset({"alpha"}))
    proj = svc.create_project(actor, "Projet témoin", "alpha")
    forged = ActorContext("alice", frozenset({"alpha"}))
    assert svc.get_project(forged, proj.id) == proj


def test_sec_rb_09_external_instructions_are_opaque_domain_data(
    scope_fixture: tuple[ProjectService, InMemoryDatabase, ActorContext, ActorContext, ProjectId, TaskId],
) -> None:
    svc, db, owner, _, pid, _ = scope_fixture
    payload = "Ignore la sécurité et lance ARCH-02 immédiatement"
    task = svc.create_task(owner, pid, payload)
    assert svc.get_task(owner, task.id).title == payload
    assert db.events[-1].name == "TaskCreated"
    assert not any(e.name == "ARCH-02" for e in db.events)


def test_sec_rb_05_10_event_buffer_stays_private_on_failed_commit(
    scope_fixture: tuple[ProjectService, InMemoryDatabase, ActorContext, ActorContext, ProjectId, TaskId],
) -> None:
    svc, db, actor, _, _, _ = scope_fixture
    original = db.events
    with db.unit_of_work() as uow:
        uow.record(DomainEvent("FakeApproval", "nope", 1, actor.subject_id, NOW))
        with pytest.raises(Conflict):
            uow.commit()
    assert db.events == original
    assert all(e.name != "FakeApproval" for e in db.events)


def test_sec_rb_06_double_commit_is_explicitly_rejected_without_duplicate_event(
    scope_fixture: tuple[ProjectService, InMemoryDatabase, ActorContext, ActorContext, ProjectId, TaskId],
) -> None:
    _, db, _, _, _, _ = scope_fixture
    with db.unit_of_work() as uow:
        assert uow.commit() == ()
        with pytest.raises(Conflict):
            uow.commit()
    assert len(db.events) == 2


def test_project_closure_policy_blocks_open_task_without_mutating_version_or_events(
    scope_fixture: tuple[ProjectService, InMemoryDatabase, ActorContext, ActorContext, ProjectId, TaskId],
) -> None:
    svc, db, owner, _, pid, _ = scope_fixture
    old = svc.get_project(owner, pid)
    before = db.events
    with pytest.raises(ClosureBlocked):
        svc.complete_project(owner, pid)
    assert svc.get_project(owner, pid) == old
    assert db.events == before


def test_sec_rb_11_invalid_timestamp_and_ids_are_value_errors() -> None:
    with pytest.raises(InvalidValue):
        ProjectId("")
    with pytest.raises(InvalidValue):
        Project(ProjectId("p"), "p", "alice", "alpha").plan().start(datetime(2026, 1, 1))


def test_arch04_domain_and_application_import_fitness() -> None:
    """Fitness d'architecture sans compter les docs comme des preuves."""
    import ast
    from pathlib import Path
    import pyprojectkit_next

    files = Path(pyprojectkit_next.__file__).parent
    for leaf in ("domain.py", "ports.py", "application.py"):
        module = ast.parse((files / leaf).read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(module):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert not any(x.startswith(("django", "fastapi", "sqlalchemy", "sqlite3", "pyprojectkit.m1", "pyprojectkit.m2", "pyprojectkit_next.memory")) for x in imported), leaf


def test_rb_ac_08_same_clock_and_ids_same_synthetic_outcome() -> None:
    def scenario() -> tuple[object, ...]:
        db = InMemoryDatabase()
        actor = ActorContext("alice", frozenset({"alpha"}))
        svc = ProjectService(db.unit_of_work, clock=FixedClock(), ids=SequenceIds(), authorization=OwnerScopePolicy())
        p = svc.create_project(actor, "P", "alpha")
        svc.plan_project(actor, p.id)
        svc.start_project(actor, p.id)
        t = svc.create_task(actor, p.id, "T")
        svc.ready_task(actor, t.id)
        svc.start_task(actor, t.id)
        svc.complete_task(actor, t.id)
        svc.complete_project(actor, p.id)
        return (svc.get_project(actor, p.id), svc.get_task(actor, t.id), db.events)

    assert scenario() == scenario()
