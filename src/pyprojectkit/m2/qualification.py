"""M2-C - Dossier Q-M2 descriptif et non autoritatif.

Une CI verte ne signe aucune décision humaine et n'autorise aucune publication.
La source des résultats est explicitement portée par le manifest, jamais devinée.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Literal

from ..domain import InvalidValue

AcceptanceStatus = Literal["PASS", "FAIL", "PARTIAL", "NOT_EXECUTED", "NOT_APPLICABLE"]
VALID_STATUSES = frozenset({"PASS", "FAIL", "PARTIAL", "NOT_EXECUTED", "NOT_APPLICABLE"})
CRITERIA: tuple[str, ...] = tuple(f"AC-{n:03}" for n in range(27, 38))
CRITERION_REQUIREMENTS: dict[str, str] = {
    "AC-027": "Brief versionné, mandaté, borné et visible dans M1",
    "AC-028": "Rapport corrélé à la tâche, au mandat et à la référence exacte",
    "AC-029": "Déclaration agent sans promotion métier ou preuve automatique",
    "AC-030": "Audit read-only par défaut, source et Task inchangées",
    "AC-031": "A2 sans autorité merge, publish, delete ou priorité réservée",
    "AC-032": "Action hors mandat refusée sans effet de succès",
    "AC-033": "Idempotence après retries et redémarrage",
    "AC-034": "Vérification indépendante et décision humaine distincte",
    "AC-035": "Isolation des scopes et des propriétaires",
    "AC-036": "Reprise du même WorkItem depuis provenance persistée",
    "AC-037": "Projet non logiciel sans gates logiciels imposés",
}
SECURITY_BLOCKERS = frozenset({
    "AC-029", "AC-030", "AC-031", "AC-032", "AC-033", "AC-034", "AC-035",
})
_HEX = frozenset("0123456789abcdef")


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 2048:
        raise InvalidValue("Champ " + field + " invalide")


@dataclass(frozen=True, slots=True)
class AcceptanceEvidence:
    criterion_id: str
    status: AcceptanceStatus
    code_sha: str
    test_node_ids: tuple[str, ...]
    ci_run_url: str
    environment: str
    observed_result: str
    limitations: tuple[str, ...] = ()
    residual_risks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.criterion_id not in CRITERIA or self.status not in VALID_STATUSES:
            raise InvalidValue("AC ou statut inconnu")
        if len(self.code_sha) != 40 or not set(self.code_sha.lower()) <= _HEX:
            raise InvalidValue("SHA Git complet requis")
        for name in ("ci_run_url", "environment", "observed_result"):
            _require_text(getattr(self, name), name)
        if not self.ci_run_url.startswith("https://github.com/"):
            raise InvalidValue("Lien CI GitHub requis")
        if not isinstance(self.test_node_ids, tuple) or len(self.test_node_ids) > 100:
            raise InvalidValue("Identifiants de tests invalides")
        for node in self.test_node_ids:
            _require_text(node, "test_node_id")
        if self.status == "PASS" and not self.test_node_ids:
            raise InvalidValue("Aucun test référencé pour PASS")
        if self.status in ("FAIL", "PARTIAL", "NOT_EXECUTED", "NOT_APPLICABLE") and not self.limitations:
            raise InvalidValue("Statut incomplet sans limitation explicite")
        for item in self.limitations + self.residual_risks:
            _require_text(item, "limit_or_risk")


@dataclass(frozen=True, slots=True)
class QualificationDossier:
    code_sha: str
    evidence: tuple[AcceptanceEvidence, ...]
    assessed_count: int
    passed_count: int
    failed_count: int
    partial_count: int
    unassessed_count: int
    technical_status: str
    recommendation: str
    human_gate: str = "PENDING"
    adoption_decision: str = "NOT_GRANTED"

    def to_dict(self) -> dict[str, object]:
        from dataclasses import asdict
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2)


def build_qualification_dossier(entries: tuple[AcceptanceEvidence, ...]) -> QualificationDossier:
    """Assemble les 11 AC, mais ne peut PAS enregistrer un gate ou un consentement."""
    if len(entries) != len(CRITERIA) or {e.criterion_id for e in entries} != set(CRITERIA):
        raise InvalidValue("Les onze AC-027..037 sont obligatoires et uniques")
    code_shas = {e.code_sha for e in entries}
    if len(code_shas) != 1:
        raise InvalidValue("Matrice hors d'un SHA unique")
    passes = sum(e.status == "PASS" for e in entries)
    failures = sum(e.status == "FAIL" for e in entries)
    partial = sum(e.status == "PARTIAL" for e in entries)
    unassessed = sum(e.status in ("NOT_EXECUTED", "NOT_APPLICABLE") for e in entries)
    blockers = any(
        e.status in ("FAIL", "PARTIAL", "NOT_EXECUTED", "NOT_APPLICABLE")
        and e.criterion_id in SECURITY_BLOCKERS
        for e in entries
    )
    if failures or blockers:
        tech, recommendation = "BLOCKED", "NO_GO_RECOMMENDED"
    elif partial or unassessed:
        tech, recommendation = "INCOMPLETE", "HUMAN_REVIEW_REQUIRED"
    else:
        tech, recommendation = "TECHNICAL_PASS_REPORTED", "READY_FOR_HUMAN_REVIEW"
    return QualificationDossier(
        code_sha=entries[0].code_sha, evidence=entries,
        assessed_count=11 - unassessed, passed_count=passes,
        failed_count=failures, partial_count=partial, unassessed_count=unassessed,
        technical_status=tech, recommendation=recommendation,
    )
