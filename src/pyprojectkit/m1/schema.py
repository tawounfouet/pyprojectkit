"""Migrations SQLite incrémentales et contrôlées par empreinte (ADR-M1-02)."""
from __future__ import annotations

from hashlib import sha256
import re
import sqlite3
from pathlib import Path

from ..domain import Conflict

MIGRATIONS: tuple[tuple[int, str], ...] = (
    (1, """
CREATE TABLE projects (
    id TEXT PRIMARY KEY, name TEXT NOT NULL, owner_id TEXT NOT NULL,
    scope TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL CHECK(version >= 1),
    actual_start_at TEXT, actual_end_at TEXT
);
CREATE INDEX idx_projects_scope ON projects(scope);
CREATE TABLE project_milestones (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
    name TEXT NOT NULL, target_date TEXT NOT NULL, reached_at TEXT
);
CREATE TABLE tasks (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL CHECK(version >= 1),
    assignee_id TEXT, block_reason TEXT, actual_start_at TEXT, actual_end_at TEXT,
    progress INTEGER NOT NULL CHECK(progress BETWEEN 0 AND 100)
);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE TABLE dependency_graph_versions (
    project_id TEXT PRIMARY KEY REFERENCES projects(id), version INTEGER NOT NULL CHECK(version >= 0)
);
CREATE TABLE task_dependencies (
    project_id TEXT NOT NULL REFERENCES projects(id),
    successor_id TEXT NOT NULL REFERENCES tasks(id),
    predecessor_id TEXT NOT NULL REFERENCES tasks(id),
    PRIMARY KEY(project_id, successor_id, predecessor_id),
    CHECK(successor_id <> predecessor_id)
);
CREATE TABLE event_history (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, project_or_aggregate_id TEXT NOT NULL,
    event_name TEXT NOT NULL, occurred_at TEXT NOT NULL, actor_id TEXT NOT NULL
);
"""),
    (2, """
CREATE TABLE context_scopes (
    id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, classification TEXT NOT NULL,
    policy_ref TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE project_registry (
    project_id TEXT PRIMARY KEY REFERENCES projects(id), scope_id TEXT NOT NULL REFERENCES context_scopes(id),
    family TEXT NOT NULL, priority INTEGER NOT NULL CHECK(priority BETWEEN 0 AND 100),
    due_date TEXT, registered_at TEXT NOT NULL
);
CREATE INDEX idx_registry_scope_family ON project_registry(scope_id, family);
CREATE TABLE external_references (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
    scope_id TEXT NOT NULL REFERENCES context_scopes(id), provider TEXT NOT NULL,
    external_id TEXT NOT NULL, relation_type TEXT NOT NULL, uri TEXT,
    recorded_at TEXT NOT NULL,
    UNIQUE(scope_id,provider,external_id,relation_type)
);
CREATE INDEX idx_external_project_scope ON external_references(project_id,scope_id);
CREATE TABLE history (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL, project_id TEXT NOT NULL REFERENCES projects(id),
    scope_id TEXT NOT NULL REFERENCES context_scopes(id),
    classification TEXT NOT NULL CHECK(classification IN ('INTERNAL','PRIVATE')),
    recorded_at TEXT NOT NULL, payload TEXT NOT NULL
);
CREATE INDEX idx_history_lookup ON history(scope_id, project_id, kind, seq);
CREATE TRIGGER history_no_update BEFORE UPDATE ON history
BEGIN SELECT RAISE(ABORT, 'append-only'); END;
CREATE TRIGGER history_no_delete BEFORE DELETE ON history
BEGIN SELECT RAISE(ABORT, 'append-only'); END;
"""),

    (3, """
CREATE TABLE m2_issued_briefs (
    brief_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL REFERENCES context_scopes(id),
    project_id TEXT NOT NULL REFERENCES projects(id),
    task_id TEXT NOT NULL REFERENCES tasks(id),
    mandate_id TEXT NOT NULL, issuer_id TEXT NOT NULL,
    mode TEXT NOT NULL, target_type TEXT NOT NULL,
    target_resource TEXT NOT NULL, target_revision TEXT NOT NULL,
    source_watermark TEXT NOT NULL, schema_version TEXT NOT NULL,
    issued_at TEXT NOT NULL, expires_at TEXT NOT NULL,
    brief_fingerprint TEXT NOT NULL
);
CREATE INDEX idx_m2_briefs_project ON m2_issued_briefs(scope_id,project_id,task_id);
CREATE TABLE m2_report_inbox (
    ingestion_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL REFERENCES context_scopes(id),
    project_id TEXT NOT NULL REFERENCES projects(id),
    task_id TEXT NOT NULL REFERENCES tasks(id),
    mandate_id TEXT NOT NULL, brief_id TEXT NOT NULL REFERENCES m2_issued_briefs(brief_id),
    report_id TEXT NOT NULL, idempotency_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL, payload_json TEXT NOT NULL,
    received_at TEXT NOT NULL, received_by TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status='ACCEPTED_AS_DECLARATION'),
    UNIQUE(scope_id,mandate_id,report_id),
    UNIQUE(scope_id,mandate_id,idempotency_key)
);
CREATE INDEX idx_m2_reports_project ON m2_report_inbox(scope_id,project_id,task_id,received_at);
CREATE TABLE m2_report_links (
    ingestion_id TEXT NOT NULL REFERENCES m2_report_inbox(ingestion_id),
    history_id TEXT NOT NULL REFERENCES history(id) DEFERRABLE INITIALLY DEFERRED,
    kind TEXT NOT NULL CHECK(kind IN ('observation','evidence','handoff')),
    PRIMARY KEY(ingestion_id,history_id)
);
CREATE TABLE m2_verifications (
    request_id TEXT PRIMARY KEY, ingestion_id TEXT NOT NULL REFERENCES m2_report_inbox(ingestion_id),
    criterion TEXT NOT NULL, evidence_revision TEXT NOT NULL,
    result TEXT NOT NULL CHECK(result IN ('PASS','FAIL','PARTIAL','UNKNOWN')),
    source_method TEXT NOT NULL, source_ref TEXT NOT NULL,
    verifier_id TEXT NOT NULL, recorded_at TEXT NOT NULL,
    history_id TEXT NOT NULL REFERENCES history(id) DEFERRABLE INITIALLY DEFERRED,
    UNIQUE(ingestion_id,criterion,evidence_revision)
);
CREATE TABLE m2_human_requests (
    request_id TEXT PRIMARY KEY, ingestion_id TEXT NOT NULL REFERENCES m2_report_inbox(ingestion_id),
    requested_by TEXT NOT NULL, subject TEXT NOT NULL, reason TEXT NOT NULL,
    created_at TEXT NOT NULL, UNIQUE(ingestion_id,subject)
);
CREATE TABLE m2_human_decisions (
    decision_id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE REFERENCES m2_human_requests(request_id),
    decided_by TEXT NOT NULL, outcome TEXT NOT NULL CHECK(outcome IN ('APPROVED','REJECTED','MORE_INFO')),
    rationale TEXT NOT NULL, decided_at TEXT NOT NULL,
    history_id TEXT NOT NULL REFERENCES history(id) DEFERRABLE INITIALLY DEFERRED
);
-- TRIGGERS
CREATE TRIGGER m2_briefs_no_update BEFORE UPDATE ON m2_issued_briefs BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_briefs_no_delete BEFORE DELETE ON m2_issued_briefs BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_inbox_no_update BEFORE UPDATE ON m2_report_inbox BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_inbox_no_delete BEFORE DELETE ON m2_report_inbox BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_links_no_update BEFORE UPDATE ON m2_report_links BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_links_no_delete BEFORE DELETE ON m2_report_links BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_verifications_no_update BEFORE UPDATE ON m2_verifications BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_verifications_no_delete BEFORE DELETE ON m2_verifications BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_human_requests_no_update BEFORE UPDATE ON m2_human_requests BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_human_requests_no_delete BEFORE DELETE ON m2_human_requests BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_human_decisions_no_update BEFORE UPDATE ON m2_human_decisions BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER m2_human_decisions_no_delete BEFORE DELETE ON m2_human_decisions BEGIN SELECT RAISE(ABORT,'append-only'); END;
"""),
)


def _connect(path: Path) -> sqlite3.Connection:
    if str(path) == ":memory:":
        raise ValueError("M1 exige un chemin de fichier durable")
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=3.0, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=3000")
    return connection


def migrate(path: str | Path) -> None:
    """Échoue sur checksum inconnu; ne transforme jamais une migration existante."""
    db = _connect(Path(path))
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, checksum TEXT NOT NULL)")
        rows = {int(row[0]): str(row[1]) for row in db.execute("SELECT version, checksum FROM schema_migrations")}
        known = {v: sha256(sql.encode("utf-8")).hexdigest() for v, sql in MIGRATIONS}
        if set(rows) - set(known):
            raise Conflict("Version de schéma inconnue")
        for version, expected in rows.items():
            if expected != known[version]:
                raise Conflict("Migration appliquée modifiée")
        for version, sql in MIGRATIONS:
            if version not in rows:
                # Simple SQL sans chaîne contenant de séparateur ni triggers dans les migrations 0001.
                # Pour les triggers de 0002, exécuter les déclarations séparément sans executescript
                # car executescript déclenche un COMMIT implicite en mode sqlite3.
                if version == 1:
                    statements = [p.strip() for p in sql.split(";") if p.strip()]
                elif version == 3:
                    prefix, trigger_sql = sql.split("-- TRIGGERS", 1)
                    statements = [p.strip() for p in prefix.split(";") if p.strip()]
                    statements.extend(re.findall(r"CREATE TRIGGER .*?END;", trigger_sql, re.DOTALL))
                else:
                    prefix, tail = sql.split("CREATE TRIGGER history_no_update", 1)
                    statements = [p.strip() for p in prefix.split(";") if p.strip()]
                    parts = tail.split("CREATE TRIGGER history_no_delete", 1)
                    statements += ["CREATE TRIGGER history_no_update" + parts[0].strip(),
                                   "CREATE TRIGGER history_no_delete" + parts[1].strip()]
                for statement in statements:
                    db.execute(statement)
                db.execute("INSERT INTO schema_migrations(version,checksum) VALUES(?,?)", (version, known[version]))
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def backup(source: str | Path, destination: str | Path) -> None:
    """Copie cohérente SQLite via API de backup (WAL inclus)."""
    dst_path = Path(destination)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(Path(source)) as conn:
        with _connect(dst_path) as other:
            conn.backup(other)