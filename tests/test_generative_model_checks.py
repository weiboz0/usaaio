"""Answer-check integrity for B2-023 pinned functions (Plan 028 Task 4).

Every pinned function has an untouched solution that passes and a named, plausible
wrong implementation that fails its answer check.  Mutants are named-function
substitutions in copied solution notebooks.  ``gan_step`` is additionally driven through
its pinned ``d_step`` helper alone, asserting that every generator parameter's ``.grad``
is ``None`` afterwards.  The four training functions (p17-p20) also get a no-op
optimizer-step mutant and a held-out-row mutant, checked by an in-process harness that
wraps the practice's named clean-row seam (the discriminator's ``forward``, ``q_sample``'s
``x0``, or the frozen ``encode``) only for the duration of the ``train_*`` call and hashes
every clean row against the held-out hash set built from the generator's ``HELDOUT_IDS``
and canonical per-row SHA-256 map.  This is a plain correctness check, not adversarial
hardening.
"""

from __future__ import annotations

import ast
import importlib.util
import shutil
import sys
from collections.abc import Callable
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
UNIT_ID = "B2-023-generative-models-diffusion"
UNIT = BOOK2_ROOT / "units" / UNIT_ID
CI_LOCAL = ROOT / "scripts/ci-local.sh"
GENERATOR = UNIT / "scripts" / "generate_generative_data.py"

# --- named-function mutants (one per pinned function) -----------------------------------

DISCRIMINATOR_LABELS_SWAPPED = '''def discriminator_loss(real_logits, fake_logits):
    _check_logits(real_logits, fake_logits)
    return (F.binary_cross_entropy_with_logits(real_logits, torch.zeros_like(real_logits))
            + F.binary_cross_entropy_with_logits(fake_logits, torch.ones_like(fake_logits)))
'''
GENERATOR_SATURATING = '''def generator_loss(fake_logits):
    _check_logits(fake_logits)
    return -F.binary_cross_entropy_with_logits(fake_logits, torch.zeros_like(fake_logits))
'''
D_STEP_MISSING_DETACH = '''def d_step(G, D, opt_d, real, z):
    opt_d.zero_grad(set_to_none=True)
    real_logits = D(real)
    fake_logits = D(G(z))
    loss = discriminator_loss(real_logits, fake_logits)
    loss.backward()
    opt_d.step()
    return loss.item()
'''
MODE_COVERAGE_STRICT_RADIUS = '''def mode_coverage(samples, centers, radius):
    _check(samples, centers, radius)
    counts = _counts(samples, centers, radius, strict=True)
    need = math.ceil(samples.shape[0] / (8 * centers.shape[0]))
    return counts, int((counts >= need).sum().item())
'''
MAKE_SCHEDULE_OFF_BY_ONE_ENDPOINT = '''def make_schedule(T, beta_1, beta_T):
    if not isinstance(T, int) or isinstance(T, bool) or T < 2:
        raise ValueError("T must be an int >= 2")
    if not (0 < beta_1 <= beta_T < 1):
        raise ValueError("need 0 < beta_1 <= beta_T < 1")
    beta = torch.zeros(T + 1, dtype=torch.float64)
    beta[1:] = torch.linspace(beta_1, beta_T, T + 1, dtype=torch.float64)[1:]
    alpha = 1 - beta
    alpha_bar = torch.cumprod(alpha, dim=0)
    beta_tilde = torch.zeros(T + 1, dtype=torch.float64)
    beta_tilde[1:] = (1 - alpha_bar[:-1]) / (1 - alpha_bar[1:]) * beta[1:]
    return {"beta": beta, "alpha": alpha, "alpha_bar": alpha_bar, "beta_tilde": beta_tilde}
'''
Q_SAMPLE_ALPHA_FOR_ALPHA_BAR = '''def q_sample(x0, t, eps, alpha_bar):
    if x0.shape != eps.shape:
        raise ValueError("x0 and eps must have the same shape")
    if (not isinstance(t, torch.Tensor) or t.dtype != torch.int64 or t.dim() != 1
            or x0.dim() != 2 or t.shape[0] != x0.shape[0]):
        raise ValueError("t must be an int64 tensor of shape (B,)")
    T = alpha_bar.shape[0] - 1
    if bool((t < 1).any()) or bool((t > T).any()):
        raise ValueError("timesteps must lie in 1..T")
    a = (alpha_bar[t] / alpha_bar[t - 1]).to(x0.dtype).unsqueeze(1)
    return a.sqrt() * x0 + (1 - a).sqrt() * eps
'''
DDPM_LOSS_X0_TARGET = '''def ddpm_loss(model, x0, t, eps, alpha_bar):
    T = alpha_bar.shape[0] - 1
    x_t = q_sample(x0, t, eps, alpha_bar)
    t_scaled = (t.to(x0.dtype) / T).unsqueeze(1)
    eps_hat = model(x_t, t_scaled)
    if eps_hat.shape != eps.shape:
        raise ValueError("model output must have the shape of eps")
    return ((eps_hat - x0) ** 2).mean()
'''
P_SAMPLE_NOISY_FINAL_STEP = '''def p_sample(model, x_t, t, z, schedule):
    T = schedule["beta"].shape[0] - 1
    if not isinstance(t, int) or isinstance(t, bool) or not 1 <= t <= T:
        raise ValueError("t must be an int in 1..T")
    B = x_t.shape[0]
    eps_hat = model(x_t, torch.full((B, 1), t / T, dtype=x_t.dtype))
    beta_t = schedule["beta"][t].item()
    alpha_t = schedule["alpha"][t].item()
    alpha_bar_t = schedule["alpha_bar"][t].item()
    mean = (x_t - beta_t / math.sqrt(1 - alpha_bar_t) * eps_hat) / math.sqrt(alpha_t)
    if t == 1:
        return mean + math.sqrt(beta_t) * z
    return mean + math.sqrt(schedule["beta_tilde"][t].item()) * z
'''
SAMPLE_LOOP_ASCENDING = '''def sample_loop(model, x_T, noises, schedule):
    T = schedule["beta"].shape[0] - 1
    if tuple(noises.shape) != (T, *x_T.shape):
        raise ValueError("noises must have shape (T, *x_T.shape)")
    x = x_T
    for t in range(1, T + 1):
        x = p_sample(model, x, t, noises[t - 1], schedule)
    return x
'''
CFG_SIGN_FLIPPED = '''def cfg_combine(eps_uncond, eps_cond, w):
    if eps_uncond.shape != eps_cond.shape:
        raise ValueError("eps_uncond and eps_cond must have the same shape")
    return eps_uncond - w * (eps_cond - eps_uncond)
'''

# (practice, substituted function, mutant source); ``gan_step``'s mutant lives in its
# pinned ``d_step`` helper.
FUNCTION_MUTANTS = (
    pytest.param("p06", "generator_loss", GENERATOR_SATURATING, id="generator_loss-saturating"),
    pytest.param("p06", "discriminator_loss", DISCRIMINATOR_LABELS_SWAPPED, id="discriminator_loss-labels-swapped"),
    pytest.param("p07", "d_step", D_STEP_MISSING_DETACH, id="gan_step-d_step-missing-detach"),
    pytest.param("p08", "mode_coverage", MODE_COVERAGE_STRICT_RADIUS, id="mode_coverage-strict-radius"),
    pytest.param("p09", "make_schedule", MAKE_SCHEDULE_OFF_BY_ONE_ENDPOINT, id="make_schedule-off-by-one-endpoint"),
    pytest.param("p09", "q_sample", Q_SAMPLE_ALPHA_FOR_ALPHA_BAR, id="q_sample-alpha-for-alpha-bar"),
    pytest.param("p10", "ddpm_loss", DDPM_LOSS_X0_TARGET, id="ddpm_loss-x0-target"),
    pytest.param("p11", "p_sample", P_SAMPLE_NOISY_FINAL_STEP, id="p_sample-noisy-final-step"),
    pytest.param("p11", "sample_loop", SAMPLE_LOOP_ASCENDING, id="sample_loop-ascending"),
    pytest.param("p12", "cfg_combine", CFG_SIGN_FLIPPED, id="cfg_combine-sign-flipped"),
)
PINNED_FUNCTIONS = {
    "discriminator_loss", "generator_loss", "gan_step", "mode_coverage", "make_schedule",
    "q_sample", "ddpm_loss", "p_sample", "sample_loop", "cfg_combine",
}

# --- training mutants -------------------------------------------------------------------


def _gan_trainer(*, step: bool, leak: bool) -> str:
    leak_line = "    batch = torch.cat([batch, heldout_rows()])\n" if leak else ""
    if step:
        body = "        trace.append(gan_step(G, D, opt_g, opt_d, batch, z))\n"
    else:
        body = (
            "        opt_d.zero_grad(set_to_none=True)\n"
            "        d_loss = discriminator_loss(D(batch), D(G(z).detach()))\n"
            "        d_loss.backward()\n"
            "        opt_g.zero_grad(set_to_none=True)\n"
            "        g_loss = generator_loss(D(G(z)))\n"
            "        g_loss.backward()\n"
            "        trace.append((d_loss.item(), g_loss.item()))\n"
        )
    return (
        "def train_gan(G, D, opt_g, opt_d, batch):\n"
        f"{leak_line}"
        "    noise_generator = torch.Generator().manual_seed(SEED)\n"
        "    trace = []\n"
        "    for _ in range(600):\n"
        "        z = torch.randn(batch.shape[0], 2, generator=noise_generator)\n"
        f"{body}"
        "    return trace\n"
    )


def _ddpm_trainer(*, step: bool, leak: bool) -> str:
    leak_line = "    batch = torch.cat([batch, heldout_rows()])\n" if leak else ""
    step_line = "        optimizer.step()\n" if step else ""
    return (
        "def train_ddpm(model, batch, optimizer):\n"
        f"{leak_line}"
        "    noise_generator = torch.Generator().manual_seed(SEED)\n"
        "    trace = []\n"
        "    for _ in range(1500):\n"
        "        t = torch.randint(1, T + 1, (batch.shape[0],), generator=noise_generator)\n"
        "        eps = torch.randn(batch.shape[0], 2, generator=noise_generator)\n"
        "        optimizer.zero_grad(set_to_none=True)\n"
        '        loss = ddpm_loss(model, batch, t, eps, SCHEDULE["alpha_bar"])\n'
        "        loss.backward()\n"
        f"{step_line}"
        "        trace.append(loss.item())\n"
        "    return trace\n"
    )


def _latent_trainer(*, step: bool, leak: bool) -> str:
    leak_lines = (
        "    rows = torch.cat([rows, heldout_rows()])\n"
        "    labels = torch.cat([labels, heldout_labels()])\n"
        if leak
        else ""
    )
    step_line = "        optimizer.step()\n" if step else ""
    return (
        "def train_latent_diffusion(model, batch, optimizer):\n"
        "    rows, labels = batch\n"
        f"{leak_lines}"
        "    z0 = encode(rows) * LATENT_SCALE\n"
        "    B = z0.shape[0]\n"
        "    noise_generator = torch.Generator().manual_seed(SEED)\n"
        "    trace = []\n"
        "    for _ in range(1500):\n"
        "        t = torch.randint(1, 51, (B,), generator=noise_generator)\n"
        "        eps = torch.randn(B, 2, generator=noise_generator)\n"
        "        keep = torch.rand(B, generator=noise_generator) >= 0.2\n"
        "        optimizer.zero_grad(set_to_none=True)\n"
        '        z_t = q_sample(z0, t, eps, SCHEDULE["alpha_bar"])\n'
        "        eps_hat = model(z_t, (t.to(torch.float32) / 50).unsqueeze(1), labels, keep)\n"
        "        loss = ((eps_hat - eps) ** 2).mean()\n"
        "        loss.backward()\n"
        f"{step_line}"
        "        trace.append(loss.item())\n"
        "    return trace\n"
    )


# practice -> (train function, steps, dataset, seam, builder)
TRAINING: dict[str, tuple[str, int, str, str, Callable[..., str]]] = {
    "p17": ("train_gan", 600, "mixture2d", "discriminator forward", _gan_trainer),
    "p18": ("train_ddpm", 1500, "mixture2d", "q_sample x0", _ddpm_trainer),
    "p19": ("train_ddpm", 1500, "mixture2d", "q_sample x0", _ddpm_trainer),
    "p20": ("train_latent_diffusion", 1500, "latent4d", "frozen encode", _latent_trainer),
}
TRAINING_KINDS = ("no-op-step", "heldout-in-training")


def _training_mutant(practice: str, kind: str) -> tuple[str, str]:
    function, _, _, _, builder = TRAINING[practice]
    if kind == "no-op-step":
        return function, builder(step=False, leak=False)
    return function, builder(step=True, leak=True)


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


def _assert_answer_check_fails(notebook_path: Path) -> None:
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
    assert observed == "AssertionError"
    assert index == len(notebook.cells) - 1
    assert notebook.cells[-2].source.strip() == "### Answer check"


# --- in-process harness -----------------------------------------------------------------


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("b2_023_generative_generator", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _split_hashes(dataset: str) -> tuple[frozenset[str], frozenset[str]]:
    generator = _load_generator()
    hashes = generator.ROW_SHA256[dataset]
    return (
        frozenset(hashes[index] for index in generator.TRAIN_IDS[dataset]),
        frozenset(hashes[index] for index in generator.HELDOUT_IDS[dataset]),
    )


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
    namespace: dict[str, Any] = {"__name__": f"b2_023_{notebook_path.stem}"}
    exec(compile(supplied, f"{notebook_path.name}:supplied", "exec"), namespace)  # noqa: S102
    definitions = _definitions_only(solution)
    exec(compile(definitions, f"{notebook_path.name}:defs", "exec"), namespace)  # noqa: S102
    return namespace


def _adam(parameters, lr: float):
    return torch.optim.Adam(parameters, lr=lr, betas=(0.9, 0.999), eps=1e-8, weight_decay=0)


def _snapshot(*modules: torch.nn.Module) -> list[torch.Tensor]:
    return [p.detach().clone() for module in modules for p in module.parameters()]


def _run_training_harness(practice: str, namespace: dict[str, Any]) -> dict[str, Any]:
    """Arm the named clean-row seam only while ``train_*`` runs, then disarm it."""
    function, _, dataset, _, _ = TRAINING[practice]
    generator = _load_generator()
    seen: list[str] = []

    def record(rows: torch.Tensor) -> None:
        seen.extend(
            generator.canonical_row_sha256(row.detach().cpu().numpy()) for row in rows
        )

    torch.manual_seed(namespace["SEED"])
    if practice == "p17":
        G, D = namespace["make_generator"](), namespace["make_discriminator"]()
        modules: tuple[torch.nn.Module, ...] = (G, D)
        args = (G, D, _adam(G.parameters(), 5e-4), _adam(D.parameters(), 2e-3))
        original_forward = D.forward

        def arm() -> None:
            def recording_forward(x):
                record(x)
                return original_forward(x)

            D.forward = recording_forward

        def disarm() -> None:
            del D.forward

        batch: Any = namespace["train_rows"]()
    else:
        if practice == "p20":
            model = namespace["LatentDenoiser"]()
            optimizer = _adam(model.parameters(), 1e-2)
            seam = "encode"
            batch = (namespace["train_rows"](), namespace["train_labels"]())
        else:
            model = namespace["Denoiser"]()
            optimizer = _adam(model.parameters(), 1e-3)
            seam = "q_sample"
            batch = namespace["train_rows"]()
        modules = (model,)
        args = (model,)
        trailing = (optimizer,)
        original_seam = namespace[seam]

        def arm() -> None:
            def recording_seam(x, *rest):
                record(x)
                return original_seam(x, *rest)

            namespace[seam] = recording_seam

        def disarm() -> None:
            namespace[seam] = original_seam

    before = _snapshot(*modules)
    arm()
    try:
        if practice == "p17":
            trace = namespace[function](*args, batch)
        else:
            trace = namespace[function](*args, batch, *trailing)
    finally:
        disarm()
    if practice == "p17":
        assert "forward" not in vars(D)
    else:
        assert namespace[seam] is original_seam
    after = _snapshot(*modules)
    train_hashes, held_hashes = _split_hashes(dataset)
    return {
        "steps": len(trace),
        "changed": any(not torch.equal(a, b) for a, b in zip(before, after, strict=True)),
        "seen": set(seen),
        "train_hashes": train_hashes,
        "heldout_seen": sorted(set(seen) & held_hashes),
        "heldout_all": sorted(held_hashes),
    }


@pytest.fixture
def single_thread_torch():
    threads = torch.get_num_threads()
    dtype = torch.get_default_dtype()
    torch.set_default_dtype(torch.float32)  # notebook kernels start with float32 defaults
    yield
    torch.set_default_dtype(dtype)
    torch.set_num_threads(threads)


# --- tests ------------------------------------------------------------------------------


def test_mutant_table_covers_all_ten_pinned_functions() -> None:
    names = {param.values[1] for param in FUNCTION_MUTANTS}
    covered = (names - {"d_step"}) | ({"gan_step"} if "d_step" in names else set())
    assert covered == PINNED_FUNCTIONS
    assert len(FUNCTION_MUTANTS) == 10


def test_heldout_hash_sets_come_from_generator_ids_and_canonical_map() -> None:
    generator = _load_generator()
    for dataset, (n_train, n_held) in {"mixture2d": (256, 64), "latent4d": (192, 48)}.items():
        train, held = _split_hashes(dataset)
        assert len(held) == len(generator.HELDOUT_IDS[dataset]) == n_held
        assert len(train) == n_train and held.isdisjoint(train)


@pytest.mark.parametrize(
    "practice", ("p06", "p07", "p08", "p09", "p10", "p11", "p12", "p17", "p18", "p19", "p20")
)
def test_untouched_generative_answer_check_passes(tmp_path: Path, practice: str) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _, client = _client(notebook_path)
    client.execute()


@pytest.mark.parametrize(("practice", "function", "replacement"), FUNCTION_MUTANTS)
def test_named_function_wrong_implementation_fails_answer_check(
    tmp_path: Path, practice: str, function: str, replacement: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _substitute(notebook_path, function, replacement)
    _assert_answer_check_fails(notebook_path)


@pytest.mark.parametrize("mutant", (False, True), ids=("untouched", "missing-detach"))
def test_d_step_alone_leaves_every_generator_grad_none(
    tmp_path: Path,
    mutant: bool,
    monkeypatch: pytest.MonkeyPatch,
    single_thread_torch: None,
) -> None:
    notebook_path = _working_notebook(tmp_path, "p07")
    if mutant:
        _substitute(notebook_path, "d_step", D_STEP_MISSING_DETACH)
    namespace = _solution_namespace(notebook_path, monkeypatch)
    G, D, _, opt_d = namespace["make_setup"]()
    namespace["d_step"](G, D, opt_d, namespace["REAL"], namespace["Z"])
    grads_none = all(p.grad is None for p in G.parameters())
    assert grads_none is (not mutant)


@pytest.mark.parametrize("kind", TRAINING_KINDS)
@pytest.mark.parametrize("practice", tuple(TRAINING))
def test_training_mutant_fails_answer_check(tmp_path: Path, practice: str, kind: str) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    function, mutant = _training_mutant(practice, kind)
    _substitute(notebook_path, function, mutant)
    _assert_answer_check_fails(notebook_path)


@pytest.mark.parametrize("practice", tuple(TRAINING))
def test_shipped_training_function_updates_and_seam_sees_only_training_rows(
    tmp_path: Path,
    practice: str,
    monkeypatch: pytest.MonkeyPatch,
    single_thread_torch: None,
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    namespace = _solution_namespace(notebook_path, monkeypatch)
    result = _run_training_harness(practice, namespace)
    assert result["steps"] == TRAINING[practice][1]
    assert result["changed"], "no parameter changed after the stated step count"
    assert result["heldout_seen"] == []
    assert result["train_hashes"] <= result["seen"]


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
    assert result["steps"] == TRAINING[practice][1]
    assert not result["changed"]
    assert result["heldout_seen"] == []


@pytest.mark.parametrize("practice", tuple(TRAINING))
def test_heldout_rows_in_training_are_detected_at_the_named_seam(
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
    assert result["heldout_seen"] == result["heldout_all"]


def test_book2_ci_runs_generative_model_integrity_suite() -> None:
    source = CI_LOCAL.read_text(encoding="utf-8")
    latent = "uv run pytest -q tests/test_latent_model_checks.py\n"
    generative = "uv run pytest -q tests/test_generative_model_checks.py\n"
    assert latent + generative in source
