"""Modèles de lecture et historiques M1, sans seconde vérité de ProjectStatus."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Family(StrEnum):
    PACKAGE = "PACKAGE"
    PRODUCT = "PRODUCT"
    CLIENT = "CLIENT"
    TEACHING = "TEACHING"
    PERSONAL = "PERSONAL"


class AssessmentResult(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class PortfolioDecision(StrEnum):
    KEEP = "KEEP"
    MERGE = "MERGE"
    PARK = "PARK"
    RETIRE = "RETIRE"


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    project_id: str
    name: str
    owner_id: str
    scope_id: str
    project_status: str
    family: str
    priority: int
    due_date: str | None
    registered_at: str


@dataclass(frozen=True, slots=True)
class PortfolioPage:
    items: tuple[RegistryEntry, ...]
    total: int
    facets: dict[str, int]
    offset: int
    limit: int


@dataclass(frozen=True, slots=True)
class NextAction:
    task_id: str | None
    description: str | None
    reason: str


@dataclass(frozen=True, slots=True)
class ResumeContext:
    project: RegistryEntry
    open_tasks: tuple[dict[str, str], ...]
    latest_observation: dict[str, object] | None
    latest_snapshot: dict[str, object] | None
    latest_handoff: dict[str, object] | None
    decisions: tuple[dict[str, object], ...]
    unresolved_cases: tuple[dict[str, object], ...]
    next_action: NextAction
    source_freshness: str
    incomplete_sections: tuple[str, ...]