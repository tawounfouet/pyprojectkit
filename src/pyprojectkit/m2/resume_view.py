"""M2-C - Reconstitution d'un WorkItem depuis les seules preuves persistées.

CQRS Query : lecture filtrée M1/M2, sans provisionnement de mandat ni écriture métier.
Les rapports sont des déclarations, non des preuves approuvées.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..domain import InvalidValue, NotFound
from ..m1 import RegistryService, SqliteUnitOfWork, VerifiedActor
from .contracts import WorkItemRef
from .inbox import ReportInboxService


@dataclass(frozen=True, slots=True)
class ResumeWorkItemView:
    project_id: str
    work_item_ref: WorkItemRef
    scope_id: str
    project_family: str
    project_status: str
    task_status: str
    task_version: str
    snapshot_ref: str | None
    snapshot_recorded_at: str | None
    latest_handoff_ref: str | None
    latest_report_ids: tuple[str, ...]
    issued_brief_ids: tuple[str, ...]
    verification_status: str
    human_review_status: str
    missing_sections: tuple[str, ...]
    stale_sections: tuple[str, ...]
    next_safe_action: str
    source_references: tuple[str, ...]


class ResumeWorkItemQuery:
    """Reader dédié de M2, par scope et projet; aucun accès SQL direct du client."""

    def __init__(self, inbox: ReportInboxService) -> None:
        self.inbox = inbox
        self.registry: RegistryService = inbox.registry

    def execute(self, actor: VerifiedActor, project_id: str,
                work_item_ref: WorkItemRef) -> ResumeWorkItemView:
        if not isinstance(work_item_ref, WorkItemRef) or work_item_ref.kind != "TASK":
            raise InvalidValue("WorkItemRef TASK requis")

        # Résumé M1 et lecture de tâche : M1 contrôle le scope et le propriétaire.
        context = self.registry.resume(actor, project_id)
        tasks = self.registry.list_tasks(actor, project_id)
        task = next((item for item in tasks if item["id"] == work_item_ref.id), None)
        if task is None:
            raise NotFound("Ressource indisponible")

        # La lecture inbox a sa propre permission REPORT_READ et son filtre M1.
        report_receipts = self.inbox.list_reports(actor, project_id, work_item_ref.id)
        report_ids = tuple(item.report_id for item in report_receipts)
        ingestion_ids = tuple(item.ingestion_id for item in report_receipts)

        # Seules des métadonnées bornées sont lues, après le contrôle de l'owner
        # et des permissions, dans la même UoW. Pas de raw payload ni de brief JSON.
        self.registry.authority.require(actor, "REPORT_READ")
        with SqliteUnitOfWork(self.registry.db) as uow:
            self.inbox._project_in_transaction(uow, actor, project_id, work_item_ref.id)
            conn = uow._db()
            briefs = tuple(str(row[0]) for row in conn.execute(
                """SELECT brief_id FROM m2_issued_briefs
                   WHERE scope_id=? AND project_id=? AND task_id=?
                   ORDER BY issued_at,brief_id""",
                (actor.scope_id, project_id, work_item_ref.id),
            ))
            verification_rows = tuple(conn.execute(
                """SELECT v.result FROM m2_verifications v
                   JOIN m2_report_inbox r ON v.ingestion_id=r.ingestion_id
                   WHERE r.scope_id=? AND r.project_id=? AND r.task_id=?
                   ORDER BY v.recorded_at,v.request_id""",
                (actor.scope_id, project_id, work_item_ref.id),
            ))
            review_rows = tuple(conn.execute(
                """SELECT q.request_id,d.outcome FROM m2_human_requests q
                   JOIN m2_report_inbox r ON q.ingestion_id=r.ingestion_id
                   LEFT JOIN m2_human_decisions d ON d.request_id=q.request_id
                   WHERE r.scope_id=? AND r.project_id=? AND r.task_id=?
                   ORDER BY q.created_at,q.request_id""",
                (actor.scope_id, project_id, work_item_ref.id),
            ))

        missing: list[str] = []
        stale: list[str] = []

        # Une observation project-level M1 ne doit pas être présentée comme
        # preuve task-level. La provenance est conservée, sans auto-qualification.
        snapshot = context.latest_snapshot
        handoff = context.latest_handoff
        snapshot_ref: str | None = None
        snapshot_at: str | None = None
        if snapshot is None:
            missing.append("snapshot")
        else:
            snapshot_ref = str(snapshot["id"])
            snapshot_at = str(snapshot["recorded_at"])
            versions = snapshot.get("task_versions")
            if not isinstance(versions, dict) or versions.get(work_item_ref.id) != task["version"]:
                stale.append("snapshot_task_version")
        if handoff is None:
            missing.append("handoff")
        if not report_ids:
            missing.append("reports")
        if not briefs:
            missing.append("issued_briefs")
        if not verification_rows:
            missing.append("independent_verification")
        if not review_rows:
            missing.append("human_review")

        verification = "DECLARED" if report_ids else "UNAVAILABLE"
        if verification_rows:
            # Une vérification M2 ne devient jamais un PASS externe/M1.
            observed = {str(row["result"]) for row in verification_rows}
            verification = ("UNKNOWN" if observed == {"UNKNOWN"}
                            else "SYNTHETIC_CHECK_RECORDED")
        review = "UNAVAILABLE"
        if review_rows:
            review = "PENDING" if any(row["outcome"] is None for row in review_rows) else "DECIDED"

        proposed = context.next_action
        if proposed.task_id == work_item_ref.id and proposed.description:
            action = "PROPOSED_M1: " + proposed.description
        else:
            action = "NONE_WITH_REASON: vérifier le travail courant et obtenir une décision humaine"
        if context.project.family == "TEACHING":
            action = "PROPOSED_EDUCATION: vérifier les critères pédagogiques et demander une revue humaine"

        sources: list[str] = ["m1:project:" + project_id, "m1:task:" + work_item_ref.id]
        if snapshot_ref:
            sources.append("m1:snapshot:" + snapshot_ref)
        if handoff:
            sources.append("m1:handoff:" + str(handoff["id"]))
        sources.extend("m2:issued-brief:" + brief_id for brief_id in briefs)
        sources.extend("m2:ingestion:" + ingestion for ingestion in ingestion_ids)

        return ResumeWorkItemView(
            project_id=project_id,
            work_item_ref=work_item_ref,
            scope_id=actor.scope_id,
            project_family=context.project.family,
            project_status=context.project.project_status,
            task_status=task["status"],
            task_version=task["version"],
            snapshot_ref=snapshot_ref,
            snapshot_recorded_at=snapshot_at,
            latest_handoff_ref=str(handoff["id"]) if handoff else None,
            latest_report_ids=report_ids,
            issued_brief_ids=briefs,
            verification_status=verification,
            human_review_status=review,
            missing_sections=tuple(sorted(set(missing))),
            stale_sections=tuple(sorted(set(stale))),
            next_safe_action=action,
            source_references=tuple(sources),
        )
