"""Outil local G1 de sauvegarde Git chiffrée et de restauration contrôlée.

Il ne publie aucun bundle, ne transfère rien et ne signe aucun gate.
Dépendance optionnelle de l'outil seulement: cryptography (AES-256-GCM).
ATTENTION: la clé doit être gardée sur un support distinct de l'archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import stat
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DEFAULT_LEGACY_SHA = "a523d9c61c30ef41afe3bc9cf0723beafe3c2d38"
LOCAL_REF = "refs/heads/g1-legacy-local-custody"
CIPHERTEXT_NAME = "legacy-g1.bundle.aesgcm"
MANIFEST_NAME = "legacy-g1.manifest.json"
MAGIC = b"PYPROJECTKIT-G1-AES256GCM-v1\n"
MAX_BUNDLE_BYTES = 64 * 1024 * 1024


class CustodyError(RuntimeError):
    """Arrêt sans valider la chaîne de conservation."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")


def _git(directory: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(directory), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        # Erreur délibérément neutre : ne jamais réémettre stderr contenant des paths / secrets.
        raise CustodyError(f"opération Git non validée ({args[0]}, code {result.returncode})")
    return result.stdout.strip()


def _canonical_sha(value: str) -> bool:
    return len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def _private_directory(path: Path, *, may_create: bool = False) -> Path:
    if path.is_symlink():
        raise CustodyError("répertoire symbolique interdit")
    if may_create and not path.exists():
        path.mkdir(mode=0o700, parents=False)
    resolved = path.resolve(strict=True)
    if not resolved.is_dir() or stat.S_IMODE(resolved.stat().st_mode) & 0o077:
        raise CustodyError("répertoire privé requis (permissions 0700)")
    return resolved


def _private_file(path: Path) -> Path:
    if path.is_symlink():
        raise CustodyError("fichier symbolique interdit")
    resolved = path.resolve(strict=True)
    if not resolved.is_file() or stat.S_IMODE(resolved.stat().st_mode) & 0o077:
        raise CustodyError("fichier privé requis (permissions 0600)")
    return resolved


def _outside(path: Path, forbidden: Path, message: str) -> None:
    if path == forbidden or path.is_relative_to(forbidden):
        raise CustodyError(message)


def _read_key(key_file: Path) -> bytes:
    raw = _private_file(key_file).read_bytes()
    if len(raw) != 32:
        raise CustodyError("clé AES-256 invalide : 32 octets requis")
    return raw


def create_key(key_file: Path) -> None:
    """Génère une clé locale en 0600, jamais dans le dépôt ou le coffre ciphertext.

    L'opérateur est responsable d'enregistrer la clé dans son propre coffre distinct.
    """
    if key_file.is_symlink() or not key_file.parent.is_dir():
        raise CustodyError("parent de clé absent ou lien symbolique")
    parent = _private_directory(key_file.parent)
    if any((ancestor / ".git").exists() for ancestor in (parent, *parent.parents)):
        raise CustodyError("ne jamais créer de clé dans un dépôt Git")
    try:
        fd = os.open(str(key_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise CustodyError("clé existante : écrasement interdit") from error
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(secrets.token_bytes(32))
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        key_file.unlink(missing_ok=True)
        raise


def _write_exclusive(path: Path, data: bytes) -> None:
    if path.is_symlink():
        raise CustodyError("destination symbolique interdite")
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise CustodyError("destination déjà présente : écrasement interdit") from error
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _source_baseline(source: Path, sha: str) -> str:
    if not _canonical_sha(sha):
        raise CustodyError("SHA legacy non canonique")
    if not (source / ".git").exists() and not (source / "HEAD").exists():
        raise CustodyError("dépôt Git source introuvable")
    if _git(source, "rev-parse", "--is-shallow-repository") != "false":
        raise CustodyError("historique shallow : archive incomplète")
    if _git(source, "cat-file", "-t", sha) != "commit":
        raise CustodyError("référence source non commit")
    return _git(source, "rev-parse", f"{sha}^{{tree}}")


def _bundle_plaintext(source: Path, sha: str, root: Path) -> bytes:
    proof = root / "proof"
    bundle_path = root / "archive.bundle"
    _git(root, "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(source), str(proof))
    _git(proof, "update-ref", LOCAL_REF, sha)
    _git(proof, "bundle", "create", str(bundle_path), LOCAL_REF)
    _git(proof, "bundle", "verify", str(bundle_path))
    if not 0 < bundle_path.stat().st_size <= MAX_BUNDLE_BYTES:
        raise CustodyError("bundle hors limites : utiliser un dispositif de chiffrement streaming revu")
    return bundle_path.read_bytes()


def seal(source: Path, baseline_sha: str, output_directory: Path, key_file: Path, *, acknowledge_sensitive_history: bool = False) -> dict[str, Any]:
    """Produit uniquement dans un répertoire local privé un bundle chiffré.

    Aucun upload, aucun artefact GitHub et aucune décision G1 sont réalisés.
    """
    if not acknowledge_sensitive_history:
        raise CustodyError("consentement explicite requis : historique potentiellement sensible")
    source = source.resolve(strict=True)
    output = _private_directory(output_directory)
    key_path = _private_file(key_file)
    _outside(output, source, "coffre dans le dépôt Git interdit")
    _outside(key_path, source, "clé dans le dépôt Git interdite")
    _outside(key_path, output, "clé dans le coffre ciphertext interdite")
    if (output / CIPHERTEXT_NAME).exists() or (output / MANIFEST_NAME).exists():
        raise CustodyError("archive existante : écrasement interdit")
    key = _read_key(key_path)
    tree = _source_baseline(source, baseline_sha)
    with tempfile.TemporaryDirectory(prefix="pyprojectkit-g1-seal-") as dirname:
        payload = _bundle_plaintext(source, baseline_sha, Path(dirname))
        metadata = {
            "format": "pyprojectkit.g1.encrypted-bundle.v1",
            "algorithm": "AES-256-GCM",
            "legacy_commit": baseline_sha,
            "legacy_tree": tree,
            "bundle_sha256": _sha256(payload),
            "bundle_size_bytes": len(payload),
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "contains_full_github_metadata": False,
            "custody_status": "AWAITING_OFFSITE_AND_HUMAN_VERIFICATION",
        }
        nonce = secrets.token_bytes(12)
        encrypted = MAGIC + nonce + AESGCM(key).encrypt(nonce, payload, _json_bytes(metadata))
        manifest = {"metadata": metadata, "ciphertext_sha256": _sha256(encrypted), "ciphertext_size_bytes": len(encrypted)}
        ciphertext_path = output / CIPHERTEXT_NAME
        manifest_path = output / MANIFEST_NAME
        created_ciphertext = False
        try:
            _write_exclusive(ciphertext_path, encrypted)
            created_ciphertext = True
            _write_exclusive(manifest_path, json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n")
        except BaseException:
            # Un échec O_EXCL ne doit jamais effacer un fichier préexistant.
            if created_ciphertext:
                ciphertext_path.unlink(missing_ok=True)
            raise
    return {
        "status": "LOCAL_CIPHERTEXT_CREATED",
        "legacy_commit": baseline_sha,
        "ciphertext_sha256": manifest["ciphertext_sha256"],
        "ciphertext_size_bytes": len(encrypted),
        "independent_custody_verified": False,
        "g1_gate": "PENDING",
    }


def verify_encrypted_restore(archive_directory: Path, key_file: Path) -> dict[str, Any]:
    """Restaure depuis le ciphertext, vérifie Git et efface le clone temporaire.

    À exécuter sur un autre poste et depuis la copie hors machine pour prouver G1.
    """
    archive = _private_directory(archive_directory)
    key_path = _private_file(key_file)
    _outside(key_path, archive, "clé colocalisée avec l'archive interdite")
    data_path = _private_file(archive / CIPHERTEXT_NAME)
    manifest_path = _private_file(archive / MANIFEST_NAME)
    if manifest_path.stat().st_size > 32 * 1024:
        raise CustodyError("manifeste excessif")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata = manifest["metadata"]
        if (metadata["format"] != "pyprojectkit.g1.encrypted-bundle.v1" or metadata["algorithm"] != "AES-256-GCM"):
            raise ValueError("format")
        sha, tree = metadata["legacy_commit"], metadata["legacy_tree"]
        if not _canonical_sha(sha) or not _canonical_sha(tree):
            raise ValueError("sha")
        if (type(metadata["bundle_size_bytes"]) is not int
                or metadata["bundle_size_bytes"] > MAX_BUNDLE_BYTES
                or metadata["bundle_size_bytes"] <= 0):
            raise ValueError("size")
        if not isinstance(metadata["bundle_sha256"], str) or len(metadata["bundle_sha256"]) != 64:
            raise ValueError("hash")
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise CustodyError("manifeste d'archive invalide") from error
    if data_path.stat().st_size > MAX_BUNDLE_BYTES + len(MAGIC) + 12 + 16:
        raise CustodyError("ciphertext hors limite")
    encrypted = data_path.read_bytes()
    if _sha256(encrypted) != manifest.get("ciphertext_sha256") or len(encrypted) != manifest.get("ciphertext_size_bytes"):
        raise CustodyError("empreinte ou taille du ciphertext incorrecte")
    if not encrypted.startswith(MAGIC) or len(encrypted) < len(MAGIC) + 12 + 16:
        raise CustodyError("enveloppe chiffrée invalide")
    nonce = encrypted[len(MAGIC):len(MAGIC) + 12]
    try:
        raw = AESGCM(_read_key(key_path)).decrypt(nonce, encrypted[len(MAGIC) + 12:], _json_bytes(metadata))
    except (InvalidTag, ValueError) as error:
        raise CustodyError("échec de l'authenticité ou de la clé") from error
    if _sha256(raw) != metadata["bundle_sha256"] or len(raw) != metadata["bundle_size_bytes"]:
        raise CustodyError("bundle déchiffré incohérent")
    with tempfile.TemporaryDirectory(prefix="pyprojectkit-g1-restore-") as dirname:
        root = Path(dirname)
        bundle_file = root / "legacy.bundle"
        _write_exclusive(bundle_file, raw)
        restored = root / "restored"
        _git(root, "clone", "--quiet", "--no-checkout", "--branch", "g1-legacy-local-custody", str(bundle_file), str(restored))
        _git(restored, "fsck", "--full", "--no-reflogs")
        got_sha = _git(restored, "rev-parse", "HEAD")
        got_tree = _git(restored, "rev-parse", "HEAD^{tree}")
        if got_sha != sha or got_tree != tree:
            raise CustodyError("restauration non conforme à l'oracle")
    return {
        "status": "ENCRYPTED_ARCHIVE_RESTORE_VERIFIED",
        "legacy_commit": sha,
        "legacy_tree": tree,
        "ciphertext_sha256": manifest["ciphertext_sha256"],
        "restored_git_fsck": True,
        "independent_offsite_custody_verified": False,
        "g1_gate": "PENDING",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="G1 : chiffrement local et vérification depuis un coffre privé")
    subparsers = parser.add_subparsers(dest="command", required=True)
    make_key = subparsers.add_parser("generate-key", help="Générer une clé 32 octets dans un coffre séparé")
    make_key.add_argument("--key-file", required=True, type=Path)
    make_seal = subparsers.add_parser("seal", help="Créer une copie Git chiffrée dans un emplacement privé")
    make_seal.add_argument("--repository", type=Path, required=True)
    make_seal.add_argument("--baseline-sha", default=DEFAULT_LEGACY_SHA)
    make_seal.add_argument("--output-dir", type=Path, required=True)
    make_seal.add_argument("--key-file", type=Path, required=True)
    make_seal.add_argument("--acknowledge-sensitive-history", action="store_true", required=True)
    make_verify = subparsers.add_parser("verify", help="Vérifier et restaurer sans extraction persistante")
    make_verify.add_argument("--archive-dir", type=Path, required=True)
    make_verify.add_argument("--key-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "generate-key":
            create_key(args.key_file)
            report = {"status": "KEY_GENERATED_LOCAL_ONLY", "key_published": False, "g1_gate": "PENDING"}
        elif args.command == "seal":
            report = seal(args.repository, args.baseline_sha, args.output_dir, args.key_file,
                          acknowledge_sensitive_history=args.acknowledge_sensitive_history)
        else:
            report = verify_encrypted_restore(args.archive_dir, args.key_file)
    except (CustodyError, OSError) as error:
        parser.exit(2, f"G1 STOP : {error}\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
