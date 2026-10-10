"""Answer-check integrity for B2-022 pinned functions (Plan 027 Task 4).

Every pinned function has an untouched solution that passes and named, plausible wrong
implementations that fail.  Mutants are named-function substitutions in copied solution
notebooks.  The four training functions are additionally driven by an in-process harness
that (a) compares parameters before and after the stated step count and (b) wraps the
model's ``forward`` during the training call, hashing every input row it receives against
the held-out hash set built from the generator's ``HELDOUT_IDS`` and canonical per-row
SHA-256 map.  This is a plain correctness check, not adversarial hardening.
"""

from __future__ import annotations

import ast
import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import nbformat
import pytest
import torch
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"
UNIT_ID = "B2-022-probabilistic-latent-models"
UNIT = BOOK2_ROOT / "units" / UNIT_ID
CI_LOCAL = ROOT / "scripts/ci-local.sh"
GENERATOR = UNIT / "scripts" / "generate_latent_data.py"

# --- named-function mutants -------------------------------------------------------------

KL_DROP_MINUS_ONE = '''def kl_to_standard_normal(mu, logvar):
    if mu.dim() != 2 or logvar.dim() != 2:
        raise ValueError("mu and logvar must be 2-D (B, k)")
    if mu.shape != logvar.shape:
        raise ValueError("mu and logvar shapes differ")
    return 0.5 * (mu ** 2 + logvar.exp() - logvar).sum(dim=1)
'''
KL_SIGMA_FOR_VARIANCE = '''def kl_to_standard_normal(mu, logvar):
    if mu.dim() != 2 or logvar.dim() != 2:
        raise ValueError("mu and logvar must be 2-D (B, k)")
    if mu.shape != logvar.shape:
        raise ValueError("mu and logvar shapes differ")
    return 0.5 * (mu ** 2 + torch.exp(0.5 * logvar) - logvar - 1).sum(dim=1)
'''
REPARAM_VARIANCE_AS_STD = '''def reparameterize(mu, logvar, eps):
    if not (mu.shape == logvar.shape == eps.shape):
        raise ValueError("mu, logvar, and eps must have identical shapes")
    return mu + torch.exp(logvar) * eps
'''
REPARAM_SAMPLED_INSIDE = '''def reparameterize(mu, logvar, eps):
    if not (mu.shape == logvar.shape == eps.shape):
        raise ValueError("mu, logvar, and eps must have identical shapes")
    return torch.normal(mu.detach(), torch.exp(0.5 * logvar.detach()))
'''
ELBO_KL_SIGN_FLIPPED = '''def negative_elbo(x, x_hat, mu, logvar):
    recon, kl = negative_elbo_terms(x, x_hat, mu, logvar)
    return (recon - kl).mean()
'''
ELBO_MEAN_OVER_FEATURES = '''def negative_elbo(x, x_hat, mu, logvar):
    _check_inputs(x, x_hat, mu, logvar)
    recon = 0.5 * ((x - x_hat) ** 2).mean(dim=1)
    kl = 0.5 * (mu ** 2 + logvar.exp() - logvar - 1).sum(dim=1)
    return (recon + kl).mean()
'''


def _ae_trainer(name: str, steps: int, *, step: bool, leak: bool) -> str:
    batch_line = "    batch = torch.cat([batch, heldout_rows()])\n" if leak else ""
    step_line = "        optimizer.step()\n" if step else ""
    return (
        f"def {name}(model, batch, optimizer):\n"
        f"{batch_line}"
        "    trace = []\n"
        f"    for _ in range({steps}):\n"
        "        optimizer.zero_grad(set_to_none=True)\n"
        "        reconstruction = model(batch)\n"
        "        loss = F.mse_loss(reconstruction, batch)\n"
        "        trace.append(loss.item())\n"
        "        loss.backward()\n"
        f"{step_line}"
        "    return trace\n"
    )


def _vae_trainer(name: str, steps: int, *, step: bool, leak: bool) -> str:
    batch_line = "    batch = torch.cat([batch, heldout_rows()])\n" if leak else ""
    step_line = "        optimizer.step()\n" if step else ""
    if name == "train_vae":
        record = (
            "        recon, kl = negative_elbo_terms(batch, x_hat, mu, logvar)\n"
            "        loss = (recon + kl).mean()\n"
            '        trace.append({"total": loss.item(), "recon": recon.mean().item(), '
            '"kl": kl.mean().item()})\n'
        )
    else:
        record = (
            "        loss = negative_elbo(batch, x_hat, mu, logvar)\n"
            "        trace.append(loss.item())\n"
        )
    return (
        f"def {name}(model, batch, optimizer):\n"
        f"{batch_line}"
        "    eps_generator = torch.Generator().manual_seed(SEED)\n"
        "    trace = []\n"
        f"    for _ in range({steps}):\n"
        "        eps = torch.randn(batch.shape[0], 2, generator=eps_generator)\n"
        "        optimizer.zero_grad(set_to_none=True)\n"
        "        x_hat, mu, logvar = model(batch, eps)\n"
        f"{record}"
        "        loss.backward()\n"
        f"{step_line}"
        "    return trace\n"
    )


# (practice, function, factory expression, lr, steps, trainer builder)
TRAINING = {
    "p17": ("train_autoencoder", "TinyAutoencoder()", 0.01, 400, _ae_trainer),
    "p18": ("train_linear_autoencoder", "LinearAutoencoder()", 0.02, 1500, _ae_trainer),
    "p19": ("train_vae", "TinyVAE()", 0.01, 600, _vae_trainer),
    "p20": (
        "train_vae_for_sampling",
        "TinyVAE(in_dim=2, hidden=16, latent=2)",
        0.01,
        800,
        _vae_trainer,
    ),
}
DATASETS = {"p17": "mixture8d", "p18": "lowrank8d", "p19": "mixture8d", "p20": "mixture2d"}


def _training_mutant(practice: str, kind: str) -> tuple[str, str]:
    function, _, _, steps, builder = TRAINING[practice]
    if kind == "no-op-step":
        return function, builder(function, steps, step=False, leak=False)
    return function, builder(function, steps, step=True, leak=True)


# (practice, function, mutant source, failing cell, exception name)
ANSWER_CHECK = "answer-check"
SOLUTION_CELL = "solution"
FUNCTION_VARIANTS = (
    pytest.param("p09", "kl_to_standard_normal", KL_DROP_MINUS_ONE, ANSWER_CHECK, "AssertionError", id="p09-drop-minus-one"),
    pytest.param("p09", "kl_to_standard_normal", KL_SIGMA_FOR_VARIANCE, ANSWER_CHECK, "AssertionError", id="p09-sigma-for-variance"),
    pytest.param("p11", "reparameterize", REPARAM_VARIANCE_AS_STD, ANSWER_CHECK, "AssertionError", id="p11-exp-logvar-as-std"),
    pytest.param("p11", "reparameterize", REPARAM_SAMPLED_INSIDE, SOLUTION_CELL, "RuntimeError", id="p11-sampled-inside-detached"),
    pytest.param("p19", "negative_elbo", ELBO_KL_SIGN_FLIPPED, ANSWER_CHECK, "AssertionError", id="p19-kl-sign-flipped"),
    pytest.param("p19", "negative_elbo", ELBO_MEAN_OVER_FEATURES, ANSWER_CHECK, "AssertionError", id="p19-mean-over-features"),
    *(
        pytest.param(
            practice,
            *_training_mutant(practice, "no-op-step"),
            ANSWER_CHECK,
            "AssertionError",
            id=f"{practice}-no-op-step",
        )
        for practice in TRAINING
    ),
    *(
        pytest.param(
            practice,
            *_training_mutant(practice, "heldout-in-training"),
            SOLUTION_CELL,
            "AssertionError",
            id=f"{practice}-heldout-in-training",
        )
        for practice in TRAINING
    ),
)
PRACTICES = ("p09", "p11", "p17", "p18", "p19", "p20")


# --- notebook helpers -------------------------------------------------------------------


def _working_notebook(tmp_path: Path, practice: str) -> Path:
    working_unit = tmp_path / UNIT_ID
    shutil.copytree(UNIT, working_unit, ignore=shutil.ignore_patterns("__pycache__"))
    return working_unit / "practice" / f"{practice}_solution.ipynb"


def _replace_function(source: str, name: str, replacement: str) -> str | None:
    tree = ast.parse(source)
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if not matches:
        return None
    assert len(matches) == 1
    node = matches[0]
    lines = source.splitlines(keepends=True)
    start = node.lineno - 1 - len(node.decorator_list)
    return "".join(lines[:start]) + replacement + "".join(lines[node.end_lineno :])


def _substitute(notebook_path: Path, name: str, replacement: str) -> None:
    notebook = nbformat.read(notebook_path, as_version=4)
    replaced = 0
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        updated = _replace_function(str(cell.source), name, replacement)
        if updated is not None:
            cell.source = updated
            replaced += 1
    assert replaced == 1, f"expected one definition of {name} in {notebook_path.name}"
    nbformat.write(notebook, notebook_path)


def _client(notebook_path: Path):
    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )
    return notebook, client


# --- in-process training harness --------------------------------------------------------


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("b2_022_latent_generator", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _heldout_hashes(dataset: str) -> frozenset[str]:
    generator = _load_generator()
    hashes = generator.ROW_SHA256[dataset]
    return frozenset(hashes[index] for index in generator.HELDOUT_IDS[dataset])


def _definitions_only(source: str) -> str:
    """Keep imports, defs, classes, and ALL-CAPS constants; drop training side effects."""
    tree = ast.parse(source)
    kept: list[ast.stmt] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef)):
            kept.append(node)
        elif isinstance(node, ast.Assign):
            names = [
                element
                for target in node.targets
                for element in (target.elts if isinstance(target, ast.Tuple) else [target])
            ]
            if all(isinstance(item, ast.Name) and item.id.isupper() for item in names):
                kept.append(node)
    return ast.unparse(ast.Module(body=kept, type_ignores=[]))


def _solution_namespace(
    notebook_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    notebook = nbformat.read(notebook_path, as_version=4)
    code_cells = [str(cell.source) for cell in notebook.cells if cell.cell_type == "code"]
    supplied, solution = code_cells[0], code_cells[1]
    monkeypatch.chdir(notebook_path.parent)
    namespace: dict[str, Any] = {"__name__": f"b2_022_{notebook_path.stem}"}
    exec(compile(supplied, f"{notebook_path.name}:supplied", "exec"), namespace)  # noqa: S102
    definitions = _definitions_only(solution)
    exec(compile(definitions, f"{notebook_path.name}:defs", "exec"), namespace)  # noqa: S102
    return namespace


def _run_training_harness(
    practice: str, namespace: dict[str, Any]
) -> dict[str, Any]:
    function, factory, lr, _, _ = TRAINING[practice]
    generator = _load_generator()
    held = _heldout_hashes(DATASETS[practice])
    torch.manual_seed(namespace["SEED"])
    model = eval(factory, namespace)  # pinned literal constructor expression
    optimizer = torch.optim.Adam(
        model.parameters(), lr=lr, betas=(0.9, 0.999), eps=1e-8, weight_decay=0
    )
    before = {name: p.detach().clone() for name, p in model.named_parameters()}
    seen: list[str] = []
    original_forward = model.forward

    def wrapped_forward(batch, *args, **kwargs):
        seen.extend(
            generator.canonical_row_sha256(row.detach().cpu().numpy()) for row in batch
        )
        return original_forward(batch, *args, **kwargs)

    model.forward = wrapped_forward
    try:
        trace = namespace[function](model, namespace["train_rows"](), optimizer)
    finally:
        model.forward = original_forward
    changed = [
        name
        for name, p in model.named_parameters()
        if not torch.equal(p.detach(), before[name])
    ]
    return {
        "steps": len(trace),
        "changed": changed,
        "rows_seen": len(seen),
        "heldout_seen": sorted(set(seen) & held),
    }


@pytest.fixture
def single_thread_torch():
    threads = torch.get_num_threads()
    yield
    torch.set_num_threads(threads)


# --- tests ------------------------------------------------------------------------------


def test_heldout_hash_set_comes_from_generator_ids_and_canonical_map() -> None:
    generator = _load_generator()
    for dataset in ("mixture2d", "mixture8d", "lowrank8d"):
        held = _heldout_hashes(dataset)
        assert len(held) == len(generator.HELDOUT_IDS[dataset]) == 12
        train = {generator.ROW_SHA256[dataset][i] for i in generator.TRAIN_IDS[dataset]}
        assert held.isdisjoint(train) and len(train) == 48


@pytest.mark.parametrize("practice", PRACTICES)
def test_untouched_latent_model_answer_check_passes(tmp_path: Path, practice: str) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _, client = _client(notebook_path)
    client.execute()


@pytest.mark.parametrize(
    ("practice", "function", "replacement", "where", "ename"), FUNCTION_VARIANTS
)
def test_named_function_wrong_implementation_fails(
    tmp_path: Path,
    practice: str,
    function: str,
    replacement: str,
    where: str,
    ename: str,
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _substitute(notebook_path, function, replacement)
    notebook, client = _client(notebook_path)
    with pytest.raises(CellExecutionError):
        client.execute()
    failures = [
        (index, output.get("ename"))
        for index, cell in enumerate(notebook.cells)
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    assert len(failures) == 1, failures
    index, observed = failures[0]
    assert observed == ename
    if where == ANSWER_CHECK:
        assert index == len(notebook.cells) - 1
        assert notebook.cells[-2].source.strip() == "### Answer check"
    else:
        assert f"def {function}(" in notebook.cells[index].source


@pytest.mark.parametrize("practice", tuple(TRAINING))
def test_shipped_training_function_updates_and_sees_only_training_rows(
    tmp_path: Path,
    practice: str,
    monkeypatch: pytest.MonkeyPatch,
    single_thread_torch: None,
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    namespace = _solution_namespace(notebook_path, monkeypatch)
    result = _run_training_harness(practice, namespace)
    steps = TRAINING[practice][3]
    assert result["steps"] == steps
    assert result["changed"], "no parameter changed after the stated step count"
    assert result["rows_seen"] == steps * 48
    assert result["heldout_seen"] == []


@pytest.mark.parametrize("practice", tuple(TRAINING))
def test_no_op_optimizer_step_is_detected_by_parameter_comparison(
    tmp_path: Path,
    practice: str,
    monkeypatch: pytest.MonkeyPatch,
    single_thread_torch: None,
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    function, mutant = _training_mutant(practice, "no-op-step")
    _substitute(notebook_path, function, mutant)
    namespace = _solution_namespace(notebook_path, monkeypatch)
    result = _run_training_harness(practice, namespace)
    assert result["steps"] == TRAINING[practice][3]
    assert result["changed"] == []
    assert result["heldout_seen"] == []


@pytest.mark.parametrize("practice", tuple(TRAINING))
def test_heldout_rows_in_training_are_detected_at_forward(
    tmp_path: Path,
    practice: str,
    monkeypatch: pytest.MonkeyPatch,
    single_thread_torch: None,
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    function, mutant = _training_mutant(practice, "heldout-in-training")
    _substitute(notebook_path, function, mutant)
    namespace = _solution_namespace(notebook_path, monkeypatch)
    result = _run_training_harness(practice, namespace)
    assert result["changed"]
    assert len(result["heldout_seen"]) == 12
    assert result["heldout_seen"] == sorted(_heldout_hashes(DATASETS[practice]))


def test_book2_ci_runs_latent_model_integrity_suite() -> None:
    source = CI_LOCAL.read_text(encoding="utf-8")
    language = "uv run pytest -q tests/test_language_transformer_checks.py\n"
    latent = "uv run pytest -q tests/test_latent_model_checks.py\n"
    assert language + latent in source
