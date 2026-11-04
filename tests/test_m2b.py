"""M2-B: contrat, émission, réception atomique, idempotence et gouvernance synthétique."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from uuid import UUID, uuid4
import json
import sqlite3

import pytest

from pyprojectkit import AccessDenied, Conflict, ExplicitPolicy, FixedClock, InvalidValue, NotFound, ProjectId, ProjectService
from pyprojectkit.m1 import RegistryService, SqliteDatabase, SqliteUnitOfWork, TrustedHost
from pyprojectkit.m2 import (
    BuildBriefRequest, DelegationMandate, ExactTargetReference, ExecutionReportDTO,
    FakeIndependentEvidenceVerifier, FakePythosAdapter, IdempotencyConflict,
    InMemoryMandateStore, MandateVerifier, ReportGovernanceService, ReportInboxService,
    UnsupportedContractVersion, VerificationResult, WorkItemRef,
)

NOW = datetime(2026, 11, 4, 12, tzinfo=timezone.utc)
SHA = "a" * 40
PERMS = {
    "PROJECT_VIEW", "PROJECT_VIEW_ALL", "PROJECT_CREATE", "SCOPE_CREATE", "TASK_VIEW", "TASK_CREATE",
    "BRIEF_BUILD", "BRIEF_ISSUE", "REPORT_RECEIVE", "REPORT_READ",
    "WRITE_OBSERVATION", "WRITE_HANDOFF", "WRITE_EVIDENCE", "READ_OBSERVATION", "READ_EVIDENCE",
    "VERIFY_REQUEST", "ASSESS", "WRITE_ASSESSMENT", "HUMAN_REQUEST",
    "HUMAN_DECIDE", "APPROVE", "WRITE_DECISION",
}


@pytest.fixture
def m2(tmp_path: Path):
    db = SqliteDatabase(tmp_path / "m2b.sqlite")
    host = TrustedHost({
        "owner-token": ("owner", {"alpha": set(PERMS)}),
        "reviewer-token": ("reviewer", {"alpha": set(PERMS)}),
        "outsider-token": ("outsider", {"beta": set(PERMS)}),
    })
    actor = host.authenticate("owner-token", "alpha")
    reviewer = host.authenticate("reviewer-token", "alpha")
    outsider = host.authenticate("outsider-token", "beta")
    registry = RegistryService(db, host, FixedClock(NOW))
    registry.create_scope(actor)
    registry.create_scope(outsider)
    project = registry.register_project(actor, "Package synthétique", "PACKAGE")
    m0 = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"owner": PERMS}), FixedClock(NOW))
    task = str(m0.create_task(actor.legacy(), ProjectId(UUID(project)), "Audit synthétique").value)
    work = WorkItemRef("TASK", task)
    target = ExactTargetReference("GIT_COMMIT", "synthetic/repository", SHA)
    mandates = InMemoryMandateStore()
    mandate = DelegationMandate(
        "mandate-pilot", "owner", "pythos", "alpha", project, work, "AUDIT", "A0",
        ("PROJECT_VIEW", "TASK_VIEW"), target,
        NOW - timedelta(minutes=2), NOW + timedelta(hours=2),
    )
    mandates.provision(mandate)
    verifier = MandateVerifier(host, mandates)
    inbox = ReportInboxService(registry, verifier, FixedClock(NOW))
    req = BuildBriefRequest(mandate.mandate_id, project, work, "AUDIT", target)
    brief = inbox.issue_brief(actor, req)
    report = FakePythosAdapter().make_report(brief, produced_at=NOW, report_id=str(uuid4()))
    governance = ReportGovernanceService(inbox, FixedClock(NOW))
    return locals()


def _snap(db):
    with db.connection() as conn:
        return {
            table: conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
            for table in (
                "m2_issued_briefs", "m2_report_inbox", "m2_report_links",
                "history", "m2_verifications", "m2_human_requests", "m2_human_decisions",
            )
        }


def test_m2b_01_report_contract_roundtrip_and_qualified_declared(m2):
    report = m2["report"]
    assert report.reported_status == "QUALIFIED"
    assert ExecutionReportDTO.from_json(report.to_json()) == report
    assert report.fingerprint() == ExecutionReportDTO.from_dict(report.to_dict()).fingerprint()


def test_m2b_02_schema_version_missing_fields_and_duplicates(m2):
    raw = m2["report"].to_dict()
    raw["schema_version"] = "99"
    with pytest.raises(UnsupportedContractVersion):
        ExecutionReportDTO.from_dict(raw)
    raw["schema_version"] = "1.0"
    raw["unexpected"] = "bad"
    with pytest.raises(InvalidValue):
        ExecutionReportDTO.from_dict(raw)
    with pytest.raises(InvalidValue):
        ExecutionReportDTO.from_json('{"report_id":"1","report_id":"2"}')
    with pytest.raises(InvalidValue):
        ExecutionReportDTO.from_json(" " * 35000)


def test_m2b_03_invalid_timestamps_and_exact_sha(m2):
    raw = m2["report"].to_dict()
    raw["produced_at"] = "2026-11-04T12:00:00"
    with pytest.raises(InvalidValue):
        ExecutionReportDTO.from_dict(raw)
    with pytest.raises(InvalidValue):
        replace(m2["report"], target_reference=ExactTargetReference("GIT_COMMIT", "repo", "branch"))


def test_m2b_04_issue_receipt_is_durable_and_strictly_correlated(m2):
    with m2["db"].connection() as conn:
        row = conn.execute("SELECT * FROM m2_issued_briefs WHERE brief_id=?", (m2["brief"].brief_id,)).fetchone()
        assert row is not None
        assert row["task_id"] == m2["task"]
        assert row["target_revision"] == SHA
        assert len(row["brief_fingerprint"]) == 64


def test_m2b_05_report_is_declared_with_atomic_m1_links(m2):
    before = _snap(m2["db"])
    receipt = m2["inbox"].receive(m2["actor"], m2["report"])
    after = _snap(m2["db"])
    assert receipt.outcome == "ACCEPTED_AS_DECLARATION"
    assert not receipt.is_replay and len(receipt.linked_record_ids) == 3
    assert after["m2_report_inbox"] == before["m2_report_inbox"] + 1
    assert after["history"] == before["history"] + 3
    assert m2["inbox"].get_report(m2["actor"], receipt.ingestion_id).classification == "DECLARED"
    with m2["db"].connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM history WHERE kind='approval'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM history WHERE kind='assessment'").fetchone()[0] == 0
        assert conn.execute("SELECT status FROM tasks WHERE id=?", (m2["task"],)).fetchone()[0] == "TODO"


def test_m2b_06_retries_and_idempotency_collisions(m2):
    inbox, actor, report = m2["inbox"], m2["actor"], m2["report"]
    first = inbox.receive(actor, report)
    before = _snap(m2["db"])
    for _ in range(10):
        replay = inbox.receive(actor, report)
        assert replay.ingestion_id == first.ingestion_id and replay.is_replay
        assert replay.outcome == "ALREADY_ACCEPTED"
    assert _snap(m2["db"]) == before
    with pytest.raises(IdempotencyConflict):
        inbox.receive(actor, replace(report, outcome="FAILED"))
    with pytest.raises(IdempotencyConflict):
        inbox.receive(actor, replace(report, report_id=str(uuid4())))


def test_m2b_07_unknown_brief_and_wrong_reference(m2):
    with pytest.raises(NotFound):
        m2["inbox"].receive(m2["actor"], replace(m2["report"], brief_id=str(uuid4())))
    with pytest.raises(AccessDenied):
        m2["inbox"].receive(
            m2["actor"], replace(m2["report"],
            target_reference=ExactTargetReference("GIT_COMMIT", "synthetic/repository", "b" * 40))
        )


def test_m2b_08_transaction_rollback_after_inbox_and_links(m2):
    for point in ("after_inbox", "after_links_before_commit"):
        before = _snap(m2["db"])
        def fail(current):
            if current == point:
                raise RuntimeError("injected crash")
        with pytest.raises(RuntimeError, match="injected"):
            m2["inbox"].receive(m2["actor"], m2["report"], fault=fail)
        assert _snap(m2["db"]) == before
    assert m2["inbox"].receive(m2["actor"], m2["report"]).outcome == "ACCEPTED_AS_DECLARATION"


def test_m2b_09_permission_scope_owner_and_revoke(m2):
    with pytest.raises(AccessDenied):
        m2["inbox"].receive(m2["reviewer"], m2["report"])
    with pytest.raises(AccessDenied):
        m2["inbox"].receive(m2["outsider"], m2["report"])
    m2["mandates"].revoke(m2["mandate"].mandate_id)
    with pytest.raises(AccessDenied):
        m2["inbox"].receive(m2["actor"], m2["report"])


def test_m2b_10_read_requires_project_access(m2):
    rec = m2["inbox"].receive(m2["actor"], m2["report"])
    assert len(m2["inbox"].list_reports(m2["actor"], m2["project"], m2["task"])) == 1
    with pytest.raises(NotFound):
        m2["inbox"].get_report(m2["outsider"], rec.ingestion_id)


def test_m2b_11_reconcile_after_lost_ack(m2):
    first = m2["inbox"].receive(m2["actor"], m2["report"])
    recovered = m2["inbox"].reconcile(m2["actor"], m2["report"])
    assert recovered is not None and recovered.ingestion_id == first.ingestion_id
    assert m2["inbox"].reconcile(m2["actor"], replace(m2["report"], report_id=str(uuid4()),
                                                         idempotency_key="new")) is None


def test_m2b_12_evidence_verification_does_not_approve(m2):
    rec = m2["inbox"].receive(m2["actor"], m2["report"])
    v = FakeIndependentEvidenceVerifier({
        ("synthetic/repository", SHA, "CI"): VerificationResult("PASS", "synthetic-source", "synthetic/repository")
    })
    request_id = m2["governance"].request_verification(m2["actor"], rec.ingestion_id, 0, "CI", v)
    assert request_id
    with m2["db"].connection() as conn:
        assert conn.execute("SELECT result FROM m2_verifications").fetchone()[0] == "PASS"
        assert conn.execute("SELECT COUNT(*) FROM history WHERE kind='approval'").fetchone()[0] == 0
        assert conn.execute("SELECT status FROM tasks WHERE id=?", (m2["task"],)).fetchone()[0] == "TODO"


def test_m2b_13_unavailable_verifier_is_unknown(m2):
    rec = m2["inbox"].receive(m2["actor"], m2["report"])
    m2["governance"].request_verification(m2["actor"], rec.ingestion_id, 0, "CI",
                                            FakeIndependentEvidenceVerifier())
    with m2["db"].connection() as conn:
        assert conn.execute("SELECT result FROM m2_verifications").fetchone()[0] == "UNKNOWN"


def test_m2b_14_human_request_is_pending_and_sod(m2):
    rec = m2["inbox"].receive(m2["actor"], m2["report"])
    pending = m2["governance"].request_human_decision(
        m2["actor"], rec.ingestion_id, subject="G5", reason="Demander revue"
    )
    assert pending.status == "PENDING"
    with pytest.raises(AccessDenied):
        m2["governance"].decide_human_request(
            m2["actor"], pending.request_id, outcome="APPROVED", rationale="self approval"
        )
    decision = m2["governance"].decide_human_request(
        m2["reviewer"], pending.request_id, outcome="REJECTED", rationale="Preuves réelles insuffisantes"
    )
    assert decision.outcome == "REJECTED"
    with m2["db"].connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM m2_human_decisions").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM history WHERE kind='approval'").fetchone()[0] == 0
        assert conn.execute("SELECT status FROM tasks WHERE id=?", (m2["task"],)).fetchone()[0] == "TODO"


def test_m2b_15_sqlite_append_only_and_schema_0003(m2):
    with m2["db"].connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 3
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM m2_issued_briefs")
    rec = m2["inbox"].receive(m2["actor"], m2["report"])
    with m2["db"].connection() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM m2_report_inbox WHERE ingestion_id=?", (rec.ingestion_id,))
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE m2_report_inbox SET status='REJECTED' WHERE ingestion_id=?", (rec.ingestion_id,))


def test_m2b_16_ephemeral_m2a_brief_is_not_an_issued_receipt(m2):
    from pyprojectkit.m2 import BuildAuthorizedOperatingBrief
    ephemeral = BuildAuthorizedOperatingBrief(
        m2["registry"], m2["verifier"], FixedClock(NOW)
    ).execute(m2["actor"], m2["req"])
    report = FakePythosAdapter().make_report(ephemeral, produced_at=NOW)
    with pytest.raises(NotFound):
        m2["inbox"].receive(m2["actor"], report)


def test_m2b_17_report_declares_changes_in_audit_rejected(m2):
    before = _snap(m2["db"])
    with pytest.raises(InvalidValue):
        m2["inbox"].receive(m2["actor"], replace(m2["report"], changes_made=("DELETE",)))
    assert _snap(m2["db"]) == before


def test_m2b_18_signed_url_and_secret_not_persisted(m2):
    before = _snap(m2["db"])
    with pytest.raises(InvalidValue):
        m2["inbox"].receive(
            m2["actor"], replace(m2["report"], next_action="Bearer synthetic-secret")
        )
    assert _snap(m2["db"]) == before
    with pytest.raises(InvalidValue):
        from pyprojectkit.m2.reports import ReportEvidenceRefDTO
        ReportEvidenceRefDTO("CI_RUN", "https://source.example/?token=x", "a"*40, "test", True)


def test_m2b_19_produced_at_outside_freshness_policy(m2):
    for at in (NOW + timedelta(minutes=6), NOW - timedelta(hours=25)):
        with pytest.raises(InvalidValue):
            m2["inbox"].receive(m2["actor"], replace(m2["report"], produced_at=at))


def test_m2b_20_replay_after_revocation_cannot_leak_receipt(m2):
    m2["inbox"].receive(m2["actor"], m2["report"])
    m2["mandates"].revoke(m2["mandate"].mandate_id)
    with pytest.raises(AccessDenied):
        m2["inbox"].reconcile(m2["actor"], m2["report"])
    with pytest.raises(AccessDenied):
        m2["inbox"].receive(m2["actor"], m2["report"])


def test_m2b_21_other_retry_key_for_existing_report_conflicts(m2):
    m2["inbox"].receive(m2["actor"], m2["report"])
    with pytest.raises(IdempotencyConflict):
        m2["inbox"].receive(
            m2["actor"], replace(m2["report"], idempotency_key="different-intent")
        )


def test_m2b_22_changed_report_id_for_existing_key_conflicts(m2):
    m2["inbox"].receive(m2["actor"], m2["report"])
    with pytest.raises(IdempotencyConflict):
        m2["inbox"].receive(
            m2["actor"], replace(m2["report"], report_id=str(uuid4()))
        )


def test_m2b_23_wrong_revision_refuses_independent_verification(m2):
    from pyprojectkit.m2.reports import ReportEvidenceRefDTO
    wrong = ReportEvidenceRefDTO("GIT_COMMIT", "synthetic/repository", "b"*40, "wrong revision", True)
    forged = replace(m2["report"], evidence_references=(wrong,))
    receipt = m2["inbox"].receive(m2["actor"], forged)
    with pytest.raises(Conflict):
        m2["governance"].request_verification(
            m2["actor"], receipt.ingestion_id, 0, "CI", FakeIndependentEvidenceVerifier()
        )


def test_m2b_24_unavailable_evidence_cannot_promote_pass(m2):
    from pyprojectkit.m2.reports import ReportEvidenceRefDTO
    unavailable = ReportEvidenceRefDTO(
        "GIT_COMMIT", "synthetic/repository", SHA, "not accessible", False
    )
    report = replace(m2["report"], evidence_references=(unavailable,))
    receipt = m2["inbox"].receive(m2["actor"], report)
    fake = FakeIndependentEvidenceVerifier({
        ("synthetic/repository", SHA, "CI"): VerificationResult(
            "PASS", "synthetic-source", "synthetic/repository"
        )
    })
    m2["governance"].request_verification(
        m2["actor"], receipt.ingestion_id, 0, "CI", fake
    )
    with m2["db"].connection() as conn:
        assert conn.execute("SELECT result FROM m2_verifications").fetchone()[0] == "UNKNOWN"


def test_m2b_25_unapproved_request_cannot_create_approval(m2):
    receipt = m2["inbox"].receive(m2["actor"], m2["report"])
    request = m2["governance"].request_human_decision(
        m2["actor"], receipt.ingestion_id, subject="G5", reason="Revue manuelle"
    )
    assert request.status == "PENDING"
    with m2["db"].connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM m2_human_decisions").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM history WHERE kind='approval'").fetchone()[0] == 0


def test_m2b_26_weak_host_permissions_are_refused_before_write(m2):
    weak = TrustedHost({
        "limited": ("owner", {"alpha": set(PERMS) - {"REPORT_RECEIVE"}})
    })
    actor = weak.authenticate("limited", "alpha")
    svc = ReportInboxService(
        RegistryService(m2["db"], weak, FixedClock(NOW)),
        MandateVerifier(weak, m2["mandates"]), FixedClock(NOW)
    )
    before = _snap(m2["db"])
    with pytest.raises(AccessDenied):
        svc.receive(actor, m2["report"])
    assert _snap(m2["db"]) == before


def test_m2b_27_checksum_tamper_of_migration_0003_rejected(m2):
    with m2["db"].connection() as conn:
        conn.execute("UPDATE schema_migrations SET checksum='tampered' WHERE version=3")
    with pytest.raises(Conflict):
        SqliteDatabase(m2["db"].path)
