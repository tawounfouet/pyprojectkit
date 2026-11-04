"""Mandats host-side pour M2-A : aucune élévation par le texte du brief."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from ..domain import AccessDenied, Conflict, InvalidValue
from ..m1.security import TrustedHost, VerifiedActor
from .contracts import AuthorityLevel, ExactTargetReference, PythosMode, READ_ACTIONS, WorkItemRef

_GENERIC_DENIAL = "Mandat indisponible ou non autorisé"


@dataclass(frozen=True, slots=True)
class DelegationMandate:
    """Mandat provisionné par un hôte de confiance, jamais reconstruit du payload agent."""
    mandate_id: str
    actor_id: str
    delegate_id: str
    scope_id: str
    project_id: str
    work_item_ref: WorkItemRef
    mode: PythosMode
    authority_level: AuthorityLevel
    allowed_actions: tuple[str, ...]
    target_reference: ExactTargetReference
    not_before: datetime
    expires_at: datetime
    version: int = 1
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        for value in (self.mandate_id, self.actor_id, self.delegate_id, self.scope_id, self.project_id):
            if not isinstance(value, str) or not value.strip() or len(value) > 256:
                raise InvalidValue("Identifiant du mandat invalide")
        if not isinstance(self.work_item_ref, WorkItemRef) or not isinstance(
            self.target_reference, ExactTargetReference
        ):
            raise InvalidValue("Cible du mandat invalide")
        if self.mode not in ("AUDIT", "LEARNING", "PRODUCTION", "PORTFOLIO"):
            raise InvalidValue("Mode du mandat invalide")
        if self.authority_level not in ("A0", "A1", "A2", "A3"):
            raise InvalidValue("Mandat M2-A limité à A0..A3")
        if self.mode == "AUDIT" and self.authority_level != "A0":
            raise InvalidValue("Audit en A0 uniquement")
        if not isinstance(self.allowed_actions, tuple) or not set(self.allowed_actions) == READ_ACTIONS:
            raise InvalidValue("Mandat M2-A exige uniquement PROJECT_VIEW et TASK_VIEW")
        if not isinstance(self.version, int) or self.version < 1 or self.status not in (
            "ACTIVE", "SUSPENDED", "REVOKED"
        ):
            raise InvalidValue("Etat du mandat invalide")
        if not isinstance(self.not_before, datetime) or not isinstance(self.expires_at, datetime):
            raise InvalidValue("Horodatages du mandat invalides")
        if self.not_before.utcoffset() is None or self.expires_at.utcoffset() is None:
            raise InvalidValue("Horodatages du mandat sans fuseau")
        if self.not_before >= self.expires_at:
            raise InvalidValue("Validité du mandat invalide")


class MandateStorePort(Protocol):
    """Port de l'hôte : requête id seule; retourne un enregistrement autoritatif."""
    def resolve(self, mandate_id: str) -> DelegationMandate: ...


class InMemoryMandateStore:
    """Adaptateur PILOTE, alimenté par l'hôte. Pas un service IAM public."""
    def __init__(self) -> None:
        self._mandates: dict[str, DelegationMandate] = {}

    def provision(self, mandate: DelegationMandate) -> None:
        if mandate.mandate_id in self._mandates:
            raise Conflict("Mandat déjà provisionné")
        self._mandates[mandate.mandate_id] = mandate

    def resolve(self, mandate_id: str) -> DelegationMandate:
        result = self._mandates.get(mandate_id)
        if result is None:
            raise AccessDenied(_GENERIC_DENIAL)
        return result

    def revoke(self, mandate_id: str) -> None:
        before = self.resolve(mandate_id)
        self._mandates[mandate_id] = replace(before, status="REVOKED", version=before.version + 1)

    def suspend(self, mandate_id: str) -> None:
        before = self.resolve(mandate_id)
        self._mandates[mandate_id] = replace(before, status="SUSPENDED", version=before.version + 1)


class MandateVerifier:
    """Vérifie simultanément session hôte, délégation, cible et droits M1."""
    def __init__(self, host: TrustedHost, store: MandateStorePort, *, delegate_id: str = "pythos"):
        if not delegate_id.strip():
            raise InvalidValue("Délégué requis")
        self.host = host
        self.store = store
        self.delegate_id = delegate_id

    def require_authorized(
        self,
        actor: VerifiedActor,
        *,
        mandate_id: str,
        project_id: str,
        work_item_ref: WorkItemRef,
        mode: PythosMode,
        target_reference: ExactTargetReference,
        now: datetime,
    ) -> DelegationMandate:
        # La session et l'opération de construction sont vérifiées AVANT les lectures M1.
        self.host.require(actor, "BRIEF_BUILD")
        if now.utcoffset() is None:
            raise InvalidValue("Horloge avec fuseau requise")
        try:
            mandate = self.store.resolve(mandate_id)
        except Exception as exc:
            raise AccessDenied(_GENERIC_DENIAL) from exc
        if (mandate.status != "ACTIVE" or mandate.actor_id != actor.actor_id
                or mandate.scope_id != actor.scope_id or mandate.delegate_id != self.delegate_id
                or mandate.project_id != project_id or mandate.work_item_ref != work_item_ref
                or mandate.mode != mode or mandate.target_reference != target_reference
                or not (mandate.not_before <= now < mandate.expires_at)):
            raise AccessDenied(_GENERIC_DENIAL)
        if mandate.authority_level not in ("A0", "A1", "A2", "A3"):
            raise AccessDenied(_GENERIC_DENIAL)
        if mandate.mode == "AUDIT" and mandate.authority_level != "A0":
            raise AccessDenied(_GENERIC_DENIAL)
        if set(mandate.allowed_actions) != READ_ACTIONS:
            raise AccessDenied(_GENERIC_DENIAL)
        for permission in mandate.allowed_actions:
            self.host.require(actor, permission)
        return mandate

    def require_current(self, actor: VerifiedActor, previous: DelegationMandate,
                        now: datetime) -> None:
        latest = self.require_authorized(
            actor, mandate_id=previous.mandate_id, project_id=previous.project_id,
            work_item_ref=previous.work_item_ref, mode=previous.mode,
            target_reference=previous.target_reference, now=now,
        )
        if latest != previous:
            raise AccessDenied(_GENERIC_DENIAL)
