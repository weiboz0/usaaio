from pathlib import Path

from tools.checks.coverage import check_coverage
from tools.checks.prereq import check_prereq

ROOT = Path(__file__).resolve().parents[1]


def write_syllabus(
    root: Path,
    unit_extra: str = "",
    units_extra: str = "",
    second_unit: str = "U2",
    second_length: str | None = None,
) -> None:
    length_line = f"    length: {second_length}\n" if second_length else ""
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
  - id: {second_unit}
    track: core
    title: Two
{length_line}\
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
    prereq_units: str = "U1",
    practice_concept: str | None = None,
    practice_count: int = 3,
    lesson_sessions: list[int] | None = None,
) -> Path:
    unit_dir = root / "units" / unit
    (unit_dir / "practice").mkdir(parents=True)
    for number in range(1, practice_count + 1):
        (unit_dir / "practice" / f"p{number:02}.ipynb").write_text("{}")
        (unit_dir / "practice" / f"p{number:02}_solution.ipynb").write_text("{}")
    practice = "\n".join(
        f"""  - id: p{number:02}
    concepts: [{practice_concept or taught}]
    path: practice/p{number:02}.ipynb
    solution_path: practice/p{number:02}_solution.ipynb"""
        for number in range(1, practice_count + 1)
    )
    estimated_minutes = ""
    if lesson_sessions is not None:
        session_values = ", ".join(str(value) for value in lesson_sessions)
        estimated_minutes = (
            "estimated_minutes:\n"
            f"  lesson_sessions: [{session_values}]\n"
        )
    (unit_dir / "manifest.yaml").write_text(
        f"""
unit: {unit}
concepts_taught: [{taught}]
concepts_used: [{used}]
prereq_units: [{prereq_units}]
{estimated_minutes}\
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


def test_unit_practice_allows_foreign_tag_from_prereq_unit(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path, practice_concept="a")

    report = check_prereq(tmp_path)

    assert report.ok
    assert report.errors == []


def test_unit_practice_rejects_tag_from_later_unit(tmp_path):
    write_syllabus(tmp_path)
    unit_dir = write_unit(
        tmp_path,
        unit="U1",
        taught="a",
        used="",
        prereq_units="",
        practice_concept="b",
    )

    report = check_prereq(tmp_path)

    assert not report.ok
    assert (
        f"{unit_dir / 'manifest.yaml'}: practice problem p01 tags concept b owned by unit U2; "
        "not taught by unit U1 or its prerequisites"
    ) in report.errors


def test_unit_practice_allows_same_unit_tag(tmp_path):
    write_syllabus(tmp_path)
    write_unit(tmp_path)

    report = check_prereq(tmp_path)

    assert report.ok
    assert report.errors == []


def test_unit_practice_foreign_tag_must_be_declared_in_concepts_used(tmp_path):
    write_syllabus(tmp_path)
    unit_dir = write_unit(tmp_path, used="", practice_concept="a")

    report = check_prereq(tmp_path)

    assert not report.ok
    assert (
        f"{unit_dir / 'manifest.yaml'}: practice problem p01 tags foreign concept a "
        "missing from concepts_used"
    ) in report.errors


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


def test_double_length_coverage_requires_lesson_sessions(tmp_path):
    write_syllabus(tmp_path, second_length="double")
    unit_dir = write_unit(tmp_path, practice_count=24)

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{unit_dir / 'manifest.yaml'}: double-length unit U2 has 0 lesson sessions "
        "(missing estimated_minutes.lesson_sessions); requires 4-6"
    ) in report.errors


def test_double_length_coverage_rejects_lesson_count_below_band(tmp_path):
    write_syllabus(tmp_path, second_length="double")
    unit_dir = write_unit(tmp_path, practice_count=24, lesson_sessions=[85] * 3)

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{unit_dir / 'manifest.yaml'}: double-length unit U2 has 3 lesson sessions; "
        "requires 4-6"
    ) in report.errors


def test_double_length_coverage_rejects_lesson_count_above_band(tmp_path):
    write_syllabus(tmp_path, second_length="double")
    unit_dir = write_unit(tmp_path, practice_count=24, lesson_sessions=[60] * 7)

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{unit_dir / 'manifest.yaml'}: double-length unit U2 has 7 lesson sessions; "
        "requires 4-6"
    ) in report.errors


def test_double_length_coverage_rejects_practice_count_below_band(tmp_path):
    write_syllabus(tmp_path, second_length="double")
    unit_dir = write_unit(tmp_path, practice_count=23, lesson_sessions=[85] * 4)

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{unit_dir / 'manifest.yaml'}: double-length unit U2 has 23 distinct practice ids; "
        "requires 24-30"
    ) in report.errors
    assert (
        f"{unit_dir / 'manifest.yaml'}: double-length unit U2 has 23 distinct practice paths; "
        "requires 24-30"
    ) in report.errors


def test_double_length_coverage_rejects_practice_count_above_band(tmp_path):
    write_syllabus(tmp_path, second_length="double")
    unit_dir = write_unit(tmp_path, practice_count=31, lesson_sessions=[85] * 6)

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{unit_dir / 'manifest.yaml'}: double-length unit U2 has 31 distinct practice ids; "
        "requires 24-30"
    ) in report.errors
    assert (
        f"{unit_dir / 'manifest.yaml'}: double-length unit U2 has 31 distinct practice paths; "
        "requires 24-30"
    ) in report.errors


def test_double_length_coverage_counts_distinct_practice_ids_and_paths(tmp_path):
    write_syllabus(tmp_path, second_length="double")
    unit_dir = write_unit(tmp_path, practice_count=24, lesson_sessions=[85] * 4)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_text = manifest_path.read_text()
    manifest_text = manifest_text.replace("id: p24", "id: p23")
    manifest_text = manifest_text.replace(
        "path: practice/p24.ipynb", "path: practice/p23.ipynb"
    )
    manifest_path.write_text(manifest_text)

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{manifest_path}: double-length unit U2 has 23 distinct practice ids; "
        "requires 24-30"
    ) in report.errors
    assert (
        f"{manifest_path}: double-length unit U2 has 23 distinct practice paths; "
        "requires 24-30"
    ) in report.errors


def test_double_length_coverage_accepts_compliant_unit(tmp_path):
    write_syllabus(tmp_path, second_length="double")
    write_unit(tmp_path, practice_count=24, lesson_sessions=[85] * 4)

    report = check_coverage(tmp_path)

    assert report.ok
    assert report.errors == []


def test_double_length_coverage_real_f6_passes():
    report = check_coverage(ROOT)

    assert not any("double-length unit F6-svd-spectral" in error for error in report.errors)


def test_normal_length_planned_f5_shape_passes(tmp_path):
    write_syllabus(tmp_path, second_unit="F5-probability")
    write_unit(
        tmp_path,
        unit="F5-probability",
        practice_count=19,
        lesson_sessions=[80, 85, 85],
    )

    report = check_coverage(tmp_path)

    assert report.ok
    assert report.errors == []


def test_hypothetical_double_length_c7_rejects_three_sessions(tmp_path):
    write_syllabus(
        tmp_path,
        second_unit="C7-cnn-transfer",
        second_length="double",
    )
    unit_dir = write_unit(
        tmp_path,
        unit="C7-cnn-transfer",
        practice_count=27,
        lesson_sessions=[85, 85, 85],
    )

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{unit_dir / 'manifest.yaml'}: double-length unit C7-cnn-transfer has 3 lesson "
        "sessions; requires 4-6"
    ) in report.errors


def test_normal_length_c7_overflow_behavior_is_unchanged(tmp_path):
    write_syllabus(tmp_path, second_unit="C7-cnn-transfer")
    write_unit(
        tmp_path,
        unit="C7-cnn-transfer",
        practice_count=27,
        lesson_sessions=[85, 85, 85],
    )

    report = check_coverage(tmp_path)

    assert report.ok
    assert not any("double-length unit C7-cnn-transfer" in error for error in report.errors)
