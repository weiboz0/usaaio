"""Answer-check integrity for the B2-024 capstone (Plan 029 Task 4).

Lightweight correctness checks, not anti-cheat hardening.  Every mutant edits a copied
solution notebook and executes it end to end:

* named-function mutants replace one pinned function with a plausible wrong version;
* no-op optimizer-step mutants (p16, p17, p19, p20) drop ``optimizer.step()`` from the
  named training function or loop;
* leakage mutants route validation rows into fitting, which the practice's named
  clean-row seam (first training ``forward``, frozen ``features(x)``, or ``fit``) hashes
  through ``capstone_data.split_of`` while it is armed, i.e. only during fitting;
* protocol mutants call ``final_test_score`` twice or before fitting, with the
  solution's inline call-count guards removed so the answer check alone must notice.

The untouched solutions pass, so validation and test forward passes outside fitting
never trip the seam.
"""

from __future__ import annotations

import ast
import re
import shutil
import sys
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
UNIT_ID = "B2-024-gpu-scientific-ml-capstone"
UNIT = ROOT / "book2" / "units" / UNIT_ID
CI_LOCAL = ROOT / "scripts/ci-local.sh"
ANSWER_CHECK = "### Answer check"

# --- named-function mutants ----------------------------------------------------------

MOVE_BATCH_LEFT_BEHIND = '''def move_batch(batch, device):
    return batch
'''
TRAIN_STEP_NO_AUTOCAST = '''def train_step(model, batch, optimizer, device, amp_dtype):
    images, labels = move_batch(batch, device)
    optimizer.zero_grad(set_to_none=True)
    logits = model(images)
    loss = F.cross_entropy(logits, labels)
    loss.backward()
    optimizer.step()
    return {"loss": loss.item(), "logits_dtype": logits.dtype}
'''
LOAD_CHECKPOINT_NO_RNG = '''def load_checkpoint(path, model, optimizer):
    state = torch.load(path, weights_only=True)
    model.load_state_dict(state["model"])
    optimizer.load_state_dict(state["optimizer"])
    return int(state["step"])
'''
BOOTSTRAP_PREDICTIONS_ONLY = '''def bootstrap_ci(metric_fn, y_true, y_pred, n_boot, alpha, generator):
    point = float(metric_fn(y_true, y_pred))
    n = y_true.shape[0]
    idx = torch.randint(0, n, (n_boot, n), generator=generator)
    stats = [float(metric_fn(y_true, y_pred[idx[b]])) for b in range(n_boot)]
    low, high = _quantiles(stats, alpha)
    return point, low, high
'''
SELECT_STRICT_THRESHOLD = '''def select_pseudo_labels(probs, threshold, max_per_class, *, strict=False, use_cap=True):
    pred = probs.argmax(dim=1)
    conf = probs.max(dim=1).values
    candidate = conf > threshold
    kept = []
    for k in range(probs.shape[1]):
        rows = torch.nonzero(candidate & (pred == k)).flatten()
        rows = rows[torch.sort(-conf[rows], stable=True).indices]
        kept.append(rows[:max_per_class] if use_cap else rows)
    indices = torch.sort(torch.cat(kept)).values.to(torch.int64)
    return indices, pred[indices].to(torch.int64)
'''
SELECT_CAP_IGNORED = '''def select_pseudo_labels(probs, threshold, max_per_class, *, strict=False, use_cap=True):
    pred = probs.argmax(dim=1)
    conf = probs.max(dim=1).values
    candidate = conf > threshold if strict else conf >= threshold
    kept = []
    for k in range(probs.shape[1]):
        rows = torch.nonzero(candidate & (pred == k)).flatten()
        rows = rows[torch.sort(-conf[rows], stable=True).indices]
        kept.append(rows)
    indices = torch.sort(torch.cat(kept)).values.to(torch.int64)
    return indices, pred[indices].to(torch.int64)
'''
TIKHONOV_NO_LAMBDA = '''def tikhonov_solve(A, y, lam):
    A = A.double()
    y = y.double()
    return torch.linalg.solve(A.T @ A, A.T @ y)
'''
CANONICALIZE_BY_WEIGHT = '''def canonicalize(params, key=1):
    p = params.reshape(-1, 3, 3)
    order = torch.argsort(p[..., 0], dim=1, stable=True)
    return torch.gather(p, 1, order[..., None].expand(-1, -1, 3)).reshape(-1, 9)
'''
RUN_ABLATION_POPULATION_STD = '''def run_ablation(configs, train_fn, seeds, steps_per_run):
    seeds = tuple(seeds)
    if len(seeds) < 2:
        raise ValueError("run_ablation needs at least two seeds for a sample standard deviation")
    table = {}
    for name, config in configs.items():
        scores = []
        for seed in seeds:
            budget = capstone_data.StepBudget(steps_per_run)
            score = float(train_fn(config, seed, budget))
            if budget.used != steps_per_run:
                raise RuntimeError(f"{name}, seed {seed}: used {budget.used} of {steps_per_run} steps")
            scores.append(score)
        r = len(scores)
        mean = sum(scores) / r
        std = math.sqrt(sum((s - mean) ** 2 for s in scores) / r)
        table[name] = {"scores": tuple(scores), "mean": mean, "std": std, "steps": steps_per_run * r}
    return table
'''

# (practice, function, mutant)
FUNCTION_MUTANTS = (
    pytest.param("p06", "move_batch", MOVE_BATCH_LEFT_BEHIND,
                 id="move_batch-batch-left-behind"),
    pytest.param("p06", "train_step", TRAIN_STEP_NO_AUTOCAST,
                 id="train_step-autocast-omitted"),
    pytest.param("p07", "load_checkpoint", LOAD_CHECKPOINT_NO_RNG,
                 id="load_checkpoint-rng-not-restored"),
    pytest.param("p08", "bootstrap_ci", BOOTSTRAP_PREDICTIONS_ONLY,
                 id="bootstrap_ci-predictions-without-labels"),
    pytest.param("p09", "select_pseudo_labels", SELECT_STRICT_THRESHOLD,
                 id="select_pseudo_labels-strict-threshold"),
    pytest.param("p09", "select_pseudo_labels", SELECT_CAP_IGNORED,
                 id="select_pseudo_labels-cap-ignored"),
    pytest.param("p10", "tikhonov_solve", TIKHONOV_NO_LAMBDA,
                 id="tikhonov_solve-lambda-dropped"),
    pytest.param("p11", "canonicalize", CANONICALIZE_BY_WEIGHT,
                 id="canonicalize-sort-by-weight"),
    pytest.param("p12", "run_ablation", RUN_ABLATION_POPULATION_STD,
                 id="run_ablation-population-std"),
)
PINNED_FUNCTIONS = {
    "move_batch", "train_step", "load_checkpoint", "bootstrap_ci", "select_pseudo_labels",
    "tikhonov_solve", "canonicalize", "run_ablation",
}

# --- no-op optimizer-step mutants ----------------------------------------------------

TRAIN_STEP_NO_STEP = TRAIN_STEP_NO_AUTOCAST.replace("    optimizer.step()\n", "")
TRAIN_STUDENT_NO_STEP = '''def train_student(x, y, noise_std, config):
    device = torch.device(config["device"])
    torch.manual_seed(SEED)
    model = NoisyStudent(noise_std).to(device)
    model.register_forward_pre_hook(make_seam_hook())
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, betas=(0.9, 0.999), eps=1e-8, weight_decay=0)
    model.train()
    x, y = x.to(device), y.to(device)
    amp = config["amp_dtype"]
    for _ in range(config["steps_per_round"]):
        if config["batch_size"] is None:
            xb, yb = x, y
        else:
            idx = torch.randint(0, x.shape[0], (config["batch_size"],))
            xb, yb = x[idx], y[idx]
        optimizer.zero_grad(set_to_none=True)
        with nullcontext() if amp is None else torch.autocast(device_type=device.type, dtype=amp):
            loss = F.cross_entropy(model(xb), yb)
        loss.backward()
    return model.eval()
'''
TRAIN_INVERSE_NO_STEP = '''def train_inverse(model, x, y, optimizer, config):
    device = torch.device(config["device"])
    x, y = x.to(device), y.to(device)
    amp = config["amp_dtype"]
    model.train()
    losses = []
    for _ in range(config["steps"]):
        if config["batch_size"] is None:
            xb, yb = x, y
        else:
            idx = torch.randint(0, x.shape[0], (config["batch_size"],))
            xb, yb = x[idx], y[idx]
        optimizer.zero_grad(set_to_none=True)
        with nullcontext() if amp is None else torch.autocast(device_type=device.type, dtype=amp):
            loss = F.mse_loss(model(xb), yb)
        loss.backward()
        losses.append(loss.item())
    return losses
'''
P20_LOOP = "        loss.backward()\n        optimizer.step()\n        losses.append(loss.item())\n"

# practice -> ("function", name, source) or ("text", old, new)
NO_OP_STEP = {
    "p16": ("function", "train_step", TRAIN_STEP_NO_STEP),
    "p17": ("function", "train_student", TRAIN_STUDENT_NO_STEP),
    "p19": ("function", "train_inverse", TRAIN_INVERSE_NO_STEP),
    "p20": ("text", P20_LOOP, "        loss.backward()\n        losses.append(loss.item())\n"),
}

# --- leakage mutants (validation rows reach fitting) ---------------------------------

P16_TRAIN_WITH_VAL = '''def train(config, model, optimizer, start_step, checkpoint_path):
    device = torch.device(config["device"])
    pool_x, pool_y = training_pool(config)
    pool_x, pool_y = torch.cat([pool_x, xv]), torch.cat([pool_y, yv])
    losses = []
    for step in range(start_step + 1, config["steps"] + 1):
        idx = torch.randint(0, pool_x.shape[0], (config["batch_size"],))
        out = train_step(model, (pool_x[idx], pool_y[idx]), optimizer, device, config["amp_dtype"])
        losses.append(out["loss"])
        if step == config["checkpoint_at"]:
            save_checkpoint(checkpoint_path, model, optimizer, step)
    return losses
'''
P17_STUDENT_WITH_VAL = '''def train_student(x, y, noise_std, config):
    x, y = torch.cat([x, xv]), torch.cat([y, yv])
    device = torch.device(config["device"])
    torch.manual_seed(SEED)
    model = NoisyStudent(noise_std).to(device)
    model.register_forward_pre_hook(make_seam_hook())
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, betas=(0.9, 0.999), eps=1e-8, weight_decay=0)
    model.train()
    x, y = x.to(device), y.to(device)
    amp = config["amp_dtype"]
    for _ in range(config["steps_per_round"]):
        if config["batch_size"] is None:
            xb, yb = x, y
        else:
            idx = torch.randint(0, x.shape[0], (config["batch_size"],))
            xb, yb = x[idx], y[idx]
        optimizer.zero_grad(set_to_none=True)
        with nullcontext() if amp is None else torch.autocast(device_type=device.type, dtype=amp):
            loss = F.cross_entropy(model(xb), yb)
        loss.backward()
        optimizer.step()
    return model.eval()
'''

# practice -> (seam, ("function", name, source) | ("text", old, new))
LEAKAGE = {
    "p16": ("model forward (pre-hook)", ("function", "train", P16_TRAIN_WITH_VAL)),
    "p17": ("model forward (pre-hook)", ("function", "train_student", P17_STUDENT_WITH_VAL)),
    "p18": ("features(x)", ("text",
        "Z = torch.cat([features(xl), features(pool)])",
        "Z = torch.cat([features(xl), features(pool), features(xv)])")),
    "p19": ("model forward (pre-hook)", ("text",
        "losses = train_inverse(model, x_fit, y_fit, optimizer, CONFIG)",
        "losses = train_inverse(model, torch.cat([x_fit, xv]), torch.cat([y_fit, yv]), optimizer, CONFIG)")),
    "p20": ("model forward (pre-hook)", ("text",
        "losses = train_regressor(model, f_fit, theta_fit, optimizer, CONFIG)",
        ("losses = train_regressor(model, torch.cat([f_fit, fv]), torch.cat([theta_fit, theta_v]), "
         "optimizer, CONFIG)"))),
    "p21": ("InverseRegressor.fit", ("text",
        "reg = InverseRegressor(family, True, seed, STEPS_PER_RUN, budget).fit(train_x, train_y)",
        ("reg = InverseRegressor(family, True, seed, STEPS_PER_RUN, budget).fit("
         "torch.cat([train_x, val_x]), torch.cat([train_y, val_y]))"))),
    "p22": ("InverseMLP.fit", ("text",
        "model = InverseMLP(config, seed, STEPS, budget).fit(train_x, train_y)",
        ("model = InverseMLP(config, seed, STEPS, budget).fit("
         "torch.cat([train_x, val_x]), torch.cat([train_y, val_y]))"))),
    "p26": ("AmortizedPhysicsInverse.fit", ("text",
        "approach = AmortizedPhysicsInverse(budget).fit(train_x, train_y)",
        ("approach = AmortizedPhysicsInverse(budget).fit("
         "torch.cat([train_x, val_x]), torch.cat([train_y, val_y]))"))),
    "p27": ("PeakInitLeastSquares.fit", ("text",
        "approach = PeakInitLeastSquares(budget).fit(train_x, train_y)",
        ("approach = PeakInitLeastSquares(budget).fit("
         "torch.cat([train_x, val_x]), torch.cat([train_y, val_y]))"))),
}
MODEL_BUILDING = tuple(LEAKAGE)

# --- protocol mutants ----------------------------------------------------------------

TASKS = {
    "p16": "shapes_supervised", "p17": "shapes_ssl", "p18": "shapes_ssl",
    "p19": "inverse", "p20": "mixture", "p21": "inverse", "p22": "inverse",
    "p26": "inverse", "p27": "mixture",
}
DUMMY_PREDICT = {
    "shapes_supervised": "lambda x: torch.zeros(x.shape[0], dtype=torch.int64)",
    "shapes_ssl": "lambda x: torch.zeros(x.shape[0], dtype=torch.int64)",
    "inverse": "lambda x: torch.full((x.shape[0], 3), 0.5)",
    "mixture": "lambda x: torch.full((x.shape[0], 9), 0.5)",
}
PROTOCOL = {
    "p16": "called-twice", "p17": "before-fitting", "p18": "called-twice",
    "p19": "before-fitting", "p20": "called-twice", "p21": "before-fitting",
    "p22": "called-twice", "p26": "before-fitting", "p27": "called-twice",
}
INLINE_GUARD = re.compile(
    r"^assert capstone_data\.test_call_count\([^)]*\) == \d+\n", re.MULTILINE
)

# --- notebook helpers ----------------------------------------------------------------


def _working_notebook(tmp_path: Path, practice: str) -> Path:
    working_unit = tmp_path / UNIT_ID
    shutil.copytree(UNIT, working_unit, ignore=shutil.ignore_patterns("__pycache__"))
    return working_unit / "practice" / f"{practice}_solution.ipynb"


def _answer_index(notebook: nbformat.NotebookNode) -> int:
    indices = [
        index
        for index, cell in enumerate(notebook.cells)
        if cell.cell_type == "markdown" and str(cell.source).strip() == ANSWER_CHECK
    ]
    assert len(indices) == 1
    return indices[0]


def _replace_function(source: str, name: str, replacement: str) -> str | None:
    tree = ast.parse(source)
    matches = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if not matches:
        return None
    assert len(matches) == 1
    node = matches[0]
    lines = source.splitlines(keepends=True)
    start = node.lineno - 1 - len(node.decorator_list)
    return "".join(lines[:start]) + replacement + "".join(lines[node.end_lineno :])


def _solution_code_cells(notebook: nbformat.NotebookNode) -> list[nbformat.NotebookNode]:
    answer = _answer_index(notebook)
    return [cell for cell in notebook.cells[:answer] if cell.cell_type == "code"]


def _mutate(notebook_path: Path, spec: tuple[str, str, str]) -> None:
    kind, target, replacement = spec
    notebook = nbformat.read(notebook_path, as_version=4)
    replaced = 0
    for cell in _solution_code_cells(notebook):
        source = str(cell.source)
        if kind == "function":
            updated = _replace_function(source, target, replacement)
            if updated is None:
                continue
        else:
            count = source.count(target)
            if not count:
                continue
            assert count == 1, f"{target!r} must occur once"
            updated = source.replace(target, replacement)
        cell.source = updated
        replaced += 1
    assert replaced == 1, f"expected one edit site for {target!r} in {notebook_path.name}"
    nbformat.write(notebook, notebook_path)


def _protocol_mutant(notebook_path: Path, practice: str) -> None:
    notebook = nbformat.read(notebook_path, as_version=4)
    task = TASKS[practice]
    stripped = 0
    for cell in _solution_code_cells(notebook):
        source, n = INLINE_GUARD.subn("", str(cell.source))
        stripped += n
        if PROTOCOL[practice] == "called-twice" and "final_test_score(" in source:
            line = next(row for row in source.splitlines() if "final_test_score(" in row)
            source = source.replace(line, f"{line}\n{line}", 1)
        cell.source = source
    assert stripped == 2, f"{practice}: expected two inline call-count guards"
    if PROTOCOL[practice] == "before-fitting":
        supplied = next(
            index for index, cell in enumerate(notebook.cells) if cell.cell_type == "code"
        )
        peek = nbformat.v4.new_code_cell(
            f"peek = capstone_data.final_test_score({DUMMY_PREDICT[task]}, task={task!r})"
        )
        notebook.cells.insert(supplied + 1, peek)
    nbformat.write(notebook, notebook_path)


def _execute(notebook_path: Path) -> nbformat.NotebookNode:
    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=180,
        kernel_name="python3",
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )
    try:
        client.execute()
    except CellExecutionError:
        pass
    return notebook


def _errors(notebook: nbformat.NotebookNode) -> list[tuple[int, str]]:
    return [
        (index, output.get("ename"))
        for index, cell in enumerate(notebook.cells)
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]


def _assert_passes(notebook_path: Path) -> None:
    notebook = _execute(notebook_path)
    assert _errors(notebook) == []
    assert notebook.cells[-1].get("outputs") is not None


def _assert_fails(notebook_path: Path) -> None:
    """Exactly one error: an AssertionError raised by the answer-check cell."""
    notebook = _execute(notebook_path)
    failures = _errors(notebook)
    assert failures == [(_answer_index(notebook) + 1, "AssertionError")], failures


# --- tests ---------------------------------------------------------------------------


def test_mutant_tables_cover_the_plan_029_contract() -> None:
    assert {param.values[1] for param in FUNCTION_MUTANTS} == PINNED_FUNCTIONS
    assert set(NO_OP_STEP) == {"p16", "p17", "p19", "p20"}
    assert MODEL_BUILDING == ("p16", "p17", "p18", "p19", "p20", "p21", "p22", "p26", "p27")
    assert set(PROTOCOL) == set(MODEL_BUILDING) == set(TASKS)
    assert set(PROTOCOL.values()) == {"called-twice", "before-fitting"}


@pytest.mark.parametrize(
    "practice", ("p06", "p07", "p08", "p09", "p10", "p11", "p12", *MODEL_BUILDING)
)
def test_untouched_solution_answer_check_passes(tmp_path: Path, practice: str) -> None:
    _assert_passes(_working_notebook(tmp_path, practice))


@pytest.mark.parametrize(("practice", "function", "replacement"), FUNCTION_MUTANTS)
def test_named_function_wrong_implementation_fails(
    tmp_path: Path, practice: str, function: str, replacement: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _mutate(notebook_path, ("function", function, replacement))
    _assert_fails(notebook_path)


@pytest.mark.parametrize("practice", tuple(NO_OP_STEP))
def test_no_op_optimizer_step_fails_answer_check(tmp_path: Path, practice: str) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _mutate(notebook_path, NO_OP_STEP[practice])
    _assert_fails(notebook_path)


@pytest.mark.parametrize("practice", MODEL_BUILDING)
def test_validation_rows_in_fitting_are_caught_at_the_named_seam(
    tmp_path: Path, practice: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _mutate(notebook_path, LEAKAGE[practice][1])
    _assert_fails(notebook_path)


@pytest.mark.parametrize("practice", MODEL_BUILDING)
def test_final_test_score_protocol_violation_fails_answer_check(
    tmp_path: Path, practice: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _protocol_mutant(notebook_path, practice)
    _assert_fails(notebook_path)


def test_answer_checks_assert_one_test_call_and_a_clean_seam() -> None:
    for practice in MODEL_BUILDING:
        notebook = nbformat.read(UNIT / "practice" / f"{practice}_solution.ipynb", as_version=4)
        check = str(notebook.cells[_answer_index(notebook) + 1].source)
        assert f'capstone_data.test_call_count("{TASKS[practice]}") == 1' in check, practice
        assert "SEAM" in check, practice


def test_book2_ci_runs_capstone_integrity_suite() -> None:
    source = CI_LOCAL.read_text(encoding="utf-8")
    generative = "uv run pytest -q tests/test_generative_model_checks.py\n"
    capstone = "uv run pytest -q tests/test_capstone_checks.py\n"
    assert generative + capstone in source
