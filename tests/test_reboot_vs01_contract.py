"""Qualification VS01 : frontières publiques, UUID et parité M0 démontrable.

La comparaison M0 historique s'exécute dans la CI du dépôt complet ; le sous-arbre
local isolé peut exécuter les tests autonomes sans disposer du package legacy.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

import pytest

from pyprojectkit_next import (
    AccessDenied, ActorContext, InMemoryDatabase, InvalidValue, Milestone,
    MilestoneId, OwnerScopePolicy, Project, ProjectId, ProjectService,
    ProjectStatus, Task, TaskId, TaskStatus, UUIDFactory,
)

NOW = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)


class Clock:
    def now(self) -> datetime:
        return NOW


class Ids:
    def __init__(self) -> None:
        self.value = 0

    def new(self) -> UUID:
        self.value += 1
        return UUID(int=self.value)

    def project_id(self) -> ProjectId:
        return ProjectId.from_uuid(self.new())

    def task_id(self) -> TaskId:
        return TaskId.from_uuid(self.new())

    def milestone_id(self) -> MilestoneId:
        return MilestoneId.from_uuid(self.new())


def test_list_projects_is_scoped_by_owner_and_scope_and_read_only() -> None:
    db = InMemoryDatabase()
    svc = ProjectService(db.unit_of_work, clock=Clock(), ids=Ids(), authorization=OwnerScopePolicy())
    owner_alpha = ActorContext('owner', frozenset({'alpha'}))
    owner_beta = ActorContext('owner', frozenset({'beta'}))
    outsider = ActorContext('other', frozenset({'alpha', 'beta'}))
    a = svc.create_project(owner_alpha, 'Alpha', 'alpha')
    b = svc.create_project(owner_beta, 'Beta', 'beta')
    original_events = db.events
    assert svc.list_projects(owner_alpha) == (a,)
    assert svc.list_projects(owner_beta) == (b,)
    assert svc.list_projects(ActorContext('owner', frozenset({'alpha', 'beta'}))) == (a, b)
    assert svc.list_projects(outsider) == ()
    assert db.events == original_events
    for actor in (ActorContext('', frozenset({'alpha'})), ActorContext('owner', frozenset())):
        with pytest.raises(AccessDenied):
            svc.list_projects(actor)


@pytest.mark.parametrize('cls', [ProjectId, TaskId, MilestoneId])
def test_uuid_boundary_roundtrip_and_explicit_rejections(cls: type[ProjectId] | type[TaskId] | type[MilestoneId]) -> None:
    identifier = UUID('aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee')
    domain_id = cls.from_uuid(identifier)
    assert domain_id.to_uuid() == identifier
    assert domain_id.value == str(identifier)
    with pytest.raises(InvalidValue):
        cls.from_uuid('not-a-uuid')  # type: ignore[arg-type]
    with pytest.raises(InvalidValue):
        cls('synthetic').to_uuid()
    with pytest.raises(InvalidValue):
        cls(str(identifier).upper()).to_uuid()


def test_factory_generates_uuid_compatible_ids() -> None:
    ids = UUIDFactory()
    for identifier in (ids.project_id(), ids.task_id(), ids.milestone_id()):
        assert isinstance(identifier.to_uuid(), UUID)


@pytest.mark.parametrize('invalid', [None, datetime(2026, 1, 1), '2026-01-01'])
def test_domain_transitions_reject_non_aware_timestamps(invalid: object) -> None:
    project = Project(ProjectId('p'), 'Projet', 'owner', 'scope').plan()
    with pytest.raises(InvalidValue):
        project.start(invalid)  # type: ignore[arg-type]
    with pytest.raises(InvalidValue):
        project.start(NOW).complete(invalid)  # type: ignore[arg-type]
    task = Task(TaskId('t'), ProjectId('p'), 'Tache').ready()
    with pytest.raises(InvalidValue):
        task.start(invalid)  # type: ignore[arg-type]
    with pytest.raises(InvalidValue):
        task.start(NOW).complete(invalid)  # type: ignore[arg-type]
    with pytest.raises(InvalidValue):
        task.start(NOW).block('attente').unblock(invalid)  # type: ignore[arg-type]
    with pytest.raises(InvalidValue):
        Milestone(MilestoneId('m'), 'Jalon', date(2027, 1, 1)).reach(invalid)  # type: ignore[arg-type]


@pytest.mark.parametrize('factory', [
    lambda: Project('wrong', 'Projet', 'owner', 'scope'),
    lambda: Task('wrong', ProjectId('p'), 'Tache'),
    lambda: Task(TaskId('t'), 'wrong', 'Tache'),
    lambda: Milestone('wrong', 'Jalon', date(2027, 1, 1)),
])
def test_invalid_identifier_types_fail_early(factory: object) -> None:
    with pytest.raises(InvalidValue):
        factory()  # type: ignore[operator]


def test_differential_core_scenario_against_legacy_m0() -> None:
    """Comparer la sémantique métier commune, pas les signatures ni event labels."""
    pytest.importorskip('pyprojectkit')
    from pyprojectkit.domain import ProjectStatus as OldProjectStatus
    from pyprojectkit.domain import TaskStatus as OldTaskStatus
    from pyprojectkit.memory import InMemoryDatabase as OldDatabase
    from pyprojectkit.memory import InMemoryUnitOfWork as OldUnitOfWork
    from pyprojectkit.ports import ActorContext as OldActorContext
    from pyprojectkit.service import ExplicitPolicy, ProjectService as OldService

    old_db = OldDatabase()
    old_ids = Ids()
    old_svc = OldService(
        lambda: OldUnitOfWork(old_db),
        ExplicitPolicy({'owner': {
            'PROJECT_CREATE', 'PROJECT_VIEW', 'PROJECT_PLAN', 'PROJECT_START', 'PROJECT_COMPLETE',
            'TASK_CREATE', 'TASK_VIEW', 'TASK_EDIT', 'TASK_START', 'TASK_COMPLETE',
            'MILESTONE_CREATE', 'MILESTONE_EDIT',
        }}), clock=Clock(), ids=old_ids,
    )
    new_db = InMemoryDatabase()
    new_svc = ProjectService(new_db.unit_of_work, clock=Clock(), ids=Ids(), authorization=OwnerScopePolicy())
    oa = OldActorContext('owner', 'scope')
    na = ActorContext('owner', frozenset({'scope'}))
    old_id = old_svc.create_project(oa, 'Projet', 'owner')
    new_project = new_svc.create_project(na, 'Projet', 'scope')
    assert old_id.value == new_project.id.to_uuid()
    assert old_svc.get_project(oa, old_id).status.value == new_project.status.value
    old_svc.transition_project(oa, old_id, OldProjectStatus.PLANNED)
    new_svc.plan_project(na, new_project.id)
    old_svc.transition_project(oa, old_id, OldProjectStatus.ACTIVE)
    new_svc.start_project(na, new_project.id)
    old_milestone_id = old_svc.add_milestone(oa, old_id, 'Jalon', date(2027, 1, 1))
    milestone = new_svc.add_milestone(na, new_project.id, 'Jalon', date(2027, 1, 1))
    assert old_milestone_id.value == milestone.id.to_uuid()
    old_svc.reach_milestone(oa, old_id, old_milestone_id)
    new_svc.reach_milestone(na, new_project.id, milestone.id)
    old_task_id = old_svc.create_task(oa, old_id, 'Tache')
    new_task = new_svc.create_task(na, new_project.id, 'Tache')
    assert old_task_id.value == new_task.id.to_uuid()
    for old_status, run in (
        (OldTaskStatus.READY, new_svc.ready_task),
        (OldTaskStatus.IN_PROGRESS, new_svc.start_task),
        (OldTaskStatus.DONE, new_svc.complete_task),
    ):
        old_svc.transition_task(oa, old_task_id, old_status)
        new_status = run(na, new_task.id).status
        assert old_svc.get_task(oa, old_task_id).status.value == new_status.value
    old_svc.transition_project(oa, old_id, OldProjectStatus.COMPLETED)
    new_svc.complete_project(na, new_project.id)
    op = old_svc.get_project(oa, old_id)
    np = new_svc.get_project(na, new_project.id)
    assert (op.status.value, op.actual_start_at, op.actual_end_at) == (
        np.status.value, np.actual_start_at, np.actual_end_at,
    )
    assert op.milestones[old_milestone_id].reached_at == np.get_milestone(milestone.id).reached_at
    assert new_svc.get_task(na, new_task.id).status == TaskStatus.DONE
    assert len(old_db.events) == len(new_db.events)
    assert np.status == ProjectStatus.COMPLETED
