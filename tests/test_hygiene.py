import json

from tools.checks.hygiene import check_hygiene


def notebook(cell):
    return {
        "cells": [cell],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_nb(path, cell):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notebook(cell)))


def test_hygiene_clean_notebook_passes(tmp_path):
    write_nb(
        tmp_path / "units" / "U1" / "practice" / "p01.ipynb",
        {"cell_type": "code", "source": "x = 1", "metadata": {}, "outputs": [], "execution_count": None},
    )
    assert check_hygiene(tmp_path).ok


def test_hygiene_flags_outputs(tmp_path):
    write_nb(
        tmp_path / "mocktests" / "r1-001" / "problems" / "p01.ipynb",
        {
            "cell_type": "code",
            "source": "x",
            "metadata": {},
            "outputs": [{"output_type": "stream", "text": "1"}],
            "execution_count": 1,
        },
    )
    report = check_hygiene(tmp_path)
    assert not report.ok
    assert any("executed outputs" in error for error in report.errors)
    assert any("execution_count" in error for error in report.errors)


def test_hygiene_flags_solution_marker(tmp_path):
    write_nb(
        tmp_path / "units" / "U1" / "practice" / "p01.ipynb",
        {
            "cell_type": "code",
            "source": "# SOLUTION\nanswer_key = 3",
            "metadata": {"tags": ["solution"]},
            "outputs": [],
            "execution_count": None,
        },
    )
    report = check_hygiene(tmp_path)
    assert not report.ok
    assert any("solution marker" in error for error in report.errors)


def test_hygiene_vacuous_without_notebooks(tmp_path):
    assert check_hygiene(tmp_path).ok
    write_nb(
        tmp_path / "units" / "U1" / "practice" / "p01_solution.ipynb",
        {
            "cell_type": "code",
            "source": "# SOLUTION",
            "metadata": {"tags": ["solution"]},
            "outputs": [{"output_type": "stream", "text": "ok"}],
            "execution_count": 1,
        },
    )
    assert not check_hygiene(tmp_path).ok


def test_hygiene_rejects_solution_notebook_without_executable_assert(tmp_path):
    write_nb(
        tmp_path / "units" / "U1" / "practice" / "p01_solution.ipynb",
        {
            "cell_type": "code",
            "source": "answer = 42",
            "metadata": {},
            "outputs": [],
            "execution_count": None,
        },
    )

    report = check_hygiene(tmp_path)

    assert not report.ok
    assert any("solution notebook has no executable assert" in error for error in report.errors)


def test_hygiene_accepts_solution_notebook_with_assert(tmp_path):
    write_nb(
        tmp_path / "mocktests" / "r1-001" / "solutions" / "p01.ipynb",
        {
            "cell_type": "code",
            "source": "answer = 42\nassert answer == 42",
            "metadata": {},
            "outputs": [],
            "execution_count": None,
        },
    )

    assert check_hygiene(tmp_path).ok
