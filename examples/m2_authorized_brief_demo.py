"""VS-M2-01: démonstration locale synthétique, sans Pythos ni secrets."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from pyprojectkit import ExplicitPolicy, FixedClock, ProjectId, ProjectService
from pyprojectkit.m1 import RegistryService, SqliteDatabase, SqliteUnitOfWork, TrustedHost
from pyprojectkit.m2 import (
    BuildAuthorizedOperatingBrief, BuildBriefRequest, DelegationMandate,
    ExactTargetReference, InMemoryMandateStore, MandateVerifier, WorkItemRef,
)


def main() -> None:
    now = datetime(2026, 11, 4, 12, tzinfo=timezone.utc)
    grants = {"SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "TASK_CREATE", "TASK_VIEW", "BRIEF_BUILD"}
    with TemporaryDirectory() as temp:
        db = SqliteDatabase(Path(temp) / "m2a-pilot.sqlite")
        host = TrustedHost({"synthetic": ("pilot-owner", {"synthetic": grants})})
        actor = host.authenticate("synthetic", "synthetic")
        registry = RegistryService(db, host, FixedClock(now))
        registry.create_scope(actor)
        pid = registry.register_project(actor, "Projet de démonstration", "PACKAGE")
        core = ProjectService(partial(SqliteUnitOfWork, db),
                              ExplicitPolicy({"pilot-owner": grants}), FixedClock(now))
        task = core.create_task(actor.legacy(), ProjectId(UUID(pid)), "Audit de tâche fictive")
        work = WorkItemRef("TASK", str(task.value))
        target = ExactTargetReference("GIT_COMMIT", "demo/repo", "a" * 40)
        mandates = InMemoryMandateStore()
        mandates.provision(DelegationMandate(
            "mandate-demo", "pilot-owner", "pythos", "synthetic", pid, work,
            "AUDIT", "A0", ("PROJECT_VIEW", "TASK_VIEW"), target,
            now - timedelta(minutes=1), now + timedelta(minutes=30),
        ))
        service = BuildAuthorizedOperatingBrief(
            registry, MandateVerifier(host, mandates), FixedClock(now)
        )
        brief = service.execute(actor, BuildBriefRequest("mandate-demo", pid, work, "AUDIT", target))
        assert brief.allowed_actions == ("PROJECT_VIEW", "TASK_VIEW")
        assert brief.mode == "AUDIT"
        print("VS-M2-01 OK: brief v1, lecture autorisée, aucune exécution Pythos")
        print(brief.to_json())


if __name__ == "__main__":
    main()
