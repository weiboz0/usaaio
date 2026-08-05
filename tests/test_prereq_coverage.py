from pathlib import Path

from tools.checks.coverage import check_coverage
from tools.checks.prereq import check_prereq

ROOT = Path(__file__).resolve().parents[1]


def write_syllabus(root: Path, unit_extra: str = "", units_extra: str = "") -> None:
    root.joinpath("syllabus.md").write_text(
        f"""
<!-- syllabus-canonical -->
```yaml
syllabus_version: 1
baseline:
  math: [algebra]
  python: [variables-and-types]
clusters: [c]
concepts:
  - {{id: a, cluster: c}}
  - {{id: b, cluster: c}}
units:
  - id: U1
    track: foundation
    title: One
    prereqs: []
    teaches: [a]
    {unit_extra}
  - id: U2
    track: core
    title: Two
    prereqs: [U1]
    teaches: [b]
{units_extra}
```
"""
    )


def write_unit(
    root: Path,
    unit: str = "U2",
    taught: str = "b",
    used: str = "a",
    practice_count: int = 3,
) -> Path:
    unit_dir = root / "units" / unit
    (unit_dir / "practice").mkdir(parents=True)
    for number in range(1, practice_count + 1):
        (unit_dir / "practice" / f"p{number:02}.ipynb").write_text("{}")
        (unit_dir / "practice" / f"p{number:02}_solution.ipynb").write_text("{}")
    practice = "\n".join(
        f"""  - id: p{number:02}
    concepts: [{taught}]
    path: practice/p{number:02}.ipynb
    solution_path: practice/p{number:02}_solution.ipynb"""
        for number in range(1, practice_count + 1)
    )
    (unit_dir / "manifest.yaml").write_text(
        f"""
unit: {unit}
concepts_taught: [{taught}]
concepts_used: [{used}]
prereq_units: [U1]
practice:
{practice}
"""
    )
    return unit_dir


def test_prereq_pass_on_real_syllabus():
    report = check_prereq(ROOT)
    assert report.ok
    assert report.errors == []


def test_prereq_detects_cycle(tmp_path):
    write_syllabus(tmp_path, units_extra="  - id: U3\n    track: core\n    title: Three\n    prereqs: [U3]\n    teaches: []\n")
    report = check_prereq(tmp_path)
    assert not report.ok
    assert any("cycle detected" in error for error in report.errors)


def test_prereq_detects_untaught_use(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path, used="b")
    report = check_prereq(tmp_path)
    assert not report.ok
    assert any("uses untaught concept b" in error for error in report.errors)


def test_prereq_detects_manifest_syllabus_drift(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path, taught="a")
    report = check_prereq(tmp_path)
    assert not report.ok
    assert any("concepts_taught drift" in error for error in report.errors)


def test_mock_tested_only_if_taught(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path)
    test_dir = tmp_path / "mocktests" / "r1-001"
    test_dir.mkdir(parents=True)
    (test_dir / "manifest.yaml").write_text(
        """
test: r1-001
blueprint_version: 1
duration_minutes: 180
total_points: 300
time_budget: {}
problems:
  - id: p01
    section: s
    units: [U1]
    concepts: [b]
    points: 1
    difficulty: intro
    type: theory
    answer_form: short
    provenance: original
    spec: x
    answer_key: x
"""
    )
    report = check_prereq(tmp_path)
    assert not report.ok
    assert any("tests untaught concept b" in error for error in report.errors)


def test_coverage_pass_and_gap(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path)
    assert check_coverage(tmp_path).ok
    (tmp_path / "units" / "U2" / "manifest.yaml").write_text(
        """
unit: U2
concepts_taught: [b]
concepts_used: [a]
prereq_units: [U1]
practice:
  - id: p01
    concepts: [a]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
"""
    )
    report = check_coverage(tmp_path)
    assert not report.ok
    assert any("without practice" in error for error in report.errors)


def test_coverage_missing_practice_file(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path)
    (tmp_path / "units" / "U2" / "practice" / "p01.ipynb").unlink()
    report = check_coverage(tmp_path)
    assert not report.ok
    assert any("missing practice path" in error for error in report.errors)


def test_coverage_requires_three_tagged_problems_per_taught_concept(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path, practice_count=2)

    report = check_coverage(tmp_path)

    assert not report.ok
    assert any(
        "taught concept b has 2 tagged practice problems; requires at least 3" in error
        for error in report.errors
    )


def test_coverage_does_not_count_duplicate_problem_ids(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path, practice_count=1)
    (tmp_path / "units" / "U2" / "manifest.yaml").write_text(
        """
unit: U2
concepts_taught: [b]
concepts_used: [a]
prereq_units: [U1]
practice:
  - &duplicate
    id: p01
    concepts: [b]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
  - *duplicate
  - *duplicate
"""
    )

    report = check_coverage(tmp_path)

    assert not report.ok
    assert any(
        "taught concept b has 1 tagged practice problems; requires at least 3" in error
        for error in report.errors
    )


def test_coverage_does_not_count_duplicate_problem_paths(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path, practice_count=1)
    (tmp_path / "units" / "U2" / "manifest.yaml").write_text(
        """
unit: U2
concepts_taught: [b]
concepts_used: [a]
prereq_units: [U1]
practice:
  - id: p01
    concepts: [b]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
  - id: p02
    concepts: [b]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
  - id: p03
    concepts: [b]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
"""
    )

    report = check_coverage(tmp_path)

    assert not report.ok
    assert any(
        "taught concept b has 1 tagged practice problems; requires at least 3" in error
        for error in report.errors
    )
