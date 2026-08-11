import shutil
from pathlib import Path

import pytest

from tools.checks.answerkey import check_answerkey
from tools.cli import main
from tools.model import load_mock_manifests

FIXTURES = Path(__file__).parent / "fixtures" / "answerkey"


def _registered_fixture(tmp_path: Path, content_root: Path) -> Path:
    repo = tmp_path / "repo"
    book = repo / "book1"
    shutil.copytree(content_root, book)
    (repo / "books.yaml").write_text(
        "books_version: 1\n"
        "books:\n"
        "  - {id: book1, number: 1, root: book1, depends_on: []}\n",
        encoding="utf-8",
    )
    for relative in (
        "syllabus.md",
        "curriculum/course-schedule.yaml",
        "curriculum/coverage-map.yaml",
        "curriculum/material-inventory.yaml",
        "curriculum/official-topics.yaml",
        "curriculum/source-manifest.yaml",
        "mocktests/blueprint.yaml",
        "docs/course-structure.md",
        "units/.gitkeep",
        "reference/.gitkeep",
    ):
        path = book / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n" if path.suffix == ".yaml" else "fixture\n")
    return repo


def write_direct_key_fixture(
    root: Path,
    *,
    answer_key: str | int,
    marker: str,
    files: list[str] | None = None,
    book_number: int = 1,
) -> None:
    test_id = f"r{book_number}-001"
    problem_id = f"{test_id}-p01"
    test_dir = root / "mocktests" / test_id
    solutions = test_dir / "solutions"
    solutions.mkdir(parents=True)
    files_block = ""
    if files:
        files_block = "    files:\n" + "".join(f"      - {path}\n" for path in files)
        for rel in files:
            path = test_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("theory statement")
    test_dir.joinpath("manifest.yaml").write_text(
        f"""
test: {test_id}
blueprint_version: 1
status: final
problems:
  - id: {problem_id}
    section: math-computation
    answer_key: {answer_key!r}
{files_block}
"""
    )
    solutions.joinpath("answers.md").write_text(
        f"- {problem_id}: answer: {marker}\n"
    )


def test_answerkey_fixture_passes_with_numeric_tolerance(tmp_path, capsys):
    root = FIXTURES / "pass"
    report = check_answerkey(root)

    assert report.ok
    assert report.errors == []
    assert report.skipped is None
    repo = _registered_fixture(tmp_path, root)
    assert main(["--root", str(repo), "--book", "book1", "answerkey-check"]) == 0
    assert "PASS answerkey-check" in capsys.readouterr().out


def test_answerkey_fixture_reports_mismatch(tmp_path, capsys):
    root = FIXTURES / "mismatch"
    report = check_answerkey(root)

    assert not report.ok
    assert any("r1-001-p01" in error and "answers.md" in error for error in report.errors)
    repo = _registered_fixture(tmp_path, root)
    assert main(["--root", str(repo), "--book", "book1", "answerkey-check"]) == 1
    assert "FAIL answerkey-check" in capsys.readouterr().err


def test_answerkey_fraction_key_matches_marker_as_text(tmp_path):
    write_direct_key_fixture(tmp_path, answer_key="775/24", marker="775/24")

    report = check_answerkey(tmp_path)

    assert report.ok
    assert report.errors == []


def test_answerkey_theory_only_problem_passes_without_tagged_cell(tmp_path):
    write_direct_key_fixture(
        tmp_path,
        answer_key=42,
        marker="42",
        files=["theory/p01.md"],
    )

    report = check_answerkey(tmp_path)

    assert report.ok
    assert report.errors == []


def test_answerkey_marker_comparison_normalizes_whitespace(tmp_path):
    write_direct_key_fixture(
        tmp_path,
        answer_key="hash-dependent  set order",
        marker="hash-dependent set order",
    )

    assert check_answerkey(tmp_path).ok


def test_answerkey_draft_only_fixture_is_loud_skip(tmp_path, capsys):
    root = FIXTURES / "draft-only"

    report = check_answerkey(root)
    assert report.ok
    assert report.skipped is not None
    repo = _registered_fixture(tmp_path, root)
    assert main(["--root", str(repo), "--book", "book1", "answerkey-check"]) == 3
    assert "SKIP answerkey-check" in capsys.readouterr().out


def test_answer_tolerance_loads_from_manifest():
    manifest = load_mock_manifests(FIXTURES / "pass")[0]

    assert manifest.problems[2].answer_tolerance == 0.01


def test_answerkey_checks_final_round2_manifest_with_authoritative_number(
    tmp_path: Path,
) -> None:
    write_direct_key_fixture(
        tmp_path,
        answer_key=42,
        marker="41",
        files=["theory/p01.md"],
        book_number=2,
    )

    report = check_answerkey(tmp_path, book_number=2)

    assert not report.ok
    assert any("r2-001-p01" in error for error in report.errors)


def test_answerkey_rejects_wrong_round_directory_for_selected_book2(
    tmp_path: Path,
) -> None:
    write_direct_key_fixture(tmp_path, answer_key=42, marker="42")

    with pytest.raises(ValueError, match="book 2 assessments"):
        check_answerkey(tmp_path, book_number=2)
