"""Tests synthétiques: aucun secret réel n'est utilisé ou imprimé."""
from __future__ import annotations

import json
import stat
import subprocess
from pathlib import Path

import pytest

from scripts.g1_history_secret_preflight import HistoryAuditError, scan_history, write_private_report


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init", "--quiet", "-b", "main")
    git(root, "config", "user.name", "Synthetic Fixture")
    git(root, "config", "user.email", "synthetic@example.invalid")
    (root / "example.txt").write_text("synthétique sans secret", encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    return root, git(root, "rev-parse", "HEAD")


def commit(repo: Path, filename: str, content: str, *, message: str = "synthetic change") -> str:
    (repo / filename).write_text(content, encoding="utf-8")
    git(repo, "add", filename)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def test_clean_fixture_does_not_certify_cleanliness(repo: tuple[Path, str]) -> None:
    root, baseline = repo
    result = scan_history(root, baseline)
    assert result["status"] == "NO_PATTERN_HITS_NOT_A_CLEAN_BILL"
    assert result["pattern_hits_total"] == 0
    assert result["manual_security_review_required"] is True
    assert result["history_clean_certified"] is False
    assert result["g1_gate"] == "PENDING"
    assert result["commits_scanned"] == 1


def test_detects_removed_historical_token_without_disclosing_value(repo: tuple[Path, str]) -> None:
    root, _ = repo
    marker = "ghp_" + "A" * 40
    commit(root, "temporary.txt", marker)
    sha = commit(root, "temporary.txt", "obsolete value removed")
    result = scan_history(root, sha)
    assert result["pattern_hit_counts"]["github_token"] >= 1
    assert marker not in json.dumps(result)
    assert "temporary.txt" not in json.dumps(result)


def test_detects_private_key_header(repo: tuple[Path, str]) -> None:
    root, _ = repo
    sha = commit(root, "private.txt", "-----BEGIN PRIVATE KEY-----\nsynthetic\n-----END PRIVATE KEY-----\n")
    assert scan_history(root, sha)["pattern_hit_counts"]["pem_private_key"] >= 1


def test_detects_aws_pattern(repo: tuple[Path, str]) -> None:
    root, _ = repo
    sha = commit(root, "aws.txt", "AKIA" + "B" * 16)
    assert scan_history(root, sha)["pattern_hit_counts"]["aws_access_key_id"] >= 1


def test_detects_in_commit_message(repo: tuple[Path, str]) -> None:
    root, _ = repo
    sha = commit(root, "msg.txt", "safe", message="sk-" + "Z" * 35)
    assert scan_history(root, sha)["pattern_hit_counts"]["openai_api_key"] >= 1


def test_detects_assignment(repo: tuple[Path, str]) -> None:
    root, _ = repo
    sha = commit(root, "env.txt", "ACCESS_TOKEN = '" + "Y" * 32 + "'\n")
    assert scan_history(root, sha)["pattern_hit_counts"]["sensitive_assignment"] >= 1


def test_reject_invalid_baseline(repo: tuple[Path, str]) -> None:
    root, _ = repo
    with pytest.raises(HistoryAuditError, match="SHA non canonique"):
        scan_history(root, "invalid")


def test_missing_baseline_fails_closed(repo: tuple[Path, str]) -> None:
    root, _ = repo
    with pytest.raises(HistoryAuditError, match="Git non vérifiable"):
        scan_history(root, "a" * 40)


def test_shallow_clone_is_rejected(repo: tuple[Path, str], tmp_path: Path) -> None:
    root, sha = repo
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{root}", str(shallow)], check=True)
    with pytest.raises(HistoryAuditError, match="superficiel"):
        scan_history(shallow, sha)


def test_oversized_object_requires_review(repo: tuple[Path, str]) -> None:
    root, _ = repo
    sha = commit(root, "huge.bin", "A" * 200)
    result = scan_history(root, sha, max_object_bytes=100)
    assert result["oversized_objects_not_scanned"] >= 1
    assert result["history_clean_certified"] is False


def test_total_bytes_limit_fails_closed(repo: tuple[Path, str]) -> None:
    root, sha = repo
    with pytest.raises(HistoryAuditError, match="quota"):
        scan_history(root, sha, max_total_bytes=1)


def test_object_count_limit_fails_closed(repo: tuple[Path, str]) -> None:
    root, sha = repo
    with pytest.raises(HistoryAuditError, match="limite du nombre"):
        scan_history(root, sha, max_objects=1)


def test_private_report_is_redacted_and_mode_0600(repo: tuple[Path, str], tmp_path: Path) -> None:
    root, sha = repo
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    path = folder / "result.json"
    write_private_report(scan_history(root, sha), path, root)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert json.loads(path.read_text())["g1_gate"] == "PENDING"
    assert "example.txt" not in path.read_text()


def test_refuse_write_report_into_git_tree(repo: tuple[Path, str]) -> None:
    root, sha = repo
    d = root / "reports"
    d.mkdir(mode=0o700)
    with pytest.raises(HistoryAuditError, match="dans dépôt Git"):
        write_private_report(scan_history(root, sha), d / "report.json", root)


def test_refuse_existing_report(repo: tuple[Path, str], tmp_path: Path) -> None:
    root, sha = repo
    d = tmp_path / "private"
    d.mkdir(mode=0o700)
    f = d / "existing.json"
    f.write_text("existing")
    with pytest.raises(HistoryAuditError, match="déjà utilisée"):
        write_private_report(scan_history(root, sha), f, root)
    assert f.read_text() == "existing"


def test_refuse_symlink_destination(repo: tuple[Path, str], tmp_path: Path) -> None:
    root, sha = repo
    d = tmp_path / "private"
    d.mkdir(mode=0o700)
    target = d / "target"
    link = d / "pointer"
    link.symlink_to(target)
    with pytest.raises(HistoryAuditError, match="symbolique"):
        write_private_report(scan_history(root, sha), link, root)


def test_report_parent_must_be_private(repo: tuple[Path, str], tmp_path: Path) -> None:
    root, sha = repo
    folder = tmp_path / "public"
    folder.mkdir(mode=0o755)
    with pytest.raises(HistoryAuditError, match="0700"):
        write_private_report(scan_history(root, sha), folder / "result.json", root)
