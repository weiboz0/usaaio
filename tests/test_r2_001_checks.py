"""Answer-check integrity for mock test r2-001 (Plan 024 Task 4).

Lightweight correctness checks, not anti-cheat hardening.  Every mutant edits an
in-memory copy of a published reference solution and executes it end to end:

* P1 named-function mutants: causal mask omitted, targets not shifted, sinusoidal
  sin/cos swapped;
* P3 named-function mutants: KL sign flipped, beta applied to the reconstruction
  instead of the KL (run at the statement's beta = 2, where it is detectable);
* open-ended leakage mutants route validation rows into ``fit``; the named seam
  (``split_of`` recorded inside ``fit`` for P2/P5, ``record_seam`` at the
  feature-extraction step for P4) sees them and the final answer check rejects them;
* open-ended protocol mutants call ``final_test_score`` twice (an extra peek with the
  committed baseline predictor) with the inline call-count guards removed, so the
  answer check alone must notice.

Leakage and protocol mutants must fail in the final ``### Answer check`` cell.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"
SOLUTIONS = BOOK2_ROOT / "mocktests" / "r2-001" / "solutions"
CI_LOCAL = ROOT / "scripts" / "ci-local.sh"
ANSWER_CHECK = "### Answer check"

Edit = tuple[str, str]


def _mutated(stem: str, edits: list[Edit]) -> nbformat.NotebookNode:
    notebook = nbformat.read(SOLUTIONS / f"{stem}_solution.ipynb", as_version=4)
    for old, new in edits:
        hits = [cell for cell in notebook.cells if cell.cell_type == "code" and old in cell.source]
        assert len(hits) == 1, f"{stem}: mutation anchor not unique: {old!r}"
        hits[0].source = hits[0].source.replace(old, new, 1)
    return notebook


def _run(notebook: nbformat.NotebookNode) -> tuple[int | None, str | None]:
    """Execute; return (index of the first failing cell, exception name) or (None, None)."""
    previous = os.environ.get("USAAIO_BOOK_ROOT")
    os.environ["USAAIO_BOOK_ROOT"] = str(BOOK2_ROOT)
    try:
        NotebookClient(
            notebook, timeout=300, kernel_name="python3",
            resources={"metadata": {"path": str(SOLUTIONS)}},
        ).execute()
    except CellExecutionError:
        for index, cell in enumerate(notebook.cells):
            for output in cell.get("outputs", []):
                if output.get("output_type") == "error":
                    return index, output.get("ename")
        raise
    finally:
        if previous is None:
            os.environ.pop("USAAIO_BOOK_ROOT", None)
        else:
            os.environ["USAAIO_BOOK_ROOT"] = previous
    return None, None


def _answer_check_index(notebook: nbformat.NotebookNode) -> int:
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "markdown" and cell.source.strip() == ANSWER_CHECK:
            return index + 1
    raise AssertionError("no answer-check cell")


# --- P1 and P3 named-function mutants -------------------------------------------------

FUNCTION_MUTANTS = {
    "p01-causal-mask-omitted": ("p01", [(
        "return torch.tril(torch.ones(n, n, dtype=torch.bool))",
        "return torch.ones(n, n, dtype=torch.bool)",
    )]),
    "p01-targets-not-shifted": ("p01", [(
        "return tokens[:, :-1], tokens[:, 1:]",
        "return tokens[:, :-1], tokens[:, :-1]",
    )]),
    "p01-sin-cos-swapped": ("p01", [(
        "table[:, 0::2] = torch.sin(p * omega)\n    table[:, 1::2] = torch.cos(p * omega)",
        "table[:, 0::2] = torch.cos(p * omega)\n    table[:, 1::2] = torch.sin(p * omega)",
    )]),
    "p03-kl-sign-flipped": ("p03", [(
        "return 0.5 * (mu ** 2 + torch.exp(logvar) - logvar - 1.0).sum(dim=-1)",
        "return -0.5 * (mu ** 2 + torch.exp(logvar) - logvar - 1.0).sum(dim=-1)",
    )]),
    "p03-beta-on-reconstruction": ("p03", [(
        "total = recon_mean + beta * kl_mean",
        "total = beta * recon_mean + kl_mean",
    )]),
}


@pytest.mark.parametrize("name", sorted(FUNCTION_MUTANTS))
def test_named_function_mutant_is_rejected(name):
    stem, edits = FUNCTION_MUTANTS[name]
    failed_at, ename = _run(_mutated(stem, edits))
    assert failed_at is not None, f"{name} was not detected"
    assert ename == "AssertionError", (name, ename)


def test_beta_mutant_needs_beta_other_than_one():
    """At beta = 1 the reconstruction-weighted mutant equals the correct loss; the
    statement's probe and training run use beta = 2, where the two differ."""
    torch = pytest.importorskip("torch")
    x = torch.tensor([[1.0, -1.0, 2.0], [0.0, 3.0, -2.0]], dtype=torch.float64)
    x_hat = torch.tensor([[0.5, -1.0, 1.0], [0.0, 2.0, -2.0]], dtype=torch.float64)
    mu = torch.tensor([[0.5, 0.0], [1.0, -1.0]], dtype=torch.float64)
    logvar = torch.tensor([[0.0, 0.0], [0.0, 0.6931471805599453]], dtype=torch.float64)
    recon = (0.5 * (x - x_hat) ** 2).sum(dim=-1).mean()
    kl = (0.5 * (mu ** 2 + torch.exp(logvar) - logvar - 1.0).sum(dim=-1)).mean()
    assert float(recon + 1.0 * kl) == pytest.approx(float(1.0 * recon + kl), abs=1e-15)
    assert abs(float(recon + 2.0 * kl) - float(2.0 * recon + kl)) > 1e-3   # 0.0767 vs atol 1e-6


# --- open-ended leakage and protocol mutants ------------------------------------------

def _second_call(task: str) -> list[Edit]:
    """An extra test-set peek (the committed baseline's predictor, which uses no budget
    steps) before the real call, with both inline call-count guards removed."""
    return [
        (
            f'assert r2_001_data.test_call_count("{task}") == 0\n',
            f'r2_001_data.final_test_score(r2_001_data._baseline_predict_fn("{task}"), task="{task}")\n',
        ),
        (
            f'task="{task}")\nassert r2_001_data.test_call_count("{task}") == 1\n',
            f'task="{task}")\n',
        ),
    ]


OPEN_ENDED_MUTANTS = {
    "p02-leak-validation-into-fit": ("p02", [
        ("fit(torch.cat([x_train, x_sim]), torch.cat([y_train, y_sim]))",
         "fit(torch.cat([x_train, x_sim, x_val]), torch.cat([y_train, y_sim, y_val]))"),
        ('assert seam <= {"train", None} and "val" not in seam and "test" not in seam\n', ""),
    ]),
    "p02-final-test-score-twice": ("p02", _second_call("heat")),
    "p04-leak-validation-into-pool": ("p04", [
        ("history = fit(x_lab, y_lab, x_pool, rounds=ROUNDS)",
         "history = fit(x_lab, y_lab, torch.cat([x_pool, x_val]), rounds=ROUNDS)"),
        ("assert acc_self >= acc_corr > acc_per_scanner > acc_no_pool\n", ""),
        ('assert seam <= {"train", "unlabelled"} and "val" not in seam and "test" not in seam\n', ""),
    ]),
    "p04-final-test-score-twice": ("p04", _second_call("texture")),
    "p05-leak-validation-into-fit": ("p05", [
        ("fit(torch.cat([f_train, x_sim]), torch.cat([theta_train, y_sim]))",
         "fit(torch.cat([f_train, x_sim, f_val]), torch.cat([theta_train, y_sim, theta_val]))"),
        ('assert seam <= {"train", None} and "val" not in seam and "test" not in seam\n', ""),
    ]),
    "p05-final-test-score-twice": ("p05", _second_call("lorentz")),
}


@pytest.mark.parametrize("name", sorted(OPEN_ENDED_MUTANTS))
def test_open_ended_mutant_fails_the_answer_check(name):
    stem, edits = OPEN_ENDED_MUTANTS[name]
    notebook = _mutated(stem, edits)
    failed_at, ename = _run(notebook)
    assert failed_at == _answer_check_index(notebook), (name, failed_at)
    assert ename == "AssertionError", (name, ename)


def test_suite_is_wired_into_ci_local_step_7():
    text = CI_LOCAL.read_text()
    step7 = text[text.index('step "7/9'):text.index('step "8/9')]
    assert "uv run pytest -q tests/test_r2_001_checks.py" in step7
