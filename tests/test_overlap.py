import json
from pathlib import Path

import nbformat

from tools.checks.overlap import check_overlap
from tools.cli import print_report


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
{adapted_line}    spec: {json.dumps(spec)}
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
    text: {json.dumps(text)}
"""
    )


def write_notebook(
    root: Path,
    name: str,
    *,
    markdown: str = "",
    code: str = "",
) -> Path:
    practice = root / "units" / "U1" / "practice"
    practice.mkdir(parents=True, exist_ok=True)
    cells = []
    if markdown:
        cells.append(nbformat.v4.new_markdown_cell(markdown))
    if code:
        cells.append(nbformat.v4.new_code_cell(code))
    path = practice / name
    nbformat.write(nbformat.v4.new_notebook(cells=cells), path)
    return path


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


def test_overlap_scans_unit_practice(tmp_path):
    copied = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    write_reference(tmp_path, copied)
    markdown_path = write_notebook(tmp_path, "markdown.ipynb", markdown=copied)
    code_path = write_notebook(tmp_path, "code.ipynb", code=f"# {copied}")

    report = check_overlap(tmp_path)

    assert not report.ok
    assert any(str(markdown_path) in error for error in report.errors)
    assert any(str(code_path) in error for error in report.errors)


def test_overlap_boilerplate_exempt(tmp_path):
    boilerplate = (
        "import alpha beta gamma delta epsilon zeta eta theta iota\n"
        "from kappa lambda mu nu xi omicron pi rho sigma import tau\n"
        "rng = default_rng(alpha beta gamma delta epsilon zeta eta theta)\n"
        "SEED = alpha beta gamma delta epsilon zeta eta theta iota"
    )
    write_reference(tmp_path, boilerplate)
    write_manifest(tmp_path, boilerplate)
    write_notebook(tmp_path, "boilerplate.ipynb", code=boilerplate)

    report = check_overlap(tmp_path)

    assert report.ok
    assert not report.errors


def test_overlap_units_shingle_only(tmp_path):
    reference = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    same_terms_different_order = (
        "mu lambda kappa iota theta eta zeta epsilon delta gamma beta alpha"
    )
    write_reference(tmp_path, reference)
    write_notebook(tmp_path, "topical.ipynb", markdown=same_terms_different_order)

    report = check_overlap(tmp_path)

    assert report.ok
    assert not report.errors


def test_overlap_loud_skip_preserved(tmp_path, monkeypatch, capsys):
    write_reference(tmp_path, "reference text that must not be scanned")
    notebook = write_notebook(tmp_path, "unreadable.ipynb", markdown="not scanned")
    notebook.write_text("not valid notebook json")
    monkeypatch.setattr("tools.checks.overlap.shutil.which", lambda _: None)

    report = check_overlap(tmp_path)

    assert report.skipped
    assert report.skipped.startswith("pdftotext unavailable")
    assert "bash scripts/fetch-reference.sh" in report.skipped
    assert print_report(report) == 3
    assert "SKIP overlap-scan" in capsys.readouterr().out
