import json
from pathlib import Path

import nbformat

from tools.checks.overlap import check_overlap
from tools.cli import print_report


def write_manifest(
    root: Path,
    spec: str,
    provenance: str = "original",
    adapted_from: str = "",
    files: list[str] | None = None,
    problem_ids: list[str] | None = None,
) -> None:
    test_dir = root / "mocktests" / "r1-001"
    test_dir.mkdir(parents=True)
    adapted_line = f"    adapted-from: {adapted_from}\n" if adapted_from else ""
    files_block = ""
    if files:
        files_block = "    files:\n" + "".join(f"      - {path}\n" for path in files)
    problem_blocks = "".join(
        f"""
  - id: {problem_id}
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
{files_block}"""
        for problem_id in (problem_ids or ["p01"])
    )
    test_dir.joinpath("manifest.yaml").write_text(
        f"""
test: r1-001
blueprint_version: 1
duration_minutes: 180
total_points: 300
time_budget: {{}}
problems:
{problem_blocks}
"""
    )


def write_reference(
    root: Path,
    text: str,
    *,
    ref_id: str = "r1-fixture",
    summary: str | None = None,
) -> None:
    ref = root / "reference" / ref_id
    ref.mkdir(parents=True)
    summary_line = f"    summary: {json.dumps(summary)}\n" if summary else ""
    ref.joinpath("index.yaml").write_text(
        f"""
test: fixture
problems:
  - id: ref-p01
{summary_line}
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


def test_mock_spec_cosine_scans_distinct_summary_stream(tmp_path):
    write_reference(
        tmp_path,
        "unrelated source statement about quartz lanterns",
        summary="alpha beta gamma delta epsilon zeta eta theta",
    )
    write_manifest(tmp_path, "theta eta zeta epsilon delta gamma beta alpha")

    report = check_overlap(tmp_path)

    assert not report.ok
    assert any("#summary-0" in error and "cosine=" in error for error in report.errors)


def test_summary_stream_is_not_used_for_statement_overlap(tmp_path):
    copied_summary = "alpha beta gamma delta epsilon zeta eta theta iota kappa"
    write_reference(
        tmp_path,
        "unrelated source statement about quartz lanterns",
        summary=copied_summary,
    )
    write_manifest(
        tmp_path,
        "fresh prompt about harbor census",
        files=["statement.md"],
    )
    statement = tmp_path / "mocktests" / "r1-001" / "statement.md"
    statement.write_text(copied_summary)

    report = check_overlap(tmp_path)

    assert report.ok
    assert not report.errors
    assert not any("file-level cosine" in warning for warning in report.warnings)


def test_mock_problem_reports_every_overlapping_reference(tmp_path):
    copied = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    write_reference(tmp_path, copied, ref_id="r1-first")
    write_reference(tmp_path, copied, ref_id="r1-second")
    write_manifest(tmp_path, copied)

    report = check_overlap(tmp_path)

    overlap_errors = [error for error in report.errors if " overlaps " in error]
    assert len(overlap_errors) == 2
    assert any("r1-first" in error for error in overlap_errors)
    assert any("r1-second" in error for error in overlap_errors)


def test_overlap_passes_original_fixture(tmp_path):
    write_reference(tmp_path, "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda")
    write_manifest(tmp_path, "fresh prompt about matrices and gradients")
    assert check_overlap(tmp_path).ok


def test_mock_spec_cosine_ignores_mandated_register_boilerplate(tmp_path):
    mock_register = """
Total: 25 points.
Part 2.3 (5 points)
Reasoning is required.
Coding is not allowed.
- A. amber
- B. birch
- C. copper
- D. dune
- E. elm
Write the result in the unique form p/q, where p and q are integers, q > 0, and gcd(p, q) = 1.
What is p + q?
"""
    corpus_register = """
- E. quartz
- D. river
- C. slate
- B. timber
- A. umber
Coding is not allowed.
Reasoning is required.
Part 2.3 (5 points)
Total: 25 points.
Write your result in the unique form p/q, with relatively prime integers p and q and positive q.
What is p+q?
    """
    write_reference(tmp_path, corpus_register + "classify basalt lanterns")
    write_manifest(
        tmp_path,
        mock_register + "derive zephyr covariances",
        files=["statement.md"],
    )
    statement = tmp_path / "mocktests" / "r1-001" / "statement.md"
    statement.write_text("fresh statement about zephyr covariances")

    report = check_overlap(tmp_path)

    assert report.ok
    assert not report.errors


def test_mock_statement_file_cosine_near_point_four_is_silent(tmp_path):
    reference = "alpha beta gamma delta epsilon zeta eta"
    topical_but_distinct = "delta gamma beta alpha harbor island jasmine"
    write_reference(tmp_path, reference)
    write_manifest(tmp_path, "fresh prompt about harbor census", files=["statement.md"])
    statement = tmp_path / "mocktests" / "r1-001" / "statement.md"
    statement.write_text(topical_but_distinct)

    report = check_overlap(tmp_path)

    assert report.ok
    assert not report.errors
    assert not any("file-level cosine" in warning for warning in report.warnings)


def test_mock_statement_file_cosine_above_point_five_warns_once_and_passes(
    tmp_path, capsys
):
    reference = "alpha beta gamma delta epsilon zeta eta"
    same_terms_different_order = "eta zeta epsilon delta gamma beta alpha"
    write_reference(tmp_path, reference)
    write_manifest(
        tmp_path,
        "fresh prompt about harbor census",
        files=["statement.md"],
        problem_ids=["p01-1", "p01-2"],
    )
    statement = tmp_path / "mocktests" / "r1-001" / "statement.md"
    statement.write_text(same_terms_different_order)

    report = check_overlap(tmp_path)
    cosine_warnings = [
        warning for warning in report.warnings if "file-level cosine" in warning
    ]

    assert report.ok
    assert not report.errors
    assert len(cosine_warnings) == 1
    assert str(statement) in cosine_warnings[0]
    assert print_report(report) == 0
    assert "WARNING overlap-scan" in capsys.readouterr().out


def test_mock_statement_file_verbatim_shingles_still_error(tmp_path):
    copied = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    write_reference(tmp_path, copied)
    write_manifest(tmp_path, "fresh prompt about harbor census", files=["statement.md"])
    statement = tmp_path / "mocktests" / "r1-001" / "statement.md"
    statement.write_text(copied)

    report = check_overlap(tmp_path)

    assert not report.ok
    assert any("shingles=4" in error for error in report.errors)


def test_mock_register_filter_preserves_real_content_detection(tmp_path):
    copied = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    write_reference(tmp_path, f"Reasoning is required. Coding is not allowed. {copied}")
    write_manifest(tmp_path, f"Coding is not allowed. Reasoning is required. {copied}")

    report = check_overlap(tmp_path)

    assert not report.ok
    assert any("shingles=" in error for error in report.errors)


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


def test_mock_register_filter_leaves_unit_real_content_detection_unchanged(tmp_path):
    copied = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    write_reference(tmp_path, copied)
    notebook = write_notebook(tmp_path, "copied.ipynb", markdown=copied)

    report = check_overlap(tmp_path)

    assert not report.ok
    assert any(str(notebook) in error for error in report.errors)


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


def test_overlap_partial_pdftotext_failure_warns(tmp_path, monkeypatch):
    # One good corpus part + one corrupt PDF: the corrupt part must surface as a
    # warning, never be silently dropped (a copied source could escape scanning).
    ref = tmp_path / "reference" / "r1-9999"
    ref.mkdir(parents=True)
    (ref / "index.yaml").write_text("sections:\n  - problems:\n      - text: |\n          alpha beta gamma delta epsilon zeta eta theta iota kappa\n")
    (ref / "broken.pdf").write_bytes(b"%PDF-1.5 truncated garbage")
    (tmp_path / "mocktests").mkdir()
    (tmp_path / "units").mkdir()
    import shutil as _sh

    from tools.checks.overlap import check_overlap
    if _sh.which("pdftotext") is None:
        import pytest as _pytest
        _pytest.skip("pdftotext unavailable")
    report = check_overlap(tmp_path)
    assert any("NOT scanned" in w and "broken.pdf" in w for w in report.warnings)
