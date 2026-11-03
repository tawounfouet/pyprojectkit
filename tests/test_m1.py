from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from uuid import UUID
import json
import sqlite3
import subprocess
import sys

import pytest

from pyprojectkit import (
    AccessDenied, ActorContext, Conflict, Dependency, DependencyViolation, ExplicitPolicy, FixedClock,
    InvalidStateTransition, NotFound, ProjectId, ProjectService, ProjectStatus, TaskId, TaskStatus,
)
from pyprojectkit.m1 import (
    AssessmentResult, Family, PortfolioDecision, RegistryService, ScopeRule,
    SqliteDatabase, SqliteUnitOfWork, TrustedHost, VerifiedActor, migrate,
)

NOW = datetime(2026, 11, 3, 12, tzinfo=timezone.utc)
M0_PERMS = {
    "PROJECT_CREATE", "PROJECT_VIEW", "PROJECT_PLAN", "PROJECT_START", "PROJECT_EDIT",
    "PROJECT_COMPLETE", "TASK_CREATE", "TASK_VIEW", "TASK_EDIT", "TASK_ASSIGN", "TASK_START",
    "TASK_COMPLETE", "MILESTONE_CREATE", "MILESTONE_EDIT",
}
ALL = M0_PERMS | {
    "SCOPE_CREATE", "EXTERNAL_LINK", "EXTERNAL_READ", "ASSESS", "RESOLVE", "APPROVE", "CAPTURE", "RESUME", "EXPORT",
    *("READ_"+x for x in ("CLAIM", "OBSERVATION", "EVIDENCE", "ASSESSMENT", "RECONCILIATION",
                              "RESOLUTION", "DECISION", "APPROVAL", "BLOCKER", "SNAPSHOT", "HANDOFF")),
    *("WRITE_"+x for x in ("CLAIM", "OBSERVATION", "EVIDENCE", "ASSESSMENT", "RECONCILIATION",
                               "RESOLUTION", "DECISION", "APPROVAL", "BLOCKER", "SNAPSHOT", "HANDOFF")),
    "WRITE_PRIVATE", "READ_PRIVATE",
}


@pytest.fixture
def env(tmp_path: Path):
    path = tmp_path / "durable.sqlite"
    db = SqliteDatabase(path)
    grants = {
        "good": ("alice", {"a": set(ALL), "b": set(ALL)}),
        "restricted": ("bob", {"a": {"PROJECT_VIEW", "PROJECT_VIEW_ALL", "TASK_VIEW", "RESUME", "READ_OBSERVATION",
                                    "READ_SNAPSHOT", "READ_HANDOFF", "READ_DECISION"}}),
        "outsider": ("mallory", {"b": set(ALL)}),
    }
    host = TrustedHost(grants, rules={"b": ScopeRule(require_pass_for_publish=False)})
    a = host.authenticate("good", "a")
    b = host.authenticate("outsider", "b")
    service = RegistryService(db, host, FixedClock(NOW))
    service.create_scope(a)
    service.create_scope(b)
    return db, host, service, a, b


def test_m1_01_sqlite_m0_project_task_milestone_graph_and_restart(env):
    db, _, _, _, _ = env
    actor = ActorContext("owner", "a")
    s = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"owner": M0_PERMS}), FixedClock(NOW))
    pid = s.create_project(actor, "M0 persisté", "owner")
    a, b = [s.create_task(actor, pid, n) for n in ("A", "B")]
    mid = s.add_milestone(actor, pid, "Release", date(2027, 1, 1))
    s.add_dependency(actor, b, a)
    s.transition_project(actor, pid, ProjectStatus.PLANNED)
    db2 = SqliteDatabase(db.path)
    new = ProjectService(partial(SqliteUnitOfWork, db2), ExplicitPolicy({"owner": M0_PERMS}), FixedClock(NOW))
    assert new.get_project(actor, pid).milestones[mid].target_date == date(2027, 1, 1)
    assert new.get_project(actor, pid).status == ProjectStatus.PLANNED
    assert new.get_task(actor, a).version == 1
    with SqliteUnitOfWork(db2) as tx:
        _, edges = tx.dependencies.snapshot(pid)
        assert Dependency(b, a) in edges
    with pytest.raises(DependencyViolation):
        new.add_dependency(actor, a, b)
    assert db2.events == []  # événements observables du processus, pas Outbox


def test_m1_sqlite_atomic_rollback_versions_fk_and_backup(env, tmp_path):
    db, _, _, _, _ = env
    actor = ActorContext("owner", "a")
    s = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"owner": M0_PERMS}), FixedClock(NOW))
    pid = s.create_project(actor, "Etat stable", "owner")
    with SqliteUnitOfWork(db) as uow:
        p = uow.projects.get(pid)
        assert p
        p.name = "mutation non persistée"
        uow.projects.save(p, expected_version=p.version)
    assert s.get_project(actor, pid).name == "Etat stable"
    with pytest.raises(RuntimeError):
        with SqliteUnitOfWork(db) as uow:
            p = uow.projects.get(pid)
            assert p
            p.name = "rollback exception"
            uow.projects.save(p, expected_version=p.version)
            raise RuntimeError("crash simulé avant commit")
    assert s.get_project(actor, pid).name == "Etat stable"
    old = s.get_project(actor, pid)
    with SqliteUnitOfWork(db) as uow:
        p = uow.projects.get(pid)
        assert p
        p.name = "nouveau"
        uow.projects.save(p, expected_version=p.version)
        uow.commit()
    with SqliteUnitOfWork(db) as uow:
        old.name = "obsolète"
        with pytest.raises(Conflict):
            uow.projects.save(old, expected_version=old.version)
    copy_path = tmp_path / "backup.sqlite"
    db.backup(copy_path)
    restored = ProjectService(partial(SqliteUnitOfWork, SqliteDatabase(copy_path)),
                              ExplicitPolicy({"owner": M0_PERMS}), FixedClock(NOW))
    assert restored.get_project(actor, pid).name == "nouveau"
    with db.connection() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO tasks(id,project_id,title,status,version,progress) VALUES(?,?,?,?,?,?)",
                         (str(UUID(int=999)), str(UUID(int=998)), "bad", "TODO", 1, 0))


def test_migrations_idempotent_checksum_and_unknown_version(env):
    db, *_ = env
    migrate(db.path)
    with db.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 2
        c.execute("UPDATE schema_migrations SET checksum=? WHERE version=2", ("tampered",))
    with pytest.raises(Conflict, match="modifiée"):
        migrate(db.path)


def test_verified_host_rejects_forged_scope_and_credentials(env):
    _db, host, svc, a, _b = env
    pid = svc.register_project(a, "Secret", "PACKAGE")
    with pytest.raises(AccessDenied):
        host.authenticate("good", "outsider-scope")
    with pytest.raises(AccessDenied):
        host.authenticate("random", "a")
    fake = VerifiedActor(a.actor_id, a.scope_id, a._issuer, "forged-nonce")
    with pytest.raises(AccessDenied):
        svc.get_registry(fake, pid)
    # Deux credentials du même actor n'additionnent pas silencieusement les droits.
    h2 = TrustedHost({"weak": ("same", {"a": {"PROJECT_VIEW"}}),
                      "strong": ("same", {"a": {"PROJECT_VIEW", "APPROVE"}})})
    with pytest.raises(AccessDenied):
        h2.require(h2.authenticate("weak", "a"), "APPROVE")


def test_ac013_ac014_five_families_registry_facets_scope_pagination(env):
    _db, host, svc, a, b = env
    ids = [svc.register_project(a, f"Synthetic-{family.value}", family.value, priority=i*10)
           for i, family in enumerate(Family)]
    foreign = svc.register_project(b, "Client secret", Family.CLIENT)
    page = svc.list_registry(a, limit=2, offset=1)
    assert page.total == 5
    assert len(page.items) == 2 and sum(page.facets.values()) == 5
    assert set(page.facets) == {x.value for x in Family}
    assert svc.list_registry(a, family="PACKAGE").total == 1
    assert svc.list_registry(a, offset=50).items == ()
    with pytest.raises(NotFound):
        svc.get_registry(a, foreign)
    assert svc.list_registry(b).total == 1
    assert svc.get_registry(a, ids[0]).family == Family.PACKAGE
    assert all(x.scope_id == "a" for x in page.items)
    reader = host.authenticate("restricted", "a")
    assert svc.list_registry(reader).total == 5
    with pytest.raises(AccessDenied):
        svc.register_project(reader, "No", "PACKAGE")


def test_external_refs_identity_scope_unique_and_no_cross_lookup(env):
    _db, _, svc, a, b = env
    p = svc.register_project(a, "one", "PRODUCT")
    q = svc.register_project(b, "two", "PRODUCT")
    ref = svc.link_external(a, p, "GITHUB", "sha123", uri="https://example.invalid/dummy")
    assert ref in {x["id"] for x in svc.list_external(a, p)}
    with pytest.raises(Conflict):
        svc.link_external(a, p, "GITHUB", "sha123")
    with pytest.raises(NotFound):
        svc.list_external(a, q)
    assert svc.list_external(b, q) == ()


def test_ac016_019_021_evidence_unknown_and_sha_specific(env):
    db, _, svc, a, _ = env
    p = svc.register_project(a, "CI", "PACKAGE")
    broken = svc.attach_evidence(a, p, target_ref="repo", revision="sha-a", source_ref="missing", available=False)
    with pytest.raises(Conflict):
        svc.assess(a, p, evidence_id=broken, target_ref="repo", revision="sha-a",
                   criterion="CI", result=AssessmentResult.PASS, method="github")
    unknown = svc.assess(a, p, evidence_id=broken, target_ref="repo", revision="sha-a",
                         criterion="CI", result=AssessmentResult.UNKNOWN, method="offline")
    evidence = svc.attach_evidence(a, p, target_ref="repo", revision="sha-a", source_ref="ci-run:1")
    with pytest.raises(Conflict):
        svc.assess(a, p, evidence_id=evidence, target_ref="repo", revision="sha-b",
                   criterion="CI", result=AssessmentResult.PASS, method="ci")
    passed = svc.assess(a, p, evidence_id=evidence, target_ref="repo", revision="sha-a",
                        criterion="CI", result=AssessmentResult.PASS, method="ci")
    assert passed != unknown
    assert svc.verify_status(a, p, target_ref="repo", revision="sha-a", criterion="CI") == "PASS"
    assert svc.verify_status(a, p, target_ref="repo", revision="sha-b", criterion="CI") == "UNKNOWN"
    assert svc.get_registry(a, p).project_status == "DRAFT"  # PASS != état métier
    with db.connection() as c:
        with pytest.raises(sqlite3.IntegrityError):
            c.execute("DELETE FROM history WHERE id=?", (passed,))
        with pytest.raises(sqlite3.IntegrityError):
            c.execute("UPDATE history SET payload='{}' WHERE id=?", (passed,))


def test_ac020_observation_conflict_keeps_both_and_resolution(env):
    _db, _, svc, a, _ = env
    p = svc.register_project(a, "contradiction", "CLIENT")
    first = svc.observe(a, p, subject="delivery", value="yes", source_ref="source:a", observed_at=NOW)
    second = svc.observe(a, p, subject="delivery", value="no", source_ref="source:b", observed_at=NOW)
    case = svc.open_reconciliation(a, p, first, second)
    resume = svc.resume(a, p)
    assert len(resume.unresolved_cases) == 1
    assert len(svc.list_history(a, p, "observation")) == 2
    svc.resolve_reconciliation(a, p, case, "Deux sources conservées")
    assert svc.resume(a, p).unresolved_cases == ()
    assert len(svc.list_history(a, p, "observation")) == 2
    with pytest.raises(Conflict):
        svc.resolve_reconciliation(a, p, case, "once")


def test_ac017_023_publication_policy_portfolio_separate_from_hold(env):
    db, _, svc, a, b = env
    project = svc.register_project(a, "package", "PACKAGE")
    soft = svc.register_project(b, "classe", "TEACHING")
    with pytest.raises(Conflict):
        svc.approve_publication(a, project, target_ref="repo", revision="sha-a", criterion="RELEASE")
    decision = svc.record_decision(a, project, subject="portfolio", statement="PARK on portfolio",
                                   portfolio=PortfolioDecision.PARK)
    svc.approve_decision(a, project, decision)
    assert svc.get_registry(a, project).project_status == "DRAFT"
    assert svc.list_history(a, project, "decision")[0]["portfolio"] == "PARK"
    # Le scope b autorise une policy pédagogique plus souple, sans faux PASS créé.
    approved = svc.approve_publication(b, soft, target_ref="teaching", revision="v1", criterion="POST")
    assert approved
    assert svc.verify_status(b, soft, target_ref="teaching", revision="v1", criterion="POST") == "UNKNOWN"


def test_ac024_scope_counts_pages_exports_child_privacy_and_approval(env):
    _db, host, svc, a, b = env
    p = svc.register_project(a, "private", "CLIENT")
    hidden = svc.register_project(b, "hidden", "CLIENT")
    reader = host.authenticate("restricted", "a")
    svc.observe(a, p, subject="public", value="value", source_ref="source", observed_at=NOW)
    svc.observe(a, p, subject="private", value="very-secret", source_ref="source", observed_at=NOW,
                classification="PRIVATE")
    assert svc.list_registry(reader).total == 1
    assert svc.list_registry(reader).facets == {"CLIENT": 1}
    assert len(svc.list_history(reader, p, "observation")) == 1
    assert "very-secret" not in repr(svc.resume(reader, p))
    with pytest.raises(AccessDenied):
        svc.export_project(reader, p)
    with pytest.raises(NotFound):
        svc.resume(a, hidden)
    assert svc.list_registry(a, offset=1).total == 1
    assert svc.list_registry(a, offset=1).items == ()
    with pytest.raises(AccessDenied):
        svc.approve_decision(reader, p, str(UUID(int=9)))


def test_ac015_022_snapshot_handoff_resume_across_process_and_no_next(env):
    db, host, svc, a, _ = env
    p = svc.register_project(a, "reprise", "PERSONAL")
    svc.observe(a, p, subject="state", value="current", source_ref="src:1", observed_at=NOW)
    decision = svc.record_decision(a, p, subject="scope", statement="Keep")
    handoff_id = svc.record_handoff(a, p, summary="Reprise à effectuer", outcome="IN_PROGRESS", unknowns=["CI?"], risks=["bug"])
    snapshot_id = svc.capture_snapshot(a, p)
    another_db = SqliteDatabase(db.path)
    another_host = TrustedHost({"valid": ("alice", {"a": set(ALL)})})
    new_actor = another_host.authenticate("valid", "a")
    resume = RegistryService(another_db, another_host).resume(new_actor, p)
    assert resume.project.name == "reprise"
    assert resume.latest_snapshot and resume.latest_snapshot["id"] == snapshot_id
    assert resume.latest_handoff and resume.latest_handoff["id"] == handoff_id
    assert any(x["id"] == decision for x in resume.decisions)
    assert resume.next_action.task_id is None and "NONE_WITH_REASON" in resume.next_action.reason
    assert resume.source_freshness.startswith("2026-11-03")
    # Vérification réelle du second interpréteur (aucune mémoire de conversation).
    code = '''import sys, json
from pyprojectkit.m1 import SqliteDatabase, TrustedHost, RegistryService
host=TrustedHost({"valid":("alice",{"a":set(%r)})})
actor=host.authenticate("valid","a")
ctx=RegistryService(SqliteDatabase(sys.argv[1]),host).resume(actor,sys.argv[2])
print(json.dumps({"name":ctx.project.name,"snapshot":ctx.latest_snapshot["id"],"handoff":ctx.latest_handoff["id"]}))
''' % sorted(ALL)
    run = subprocess.run([sys.executable, "-c", code, str(db.path), p], text=True, capture_output=True,
                         check=True)
    result = json.loads(run.stdout)
    assert result == {"name": "reprise", "snapshot": snapshot_id, "handoff": handoff_id}


def test_snapshot_immutable_and_current_state_not_replaced(env):
    db, _, svc, a, _ = env
    p = svc.register_project(a, "init", "PRODUCT")
    old = svc.capture_snapshot(a, p)
    # Modifier le projet M0 indépendamment de la projection, le snapshot reste historique.
    actor = ActorContext("alice", "a")
    m0 = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"alice": M0_PERMS}), FixedClock(NOW))
    m0.transition_project(actor, ProjectId(UUID(p)), ProjectStatus.PLANNED)
    cur = svc.resume(a, p)
    assert cur.project.project_status == "PLANNED"
    assert cur.latest_snapshot and cur.latest_snapshot["project_status"] == "DRAFT"
    assert cur.latest_snapshot["id"] == old


def test_two_processes_graph_serialization(env):
    db, _host, _svc, _, _ = env
    actor = ActorContext("owner", "a")
    m0 = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"owner": M0_PERMS}), FixedClock(NOW))
    pid = m0.create_project(actor, "concurrence", "owner")
    a = m0.create_task(actor, pid, "A")
    b = m0.create_task(actor, pid, "B")
    proc_code = '''from pyprojectkit.m1 import SqliteDatabase, SqliteUnitOfWork
from pyprojectkit import Dependency, ProjectId, TaskId, DependencyViolation
from uuid import UUID
import sys, time
p=ProjectId(UUID(sys.argv[2])); successor=TaskId(UUID(sys.argv[3])); predecessor=TaskId(UUID(sys.argv[4]))
try:
 with SqliteUnitOfWork(SqliteDatabase(sys.argv[1])) as u:
  v, edges = u.dependencies.snapshot(p)
  time.sleep(0.05)
  u.dependencies.replace_if_version(p,expected_version=v,edges=edges|{Dependency(successor,predecessor)})
  u.commit()
 print('COMMIT')
except DependencyViolation:
 print('REJECT')
'''
    p1 = subprocess.Popen([sys.executable, "-c", proc_code, str(db.path), str(pid.value), str(a.value), str(b.value)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p2 = subprocess.Popen([sys.executable, "-c", proc_code, str(db.path), str(pid.value), str(b.value), str(a.value)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    o1, e1 = p1.communicate(timeout=20)
    o2, e2 = p2.communicate(timeout=20)
    assert p1.returncode == 0, e1
    assert p2.returncode == 0, e2
    assert sorted([o1.strip(), o2.strip()]) == ["COMMIT", "REJECT"]
    with SqliteUnitOfWork(db) as uow:
        _version, edges = uow.dependencies.snapshot(pid)
        assert len(edges) == 1


def test_cli_demo_mode_refuses_untrusted_without_flag(tmp_path: Path):
    cmd = [sys.executable, "-m", "pyprojectkit.m1.cli", "--db", str(tmp_path/"demo.sqlite"), "init"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode != 0
    assert "--demo" in r.stderr
    cmd.insert(3, "--demo")
    ok = subprocess.run(cmd, capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    assert json.loads(ok.stdout)["initialized"]


def test_real_process_crash_before_commit_does_not_persist(env):
    db, _, _, _, _ = env
    actor = ActorContext("owner", "a")
    m0 = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"owner": M0_PERMS}), FixedClock(NOW))
    pid = m0.create_project(actor, "durable", "owner")
    cmd = '''from pyprojectkit.m1 import SqliteDatabase,SqliteUnitOfWork
from pyprojectkit import ProjectId
from uuid import UUID
import os,sys
with SqliteUnitOfWork(SqliteDatabase(sys.argv[1])) as u:
 p=u.projects.get(ProjectId(UUID(sys.argv[2])))
 p.name="interrupted"
 u.projects.save(p,expected_version=p.version)
 os._exit(0)
'''
    p = subprocess.run([sys.executable, "-c", cmd, str(db.path), str(pid.value)], capture_output=True, text=True)
    assert p.returncode == 0
    assert m0.get_project(actor, pid).name == "durable"


def test_private_snapshot_requires_private_read(env):
    _db, host, svc, a, _ = env
    pid = svc.register_project(a, "restricted", "CLIENT")
    svc.observe(a, pid, subject="private", value="SECRET-M1", source_ref="s", observed_at=NOW,
                classification="PRIVATE")
    svc.capture_snapshot(a, pid)
    limited = host.authenticate("restricted", "a")
    visible = svc.resume(limited, pid)
    assert visible.latest_snapshot is None
    assert visible.latest_observation is None
    assert "SECRET-M1" not in repr(visible)
    assert len(svc.list_history(limited, pid, "snapshot")) == 0


def test_claim_not_automatically_evidence_or_approval(env):
    _db, _, svc, a, _ = env
    pid = svc.register_project(a, "claims", "PACKAGE")
    svc.record_claim(a, pid, subject="package", statement="deployed", source_ref="human")
    assert svc.verify_status(a, pid, target_ref="package", revision="v1", criterion="DEPLOYED") == "UNKNOWN"
    assert svc.list_history(a, pid, "assessment") == ()
    assert svc.list_history(a, pid, "approval") == ()


def test_scope_classification_does_not_override_verified_host(env):
    db, host, svc, a, _ = env
    with pytest.raises(AccessDenied):
        svc.register_project(VerifiedActor(a.actor_id, "b", a._issuer, a._nonce), "forged", "PACKAGE")
    with db.connection() as c:
        assert c.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0


def test_scope_private_classification_requires_read_private(tmp_path: Path):
    db = SqliteDatabase(tmp_path / "private.sqlite")
    perms = {"SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "WRITE_PRIVATE", "READ_PRIVATE", "TASK_VIEW", "RESUME"}
    host = TrustedHost({"owner": ("alice", {"private": perms}),
                        "limited": ("bob", {"private": {"PROJECT_VIEW", "PROJECT_VIEW_ALL", "RESUME", "TASK_VIEW"}})})
    owner = host.authenticate("owner", "private")
    svc = RegistryService(db, host)
    svc.create_scope(owner, classification="PRIVATE")
    p = svc.register_project(owner, "private meta", "CLIENT")
    limited = host.authenticate("limited", "private")
    with pytest.raises(AccessDenied):
        svc.list_registry(limited)
    with pytest.raises(AccessDenied):
        svc.get_registry(limited, p)
    with pytest.raises(AccessDenied):
        svc.resume(limited, p)


def test_ac021_done_task_does_not_approve_anything(env):
    db, _host, svc, a, _ = env
    pid = svc.register_project(a, "package", "PACKAGE")
    actor = ActorContext("alice", "a")
    m0 = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"alice": M0_PERMS}), FixedClock(NOW))
    project_id = ProjectId(UUID(pid))
    m0.transition_project(actor, project_id, ProjectStatus.PLANNED)
    m0.transition_project(actor, project_id, ProjectStatus.ACTIVE)
    tid = m0.create_task(actor, project_id, "done")
    m0.transition_task(actor, tid, TaskStatus.READY)
    m0.transition_task(actor, tid, TaskStatus.IN_PROGRESS)
    m0.transition_task(actor, tid, TaskStatus.DONE)
    assert m0.get_task(actor, tid).status == TaskStatus.DONE
    assert svc.list_history(a, pid, "approval") == ()
    assert svc.verify_status(a, pid, target_ref="release", revision="sha1", criterion="APPROVED") == "UNKNOWN"


def test_ac023_portfolio_park_is_independent_from_project_on_hold(env):
    db, _, svc, a, _ = env
    pid = svc.register_project(a, "bundle", "PACKAGE")
    actor = ActorContext("alice", "a")
    m0 = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"alice": M0_PERMS}), FixedClock(NOW))
    project_id = ProjectId(UUID(pid))
    m0.transition_project(actor, project_id, ProjectStatus.PLANNED)
    m0.transition_project(actor, project_id, ProjectStatus.ACTIVE)
    m0.transition_project(actor, project_id, ProjectStatus.ON_HOLD)
    did = svc.record_decision(a, pid, subject="portfolio", statement="PARK", portfolio=PortfolioDecision.PARK)
    assert did
    assert svc.get_registry(a, pid).project_status == "ON_HOLD"
    assert svc.list_history(a, pid, "decision")[-1]["portfolio"] == "PARK"


def test_ac025_personal_finance_fixture_has_no_sensitive_raw_data(env):
    db, _, svc, actor, _ = env
    pid = svc.register_project(actor, "Finance fictive", "PERSONAL")
    svc.record_blocker(actor, pid, "Données réelles non importées")
    result = svc.export_project(actor, pid)
    assert result["project"]["family"] == "PERSONAL"
    with db.connection() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert not tables.intersection({"bank_transactions", "account_statements", "payment_cards"})


def test_ac015_full_resume_after_restart_includes_open_task_snapshot_decision_and_handoff(env):
    db, host, svc, actor, _ = env
    pid = svc.register_project(actor, "full restart", "PACKAGE")
    m0 = ProjectService(partial(SqliteUnitOfWork, db), ExplicitPolicy({"alice": M0_PERMS}), FixedClock(NOW))
    task = m0.create_task(ActorContext("alice", "a"), ProjectId(UUID(pid)), "Task après redémarrage")
    decision = svc.record_decision(actor, pid, subject="architecture", statement="SQLite pilote")
    snapshot = svc.capture_snapshot(actor, pid)
    handoff = svc.record_handoff(actor, pid, summary="Continuer la tâche", outcome="IN_PROGRESS")
    code = '''import sys,json
from pyprojectkit.m1 import TrustedHost, SqliteDatabase, RegistryService
host=TrustedHost({"t":("alice",{"a":set(%r)})})
ctx=RegistryService(SqliteDatabase(sys.argv[1]),host).resume(host.authenticate("t","a"),sys.argv[2])
print(json.dumps({"open":list(ctx.open_tasks), "decisions":list(ctx.decisions),
 "snapshot":ctx.latest_snapshot["id"],"handoff":ctx.latest_handoff["id"],
 "next_id":ctx.next_action.task_id}))
''' % sorted(ALL)
    other = subprocess.run([sys.executable, "-c", code, str(db.path), pid], check=True,
                           capture_output=True, text=True)
    data = json.loads(other.stdout)
    assert data["open"][0]["id"] == str(task.value)
    assert any(x["id"] == decision for x in data["decisions"])
    assert data["snapshot"] == snapshot
    assert data["handoff"] == handoff
    assert data["next_id"] == str(task.value)


def test_security_same_scope_does_not_imply_cross_owner_access(tmp_path: Path):
    """Régression : PROJECT_VIEW seul ne révèle pas un projet d'un autre owner."""
    db = SqliteDatabase(tmp_path / "owned.sqlite")
    permissions = {"PROJECT_VIEW", "TASK_VIEW", "RESUME", "EXPORT", "EXTERNAL_READ"}
    host = TrustedHost({
        "alice-secret": ("alice", {"team": permissions | {"SCOPE_CREATE", "PROJECT_CREATE"}}),
        "bob-secret": ("bob", {"team": permissions}),
        "admin-secret": ("charlie", {"team": permissions | {"PROJECT_VIEW_ALL"}}),
    })
    svc = RegistryService(db, host)
    alice = host.authenticate("alice-secret", "team")
    bob = host.authenticate("bob-secret", "team")
    admin = host.authenticate("admin-secret", "team")
    svc.create_scope(alice)
    project_id = svc.register_project(alice, "Projet privé non partagé", "PERSONAL")
    assert svc.list_registry(bob).total == 0
    assert svc.list_registry(bob).facets == {}
    assert svc.list_registry(bob, offset=50).items == ()
    for read in [
        lambda: svc.get_registry(bob, project_id),
        lambda: svc.list_tasks(bob, project_id),
        lambda: svc.list_external(bob, project_id),
        lambda: svc.resume(bob, project_id),
        lambda: svc.export_project(bob, project_id),
    ]:
        with pytest.raises(NotFound, match="Ressource indisponible"):
            read()
    assert svc.get_registry(admin, project_id).owner_id == "alice"
    assert svc.list_registry(admin).total == 1
    # Une ressource peut aussi être partagée individuellement par permission ciblée.
    host2 = TrustedHost({"reader": ("bob", {"team": permissions | {f"PROJECT_VIEW:{project_id}"}})})
    assert RegistryService(db, host2).get_registry(host2.authenticate("reader", "team"), project_id).name == "Projet privé non partagé"