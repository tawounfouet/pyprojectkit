"""FakePythosAdapter purement déterministe, sans appels réseau ou outils."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from .contracts import OperatingBriefDTO
from .reports import ExecutionReportDTO, ReportEvidenceRefDTO


class FakePythosAdapter:
    def make_report(
        self, brief: OperatingBriefDTO, *,
        produced_at: datetime | None = None,
        report_id: str | None = None,
        idempotency_key: str = "synthetic-report-v1",
        reported_status: str = "QUALIFIED",
        with_evidence: bool = True,
    ) -> ExecutionReportDTO:
        """QUALIFIED signifie une déclaration, et non un contrôle réellement passé."""
        if produced_at is None:
            produced_at = datetime.now(timezone.utc)
        evidence = (
            (ReportEvidenceRefDTO(
                source_type=brief.target_reference.source_type,
                resource_ref=brief.target_reference.resource_ref,
                revision=brief.target_reference.revision,
                claim="Résultat déclaré sans vérification indépendante",
                available=True,
            ),)
            if with_evidence else ()
        )
        return ExecutionReportDTO(
            schema_version="1.0", report_id=report_id or str(uuid4()),
            brief_id=brief.brief_id, mandate_id=brief.mandate_id,
            scope_id=brief.scope_id, project_id=brief.project_id,
            work_item_ref=brief.work_item_ref, mode=brief.mode,
            target_reference=brief.target_reference,
            source_watermark=brief.source_watermark, produced_at=produced_at,
            outcome="SUCCEEDED", reported_status=reported_status,
            idempotency_key=idempotency_key, changes_made=(),
            verification_performed=("test declared by FakePythos",),
            evidence_references=evidence, limitations=("Données synthétiques",),
            residual_risks=("Aucune CI réelle vérifiée",),
            human_decisions_required=("Revue humaine séparée",),
            next_action="Soumettre une demande de revue",
        )
