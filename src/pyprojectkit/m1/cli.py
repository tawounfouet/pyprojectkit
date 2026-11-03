"""CLI de démonstration M1 local. Ne constitue pas un système d'authentification.

La CLI refuse tout usage hors --demo. Le principal et les scopes synthétiques
sont provisionnés par le code, sans accepter de principal arbitraire en argument.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Sequence

from ..domain import DomainError
from .models import Family
from .security import ScopeRule, TrustedHost
from .service import RegistryService
from .sqlite import SqliteDatabase

DEMO_CREDENTIAL = "demo-only-fixture-never-use-in-production"
DEMO_SCOPES = {"demo-package", "demo-personal", "demo-client", "demo-teaching", "demo-product"}
DEMO_PERMISSIONS = {
    "SCOPE_CREATE", "PROJECT_CREATE", "PROJECT_VIEW", "TASK_VIEW", "EXTERNAL_LINK", "EXTERNAL_READ",
    "WRITE_CLAIM", "READ_CLAIM", "WRITE_OBSERVATION", "READ_OBSERVATION", "WRITE_EVIDENCE", "READ_EVIDENCE",
    "WRITE_ASSESSMENT", "READ_ASSESSMENT", "ASSESS", "WRITE_RECONCILIATION", "READ_RECONCILIATION",
    "WRITE_RESOLUTION", "READ_RESOLUTION", "RESOLVE", "WRITE_DECISION", "READ_DECISION", "APPROVE",
    "WRITE_APPROVAL", "READ_APPROVAL", "WRITE_SNAPSHOT", "READ_SNAPSHOT", "CAPTURE", "RESUME",
    "WRITE_HANDOFF", "READ_HANDOFF", "WRITE_BLOCKER", "READ_BLOCKER", "EXPORT",
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pyprojectkit", description="M1 local, uniquement des fixtures synthétiques")
    parser.add_argument("--demo", action="store_true", help="Mode démo synthétique obligatoire")
    parser.add_argument("--db", type=Path, required=True, help="Chemin SQLite local, hors dépôt")
    parser.add_argument("--scope", choices=sorted(DEMO_SCOPES), default="demo-package")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("init")
    reg = commands.add_parser("register")
    reg.add_argument("--name", required=True)
    reg.add_argument("--family", choices=[e.value for e in Family], required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--limit", type=int, default=50)
    resume = commands.add_parser("resume")
    resume.add_argument("project_id")
    observe = commands.add_parser("observe")
    observe.add_argument("project_id")
    observe.add_argument("--subject", required=True)
    observe.add_argument("--value", required=True)
    observe.add_argument("--source", required=True)
    snap = commands.add_parser("snapshot")
    snap.add_argument("project_id")
    handoff = commands.add_parser("handoff")
    handoff.add_argument("project_id")
    handoff.add_argument("--summary", required=True)
    handoff.add_argument("--outcome", required=True)
    args = parser.parse_args(argv)
    if not args.demo:
        parser.error("Cette CLI n'autorise que --demo sur données synthétiques")
    host = TrustedHost({DEMO_CREDENTIAL: ("demo-owner", {scope: set(DEMO_PERMISSIONS) for scope in DEMO_SCOPES})},
                       rules={"demo-teaching": ScopeRule(require_pass_for_publish=False)})
    actor = host.authenticate(DEMO_CREDENTIAL, args.scope)
    service = RegistryService(SqliteDatabase(args.db), host)
    try:
        if args.action == "init":
            service.create_scope(actor)
            output: object = {"scope": actor.scope_id, "initialized": True}
        elif args.action == "register":
            output = {"project_id": service.register_project(actor, args.name, args.family)}
        elif args.action == "list":
            from dataclasses import asdict
            output = asdict(service.list_registry(actor, limit=args.limit))
        elif args.action == "resume":
            from dataclasses import asdict
            output = asdict(service.resume(actor, args.project_id))
        elif args.action == "observe":
            output = {"observation_id": service.observe(actor, args.project_id, subject=args.subject,
                                                       value=args.value, source_ref=args.source,
                                                       observed_at=datetime.now(timezone.utc))}
        elif args.action == "snapshot":
            output = {"snapshot_id": service.capture_snapshot(actor, args.project_id)}
        else:
            output = {"handoff_id": service.record_handoff(actor, args.project_id,
                                                           summary=args.summary, outcome=args.outcome)}
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
        return 0
    except DomainError as exc:
        parser.exit(2, f"Erreur métier : {type(exc).__name__}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())