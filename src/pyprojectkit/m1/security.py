"""Identité hôte vérifiée et autorisation contextuelle, sans IAM ni réseau.

Une identité est obtenue à partir d'un *secret de session fourni par l'hôte*, jamais
à partir d'un actor_id/scope soumis par un client. Le code dans le même interpréteur
reste de confiance, ce module ne fournit pas d'isolation de processus hostiles.
"""
from __future__ import annotations

from dataclasses import dataclass
from hmac import compare_digest
from secrets import token_hex

from ..domain import AccessDenied, InvalidValue
from ..ports import ActorContext


@dataclass(frozen=True, slots=True)
class VerifiedActor:
    actor_id: str
    scope_id: str
    _issuer: str
    _nonce: str

    def legacy(self) -> ActorContext:
        """Ne transmettre à M0 qu'après vérification par TrustedHost.verify()."""
        return ActorContext(self.actor_id, self.scope_id)


@dataclass(frozen=True, slots=True)
class ScopeRule:
    """Un scope peut imposer plus de preuves qu'un autre."""
    require_pass_for_publish: bool = True
    allowed_families: frozenset[str] = frozenset({"PACKAGE", "PRODUCT", "CLIENT", "TEACHING", "PERSONAL"})


class TrustedHost:
    """Autorité de composition : tokens opaques et privilèges provisionnés hors payload.

    Le token ne doit jamais être affiché, envoyé dans une Query ou journalisé.
    """

    def __init__(self, principals: dict[str, tuple[str, dict[str, set[str]]]],
                 rules: dict[str, ScopeRule] | None = None):
        if not principals:
            raise InvalidValue("Aucun principal de confiance configuré")
        self._issuer = token_hex(32)
        self._issued: dict[tuple[str, str, str], frozenset[str]] = {}
        self._principals = {token: (actor, {scope: frozenset(perms) for scope, perms in grants.items()})
                            for token, (actor, grants) in principals.items()}
        self.rules = dict(rules or {})

    def authenticate(self, opaque_credential: str, requested_scope: str) -> VerifiedActor:
        principal = self._principals.get(opaque_credential)
        if principal is None or requested_scope not in principal[1]:
            raise AccessDenied("Accès indisponible")
        actor = VerifiedActor(principal[0], requested_scope, self._issuer, token_hex(24))
        self._issued[(actor.actor_id, actor.scope_id, actor._nonce)] = principal[1][requested_scope]
        return actor

    def require(self, actor: VerifiedActor, permission: str, *, classification: str = "INTERNAL") -> None:
        if not isinstance(actor, VerifiedActor) or not compare_digest(actor._issuer, self._issuer):
            raise AccessDenied("Accès indisponible")
        if (actor.actor_id, actor.scope_id, actor._nonce) not in self._issued:
            raise AccessDenied("Accès indisponible")
        allowed = permission in self._issued[(actor.actor_id, actor.scope_id, actor._nonce)]
        if not allowed:
            raise AccessDenied("Accès indisponible")
        if classification == "PRIVATE":
            self.require(actor, "READ_PRIVATE") if permission.startswith(("READ", "LIST", "EXPORT")) else self._require_private_write(actor)
        elif classification != "INTERNAL":
            raise AccessDenied("Accès indisponible")

    def permits(self, actor: VerifiedActor, permission: str) -> bool:
        """Vérifie un privilège explicite sans divulguer l'existence d'une ressource.

        L'appelant doit d'abord vérifier le droit de lire le scope. Une permission
        PROJECT_VIEW ne donne pas automatiquement accès aux projets d'autrui.
        """
        try:
            self.require(actor, permission)
        except AccessDenied:
            return False
        return True

    def _require_private_write(self, actor: VerifiedActor) -> None:
        allowed = "WRITE_PRIVATE" in self._issued[(actor.actor_id, actor.scope_id, actor._nonce)]
        if not allowed:
            raise AccessDenied("Accès indisponible")

    def scope_rule(self, actor: VerifiedActor) -> ScopeRule:
        self.require(actor, "PROJECT_VIEW")
        return self.rules.get(actor.scope_id, ScopeRule())