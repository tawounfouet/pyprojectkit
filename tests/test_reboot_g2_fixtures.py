"""Oracles ARCH-03 lisibles et exécutables, sans données réelles."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import pytest

from pyprojectkit_next import (
    ActorContext, ClosureBlocked, InMemoryDatabase, NotFound,
    OwnerScopePolicy, ProjectId, ProjectService, TaskId, MilestoneId,
)

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic" / "g2_acceptance_cases.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]
NOW = datetime(2026, 11, 5, 20, tzinfo=timezone.utc)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class Ids:
    def __init__(self) -> None:
        self.number = 0

    def _new(self) -> str:
        self.number += 1
        return str(UUID(int=self.number))

    def project_id(self) -> ProjectId:
        return ProjectId(self._new())

    def task_id(self) -> TaskId:
        return TaskId(self._new())

    def milestone_id(self) -> MilestoneId:
        return MilestoneId(self._new())


@pytest.mark.parametrize("case", CASES, ids=lambda x: x["id"])
def test_arch03_synthetic_oracles(case: dict[str, str]) -> None:
    db = InMemoryDatabase()
    actor = ActorContext("alice", frozenset({case["scope"]}))
    service = ProjectService(db.unit_of_work, clock=FixedClock(), ids=Ids(), authorization=OwnerScopePolicy())
    p = service.create_project(actor, case["name"], case["scope"])
    kind = case["kind"]
    if kind == "create_draft":
        assert p.status.value == case["expected_status"]
    elif kind == "lifecycle":
        service.plan_project(actor, p.id)
        assert service.start_project(actor, p.id).status.value == case["expected_status"]
    elif kind == "invalid_complete":
        # Le cas utilise une tâche ouverte afin de discriminer la policy de clôture.
        service.create_task(actor, p.id, "À finir")
        with pytest.raises(ClosureBlocked) as error:
            service.complete_project(actor, p.id)
        assert error.value.code == case["expected_error"]
    elif kind == "cross_owner":
        with pytest.raises(NotFound) as error:
            service.get_project(ActorContext("other", frozenset({case["scope"]})), p.id)
        assert error.value.code == case["expected_error"]
    elif kind == "clock_determinism":
        assert db.events[0].occurred_at.isoformat() == case["expected_occurred_at"]
    else:
        raise AssertionError(f"unknown oracle kind: {kind}")
    assert db.events[0].name == "ProjectCreated"


def test_arch03_fixture_is_synthetic_and_ids_are_unique() -> None:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert document["classification"] == "SYNTHETIC_ONLY"
    assert document["schema"].endswith(".v1")
    ids = [case["id"] for case in document["cases"]]
    assert len(ids) == len(set(ids))
