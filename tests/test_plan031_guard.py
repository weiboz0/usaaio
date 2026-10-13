"""Plan 031: pre-merge-guard unit-collision logic with NN- teaching-order prefixes."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _fake_uv_environment(tmp_path: Path) -> dict[str, str]:
    executable = tmp_path / "bin" / "uv"
    executable.parent.mkdir()
    executable.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "[[ $1 == run ]]\n"
        "shift\n"
        "[[ $1 == python ]]\n"
        "shift\n"
        'exec "$TEST_PYTHON" "$@"\n'
    )
    executable.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{executable.parent}:{env['PATH']}"
    env["TEST_PYTHON"] = sys.executable
    return env


def _install_pre_merge_enforcement(repo: Path) -> None:
    for relative in (
        "scripts/pre-merge-guard.sh",
        "scripts/verify-staged-scope.py",
        "scripts/renumber-book1-units.py",
        "tests/fixtures/plan019-path-inventory.yaml",
    ):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    (repo / "scripts/pre-merge-guard.sh").chmod(0o755)
    (repo / "scripts/verify-staged-scope.py").chmod(0o755)


def _plan031_guard_repo(tmp_path: Path, main_units: tuple[str, ...]) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _install_pre_merge_enforcement(repo)
    (repo / "books.yaml").write_text("books_version: 1\n")
    for name in main_units:
        directory = repo / "book1" / "units" / name
        directory.mkdir(parents=True)
        directory.joinpath("manifest.yaml").write_text(
            f"unit: {name}\nsessions: 3\npractice: [{name}-a, {name}-b, {name}-c]\n"
        )
        directory.joinpath("lesson.ipynb").write_text(f'{{"unit": "{name}", "cells": []}}\n')
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    _git(tmp_path, "init", "--bare", str(remote))
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "checkout", "-b", "feature")
    return repo, remote


def _guard_pr(repo: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh", "--pr"],
        cwd=repo,
        env=_fake_uv_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )


def test_pre_merge_guard_accepts_plan031_mixed_layout_rename_union(tmp_path: Path) -> None:
    """origin/main F3-matrices is the rename source of 04-F4-matrices: not a collision."""
    repo, _ = _plan031_guard_repo(tmp_path, ("F3-matrices", "F4-multivar-calculus"))
    _git(repo, "mv", "book1/units/F3-matrices", "book1/units/04-F4-matrices")
    _git(repo, "mv", "book1/units/F4-multivar-calculus", "book1/units/03-F3-multivar-calculus")
    _git(repo, "commit", "-m", "renumber")

    proc = _guard_pr(repo, tmp_path)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "pre-merge-guard: OK" in proc.stdout


def test_pre_merge_guard_rejects_genuine_prefixed_code_collision(tmp_path: Path) -> None:
    """Two different F3 units still collide once the NN- prefix is stripped."""
    repo, _ = _plan031_guard_repo(tmp_path, ("F3-matrices",))
    directory = repo / "book1" / "units" / "03-F3-multivar-calculus"
    directory.mkdir(parents=True)
    directory.joinpath("manifest.yaml").write_text("unit: F3-multivar-calculus\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "second F3")

    proc = _guard_pr(repo, tmp_path)

    assert proc.returncode == 1
    assert "duplicate book1/units number(s): F3" in proc.stdout


def test_pre_merge_guard_rejects_duplicate_teaching_order_prefix(tmp_path: Path) -> None:
    repo, _ = _plan031_guard_repo(tmp_path, ())
    for name in ("05-F5-probability", "05-C1-ml-fundamentals"):
        directory = repo / "book1" / "units" / name
        directory.mkdir(parents=True)
        directory.joinpath("manifest.yaml").write_text("unit: x\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "two 05 prefixes")

    proc = _guard_pr(repo, tmp_path)

    assert proc.returncode == 1
    assert "duplicate book1/units teaching-order prefix number(s): 05" in proc.stdout
