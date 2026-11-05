"""Tests isolés du contrôle G1. Aucun commit du dépôt PyProjectKit n'est modifié."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.g1_legacy_restore_drill import RestoreDrillError, verify_legacy_restoration


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def synthetic_repository(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "source-repo"
    repo.mkdir()
    git(repo, "init", "--quiet", "-b", "main")
    git(repo, "config", "user.name", "Synthetic Test")
    git(repo, "config", "user.email", "synthetic@example.invalid")
    (repo / "synthetic.txt").write_text("legacy synthetic fixture", encoding="utf-8")
    git(repo, "add", "synthetic.txt")
    git(repo, "commit", "--quiet", "-m", "legacy reference")
    legacy = git(repo, "rev-parse", "HEAD")
    (repo / "synthetic.txt").write_text("post-legacy mutation", encoding="utf-8")
    git(repo, "commit", "--quiet", "-am", "later commit")
    return repo, legacy


def test_g1_restore_drill_roundtrip_without_persisting_bundle(synthetic_repository: tuple[Path, str]) -> None:
    repo, baseline = synthetic_repository
    current = git(repo, "rev-parse", "HEAD")
    report = verify_legacy_restoration(repo, baseline)
    assert report["legacy_commit"] == baseline
    assert report["legacy_commit"] != current
    assert report["isolated_clone_verified"] is True
    assert report["git_fsck_verified"] is True
    assert report["bundle_size_bytes"] > 0
    assert len(report["bundle_sha256"]) == 64
    assert report["bundle_retained"] is False
    assert report["g1_gate"] == "PENDING"
    assert git(repo, "rev-parse", "HEAD") == current
    assert not (repo / ".git" / "refs" / "heads" / "g1-legacy-local-proof").exists()
    assert not (repo / "legacy.bundle").exists()


def test_g1_rejects_missing_legacy_commit(synthetic_repository: tuple[Path, str]) -> None:
    repo, _ = synthetic_repository
    with pytest.raises(RestoreDrillError, match="référence historique"):
        verify_legacy_restoration(repo, "a" * 40)


def test_g1_rejects_invalid_sha(synthetic_repository: tuple[Path, str]) -> None:
    repo, _ = synthetic_repository
    with pytest.raises(RestoreDrillError, match="SHA legacy non canonique"):
        verify_legacy_restoration(repo, "invalide")


def test_g1_rejects_shallow_repository(synthetic_repository: tuple[Path, str], tmp_path: Path) -> None:
    repo, baseline = synthetic_repository
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "--quiet", "--depth", "1", f"file://{repo}", str(shallow)], check=True)
    with pytest.raises(RestoreDrillError, match="clone superficiel"):
        verify_legacy_restoration(shallow, baseline)
