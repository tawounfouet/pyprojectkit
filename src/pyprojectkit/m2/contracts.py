"""Contrat d'échange M2-A v1. Le brief n'est ni une permission ni un fait métier."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import re
from typing import Any, Literal

from ..domain import InvalidValue

SCHEMA_VERSION = "1.0"
MAX_BRIEF_BYTES = 16_384
READ_ACTIONS = frozenset({"PROJECT_VIEW", "TASK_VIEW"})
PythosMode = Literal["AUDIT", "LEARNING", "PRODUCTION", "PORTFOLIO"]
AuthorityLevel = Literal["A0", "A1", "A2", "A3", "A4", "A5"]
_MODES = frozenset({"AUDIT", "LEARNING", "PRODUCTION", "PORTFOLIO"})
_LEVELS = frozenset({"A0", "A1", "A2", "A3", "A4", "A5"})
_SHA = re.compile(r"[0-9a-fA-F]{40}\Z")
_FIELDS = frozenset({
    "schema_version", "brief_id", "created_at", "expires_at", "projection_created_at",
    "scope_id", "project_id", "work_item_ref", "mandate_id", "mode", "authority_level",
    "allowed_actions", "problem", "expected_outcome", "in_scope", "out_of_scope",
    "target_reference", "source_watermark", "acceptance_criteria", "required_evidence",
    "human_decisions", "risks", "limitations", "next_safe_action",
})
_LIST_FIELDS = frozenset({
    "allowed_actions", "in_scope", "out_of_scope", "acceptance_criteria",
    "required_evidence", "human_decisions", "risks", "limitations",
})
_TIME_FIELDS = frozenset({"created_at", "expires_at", "projection_created_at"})


class UnsupportedContractVersion(InvalidValue):
    """Version du contrat non reconnue."""


def _str(value: object, name: str, *, limit: int = 2048) -> str:
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise InvalidValue(f"Champ {name} invalide")
    return value


def _time(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise InvalidValue(f"Horodatage {name} invalide")
    return value.astimezone(timezone.utc)


def _list(value: tuple[str, ...], name: str) -> None:
    if not isinstance(value, tuple) or len(value) > 32:
        raise InvalidValue(f"Liste {name} invalide")
    for item in value:
        _str(item, name, limit=512)


def _mapping(value: object, fields: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise InvalidValue("Schéma de contrat invalide")
    return value


def _deduplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidValue("Clé JSON dupliquée")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class WorkItemRef:
    kind: Literal["TASK"]
    id: str

    def __post_init__(self) -> None:
        if self.kind != "TASK":
            raise InvalidValue("Type de travail non pris en charge")
        _str(self.id, "work_item_ref.id", limit=128)


@dataclass(frozen=True, slots=True)
class ExactTargetReference:
    source_type: str
    resource_ref: str
    revision: str

    def __post_init__(self) -> None:
        if self.source_type not in ("GIT_COMMIT", "DOCUMENT_VERSION", "PROJECT_REVISION"):
            raise InvalidValue("Type de référence non pris en charge")
        _str(self.resource_ref, "resource_ref", limit=256)
        _str(self.revision, "revision", limit=256)
        if self.source_type == "GIT_COMMIT" and not _SHA.fullmatch(self.revision):
            raise InvalidValue("Référence Git: SHA de commit complet requis")


@dataclass(frozen=True, slots=True)
class OperatingBriefDTO:
    schema_version: str
    brief_id: str
    created_at: datetime
    expires_at: datetime
    projection_created_at: datetime
    scope_id: str
    project_id: str
    work_item_ref: WorkItemRef
    mandate_id: str
    mode: PythosMode
    authority_level: AuthorityLevel
    allowed_actions: tuple[str, ...]
    problem: str
    expected_outcome: str
    in_scope: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    target_reference: ExactTargetReference
    source_watermark: str
    acceptance_criteria: tuple[str, ...]
    required_evidence: tuple[str, ...]
    human_decisions: tuple[str, ...]
    risks: tuple[str, ...]
    limitations: tuple[str, ...]
    next_safe_action: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise UnsupportedContractVersion("Version de brief non supportée")
        for field in ("brief_id", "scope_id", "project_id", "mandate_id", "problem",
                      "expected_outcome", "source_watermark", "next_safe_action"):
            _str(getattr(self, field), field)
        if not isinstance(self.work_item_ref, WorkItemRef) or not isinstance(
            self.target_reference, ExactTargetReference
        ):
            raise InvalidValue("Référence du brief invalide")
        if self.mode not in _MODES or self.authority_level not in _LEVELS:
            raise InvalidValue("Mode ou niveau d'autorité invalide")
        if self.authority_level in ("A4", "A5"):
            raise InvalidValue("Autorité réservée à l'humain")
        if self.mode == "AUDIT" and self.authority_level != "A0":
            raise InvalidValue("Audit exige le niveau A0")
        for name in _LIST_FIELDS:
            _list(getattr(self, name), name)
        if not self.allowed_actions or not set(self.allowed_actions) <= READ_ACTIONS:
            raise InvalidValue("Actions du brief non autorisées")
        if not self.in_scope or not self.out_of_scope or not self.acceptance_criteria:
            raise InvalidValue("Périmètre ou critères absents")
        start, stop, projection = (
            _time(self.created_at, "created_at"), _time(self.expires_at, "expires_at"),
            _time(self.projection_created_at, "projection_created_at"),
        )
        if stop <= start or projection > start:
            raise InvalidValue("Période du brief incohérente")
        if len(self.to_json().encode("utf-8")) > MAX_BRIEF_BYTES:
            raise InvalidValue("Brief trop volumineux")

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = asdict(self)
        for field in _TIME_FIELDS:
            result[field] = _time(getattr(self, field), field).isoformat()
        for field in _LIST_FIELDS:
            result[field] = list(getattr(self, field))
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: object) -> "OperatingBriefDTO":
        raw = _mapping(value, _FIELDS)
        if raw["schema_version"] != SCHEMA_VERSION:
            raise UnsupportedContractVersion("Version de brief non supportée")
        work = _mapping(raw["work_item_ref"], frozenset({"kind", "id"}))
        target = _mapping(raw["target_reference"], frozenset({"source_type", "resource_ref", "revision"}))
        for field in _LIST_FIELDS:
            v = raw[field]
            if not isinstance(v, list) or len(v) > 32:
                raise InvalidValue(f"Liste {field} invalide")
            for item in v:
                _str(item, field, limit=512)
        dates: dict[str, datetime] = {}
        for field in _TIME_FIELDS:
            value_date = _str(raw[field], field, limit=48)
            try:
                dates[field] = datetime.fromisoformat(value_date.replace("Z", "+00:00"))
            except ValueError as exc:
                raise InvalidValue(f"Date {field} invalide") from exc
        for field in _FIELDS - _LIST_FIELDS - _TIME_FIELDS - {"work_item_ref", "target_reference"}:
            _str(raw[field], field)
        return cls(
            schema_version=raw["schema_version"],
            brief_id=raw["brief_id"],
            created_at=dates["created_at"],
            expires_at=dates["expires_at"],
            projection_created_at=dates["projection_created_at"],
            scope_id=raw["scope_id"],
            project_id=raw["project_id"],
            work_item_ref=WorkItemRef(kind=work["kind"], id=work["id"]),
            mandate_id=raw["mandate_id"],
            mode=raw["mode"],
            authority_level=raw["authority_level"],
            allowed_actions=tuple(raw["allowed_actions"]),
            problem=raw["problem"],
            expected_outcome=raw["expected_outcome"],
            in_scope=tuple(raw["in_scope"]),
            out_of_scope=tuple(raw["out_of_scope"]),
            target_reference=ExactTargetReference(**target),
            source_watermark=raw["source_watermark"],
            acceptance_criteria=tuple(raw["acceptance_criteria"]),
            required_evidence=tuple(raw["required_evidence"]),
            human_decisions=tuple(raw["human_decisions"]),
            risks=tuple(raw["risks"]),
            limitations=tuple(raw["limitations"]),
            next_safe_action=raw["next_safe_action"],
        )

    @classmethod
    def from_json(cls, payload: str) -> "OperatingBriefDTO":
        if not isinstance(payload, str) or len(payload.encode("utf-8")) > MAX_BRIEF_BYTES:
            raise InvalidValue("Payload du brief trop volumineux ou invalide")
        try:
            data = json.loads(payload, object_pairs_hook=_deduplicate)
        except (ValueError, TypeError) as exc:
            raise InvalidValue("JSON de brief invalide") from exc
        return cls.from_dict(data)
