"""M2-C sécurité SEC-01..15 : frontières de mandat et d'idempotence."""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from functools import partial
from uuid import UUID, uuid4
import sqlite3

import pytest

from pyprojectkit import AccessDenied, CommitOutcomeUnknown, Conflict, ExplicitPolicy, FixedClock, InvalidValue, NotFound, ProjectId, ProjectService
from pyprojectkit.m1 import RegistryService, SqliteDatabase, SqliteUnitOfWork, TrustedHost
from pyprojectkit.m2 import (
    BuildAuthorizedOperatingBrief, BuildBriefRequest, DelegationMandate,
    ExactTargetReference, FakePythosAdapter, IdempotencyConflict,
    InMemoryMandateStore, MandateVerifier, ReportInboxService, WorkItemRef,
)
from conftest import AT, WRITER


def counts(p):
    with p.db.connection() as conn:
        return tuple(conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
                     for table in (
                         "m2_issued_briefs", "m2_report_inbox", "m2_report_links",
                         "m2_verifications", "m2_human_decisions",
                         "history", "event_history",
                     ))


def test_sec_01_expired_mandate_denied_before_report(two_pilots):
    p = two_pilots["software"]
    later = FixedClock(AT + timedelta(hours=3))
    svc = ReportInboxService(p.registry, MandateVerifier(p.host, p.mandate_store), later)
    before = counts(p)
    with pytest.raises(AccessDenied):
        svc.receive(p.actor, p.report)
    assert counts(p) == before


def test_sec_02_suspended_and_revoked_mandate_deny_replay(two_pilots):
    p = two_pilots["software"]
    p.inbox.receive(p.actor, p.report)
    p.mandate_store.suspend("mandate-software")
    before = counts(p)
    with pytest.raises(AccessDenied):
        p.inbox.receive(p.actor, p.report)
    p.mandate_store.revoke("mandate-software")
    with pytest.raises(AccessDenied):
        p.inbox.receive(p.actor, p.report)
    assert counts(p) == before


def test_sec_03_cross_scope_is_fail_closed(two_pilots):
    p, other = two_pilots["software"], two_pilots["education"]
    rec = p.inbox.receive(p.actor, p.report)
    with pytest.raises((AccessDenied, NotFound)):
        p.inbox.get_report(other.actor, rec.ingestion_id)
    with pytest.raises((AccessDenied, NotFound)):
        p.resume.execute(other.actor, p.project_id, p.work)


def test_sec_04_other_owner_same_scope_cannot_list_report(two_pilots):
    p = two_pilots["software"]
    p.inbox.receive(p.actor, p.report)
    other = p.host.authenticate("other-owner-credential", p.scope)
    with pytest.raises(NotFound):
        p.inbox.list_reports(other, p.project_id, p.task_id)


def test_sec_05_private_scope_is_not_delegated_even_with_read_private(tmp_path):
    rights = set(WRITER) | {"READ_PRIVATE", "WRITE_PRIVATE"}
    host = TrustedHost({"private": ("private-owner", {"secret-zone": rights})})
    actor = host.authenticate("private", "secret-zone")
    db = SqliteDatabase(tmp_path / "private-fixture.sqlite")
    registry = RegistryService(db, host, FixedClock(AT))
    registry.create_scope(actor, classification="PRIVATE")
    project = registry.register_project(actor, "Fake private project", "PACKAGE")
    core = ProjectService(partial(SqliteUnitOfWork, db),
                          ExplicitPolicy({"private-owner": rights}), FixedClock(AT))
    task = str(core.create_task(actor.legacy(), ProjectId(UUID(project)), "Synthetic private work").value)
    work = WorkItemRef("TASK", task)
    ref = ExactTargetReference("PROJECT_REVISION", "synthetic-private", "rev-1")
    store = InMemoryMandateStore()
    store.provision(DelegationMandate(
        "private-mandate", "private-owner", "pythos", "secret-zone", project, work,
        "AUDIT", "A0", ("PROJECT_VIEW", "TASK_VIEW"), ref,
        AT - timedelta(minutes=1), AT + timedelta(minutes=5),
    ))
    svc = ReportInboxService(registry, MandateVerifier(host, store), FixedClock(AT))
    with pytest.raises(AccessDenied):
        svc.issue_brief(actor, BuildBriefRequest("private-mandate", project, work, "AUDIT", ref))


def test_sec_06_unauthorized_a4_or_a5_mandate_rejected(two_pilots):
    p = two_pilots["software"]
    original = p.mandate_store.resolve("mandate-software")
    for level in ("A4", "A5"):
        with pytest.raises(InvalidValue):
            replace(original, authority_level=level)


def test_sec_07_no_merge_publish_delete_tool_exposed(two_pilots):
    # NOT_APPLICABLE_NO_TOOL : absence contrôlée, pas refus prétendument exécuté.
    p = two_pilots["software"]
    assert not any(hasattr(p.inbox, command) for command in ("merge", "publish", "delete"))
    assert {"MERGE", "PUBLISH", "DELETE"}.isdisjoint(p.brief.allowed_actions)


def test_sec_08_no_project_priority_command_on_m2_boundary(two_pilots):
    # NOT_APPLICABLE_NO_TOOL : pas de commande M2 de changement de priorité.
    p = two_pilots["software"]
    assert not hasattr(p.inbox, "set_priority")
    assert "CHANGE_PRIORITY" not in p.brief.allowed_actions


def test_sec_09_forged_brief_id_is_refused_without_success(two_pilots):
    p = two_pilots["software"]
    before = counts(p)
    with pytest.raises(NotFound):
        p.inbox.receive(p.actor, replace(p.report, brief_id=str(uuid4())))
    assert counts(p) == before


def test_sec_10_wrong_task_or_exact_revision_denied(two_pilots):
    p = two_pilots["software"]
    before = counts(p)
    with pytest.raises(AccessDenied):
        p.inbox.receive(p.actor, replace(
            p.report, work_item_ref=WorkItemRef("TASK", str(uuid4()))
        ))
    with pytest.raises(AccessDenied):
        p.inbox.receive(p.actor, replace(
            p.report, target_reference=ExactTargetReference(
                "GIT_COMMIT", p.target.resource_ref, "b"*40
            )
        ))
    assert counts(p) == before


def test_sec_11_colliding_key_and_changed_payload_rejected(two_pilots):
    p = two_pilots["software"]
    p.inbox.receive(p.actor, p.report)
    before = counts(p)
    with pytest.raises(IdempotencyConflict):
        p.inbox.receive(p.actor, replace(p.report, outcome="FAILED"))
    assert counts(p) == before


def test_sec_12_many_identical_retries_one_intention(two_pilots):
    p = two_pilots["software"]
    first = p.inbox.receive(p.actor, p.report)
    before = counts(p)
    for _ in range(14):
        assert p.inbox.receive(p.actor, p.report).ingestion_id == first.ingestion_id
    assert counts(p) == before


def test_sec_13_crash_before_commit_rolls_back(two_pilots):
    p = two_pilots["software"]
    before = counts(p)
    def fail(stage):
        if stage == "after_links_before_commit":
            raise RuntimeError("simulated interruption")
    with pytest.raises(RuntimeError, match="simulated"):
        p.inbox.receive(p.actor, p.report, fault=fail)
    assert counts(p) == before


def test_sec_14_lost_ack_reconciles_without_second_report(two_pilots, monkeypatch):
    p = two_pilots["software"]
    original = SqliteUnitOfWork.commit
    def lost_ack(uow):
        original(uow)
        raise CommitOutcomeUnknown("ACK lost after commit")
    monkeypatch.setattr(SqliteUnitOfWork, "commit", lost_ack)
    with pytest.raises(CommitOutcomeUnknown):
        p.inbox.receive(p.actor, p.report)
    monkeypatch.setattr(SqliteUnitOfWork, "commit", original)
    reconciled = p.inbox.reconcile(p.actor, p.report)
    assert reconciled is not None and reconciled.is_replay
    before = counts(p)
    assert p.inbox.receive(p.actor, p.report).ingestion_id == reconciled.ingestion_id
    assert counts(p) == before


def test_sec_15_fake_actor_and_credential_not_authorized(two_pilots):
    p = two_pilots["software"]
    with pytest.raises(AccessDenied):
        p.host.authenticate("unknown-credential", p.scope)
    rival = TrustedHost({"foreign": ("software-owner", {p.scope: set(WRITER)})})
    forged = rival.authenticate("foreign", p.scope)
    before = counts(p)
    with pytest.raises(AccessDenied):
        p.inbox.receive(forged, p.report)
    assert counts(p) == before
