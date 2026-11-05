"""Vérification G1 locale et éphémère : git bundle, intégrité et clone restauré.

Ne crée PAS une archive conservée, ne transfère rien hors du runner et ne valide
pas le gate G1. La conservation chiffrée et le gardien restent des décisions humaines.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

DEFAULT_LEGACY_SHA = "a523d9c61c30ef41afe3bc9cf0723beafe3c2d38"
BUNDLE_REF = "refs/heads/g1-legacy-local-proof"


class RestoreDrillError(RuntimeError):
    """La preuve de restauration n'est pas démontrée."""


def _git(*args: str, cwd: Path) -> str:
    command = ["git", "-C", str(cwd), *args]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        # Ne pas republier de chemins, détails de l'historique ni secrets
        # éventuels dans les journaux d'actions.
        raise RestoreDrillError(f"étape git échouée : {args[0]} (code {result.returncode})")
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_legacy_restoration(source: Path, legacy_sha: str) -> dict[str, str | int | bool]:
    """Test restauration dans un répertoire distinct, jamais dans la source.

    Précondition : copie Git locale non shallow avec commit historique présent.
    Aucun accès réseau ni artefact de sauvegarde durable n'est utilisé.
    """
    source = source.resolve()
    if len(legacy_sha) != 40 or any(c not in "0123456789abcdef" for c in legacy_sha):
        raise RestoreDrillError("SHA legacy non canonique")
    if _git("rev-parse", "--is-shallow-repository", cwd=source) != "false":
        raise RestoreDrillError("clone superficiel : historique complet exigé")
    try:
        kind = _git("cat-file", "-t", legacy_sha, cwd=source)
    except RestoreDrillError as error:
        raise RestoreDrillError("référence historique non disponible") from error
    if kind != "commit":
        raise RestoreDrillError("référence historique non disponible")

    original_tree = _git("rev-parse", f"{legacy_sha}^{{tree}}", cwd=source)
    with tempfile.TemporaryDirectory(prefix="pyprojectkit-g1-precheck-") as temporary:
        tempdir = Path(temporary)
        # L'écriture reste dans un dépôt temporaire isolé, pas sur le checkout.
        proof_repo = tempdir / "source"
        bundle = tempdir / "legacy.bundle"
        restore = tempdir / "restored"
        _git("clone", "--quiet", "--no-hardlinks", str(source), str(proof_repo), cwd=tempdir)
        _git("update-ref", BUNDLE_REF, legacy_sha, cwd=proof_repo)
        _git("bundle", "create", str(bundle), BUNDLE_REF, cwd=proof_repo)
        _git("bundle", "verify", str(bundle), cwd=proof_repo)
        hash_before = _sha256(bundle)
        _git("clone", "--quiet", "--branch", "g1-legacy-local-proof", str(bundle), str(restore), cwd=tempdir)
        _git("fsck", "--full", "--no-reflogs", cwd=restore)
        restored_sha = _git("rev-parse", "HEAD", cwd=restore)
        restored_tree = _git("rev-parse", "HEAD^{tree}", cwd=restore)
        if restored_sha != legacy_sha or restored_tree != original_tree:
            raise RestoreDrillError("référence ou arbre Git restauré différents")
        if hash_before != _sha256(bundle):
            raise RestoreDrillError("empreinte du bundle modifiée durant le test")
        return {
            "status": "EPHEMERAL_GIT_RESTORE_VERIFIED",
            "legacy_commit": restored_sha,
            "legacy_tree": restored_tree,
            "bundle_sha256": hash_before,
            "bundle_size_bytes": bundle.stat().st_size,
            "isolated_clone_verified": True,
            "git_fsck_verified": True,
            "bundle_retained": False,
            "independent_encrypted_custody_verified": False,
            "g1_gate": "PENDING",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Precheck G1 sans sauvegarde persistante")
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--baseline-sha", default=DEFAULT_LEGACY_SHA)
    arguments = parser.parse_args()
    print(json.dumps(verify_legacy_restoration(arguments.repository, arguments.baseline_sha), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
