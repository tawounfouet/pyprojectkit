"""VS-M2-04 / reprise VS-M2-05 : pilotes locaux intégralement synthétiques.

Lancer : python examples/m2c_pilots_demo.py
Aucune lecture de dépôt réel, aucune invocation de Pythos/LLM ou réseau.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
from uuid import UUID

from pyprojectkit import ExplicitPolicy, FixedClock, ProjectId, ProjectService
from pyprojectkit.m1 import RegistryService, SqliteDatabase, SqliteUnitOfWork, TrustedHost
from pyprojectkit.m2 import (
    BuildBriefRequest, DelegationMandate, ExactTargetReference, FakePythosAdapter,
    InMemoryMandateStore, MandateVerifier, ReportGovernanceService,
    ReportInboxService, WorkItemRef,
)
from pyprojectkit.m2.resume_view import ResumeWorkItemQuery

AT = datetime(2026, 11, 4, 12, tzinfo=timezone.utc)
RIGHTS = {
    "SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "TASK_CREATE", "TASK_VIEW",
    "BRIEF_BUILD", "BRIEF_ISSUE", "REPORT_RECEIVE", "REPORT_READ", "RESUME",
    "WRITE_OBSERVATION", "READ_OBSERVATION", "WRITE_EVIDENCE", "READ_EVIDENCE",
    "WRITE_HANDOFF", "READ_HANDOFF", "CAPTURE", "WRITE_SNAPSHOT", "READ_SNAPSHOT",
    "READ_DECISION", "HUMAN_REQUEST",
}


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, text=True,
        capture_output=True, timeout=15,
    ).stdout.strip()


def make_repo(root: Path) -> tuple[str, str]:
    root.mkdir()
    (root / "README.md").write_text("# synthetic-pysrmkit\nExemple fictif.\n", encoding="utf-8")
    git(root, "init", "--object-format=sha1", "-q")
    git(root, "add", "README.md")
    git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@invalid.example",
        "-c", "core.hooksPath=/dev/null", "commit", "-qm", "Synthetic")
    return git(root, "rev-parse", "HEAD"), git(root, "rev-parse", "HEAD^{tree}")


def resume_only(database: Path, project_id: str, task_id: str,
                scope: str, owner: str) -> None:
    # Nouveau processus, identifiants provisionnés localement par l'hôte fictif.
    host = TrustedHost({"synthetic-session": (owner, {scope: set(RIGHTS)})})
    actor = host.authenticate("synthetic-session", scope)
    registry = RegistryService(SqliteDatabase(database), host, FixedClock(AT))
    # La lecture ne reconstitue PAS un mandat depuis le report.
    inbox = ReportInboxService(
        registry, MandateVerifier(host, InMemoryMandateStore()), FixedClock(AT)
    )
    view = ResumeWorkItemQuery(inbox).execute(actor, project_id, WorkItemRef("TASK", task_id))
    assert view.project_id == project_id and view.work_item_ref.id == task_id
    assert len(view.latest_report_ids) == 1
    print(f"RESTART OK: {view.project_family}, report={len(view.latest_report_ids)}, "
          f"human={view.human_review_status}, missing={','.join(view.missing_sections)}")


def run_pilots() -> None:
    with TemporaryDirectory() as folder:
        tmp = Path(folder)
        database = SqliteDatabase(tmp / "m2c.sqlite")
        repo_root = tmp / "synthetic-pysrmkit"
        sha, tree = make_repo(repo_root)
        host = TrustedHost({
            "sw": ("pilot-owner-software", {"software-fixture": set(RIGHTS)}),
            "edu": ("pilot-owner-education", {"education-fixture": set(RIGHTS)}),
        })
        cases = (
            ("PACKAGE", "software-fixture", "sw",
             ExactTargetReference("GIT_COMMIT", "synthetic-pysrmkit", sha)),
            ("TEACHING", "education-fixture", "edu",
             ExactTargetReference("PROJECT_REVISION", "synthetic-workshop", "rev-1")),
        )
        for family, scope, token, target in cases:
            actor = host.authenticate(token, scope)
            registry = RegistryService(database, host, FixedClock(AT))
            registry.create_scope(actor)
            project_id = registry.register_project(actor, "Pilot " + family, family)
            core = ProjectService(
                partial(SqliteUnitOfWork, database),
                ExplicitPolicy({actor.actor_id: set(RIGHTS)}),
                FixedClock(AT),
            )
            task_id = str(core.create_task(
                actor.legacy(), ProjectId(UUID(project_id)),
                "Audit de code fictif" if family == "PACKAGE" else "Revue pédagogique fictive"
            ).value)
            work = WorkItemRef("TASK", task_id)
            mandate_id = "synthetic-" + family.lower()
            store = InMemoryMandateStore()
            store.provision(DelegationMandate(
                mandate_id, actor.actor_id, "pythos", scope, project_id,
                work, "AUDIT", "A0", ("PROJECT_VIEW", "TASK_VIEW"), target,
                AT - timedelta(minutes=1), AT + timedelta(minutes=30),
            ))
            inbox = ReportInboxService(
                registry, MandateVerifier(host, store), FixedClock(AT)
            )
            brief = inbox.issue_brief(actor, BuildBriefRequest(
                mandate_id, project_id, work, "AUDIT", target,
            ))
            report = FakePythosAdapter().make_report(
                brief, produced_at=AT, idempotency_key="demo-" + family.lower(),
            )
            receipt = inbox.receive(actor, report)
            assert receipt.outcome == "ACCEPTED_AS_DECLARATION"
            assert inbox.receive(actor, report).is_replay
            registry.capture_snapshot(actor, project_id)
            registry.record_handoff(actor, project_id, summary="Fixture locale",
                                    outcome="REVIEW")
            if family == "TEACHING":
                request = ReportGovernanceService(inbox, FixedClock(AT)).request_human_decision(
                    actor, receipt.ingestion_id, subject="Programme atelier",
                    reason="Validation humaine requise",
                )
                assert request.status == "PENDING"
            view = ResumeWorkItemQuery(inbox).execute(actor, project_id, work)
            assert view.task_status == "TODO"
            assert view.latest_report_ids == (report.report_id,)
            if family == "TEACHING":
                assert view.next_safe_action.startswith("PROPOSED_EDUCATION")
            subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--resume",
                 str(database.path), project_id, task_id, scope, actor.actor_id],
                check=True, capture_output=False, text=True, timeout=25,
            )
            print(f"PILOT {family} OK: declared report, no implicit task completion")
        assert git(repo_root, "rev-parse", "HEAD") == sha
        assert git(repo_root, "rev-parse", "HEAD^{tree}") == tree
        assert git(repo_root, "status", "--porcelain") == ""
        print(f"SYNTHETIC_GIT_HEAD={sha} TREE={tree} STATUS=CLEAN")
        print("VS-M2-04 PASS: two segregated local synthetic pilots")
        print("M2-10 PASS: independent process restarted from SQLite")
        print("Q-M2: human gate PENDING, no publication")


if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--resume":
        resume_only(Path(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    elif len(sys.argv) == 1:
        run_pilots()
    else:
        raise SystemExit("Usage: m2c_pilots_demo.py [--resume db project_id task_id scope owner]")
