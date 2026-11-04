"""Fixturing M2-C : deux contextes distincts, anonymes et synthétiques."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import partial
from hashlib import sha256
from pathlib import Path
import subprocess
from uuid import UUID

import pytest

from pyprojectkit import ExplicitPolicy, FixedClock, ProjectId, ProjectService
from pyprojectkit.m1 import RegistryService, ScopeRule, SqliteDatabase, SqliteUnitOfWork, TrustedHost
from pyprojectkit.m2 import (
    BuildBriefRequest, DelegationMandate, ExactTargetReference,
    FakePythosAdapter, InMemoryMandateStore, MandateVerifier,
    ReportGovernanceService, ReportInboxService, WorkItemRef,
)
from pyprojectkit.m2.resume_view import ResumeWorkItemQuery

AT = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)
WRITER = frozenset({
    "SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "TASK_CREATE", "TASK_VIEW", "TASK_ASSIGN",
    "BRIEF_BUILD", "BRIEF_ISSUE", "REPORT_RECEIVE", "REPORT_READ",
    "WRITE_OBSERVATION", "READ_OBSERVATION", "WRITE_EVIDENCE", "READ_EVIDENCE",
    "WRITE_HANDOFF", "READ_HANDOFF", "CAPTURE", "WRITE_SNAPSHOT",
    "READ_SNAPSHOT", "RESUME", "HUMAN_REQUEST", "READ_DECISION",
    "VERIFY_REQUEST", "ASSESS", "WRITE_ASSESSMENT", "READ_ASSESSMENT",
})
REVIEWER = frozenset({
    "PROJECT_VIEW", "PROJECT_VIEW_ALL", "TASK_VIEW", "REPORT_READ",
    "READ_OBSERVATION", "READ_EVIDENCE", "READ_HANDOFF", "READ_SNAPSHOT",
    "READ_DECISION", "RESUME", "HUMAN_DECIDE", "APPROVE", "WRITE_DECISION",
})


def run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True, capture_output=True, text=True, timeout=15,
    )
    return completed.stdout.strip()


def create_synthetic_git(root: Path) -> tuple[str, str, str]:
    root.mkdir(parents=True)
    (root / "src").mkdir()
    (root / "README.md").write_text("# synthetic-pysrmkit\nFixture sans données réelles.\n", "utf-8")
    (root / "src" / "sample.py").write_text("VALUE = 42\n", "utf-8")
    run_git(root, "init", "--object-format=sha1", "-q")
    run_git(root, "add", "README.md", "src/sample.py")
    run_git(root, "-c", "user.name=Fixture Bot", "-c",
            "user.email=fixture@invalid.example", "-c", "core.hooksPath=/dev/null",
            "commit", "-q", "-m", "Synthetic fixture")
    return git_state(root)


def git_state(root: Path) -> tuple[str, str, str]:
    sha = run_git(root, "rev-parse", "HEAD")
    tree = run_git(root, "rev-parse", "HEAD^{tree}")
    status = run_git(root, "status", "--porcelain")
    digest = sha256(b"".join(
        file.relative_to(root).as_posix().encode() + b":" + file.read_bytes()
        for file in sorted(root.rglob("*")) if file.is_file() and ".git" not in file.parts
    )).hexdigest()
    assert len(sha) == 40 and len(tree) == 40
    return sha, tree, digest + ":" + status


@dataclass
class PilotContext:
    db: SqliteDatabase
    host: TrustedHost
    actor: object
    reviewer: object
    registry: RegistryService
    inbox: ReportInboxService
    governance: ReportGovernanceService
    resume: ResumeWorkItemQuery
    mandate_store: InMemoryMandateStore
    project_id: str
    task_id: str
    work: WorkItemRef
    target: ExactTargetReference
    brief: object
    report: object
    scope: str
    family: str
    git_root: Path | None


@pytest.fixture
def two_pilots(tmp_path: Path) -> dict[str, PilotContext]:
    host = TrustedHost({
        "software-credential": ("software-owner", {"m2c-software": set(WRITER)}),
        "education-credential": ("education-owner", {"m2c-education": set(WRITER)}),
        "software-review": ("software-reviewer", {"m2c-software": set(REVIEWER)}),
        "education-review": ("education-reviewer", {"m2c-education": set(REVIEWER)}),
    }, rules={
        "m2c-software": ScopeRule(allowed_families=frozenset({"PACKAGE"})),
        "m2c-education": ScopeRule(allowed_families=frozenset({"TEACHING"})),
    })
    db = SqliteDatabase(tmp_path / "m2c.sqlite")
    git_root = tmp_path / "synthetic-pysrmkit"
    sha, _, _ = create_synthetic_git(git_root)
    result: dict[str, PilotContext] = {}
    configs = (
        ("software", "software-credential", "software-review", "m2c-software",
         "PACKAGE", ExactTargetReference("GIT_COMMIT", "synthetic-pysrmkit", sha),
         git_root, "Audit de code fictif sur SHA exact"),
        ("education", "education-credential", "education-review", "m2c-education",
         "TEACHING", ExactTargetReference("PROJECT_REVISION", "synthetic-education", "revision-1"),
         None, "Valider le programme pédagogique fictif"),
    )
    for label, token, reviewer_token, scope, family, target, root, task_title in configs:
        actor = host.authenticate(token, scope)
        reviewer = host.authenticate(reviewer_token, scope)
        registry = RegistryService(db, host, FixedClock(AT))
        registry.create_scope(actor)
        project = registry.register_project(actor, f"Pilot {label}", family)
        core = ProjectService(partial(SqliteUnitOfWork, db),
                              ExplicitPolicy({actor.actor_id: set(WRITER)}), FixedClock(AT))
        task_id = str(core.create_task(actor.legacy(), ProjectId(UUID(project)), task_title).value)
        work = WorkItemRef("TASK", task_id)
        store = InMemoryMandateStore()
        mandate = DelegationMandate(
            f"mandate-{label}", actor.actor_id, "pythos", scope, project,
            work, "AUDIT", "A0", ("PROJECT_VIEW", "TASK_VIEW"), target,
            AT - timedelta(minutes=1), AT + timedelta(hours=1),
        )
        store.provision(mandate)
        inbox = ReportInboxService(registry, MandateVerifier(host, store), FixedClock(AT))
        brief = inbox.issue_brief(actor, BuildBriefRequest(
            mandate.mandate_id, project, work, "AUDIT", target,
        ))
        report = FakePythosAdapter().make_report(
            brief, produced_at=AT, idempotency_key=f"m2c-{label}",
        )
        gov = ReportGovernanceService(inbox, FixedClock(AT))
        result[label] = PilotContext(
            db, host, actor, reviewer, registry, inbox, gov,
            ResumeWorkItemQuery(inbox), store, project, task_id, work,
            target, brief, report, scope, family, root,
        )
    return result
