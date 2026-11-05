"""Audit local de motifs de secrets dans l'historique Git atteignable de G1.

Aucun extrait, chemin, identifiant Git d'objet ou secret n'est publié.
Les résultats sont des signaux à examiner humainement, jamais une certification.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BASELINE = "a523d9c61c30ef41afe3bc9cf0723beafe3c2d38"
MAX_OBJECT_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_OBJECTS = 20000

# Motifs volontaires : pas de faux verdict CLEAN garanti, ni de valeurs dans le rapport.
PATTERNS: dict[str, re.Pattern[bytes]] = {
    "pem_private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "github_token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{22,})\b"),
    "aws_access_key_id": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "openai_api_key": re.compile(rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}\b"),
    "slack_token": re.compile(rb"\bxox[bpars]-[A-Za-z0-9-]{16,}\b"),
    "sensitive_assignment": re.compile(
        rb"(?im)^\s*(?:export\s+)?(?:[A-Z][A-Z0-9_]*_)?(?:PASSWORD|SECRET|API_KEY|ACCESS_TOKEN|PRIVATE_KEY)(?:_[A-Z0-9_]+)?\s*[:=]\s*['\"]?[A-Za-z0-9+/_=-]{16,}"
    ),
}


class HistoryAuditError(RuntimeError):
    """Erreur neutre pour empêcher la divulgation accidentelle d'informations."""


def _git(repo: Path, *args: str, binary: bool = False) -> bytes:
    env = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1", GIT_OPTIONAL_LOCKS="0")
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, env=env, timeout=45, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise HistoryAuditError("opération Git indisponible") from error
    if result.returncode:
        # Jamais de stderr : certains outils Git peuvent y inclure des chemins sensibles.
        raise HistoryAuditError("opération Git non vérifiable")
    return result.stdout


def _canonical_sha(sha: str) -> bool:
    return bool(re.fullmatch(r"[a-f0-9]{40}", sha))


def _inside(child: Path, root: Path) -> bool:
    return child == root or child.is_relative_to(root)


def scan_history(
    repo: Path,
    baseline_sha: str = DEFAULT_BASELINE,
    *,
    max_object_bytes: int = MAX_OBJECT_BYTES,
    max_total_bytes: int = MAX_TOTAL_BYTES,
    max_objects: int = MAX_OBJECTS,
) -> dict[str, Any]:
    """Inspecte commits et blobs atteignables de la baseline, sans divulguer les matches.

    Ne parcourt pas reflogs, fichiers non suivis, GitHub metadata, sous-modules,
    objets LFS externes ou secrets absents de l'historique Git accessible.
    """
    if not _canonical_sha(baseline_sha):
        raise HistoryAuditError("SHA non canonique")
    if min(max_object_bytes, max_total_bytes, max_objects) <= 0:
        raise HistoryAuditError("limites invalides")
    if not repo.is_dir() or repo.is_symlink():
        raise HistoryAuditError("dépôt source non sûr")
    root = repo.resolve(strict=True)
    if _git(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise HistoryAuditError("historique superficiel interdit")
    if _git(root, "cat-file", "-t", baseline_sha).strip() != b"commit":
        raise HistoryAuditError("baseline non commit")

    raw_oids = _git(root, "rev-list", "--objects", "--no-object-names", baseline_sha).splitlines()
    oids = list(dict.fromkeys(raw_oids))
    if len(oids) > max_objects:
        raise HistoryAuditError("limite du nombre d'objets dépassée")
    counts: Counter[str] = Counter()
    inspected: Counter[str] = Counter()
    oversized = 0
    total_bytes = 0
    for oid_bytes in oids:
        if not re.fullmatch(rb"[0-9a-f]{40}", oid_bytes):
            raise HistoryAuditError("liste Git non canonique")
        oid = oid_bytes.decode("ascii")
        kind = _git(root, "cat-file", "-t", oid).strip()
        if kind not in (b"blob", b"commit", b"tree", b"tag"):
            raise HistoryAuditError("type d'objet non reconnu")
        if kind not in (b"blob", b"commit"):
            continue
        n_bytes_raw = _git(root, "cat-file", "-s", oid).strip()
        if not n_bytes_raw.isdigit():
            raise HistoryAuditError("taille d'objet invalide")
        size = int(n_bytes_raw)
        if size > max_object_bytes:
            oversized += 1
            continue
        if total_bytes + size > max_total_bytes:
            raise HistoryAuditError("quota de lecture historique dépassé")
        contents = _git(root, "cat-file", "-p", oid, binary=True)
        if len(contents) != size:
            raise HistoryAuditError("taille d'objet incohérente")
        total_bytes += len(contents)
        inspected[kind.decode("ascii")] += 1
        for category, expression in PATTERNS.items():
            counts[category] += len(expression.findall(contents))

    matches = sum(counts.values())
    return {
        "status": "PATTERNS_DETECTED_REVIEW_REQUIRED" if matches else "NO_PATTERN_HITS_NOT_A_CLEAN_BILL",
        "scan_scope": "git_commits_and_blobs_reachable_from_baseline_only",
        "baseline_commit": baseline_sha,
        "objects_enumerated": len(oids),
        "commits_scanned": inspected["commit"],
        "blobs_scanned": inspected["blob"],
        "bytes_scanned": total_bytes,
        "oversized_objects_not_scanned": oversized,
        "pattern_hit_counts": {name: counts[name] for name in PATTERNS},
        "pattern_hits_total": matches,
        "manual_security_review_required": True,
        "history_clean_certified": False,
        "g1_gate": "PENDING",
        "no_contents_or_paths_disclosed": True,
    }


def write_private_report(report: dict[str, Any], destination: Path, repository: Path) -> None:
    """Écrit uniquement les agrégats hors dépôt Git, avec permissions strictes."""
    if destination.is_symlink() or destination.parent.is_symlink():
        raise HistoryAuditError("destination symbolique interdite")
    if not destination.parent.is_dir() or destination.exists():
        raise HistoryAuditError("destination absente ou déjà utilisée")
    parent = destination.parent.resolve(strict=True)
    if stat.S_IMODE(parent.stat().st_mode) & 0o077:
        raise HistoryAuditError("répertoire privé 0700 requis")
    if _inside(parent, repository.resolve(strict=True)):
        raise HistoryAuditError("rapport dans dépôt Git interdit")
    payload = dict(report, generated_utc=datetime.now(timezone.utc).isoformat())
    try:
        fd = os.open(str(destination), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except OSError as error:
        raise HistoryAuditError("création du rapport impossible") from error
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Préflight G1 sans divulgation des secrets")
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--baseline-sha", default=DEFAULT_BASELINE)
    parser.add_argument("--private-report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = scan_history(args.repository, args.baseline_sha)
        write_private_report(report, args.private_report, args.repository)
    except HistoryAuditError:
        print("G1 history audit: BLOCKED (preflight failed, no sensitive details emitted)")
        return 2
    print("G1 history audit: REPORT_WRITTEN / HUMAN_REVIEW_REQUIRED / G1=PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
