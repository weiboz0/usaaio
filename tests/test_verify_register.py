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
