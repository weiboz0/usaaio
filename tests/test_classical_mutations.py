from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

EXPECTED_MUTATIONS = [
    {
        "id": "c12-p07-logistic-mean-factor",
        "notebook": "units/C12-classical-models/practice/p07_solution.ipynb",
        "mutation_kind": "remove-logistic-mean-factor",
        "target_marker": "PLAN018_MUTATION_TARGET: C12-p07-logistic-mean-factor",
        "expected_failure_marker": "PLAN018_ANSWER_CHECK: C12-p07-logistic-training",
    },
    {
        "id": "c12-p08-signed-hinge-branch",
        "notebook": "units/C12-classical-models/practice/p08_solution.ipynb",
        "mutation_kind": "reverse-signed-hinge-branch",
        "target_marker": "PLAN018_MUTATION_TARGET: C12-p08-signed-hinge-branch",
        "expected_failure_marker": "PLAN018_ANSWER_CHECK: C12-p08-hinge-subgradient",
    },
    {
        "id": "c12-p10-maximum-impurity-split",
        "notebook": "units/C12-classical-models/practice/p10_solution.ipynb",
        "mutation_kind": "select-maximum-impurity-split",
        "target_marker": "PLAN018_MUTATION_TARGET: C12-p10-best-split",
        "expected_failure_marker": "PLAN018_ANSWER_CHECK: C12-p10-best-split",
    },
    {
        "id": "c12-p29-missing-adaboost-weight-update",
        "notebook": "units/C12-classical-models/practice/p29_solution.ipynb",
        "mutation_kind": "remove-adaboost-weight-update",
        "target_marker": "PLAN018_MUTATION_TARGET: C12-p29-weight-update",
        "expected_failure_marker": "PLAN018_ANSWER_CHECK: C12-p29-adaboost-ledger",
    },
    {
        "id": "c12-p13-non-centroid-lloyd-update",
        "notebook": "units/C12-classical-models/practice/p13_solution.ipynb",
        "mutation_kind": "replace-centroid-with-non-centroid-update",
        "target_marker": "PLAN018_MUTATION_TARGET: C12-p13-centroid-update",
        "expected_failure_marker": "PLAN018_ANSWER_CHECK: C12-p13-lloyd-update",
    },
]


def _mutation_module():
    try:
        return importlib.import_module("tools.verify_classical_mutations")
    except ModuleNotFoundError:
        pytest.fail(
            "tools.verify_classical_mutations must provide the permanent classical mutation runner"
        )


def _write_notebook(path: Path, target_source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "id": "mutation-target",
                        "execution_count": None,
                        "metadata": {},
                        "outputs": [],
                        "source": target_source,
                    },
                    {
                        "cell_type": "code",
                        "id": "answer-check",
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
        id="fixture-classical-mutation",
        notebook="fixture/solution.ipynb",
        mutation_kind="replace-source",
        target_marker="# MUTATION_TARGET",
        search=search,
        replacement=replacement,
        expected_failure_marker="# ANSWER_CHECK",
    )


def test_classical_registry_has_exactly_five_answer_check_mutations() -> None:
    module = _mutation_module()

    actual = [
        {
            "id": mutation.id,
            "notebook": mutation.notebook,
            "mutation_kind": mutation.mutation_kind,
            "target_marker": mutation.target_marker,
            "expected_failure_marker": mutation.expected_failure_marker,
        }
        for mutation in module.MUTATIONS
    ]

    assert actual == EXPECTED_MUTATIONS


def test_each_classical_mutation_resolves_one_file_cell_and_source_replacement() -> None:
    module = _mutation_module()
    root = Path(__file__).resolve().parents[1]

    assert len(module.MUTATIONS) == 5
    for mutation in module.MUTATIONS:
        notebook_path = root / mutation.notebook
        assert notebook_path.is_file()
        notebook = json.loads(notebook_path.read_text())
        code_sources = [
            "".join(cell.get("source", ""))
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        ]
        assert mutation.target_marker in mutation.search
        assert mutation.search != mutation.replacement
        assert sum(source.count(mutation.target_marker) for source in code_sources) == 1
        assert sum(source.count(mutation.search) for source in code_sources) == 1
        assert sum(
            source.count(mutation.expected_failure_marker) for source in code_sources
        ) == 1


@pytest.mark.parametrize(
    ("target_source", "search", "match_count"),
    [
        pytest.param(
            "value = 1  # MUTATION_TARGET\n",
            "missing value  # MUTATION_TARGET",
            0,
            id="zero-match",
        ),
        pytest.param(
            "value = 1  # MUTATION_TARGET\nvalue = 1  # MUTATION_TARGET\n",
            "value = 1  # MUTATION_TARGET",
            2,
            id="multiple-match",
        ),
    ],
)
def test_classical_mutation_runner_fails_closed_on_nonunique_source_match(
    tmp_path: Path,
    target_source: str,
    search: str,
    match_count: int,
) -> None:
    module = _mutation_module()
    _write_notebook(tmp_path / "fixture" / "solution.ipynb", target_source)
    spec = _spec(
        module,
        search=search,
        replacement="value = 2  # MUTATION_TARGET",
    )

    with pytest.raises(
        module.MutationVerificationError,
        match=rf"matched {match_count} source locations",
    ):
        module.run_mutation(tmp_path, spec)


def test_classical_mutation_runner_fails_closed_on_unexpected_success(
    tmp_path: Path,
) -> None:
    module = _mutation_module()
    _write_notebook(
        tmp_path / "fixture" / "solution.ipynb",
        "value = 1  # MUTATION_TARGET\n",
    )
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 1  # mutant still passes",
    )

    with pytest.raises(
        module.MutationVerificationError,
        match="mutant executed successfully",
    ):
        module.run_mutation(tmp_path, spec)


def test_classical_mutation_runner_rejects_search_without_bound_target_marker(
    tmp_path: Path,
) -> None:
    module = _mutation_module()
    _write_notebook(
        tmp_path / "fixture" / "solution.ipynb",
        "value = 1  # MUTATION_TARGET\n",
    )
    spec = _spec(module, search="value = 1", replacement="value = 2")

    with pytest.raises(
        module.MutationVerificationError,
        match="target marker must be contained in search",
    ):
        module.run_mutation(tmp_path, spec)


@pytest.mark.parametrize(
    ("answer_source", "match_count"),
    [
        pytest.param("assert value == 1\n", 0, id="zero-match"),
        pytest.param(
            "assert value == 1  # ANSWER_CHECK\n# ANSWER_CHECK\n",
            2,
            id="multiple-match",
        ),
    ],
)
def test_classical_mutation_runner_fails_closed_on_nonunique_failure_marker(
    tmp_path: Path,
    answer_source: str,
    match_count: int,
) -> None:
    module = _mutation_module()
    notebook_path = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook_path, "value = 1  # MUTATION_TARGET\n")
    notebook = json.loads(notebook_path.read_text())
    notebook["cells"][1]["source"] = answer_source
    notebook_path.write_text(json.dumps(notebook))
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )

    with pytest.raises(
        module.MutationVerificationError,
        match=rf"expected failure marker matched {match_count} source locations",
    ):
        module.run_mutation(tmp_path, spec)


def test_classical_mutation_runner_rejects_failure_before_registered_check(
    tmp_path: Path,
) -> None:
    module = _mutation_module()
    _write_notebook(
        tmp_path / "fixture" / "solution.ipynb",
        "value = 1  # MUTATION_TARGET\n",
    )
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="raise AssertionError('early failure')  # MUTATION_TARGET",
    )

    with pytest.raises(
        module.MutationVerificationError,
        match="failed at cell 0; expected failure at cell 1",
    ):
        module.run_mutation(tmp_path, spec)
