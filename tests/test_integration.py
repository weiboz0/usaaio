from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

from tools.checks.blueprint import check_blueprint
from tools.checks.coverage import check_coverage
from tools.checks.hygiene import check_hygiene
from tools.checks.new_mocktest import scaffold_mocktest
from tools.checks.overlap import check_overlap
from tools.checks.prereq import check_prereq

ROOT = Path(__file__).resolve().parents[1]


def seed_repo(root: Path) -> None:
    (root / "mocktests").mkdir(parents=True)
    (root / "mocktests" / "blueprint.yaml").write_text((ROOT / "mocktests" / "blueprint.yaml").read_text())
    (root / "syllabus.md").write_text((ROOT / "syllabus.md").read_text())


def test_ci_checks_green_on_current_repo():
    reports = [
        check_prereq(ROOT),
        check_coverage(ROOT),
        check_hygiene(ROOT),
        check_blueprint(ROOT),
        check_overlap(ROOT),
    ]
    for report in reports:
        assert not report.errors
        assert report.ok
        if report.name == "overlap-scan":
            assert report.skipped is None


def test_cli_exit_codes(tmp_path):
    seed_repo(tmp_path)
    ok = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(tmp_path), "prereq-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0
    fail_root = tmp_path / "fail"
    seed_repo(fail_root)
    manifest = fail_root / "mocktests" / "r1-001"
    manifest.mkdir(parents=True)
    manifest.joinpath("manifest.yaml").write_text(
        """
test: r1-001
blueprint_version: 1
duration_minutes: 180
total_points: 300
time_budget: {}
problems:
  - id: p01
    section: concept-block
    units: [F1-scientific-python]
    concepts: [vectors-and-norms]
    cluster: linear-algebra
    points: 1
    difficulty: intro
    type: theory
    answer_form: short
    provenance: original
    spec: x
    answer_key: x
"""
    )
    fail = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(fail_root), "prereq-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert fail.returncode == 1
    skip_root = tmp_path / "skip"
    seed_repo(skip_root)
    scaffold_mocktest(skip_root, "r1-001", "2026-08-15")
    skipped = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(skip_root), "blueprint-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert skipped.returncode == 3


def test_full_pipeline_on_synthetic_test(tmp_path):
    seed_repo(tmp_path)
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    (unit_dir / "practice").mkdir(parents=True)
    for number in range(1, 4):
        (unit_dir / "practice" / f"p{number:02}.ipynb").write_text(
            '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}'
        )
        (unit_dir / "practice" / f"p{number:02}_solution.ipynb").write_text("{}")
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F1-scientific-python
concepts_taught: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics]
concepts_used: [variables-and-types]
prereq_units: []
practice:
  - id: p01
    concepts: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
  - id: p02
    concepts: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics]
    path: practice/p02.ipynb
    solution_path: practice/p02_solution.ipynb
  - id: p03
    concepts: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics]
    path: practice/p03.ipynb
    solution_path: practice/p03_solution.ipynb
"""
    )
    scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")
    assert check_prereq(tmp_path).ok
    assert check_coverage(tmp_path).ok
    assert check_hygiene(tmp_path).ok
    report = check_blueprint(tmp_path)
    assert report.skipped
    assert report.warnings


def test_ci_flags_draft_manifest_loudly(tmp_path):
    seed_repo(tmp_path)
    scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")
    proc = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(tmp_path), "blueprint-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 3
    assert "DRAFT manifest" in proc.stdout


def test_scope_cli_is_registered_and_loader_errors_are_blocking(tmp_path):
    seed_repo(tmp_path)

    proc = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(tmp_path), "scope-check"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "curriculum/sources.yaml" in proc.stderr
    assert "invalid choice" not in proc.stderr


def test_ci_local_wires_inventory_scope_and_generated_document_checks():
    script = (ROOT / "scripts" / "ci-local.sh").read_text()

    assert "python -m tools.audit_curriculum --check" in script
    assert 'usaaio-tools "$c"' in script
    assert "scope-check" in script
    assert "python -m tools.render_curriculum_roadmap --check" in script


def test_pre_merge_guard_runs_embedded_yaml_with_uv_python():
    script = (ROOT / "scripts" / "pre-merge-guard.sh").read_text()

    assert "uv run python -" in script
    assert "python3 -" not in script


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


def _roadmap(destination: str | None, planned_id: str | None) -> str:
    return yaml.safe_dump(
        {
            "roadmap_version": 1,
            "layers": [],
            "planned_units": (
                [{"id": planned_id, "knowledge_points": ["topic-a"]}] if planned_id else []
            ),
            "knowledge_points": (
                [{"id": "topic-a", "destination": destination}] if destination else []
            ),
        },
        sort_keys=False,
    )


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


def test_pre_merge_guard_pr_mode_fails_when_origin_main_is_unavailable(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    script = repo / "scripts" / "pre-merge-guard.sh"
    script.parent.mkdir()
    script.write_bytes((ROOT / "scripts" / "pre-merge-guard.sh").read_bytes())
    script.chmod(0o755)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh", "--pr"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "origin/main" in proc.stderr
    assert "unverified" in proc.stderr


def test_pre_merge_guard_rejects_parallel_roadmap_ownership_collisions(tmp_path):
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    other = tmp_path / "other"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    script = repo / "scripts" / "pre-merge-guard.sh"
    script.parent.mkdir()
    script.write_bytes((ROOT / "scripts" / "pre-merge-guard.sh").read_bytes())
    script.chmod(0o755)
    coverage = repo / "curriculum" / "coverage-map.yaml"
    coverage.parent.mkdir()
    coverage.write_text(_roadmap(None, None))
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    _git(tmp_path, "init", "--bare", str(remote))
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "checkout", "-b", "feature")
    coverage.write_text(_roadmap("U-feature", "P-collision"))

    _git(tmp_path, "clone", "-b", "main", str(remote), str(other))
    _git(other, "config", "user.email", "test@example.com")
    _git(other, "config", "user.name", "Test")
    other.joinpath("curriculum", "coverage-map.yaml").write_text(
        _roadmap("U-main", "P-collision")
    )
    _git(other, "add", ".")
    _git(other, "commit", "-m", "parallel roadmap")
    _git(other, "push", "origin", "main")

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh", "--pr"],
        cwd=repo,
        env=_fake_uv_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "roadmap knowledge-point ownership collision: topic-a" in proc.stdout
    assert "roadmap planned-unit ownership collision: P-collision" in proc.stdout
