from pathlib import Path

from tools.checks.answerkey import check_answerkey
from tools.cli import main
from tools.model import load_mock_manifests

FIXTURES = Path(__file__).parent / "fixtures" / "answerkey"


def test_answerkey_fixture_passes_with_numeric_tolerance(capsys):
    root = FIXTURES / "pass"
    report = check_answerkey(root)

    assert report.ok
    assert report.errors == []
    assert report.skipped is None
    assert main(["--root", str(root), "answerkey-check"]) == 0
    assert "PASS answerkey-check" in capsys.readouterr().out


def test_answerkey_fixture_reports_mismatch(capsys):
    root = FIXTURES / "mismatch"
    report = check_answerkey(root)

    assert not report.ok
    assert any("r1-001-p01" in error and "answers.md" in error for error in report.errors)
    assert main(["--root", str(root), "answerkey-check"]) == 1
    assert "FAIL answerkey-check" in capsys.readouterr().err


def test_answerkey_draft_only_fixture_is_loud_skip(capsys):
    root = FIXTURES / "draft-only"

    report = check_answerkey(root)
    assert report.ok
    assert report.skipped is not None
    assert main(["--root", str(root), "answerkey-check"]) == 3
    assert "SKIP answerkey-check" in capsys.readouterr().out


def test_answer_tolerance_loads_from_manifest():
    manifest = load_mock_manifests(FIXTURES / "pass")[0]

    assert manifest.problems[2].answer_tolerance == 0.01
