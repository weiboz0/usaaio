from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
