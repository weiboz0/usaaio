from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

EXPECTED_MUTATIONS = [
    {
        "id": "c11-p16-delay-zero-grad",
        "notebook": "units/C11-neural-training/practice/p16_solution.ipynb",
        "mutation_kind": "delay-zero-grad-until-after-backward",
        "target_marker": "PLAN017_MUTATION_TARGET: C11-p16-zero-grad",
        "expected_failure_marker": "PLAN017_ANSWER_CHECK: C11-p16-training",
    },
    {
        "id": "c11-p23-noop-optimizer-step",
        "notebook": "units/C11-neural-training/practice/p23_solution.ipynb",
        "mutation_kind": "replace-optimizer-step-with-no-op",
        "target_marker": "PLAN017_MUTATION_TARGET: C11-p23-optimizer-step",
        "expected_failure_marker": "PLAN017_ANSWER_CHECK: C11-p23-training",
    },
    {
        "id": "c7-p10-forbidden-frozen-update",
        "notebook": "units/C7-cnn-transfer/practice/p10_solution.ipynb",
        "mutation_kind": "enable-forbidden-frozen-parameter-update",
        "target_marker": "PLAN017_MUTATION_TARGET: C7-p10-frozen-update",
        "expected_failure_marker": "PLAN017_ANSWER_CHECK: C7-p10-freezing",
    },
    {
        "id": "c7-p27-move-committed-predictions",
        "notebook": "units/C7-cnn-transfer/practice/p27_solution.ipynb",
        "mutation_kind": "move-committed-predictions-below-verifier",
        "target_marker": "PLAN017_MUTATION_TARGET: C7-p27-committed-predictions",
        "expected_failure_marker": "PLAN017_VERIFIER: C7-p27-committed-predictions",
    },
    {
        "id": "c7-p27-train-mode-buffer-audit",
        "notebook": "units/C7-cnn-transfer/practice/p27_solution.ipynb",
        "mutation_kind": "replace-eval-mode-with-train-mode-for-buffer-audit",
        "target_marker": "PLAN017_MUTATION_TARGET: C7-p27-eval-mode",
        "expected_failure_marker": "PLAN017_ANSWER_CHECK: C7-p27-mode-buffer-audit",
    },
]


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
        id="fixture-mutation",
        notebook="fixture/solution.ipynb",
        mutation_kind="replace-source",
        target_marker="# MUTATION_TARGET",
        search=search,
        replacement=replacement,
        expected_failure_marker="# ANSWER_CHECK",
    )


def test_permanent_registry_has_the_exact_five_real_notebook_mutations() -> None:
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


def test_each_real_mutation_source_contract_resolves_exactly_once() -> None:
    module = _mutation_module()
    root = Path(__file__).resolve().parents[1]

    for mutation in module.MUTATIONS:
        assert mutation.target_marker in mutation.search
        notebook = json.loads((root / mutation.notebook).read_text())
        code_sources = [
            "".join(cell.get("source", ""))
            for cell in notebook["cells"]
            if cell["cell_type"] == "code"
        ]
        assert sum(source.count(mutation.target_marker) for source in code_sources) == 1
        assert sum(source.count(mutation.search) for source in code_sources) == 1
        assert sum(source.count(mutation.expected_failure_marker) for source in code_sources) == 1


def test_mutation_runner_rejects_a_zero_match_target(tmp_path: Path) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "value = 1  # MUTATION_TARGET\n")
    spec = _spec(
        module,
        search="missing value  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )

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


def test_mutation_runner_rejects_search_that_does_not_contain_target_marker(
    tmp_path: Path,
) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "value = 1\n")
    spec = _spec(module, search="value = 1", replacement="value = 2")

    with pytest.raises(module.MutationVerificationError, match="must be contained in search"):
        module.run_mutation(tmp_path, spec)


def test_mutation_runner_rejects_duplicate_target_markers_even_when_search_matches_once(
    tmp_path: Path,
) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(
        notebook,
        "value = 1  # MUTATION_TARGET\n# MUTATION_TARGET\n",
    )
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )

    with pytest.raises(
        module.MutationVerificationError,
        match="target marker matched 2 source locations",
    ):
        module.run_mutation(tmp_path, spec)


def test_mutation_runner_rejects_unique_marker_and_search_in_separate_code_cells(
    tmp_path: Path,
) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "# MUTATION_TARGET\n")
    payload = json.loads(notebook.read_text())
    payload["cells"].insert(
        1,
        {
            "cell_type": "code",
            "id": "separate-search",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": "value = 1\n",
        },
    )
    notebook.write_text(json.dumps(payload))
    spec = _spec(module, search="value = 1", replacement="value = 2")

    with pytest.raises(
        module.MutationVerificationError,
        match="target marker must be contained in search",
    ):
        module.run_mutation(tmp_path, spec)


def test_mutation_runner_rejects_a_missing_expected_failure_marker(tmp_path: Path) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "value = 1  # MUTATION_TARGET\n")
    payload = json.loads(notebook.read_text())
    payload["cells"][1]["source"] = "assert value == 1\n"
    notebook.write_text(json.dumps(payload))
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )

    with pytest.raises(
        module.MutationVerificationError,
        match="expected failure marker matched 0 source locations",
    ):
        module.run_mutation(tmp_path, spec)


def test_mutation_runner_rejects_duplicate_expected_failure_markers(tmp_path: Path) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "value = 1  # MUTATION_TARGET\n")
    payload = json.loads(notebook.read_text())
    payload["cells"][1]["source"] += "# ANSWER_CHECK\n"
    notebook.write_text(json.dumps(payload))
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )

    with pytest.raises(
        module.MutationVerificationError,
        match="expected failure marker matched 2 source locations",
    ):
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


def test_mutation_cli_executes_the_registered_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _mutation_module()
    notebook = tmp_path / "fixture" / "solution.ipynb"
    _write_notebook(notebook, "value = 1  # MUTATION_TARGET\n")
    spec = _spec(
        module,
        search="value = 1  # MUTATION_TARGET",
        replacement="value = 2  # MUTATION_TARGET",
    )
    monkeypatch.setattr(module, "MUTATIONS", (spec,))

    assert module.main(["--root", str(tmp_path)]) == 0
    output = capsys.readouterr()
    assert "fixture-mutation" in output.out
    assert output.err == ""
