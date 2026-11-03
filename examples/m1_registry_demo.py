"""Parcours M1 synthétique : 5 familles, preuves, snapshot et reprise après restart."""
from __future__ import annotations

from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory

from uuid import UUID

from pyprojectkit import ExplicitPolicy, ProjectId, ProjectService
from pyprojectkit.m1 import AssessmentResult, Family, RegistryService, SqliteDatabase, SqliteUnitOfWork, TrustedHost

P = {"SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "TASK_CREATE", "TASK_VIEW", "TASK_EDIT", "TASK_START",
     "WRITE_OBSERVATION", "READ_OBSERVATION", "WRITE_EVIDENCE", "READ_EVIDENCE", "ASSESS", "WRITE_ASSESSMENT",
     "READ_ASSESSMENT", "WRITE_DECISION", "READ_DECISION", "WRITE_APPROVAL", "READ_APPROVAL", "APPROVE",
     "WRITE_SNAPSHOT", "READ_SNAPSHOT", "CAPTURE", "WRITE_HANDOFF", "READ_HANDOFF", "RESUME"}


def main() -> None:
    with TemporaryDirectory() as temp:
        file = Path(temp) / "pilot.sqlite"
        host = TrustedHost({"synthetic-credential": ("demo-owner", {"demo-projects": P})})
        actor = host.authenticate("synthetic-credential", "demo-projects")
        db = SqliteDatabase(file)
        registry = RegistryService(db, host)
        registry.create_scope(actor)
        projects = {family.value: registry.register_project(actor, f"Example {family.value}", family.value)
                    for family in Family}
        main_id = projects["PACKAGE"]
        m0 = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"demo-owner": P}))
        task = m0.create_task(actor.legacy(), ProjectId(UUID(main_id)), "Implement M1")
        evidence = registry.attach_evidence(actor, main_id, target_ref="repo", revision="sha-example",
                                            source_ref="synthetic-ci") if "WRITE_EVIDENCE" in P else ""
        registry.assess(actor, main_id, evidence_id=evidence, target_ref="repo", revision="sha-example",
                        criterion="CI", result=AssessmentResult.PASS, method="synthetic-tests")
        registry.observe(actor, main_id, subject="CI", value="passed", source_ref="synthetic-ci",
                         observed_at=datetime.now(timezone.utc))
        decision = registry.record_decision(actor, main_id, subject="M1", statement="Use SQLite pilot")
        registry.approve_decision(actor, main_id, decision)
        registry.capture_snapshot(actor, main_id)
        registry.record_handoff(actor, main_id, summary="Work in progress", outcome="REVIEW",
                                unknowns=["Q-M1 not assessed"])
        del db
        resumed = RegistryService(SqliteDatabase(file), host).resume(actor, main_id)
        assert resumed.latest_snapshot is not None
        assert resumed.latest_handoff is not None
        assert resumed.next_action.task_id == str(task.value)
        print(f"families={len(projects)} tasks_open={len(resumed.open_tasks)} snapshot=yes handoff=yes next_action={resumed.next_action.task_id}")


if __name__ == "__main__":
    main()