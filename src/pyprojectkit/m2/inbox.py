"""M2-05/M2-07 : émission durable, inbox et handoff atomiques sur SQLite.

Le journal reçoit une déclaration, et ne modifie aucun Aggregate M0.
Les opérations externes sont hors de la transaction locale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import sqlite3
from typing import Callable
from uuid import UUID, uuid4

from ..domain import AccessDenied, CommitOutcomeUnknown, Conflict, InvalidValue, NotFound, ProjectId, TaskId
from ..m1 import HistoryRecord, RegistryService, SqliteUnitOfWork, VerifiedActor
from ..ports import Clock
from ..service import SystemClock
from .application import BuildAuthorizedOperatingBrief, BuildBriefRequest
from .contracts import OperatingBriefDTO, WorkItemRef
from .mandates import MandateVerifier
from .reports import ExecutionReportDTO

DENIED = "Ressource indisponible"
SENSITIVE_MARKERS = ("bearer ", "password=", "token=", "secret=", "ghp_", "sk-", "akia", "://")


class IdempotencyConflict(Conflict):
    """Deux intentions partagent une clé mais pas les mêmes octets sémantiques."""


@dataclass(frozen=True, slots=True)
class ReportIngestionReceipt:
    ingestion_id: str
    report_id: str
    accepted_at: str
    outcome: str
    is_replay: bool
    linked_record_ids: tuple[str, ...]
    source_fingerprint: str


@dataclass(frozen=True, slots=True)
class ReportView:
    ingestion: ReportIngestionReceipt
    report: ExecutionReportDTO
    classification: str


def _now(clock: Clock) -> datetime:
    current = clock.now()
    if not isinstance(current, datetime) or current.utcoffset() is None:
        raise InvalidValue("Horloge de confiance invalide")
    return current.astimezone(timezone.utc)


def _sensitive(content: str) -> bool:
    return any(x in content.lower() for x in SENSITIVE_MARKERS)


class ReportInboxService:
    """Facade à faible surface; TrustedHost M1 reste la seule autorité d'identité."""

    def __init__(self, registry: RegistryService, mandates: MandateVerifier,
                 clock: Clock | None = None) -> None:
        if registry.authority is not mandates.host:
            raise InvalidValue("Autorités M1 et M2 différentes")
        self.registry = registry
        self.mandates = mandates
        self.clock = clock or SystemClock()
        self.brief_builder = BuildAuthorizedOperatingBrief(registry, mandates, self.clock)

    def _project_in_transaction(self, uow: SqliteUnitOfWork, actor: VerifiedActor,
                                project_id: str, task_id: str) -> None:
        # Reprend la police de scope/owner/classification de M1 sous la même UoW.
        self.registry._project(uow, actor, project_id)  # noqa: SLF001 - port interne du pilote
        self.registry.authority.require(actor, "TASK_VIEW")
        row = uow._db().execute(
            """SELECT t.id,t.project_id FROM tasks t WHERE t.id=? AND t.project_id=?""",
            (task_id, project_id),
        ).fetchone()
        if row is None:
            raise NotFound(DENIED)
        classification = uow._db().execute(
            "SELECT classification FROM context_scopes WHERE id=?", (actor.scope_id,)
        ).fetchone()
        if classification is None or classification["classification"] != "INTERNAL":
            raise AccessDenied(DENIED)

    def issue_brief(self, actor: VerifiedActor, request: BuildBriefRequest) -> OperatingBriefDTO:
        """M2-A Query + reçu d'émission transactionnel, avant remise du brief."""
        self.registry.authority.require(actor, "BRIEF_ISSUE")
        brief = self.brief_builder.execute(actor, request)
        # Une émission non persistée ne vaut jamais mandat pour l'inbox M2-B.
        fingerprint = sha256(brief.to_json().encode("utf-8")).hexdigest()
        with SqliteUnitOfWork(self.registry.db) as uow:
            self._project_in_transaction(uow, actor, brief.project_id, brief.work_item_ref.id)
            row = uow._db().execute(
                "SELECT version FROM tasks WHERE id=? AND project_id=?",
                (brief.work_item_ref.id, brief.project_id)
            ).fetchone()
            assert row is not None
            if f"m1:task:{brief.work_item_ref.id}:v{row['version']}:project:{brief.project_id}" != brief.source_watermark:
                raise Conflict("Contexte de brief devenu obsolète")
            self.mandates.require_authorized(
                actor, mandate_id=brief.mandate_id, project_id=brief.project_id,
                work_item_ref=brief.work_item_ref, mode=brief.mode,
                target_reference=brief.target_reference, now=_now(self.clock),
            )
            now = _now(self.clock)
            if now >= brief.expires_at:
                raise AccessDenied(DENIED)
            uow._db().execute(
                """INSERT INTO m2_issued_briefs
                   (brief_id,scope_id,project_id,task_id,mandate_id,issuer_id,mode,
                    target_type,target_resource,target_revision,source_watermark,
                    schema_version,issued_at,expires_at,brief_fingerprint)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (brief.brief_id, brief.scope_id, brief.project_id, brief.work_item_ref.id,
                 brief.mandate_id, actor.actor_id, brief.mode,
                 brief.target_reference.source_type, brief.target_reference.resource_ref,
                 brief.target_reference.revision, brief.source_watermark, brief.schema_version,
                 now.isoformat(), brief.expires_at.isoformat(), fingerprint),
            )
            uow.commit()
        return brief

    def _receipt_row(self, conn: sqlite3.Connection, report: ExecutionReportDTO,
                     actor: VerifiedActor) -> sqlite3.Row:
        row = conn.execute(
            "SELECT * FROM m2_issued_briefs WHERE brief_id=? AND scope_id=?",
            (report.brief_id, actor.scope_id),
        ).fetchone()
        if row is None:
            raise NotFound(DENIED)
        if (row["mandate_id"] != report.mandate_id or row["project_id"] != report.project_id
                or row["task_id"] != report.work_item_ref.id or row["scope_id"] != report.scope_id
                or row["mode"] != report.mode
                or (row["target_type"], row["target_resource"], row["target_revision"]) != (
                    report.target_reference.source_type, report.target_reference.resource_ref,
                    report.target_reference.revision)
                or row["source_watermark"] != report.source_watermark
                or row["issuer_id"] != actor.actor_id):
            raise AccessDenied(DENIED)
        return row

    def _authorized_receive(self, actor: VerifiedActor, report: ExecutionReportDTO,
                            *, now: datetime) -> None:
        self.registry.authority.require(actor, "REPORT_RECEIVE")
        self.mandates.require_authorized(
            actor, mandate_id=report.mandate_id, project_id=report.project_id,
            work_item_ref=report.work_item_ref, mode=report.mode,
            target_reference=report.target_reference, now=now,
            operation_permission="REPORT_RECEIVE",
        )
        for permission in ("WRITE_OBSERVATION", "WRITE_HANDOFF"):
            self.registry.authority.require(actor, permission)
        if report.evidence_references:
            self.registry.authority.require(actor, "WRITE_EVIDENCE")

    def _receipt(self, conn: sqlite3.Connection, row: sqlite3.Row, *,
                 is_replay: bool) -> ReportIngestionReceipt:
        links = tuple(r["history_id"] for r in conn.execute(
            "SELECT history_id FROM m2_report_links WHERE ingestion_id=? ORDER BY kind,history_id",
            (row["ingestion_id"],),
        ))
        return ReportIngestionReceipt(
            row["ingestion_id"], row["report_id"], row["received_at"],
            "ALREADY_ACCEPTED" if is_replay else "ACCEPTED_AS_DECLARATION",
            is_replay, links, row["fingerprint"],
        )

    def _existing(self, conn: sqlite3.Connection, report: ExecutionReportDTO,
                  fingerprint: str) -> ReportIngestionReceipt | None:
        # Deux contraintes uniques indépendantes pour le même namespace de mandat.
        hits = list(conn.execute(
            """SELECT * FROM m2_report_inbox WHERE scope_id=? AND mandate_id=?
               AND (report_id=? OR idempotency_key=?)""",
            (report.scope_id, report.mandate_id, report.report_id, report.idempotency_key),
        ))
        if not hits:
            return None
        if (len(hits) != 1 or hits[0]["report_id"] != report.report_id
                or hits[0]["idempotency_key"] != report.idempotency_key
                or hits[0]["fingerprint"] != fingerprint):
            raise IdempotencyConflict("Conflit d'idempotence")
        return self._receipt(conn, hits[0], is_replay=True)

    def receive(self, actor: VerifiedActor, report: ExecutionReportDTO,
                *, fault: Callable[[str], None] | None = None) -> ReportIngestionReceipt:
        """Transaction unique report + M1 history + links. Injection de faute pour tests."""
        if not isinstance(report, ExecutionReportDTO):
            raise InvalidValue("Report requis")
        now = _now(self.clock)
        self._authorized_receive(actor, report, now=now)
        payload = report.to_json()
        if _sensitive(payload):
            raise InvalidValue("Report potentiellement sensible interdit au pilote local")
        if report.mode == "AUDIT" and report.changes_made:
            raise InvalidValue("AUDIT read-only: modification déclarée hors mandat")
        if report.produced_at > now + timedelta(minutes=5) or report.produced_at < now - timedelta(hours=24):
            raise InvalidValue("Horodatage producteur hors fenêtre")
        fingerprint = report.fingerprint()
        with SqliteUnitOfWork(self.registry.db) as uow:
            conn = uow._db()
            issued = self._receipt_row(conn, report, actor)
            if now >= datetime.fromisoformat(issued["expires_at"]):
                raise AccessDenied(DENIED)
            if report.produced_at < datetime.fromisoformat(issued["issued_at"]) - timedelta(minutes=5):
                raise InvalidValue("Rapport antérieur au brief émis")
            self._project_in_transaction(uow, actor, report.project_id, report.work_item_ref.id)
            self._authorized_receive(actor, report, now=_now(self.clock))
            existing = self._existing(conn, report, fingerprint)
            if existing is not None:
                return existing
            ingestion_id = str(uuid4())
            accepted_at = _now(self.clock).isoformat()
            if datetime.fromisoformat(accepted_at) >= datetime.fromisoformat(issued["expires_at"]):
                raise AccessDenied(DENIED)
            conn.execute(
                """INSERT INTO m2_report_inbox
                   (ingestion_id,scope_id,project_id,task_id,mandate_id,brief_id,
                    report_id,idempotency_key,fingerprint,payload_json,received_at,received_by,status)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (ingestion_id, actor.scope_id, report.project_id, report.work_item_ref.id,
                 report.mandate_id, report.brief_id, report.report_id, report.idempotency_key,
                 fingerprint, payload, accepted_at, actor.actor_id, "ACCEPTED_AS_DECLARATION"),
            )
            if fault:
                fault("after_inbox")
            records: list[HistoryRecord] = []
            def add(kind: str, body: dict[str, object]) -> None:
                rid = str(uuid4())
                records.append(HistoryRecord(
                    rid, kind, report.project_id, actor.scope_id, "INTERNAL",
                    accepted_at, body, 0,
                ))
                uow.records.append(records[-1])
                conn.execute(
                    "INSERT INTO m2_report_links(ingestion_id,history_id,kind) VALUES(?,?,?)",
                    (ingestion_id, rid, kind),
                )
            add("observation", {
                "subject": "ExecutionReport", "value": f"DECLARED:{report.outcome}:{report.reported_status}",
                "source_ref": f"m2-report:{report.report_id}", "observed_at": accepted_at,
                "available": True, "brief_id": report.brief_id,
            })
            for item in report.evidence_references:
                add("evidence", {
                    "target_ref": item.resource_ref, "revision": item.revision,
                    "source_ref": f"m2-report:{report.report_id}",
                    "available": False, "claim": item.claim,
                })
            add("handoff", {
                "summary": f"Report déclaré : {report.outcome}",
                "outcome": "DECLARED", "risks": list(report.residual_risks),
                "unknowns": list(report.limitations), "producer": "pythos:untrusted",
                "next_action": report.next_action, "report_id": report.report_id,
            })
            if fault:
                fault("after_links_before_commit")
            self._authorized_receive(actor, report, now=_now(self.clock))
            uow.commit()
            # Une erreur de commit à issue incertaine est propagée (pas de faux ACK).
            row = conn.execute(
                "SELECT * FROM m2_report_inbox WHERE ingestion_id=?", (ingestion_id,)
            ).fetchone()
            assert row is not None
            return self._receipt(conn, row, is_replay=False)

    def reconcile(self, actor: VerifiedActor, report: ExecutionReportDTO) -> ReportIngestionReceipt | None:
        """Après CommitOutcomeUnknown : lecture autorisée avant un nouveau write."""
        self._authorized_receive(actor, report, now=_now(self.clock))
        with SqliteUnitOfWork(self.registry.db) as uow:
            self._project_in_transaction(uow, actor, report.project_id, report.work_item_ref.id)
            self._receipt_row(uow._db(), report, actor)
            self._authorized_receive(actor, report, now=_now(self.clock))
            return self._existing(uow._db(), report, report.fingerprint())

    def get_report(self, actor: VerifiedActor, ingestion_id: str) -> ReportView:
        self.registry.authority.require(actor, "REPORT_READ")
        with SqliteUnitOfWork(self.registry.db) as uow:
            row = uow._db().execute(
                "SELECT * FROM m2_report_inbox WHERE ingestion_id=? AND scope_id=?",
                (ingestion_id, actor.scope_id)
            ).fetchone()
            if row is None:
                raise NotFound(DENIED)
            self._project_in_transaction(uow, actor, row["project_id"], row["task_id"])
            self.registry.authority.require(actor, "READ_OBSERVATION")
            return ReportView(
                self._receipt(uow._db(), row, is_replay=False),
                ExecutionReportDTO.from_json(row["payload_json"]),
                "DECLARED",
            )

    def list_reports(self, actor: VerifiedActor, project_id: str, task_id: str) -> tuple[ReportIngestionReceipt, ...]:
        self.registry.authority.require(actor, "REPORT_READ")
        with SqliteUnitOfWork(self.registry.db) as uow:
            self._project_in_transaction(uow, actor, project_id, task_id)
            rows = uow._db().execute(
                """SELECT * FROM m2_report_inbox WHERE scope_id=? AND project_id=? AND task_id=?
                   ORDER BY received_at,ingestion_id""",
                (actor.scope_id, project_id, task_id),
            )
            self.registry.authority.require(actor, "READ_OBSERVATION")
            return tuple(self._receipt(uow._db(), row, is_replay=False) for row in rows)
