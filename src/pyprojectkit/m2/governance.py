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

