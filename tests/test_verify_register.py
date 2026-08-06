import importlib.util
import json
from pathlib import Path

import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify-register.py"
SPEC = importlib.util.spec_from_file_location("verify_register", SCRIPT)
verify_register = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verify_register)


def write_problem(root: Path, unit: str, markdown: str, problem_type="scenario"):
    path = root / "units" / unit / "practice" / "p01.ipynb"
    path.parent.mkdir(parents=True)
    problem = {
        "id": f"{unit.split('-', 1)[0]}-p01",
        "path": "practice/p01.ipynb",
        "type": problem_type,
        "difficulty": "core",
        "concepts": ["testing"],
    }
    path.write_text(
        json.dumps(
            {
                "cells": [{"cell_type": "markdown", "source": markdown}],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
    )
    return problem


def test_any_unpriced_bold_ban_clause_is_rejected(tmp_path, monkeypatch):
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** testing\n\n"
        "**Banned in this part: loops.**",
    )
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)

    errors = verify_register._check_problem(unit, problem)

    assert errors == ["C7-p01: bolded ban clause lacks a zero-point price"]


def test_every_bold_ban_clause_is_checked_independently(tmp_path, monkeypatch):
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** testing\n\n"
        "**Banned (zero points): loops.**\n\n"
        "**Additionally banned: comprehensions.**",
    )
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)

    errors = verify_register._check_problem(unit, problem)

    assert errors == ["C7-p01: bolded ban clause lacks a zero-point price"]


def test_semantic_zero_point_price_in_bold_span_is_accepted(tmp_path, monkeypatch):
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** testing\n\n"
        "**Banned in this part: loops. Any use scores zero points.**",
    )
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)

    assert verify_register._check_problem(unit, problem) == []


def test_emphasized_banned_word_is_not_a_bold_ban_clause(tmp_path, monkeypatch):
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** testing\n\n"
        "Loops are **banned** (zero points).",
    )
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)

    assert verify_register._check_problem(unit, problem) == []


def test_main_accepts_any_registered_problem_count(tmp_path, monkeypatch, capsys):
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** testing",
    )
    manifest_path = tmp_path / "units" / unit / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump({"practice": [problem]}))
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    monkeypatch.setattr(verify_register, "UNITS", (unit,))

    assert verify_register.main() == 0
    assert "register verification: 1/1 passed (1 problems checked)" in capsys.readouterr().out


# --- Header agreement is enforced repo-wide (plan 014 gate). The type field admits only an
# --- enumerated set of house glosses; two earlier, more permissive forms of this check each
# --- let drift through and were caught at the gate.

def test_type_gloss_allowlist_accepts_house_forms():
    assert verify_register._type_matches("scenario analysis", "scenario analysis", "scenario")
    assert verify_register._type_matches("scenario", "scenario analysis", "scenario")
    assert verify_register._type_matches(
        "integrative (parts consume earlier results)", "integrative", "integrative"
    )
    assert verify_register._type_matches(
        "integrative (multi-part; parts consume earlier results)", "integrative", "integrative"
    )
    assert verify_register._type_matches("proof / derivation", "proof", "proof")


def test_type_gloss_allowlist_rejects_drift():
    # A bare startswith accepted this.
    assert not verify_register._type_matches(
        "scenario analysis ENTIRELY WRONG", "scenario analysis", "scenario"
    )
    # Allowing any parenthetical or slash suffix accepted these two.
    assert not verify_register._type_matches(
        "scenario (actually multiple choice)", "scenario analysis", "scenario"
    )
    assert not verify_register._type_matches(
        "scenario / multiple choice", "scenario analysis", "scenario"
    )
    assert not verify_register._type_matches("proof", "scenario analysis", "scenario")


def test_header_concept_and_difficulty_drift_is_caught(tmp_path, monkeypatch):
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** advanced · **Concepts:** testing",
    )
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    # The manifest says difficulty "core"; the header says "advanced".
    errors = verify_register._check_problem(unit, problem)
    assert any("difficulty" in error for error in errors)


def test_reordered_concepts_are_caught(tmp_path, monkeypatch):
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** beta, alpha",
    )
    problem["concepts"] = ["alpha", "beta"]
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    errors = verify_register._check_problem(unit, problem)
    assert any("concepts" in error for error in errors)


def test_blank_lines_around_the_header_are_tolerated(tmp_path, monkeypatch):
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "\n\n# C7-example — Practice p01\n\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** testing",
    )
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    assert verify_register._check_problem(unit, problem) == []


def test_statement_without_markdown_reports_instead_of_crashing(tmp_path, monkeypatch):
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** testing",
    )
    path = tmp_path / "units" / unit / "practice" / "p01.ipynb"
    path.write_text(json.dumps({"cells": [{"cell_type": "code", "source": "x = 1"}]}))
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    errors = verify_register._check_problem(unit, problem)
    assert errors and "no markdown cell" in errors[0]


def test_solution_header_drift_is_caught(tmp_path, monkeypatch):
    """A solution that repeats the manifest's claims must not be allowed to drift from them.
    Plan 014 shipped a statement reading "validation" beside a solution still reading "test";
    nothing checked the second copy.
    """
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** testing",
    )
    solution = tmp_path / "units" / unit / "practice" / "p01_solution.ipynb"
    solution.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "source": "# C7-example — Practice p01 — Solution\n\n"
                        "**Type:** scenario analysis · **Difficulty:** core "
                        "· **Concepts:** something-else",
                    }
                ]
            }
        )
    )
    problem["solution_path"] = "practice/p01_solution.ipynb"
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    errors = verify_register._check_solution_header(unit, problem)
    assert any("solution header concepts" in error for error in errors)


def test_solution_without_a_header_is_accepted(tmp_path, monkeypatch):
    """338 of 343 solutions carry no header; that is the convention, not a defect."""
    unit = "C7-example"
    problem = write_problem(
        tmp_path,
        unit,
        "# C7-example — Practice p01\n\n"
        "**Type:** scenario analysis · **Difficulty:** core · **Concepts:** testing",
    )
    solution = tmp_path / "units" / unit / "practice" / "p01_solution.ipynb"
    solution.write_text(
        json.dumps({"cells": [{"cell_type": "markdown", "source": "# Solution\n\nWorking below."}]})
    )
    problem["solution_path"] = "practice/p01_solution.ipynb"
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    assert verify_register._check_solution_header(unit, problem) == []
