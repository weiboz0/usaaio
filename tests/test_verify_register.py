import importlib.util
import json
from pathlib import Path

import pytest
import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify-register.py"
SPEC = importlib.util.spec_from_file_location("verify_register", SCRIPT)
verify_register = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(verify_register)


def write_problem(root: Path, unit: str, markdown: str, problem_type="scenario"):
    path = root / "units" / unit / "practice" / "p01.ipynb"
    path.parent.mkdir(parents=True, exist_ok=True)
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

    assert verify_register.main(["--statements-only"]) == 0
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


def test_solution_without_a_header_skips_the_field_checks(tmp_path, monkeypatch):
    """328 of 343 solutions carry no metadata header; that is the convention, not a defect.
    The TITLE is still checked on every solution — only the field checks are skipped.
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
                        "source": "# C7-example — Practice p01 — Solution\n\nWorking below.",
                    }
                ]
            }
        )
    )
    problem["solution_path"] = "practice/p01_solution.ipynb"
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    assert verify_register._check_solution_header(unit, problem) == []


def test_solution_title_mis_attribution_is_caught(tmp_path, monkeypatch):
    """A solution retitled to another problem's number passed every field check until plan
    014's round 3: the fields all belonged to the manifest entry, only the title lied.
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
                        "source": "# C7-example — Practice p99 — Solution\n\n"
                        "**Type:** scenario analysis · **Difficulty:** core "
                        "· **Concepts:** testing",
                    }
                ]
            }
        )
    )
    problem["solution_path"] = "practice/p01_solution.ipynb"
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    errors = verify_register._check_solution_header(unit, problem)
    assert any("solution title" in error for error in errors)


def test_type_gloss_is_scoped_to_its_own_type():
    """A single global gloss list let one type borrow another's gloss (plan 014 round 4)."""
    assert verify_register._type_matches(
        "integrative (parts consume earlier results)", "integrative", "integrative"
    )
    assert verify_register._type_matches("proof / derivation", "proof", "proof")
    # ... but neither gloss travels to a type it does not describe.
    assert not verify_register._type_matches(
        "scenario analysis (parts consume earlier results)", "scenario analysis", "scenario"
    )
    assert not verify_register._type_matches(
        "proof (parts consume earlier results)", "proof", "proof"
    )
    assert not verify_register._type_matches(
        "scenario analysis / derivation", "scenario analysis", "scenario"
    )


def test_relocated_solution_header_cannot_opt_out(tmp_path, monkeypatch):
    """Scanning only the first markdown cell let a solution dodge the check by moving its
    header lower down and taking a wrong title with it (plan 014 round 4).
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
                    {"cell_type": "markdown", "source": "# Some Other Title\n\nprose"},
                    {
                        "cell_type": "markdown",
                        "source": "**Type:** scenario analysis · **Difficulty:** core "
                        "· **Concepts:** testing",
                    },
                ]
            }
        )
    )
    problem["solution_path"] = "practice/p01_solution.ipynb"
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    errors = verify_register._check_solution_header(unit, problem)
    assert any("solution title" in error for error in errors)


def c11_statement(*, options=5, reasoning="Reasoning is required.", budget=15, extra=""):
    option_lines = "\n".join(f"{letter}. option {letter}" for letter in "ABCDE"[:options])
    return (
        "# C11-neural-training — Practice p01\n\n"
        "**Type:** multiple choice · **Difficulty:** intro · **Concepts:** softmax"
        f"{extra}\n\n"
        f"**Time budget:** {budget} minutes\n\n"
        f"{reasoning}\n\n"
        f"{option_lines}"
    )


def c11_problem(root: Path, markdown: str) -> dict:
    problem = write_problem(
        root,
        "C11-neural-training",
        markdown,
        problem_type="mc",
    )
    problem["concepts"] = ["softmax"]
    problem["difficulty"] = "intro"
    problem["minutes"] = 15
    return problem


def test_c11_mc_requires_exactly_five_options(tmp_path, monkeypatch):
    problem = c11_problem(tmp_path, c11_statement(options=4))
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)

    assert verify_register._check_problem("C11-neural-training", problem) == [
        "C11-p01: MC options are not exactly A.-through-E. in order"
    ]


def test_c11_mc_requires_positive_reasoning_flag(tmp_path, monkeypatch):
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    missing = c11_problem(tmp_path, c11_statement(reasoning="Explain your choice."))
    assert verify_register._check_problem("C11-neural-training", missing) == [
        "C11-p01: MC reasoning flag must say 'Reasoning is required.'"
    ]

    wrong = c11_problem(tmp_path, c11_statement(reasoning="Reasoning is not required."))
    assert verify_register._check_problem("C11-neural-training", wrong) == [
        "C11-p01: MC reasoning flag must say 'Reasoning is required.'"
    ]


def test_c11_statement_requires_matching_body_time_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    missing = c11_problem(tmp_path, c11_statement().replace("**Time budget:** 15 minutes\n\n", ""))
    assert verify_register._check_problem("C11-neural-training", missing) == [
        "C11-p01: time budget is missing or does not match manifest minutes 15"
    ]

    mismatched = c11_problem(tmp_path, c11_statement(budget=20))
    assert verify_register._check_problem("C11-neural-training", mismatched) == [
        "C11-p01: time budget is missing or does not match manifest minutes 15"
    ]


def test_statement_header_rejects_a_fourth_field(tmp_path, monkeypatch):
    problem = c11_problem(
        tmp_path,
        c11_statement(extra=" · **Time:** 15 minutes"),
    )
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)

    assert verify_register._check_problem("C11-neural-training", problem) == [
        "C11-p01: header fields must be exactly Type / Difficulty / Concepts"
    ]


def test_missing_statement_path_is_a_named_finding(tmp_path, monkeypatch):
    problem = c11_problem(tmp_path, c11_statement())
    (tmp_path / "units/C11-neural-training/practice/p01.ipynb").unlink()
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)

    assert verify_register._check_problem("C11-neural-training", problem) == [
        "C11-p01: statement path does not exist"
    ]


def test_full_mode_requires_solution_key_and_existing_path(tmp_path, monkeypatch):
    problem = c11_problem(tmp_path, c11_statement())
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)

    assert verify_register._check_solution_header("C11-neural-training", problem) == [
        "C11-p01: solution_path is missing"
    ]

    problem["solution_path"] = "practice/p01_solution.ipynb"
    assert verify_register._check_solution_header("C11-neural-training", problem) == [
        "C11-p01: solution_path does not exist"
    ]


def test_c11_full_mode_requires_solution_metadata_header(tmp_path, monkeypatch):
    problem = c11_problem(tmp_path, c11_statement())
    solution = tmp_path / "units/C11-neural-training/practice/p01_solution.ipynb"
    solution.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "source": "# C11-neural-training — Practice p01 — Solution\n\nWork.",
                    }
                ]
            }
        )
    )
    problem["solution_path"] = "practice/p01_solution.ipynb"
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)

    assert verify_register._check_solution_header("C11-neural-training", problem) == [
        "C11-p01: solution metadata header is missing"
    ]


def test_statements_only_accepts_absent_solutions_but_checks_statements(
    tmp_path, monkeypatch, capsys
):
    unit = "C11-neural-training"
    problem = c11_problem(tmp_path, c11_statement())
    manifest_path = tmp_path / "units" / unit / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump({"practice": [problem]}))
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    monkeypatch.setattr(verify_register, "UNITS", (unit,))

    assert verify_register.main(["--statements-only"]) == 0
    assert "1/1 passed" in capsys.readouterr().out

    c11_problem(tmp_path, c11_statement(options=4))
    assert verify_register.main(["--statements-only"]) == 1
    assert "MC options" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("markdown", "missing_statement", "finding"),
    [
        (
            c11_statement(options=4),
            False,
            "MC options are not exactly A.-through-E. in order",
        ),
        (
            c11_statement(reasoning="Explain your choice."),
            False,
            "MC reasoning flag must say 'Reasoning is required.'",
        ),
        (
            c11_statement(reasoning="Reasoning is not required."),
            False,
            "MC reasoning flag must say 'Reasoning is required.'",
        ),
        (
            c11_statement().replace("**Time budget:** 15 minutes\n\n", ""),
            False,
            "time budget is missing or does not match manifest minutes 15",
        ),
        (
            c11_statement(budget=20),
            False,
            "time budget is missing or does not match manifest minutes 15",
        ),
        (
            c11_statement(extra=" · **Time:** 15 minutes"),
            False,
            "header fields must be exactly Type / Difficulty / Concepts",
        ),
        (
            c11_statement(),
            True,
            "statement path does not exist",
        ),
    ],
    ids=[
        "four-options",
        "missing-reasoning",
        "wrong-reasoning",
        "missing-budget",
        "mismatched-budget",
        "fourth-header-field",
        "missing-statement-path",
    ],
)
def test_statements_only_main_rejects_each_malformed_statement(
    tmp_path, monkeypatch, capsys, markdown, missing_statement, finding
):
    unit = "C11-neural-training"
    problem = c11_problem(tmp_path, markdown)
    if missing_statement:
        problem["path"] = "practice/missing.ipynb"
    manifest_path = tmp_path / "units" / unit / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump({"practice": [problem]}))
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    monkeypatch.setattr(verify_register, "UNITS", (unit,))

    assert verify_register.main(["--statements-only"]) == 1
    assert f"FAIL C11-p01: {finding}" in capsys.readouterr().out


def test_full_mode_reports_missing_statement_and_solution_without_traceback(
    tmp_path, monkeypatch, capsys
):
    unit = "C11-neural-training"
    problem = c11_problem(tmp_path, c11_statement())
    problem["path"] = "practice/missing.ipynb"
    problem["solution_path"] = "practice/missing_solution.ipynb"
    manifest_path = tmp_path / "units" / unit / "manifest.yaml"
    manifest_path.write_text(yaml.safe_dump({"practice": [problem]}))
    monkeypatch.setattr(verify_register, "ROOT", tmp_path)
    monkeypatch.setattr(verify_register, "UNITS", (unit,))

    assert verify_register.main([]) == 1
    output = capsys.readouterr().out
    assert "C11-p01: statement path does not exist" in output
    assert "C11-p01: solution_path does not exist" in output
