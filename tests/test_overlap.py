from pathlib import Path

from tools.checks.overlap import check_overlap


def write_manifest(root: Path, spec: str, provenance: str = "original", adapted_from: str = "") -> None:
    test_dir = root / "mocktests" / "r1-001"
    test_dir.mkdir(parents=True)
    adapted_line = f"    adapted-from: {adapted_from}\n" if adapted_from else ""
    test_dir.joinpath("manifest.yaml").write_text(
        f"""
test: r1-001
blueprint_version: 1
duration_minutes: 180
total_points: 300
time_budget: {{}}
problems:
  - id: p01
    section: concept-block
    units: []
    concepts: []
    cluster: ml-concepts
    points: 10
    difficulty: intro
    type: theory
    answer_form: short
    provenance: {provenance}
{adapted_line}    spec: {spec}
    answer_key: A
"""
    )


def write_reference(root: Path, text: str) -> None:
    ref = root / "reference" / "r1-fixture"
    ref.mkdir(parents=True)
    ref.joinpath("index.yaml").write_text(
        f"""
test: fixture
problems:
  - id: ref-p01
    text: {text}
"""
    )


def test_overlap_skips_loudly_without_corpus(tmp_path):
    write_manifest(tmp_path, "original problem text")
    report = check_overlap(tmp_path)
    assert report.skipped
    assert "bash scripts/fetch-reference.sh" in report.skipped


def test_overlap_flags_near_copy_fixture(tmp_path):
    text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    write_reference(tmp_path, text)
    write_manifest(tmp_path, text)
    report = check_overlap(tmp_path)
    assert not report.ok
    assert any("shingles=" in error for error in report.errors)


def test_overlap_accepts_tagged_adaptation(tmp_path):
    text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    write_reference(tmp_path, text)
    write_manifest(tmp_path, text, provenance="adapted", adapted_from="fixture-p01")
    report = check_overlap(tmp_path)
    assert report.ok
    assert any("overlaps" in warning for warning in report.warnings)


def test_overlap_passes_original_fixture(tmp_path):
    write_reference(tmp_path, "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda")
    write_manifest(tmp_path, "fresh prompt about matrices and gradients")
    assert check_overlap(tmp_path).ok
