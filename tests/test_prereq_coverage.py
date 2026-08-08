import shutil
from pathlib import Path
from posixpath import normpath

import yaml

from tools.checks.coverage import check_coverage
from tools.checks.prereq import check_prereq
from tools.model import load_mock_manifests, load_syllabus, load_unit_manifests

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


def test_practice_minutes_are_all_or_none_within_a_manifest(tmp_path):
    write_syllabus(tmp_path)
    unit_dir = write_unit(tmp_path, practice_count=3)
    manifest_path = unit_dir / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["estimated_minutes"] = {"practice": 45}
    manifest["practice"][0]["minutes"] = 15
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{manifest_path}: practice minutes must be declared for every practice when any are present"
        in report.errors
    )


def test_practice_minutes_must_sum_to_estimated_practice_minutes(tmp_path):
    write_syllabus(tmp_path)
    unit_dir = write_unit(tmp_path, practice_count=3)
    manifest_path = unit_dir / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["estimated_minutes"] = {"practice": 50}
    for row in manifest["practice"]:
        row["minutes"] = 15
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{manifest_path}: practice minutes sum to 45; expected estimated_minutes.practice 50"
        in report.errors
    )


def test_complete_practice_minutes_matching_the_estimate_pass(tmp_path):
    write_syllabus(tmp_path)
    unit_dir = write_unit(tmp_path, practice_count=3)
    manifest_path = unit_dir / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["estimated_minutes"] = {"practice": 45}
    for row in manifest["practice"]:
        row["minutes"] = 15
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))

    report = check_coverage(tmp_path)

    assert report.ok, report.errors
    loaded = load_unit_manifests(tmp_path)
    assert [problem.minutes for problem in loaded[0].practice] == [15, 15, 15]


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


def test_double_length_coverage_normalizes_lexical_practice_path_aliases(tmp_path):
    write_syllabus(tmp_path, second_length="double")
    unit_dir = write_unit(tmp_path, practice_count=24, lesson_sessions=[85] * 4)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_text = manifest_path.read_text().replace(
        "path: practice/p24.ipynb", "path: ./practice/p23.ipynb"
    )
    manifest_path.write_text(manifest_text)

    report = check_coverage(tmp_path)

    assert not report.ok
    assert (
        f"{manifest_path}: double-length unit U2 has 23 distinct practice paths; "
        "requires 24-30"
    ) in report.errors
    assert not any("distinct practice ids" in error for error in report.errors)


def test_double_length_coverage_accepts_compliant_unit(tmp_path):
    write_syllabus(tmp_path, second_length="double")
    write_unit(tmp_path, practice_count=24, lesson_sessions=[85] * 4)

    report = check_coverage(tmp_path)

    assert report.ok
    assert report.errors == []


def test_double_length_coverage_real_f6_passes():
    syllabus = load_syllabus(ROOT)
    assert "F6-svd-spectral" in syllabus.units
    unit = syllabus.units["F6-svd-spectral"]
    assert unit.length == "double"

    matching_manifests = [
        manifest
        for manifest in load_unit_manifests(ROOT)
        if manifest.unit_id == "F6-svd-spectral"
    ]
    assert len(matching_manifests) == 1
    manifest = matching_manifests[0]
    assert manifest.unit_id == unit.id
    assert manifest.lesson_sessions is not None
    assert 4 <= len(manifest.lesson_sessions) <= 6
    assert 24 <= len({problem.id for problem in manifest.practice}) <= 30
    assert 24 <= len({normpath(problem.path) for problem in manifest.practice}) <= 30

    report = check_coverage(ROOT)

    assert not any("double-length unit F6-svd-spectral" in error for error in report.errors)


def test_double_length_planned_f5_shape_passes(tmp_path):
    write_syllabus(
        tmp_path,
        second_unit="F5-probability",
        second_length="double",
    )
    write_unit(
        tmp_path,
        unit="F5-probability",
        practice_count=25,
        lesson_sessions=[85] * 5,
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


def test_valid_book2_fixture_preserves_existing_r1_manifests_and_r1_namespace(
    tmp_path: Path,
) -> None:
    shutil.copy2(ROOT / "syllabus.md", tmp_path / "syllabus.md")
    for source in sorted(ROOT.glob("units/*/manifest.yaml")):
        destination = tmp_path / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    r1_source = ROOT / "mocktests" / "r1-001" / "manifest.yaml"
    r1_destination = tmp_path / "mocktests" / "r1-001" / "manifest.yaml"
    r1_destination.parent.mkdir(parents=True)
    shutil.copy2(r1_source, r1_destination)
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.glob("units/*/manifest.yaml"))
    }
    namespace_before = [manifest.test for manifest in load_mock_manifests(tmp_path)]
    before_report = check_prereq(tmp_path)
    assert before_report.ok, before_report.errors

    book2 = tmp_path / "units" / "B2-019-attention-transformers" / "manifest.yaml"
    _write = {
        "unit": "B2-019-attention-transformers",
        "book": 2,
        "round": 2,
        "layer": "round-2-extension",
        "track": "extension",
        "concepts_taught": [
            "matrix-transpose",
            "query-key-value-attention",
            "scaled-dot-product-attention",
            "attention-mask",
            "causal-self-attention",
            "multi-head-attention",
            "sinusoidal-positional-encoding",
            "attention-complexity",
            "transformer-residual-layernorm",
            "position-wise-feed-forward",
            "transformer-block",
        ],
        "concepts_used": [
            "softmax",
            "matrix-multiplication",
            "broadcasting",
            "variance",
            "torch-tensors",
            "nn-module",
            "torch-optimizers",
            "autograd-training",
        ],
        "concept_prerequisites": [
            "softmax",
            "matrix-multiplication",
            "broadcasting",
            "variance",
            "torch-tensors",
            "nn-module",
            "torch-optimizers",
            "autograd-training",
        ],
        "prereq_units": [
            "C6-pytorch",
            "C7-cnn-transfer",
            "C8-embeddings",
            "C11-neural-training",
        ],
        "bridge_diagnostic": {
            "path": "lessons/00-book1-bridge.ipynb",
            "minutes": 30,
            "referenced_concepts": ["softmax"],
        },
        "coverage_claims": [],
        "practice": [],
    }
    book2.parent.mkdir(parents=True)
    book2.write_text(yaml.safe_dump(_write, sort_keys=False))

    parsed_book2 = next(
        manifest
        for manifest in load_unit_manifests(tmp_path)
        if manifest.unit_id == "B2-019-attention-transformers"
    )
    after_report = check_prereq(tmp_path)

    after = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted(tmp_path.glob("units/*/manifest.yaml"))
        if not path.parent.name.startswith("B2-")
    }
    namespace_after = [manifest.test for manifest in load_mock_manifests(tmp_path)]

    assert parsed_book2.concepts_taught == _write["concepts_taught"]
    assert parsed_book2.prereq_units == _write["prereq_units"]
    assert after_report.ok, after_report.errors
    assert after == before
    assert namespace_before == namespace_after == ["r1-001"]
