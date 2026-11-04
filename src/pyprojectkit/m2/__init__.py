"""M2 optionnel : briefs, mandats, rapports et gouvernance locale."""
from .application import BuildAuthorizedOperatingBrief, BuildBriefRequest
from .contracts import ExactTargetReference, OperatingBriefDTO, UnsupportedContractVersion, WorkItemRef
from .mandates import DelegationMandate, InMemoryMandateStore, MandateStorePort, MandateVerifier
from .reports import ExecutionReportDTO, ReportEvidenceRefDTO
from .inbox import (
    IdempotencyConflict, ReportInboxService, ReportIngestionReceipt, ReportView,
)
from .governance import (
    FakeIndependentEvidenceVerifier, HumanDecision, HumanDecisionRequest,
    IndependentEvidenceVerifier, ReportGovernanceService, VerificationResult,
)
from .fake import FakePythosAdapter
from .resume_view import ResumeWorkItemQuery, ResumeWorkItemView
from .qualification import AcceptanceEvidence, QualificationDossier, build_qualification_dossier

__all__ = [
    "BuildAuthorizedOperatingBrief", "BuildBriefRequest", "DelegationMandate",
    "ExactTargetReference", "InMemoryMandateStore", "MandateStorePort",
    "MandateVerifier", "OperatingBriefDTO", "UnsupportedContractVersion", "WorkItemRef",
    "ExecutionReportDTO", "ReportEvidenceRefDTO", "IdempotencyConflict",
    "ReportInboxService", "ReportIngestionReceipt", "ReportView",
    "FakeIndependentEvidenceVerifier", "HumanDecision", "HumanDecisionRequest",
    "IndependentEvidenceVerifier", "ReportGovernanceService", "VerificationResult",
    "FakePythosAdapter", "ResumeWorkItemQuery", "ResumeWorkItemView",
    "AcceptanceEvidence", "QualificationDossier", "build_qualification_dossier",
]
