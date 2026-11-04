"""M2-04 : rapports Pythos déclaratifs, schéma strict versionné et borné."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any

from ..domain import InvalidValue
from .contracts import (
    ExactTargetReference, PythosMode, UnsupportedContractVersion, WorkItemRef,
    _deduplicate, _mapping, _str, _time,
)

REPORT_VERSION = "1.0"
MAX_REPORT_BYTES = 32_768
OUTCOMES = frozenset({"SUCCEEDED", "PARTIAL", "FAILED", "UNKNOWN"})
STATUSES = frozenset({
    "CONCEPTUAL", "SPECIFIED", "IMPLEMENTED", "TESTED", "QUALIFIED",
    "PUBLISHED", "OPERATED", "UNKNOWN", "FAILED",
})
KEY = re.compile(r"[a-zA-Z0-9_.:-]{1,128}\Z")
EVIDENCE_TYPES = frozenset({"GIT_COMMIT", "CI_RUN", "DOCUMENT_VERSION", "PROJECT_REVISION"})
REPORT_FIELDS = frozenset({
    "schema_version", "report_id", "brief_id", "mandate_id", "scope_id", "project_id",
    "work_item_ref", "mode", "target_reference", "source_watermark", "produced_at",
    "outcome", "reported_status", "idempotency_key", "changes_made",
    "verification_performed", "evidence_references", "limitations",
    "residual_risks", "human_decisions_required", "next_action",
})
ARRAY_FIELDS = frozenset({
    "changes_made", "verification_performed", "limitations", "residual_risks",
    "human_decisions_required",
})


def _uuid(value: object, field: str) -> str:
    from uuid import UUID
    data = _str(value, field, limit=64)
    try:
        if str(UUID(data)) != data:
            raise ValueError("not canonical")
    except (ValueError, TypeError) as exc:
        raise InvalidValue(f"UUID {field} invalide") from exc
    return data


def _safe_ref(value: str, field: str) -> None:
    _str(value, field, limit=256)
    if any(token in value for token in ("://", "?", "#", "@", chr(10), chr(13))):
        raise InvalidValue(f"Référence {field} non opaque")


def _text_list(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)) or len(value) > 32:
        raise InvalidValue(f"Liste {name} invalide")
    result = tuple(value)
    for part in result:
        _str(part, name, limit=512)
    return result


@dataclass(frozen=True, slots=True)
class ReportEvidenceRefDTO:
    source_type: str
    resource_ref: str
    revision: str
    claim: str
    available: bool | None

    def __post_init__(self) -> None:
        if self.source_type not in EVIDENCE_TYPES:
            raise InvalidValue("Source de preuve inconnue")
        _safe_ref(self.resource_ref, "resource_ref")
        _safe_ref(self.revision, "revision")
        _str(self.claim, "claim", limit=512)
        if self.available is not None and type(self.available) is not bool:
            raise InvalidValue("Disponibilité non booléenne")
        if self.source_type == "GIT_COMMIT" and not re.fullmatch(r"[0-9a-fA-F]{40}", self.revision):
            raise InvalidValue("SHA Git complet requis")

    @classmethod
    def from_dict(cls, value: object) -> "ReportEvidenceRefDTO":
        item = _mapping(value, frozenset({"source_type", "resource_ref", "revision", "claim", "available"}))
        return cls(
            _str(item["source_type"], "source_type"),
            _str(item["resource_ref"], "resource_ref"),
            _str(item["revision"], "revision"),
            _str(item["claim"], "claim"),
            item["available"],
        )


@dataclass(frozen=True, slots=True)
class ExecutionReportDTO:
    schema_version: str
    report_id: str
    brief_id: str
    mandate_id: str
    scope_id: str
    project_id: str
    work_item_ref: WorkItemRef
    mode: PythosMode
    target_reference: ExactTargetReference
    source_watermark: str
    produced_at: datetime
    outcome: str
    reported_status: str
    idempotency_key: str
    changes_made: tuple[str, ...]
    verification_performed: tuple[str, ...]
    evidence_references: tuple[ReportEvidenceRefDTO, ...]
    limitations: tuple[str, ...]
    residual_risks: tuple[str, ...]
    human_decisions_required: tuple[str, ...]
    next_action: str

    def __post_init__(self) -> None:
        if self.schema_version != REPORT_VERSION:
            raise UnsupportedContractVersion("Version de report non supportée")
        for name in ("report_id", "brief_id", "project_id"):
            _uuid(getattr(self, name), name)
        _uuid(self.work_item_ref.id, "work_item_ref.id")
        if not isinstance(self.work_item_ref, WorkItemRef) or self.work_item_ref.kind != "TASK":
            raise InvalidValue("Type de travail invalide")
        if not isinstance(self.target_reference, ExactTargetReference):
            raise InvalidValue("Cible invalide")
        for field in ("mandate_id", "scope_id", "source_watermark", "next_action"):
            _str(getattr(self, field), field)
        if self.mode not in ("AUDIT", "PRODUCTION", "LEARNING", "PORTFOLIO"):
            raise InvalidValue("Mode invalide")
        if self.outcome not in OUTCOMES or self.reported_status not in STATUSES:
            raise InvalidValue("Outcome ou statut déclaré invalide")
        if type(self.idempotency_key) is not str or not KEY.fullmatch(self.idempotency_key):
            raise InvalidValue("Clé idempotente invalide")
        _time(self.produced_at, "produced_at")
        for field in ARRAY_FIELDS:
            _text_list(getattr(self, field), field)
        if not isinstance(self.evidence_references, tuple) or len(self.evidence_references) > 16:
            raise InvalidValue("Trop de références de preuve")
        if not all(isinstance(x, ReportEvidenceRefDTO) for x in self.evidence_references):
            raise InvalidValue("Référence de preuve invalide")
        if len(self.to_json().encode("utf-8")) > MAX_REPORT_BYTES:
            raise InvalidValue("Report trop volumineux")

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = asdict(self)
        result["produced_at"] = _time(self.produced_at, "produced_at").isoformat()
        for field in ARRAY_FIELDS:
            result[field] = list(getattr(self, field))
        result["evidence_references"] = [asdict(item) for item in self.evidence_references]
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False,
                          allow_nan=False, separators=(",", ":"))

    def fingerprint(self) -> str:
        return sha256(self.to_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, value: object) -> "ExecutionReportDTO":
        raw = _mapping(value, REPORT_FIELDS)
        if raw["schema_version"] != REPORT_VERSION:
            raise UnsupportedContractVersion("Version de report non supportée")
        wk = _mapping(raw["work_item_ref"], frozenset({"kind", "id"}))
        target = _mapping(raw["target_reference"], frozenset({"source_type", "resource_ref", "revision"}))
        try:
            at = datetime.fromisoformat(_str(raw["produced_at"], "produced_at", limit=48).replace("Z", "+00:00"))
        except ValueError as exc:
            raise InvalidValue("Date du report invalide") from exc
        for name in ("schema_version", "report_id", "brief_id", "mandate_id",
                     "scope_id", "project_id", "mode", "source_watermark",
                     "outcome", "reported_status", "idempotency_key", "next_action"):
            _str(raw[name], name)
        refs = raw["evidence_references"]
        if not isinstance(refs, list) or len(refs) > 16:
            raise InvalidValue("Références invalides")
        return cls(
            schema_version=raw["schema_version"], report_id=raw["report_id"],
            brief_id=raw["brief_id"], mandate_id=raw["mandate_id"],
            scope_id=raw["scope_id"], project_id=raw["project_id"],
            work_item_ref=WorkItemRef(kind=wk["kind"], id=wk["id"]),
            mode=raw["mode"],
            target_reference=ExactTargetReference(**target),
            source_watermark=raw["source_watermark"], produced_at=at,
            outcome=raw["outcome"], reported_status=raw["reported_status"],
            idempotency_key=raw["idempotency_key"],
            changes_made=_text_list(raw["changes_made"], "changes_made"),
            verification_performed=_text_list(raw["verification_performed"], "verification_performed"),
            evidence_references=tuple(ReportEvidenceRefDTO.from_dict(x) for x in refs),
            limitations=_text_list(raw["limitations"], "limitations"),
            residual_risks=_text_list(raw["residual_risks"], "residual_risks"),
            human_decisions_required=_text_list(raw["human_decisions_required"], "human_decisions_required"),
            next_action=raw["next_action"],
        )

    @classmethod
    def from_json(cls, payload: str) -> "ExecutionReportDTO":
        if not isinstance(payload, str) or len(payload.encode("utf-8")) > MAX_REPORT_BYTES:
            raise InvalidValue("Payload report trop volumineux")
        try:
            parsed: Any = json.loads(payload, object_pairs_hook=_deduplicate)
        except (ValueError, TypeError) as exc:
            raise InvalidValue("JSON de report invalide") from exc
        return cls.from_dict(parsed)
