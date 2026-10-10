"""Read-only loader and evaluation harness for the r2-001 open-ended problems.

The rows live in ``r2_001_datasets.json`` next to this file and are produced by
``gen_r2_001.py`` (seed 20261101).  Importing this module verifies every
dataset digest and that each dataset's splits partition its rows.

Public surface
--------------
Data (fresh tensors on every call; no accessor returns test rows or pool labels):

* ``TASKS`` -- ``("heat", "texture", "lorentz")`` for Problems 2, 4 and 5.
* ``TRAIN_IDS`` / ``VAL_IDS`` / ``TEST_IDS`` / ``UNLABELLED_IDS`` -- read-only
  maps from task name to an immutable tuple of row IDs (``UNLABELLED_IDS`` has
  only ``"texture"``).
* ``train_rows(task)`` / ``val_rows(task)`` -- ``(inputs, targets)``.
  Heat: float32 ``(N, 50)`` readings and float32 ``(N, 6)`` targets
  ``(x1, y1, q1, x2, y2, q2)`` sorted by ``x``.
  Texture: float32 ``(N, 1, 10, 10)`` patches in ``[0, 1]`` and int64 ``(N,)``
  labels; training rows come from scanner A, and validation, pool and test rows
  from scanner B (see Problem 4).  Lorentz: float32 ``(N, 40)`` sampled values and float32 ``(N, 6)``
  canonical parameters ``(a1, c1, w1, a2, c2, w2)`` sorted by centre.
* ``unlabelled_rows("texture")`` -- float32 ``(760, 1, 10, 10)`` patches only.
* ``ROW_SHA256[task]`` -- tuple of per-row SHA-256 digests indexed by row ID;
  ``row_sha256(row)`` hashes one model-input row (contiguous little-endian
  float32 bytes); ``split_of(task, row)`` returns ``"train"``, ``"val"``,
  ``"unlabelled"``, ``"test"`` or ``None`` (not a stored row).
* Constants: ``HEAT_SENSORS_XY`` (25, 2), ``HEAT_TIMES`` (0.005, 0.02),
  ``HEAT_DIFFUSIVITY`` (1.0), ``LORENTZ_X`` (40,).
* Physics helpers: ``heat_forward(sources_xy, strengths)`` and
  ``lorentz_values(x, params)`` (the forward models defined in the statements).
* ``simulate(task, n, seed)`` -- fresh draws from a task's generative process
  (for accelerator extensions); ``seed`` must differ from ``SEED``.

Evaluation:

* ``metric_per_example(task, pred, target)`` and the named metrics
  ``accuracy_per_example``, ``pair_position_error_per_example``,
  ``pair_parameter_error_per_example``.
* ``final_test_score(predict_fn, n_boot=1000, alpha=0.05, *, task)`` -- the only
  route to the locked test rows.  Returns a ``TestScore`` with the metric and
  its seeded percentile-bootstrap CI over test examples.  Every call is counted:
  ``test_call_count(task)``.
* ``baseline_score(task)`` -- the committed baseline's ``TestScore`` (not counted).
* ``StepBudget(max_steps)`` -- counts optimizer steps of wrapped optimizers.

No trained weights, losses, or metrics are stored here; baselines are computed
on demand by the committed code below.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import time
from collections import namedtuple
from pathlib import Path
from types import MappingProxyType

import numpy as np
import torch
from torch import nn
import torch.nn.functional as F

SEED = 20261101
DATA_PATH = Path(__file__).resolve().with_name("r2_001_datasets.json")
GENERATOR_PATH = Path(__file__).resolve().with_name("gen_r2_001.py")
_PAYLOAD = json.loads(DATA_PATH.read_text(encoding="utf-8"))
if _PAYLOAD.get("seed") != SEED:
    raise ValueError("r2_001_datasets.json was not generated with seed 20261101")

TASKS = ("heat", "texture", "lorentz")
_TASK_INDEX = {name: i for i, name in enumerate(TASKS)}
METRICS = MappingProxyType({
    "heat": ("mean permutation-invariant source-position error", False),
    "texture": ("accuracy", True),
    "lorentz": ("mean permutation-invariant parameter error", False),
})


def row_sha256(row) -> str:
    """Canonical SHA-256 of one model-input row's little-endian float32 bytes."""
    if isinstance(row, torch.Tensor):
        row = row.detach().cpu().numpy()
    array = np.ascontiguousarray(np.asarray(row, dtype="<f4")).reshape(-1)
    return hashlib.sha256(array.tobytes()).hexdigest()


def _input_array(name: str, inputs) -> np.ndarray:
    if name == "texture":
        arr = np.asarray(inputs, dtype=np.int64)
        if arr.min() < 0 or arr.max() > 255:
            raise ValueError("texture: pixel out of range")
        return (arr.astype("<f4") / np.float32(255.0)).reshape(-1, 1, 10, 10)
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
    if name == "texture":
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
UNLABELLED_IDS = MappingProxyType({"texture": _DATA["texture"][2]["unlabelled"]})
ROW_SHA256 = MappingProxyType({n: _DATA[n][3] for n in TASKS})
_SPLIT_BY_HASH = {
    n: MappingProxyType({ROW_SHA256[n][i]: split for split, ids in _DATA[n][2].items() for i in ids})
    for n in TASKS
}

_C = _PAYLOAD["constants"]
TEXTURE_NAMES = tuple(_C["texture_names"])
HEAT_SENSORS_XY = torch.tensor(_C["heat_sensors_xy"], dtype=torch.float64)
HEAT_TIMES = tuple(float(t) for t in _C["heat_times"])
HEAT_DIFFUSIVITY = float(_C["heat_diffusivity"])
LORENTZ_X = (torch.arange(int(_C["lorentz_points"]), dtype=torch.float64) + 0.5) / int(_C["lorentz_points"])
LORENTZ_X = LORENTZ_X.float()
for _t in (HEAT_SENSORS_XY, LORENTZ_X):
    _t.requires_grad_(False)


def _check_task(task: str) -> None:
    if task not in TASKS:
        raise KeyError(f"unknown task {task!r}; expected one of {TASKS}")


def _rows(task: str, ids):
    x, y, _, _ = _DATA[task]
    ids = list(ids)
    return torch.from_numpy(x[ids].copy()), torch.from_numpy(y[ids].copy())


def train_rows(task: str):
    """Fresh ``(inputs, targets)`` for the training split, in stored ID order."""
    _check_task(task)
    return _rows(task, TRAIN_IDS[task])


def val_rows(task: str):
    """Fresh ``(inputs, targets)`` for the validation split, in stored ID order."""
    _check_task(task)
    return _rows(task, VAL_IDS[task])


def unlabelled_rows(task: str = "texture") -> torch.Tensor:
    """Fresh unlabelled pool patches (labels are never exposed)."""
    if task != "texture":
        raise KeyError("only texture has an unlabelled pool")
    return _rows(task, UNLABELLED_IDS[task])[0]


def split_of(task: str, row):
    """Which split a model-input row belongs to (``None`` if it is not stored)."""
    _check_task(task)
    return _SPLIT_BY_HASH[task].get(row_sha256(row))


def simulate(task: str, n: int, seed: int):
    """Fresh tensors from the task's generative process (never the stored rows)."""
    _check_task(task)
    spec = importlib.util.spec_from_file_location("_r2_001_generator", GENERATOR_PATH)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    x, y = gen.simulate_block(task, n, seed)
    x = torch.from_numpy(_input_array(task, x).copy())
    if task == "texture":
        y = torch.as_tensor(np.asarray(y), dtype=torch.int64)
    else:
        y = torch.as_tensor(np.asarray(y, dtype="<f4"))
    held = {"val", "test"}
    if any(_SPLIT_BY_HASH[task].get(row_sha256(r)) in held for r in x):
        raise RuntimeError("simulated row collides with a held-out row")
    return x, y


# ------------------------------------------------------------------ forward models
def heat_forward(sources_xy: torch.Tensor, strengths: torch.Tensor) -> torch.Tensor:
    """Noise-free readings ``(N, 50)`` of two-source heat fields.

    ``sources_xy`` is ``(N, 2, 2)`` (source k's ``(x, y)`` in row ``k``) and
    ``strengths`` is ``(N, 2)``.  Reading ``(t, s)`` is
    ``sum_k q_k * exp(-|p_s - s_k|^2 / (4 D t)) / (4 pi D t)``; columns 0..24 are
    the 25 sensors at ``t = 0.005``, columns 25..49 the same sensors at
    ``t = 0.02``.  Differentiable; float64 if the inputs are float64.
    """
    sensors = HEAT_SENSORS_XY.to(sources_xy.dtype)
    d2 = ((sources_xy[:, :, None, :] - sensors[None, None, :, :]) ** 2).sum(-1)   # (N, 2, 25)
    blocks = []
    for t in HEAT_TIMES:
        scale = 4.0 * HEAT_DIFFUSIVITY * t
        g = torch.exp(-d2 / scale) / (torch.pi * scale)
        blocks.append((strengths[:, :, None] * g).sum(1))
    return torch.cat(blocks, dim=1)


def lorentz_values(x: torch.Tensor, params: torch.Tensor) -> torch.Tensor:
    """Two-peak Lorentzian sums: params ``(N, 6)`` = ``(a1, c1, w1, a2, c2, w2)`` -> ``(N, len(x))``."""
    p = params.reshape(-1, 2, 3)
    a, c, w = p[..., 0], p[..., 1], p[..., 2]
    return (a[:, None, :] / (1.0 + ((x[None, :, None] - c[:, None, :]) / w[:, None, :]) ** 2)).sum(-1)


# ------------------------------------------------------------------ metrics
def accuracy_per_example(pred_labels: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    return (pred_labels.long() == labels.long()).double()


def pair_position_error_per_example(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """min over the 2 source orders of the mean Euclidean distance of the 2 sources.

    ``pred`` is ``(N, 4)`` = ``(x1, y1, x2, y2)``; ``target`` is ``(N, 6)`` or ``(N, 4)``.
    """
    p = pred.double().reshape(-1, 2, 2)
    t = target.double()
    if t.shape[1] == 6:
        t = t[:, [0, 1, 3, 4]]
    t = t.reshape(-1, 2, 2)
    same = (p - t).norm(dim=2).mean(dim=1)
    swap = (p[:, [1, 0]] - t).norm(dim=2).mean(dim=1)
    return torch.minimum(same, swap)


def pair_parameter_error_per_example(pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """min over the 2 peak orders of the mean |difference| over the 6 parameters."""
    p = pred.double().reshape(-1, 2, 3)
    t = target.double().reshape(-1, 2, 3)
    same = (p - t).abs().mean(dim=(1, 2))
    swap = (p[:, [1, 0]] - t).abs().mean(dim=(1, 2))
    return torch.minimum(same, swap)


def metric_per_example(task: str, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    _check_task(task)
    if task == "texture":
        return accuracy_per_example(pred, target)
    if task == "heat":
        return pair_position_error_per_example(pred, target)
    return pair_parameter_error_per_example(pred, target)


TestScore = namedtuple(
    "TestScore", "task metric score ci_low ci_high n_examples n_boot alpha higher_is_better"
)


def _validate_prediction(task: str, pred, n: int) -> torch.Tensor:
    if not isinstance(pred, torch.Tensor):
        raise TypeError("predict_fn must return a torch.Tensor")
    pred = pred.detach().cpu()
    if task == "texture":
        if pred.shape != (n,) or pred.dtype != torch.int64:
            raise ValueError(f"texture: predict_fn must return int64 labels of shape ({n},)")
        if pred.min() < 0 or pred.max() > 2:
            raise ValueError("texture: labels must be in {0, 1, 2}")
        return pred
    width = 4 if task == "heat" else 6
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
    and must return floating ``(N, 4)`` source positions ``(x1, y1, x2, y2)``
    (heat), int64 labels ``(N,)`` (texture), or floating ``(N, 6)`` peak
    parameters ``(a1, c1, w1, a2, c2, w2)`` (lorentz).  The CI resamples test
    examples with replacement ``n_boot`` times using
    ``torch.Generator().manual_seed(SEED + task index)`` and takes the
    ``alpha/2`` and ``1 - alpha/2`` quantiles of the resampled means
    (``torch.quantile``, linear interpolation).  Call it once, after all fitting
    and selection; ``test_call_count(task)`` records every call.
    """
    _check_task(task)
    _TEST_CALLS[task] += 1
    return _score(task, predict_fn, n_boot, alpha)


def test_call_count(task: str) -> int:
    _check_task(task)
    return _TEST_CALLS[task]


# ------------------------------------------------------------------ baselines
class TextureCNN(nn.Module):
    """Conv(1->8, 3), ReLU, Conv(8->16, 3), ReLU, Linear(16*6*6 -> 3)."""

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 8, 3)
        self.conv2 = nn.Conv2d(8, 16, 3)
        self.head = nn.Linear(16 * 6 * 6, 3)

    def forward(self, x):
        return self.head(F.relu(self.conv2(F.relu(self.conv1(x)))).flatten(1))


def _labelled_only_cnn() -> TextureCNN:
    x, y = train_rows("texture")
    torch.manual_seed(SEED)
    model = TextureCNN()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    for _ in range(150):
        optimizer.zero_grad(set_to_none=True)
        F.cross_entropy(model(x), y).backward()
        optimizer.step()
    return model


def canonical_heat(sources_xy: torch.Tensor) -> torch.Tensor:
    """(N, 2, 2) source positions -> (N, 4) ``(x1, y1, x2, y2)`` sorted by x."""
    order = torch.argsort(sources_xy[..., 0], dim=1, stable=True)
    return torch.gather(sources_xy, 1, order[..., None].expand(-1, -1, 2)).reshape(-1, 4)


def heat_ls_fit(readings: torch.Tensor, init_xy: torch.Tensor, init_q: torch.Tensor, steps: int,
                lr: float = 0.01, optimizer_wrapper=None) -> torch.Tensor:
    """Per-example least squares by Adam on (positions, log-strengths).

    The loss is the sum over examples of each example's mean squared residual over
    the 50 readings, so every example is fitted independently (Adam is
    elementwise).  Returns canonical ``(N, 4)`` positions (float32).
    """
    xy = init_xy.detach().double().clone().requires_grad_(True)            # (N, 2, 2)
    log_q = torch.log(init_q.detach().double().clamp_min(1e-3)).clone().requires_grad_(True)   # (N, 2)
    optimizer = torch.optim.Adam([xy, log_q], lr=lr)
    if optimizer_wrapper is not None:
        optimizer = optimizer_wrapper(optimizer)
    y = readings.detach().double()
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        loss = ((heat_forward(xy, torch.exp(log_q)) - y) ** 2).mean(dim=1).sum()
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        return canonical_heat(xy.detach()).float()


def heat_baseline_init(n: int):
    """Fixed initialization: sources at (0.35, 0.5) and (0.65, 0.5), strengths 1."""
    xy = torch.tensor([[0.35, 0.5], [0.65, 0.5]], dtype=torch.float64).repeat(n, 1, 1)
    return xy, torch.ones(n, 2, dtype=torch.float64)


def canonical_lorentz(params: torch.Tensor) -> torch.Tensor:
    p = params.reshape(-1, 2, 3)
    order = torch.argsort(p[..., 1], dim=1, stable=True)
    return torch.gather(p, 1, order[..., None].expand(-1, -1, 3)).reshape(-1, 6)


def lorentz_ls_fit(values: torch.Tensor, init: torch.Tensor, steps: int, lr: float = 0.02,
                   optimizer_wrapper=None) -> torch.Tensor:
    """Per-example least squares by Adam on (amplitudes, centres, log-widths)."""
    p = init.detach().double().reshape(-1, 2, 3)
    a = p[..., 0].clone().requires_grad_(True)
    c = p[..., 1].clone().requires_grad_(True)
    log_w = torch.log(p[..., 2].clamp_min(1e-3)).clone().requires_grad_(True)
    optimizer = torch.optim.Adam([a, c, log_w], lr=lr)
    if optimizer_wrapper is not None:
        optimizer = optimizer_wrapper(optimizer)
    x = LORENTZ_X.double()
    f = values.detach().double()
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        params = torch.stack([a, c, torch.exp(log_w)], dim=-1)
        loss = ((lorentz_values(x, params) - f) ** 2).mean(dim=1).sum()
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        out = torch.stack([a, c, torch.exp(log_w)], dim=-1).reshape(-1, 6)
    return canonical_lorentz(out).float()


def lorentz_baseline_init(n: int) -> torch.Tensor:
    """Fixed initialization: centres 0.35 / 0.65, amplitudes 1, median training width."""
    _, targets = train_rows("lorentz")
    median_width = float(targets.reshape(-1, 2, 3)[..., 2].median())
    row = torch.tensor([1.0, 0.35, median_width, 1.0, 0.65, median_width], dtype=torch.float64)
    return row.repeat(n, 1)


def _baseline_predict_fn(task: str):
    if task == "heat":
        def predict(readings):
            xy, q = heat_baseline_init(readings.shape[0])
            return heat_ls_fit(readings, xy, q, steps=300, lr=0.01)
        return predict
    if task == "lorentz":
        return lambda values: lorentz_ls_fit(values, lorentz_baseline_init(values.shape[0]), steps=400, lr=0.02)
    model = _labelled_only_cnn()

    def predict(images):
        with torch.no_grad():
            return model(images).argmax(dim=1)
    return predict


BASELINE_RECIPES = MappingProxyType({
    "heat": "per-example least squares on the 50 readings, Adam lr 0.01, 300 steps, from sources (0.35, 0.5) and (0.65, 0.5) with strengths 1",
    "texture": "labelled-only TextureCNN: torch.manual_seed(SEED), Adam lr 0.01, 150 full-batch steps on the 40 labelled training patches",
    "lorentz": "per-example least squares, Adam lr 0.02, 400 steps, from centres (0.35, 0.65), amplitudes 1, median training width",
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
