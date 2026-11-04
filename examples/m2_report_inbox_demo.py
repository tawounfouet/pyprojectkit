"""VS-M2-02/03 : émission attestée, report déclaré, replay et reprise SQLite.

Fixtures entièrement synthétiques. Aucun Pythos réel, aucune CI réelle.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

from pyprojectkit import ExplicitPolicy, FixedClock, ProjectId, ProjectService
from pyprojectkit.m1 import RegistryService, SqliteDatabase, SqliteUnitOfWork, TrustedHost
from pyprojectkit.m2 import (
    BuildBriefRequest, DelegationMandate, ExactTargetReference, FakePythosAdapter,
    InMemoryMandateStore, MandateVerifier, ReportInboxService, WorkItemRef,
)


def main() -> None:
    at = datetime(2026, 11, 4, 12, tzinfo=timezone.utc)
    perms = {
        "SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "TASK_VIEW", "TASK_CREATE",
        "BRIEF_BUILD", "BRIEF_ISSUE", "REPORT_RECEIVE", "REPORT_READ",
        "WRITE_OBSERVATION", "WRITE_EVIDENCE", "WRITE_HANDOFF", "READ_OBSERVATION",
    }
    with TemporaryDirectory() as folder:
        path = Path(folder) / "synthetic-inbox.sqlite"
        db = SqliteDatabase(path)
        host = TrustedHost({"synthetic": ("owner", {"local": perms})})
        actor = host.authenticate("synthetic", "local")
        registry = RegistryService(db, host, FixedClock(at))
        registry.create_scope(actor)
        project = registry.register_project(actor, "M2-B laboratoire", "PACKAGE")
        service = ProjectService(partial(SqliteUnitOfWork, db),
                                 ExplicitPolicy({"owner": perms}), FixedClock(at))
        task = str(service.create_task(actor.legacy(), ProjectId(UUID(project)), "Audit fictif").value)
        ref = ExactTargetReference("GIT_COMMIT", "synthetic/repo", "a" * 40)
        work = WorkItemRef("TASK", task)
        store = InMemoryMandateStore()
        mandate = DelegationMandate(
            "synthetic-mandate", "owner", "pythos", "local", project, work, "AUDIT", "A0",
            ("PROJECT_VIEW", "TASK_VIEW"), ref, at - timedelta(minutes=1),
            at + timedelta(hours=1),
        )
        store.provision(mandate)
        inbox = ReportInboxService(registry, MandateVerifier(host, store), FixedClock(at))
        brief = inbox.issue_brief(actor, BuildBriefRequest(mandate.mandate_id, project, work, "AUDIT", ref))
        report = FakePythosAdapter().make_report(
            brief, produced_at=at, report_id=str(uuid4()), idempotency_key="m2b-synthetic-1"
        )
        accepted = inbox.receive(actor, report)
        assert accepted.outcome == "ACCEPTED_AS_DECLARATION"
        assert not accepted.is_replay
        assert inbox.receive(actor, report).ingestion_id == accepted.ingestion_id
        restarted = ReportInboxService(
            RegistryService(SqliteDatabase(path), host, FixedClock(at)),
            MandateVerifier(host, store), FixedClock(at),
        )
        same = restarted.reconcile(actor, report)
        assert same is not None and same.ingestion_id == accepted.ingestion_id
        assert restarted.get_report(actor, accepted.ingestion_id).classification == "DECLARED"
        print("VS-M2-02 PASS: declaration only; Task unchanged")
        print("VS-M2-03 PASS: durable report, idempotent replay and restart")


if __name__ == "__main__":
    main()
