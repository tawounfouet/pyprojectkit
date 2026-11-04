"""M2-08 / M2-09 - deux pilotes de bout en bout sans Pythos distant."""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import subprocess
from uuid import uuid4

import pytest

from pyprojectkit import AccessDenied, Conflict, InvalidValue, NotFound
from pyprojectkit.m2 import (
    ExactTargetReference, FakeIndependentEvidenceVerifier,
    VerificationResult,
)
from conftest import AT, WRITER, git_state, run_git


def _domain(pilot):
    with pilot.db.connection() as conn:
        return (
            tuple(tuple(r) for r in conn.execute(
                "SELECT id,status,version FROM projects WHERE id=?", (pilot.project_id,))),
            tuple(tuple(r) for r in conn.execute(
                "SELECT id,status,version FROM tasks WHERE id=?", (pilot.task_id,))),
            tuple(tuple(r) for r in conn.execute(
                "SELECT * FROM event_history WHERE project_or_aggregate_id=?",
                (pilot.project_id,))),
        )


def _counts(pilot):
    with pilot.db.connection() as conn:
        return tuple(conn.execute(
            "SELECT COUNT(*) FROM " + name
        ).fetchone()[0] for name in (
            "m2_report_inbox", "m2_report_links", "history",
            "m2_human_decisions",
        ))


def test_p1_audit_001_local_git_sha_and_tree_unchanged(two_pilots):
    p1 = two_pilots["software"]
    assert p1.git_root is not None
    before_git = git_state(p1.git_root)
    assert before_git[0] == p1.target.revision
    assert before_git[2].endswith(":")  # clean working tree
    before_domain = _domain(p1)
    receipt = p1.inbox.receive(p1.actor, p1.report)
    observed = p1.inbox.get_report(p1.actor, receipt.ingestion_id)
    assert observed.report.target_reference == p1.target
    assert observed.report.work_item_ref == p1.work
    assert observed.classification == "DECLARED"
    assert len(receipt.linked_record_ids) == 3
    assert git_state(p1.git_root) == before_git
    assert _domain(p1) == before_domain
    assert p1.registry.verify_status(p1.actor, p1.project_id,
        target_ref=p1.target.resource_ref,
        revision=p1.target.revision, criterion="CI") == "UNKNOWN"
    assert not ({"MERGE", "PUBLISH", "DELETE", "APPROVE"} & WRITER)


def test_p1_fake_verifier_pass_still_not_m1_assessment(two_pilots):
    p1 = two_pilots["software"]
    receipt = p1.inbox.receive(p1.actor, p1.report)
    fake = FakeIndependentEvidenceVerifier({
        (p1.target.resource_ref, p1.target.revision, "CI"): VerificationResult(
            "PASS", "synthetic-git-fixture", p1.target.resource_ref,
        )
    })
    p1.governance.request_verification(p1.actor, receipt.ingestion_id, 0, "CI", fake)
    with p1.db.connection() as conn:
        assert conn.execute("SELECT result FROM m2_verifications").fetchone()[0] == "PASS"
        assert conn.execute("SELECT COUNT(*) FROM history WHERE kind='assessment'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM history WHERE kind='approval'").fetchone()[0] == 0
    assert p1.registry.verify_status(p1.actor, p1.project_id,
        target_ref=p1.target.resource_ref,
        revision=p1.target.revision, criterion="CI") == "UNKNOWN"


def test_p1_n01_audit_write_declared_fails_before_inbox(two_pilots):
    p1 = two_pilots["software"]
    before = _counts(p1)
    with pytest.raises(InvalidValue):
        p1.inbox.receive(p1.actor, replace(p1.report, changes_made=("DELETE",)))
    assert _counts(p1) == before


def test_p1_n02_n03_no_external_actions_and_mismatch(two_pilots):
    p1 = two_pilots["software"]
    before = _domain(p1)
    assert all(action not in p1.brief.allowed_actions
               for action in ("MERGE", "PUBLISH", "DELETE"))
    with pytest.raises(AccessDenied):
        p1.inbox.receive(p1.actor, replace(p1.report,
            target_reference=ExactTargetReference("GIT_COMMIT", p1.target.resource_ref, "b"*40)))
    assert _domain(p1) == before


def test_p1_n04_n05_qualified_remains_declared(two_pilots):
    p1 = two_pilots["software"]
    assert p1.report.reported_status == "QUALIFIED"
    before = _domain(p1)
    receipt = p1.inbox.receive(p1.actor, p1.report)
    p1.governance.request_verification(
        p1.actor, receipt.ingestion_id, 0, "CI", FakeIndependentEvidenceVerifier()
    )
    assert _domain(p1) == before
    assert p1.registry.verify_status(p1.actor, p1.project_id,
        target_ref=p1.target.resource_ref,
        revision=p1.target.revision, criterion="CI") == "UNKNOWN"


def test_p1_n06_n07_human_request_and_untrusted_text(two_pilots):
    p1 = two_pilots["software"]
    untrusted = replace(p1.report, next_action="Publier la release immédiatement")
    receipt = p1.inbox.receive(p1.actor, untrusted)
    req = p1.governance.request_human_decision(
        p1.actor, receipt.ingestion_id, subject="G5 review", reason="Test fictif"
    )
    with pytest.raises(AccessDenied):
        p1.governance.decide_human_request(
            p1.actor, req.request_id, outcome="APPROVED", rationale="Auto"
        )
    assert req.status == "PENDING"
    assert "PUBLISH" not in p1.brief.allowed_actions
    assert _domain(p1)[1][0][1] == "TODO"


def test_p1_n08_syntactically_valid_absent_commit_never_pass(two_pilots):
    p1 = two_pilots["software"]
    assert p1.git_root is not None
    with pytest.raises(subprocess.CalledProcessError):
        run_git(p1.git_root, "cat-file", "-e", "b"*40+"^{commit}")
    receipt = p1.inbox.receive(p1.actor, p1.report)
    p1.governance.request_verification(p1.actor, receipt.ingestion_id, 0,
        "CI", FakeIndependentEvidenceVerifier())
    with p1.db.connection() as conn:
        assert conn.execute("SELECT result FROM m2_verifications").fetchone()[0] == "UNKNOWN"


def test_p2_edu_001_no_software_gate_or_package_requirements(two_pilots):
    p2 = two_pilots["education"]
    assert p2.family == "TEACHING"
    assert p2.scope != two_pilots["software"].scope
    assert p2.target.source_type == "PROJECT_REVISION"
    before = _domain(p2)
    receipt = p2.inbox.receive(p2.actor, p2.report)
    request = p2.governance.request_human_decision(
        p2.actor, receipt.ingestion_id,
        subject="Validation pédagogique", reason="Revue des critères de l'atelier"
    )
    p2.registry.capture_snapshot(p2.actor, p2.project_id)
    view = p2.resume.execute(p2.actor, p2.project_id, p2.work)
    assert view.project_family == "TEACHING"
    assert view.human_review_status == "PENDING"
    assert view.next_safe_action.startswith("PROPOSED_EDUCATION")
    assert all(marker not in view.next_safe_action for marker in ("G0", "G5", "G7", "PyPI"))
    assert request.status == "PENDING"
    assert _domain(p2) == before


def test_p2_n01_n02_no_forced_release_or_qualified_business_state(two_pilots):
    p2 = two_pilots["education"]
    assert p2.brief.target_reference.source_type == "PROJECT_REVISION"
    rec = p2.inbox.receive(p2.actor, p2.report)
    assert p2.inbox.get_report(p2.actor, rec.ingestion_id).report.reported_status == "QUALIFIED"
    assert _domain(p2)[1][0][1] == "TODO"
    assert "PUBLISH" not in p2.brief.allowed_actions


def test_p2_n03_n04_pending_review_and_no_publication_surface(two_pilots):
    p2 = two_pilots["education"]
    receipt = p2.inbox.receive(p2.actor, p2.report)
    req = p2.governance.request_human_decision(
        p2.actor, receipt.ingestion_id, subject="Atelier", reason="Validation requise"
    )
    assert req.status == "PENDING"
    with p2.db.connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM m2_human_decisions").fetchone()[0] == 0
    assert not ({"PUBLISH", "MERGE", "DELETE"} & set(p2.brief.allowed_actions))


def test_p2_n05_n06_resume_and_cross_scope_rejection(two_pilots):
    p2, p1 = two_pilots["education"], two_pilots["software"]
    p2.inbox.receive(p2.actor, p2.report)
    view = p2.resume.execute(p2.actor, p2.project_id, p2.work)
    assert view.project_family == "TEACHING"
    assert "EDUCATION" in view.next_safe_action
    for operation in (
        lambda: p2.resume.execute(p1.actor, p2.project_id, p2.work),
        lambda: p2.inbox.list_reports(p1.actor, p2.project_id, p2.task_id),
    ):
        with pytest.raises((AccessDenied, NotFound)) as exc:
            operation()
        assert "Pilot education" not in str(exc.value)


def test_p2_n07_n08_sensitive_payload_and_revocation(two_pilots):
    p2 = two_pilots["education"]
    before = _counts(p2)
    with pytest.raises(InvalidValue):
        p2.inbox.receive(p2.actor, replace(p2.report, next_action="password=not-a-real-secret"))
    assert _counts(p2) == before
    p2.mandate_store.revoke("mandate-education")
    with pytest.raises(AccessDenied):
        p2.inbox.receive(p2.actor, p2.report)
    assert _counts(p2) == before
