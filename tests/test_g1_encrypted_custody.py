"""Tests crypto réels sur dépôt Git purement synthétique, aucune archive PyProjectKit exportée."""
from __future__ import annotations

import json
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from scripts.g1_encrypted_custody import (
    CIPHERTEXT_NAME, MANIFEST_NAME, CustodyError, create_key, seal, verify_encrypted_restore,
)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True).stdout.strip()


@pytest.fixture
def vaults(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "user.name", "Fixture")
    (repo / "test-data.txt").write_text("synthetic history only: DEMO_MARKER_XYC5", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "synthetic baseline")
    baseline = git(repo, "rev-parse", "HEAD")
    (repo / "test-data.txt").write_text("synthetic future", encoding="utf-8")
    git(repo, "commit", "-am", "future")
    key_dir = tmp_path / "key-custody"
    key_dir.mkdir(mode=0o700)
    key_file = key_dir / "key.bin"
    create_key(key_file)
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir(mode=0o700)
    return repo, archive_dir, key_file, baseline


def prepared(vaults: tuple[Path, Path, Path, str]) -> tuple[Path, Path, Path, str]:
    repo, archive_dir, key_file, baseline = vaults
    seal(repo, baseline, archive_dir, key_file, acknowledge_sensitive_history=True)
    return repo, archive_dir, key_file, baseline


def test_roundtrip_crypto_and_git_isolated(vaults: tuple[Path, Path, Path, str]) -> None:
    repo, archive, key, sha = prepared(vaults)
    assert git(repo, "rev-parse", "HEAD") != sha
    assert stat.S_IMODE((archive / CIPHERTEXT_NAME).stat().st_mode) == 0o600
    ciphertext = (archive / CIPHERTEXT_NAME).read_bytes()
    assert b"DEMO_MARKER_XYC5" not in ciphertext
    report = verify_encrypted_restore(archive, key)
    assert report["legacy_commit"] == sha
    assert report["restored_git_fsck"] is True
    assert report["g1_gate"] == "PENDING"
    assert not (archive / "legacy.bundle").exists()
    assert git(repo, "rev-parse", "HEAD") != sha


def test_independent_copy_restore(vaults: tuple[Path, Path, Path, str], tmp_path: Path) -> None:
    _, archive, key, sha = prepared(vaults)
    offsite = tmp_path / "offsite-copy"
    offsite.mkdir(mode=0o700)
    shutil.copy2(archive / CIPHERTEXT_NAME, offsite / CIPHERTEXT_NAME)
    shutil.copy2(archive / MANIFEST_NAME, offsite / MANIFEST_NAME)
    assert verify_encrypted_restore(offsite, key)["legacy_commit"] == sha


def test_tampered_ciphertext_is_rejected(vaults: tuple[Path, Path, Path, str]) -> None:
    _, archive, key, _ = prepared(vaults)
    f = archive / CIPHERTEXT_NAME
    payload = bytearray(f.read_bytes())
    payload[-10] ^= 0x80
    f.write_bytes(payload)
    with pytest.raises(CustodyError, match="empreinte"):
        verify_encrypted_restore(archive, key)


def test_wrong_key_is_rejected(vaults: tuple[Path, Path, Path, str], tmp_path: Path) -> None:
    _, archive, _, _ = prepared(vaults)
    d = tmp_path / "wrong-key"
    d.mkdir(mode=0o700)
    other = d / "wrong.bin"
    create_key(other)
    with pytest.raises(CustodyError, match="authenticité"):
        verify_encrypted_restore(archive, other)


def test_manifest_tamper_is_rejected(vaults: tuple[Path, Path, Path, str]) -> None:
    _, archive, key, _ = prepared(vaults)
    manifest = archive / MANIFEST_NAME
    data = json.loads(manifest.read_text())
    data["metadata"]["created_utc"] = "1999-01-01T00:00:00Z"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CustodyError, match="authenticité"):
        verify_encrypted_restore(archive, key)


def test_seal_requires_explicit_ack(vaults: tuple[Path, Path, Path, str]) -> None:
    repo, archive, key, sha = vaults
    with pytest.raises(CustodyError, match="consentement"):
        seal(repo, sha, archive, key)
    assert not list(archive.iterdir())


def test_key_cannot_be_in_archive(vaults: tuple[Path, Path, Path, str]) -> None:
    repo, archive, _, sha = vaults
    key = archive / "unacceptable.key"
    create_key(key)
    with pytest.raises(CustodyError, match="colocalisée|coffre"):
        seal(repo, sha, archive, key, acknowledge_sensitive_history=True)


def test_destination_cannot_be_inside_repository(vaults: tuple[Path, Path, Path, str]) -> None:
    repo, _, key, sha = vaults
    unsafe = repo / "archive"
    unsafe.mkdir(mode=0o700)
    with pytest.raises(CustodyError, match="dans le dépôt"):
        seal(repo, sha, unsafe, key, acknowledge_sensitive_history=True)


def test_loosely_permissioned_key_rejected(vaults: tuple[Path, Path, Path, str]) -> None:
    repo, archive, key, sha = vaults
    key.chmod(0o644)
    with pytest.raises(CustodyError, match="permissions"):
        seal(repo, sha, archive, key, acknowledge_sensitive_history=True)


def test_does_not_overwrite_archives(vaults: tuple[Path, Path, Path, str]) -> None:
    repo, archive, key, sha = prepared(vaults)
    old = (archive / CIPHERTEXT_NAME).read_bytes()
    with pytest.raises(CustodyError, match="existante"):
        seal(repo, sha, archive, key, acknowledge_sensitive_history=True)
    assert (archive / CIPHERTEXT_NAME).read_bytes() == old


def test_invalid_sha_is_refused(vaults: tuple[Path, Path, Path, str]) -> None:
    repo, archive, key, _ = vaults
    with pytest.raises(CustodyError, match="non canonique"):
        seal(repo, "badsha", archive, key, acknowledge_sensitive_history=True)


def test_symlink_archive_rejected(vaults: tuple[Path, Path, Path, str], tmp_path: Path) -> None:
    repo, archive, key, sha = vaults
    link = tmp_path / "pointer"
    link.symlink_to(archive, target_is_directory=True)
    with pytest.raises(CustodyError, match="symbolique"):
        seal(repo, sha, link, key, acknowledge_sensitive_history=True)


def test_key_generation_does_not_overwrite(vaults: tuple[Path, Path, Path, str]) -> None:
    _, _, key, _ = vaults
    original = key.read_bytes()
    with pytest.raises(CustodyError, match="écrasement"):
        create_key(key)
    assert key.read_bytes() == original


def test_recomputed_ciphertext_hash_still_fails_authentication(vaults: tuple[Path, Path, Path, str]) -> None:
    _, archive, key, _ = prepared(vaults)
    content_path = archive / CIPHERTEXT_NAME
    content = bytearray(content_path.read_bytes())
    content[-1] ^= 0x01
    content_path.write_bytes(content)
    import hashlib
    manifest_path = archive / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["ciphertext_sha256"] = hashlib.sha256(content).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CustodyError, match="authenticité"):
        verify_encrypted_restore(archive, key)


def test_malformed_manifest_fails_closed(vaults: tuple[Path, Path, Path, str]) -> None:
    _, archive, key, _ = prepared(vaults)
    manifest_path = archive / MANIFEST_NAME
    data = json.loads(manifest_path.read_text())
    data["metadata"]["bundle_size_bytes"] = "not-an-integer"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CustodyError, match="manifeste"):
        verify_encrypted_restore(archive, key)


def test_key_generation_inside_nested_git_directory_denied(vaults: tuple[Path, Path, Path, str]) -> None:
    repo, _, _, _ = vaults
    nested = repo / "secrets"
    nested.mkdir(mode=0o700)
    with pytest.raises(CustodyError, match="dépôt Git"):
        create_key(nested / "key.bin")
    assert not (nested / "key.bin").exists()
