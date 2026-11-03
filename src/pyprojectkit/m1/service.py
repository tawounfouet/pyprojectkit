"""Registre M1, preuves append-only et continuité, isolés de l'état métier M0.

Toutes les opérations passent par TrustedHost et portent une portée vérifiée.
La projection Registry ne redéfinit jamais ProjectStatus.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from ..domain import (
    AccessDenied, Conflict, DomainEvent, InvalidValue, NotFound, Project, ProjectId, TaskId, TaskStatus,
)
from ..ports import Clock
from ..service import SystemClock
from .models import AssessmentResult, Family, NextAction, PortfolioDecision, PortfolioPage, RegistryEntry, ResumeContext
from .security import TrustedHost, VerifiedActor
from .sqlite import HistoryRecord, SqliteDatabase, SqliteUnitOfWork


def _uuid(value: str) -> str:
    try:
        return str(UUID(value))
    except (TypeError, ValueError, AttributeError) as exc:
        raise InvalidValue("Identifiant UUID invalide") from exc


def _nonempty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidValue(field + " requis")
    return value.strip()


def _aware(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidValue("Timestamp avec timezone requis")
    return value.astimezone(timezone.utc).isoformat()


class RegistryService:
    """Façade M1, les ressources sont filtrées avant tout agrégat ou pagination."""

    def __init__(self, database: SqliteDatabase, authority: TrustedHost, clock: Clock | None = None):
        self.db, self.authority = database, authority
        self.clock = clock or SystemClock()

    def _now(self) -> str:
        return _aware(self.clock.now())

    def _project(self, uow: SqliteUnitOfWork, actor: VerifiedActor,
                 project_id: str, permission: str = "PROJECT_VIEW") -> Project:
        self.authority.require(actor, permission)
        obj = uow.projects.get(ProjectId(UUID(_uuid(project_id))))
        if obj is None or obj.scope != actor.scope_id:
            raise NotFound("Ressource indisponible")
        reg = uow._db().execute("SELECT 1 FROM project_registry WHERE project_id=? AND scope_id=?",
                                (project_id, actor.scope_id)).fetchone()
        if reg is None:
            raise NotFound("Ressource indisponible")
        return obj

    def _entry(self, row: Any) -> RegistryEntry:
        return RegistryEntry(row["project_id"], row["name"], row["owner_id"], row["scope_id"],
                             row["status"], row["family"], int(row["priority"]), row["due_date"], row["registered_at"])

    def _entries(self, uow: SqliteUnitOfWork, actor: VerifiedActor) -> list[RegistryEntry]:
        self.authority.require(actor, "PROJECT_VIEW")
        rows = uow._db().execute("""
            SELECT r.project_id,p.name,p.owner_id,r.scope_id,p.status,r.family,r.priority,r.due_date,r.registered_at
            FROM project_registry AS r JOIN projects AS p ON r.project_id=p.id
            WHERE r.scope_id=? AND p.scope=? ORDER BY r.priority DESC, r.project_id
        """, (actor.scope_id, actor.scope_id))
        return [self._entry(row) for row in rows]

    def create_scope(self, actor: VerifiedActor, *, policy_ref: str = "local-pilot",
                     classification: str = "INTERNAL") -> None:
        self.authority.require(actor, "SCOPE_CREATE")
        if classification not in ("INTERNAL", "PRIVATE"):
            raise InvalidValue("Classification invalide")
        with SqliteUnitOfWork(self.db) as uow:
            uow.add_scope(actor.scope_id, actor.actor_id, classification, _nonempty(policy_ref, "policy_ref"), self._now())
            uow.commit()

    def register_project(self, actor: VerifiedActor, name: str, family: str, *, priority: int = 50,
                         due_date: date | None = None) -> str:
        self.authority.require(actor, "PROJECT_CREATE")
        _nonempty(name, "Nom")
        if family not in {x.value for x in Family}:
            raise InvalidValue("Famille inconnue")
        if family not in self.authority.scope_rule(actor).allowed_families:
            raise AccessDenied("Famille non autorisée par le scope")
        if not isinstance(priority, int) or isinstance(priority, bool) or not 0 <= priority <= 100:
            raise InvalidValue("Priorité hors 0..100")
        if due_date is not None and (not isinstance(due_date, date) or isinstance(due_date, datetime)):
            raise InvalidValue("Échéance civile invalide")
        with SqliteUnitOfWork(self.db) as uow:
            sid = ProjectId(uuid4())
            obj = Project(sid, name, actor.actor_id, actor.scope_id)
            uow.projects.add(obj)
            uow.add_registry(str(sid.value), actor.scope_id, family, priority,
                             due_date.isoformat() if due_date else None, self._now())
            uow.record(DomainEvent("ProjectCreated", str(sid.value), self.clock.now(), actor.actor_id))
            uow.commit()
            return str(sid.value)

    def list_registry(self, actor: VerifiedActor, *, offset: int = 0, limit: int = 50,
                      family: str | None = None) -> PortfolioPage:
        if offset < 0 or not 0 < limit <= 200:
            raise InvalidValue("Pagination invalide")
        if family is not None and family not in {x.value for x in Family}:
            raise InvalidValue("Famille inconnue")
        with SqliteUnitOfWork(self.db) as uow:
            # Filtrage de scope dans SQL AVANT comptage, facettes et pagination.
            entries = self._entries(uow, actor)
            selected = [e for e in entries if family is None or e.family == family]
            facets: dict[str, int] = {}
            for entry in selected:
                facets[entry.family] = facets.get(entry.family, 0) + 1
            return PortfolioPage(tuple(selected[offset:offset + limit]), len(selected), facets, offset, limit)

    def get_registry(self, actor: VerifiedActor, project_id: str) -> RegistryEntry:
        project_id = _uuid(project_id)
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, project_id)
            for item in self._entries(uow, actor):
                if item.project_id == project_id:
                    return item
        raise NotFound("Ressource indisponible")

    def list_tasks(self, actor: VerifiedActor, project_id: str) -> tuple[dict[str, str], ...]:
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, _uuid(project_id))
            self.authority.require(actor, "TASK_VIEW")
            return tuple({"id": str(t.id.value), "title": t.title, "status": t.status.value,
                          "version": str(t.version)} for t in sorted(uow.tasks.list_all(), key=lambda t: str(t.id.value))
                         if str(t.project_id.value) == project_id)

    def link_external(self, actor: VerifiedActor, project_id: str, provider: str,
                      external_id: str, relation_type: str = "TRACKS", uri: str | None = None) -> str:
        self.authority.require(actor, "EXTERNAL_LINK")
        project_id = _uuid(project_id)
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, project_id)
            identifier = str(uuid4())
            uow.add_external(identifier, project_id, actor.scope_id, _nonempty(provider, "Provider"),
                             _nonempty(external_id, "ExternalId"), _nonempty(relation_type, "RelationType"), uri, self._now())
            uow.commit()
            return identifier

    def list_external(self, actor: VerifiedActor, project_id: str) -> tuple[dict[str, str | None], ...]:
        self.authority.require(actor, "EXTERNAL_READ")
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, _uuid(project_id))
            return tuple(uow.records.external(project_id, actor.scope_id))

    def _append(self, uow: SqliteUnitOfWork, actor: VerifiedActor, project_id: str,
                kind: str, payload: dict[str, object], classification: str = "INTERNAL") -> str:
        self.authority.require(actor, "WRITE_" + kind.upper(), classification=classification)
        self._project(uow, actor, project_id)
        rid = str(uuid4())
        uow.records.append(HistoryRecord(rid, kind, project_id, actor.scope_id, classification, self._now(), payload, 0))
        return rid

    def _visible_records(self, uow: SqliteUnitOfWork, actor: VerifiedActor, project_id: str,
                         kind: str | None = None) -> list[HistoryRecord]:
        result = []
        for record in uow.records.list_records(project_id, actor.scope_id, kind):
            try:
                self.authority.require(actor, "READ_" + record.kind.upper(), classification=record.classification)
            except AccessDenied:
                continue
            result.append(record)
        return result

    def list_history(self, actor: VerifiedActor, project_id: str,
                     kind: str | None = None) -> tuple[dict[str, object], ...]:
        project_id = _uuid(project_id)
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, project_id)
            records = self._visible_records(uow, actor, project_id, kind)
            return tuple({"id": r.id, "kind": r.kind, "recorded_at": r.recorded_at,
                          "classification": r.classification, **r.payload} for r in records)

    def record_claim(self, actor: VerifiedActor, project_id: str, *, subject: str,
                     statement: str, source_ref: str, classification: str = "INTERNAL") -> str:
        with SqliteUnitOfWork(self.db) as uow:
            result = self._append(uow, actor, _uuid(project_id), "claim",
                                  {"subject": _nonempty(subject, "Subject"), "statement": _nonempty(statement, "Claim"),
                                   "source_ref": _nonempty(source_ref, "SourceRef")}, classification)
            uow.commit()
            return result

    def observe(self, actor: VerifiedActor, project_id: str, *, subject: str,
                value: str, source_ref: str, observed_at: datetime, available: bool = True,
                classification: str = "INTERNAL") -> str:
        payload: dict[str, object] = {"subject": _nonempty(subject, "Subject"), "value": _nonempty(value, "Value"),
                                      "source_ref": _nonempty(source_ref, "SourceRef"), "observed_at": _aware(observed_at),
                                      "available": bool(available)}
        with SqliteUnitOfWork(self.db) as uow:
            result = self._append(uow, actor, _uuid(project_id), "observation", payload, classification)
            uow.commit()
            return result

    def attach_evidence(self, actor: VerifiedActor, project_id: str, *, target_ref: str, revision: str,
                        source_ref: str, available: bool = True, classification: str = "INTERNAL") -> str:
        payload: dict[str, object] = {"target_ref": _nonempty(target_ref, "Target"),
                                      "revision": _nonempty(revision, "Revision"),
                                      "source_ref": _nonempty(source_ref, "SourceRef"), "available": bool(available)}
        with SqliteUnitOfWork(self.db) as uow:
            result = self._append(uow, actor, _uuid(project_id), "evidence", payload, classification)
            uow.commit()
            return result

    def assess(self, actor: VerifiedActor, project_id: str, *, evidence_id: str, target_ref: str,
               revision: str, criterion: str, result: AssessmentResult, method: str) -> str:
        project_id = _uuid(project_id)
        if not isinstance(result, AssessmentResult):
            raise InvalidValue("Resultat de vérification invalide")
        self.authority.require(actor, "ASSESS")
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, project_id)
            matching = [r for r in self._visible_records(uow, actor, project_id, "evidence") if r.id == _uuid(evidence_id)]
            if not matching:
                raise NotFound("Ressource indisponible")
            evidence = matching[0]
            if evidence.payload["target_ref"] != target_ref or evidence.payload["revision"] != revision:
                raise Conflict("Preuve portant sur une autre révision")
            if not evidence.payload["available"] and result == AssessmentResult.PASS:
                raise Conflict("Source inaccessible : PASS interdit")
            payload: dict[str, object] = {"evidence_id": evidence.id, "target_ref": _nonempty(target_ref, "Target"),
                                          "revision": _nonempty(revision, "Revision"), "criterion": _nonempty(criterion, "Criterion"),
                                          "result": result.value, "method": _nonempty(method, "Method"), "evaluator": actor.actor_id}
            identifier = self._append(uow, actor, project_id, "assessment", payload, evidence.classification)
            uow.commit()
            return identifier

    def verify_status(self, actor: VerifiedActor, project_id: str, *, target_ref: str,
                      revision: str, criterion: str) -> str:
        # Un PASS sur SHA A ne crée jamais un PASS sur SHA B.
        history = self.list_history(actor, project_id, "assessment")
        matching = [h for h in history if h.get("target_ref") == target_ref and h.get("revision") == revision
                    and h.get("criterion") == criterion]
        return str(matching[-1]["result"]) if matching else AssessmentResult.UNKNOWN.value

    def open_reconciliation(self, actor: VerifiedActor, project_id: str, left_id: str, right_id: str) -> str:
        project_id = _uuid(project_id)
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, project_id)
            observations = {r.id: r for r in self._visible_records(uow, actor, project_id, "observation")}
            left, right = observations.get(_uuid(left_id)), observations.get(_uuid(right_id))
            if left is None or right is None:
                raise NotFound("Ressource indisponible")
            if left.id == right.id or left.payload["subject"] != right.payload["subject"] or left.payload["value"] == right.payload["value"]:
                raise Conflict("Conflit de sources non démontré")
            classification = "PRIVATE" if "PRIVATE" in (left.classification, right.classification) else "INTERNAL"
            result = self._append(uow, actor, project_id, "reconciliation",
                                  {"left_id": left.id, "right_id": right.id, "subject": left.payload["subject"], "status": "OPEN"},
                                  classification)
            uow.commit()
            return result

    def resolve_reconciliation(self, actor: VerifiedActor, project_id: str, case_id: str, rationale: str) -> str:
        project_id = _uuid(project_id)
        self.authority.require(actor, "RESOLVE")
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, project_id)
            cases = [r for r in self._visible_records(uow, actor, project_id, "reconciliation") if r.id == _uuid(case_id)]
            if not cases:
                raise NotFound("Ressource indisponible")
            if any(r.payload.get("case_id") == case_id for r in self._visible_records(uow, actor, project_id, "resolution")):
                raise Conflict("Conflit déjà résolu")
            result = self._append(uow, actor, project_id, "resolution",
                                  {"case_id": case_id, "rationale": _nonempty(rationale, "Rationale"), "resolved_by": actor.actor_id},
                                  cases[0].classification)
            uow.commit()
            return result

    def record_decision(self, actor: VerifiedActor, project_id: str, *, subject: str,
                        statement: str, portfolio: PortfolioDecision | None = None) -> str:
        payload: dict[str, object] = {"subject": _nonempty(subject, "Subject"),
                                      "statement": _nonempty(statement, "Statement"), "status": "PROPOSED",
                                      "proposed_by": actor.actor_id}
        if portfolio is not None:
            if not isinstance(portfolio, PortfolioDecision):
                raise InvalidValue("Décision portefeuille invalide")
            payload["portfolio"] = portfolio.value
        with SqliteUnitOfWork(self.db) as uow:
            result = self._append(uow, actor, _uuid(project_id), "decision", payload)
            uow.commit()
            return result

    def approve_decision(self, actor: VerifiedActor, project_id: str, decision_id: str) -> str:
        project_id = _uuid(project_id)
        self.authority.require(actor, "APPROVE")
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, project_id)
            decisions = [r for r in self._visible_records(uow, actor, project_id, "decision") if r.id == _uuid(decision_id)]
            if not decisions:
                raise NotFound("Ressource indisponible")
            if any(r.payload.get("decision_id") == decision_id for r in self._visible_records(uow, actor, project_id, "approval")):
                raise Conflict("Décision déjà approuvée")
            result = self._append(uow, actor, project_id, "approval",
                                  {"decision_id": decision_id, "approved_by": actor.actor_id})
            uow.commit()
            return result

    def approve_publication(self, actor: VerifiedActor, project_id: str, *, target_ref: str,
                            revision: str, criterion: str) -> str:
        project_id = _uuid(project_id)
        self.authority.require(actor, "APPROVE")
        requires_pass = self.authority.scope_rule(actor).require_pass_for_publish
        if requires_pass and self.verify_status(actor, project_id, target_ref=target_ref, revision=revision, criterion=criterion) != "PASS":
            raise Conflict("Publication impossible sans preuve vérifiée sur la révision demandée")
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, project_id)
            result = self._append(uow, actor, project_id, "approval",
                                  {"target_ref": _nonempty(target_ref, "Target"), "revision": _nonempty(revision, "Revision"),
                                   "criterion": _nonempty(criterion, "Criterion"), "approved_by": actor.actor_id,
                                   "type": "PUBLICATION"})
            uow.commit()
            return result

    def record_blocker(self, actor: VerifiedActor, project_id: str, reason: str) -> str:
        with SqliteUnitOfWork(self.db) as uow:
            result = self._append(uow, actor, _uuid(project_id), "blocker", {"reason": _nonempty(reason, "Reason")})
            uow.commit()
            return result

    def _open_tasks(self, uow: SqliteUnitOfWork, actor: VerifiedActor, project_id: str) -> list[dict[str, str]]:
        self.authority.require(actor, "TASK_VIEW")
        return [{"id": str(t.id.value), "title": t.title, "status": t.status.value, "version": str(t.version)}
                for t in sorted(uow.tasks.list_all(), key=lambda t: str(t.id.value))
                if str(t.project_id.value) == project_id and t.status not in (TaskStatus.DONE, TaskStatus.CANCELLED)]

    def _next_action(self, tasks: list[dict[str, str]]) -> NextAction:
        candidates = [t for t in tasks if t["status"] in ("TODO", "READY", "IN_PROGRESS", "BLOCKED", "IN_REVIEW")]
        if not candidates:
            return NextAction(None, None, "NONE_WITH_REASON: aucune tâche ouverte")
        item = candidates[0]
        return NextAction(item["id"], item["title"], "Tâche existante à examiner; aucune commande créée")

    def next_action(self, actor: VerifiedActor, project_id: str) -> NextAction:
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, _uuid(project_id))
            return self._next_action(self._open_tasks(uow, actor, project_id))

    def capture_snapshot(self, actor: VerifiedActor, project_id: str) -> str:
        project_id = _uuid(project_id)
        self.authority.require(actor, "CAPTURE")
        with SqliteUnitOfWork(self.db) as uow:
            project = self._project(uow, actor, project_id)
            tasks = self._open_tasks(uow, actor, project_id)
            obs = self._visible_records(uow, actor, project_id, "observation")
            decisions = self._visible_records(uow, actor, project_id, "decision")
            private = any(r.classification == "PRIVATE" for r in obs + decisions)
            watermark_row = uow._db().execute("SELECT COALESCE(MAX(seq),0) FROM history WHERE project_id=? AND scope_id=?",
                                              (project_id, actor.scope_id)).fetchone()
            payload: dict[str, object] = {"captured_at": self._now(), "origin": "ORIGINAL",
                                           "project_version": project.version, "project_status": project.status.value,
                                           "task_versions": {t["id"]: t["version"] for t in tasks},
                                           "open_tasks": tasks, "watermark": int(watermark_row[0]),
                                           "latest_observation_id": obs[-1].id if obs else None,
                                           "latest_decision_id": decisions[-1].id if decisions else None,
                                           "incomplete_sections": [] if obs else ["observations"]}
            result = self._append(uow, actor, project_id, "snapshot", payload, "PRIVATE" if private else "INTERNAL")
            uow.commit()
            return result

    def record_handoff(self, actor: VerifiedActor, project_id: str, *, summary: str,
                       outcome: str, risks: list[str] | None = None, unknowns: list[str] | None = None) -> str:
        payload: dict[str, object] = {"summary": _nonempty(summary, "Summary"), "outcome": _nonempty(outcome, "Outcome"),
                                      "risks": list(risks or []), "unknowns": list(unknowns or []),
                                      "producer": actor.actor_id, "next_action": "computed_at_resume"}
        with SqliteUnitOfWork(self.db) as uow:
            result = self._append(uow, actor, _uuid(project_id), "handoff", payload)
            uow.commit()
            return result

    def resume(self, actor: VerifiedActor, project_id: str) -> ResumeContext:
        project_id = _uuid(project_id)
        self.authority.require(actor, "RESUME")
        with SqliteUnitOfWork(self.db) as uow:
            self._project(uow, actor, project_id)
            entry = next(item for item in self._entries(uow, actor) if item.project_id == project_id)
            tasks = self._open_tasks(uow, actor, project_id)
            def last(kind: str) -> dict[str, object] | None:
                records = self._visible_records(uow, actor, project_id, kind)
                return {"id": records[-1].id, "recorded_at": records[-1].recorded_at, **records[-1].payload} if records else None
            decisions = tuple({"id": r.id, "recorded_at": r.recorded_at, **r.payload}
                              for r in self._visible_records(uow, actor, project_id, "decision"))
            resolved = {str(r.payload.get("case_id")) for r in self._visible_records(uow, actor, project_id, "resolution")}
            open_cases = tuple({"id": r.id, **r.payload}
                               for r in self._visible_records(uow, actor, project_id, "reconciliation") if r.id not in resolved)
            obs = last("observation")
            snap = last("snapshot")
            handoff = last("handoff")
            raw_incomplete = ["snapshot"] if snap is None else snap.get("incomplete_sections", [])
            incomplete: tuple[str, ...] = tuple(raw_incomplete) if isinstance(raw_incomplete, list) and all(
                isinstance(item, str) for item in raw_incomplete) else ("invalid_snapshot",)
            return ResumeContext(entry, tuple(tasks), obs, snap, handoff, decisions, open_cases,
                                 self._next_action(tasks), str(obs["observed_at"]) if obs else "UNKNOWN", incomplete)

    def export_project(self, actor: VerifiedActor, project_id: str) -> dict[str, object]:
        self.authority.require(actor, "EXPORT")
        # Export ne contourne jamais les policies de lecture ; aucun octroi par paramètre.
        context = self.resume(actor, project_id)
        return {"project": context.project.__dict__ if hasattr(context.project, "__dict__") else
                {field: getattr(context.project, field) for field in context.project.__dataclass_fields__},
                "open_tasks": list(context.open_tasks), "decisions": list(context.decisions),
                "latest_snapshot": context.latest_snapshot, "latest_handoff": context.latest_handoff,
                "next_action": {"task_id": context.next_action.task_id,
                                "description": context.next_action.description, "reason": context.next_action.reason}}