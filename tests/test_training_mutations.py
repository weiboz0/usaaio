from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def _mutation_module():
    try:
        return importlib.import_module("tools.verify_training_mutations")
    except ModuleNotFoundError:
        pytest.fail("tools.verify_training_mutations must provide the permanent mutation runner")


def _write_notebook(path: Path, target_source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": target_source,
                    },
                    {
                        "cell_type": "code",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": "assert value == 1  # ANSWER_CHECK\n",
                    },
                ],
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3",
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
    )


def _spec(module, *, search: str, replacement: str):
    return module.MutationSpec(
        id="fixture-mutation",
        notebook="fixture/solution.ipynb",
        search=search,
        replacement=replacement,
        expected_failure_marker="# ANSWER_CHECK",
    )


def test_permanent_registry_has_the_exact_five_real_notebook_mutations() -> None:
    module = _mutation_module()

    assert len(module.MUTATIONS) == 5
    assert [mutation.notebook for mutation in module.MUTATIONS] == [
        "units/C11-neural-training/practice/p16_solution.ipynb",
        "units/C11-neural-training/practice/p23_solution.ipynb",
        "units/C7-cnn-transfer/practice/p10_solution.ipynb",
        "units/C7-cnn-transfer/practice/p27_solution.ipynb",
        "units/C7-cnn-transfer/practice/p27_solution.ipynb",
    ]
    assert len({mutation.id for mutation in module.MUTATIONS}) == 5
    assert all(mutation.search for mutation in module.MUTATIONS)
    assert all(mutation.replacement for mutation in module.MUTATIONS)
    assert all(mutation.expected_failure_marker for mutation in module.MUTATIONS)


def test_mutation_runner_rejects_a_zero_match_target(tmp_path: Path) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "value = 1  # MUTATION_TARGET\n")
    spec = _spec(module, search="missing target", replacement="value = 2")

    with pytest.raises(module.MutationVerificationError, match="matched 0 source locations"):
        module.run_mutation(tmp_path, spec)


def test_mutation_runner_rejects_a_multiple_match_target(tmp_path: Path) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(
        notebook,
        "value = 1  # MUTATION_TARGET\nvalue = 1  # MUTATION_TARGET\n",
    )
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )

    with pytest.raises(module.MutationVerificationError, match="matched 2 source locations"):
        module.run_mutation(tmp_path, spec)


def test_mutation_runner_rejects_a_non_failing_mutant(tmp_path: Path) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "value = 1  # MUTATION_TARGET\n")
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 1  # mutant still passes",
    )

    with pytest.raises(module.MutationVerificationError, match="mutant executed successfully"):
        module.run_mutation(tmp_path, spec)


def test_mutation_runner_rejects_failure_before_registered_answer_check(
    tmp_path: Path,
) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "value = 1  # MUTATION_TARGET\n")
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="raise AssertionError('early failure')",
    )

    with pytest.raises(
        module.MutationVerificationError,
        match="failed at cell 0; expected failure at cell 1",
    ):
        module.run_mutation(tmp_path, spec)


def test_mutation_runner_accepts_failure_at_registered_answer_check(
    tmp_path: Path,
) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "value = 1  # MUTATION_TARGET\n")
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )

    result = module.run_mutation(tmp_path, spec)

    assert result.mutation_id == "fixture-mutation"
    assert result.failure_cell == 1
