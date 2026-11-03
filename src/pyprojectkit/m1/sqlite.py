"""Adaptateur SQLite M1 respectant les ports M0 et l'atomicité transactionnelle."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
import json
import sqlite3
from typing import Callable, Generic, TypeVar
from uuid import UUID

from ..domain import (
    CommitOutcomeUnknown, Conflict, Dependency, DomainEvent, Milestone, MilestoneId,
    NotFound, Project, ProjectId, ProjectStatus, Task, TaskId, TaskStatus, assert_acyclic,
)
from .schema import _connect, backup, migrate

T = TypeVar("T", Project, Task)
I = TypeVar("I", ProjectId, TaskId)


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _text(value: datetime | date | None) -> str | None:
    return value.isoformat() if value is not None else None


def _project(row: sqlite3.Row, conn: sqlite3.Connection) -> Project:
    pid = ProjectId(UUID(row["id"]))
    milestones = {}
    for item in conn.execute("SELECT * FROM project_milestones WHERE project_id=? ORDER BY id", (row["id"],)):
        mid = MilestoneId(UUID(item["id"]))
        milestones[mid] = Milestone(mid, item["name"], date.fromisoformat(item["target_date"]), _dt(item["reached_at"]))
    return Project(pid, row["name"], row["owner_id"], row["scope"], ProjectStatus(row["status"]),
                   int(row["version"]), _dt(row["actual_start_at"]), _dt(row["actual_end_at"]), milestones)


def _task(row: sqlite3.Row, _conn: sqlite3.Connection) -> Task:
    return Task(TaskId(UUID(row["id"])), ProjectId(UUID(row["project_id"])), row["title"],
                TaskStatus(row["status"]), int(row["version"]), row["assignee_id"],
                row["block_reason"], _dt(row["actual_start_at"]), _dt(row["actual_end_at"]),
                int(row["progress"]))


class SqliteDatabase:
    """Base locale non chiffrée. Données synthétiques seulement sans politique adaptée."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        migrate(self.path)
        self.events: list[DomainEvent] = []  # notifications du processus seulement

    def connection(self) -> sqlite3.Connection:
        return _connect(self.path)

    def backup(self, destination: str | Path) -> None:
        backup(self.path, destination)


class SqliteRepository(Generic[I, T]):
    """État et versions isolés durant l'UoW, écriture effective uniquement au commit."""

    def __init__(self, conn: sqlite3.Connection, table: str, parser: Callable[[sqlite3.Row, sqlite3.Connection], T],
                 identity: Callable[[T], I]):
        if table not in ("projects", "tasks"):
            raise ValueError("Repository inconnu")
        self.conn, self.table = conn, table
        self.parser: Callable[[sqlite3.Row, sqlite3.Connection], T] = parser
        self.identity: Callable[[T], I] = identity
        self.staged: dict[I, tuple[T, int | None]] = {}

    def get(self, identifier: I) -> T | None:
        if identifier in self.staged:
            return deepcopy(self.staged[identifier][0])
        row = self.conn.execute(f"SELECT * FROM {self.table} WHERE id=?", (str(identifier.value),)).fetchone()
        return self.parser(row, self.conn) if row is not None else None

    def list_all(self) -> list[T]:
        result: list[T] = []
        seen: set[I] = set()
        for row in self.conn.execute(f"SELECT * FROM {self.table} ORDER BY id"):
            obj = self.parser(row, self.conn)
            identifier = self.identity(obj)
            seen.add(identifier)
            staged = self.staged.get(identifier)
            result.append(deepcopy(staged[0]) if staged else obj)
        for identifier, (item, _baseline) in self.staged.items():
            if identifier not in seen:
                result.append(deepcopy(item))
        return result

    def add(self, obj: T) -> None:
        identifier = self.identity(obj)
        if self.get(identifier) is not None:
            raise Conflict("Identité déjà utilisée")
        self.staged[identifier] = (deepcopy(obj), None)

    def save(self, obj: T, *, expected_version: int) -> None:
        identifier = self.identity(obj)
        current = self.get(identifier)
        if current is None or current.version != expected_version:
            raise Conflict("Version obsolète ou entité absente")
        previous = self.staged.get(identifier)
        baseline = previous[1] if previous is not None else expected_version
        self.staged[identifier] = (deepcopy(obj), baseline)

class SqliteGraph:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.staged: dict[ProjectId, tuple[int, int, set[Dependency]]] = {}

    def snapshot(self, project_id: ProjectId) -> tuple[int, set[Dependency]]:
        if project_id in self.staged:
            _old, version, edges = self.staged[project_id]
            return version, deepcopy(edges)
        row = self.conn.execute("SELECT version FROM dependency_graph_versions WHERE project_id=?", (str(project_id.value),)).fetchone()
        edges = {Dependency(TaskId(UUID(r[0])), TaskId(UUID(r[1]))) for r in self.conn.execute(
            "SELECT successor_id,predecessor_id FROM task_dependencies WHERE project_id=?",
            (str(project_id.value),))}
        return (int(row[0]) if row else 0), edges

    def replace_if_version(self, project_id: ProjectId, *, expected_version: int, edges: set[Dependency]) -> None:
        current_version, _ = self.snapshot(project_id)
        if current_version != expected_version:
            raise Conflict("Version de graphe obsolète")
        assert_acyclic(edges)
        old = self.staged[project_id][0] if project_id in self.staged else expected_version
        self.staged[project_id] = (old, expected_version + 1, deepcopy(edges))


@dataclass(frozen=True, slots=True)
class HistoryRecord:
    id: str
    kind: str
    project_id: str
    scope_id: str
    classification: str
    recorded_at: str
    payload: dict[str, object]
    seq: int


class SqliteRecords:
    """Port M1 append-only avec scope explicite; appelé à travers l'UoW."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.pending: list[HistoryRecord] = []

    def append(self, record: HistoryRecord) -> None:
        if record.kind not in {"claim", "observation", "evidence", "assessment", "reconciliation",
                               "resolution", "decision", "approval", "blocker", "snapshot", "handoff"}:
            raise ValueError("Type de record non reconnu")
        if record.classification not in ("PRIVATE", "INTERNAL"):
            raise ValueError("Classification invalide")
        if any(x.id == record.id for x in self.pending):
            raise Conflict("Record déjà inscrit")
        self.pending.append(deepcopy(record))

    def list_records(self, project_id: str, scope: str, kind: str | None = None) -> list[HistoryRecord]:
        query = "SELECT * FROM history WHERE project_id=? AND scope_id=?"
        params: list[str] = [project_id, scope]
        if kind is not None:
            query += " AND kind=?"
            params.append(kind)
        rows = self.conn.execute(query + " ORDER BY seq", params)
        stored = [HistoryRecord(row["id"], row["kind"], row["project_id"], row["scope_id"], row["classification"],
                                row["recorded_at"], json.loads(row["payload"]), int(row["seq"])) for row in rows]
        pending = [r for r in self.pending if r.project_id == project_id and r.scope_id == scope and (kind is None or r.kind == kind)]
        return stored + pending

    def external(self, project_id: str, scope: str) -> list[dict[str, str | None]]:
        return [dict(r) for r in self.conn.execute(
            "SELECT id,provider,external_id,relation_type,uri,recorded_at FROM external_references WHERE project_id=? AND scope_id=? ORDER BY provider,external_id",
            (project_id, scope))]


class SqliteUnitOfWork:
    """Transaction locale serialisée: BEGIN IMMEDIATE + CAS + post-commit events."""

    def __init__(self, database: SqliteDatabase):
        self.db = database
        self.conn: sqlite3.Connection | None = None
        self.projects: SqliteRepository[ProjectId, Project]
        self.tasks: SqliteRepository[TaskId, Task]
        self.dependencies: SqliteGraph
        self.records: SqliteRecords
        self._events: list[DomainEvent] = []
        self._committed = False
        self._active = False
        self._registry: list[tuple[str, str, str, int, str | None, str]] = []
        self._refs: list[tuple[str, str, str, str, str, str, str | None, str]] = []
        self._scopes: list[tuple[str, str, str, str, str]] = []

    def __enter__(self) -> "SqliteUnitOfWork":
        if self._active:
            raise RuntimeError("UnitOfWork déjà ouverte")
        self.conn = self.db.connection()
        try:
            self.conn.execute("BEGIN IMMEDIATE")
        except BaseException:
            self.conn.close()
            self.conn = None
            raise
        self.projects = SqliteRepository[ProjectId, Project](self.conn, "projects", _project, lambda p: p.id)
        self.tasks = SqliteRepository[TaskId, Task](self.conn, "tasks", _task, lambda t: t.id)
        self.dependencies = SqliteGraph(self.conn)
        self.records = SqliteRecords(self.conn)
        self._events = []
        self._active = True
        return self

    def _db(self) -> sqlite3.Connection:
        if not self._active or self.conn is None:
            raise RuntimeError("UnitOfWork inactive")
        return self.conn

    def record(self, event: DomainEvent) -> None:
        self._db()
        self._events.append(event)

    def add_scope(self, identifier: str, owner_id: str, classification: str, policy_ref: str, at: str) -> None:
        self._db()
        self._scopes.append((identifier, owner_id, classification, policy_ref, at))

    def add_registry(self, project_id: str, scope: str, family: str, priority: int, due_date: str | None, at: str) -> None:
        self._db()
        self._registry.append((project_id, scope, family, priority, due_date, at))

    def add_external(self, identifier: str, project_id: str, scope: str, provider: str,
                     external_id: str, relation_type: str, uri: str | None, at: str) -> None:
        self._db()
        self._refs.append((identifier, project_id, scope, provider, external_id, relation_type, uri, at))

    def _write(self) -> None:
        conn = self._db()
        for item in self._scopes:
            conn.execute("INSERT INTO context_scopes VALUES(?,?,?,?,?)", item)
        for pid_value, (project, baseline) in self.projects.staged.items():
            project_values = (project.name, project.owner_id, project.scope, project.status.value,
                              _text(project.actual_start_at), _text(project.actual_end_at), str(pid_value.value))
            if baseline is None:
                conn.execute("INSERT INTO projects(id,name,owner_id,scope,status,version,actual_start_at,actual_end_at) VALUES(?,?,?,?,?,?,?,?)",
                             (str(pid_value.value), *project_values[:4], 1, project_values[4], project_values[5]))
            else:
                result = conn.execute("UPDATE projects SET name=?,owner_id=?,scope=?,status=?,actual_start_at=?,actual_end_at=?,version=version+1 WHERE id=? AND version=?",
                                      (*project_values, baseline))
                if result.rowcount != 1:
                    raise Conflict("Version Project obsolète")
                conn.execute("DELETE FROM project_milestones WHERE project_id=?", (str(pid_value.value),))
            for mid, milestone in project.milestones.items():
                conn.execute("INSERT INTO project_milestones(id,project_id,name,target_date,reached_at) VALUES(?,?,?,?,?)",
                             (str(mid.value), str(project.id.value), milestone.name, milestone.target_date.isoformat(), _text(milestone.reached_at)))
        for tid_value, (task, baseline) in self.tasks.staged.items():
            task_values = (str(task.project_id.value), task.title, task.status.value, task.assignee_id,
                           task.block_reason, _text(task.actual_start_at), _text(task.actual_end_at), task.progress)
            if baseline is None:
                conn.execute("INSERT INTO tasks(id,project_id,title,status,version,assignee_id,block_reason,actual_start_at,actual_end_at,progress) VALUES(?,?,?,?,?,?,?,?,?,?)",
                             (str(tid_value.value), *task_values[:3], 1, *task_values[3:]))
            else:
                result = conn.execute("UPDATE tasks SET project_id=?,title=?,status=?,assignee_id=?,block_reason=?,actual_start_at=?,actual_end_at=?,progress=?,version=version+1 WHERE id=? AND version=?",
                                      (*task_values, str(tid_value.value), baseline))
                if result.rowcount != 1:
                    raise Conflict("Version Task obsolète")
        for project_id, (old, newer, edges) in self.dependencies.staged.items():
            current = conn.execute("SELECT version FROM dependency_graph_versions WHERE project_id=?", (str(project_id.value),)).fetchone()
            if (int(current[0]) if current else 0) != old:
                raise Conflict("Version graphe obsolète")
            if current:
                conn.execute("UPDATE dependency_graph_versions SET version=? WHERE project_id=? AND version=?",
                             (newer, str(project_id.value), old))
            else:
                conn.execute("INSERT INTO dependency_graph_versions VALUES(?,?)", (str(project_id.value), newer))
            conn.execute("DELETE FROM task_dependencies WHERE project_id=?", (str(project_id.value),))
            for edge in edges:
                conn.execute("INSERT INTO task_dependencies VALUES(?,?,?)",
                             (str(project_id.value), str(edge.successor.value), str(edge.predecessor.value)))
        for registry_record in self._registry:
            conn.execute("INSERT INTO project_registry VALUES(?,?,?,?,?,?)", registry_record)
        for external_record in self._refs:
            conn.execute("INSERT INTO external_references VALUES(?,?,?,?,?,?,?,?)", external_record)
        for history_record in self.records.pending:
            conn.execute("INSERT INTO history(id,kind,project_id,scope_id,classification,recorded_at,payload) VALUES(?,?,?,?,?,?,?)",
                         (history_record.id, history_record.kind, history_record.project_id, history_record.scope_id,
                          history_record.classification, history_record.recorded_at,
                          json.dumps(history_record.payload, sort_keys=True, ensure_ascii=True, allow_nan=False)))
        for event in self._events:
            conn.execute("INSERT INTO event_history(project_or_aggregate_id,event_name,occurred_at,actor_id) VALUES(?,?,?,?)",
                         (event.aggregate_id, event.name, event.occurred_at.isoformat(), event.actor_id))

    def commit(self) -> None:
        conn = self._db()
        if self._committed:
            raise RuntimeError("Commit déjà effectué")
        try:
            self._write()
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise Conflict("Contrainte de stockage violée") from exc
        except BaseException:
            conn.rollback()
            raise
        try:
            conn.commit()
        except sqlite3.Error as exc:
            raise CommitOutcomeUnknown("Résultat du commit à réconcilier") from exc
        self._committed = True
        self.db.events.extend(deepcopy(self._events))

    def rollback(self) -> None:
        if self.conn is not None and self.conn.in_transaction:
            self.conn.rollback()
        self._events.clear()

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: object) -> None:
        try:
            if not self._committed:
                self.rollback()
        finally:
            if self.conn is not None:
                self.conn.close()
                self.conn = None
            self._active = False