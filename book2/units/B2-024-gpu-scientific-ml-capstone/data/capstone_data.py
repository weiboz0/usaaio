"""Read-only loader and evaluation harness for the B2-024 capstone datasets.

The rows live in ``capstone_datasets.json`` next to this file and are produced by
``scripts/generate_capstone_data.py`` (seed 20261022). Importing this module
verifies every dataset digest and that each dataset's splits partition its rows.

Public surface
--------------
Data (fresh tensors on every call; no accessor returns test rows or pool labels):

* ``TASKS`` -- ``("shapes_supervised", "shapes_ssl", "inverse", "mixture")``.
* ``TRAIN_IDS`` / ``VAL_IDS`` / ``TEST_IDS`` / ``UNLABELLED_IDS`` -- read-only maps
  from task name to an immutable tuple of row IDs (``UNLABELLED_IDS`` has only
  ``"shapes_ssl"``).
* ``train_rows(task)`` / ``val_rows(task)`` -- ``(inputs, targets)``.
  Shapes: float32 ``(N, 1, 8, 8)`` in ``[0, 1]`` and int64 ``(N,)`` labels.
  Inverse: float32 ``(N, 8)`` sensor magnitudes and float32 ``(N, 3)`` targets
  ``(x, y, strength)``. Mixture: float32 ``(N, 32)`` sampled values and float32
  ``(N, 9)`` canonical parameters ``(w1, c1, s1, w2, c2, s2, w3, c3, s3)``.
* ``unlabelled_rows("shapes_ssl")`` -- float32 ``(600, 1, 8, 8)`` images only.
* ``ROW_SHA256[task]`` -- tuple of per-row SHA-256 digests indexed by row ID;
  ``row_sha256(row)`` hashes one model-input row (contiguous little-endian
  float32 bytes); ``split_of(task, row)`` returns ``"train"``, ``"val"``,
  ``"unlabelled"``, ``"test"`` or ``None`` (not a stored row).
* Constants: ``SENSORS_XY`` (8, 2), ``SENSOR_HEIGHT``, ``GRID_XY`` (81, 2),
  ``TIKHONOV_LAMBDA``, ``MIXTURE_X`` (32,), ``RESULTS_TABLES``.
* ``simulate(task, n, seed)`` -- fresh draws from a task's generative process
  (for accelerator extensions); ``seed`` must differ from ``SEED``.

Evaluation:

* ``metric_per_example(task, pred, target)`` and the named metrics
  ``accuracy_per_example``, ``position_error_per_example``,
  ``perm_invariant_error_per_example``.
* ``final_test_score(predict_fn, n_boot=1000, alpha=0.05, *, task)`` -- the only
  route to the locked test rows. Returns a ``TestScore`` with the metric and its
  seeded percentile-bootstrap CI over test examples. Every call is counted:
  ``test_call_count(task)``.
* ``baseline_score(task)`` -- the committed baseline's ``TestScore`` (not counted).
* ``StepBudget(max_steps)`` -- counts optimizer steps of wrapped optimizers.

No trained weights, losses, or metrics are stored here; baselines are computed
on demand by the committed code below.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import time
from collections import namedtuple
from pathlib import Path
from types import MappingProxyType

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

SEED = 20261022
DATA_PATH = Path(__file__).resolve().with_name("capstone_datasets.json")
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_capstone_data.py"
_PAYLOAD = json.loads(DATA_PATH.read_text(encoding="utf-8"))
if _PAYLOAD.get("seed") != SEED:
    raise ValueError("capstone_datasets.json was not generated with seed 20261022")

TASKS = ("shapes_supervised", "shapes_ssl", "inverse", "mixture")
_TASK_INDEX = {name: i for i, name in enumerate(TASKS)}
METRICS = MappingProxyType({
    "shapes_supervised": ("accuracy", True),
    "shapes_ssl": ("accuracy", True),
    "inverse": ("mean source-position error", False),
    "mixture": ("mean permutation-invariant parameter error", False),
})


def row_sha256(row) -> str:
    """Canonical SHA-256 of one model-input row's little-endian float32 bytes."""
    if isinstance(row, torch.Tensor):
        row = row.detach().cpu().numpy()
    array = np.ascontiguousarray(np.asarray(row, dtype="<f4")).reshape(-1)
    return hashlib.sha256(array.tobytes()).hexdigest()


def _input_array(name: str, inputs) -> np.ndarray:
    if name.startswith("shapes"):
        arr = np.asarray(inputs, dtype=np.int64)
        if arr.min() < 0 or arr.max() > 255:
            raise ValueError(f"{name}: pixel out of range")
        return (arr.astype("<f4") / np.float32(255.0)).reshape(-1, 1, 8, 8)
    return np.asarray(inputs, dtype="<f4")


def _load(name: str):
    entry = _PAYLOAD["datasets"][name]
    x = _input_array(name, entry["inputs"])
    hashes = tuple(row_sha256(r) for r in x)
    if hashlib.sha256("".join(hashes).encode()).hexdigest() != entry["digest"]:
        raise ValueError(f"{name}: stored rows do not match their digest")
    if len(set(hashes)) != len(hashes):
        raise ValueError(f"{name}: duplicate rows")
    splits = {k: tuple(v) for k, v in entry["splits"].items()}
    every = sorted(i for ids in splits.values() for i in ids)
    if every != list(range(len(hashes))):
        raise ValueError(f"{name}: splits must partition the rows")
    x.setflags(write=False)
    if name.startswith("shapes"):
        labelled = [i for s, ids in splits.items() if s != "unlabelled" for i in ids]
        y = np.full(len(hashes), -1, dtype=np.int64)
        y[labelled] = np.asarray([entry["targets"][i] for i in labelled], dtype=np.int64)
    else:
        y = np.asarray(entry["targets"], dtype="<f4")
    y.setflags(write=False)
    return x, y, splits, hashes


_DATA = {name: _load(name) for name in TASKS}
TRAIN_IDS = MappingProxyType({n: _DATA[n][2]["train"] for n in TASKS})
VAL_IDS = MappingProxyType({n: _DATA[n][2]["val"] for n in TASKS})
TEST_IDS = MappingProxyType({n: _DATA[n][2]["test"] for n in TASKS})
UNLABELLED_IDS = MappingProxyType({"shapes_ssl": _DATA["shapes_ssl"][2]["unlabelled"]})
ROW_SHA256 = MappingProxyType({n: _DATA[n][3] for n in TASKS})
_SPLIT_BY_HASH = {
    n: MappingProxyType({ROW_SHA256[n][i]: split for split, ids in _DATA[n][2].items() for i in ids})
    for n in TASKS
}

_C = _PAYLOAD["constants"]
SHAPE_NAMES = tuple(_C["shape_names"])
SENSORS_XY = torch.tensor(_C["sensors_xy"], dtype=torch.float64)
SENSOR_HEIGHT = float(_C["sensor_height"])
_g = torch.linspace(0.0, 1.0, 9, dtype=torch.float64)
GRID_XY = torch.stack(torch.meshgrid(_g, _g, indexing="ij"), dim=-1).reshape(81, 2)
TIKHONOV_LAMBDA = 1.0
MIXTURE_X = torch.linspace(0.0, 1.0, int(_C["mixture_x_points"]), dtype=torch.float32)
RESULTS_TABLES = MappingProxyType(json.loads(json.dumps(_PAYLOAD["results_tables"])))
for _t in (SENSORS_XY, GRID_XY, MIXTURE_X):
    _t.requires_grad_(False)


def _check_task(task: str) -> None:
    if task not in TASKS:
        raise KeyError(f"unknown task {task!r}; expected one of {TASKS}")


def _rows(task: str, ids):
    x, y, _, _ = _DATA[task]
    ids = list(ids)
    xt = torch.from_numpy(x[ids].copy())
    if task.startswith("shapes"):
        return xt, torch.from_numpy(y[ids].copy())
    return xt, torch.from_numpy(y[ids].copy())


def train_rows(task: str):
    """Fresh ``(inputs, targets)`` for the training split, in stored ID order."""
    _check_task(task)
    return _rows(task, TRAIN_IDS[task])


def val_rows(task: str):
    """Fresh ``(inputs, targets)`` for the validation split, in stored ID order."""
    _check_task(task)
    return _rows(task, VAL_IDS[task])


def unlabelled_rows(task: str = "shapes_ssl") -> torch.Tensor:
    """Fresh unlabelled pool images (labels are never exposed)."""
    if task != "shapes_ssl":
        raise KeyError("only shapes_ssl has an unlabelled pool")
    return _rows(task, UNLABELLED_IDS[task])[0]


def split_of(task: str, row):
    """Which split a model-input row belongs to (``None`` if it is not stored)."""
    _check_task(task)
    return _SPLIT_BY_HASH[task].get(row_sha256(row))


def simulate(task: str, n: int, seed: int):
    """Fresh tensors from the task's generative process (never the stored rows)."""
    _check_task(task)
    spec = importlib.util.spec_from_file_location("_capstone_generator", GENERATOR_PATH)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    x, y = gen.simulate_block(task, n, seed)
    x = torch.from_numpy(_input_array(task, x).copy())
    if task.startswith("shapes"):
        y = torch.as_tensor(np.asarray(y), dtype=torch.int64)
    else:
        y = torch.as_tensor(np.asarray(y, dtype="<f4"))
    held = {"val", "test"}
    if any(_SPLIT_BY_HASH[task].get(row_sha256(r)) in held for r in x):
        raise RuntimeError("simulated row collides with a held-out row")
    return x, y


# ------------------------------------------------------------------ metrics
_PERMS = tuple(itertools.permutations(range(3)))


def accuracy_per_example(pred_labels: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    return (pred_labels.long() == labels.long()).double()


def position_error_per_example(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return (pred[:, :2].double() - target[:, :2].double()).norm(dim=1)


def perm_invariant_error_per_example(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """min over the 6 component permutations of the mean |difference| over 9 entries."""
    p = pred.double().reshape(-1, 3, 3)
    t = target.double().reshape(-1, 3, 3)
    errs = torch.stack([(p[:, list(perm)] - t).abs().mean(dim=(1, 2)) for perm in _PERMS], dim=1)
    return errs.min(dim=1).values


def metric_per_example(task: str, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    _check_task(task)
    if task.startswith("shapes"):
        return accuracy_per_example(pred, target)
    if task == "inverse":
        return position_error_per_example(pred, target)
    return perm_invariant_error_per_example(pred, target)


TestScore = namedtuple(
    "TestScore", "task metric score ci_low ci_high n_examples n_boot alpha higher_is_better"
)


def _validate_prediction(task: str, pred, n: int) -> torch.Tensor:
    if not isinstance(pred, torch.Tensor):
        raise TypeError("predict_fn must return a torch.Tensor")
    pred = pred.detach().cpu()
    if task.startswith("shapes"):
        if pred.shape != (n,) or pred.dtype != torch.int64:
            raise ValueError(f"{task}: predict_fn must return int64 labels of shape ({n},)")
        if pred.min() < 0 or pred.max() > 2:
            raise ValueError(f"{task}: labels must be in {{0, 1, 2}}")
        return pred
    width = 3 if task == "inverse" else 9
    if pred.shape != (n, width) or not pred.is_floating_point():
        raise ValueError(f"{task}: predict_fn must return floating predictions of shape ({n}, {width})")
    if not torch.isfinite(pred).all():
        raise ValueError(f"{task}: predictions must be finite")
    return pred


def _bootstrap(per_example: torch.Tensor, n_boot: int, alpha: float, generator: torch.Generator):
    n = per_example.shape[0]
    idx = torch.randint(0, n, (n_boot, n), generator=generator)
    stats = per_example[idx].mean(dim=1)
    q = torch.tensor([alpha / 2, 1 - alpha / 2], dtype=torch.float64)
    lo, hi = torch.quantile(stats, q).tolist()
    return lo, hi


def _score(task: str, predict_fn, n_boot: int, alpha: float) -> TestScore:
    if not (isinstance(n_boot, int) and n_boot >= 1):
        raise ValueError("n_boot must be a positive int")
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be in (0, 1)")
    x, y = _rows(task, TEST_IDS[task])
    pred = _validate_prediction(task, predict_fn(x), x.shape[0])
    per = metric_per_example(task, pred, y)
    gen = torch.Generator().manual_seed(SEED + _TASK_INDEX[task])
    lo, hi = _bootstrap(per, n_boot, alpha, gen)
    name, higher = METRICS[task]
    return TestScore(task, name, float(per.mean()), float(lo), float(hi), int(x.shape[0]), n_boot, alpha, higher)


_TEST_CALLS = {name: 0 for name in TASKS}


def final_test_score(predict_fn, n_boot: int = 1000, alpha: float = 0.05, *, task: str) -> TestScore:
    """Score ``predict_fn`` on the locked test rows, with a percentile-bootstrap CI.

    ``predict_fn`` receives the test inputs (the same layout as ``train_rows``)
    and must return int64 labels ``(N,)`` (shapes), floating ``(N, 3)``
    ``(x, y, strength)`` predictions (inverse), or floating ``(N, 9)`` canonical
    parameters (mixture). The CI resamples test examples with replacement
    ``n_boot`` times using ``torch.Generator().manual_seed(SEED + task index)``
    and takes the ``alpha/2`` and ``1 - alpha/2`` quantiles of the resampled
    means (``torch.quantile``, linear interpolation). Call it once, after all
    fitting and selection; ``test_call_count(task)`` records every call.
    """
    _check_task(task)
    _TEST_CALLS[task] += 1
    return _score(task, predict_fn, n_boot, alpha)


def test_call_count(task: str) -> int:
    _check_task(task)
    return _TEST_CALLS[task]


# ------------------------------------------------------------------ baselines
class ShapeCNN(nn.Module):
    """Conv(1->8, 3), ReLU, Conv(8->16, 3), ReLU, Linear(256 -> 3)."""

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 8, 3)
        self.conv2 = nn.Conv2d(8, 16, 3)
        self.head = nn.Linear(16 * 4 * 4, 3)

    def forward(self, x):
        return self.head(F.relu(self.conv2(F.relu(self.conv1(x)))).flatten(1))


def _labelled_only_cnn() -> ShapeCNN:
    x, y = train_rows("shapes_ssl")
    torch.manual_seed(SEED)
    model = ShapeCNN()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    for _ in range(150):
        optimizer.zero_grad(set_to_none=True)
        F.cross_entropy(model(x), y).backward()
        optimizer.step()
    return model


def tikhonov_grid_predict(magnitudes: torch.Tensor, lam: float = TIKHONOV_LAMBDA) -> torch.Tensor:
    """Grid-Tikhonov baseline: (A^T A + lam I)^-1 A^T y on the 9x9 grid, clip at 0,
    density-weighted centroid of the top-3 nodes and their total mass."""
    d2 = ((SENSORS_XY[:, None, :] - GRID_XY[None, :, :]) ** 2).sum(-1)
    A = 1.0 / (d2 + SENSOR_HEIGHT ** 2)                       # (8, 81)
    y = magnitudes.double().T                                 # (8, N)
    density = torch.linalg.solve(A.T @ A + lam * torch.eye(81, dtype=torch.float64), A.T @ y).T
    density = density.clamp_min(0.0)
    top = torch.topk(density, 3, dim=1)
    w = top.values
    mass = w.sum(dim=1, keepdim=True)
    centroid = (w[..., None] * GRID_XY[top.indices]).sum(dim=1) / mass.clamp_min(1e-12)
    return torch.cat([centroid, mass], dim=1).float()


def mixture_values(x: torch.Tensor, params: torch.Tensor) -> torch.Tensor:
    p = params.reshape(-1, 3, 3)
    w, c, s = p[..., 0], p[..., 1], p[..., 2]
    return (w[:, None, :] * torch.exp(-(x[None, :, None] - c[:, None, :]) ** 2 / (2 * s[:, None, :] ** 2))).sum(-1)


def canonical_sort(params: torch.Tensor) -> torch.Tensor:
    p = params.reshape(-1, 3, 3)
    order = torch.argsort(p[..., 1], dim=1, stable=True)
    return torch.gather(p, 1, order[..., None].expand(-1, -1, 3)).reshape(-1, 9)


def mixture_ls_fit(values: torch.Tensor, init: torch.Tensor, steps: int, lr: float = 0.02,
                   optimizer_wrapper=None) -> torch.Tensor:
    """Per-sample least squares by Adam on (weights, centers, log-widths).

    The loss is the sum over samples of each sample's mean squared residual over
    the 32 points, so every sample is fitted independently (Adam is elementwise).
    """
    p = init.detach().double().reshape(-1, 3, 3)
    w = p[..., 0].clone().requires_grad_(True)
    c = p[..., 1].clone().requires_grad_(True)
    log_s = torch.log(p[..., 2].clamp_min(1e-3)).requires_grad_(True)
    optimizer = torch.optim.Adam([w, c, log_s], lr=lr)
    if optimizer_wrapper is not None:
        optimizer = optimizer_wrapper(optimizer)
    x = MIXTURE_X.double()
    f = values.detach().double()
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        params = torch.stack([w, c, torch.exp(log_s)], dim=-1)
        loss = ((mixture_values(x, params) - f) ** 2).mean(dim=1).sum()
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        out = torch.stack([w, c, torch.exp(log_s)], dim=-1).reshape(-1, 9)
    return canonical_sort(out).float()


def mixture_baseline_init(n: int) -> torch.Tensor:
    """Fixed initialization: centers 0.25/0.5/0.75, weights 1, median training width."""
    _, targets = train_rows("mixture")
    median_width = float(targets.reshape(-1, 3, 3)[..., 2].median())
    row = torch.tensor([1.0, 0.25, median_width, 1.0, 0.5, median_width, 1.0, 0.75, median_width])
    return row.repeat(n, 1)


def _baseline_predict_fn(task: str):
    if task == "inverse":
        return tikhonov_grid_predict
    if task == "mixture":
        return lambda values: mixture_ls_fit(values, mixture_baseline_init(values.shape[0]), steps=500)
    if task == "shapes_ssl":
        model = _labelled_only_cnn()

        def predict(images):
            with torch.no_grad():
                return model(images).argmax(dim=1)
        return predict
    raise KeyError(f"no committed baseline for {task!r}")


BASELINE_RECIPES = MappingProxyType({
    "shapes_ssl": "labelled-only ShapeCNN: torch.manual_seed(SEED), Adam lr 0.01, 150 full-batch steps on the 30 labelled training images",
    "inverse": "grid Tikhonov on the 9x9 grid of [0,1]^2, lambda = 1.0, clip at 0, top-3 density-weighted centroid; strength = top-3 mass",
    "mixture": "per-sample least squares, Adam lr 0.02, 500 steps, from centers (0.25, 0.5, 0.75), weights 1, median training width",
})


def baseline_score(task: str, n_boot: int = 1000, alpha: float = 0.05) -> TestScore:
    """The committed baseline's locked-test score (computed now; not counted as a learner call)."""
    _check_task(task)
    threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        with torch.random.fork_rng(devices=[]):
            return _score(task, _baseline_predict_fn(task), n_boot, alpha)
    finally:
        torch.set_num_threads(threads)


# ------------------------------------------------------------------ step budget
class StepBudgetExceeded(RuntimeError):
    pass


class StepBudget:
    """Counts optimizer steps across every optimizer wrapped by ``wrap``."""

    def __init__(self, max_steps: int):
        self.max_steps = int(max_steps)
        self.used = 0
        self.started = time.perf_counter()

    @property
    def remaining(self) -> int:
        return self.max_steps - self.used

    def elapsed(self) -> float:
        return time.perf_counter() - self.started

    def wrap(self, optimizer):
        return _BudgetedOptimizer(optimizer, self)


class _BudgetedOptimizer:
    def __init__(self, optimizer, budget: StepBudget):
        self._optimizer = optimizer
        self._budget = budget

    def step(self, closure=None):
        if self._budget.used >= self._budget.max_steps:
            raise StepBudgetExceeded(f"step budget of {self._budget.max_steps} optimizer steps exhausted")
        self._budget.used += 1
        return self._optimizer.step(closure)

    def zero_grad(self, set_to_none: bool = True):
        return self._optimizer.zero_grad(set_to_none=set_to_none)

    @property
    def param_groups(self):
        return self._optimizer.param_groups

    def state_dict(self):
        return self._optimizer.state_dict()

    def load_state_dict(self, state):
        return self._optimizer.load_state_dict(state)

    def __getattr__(self, name):
        return getattr(self._optimizer, name)
