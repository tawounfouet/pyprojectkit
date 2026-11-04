"""Query M2-A: projection M1 minimale, mandat vérifié, zéro mutation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from ..domain import AccessDenied, Conflict, InvalidValue, NotFound
from ..m1 import RegistryService, VerifiedActor
from ..ports import Clock
from ..service import SystemClock
from .contracts import ExactTargetReference, OperatingBriefDTO, PythosMode, WorkItemRef, SCHEMA_VERSION
from .mandates import MandateVerifier


@dataclass(frozen=True, slots=True)
class BuildBriefRequest:
    """Aucun actor_id, authority_level, permission ou delegate_id n'est accepté ici."""
    mandate_id: str
    project_id: str
    work_item_ref: WorkItemRef
    mode: PythosMode
    target_reference: ExactTargetReference

    def __post_init__(self) -> None:
        if not self.mandate_id or not isinstance(self.work_item_ref, WorkItemRef):
            raise InvalidValue("Demande de brief invalide")
        if not isinstance(self.target_reference, ExactTargetReference):
            raise InvalidValue("Référence de la demande invalide")
        try:
            if str(UUID(self.project_id)) != self.project_id or (
                str(UUID(self.work_item_ref.id)) != self.work_item_ref.id
            ):
                raise ValueError("UUID non canonique")
        except (TypeError, ValueError, AttributeError) as exc:
            raise InvalidValue("Identifiant de travail invalide") from exc


class BuildAuthorizedOperatingBrief:
    """Read-only CQRS; pas d'exécution d'agent, ni de SQL direct, ni de mutations."""
    def __init__(self, registry: RegistryService, verifier: MandateVerifier,
                 clock: Clock | None = None) -> None:
        # La source d'identité qui autorise le brief DOIT être celle des lecteurs M1.
        if registry.authority is not verifier.host:
            raise InvalidValue("Autorités M1/M2 incohérentes")
        self.registry = registry
        self.verifier = verifier
        self.clock = clock or SystemClock()

    def execute(self, actor: VerifiedActor, request: BuildBriefRequest) -> OperatingBriefDTO:
        if not isinstance(request, BuildBriefRequest):
            raise InvalidValue("Demande de brief invalide")
        start = self.clock.now()
        if not isinstance(start, datetime) or start.utcoffset() is None:
            raise InvalidValue("Horloge de brief invalide")
        start = start.astimezone(timezone.utc)
        mandate = self.verifier.require_authorized(
            actor, mandate_id=request.mandate_id, project_id=request.project_id,
            work_item_ref=request.work_item_ref, mode=request.mode,
            target_reference=request.target_reference, now=start,
        )
        # La délégation PRIVATE n'a pas encore de politique de divulgation M2-A.
        if self.registry.read_scope_classification(actor) != "INTERNAL":
            raise AccessDenied("Mandat indisponible ou non autorisé")
        # M1 applique déjà les droits de lecture, classifications, scopes et owner-sharing.
        project = self.registry.get_registry(actor, request.project_id)
        if project.scope_id != actor.scope_id or project.project_id != request.project_id:
            raise NotFound("Ressource indisponible")
        tasks = self.registry.list_tasks(actor, request.project_id)
        task = next((item for item in tasks if item["id"] == request.work_item_ref.id), None)
        if task is None:
            raise NotFound("Ressource indisponible")

        # Relecture et revalidation empêchent la remise sous mandat révoqué ou contexte périmé.
        final_time = self.clock.now()
        if not isinstance(final_time, datetime) or final_time.utcoffset() is None:
            raise InvalidValue("Horloge de brief invalide")
        final_time = final_time.astimezone(timezone.utc)
        self.verifier.require_current(actor, mandate, final_time)
        if self.registry.get_registry(actor, request.project_id) != project:
            raise Conflict("Contexte projet modifié pendant la projection")
        updated = next((item for item in self.registry.list_tasks(actor, request.project_id)
                        if item["id"] == request.work_item_ref.id), None)
        if updated != task:
            raise Conflict("Contexte tâche modifié pendant la projection")
        if self.registry.read_scope_classification(actor) != "INTERNAL":
            raise AccessDenied("Mandat indisponible ou non autorisé")
        last_seen = self.clock.now()
        if not isinstance(last_seen, datetime) or last_seen.utcoffset() is None:
            raise InvalidValue("Horloge de brief invalide")
        last_seen = last_seen.astimezone(timezone.utc)
        self.verifier.require_current(actor, mandate, last_seen)
        expiry = min(mandate.expires_at.astimezone(timezone.utc), start + timedelta(minutes=20))
        if expiry <= last_seen:
            raise AccessDenied("Mandat indisponible ou non autorisé")

        # Liste blanche strictement orientée tâche. Pas de history, evidence, URI ni export.
        read_only = request.mode == "AUDIT"
        return OperatingBriefDTO(
            schema_version=SCHEMA_VERSION,
            brief_id=str(uuid4()),
            created_at=start,
            expires_at=expiry,
            projection_created_at=start,
            scope_id=actor.scope_id,
            project_id=project.project_id,
            work_item_ref=request.work_item_ref,
            mandate_id=mandate.mandate_id,
            mode=mandate.mode,
            authority_level=mandate.authority_level,
            allowed_actions=tuple(sorted(mandate.allowed_actions)),
            problem=task["title"],
            expected_outcome=("Rapport de constats sans mutation" if read_only
                              else "Analyse structurée et recommandations soumises à validation"),
            in_scope=(f"TASK:{task['id']}",),
            out_of_scope=("MERGE", "PUBLISH", "DELETE", "APPROVE", "CHANGE_PRIORITY"),
            target_reference=mandate.target_reference,
            source_watermark=f"m1:task:{task['id']}:v{task['version']}:project:{project.project_id}",
            acceptance_criteria=("Brief issu d'un projet et travail visibles",
                                 "Aucune mutation métier ni validation implicite"),
            required_evidence=("Référence exacte et preuve vérifiable par système source",),
            human_decisions=("Toute mutation ou approbation nécessite une autorisation distincte",),
            risks=("Données de contexte non équivalentes à une preuve de résultat",),
            limitations=("Projection de lecture locale et synthétique uniquement",
                         "Aucune autorisation exécutable portée par ce DTO"),
            next_safe_action=("Produire une analyse en lecture seule" if read_only
                              else "Préparer une proposition sans modifier le domaine"),
        )
