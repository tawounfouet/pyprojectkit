"""VS-M2-01 - tests de contrats, mandats et projection M1 synthétique."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
import json

import pytest

from pyprojectkit import AccessDenied, ExplicitPolicy, FixedClock, InvalidValue, NotFound, ProjectId, ProjectService
from pyprojectkit.m1 import RegistryService, SqliteDatabase, SqliteUnitOfWork, TrustedHost
from pyprojectkit.m2 import (
    BuildAuthorizedOperatingBrief, BuildBriefRequest, DelegationMandate,
    ExactTargetReference, InMemoryMandateStore, MandateVerifier,
    OperatingBriefDTO, UnsupportedContractVersion, WorkItemRef,
)

NOW = datetime(2026, 11, 4, 12, tzinfo=timezone.utc)
REF = ExactTargetReference("GIT_COMMIT", "synthetic/repository", "a" * 40)
PERMISSIONS = {"SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "TASK_VIEW", "TASK_CREATE",
               "BRIEF_BUILD", "WRITE_EVIDENCE", "WRITE_PRIVATE", "READ_PRIVATE"}


@pytest.fixture
def workspace(tmp_path: Path):
    db = SqliteDatabase(tmp_path / "synthetic.sqlite")
    host = TrustedHost({
        "alice-token": ("alice", {"personal": set(PERMISSIONS)}),
        "bob-token": ("bob", {"personal": set(PERMISSIONS)}),
        "mallory-token": ("mallory", {"client": set(PERMISSIONS)}),
        "no-build": ("visitor", {"personal": {"PROJECT_VIEW", "TASK_VIEW"}}),
        "no-task": ("limited", {"personal": {"PROJECT_VIEW", "BRIEF_BUILD"}}),
    })
    alice = host.authenticate("alice-token", "personal")
    bob = host.authenticate("bob-token", "personal")
    mallory = host.authenticate("mallory-token", "client")
    visitor = host.authenticate("no-build", "personal")
    limited = host.authenticate("no-task", "personal")
    registry = RegistryService(db, host, FixedClock(NOW))
    registry.create_scope(alice)
    registry.create_scope(mallory)
    p1 = registry.register_project(alice, "Demo projet A", "PACKAGE")
    p2 = registry.register_project(bob, "SECRET autre propriétaire", "PACKAGE")
    p3 = registry.register_project(mallory, "SECRET autre scope", "CLIENT")
    m0 = ProjectService(partial(SqliteUnitOfWork, db),
                        ExplicitPolicy({"alice": PERMISSIONS, "bob": PERMISSIONS,
                                        "mallory": PERMISSIONS}), FixedClock(NOW))
    t1 = m0.create_task(alice.legacy(), ProjectId(__import__("uuid").UUID(p1)), "Analyser le code de démonstration")
    t2 = m0.create_task(bob.legacy(), ProjectId(__import__("uuid").UUID(p2)), "SECRET task B")
    t3 = m0.create_task(mallory.legacy(), ProjectId(__import__("uuid").UUID(p3)), "SECRET task C")
    registry.attach_evidence(alice, p1, target_ref="repo", revision="a" * 40,
                             source_ref="SECRET PRIVATE EVIDENCE", classification="PRIVATE")
    work = WorkItemRef("TASK", str(t1.value))
    store = InMemoryMandateStore()
    mandate = DelegationMandate(
        mandate_id="trusted-mandate-001", actor_id="alice", delegate_id="pythos",
        scope_id="personal", project_id=p1, work_item_ref=work, mode="AUDIT",
        authority_level="A0", allowed_actions=("PROJECT_VIEW", "TASK_VIEW"),
        target_reference=REF, not_before=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(minutes=40),
    )
    store.provision(mandate)
    verifier = MandateVerifier(host, store)
    svc = BuildAuthorizedOperatingBrief(registry, verifier, FixedClock(NOW))
    req = BuildBriefRequest(mandate.mandate_id, p1, work, "AUDIT", REF)
    return locals()


def test_01_roundtrip_v1_and_canonical_serialization(workspace):
    brief = workspace["svc"].execute(workspace["alice"], workspace["req"])
    assert OperatingBriefDTO.from_json(brief.to_json()) == brief
    assert OperatingBriefDTO.from_dict(brief.to_dict()) == brief
    assert brief.to_json() == OperatingBriefDTO.from_json(brief.to_json()).to_json()
    assert brief.expires_at <= workspace["mandate"].expires_at
    assert brief.allowed_actions == ("PROJECT_VIEW", "TASK_VIEW")
    assert brief.mode == "AUDIT" and brief.authority_level == "A0"


def test_02_unknown_version_and_unknown_fields_rejected(workspace):
    raw = workspace["svc"].execute(workspace["alice"], workspace["req"]).to_dict()
    raw["schema_version"] = "9.0"
    with pytest.raises(UnsupportedContractVersion):
        OperatingBriefDTO.from_dict(raw)
    raw["schema_version"] = "1.0"
    raw["unexpected_sensitive_field"] = "not allowed"
    with pytest.raises(InvalidValue):
        OperatingBriefDTO.from_dict(raw)


def test_03_missing_field_invalid_timestamp_and_oversized_payload(workspace):
    raw = workspace["svc"].execute(workspace["alice"], workspace["req"]).to_dict()
    raw.pop("mode")
    with pytest.raises(InvalidValue):
        OperatingBriefDTO.from_dict(raw)
    raw = workspace["svc"].execute(workspace["alice"], workspace["req"]).to_dict()
    raw["expires_at"] = "2026-11-04T12:45:00"  # pas de fuseau
    with pytest.raises(InvalidValue):
        OperatingBriefDTO.from_dict(raw)
    with pytest.raises(InvalidValue):
        OperatingBriefDTO.from_json(" " * 20000)
    with pytest.raises(InvalidValue):
        OperatingBriefDTO.from_json('{"schema_version":"1.0","schema_version":"1.0"}')


def test_04_git_ref_needs_exact_commit():
    with pytest.raises(InvalidValue):
        ExactTargetReference("GIT_COMMIT", "repo", "main")
    with pytest.raises(InvalidValue):
        ExactTargetReference("GIT_COMMIT", "repo", "a" * 7)


def test_05_authorized_m1_context_no_sensitive_history(workspace):
    brief = workspace["svc"].execute(workspace["alice"], workspace["req"])
    data = brief.to_json()
    assert brief.problem == "Analyser le code de démonstration"
    assert brief.work_item_ref.id == workspace["work"].id
    assert brief.scope_id == "personal"
    assert "SECRET" not in data
    assert '"classification":' not in data
    assert "PROJECT_VIEW" in data and "TASK_VIEW" in data


def test_06_wrong_owner_and_cross_scope_never_leak(workspace):
    svc, req, alice = workspace["svc"], workspace["req"], workspace["alice"]
    for project_id, task in ((workspace["p2"], workspace["t2"]), (workspace["p3"], workspace["t3"])):
        forged = replace(req, project_id=project_id, work_item_ref=WorkItemRef("TASK", str(task.value)))
        with pytest.raises((AccessDenied, NotFound)) as err:
            svc.execute(alice, forged)
        assert "SECRET" not in str(err.value)


def test_07_missing_build_permission_fails_before_read(workspace):
    with pytest.raises(AccessDenied):
        workspace["svc"].execute(workspace["visitor"], workspace["req"])


def test_08_revoked_and_expired_mandates_rejected(workspace):
    workspace["store"].revoke(workspace["mandate"].mandate_id)
    with pytest.raises(AccessDenied):
        workspace["svc"].execute(workspace["alice"], workspace["req"])


def test_09_expired_mandate_rejected(workspace):
    older = replace(workspace["mandate"], mandate_id="expired",
                    not_before=NOW - timedelta(hours=2),
                    expires_at=NOW - timedelta(hours=1))
    workspace["store"].provision(older)
    with pytest.raises(AccessDenied):
        workspace["svc"].execute(workspace["alice"], replace(workspace["req"], mandate_id="expired"))


def test_10_wrong_delegate_wrong_actor_wrong_revision(workspace):
    host, store = workspace["host"], workspace["store"]
    with pytest.raises(AccessDenied):
        BuildAuthorizedOperatingBrief(
            workspace["registry"], MandateVerifier(host, store, delegate_id="fake-agent"),
            FixedClock(NOW)
        ).execute(workspace["alice"], workspace["req"])
    with pytest.raises(AccessDenied):
        workspace["svc"].execute(workspace["bob"], workspace["req"])
    with pytest.raises(AccessDenied):
        workspace["svc"].execute(
            workspace["alice"],
            replace(workspace["req"], target_reference=ExactTargetReference("GIT_COMMIT", "synthetic/repository", "b" * 40)),
        )


def test_11_request_cannot_claim_authority():
    with pytest.raises(TypeError):
        BuildBriefRequest(mandate_id="m", project_id="p", work_item_ref=WorkItemRef("TASK", "x"),
                          mode="AUDIT", target_reference=REF, authority_level="A3")


def test_12_audit_cannot_claim_mutation_or_a2(workspace):
    with pytest.raises(InvalidValue):
        replace(workspace["mandate"], authority_level="A2")
    with pytest.raises(InvalidValue):
        replace(workspace["mandate"], allowed_actions=("PROJECT_VIEW", "TASK_VIEW", "PUBLISH"))


def test_13_store_unavailable_fail_closed(workspace):
    class DeadStore:
        def resolve(self, mandate_id):
            raise ConnectionError("source hors ligne")
    svc = BuildAuthorizedOperatingBrief(
        workspace["registry"], MandateVerifier(workspace["host"], DeadStore()), FixedClock(NOW)
    )
    with pytest.raises(AccessDenied):
        svc.execute(workspace["alice"], workspace["req"])


def test_14_revocation_between_first_and_second_read(workspace, monkeypatch):
    registry, store = workspace["registry"], workspace["store"]
    original = registry.list_tasks
    state = [False]
    def revoked(*args, **kwargs):
        result = original(*args, **kwargs)
        if not state[0]:
            store.revoke(workspace["mandate"].mandate_id)
            state[0] = True
        return result
    monkeypatch.setattr(registry, "list_tasks", revoked)
    with pytest.raises(AccessDenied):
        workspace["svc"].execute(workspace["alice"], workspace["req"])
    assert state[0]


def test_15_nonmutation_no_state_change(workspace):
    db, actor, svc, req = workspace["db"], workspace["alice"], workspace["svc"], workspace["req"]
    with db.connection() as conn:
        before = (list(conn.execute("SELECT id,status,version FROM projects ORDER BY id")),
                  list(conn.execute("SELECT id,status,version FROM tasks ORDER BY id")),
                  list(conn.execute("SELECT seq,kind FROM history ORDER BY seq")))
        before = tuple(tuple(tuple(row) for row in group) for group in before)
    svc.execute(actor, req)
    with db.connection() as conn:
        after = (list(conn.execute("SELECT id,status,version FROM projects ORDER BY id")),
                 list(conn.execute("SELECT id,status,version FROM tasks ORDER BY id")),
                 list(conn.execute("SELECT seq,kind FROM history ORDER BY seq")))
        after = tuple(tuple(tuple(row) for row in group) for group in after)
    assert before == after


def test_16_private_scope_without_read_private_fails(tmp_path):
    db = SqliteDatabase(tmp_path / "private.sqlite")
    host = TrustedHost({"host": ("owner", {"secret-scope": {
        "SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "TASK_CREATE", "TASK_VIEW",
        "BRIEF_BUILD", "WRITE_PRIVATE"
    }})})
    actor = host.authenticate("host", "secret-scope")
    registry = RegistryService(db, host, FixedClock(NOW))
    registry.create_scope(actor, classification="PRIVATE")
    pid = registry.register_project(actor, "Secret", "PERSONAL")
    m0 = ProjectService(partial(SqliteUnitOfWork, db),
                        ExplicitPolicy({"owner": {"PROJECT_VIEW", "TASK_CREATE"}}), FixedClock(NOW))
    task = m0.create_task(actor.legacy(), ProjectId(__import__("uuid").UUID(pid)), "secret")
    work = WorkItemRef("TASK", str(task.value))
    store = InMemoryMandateStore()
    store.provision(DelegationMandate("m", "owner", "pythos", "secret-scope", pid, work, "AUDIT", "A0",
                                      ("PROJECT_VIEW", "TASK_VIEW"), REF,
                                      NOW - timedelta(minutes=1), NOW + timedelta(minutes=5)))
    svc = BuildAuthorizedOperatingBrief(registry, MandateVerifier(host, store), FixedClock(NOW))
    with pytest.raises(AccessDenied):
        svc.execute(actor, BuildBriefRequest("m", pid, work, "AUDIT", REF))


def test_17_m1_and_m2_must_share_host(workspace):
    separate = TrustedHost({"x": ("alice", {"personal": set(PERMISSIONS)})})
    with pytest.raises(InvalidValue):
        BuildAuthorizedOperatingBrief(
            workspace["registry"], MandateVerifier(separate, workspace["store"]), FixedClock(NOW)
        )


def test_18_end_to_end_authorized_brief(workspace):
    brief = workspace["svc"].execute(workspace["alice"], workspace["req"])
    assert brief.project_id == workspace["p1"]
    assert brief.source_watermark.startswith("m1:task:")
    assert len(brief.to_json().encode()) < 16_384
    assert all(word not in brief.to_json() for word in ("SECRET", "PRIVATE EVIDENCE"))
    assert "PUBLISH" not in brief.allowed_actions and "APPROVE" not in brief.allowed_actions
    assert brief.expires_at > NOW


def test_19_valid_mandate_cannot_override_m1_owner_visibility(workspace):
    # Mandat host-side volontairement trop permissif : M1 doit encore refuser le propriétaire.
    task_b = WorkItemRef("TASK", str(workspace["t2"].value))
    mandate = replace(workspace["mandate"], mandate_id="overbroad-host-mandate",
                      project_id=workspace["p2"], work_item_ref=task_b)
    workspace["store"].provision(mandate)
    req = BuildBriefRequest(mandate.mandate_id, workspace["p2"], task_b, "AUDIT", REF)
    with pytest.raises(NotFound, match="indisponible"):
        workspace["svc"].execute(workspace["alice"], req)


def test_20_concurrent_task_change_blocks_stale_brief(workspace, monkeypatch):
    original = workspace["registry"].list_tasks
    attempts = [0]
    def modified(*args, **kwargs):
        attempts[0] += 1
        rows = original(*args, **kwargs)
        if attempts[0] == 2:
            return tuple({**row, "version": "999"} for row in rows)
        return rows
    monkeypatch.setattr(workspace["registry"], "list_tasks", modified)
    from pyprojectkit import Conflict
    with pytest.raises(Conflict):
        workspace["svc"].execute(workspace["alice"], workspace["req"])
    assert attempts[0] == 2


def test_21_mandate_suspended_before_read(workspace):
    workspace["store"].suspend(workspace["mandate"].mandate_id)
    with pytest.raises(AccessDenied):
        workspace["svc"].execute(workspace["alice"], workspace["req"])


def test_22_explicit_same_scope_project_share_can_build(workspace):
    # La visibilité inter-owner requiert un droit explicite sur ce projet exact.
    pid = workspace["p1"]
    host = TrustedHost({"shared": ("reader", {"personal": {
        "PROJECT_VIEW", "TASK_VIEW", "BRIEF_BUILD", f"PROJECT_VIEW:{pid}"
    }})})
    reader = host.authenticate("shared", "personal")
    registry = RegistryService(workspace["db"], host, FixedClock(NOW))
    store = InMemoryMandateStore()
    original = workspace["mandate"]
    mandate = replace(original, mandate_id="shared-reader-mandate", actor_id="reader")
    store.provision(mandate)
    svc = BuildAuthorizedOperatingBrief(registry, MandateVerifier(host, store), FixedClock(NOW))
    brief = svc.execute(reader, replace(workspace["req"], mandate_id=mandate.mandate_id))
    assert brief.work_item_ref.id == workspace["work"].id
    assert brief.scope_id == "personal"


def test_23_expiration_during_projection_fails_closed(workspace, monkeypatch):
    clock = FixedClock(NOW)
    svc = BuildAuthorizedOperatingBrief(
        workspace["registry"], MandateVerifier(workspace["host"], workspace["store"]), clock
    )
    original = workspace["registry"].list_tasks
    def expire(*args, **kwargs):
        result = original(*args, **kwargs)
        clock.value = NOW + timedelta(hours=1)
        return result
    monkeypatch.setattr(workspace["registry"], "list_tasks", expire)
    with pytest.raises(AccessDenied):
        svc.execute(workspace["alice"], workspace["req"])


def test_24_private_scope_still_denied_with_owner_read_private(tmp_path):
    # Le droit personnel READ_PRIVATE n'est pas délégable implicitement à Pythos.
    db = SqliteDatabase(tmp_path / "private-with-rights.sqlite")
    permissions = {"SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "TASK_CREATE",
                   "TASK_VIEW", "BRIEF_BUILD", "READ_PRIVATE", "WRITE_PRIVATE"}
    host = TrustedHost({"owner-key": ("owner", {"private-scope": permissions})})
    actor = host.authenticate("owner-key", "private-scope")
    registry = RegistryService(db, host, FixedClock(NOW))
    registry.create_scope(actor, classification="PRIVATE")
    pid = registry.register_project(actor, "Projet privé fictif", "PERSONAL")
    core = ProjectService(partial(SqliteUnitOfWork, db),
                          ExplicitPolicy({"owner": permissions}), FixedClock(NOW))
    tid = core.create_task(actor.legacy(), ProjectId(__import__("uuid").UUID(pid)), "Titre privé")
    work = WorkItemRef("TASK", str(tid.value))
    store = InMemoryMandateStore()
    store.provision(DelegationMandate(
        "private-mandate", "owner", "pythos", "private-scope", pid, work,
        "AUDIT", "A0", ("PROJECT_VIEW", "TASK_VIEW"), REF,
        NOW - timedelta(minutes=1), NOW + timedelta(minutes=30)
    ))
    svc = BuildAuthorizedOperatingBrief(registry, MandateVerifier(host, store), FixedClock(NOW))
    with pytest.raises(AccessDenied):
        svc.execute(actor, BuildBriefRequest("private-mandate", pid, work, "AUDIT", REF))


def test_25_brief_cannot_be_returned_after_own_ttl(workspace, monkeypatch):
    clock = FixedClock(NOW)
    svc = BuildAuthorizedOperatingBrief(
        workspace["registry"], MandateVerifier(workspace["host"], workspace["store"]), clock
    )
    original = workspace["registry"].list_tasks
    def slow_projection(*args, **kwargs):
        output = original(*args, **kwargs)
        clock.value = NOW + timedelta(minutes=25)  # mandat valide, TTL du brief dépassé
        return output
    monkeypatch.setattr(workspace["registry"], "list_tasks", slow_projection)
    with pytest.raises(AccessDenied):
        svc.execute(workspace["alice"], workspace["req"])


def test_26_signed_uri_or_credential_ref_not_projected():
    for value in ("https://private.example/file?token=secret", "user@example.local", "repo#access"):
        with pytest.raises(InvalidValue):
            ExactTargetReference("GIT_COMMIT", value, "a" * 40)
