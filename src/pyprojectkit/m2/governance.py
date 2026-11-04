"""Vérification de provenance et décisions humaines M2-B."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

from ..domain import AccessDenied, Conflict, InvalidValue, NotFound
from ..m1 import HistoryRecord, SqliteUnitOfWork, VerifiedActor
from ..ports import Clock
from ..service import SystemClock
from .inbox import ReportInboxService, _now
from .reports import ReportEvidenceRefDTO


@dataclass(frozen=True, slots=True)
class VerificationResult:
    result: str
    method: str
    source_ref: str

    def __post_init__(self) -> None:
        if self.result not in ("PASS", "FAIL", "PARTIAL", "UNKNOWN"):
            raise InvalidValue("Verdict invalide")
        if (not self.method or not self.source_ref or
                len(self.method) > 256 or len(self.source_ref) > 256):
            raise InvalidValue("Provenance de vérification invalide")


class IndependentEvidenceVerifier(Protocol):
    def verify(self, *, source_reference: ReportEvidenceRefDTO,
               criterion: str, target_revision: str) -> VerificationResult: ...


class FakeIndependentEvidenceVerifier:
    """Source de tests indépendante du contenu du rapport."""
    def __init__(self, results: dict[tuple[str, str, str], VerificationResult] | None = None):
        self.results = dict(results or {})

    def verify(self, *, source_reference: ReportEvidenceRefDTO,
               criterion: str, target_revision: str) -> VerificationResult:
        return self.results.get(
            (source_reference.resource_ref, target_revision, criterion),
            VerificationResult("UNKNOWN", "synthetic-unavailable", source_reference.resource_ref),
        )


@dataclass(frozen=True, slots=True)
class HumanDecisionRequest:
    request_id: str
    ingestion_id: str
    subject: str
    requested_by: str
    status: str


@dataclass(frozen=True, slots=True)
class HumanDecision:
    decision_id: str
    request_id: str
    decided_by: str
    outcome: str
    rationale: str


class ReportGovernanceService:
    """Commandes de gouvernance sans effet sur Project ou Task."""
    def __init__(self, inbox: ReportInboxService, clock: Clock | None = None):
        self.inbox = inbox
        self.registry = inbox.registry
        self.clock = clock or SystemClock()

    def _report(self, actor: VerifiedActor, ingestion_id: str):
        return self.inbox.get_report(actor, ingestion_id)


    def request_verification(self, actor: VerifiedActor, ingestion_id: str,
                             evidence_index: int, criterion: str,
                             verifier: IndependentEvidenceVerifier) -> str:
        self.registry.authority.require(actor, "VERIFY_REQUEST")
        self.registry.authority.require(actor, "ASSESS")
        self.registry.authority.require(actor, "WRITE_ASSESSMENT")
        self.registry.authority.require(actor, "READ_EVIDENCE")
        if not isinstance(criterion, str) or not criterion.strip() or len(criterion) > 256:
            raise InvalidValue("Critère invalide")
        report = self._report(actor, ingestion_id).report
        if type(evidence_index) is not int or not 0 <= evidence_index < len(report.evidence_references):
            raise InvalidValue("Index invalide")
        evidence = report.evidence_references[evidence_index]
        if evidence.revision != report.target_reference.revision:
            raise Conflict("Preuve sur une autre révision")
        try:
            result = verifier.verify(source_reference=evidence, criterion=criterion,
                                     target_revision=report.target_reference.revision)
        except (TimeoutError, ConnectionError, OSError):
            result = VerificationResult("UNKNOWN", "source-unavailable", evidence.resource_ref)
        if not isinstance(result, VerificationResult):
            raise InvalidValue("Vérificateur invalide")
        if evidence.available is not True and result.result == "PASS":
            result = VerificationResult("UNKNOWN", "source-not-available", evidence.resource_ref)
        with SqliteUnitOfWork(self.registry.db) as uow:
            self.inbox._project_in_transaction(uow, actor, report.project_id, report.work_item_ref.id)
            row = uow._db().execute(
                "SELECT ingestion_id FROM m2_report_inbox WHERE ingestion_id=? AND scope_id=?",
                (ingestion_id, actor.scope_id)
            ).fetchone()
            if row is None:
                raise NotFound("Ressource indisponible")
            request_id, history_id, at = str(uuid4()), str(uuid4()), _now(self.clock).isoformat()
            self.registry.authority.require(actor, "ASSESS")
            self.registry.authority.require(actor, "WRITE_ASSESSMENT")
            uow.records.append(HistoryRecord(
                history_id, "assessment", report.project_id, actor.scope_id, "INTERNAL", at,
                {"target_ref": evidence.resource_ref, "revision": evidence.revision,
                 "criterion": criterion, "result": result.result, "method": result.method,
                 "evaluator": actor.actor_id, "source_ref": result.source_ref,
                 "report_id": report.report_id}, 0
            ))
            uow._db().execute(
                """INSERT INTO m2_verifications
                   (request_id,ingestion_id,criterion,evidence_revision,result,source_method,
                    source_ref,verifier_id,recorded_at,history_id)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (request_id, ingestion_id, criterion, evidence.revision,
                 result.result, result.method, result.source_ref, actor.actor_id, at, history_id)
            )
            uow.commit()
            return request_id

