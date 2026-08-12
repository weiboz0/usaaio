from __future__ import annotations

import json
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
BOOK1_ROOT = ROOT / "book1"
PRACTICE = BOOK1_ROOT / "units" / "C11-neural-training" / "practice"


def _source(cell: dict[str, object]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def _notebook(problem: str, *, solution: bool) -> dict[str, object]:
    suffix = "_solution" if solution else ""
    return json.loads((PRACTICE / f"{problem}{suffix}.ipynb").read_text())


def _code(problem: str, *, solution: bool) -> str:
    notebook = _notebook(problem, solution=solution)
    return "\n".join(
        _source(cell) for cell in notebook["cells"] if cell["cell_type"] == "code"
    )


def _declared_probe(problem: str, marker: str) -> str:
    statement_code = _code(problem, solution=False)
    return statement_code[statement_code.index(marker) :].strip()


def _execute_solution(
    problem: str,
    replacements: tuple[tuple[str, str], ...] = (),
) -> dict[str, object]:
    notebook = _notebook(problem, solution=True)
    namespace: dict[str, object] = {}
    remaining = dict(replacements)

    for cell_index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = _source(cell)
        for old, new in replacements:
            count = source.count(old)
            if count:
                assert count == 1
                source = source.replace(old, new)
                remaining.pop(old)
        exec(  # noqa: S102 - execute the notebook's actual answer-check cells
            compile(source, f"{problem}_solution.ipynb:cell-{cell_index}", "exec"), namespace
        )

    assert not remaining, f"mutation targets not found: {sorted(remaining)}"
    return namespace


@pytest.mark.parametrize(
    ("problem", "marker"),
    [
        ("p05", "probe_p05 ="),
        ("p06", "probe_logits_p06 ="),
        ("p07", "X_p07 ="),
        ("p08", "X_p08 ="),
        ("p09", "X_p09 ="),
        ("p10", "x_p10 ="),
        ("p14", "logits_p14 ="),
        ("p15", "result_p15 ="),
        ("p21", "rng_p21 ="),
    ],
)
def test_solution_executes_the_declared_statement_probe(problem: str, marker: str) -> None:
    assert _declared_probe(problem, marker) in _code(problem, solution=True)


def test_p04_solution_recomputes_the_revised_squared_dropout_expectation() -> None:
    namespace = _execute_solution("p04")

    assert str(namespace["numerator_expectation_p04"]) == "16/3"
    assert str(namespace["denominator_expectation_p04"]) == "5"
    assert str(namespace["ratio_p04"]) == "16/15"


def test_p09_answer_check_exercises_the_constant_feature_path() -> None:
    source = _code("p09", solution=True)

    assert 'assert result_p09["batch_var_biased"][1] == 0.0' in source
    _execute_solution("p09")


def test_p10_solution_executes_from_a_fresh_default_dtype() -> None:
    torch.set_default_dtype(torch.float32)
    try:
        _execute_solution("p10")
    finally:
        torch.set_default_dtype(torch.float64)


def test_p14_and_p21_pin_independent_fixed_reference_values() -> None:
    for problem in ("p14", "p21"):
        source = _code(problem, solution=True)
        assert f"expected_loss_{problem}" in source
        assert f"expected_probabilities_{problem}" in source
        assert f"expected_gradient_{problem}" in source


@pytest.mark.parametrize(
    "replacements",
    [
        (
            (
                "loss=float(np.mean(np.log(sums[:,0])-shifted[np.arange(z.shape[0]),y]))",
                "loss=float(np.sum(np.log(sums[:,0])-shifted[np.arange(z.shape[0]),y]))",
            ),
            ("gradient/=z.shape[0]", "gradient/=1.0"),
        ),
        (
            (
                "loss=float(np.mean(np.log(sums[:,0])-shifted[np.arange(z.shape[0]),y]))",
                "loss=float(np.sum(np.log(sums[:,0])-shifted[np.arange(z.shape[0]),y])/z.size)",
            ),
            ("gradient/=z.shape[0]", "gradient/=z.size"),
        ),
    ],
    ids=("sum-loss", "one-over-n-times-c"),
)
def test_p14_actual_answer_check_rejects_self_consistent_wrong_normalization(
    replacements: tuple[tuple[str, str], ...],
) -> None:
    with pytest.raises(AssertionError):
        _execute_solution("p14", replacements)


@pytest.mark.parametrize(
    "replacements",
    [
        (
            (
                "return float(np.mean(np.log(np.exp(shifted).sum(axis=1))-shifted[np.arange(z.shape[0]),y]))",
                "return float(np.sum(np.log(np.exp(shifted).sum(axis=1))-shifted[np.arange(z.shape[0]),y]))",
            ),
            ("grad/=len(y)", "grad/=1.0"),
        ),
        (
            (
                "return float(np.mean(np.log(np.exp(shifted).sum(axis=1))-shifted[np.arange(z.shape[0]),y]))",
                "return float(np.sum(np.log(np.exp(shifted).sum(axis=1))-shifted[np.arange(z.shape[0]),y])/z.shape[1])",
            ),
            ("grad/=len(y)", "grad/=z.shape[1]"),
        ),
    ],
    ids=("sum-loss", "one-over-c"),
)
def test_p21_actual_answer_check_rejects_self_consistent_wrong_normalization(
    replacements: tuple[tuple[str, str], ...],
) -> None:
    with pytest.raises(AssertionError):
        _execute_solution("p21", replacements)


def test_p16_prediction_uses_evaluation_mode_without_gradient_tracking() -> None:
    source = _code("p16", solution=True)

    assert "model.eval()\n    with torch.no_grad():\n        predictions =" in source
