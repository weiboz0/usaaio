#!/usr/bin/env python3
"""Generate and check the seeded B2-024 capstone datasets.

Four CPU datasets are produced from ``SEED`` with NumPy's PCG64 streams, plus two
literal results tables:

* ``shapes_supervised`` -- 900 synthetic 8x8 grey images of three shapes
  (0 = square frame, 1 = plus, 2 = diagonal cross) with pixel noise, sub-pixel
  position jitter, size and stroke-width variation: 600 train, 150 validation,
  150 test rows, all labelled.
* ``shapes_ssl`` -- 960 images from the same process but a disjoint stream:
  30 labelled train, 30 labelled validation, 600 unlabelled, 300 test rows.
  The unlabelled pool's labels are never written to disk.
* ``inverse`` -- 1,200 pairs: a point source at (x, y) in [0.1, 0.9]^2 with
  strength q in [0.5, 2.0] produces field magnitudes q / (r^2 + h^2) at 8 fixed
  sensors (h is the sensor height), observed with 3% multiplicative noise:
  800 train, 200 validation, 200 test rows. Targets are (x, y, q).
* ``mixture`` -- 1,200 functions, each a sum of exactly K = 3 positive
  one-dimensional Gaussian bumps sampled at 32 equally spaced x-values in [0, 1]
  with additive noise; centers are separated by at least 3x the largest width.
  800 train, 200 validation, 200 test rows. Targets are the canonical
  parameters (w1, c1, s1, w2, c2, s2, w3, c3, s3), sorted by center.
* ``results_tables`` -- literal tables used by practices p24 and p28.

Image pixels are stored as integers 0..255 (value = integer / 255 as float32);
other values are rounded to four decimals and read back as float32. Split IDs
are immutable contiguous index tuples. The canonical per-row SHA-256 is the
digest of the row's model input as contiguous little-endian float32 bytes.

Running the script writes ``data/capstone_datasets.json``. ``--check``
regenerates everything in memory, compares it with the stored file, and exits
nonzero on any mismatch. The script never trains a model and never stores
weights, losses, metrics, or any other result of training.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

SEED = 20261022
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "capstone_datasets.json"
FORMAT_VERSION = 1

# ---------------------------------------------------------------- shapes
IMAGE_SIZE = 8
SHAPE_NAMES = ("frame", "plus", "cross")
SHAPE_HALF_SIZE = (2.0, 2.6)       # half side / half arm length, in pixels
SHAPE_JITTER = 0.25                # center offset per axis, in pixels
SHAPE_STROKE = (0.45, 0.9)         # Gaussian stroke width, in pixels
SHAPE_CONTRAST = (0.7, 1.0)        # peak intensity before noise
SHAPE_NOISE_STD = 0.7              # additive pixel noise before clipping to [0, 1]
SUPERVISED_SIZES = {"train": 600, "val": 150, "test": 150}
SSL_SIZES = {"train": 30, "val": 30, "unlabelled": 600, "test": 300}

# ---------------------------------------------------------------- inverse
SENSORS_XY = ((0.0, 0.0), (0.5, 0.0), (1.0, 0.0), (1.0, 0.5),
              (1.0, 1.0), (0.5, 1.0), (0.0, 1.0), (0.0, 0.5))
SENSOR_HEIGHT = 0.25
SOURCE_RANGE = (0.1, 0.9)
STRENGTH_RANGE = (0.5, 2.0)
FIELD_NOISE_REL = 0.03
INVERSE_SIZES = {"train": 800, "val": 200, "test": 200}

# ---------------------------------------------------------------- mixture
N_COMPONENTS = 3
N_POINTS = 32
MIX_WEIGHT_RANGE = (0.5, 1.5)
MIX_CENTER_RANGE = (0.1, 0.9)
MIX_WIDTH_RANGE = (0.04, 0.09)
MIX_SEPARATION = 3.0               # min center gap >= MIX_SEPARATION * max width
MIX_NOISE_STD = 0.02
MIXTURE_SIZES = {"train": 800, "val": 200, "test": 200}

DECIMALS = 4

STREAMS = {"shapes_supervised": 1, "shapes_ssl": 2, "inverse": 3, "mixture": 4}
SPLIT_ORDER = {
    "shapes_supervised": ("train", "val", "test"),
    "shapes_ssl": ("train", "val", "unlabelled", "test"),
    "inverse": ("train", "val", "test"),
    "mixture": ("train", "val", "test"),
}

# Literal results tables (hand-written teaching data, not produced by training).
RESULTS_TABLES = {
    "p24": {
        "task": "inverse",
        "metric": "validation mean source-position error (lower is better)",
        "seeds": [0, 1, 2, 3, 4],
        "configs": {
            "A": {"description": "MLP 8-64-64-3 on log magnitudes (reference)",
                  "per_seed": [0.0118, 0.0124, 0.0121, 0.0116, 0.0126],
                  "seed0_ci": [0.0104, 0.0134]},
            "B": {"description": "A + Gaussian input-noise augmentation (std 0.03 on log magnitudes)",
                  "per_seed": [0.0109, 0.0113, 0.0112, 0.0105, 0.0116],
                  "seed0_ci": [0.0096, 0.0123]},
            "C": {"description": "A with hidden width 128",
                  "per_seed": [0.0114, 0.0127, 0.0117, 0.0119, 0.0121],
                  "seed0_ci": [0.0100, 0.0129]},
            "D": {"description": "ablation of A: raw magnitudes instead of log magnitudes",
                  "per_seed": [0.0161, 0.0148, 0.0172, 0.0155, 0.0166],
                  "seed0_ci": [0.0140, 0.0183]},
        },
        "paired_seed0": {
            "B-A": {"mean_diff": -0.0009, "ci": [-0.0014, -0.0004]},
            "C-A": {"mean_diff": -0.0004, "ci": [-0.0011, 0.0003]},
            "D-A": {"mean_diff": 0.0043, "ci": [0.0029, 0.0058]},
        },
    },
    "p28": {
        "task": "mixture",
        "metric": "test permutation-invariant error (lower is better)",
        "rows": [
            {"run": 1, "config": "MLP-64, 1000 steps", "seed": 3, "test_error": 0.0231},
            {"run": 2, "config": "MLP-128, 1000 steps", "seed": 3, "test_error": 0.0204},
            {"run": 3, "config": "MLP-128, 1500 steps", "seed": 3, "test_error": 0.0197},
            {"run": 4, "config": "MLP-128, 1500 steps, dropout 0.1", "seed": 3, "test_error": 0.0201},
            {"run": 5, "config": "MLP-256, 1500 steps", "seed": 3, "test_error": 0.0199},
            {"run": 6, "config": "MLP-128, 1500 steps", "seed": 0, "test_error": 0.0226},
            {"run": 7, "config": "MLP-128, 1500 steps", "seed": 1, "test_error": 0.0219},
            {"run": 8, "config": "MLP-128, 1500 steps", "seed": 2, "test_error": 0.0231},
            {"run": 9, "config": "MLP-128, 1500 steps", "seed": 4, "test_error": 0.0224},
        ],
        "reported_ci": {"method": "best run's test error +/- 1.96 * (sample std of the five seed scores of runs 3 and 6-9) / sqrt(200)",
                        "interval": [0.0195, 0.0199]},
        "preprocessing": "inputs standardized with the mean and std of all 1,200 rows (train, validation, and test) before the split",
        "claim": "MLP-128 with 1500 steps reaches a test error of 0.0197 (95% CI [0.0195, 0.0199]).",
    },
}


def _rng(stream: int, sub: int) -> np.random.Generator:
    return np.random.default_rng([SEED, stream, sub])


def _seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy), 0.0, 1.0)
    return np.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


_YY, _XX = np.meshgrid(np.arange(IMAGE_SIZE) + 0.5, np.arange(IMAGE_SIZE) + 0.5, indexing="ij")


def render_shape(label: int, rng: np.random.Generator) -> np.ndarray:
    """One 8x8 image as integers 0..255 (row-major)."""
    cx = IMAGE_SIZE / 2 + rng.uniform(-SHAPE_JITTER, SHAPE_JITTER)
    cy = IMAGE_SIZE / 2 + rng.uniform(-SHAPE_JITTER, SHAPE_JITTER)
    a = rng.uniform(*SHAPE_HALF_SIZE)
    w = rng.uniform(*SHAPE_STROKE)
    peak = rng.uniform(*SHAPE_CONTRAST)
    segments = {
        0: ((-a, -a, a, -a), (a, -a, a, a), (a, a, -a, a), (-a, a, -a, -a)),
        1: ((-a, 0.0, a, 0.0), (0.0, -a, 0.0, a)),
        2: ((-a, -a, a, a), (-a, a, a, -a)),
    }[int(label)]
    d = np.full((IMAGE_SIZE, IMAGE_SIZE), np.inf)
    for x0, y0, x1, y1 in segments:
        d = np.minimum(d, _seg_dist(_XX, _YY, cx + x0, cy + y0, cx + x1, cy + y1))
    img = peak * np.exp(-(d / w) ** 2) + SHAPE_NOISE_STD * rng.standard_normal((IMAGE_SIZE, IMAGE_SIZE))
    return np.rint(np.clip(img, 0.0, 1.0) * 255.0).astype(np.int64).reshape(-1)


def _balanced_labels(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.permutation(np.arange(n) % 3)


def shapes_block(n: int, rng: np.random.Generator):
    labels = _balanced_labels(n, rng)
    images = np.stack([render_shape(int(k), rng) for k in labels])
    return images, labels


def inverse_block(n: int, rng: np.random.Generator):
    sensors = np.asarray(SENSORS_XY, dtype=np.float64)
    src = rng.uniform(*SOURCE_RANGE, size=(n, 2))
    q = rng.uniform(*STRENGTH_RANGE, size=n)
    r2 = ((src[:, None, :] - sensors[None]) ** 2).sum(-1)
    clean = q[:, None] / (r2 + SENSOR_HEIGHT ** 2)
    noisy = clean * (1.0 + FIELD_NOISE_REL * rng.standard_normal((n, len(sensors))))
    return np.round(noisy, DECIMALS), np.round(np.c_[src, q], DECIMALS)


def mixture_x() -> np.ndarray:
    return np.linspace(0.0, 1.0, N_POINTS)


def mixture_values(params: np.ndarray, x: np.ndarray) -> np.ndarray:
    p = params.reshape(-1, N_COMPONENTS, 3)
    w, c, s = p[..., 0], p[..., 1], p[..., 2]
    return (w[:, None, :] * np.exp(-(x[None, :, None] - c[:, None, :]) ** 2 / (2.0 * s[:, None, :] ** 2))).sum(-1)


def mixture_block(n: int, rng: np.random.Generator):
    params = np.empty((n, N_COMPONENTS, 3))
    for i in range(n):
        while True:
            widths = rng.uniform(*MIX_WIDTH_RANGE, size=N_COMPONENTS)
            centers = np.sort(rng.uniform(*MIX_CENTER_RANGE, size=N_COMPONENTS))
            if np.diff(centers).min() >= MIX_SEPARATION * widths.max():
                break
        weights = rng.uniform(*MIX_WEIGHT_RANGE, size=N_COMPONENTS)
        params[i] = np.stack([weights, centers, widths], axis=1)
    params = np.round(params.reshape(n, -1), DECIMALS)
    p3 = params.reshape(n, N_COMPONENTS, 3)
    gaps = np.diff(p3[..., 1], axis=1).min(1)
    if not np.all(gaps >= MIX_SEPARATION * p3[..., 2].max(1) - 1e-9):
        raise ValueError("rounding broke the separation rule")
    values = mixture_values(params, mixture_x()) + MIX_NOISE_STD * rng.standard_normal((n, N_POINTS))
    return np.round(values, DECIMALS), params


def input_rows_float32(name: str, inputs) -> np.ndarray:
    """The canonical float32 model-input rows of a dataset (flattened per row)."""
    arr = np.asarray(inputs)
    if name.startswith("shapes"):
        return arr.astype("<f4") / np.float32(255.0)
    return arr.astype("<f4")


def row_sha256(row) -> str:
    array = np.ascontiguousarray(np.asarray(row, dtype="<f4")).reshape(-1)
    return hashlib.sha256(array.tobytes()).hexdigest()


def _dataset(name: str) -> dict:
    stream = STREAMS[name]
    sizes = {"shapes_supervised": SUPERVISED_SIZES, "shapes_ssl": SSL_SIZES,
             "inverse": INVERSE_SIZES, "mixture": MIXTURE_SIZES}[name]
    maker = {"shapes_supervised": shapes_block, "shapes_ssl": shapes_block,
             "inverse": inverse_block, "mixture": mixture_block}[name]
    inputs, targets, splits, start = [], [], {}, 0
    for sub, split in enumerate(SPLIT_ORDER[name]):
        x, y = maker(sizes[split], _rng(stream, sub))
        inputs.extend(np.asarray(x).tolist())
        if split == "unlabelled":
            targets.extend([None] * len(x))
        else:
            targets.extend(np.asarray(y).tolist())
        splits[split] = list(range(start, start + len(x)))
        start += len(x)
    rows32 = input_rows_float32(name, inputs)
    hashes = [row_sha256(r) for r in rows32]
    if len(set(hashes)) != len(hashes):
        raise ValueError(f"{name}: duplicate input rows")
    digest = hashlib.sha256("".join(hashes).encode()).hexdigest()
    return {"inputs": inputs, "targets": targets, "splits": splits, "digest": digest}


def build_payload() -> dict:
    return {
        "seed": SEED,
        "format_version": FORMAT_VERSION,
        "constants": {
            "shape_names": list(SHAPE_NAMES),
            "sensors_xy": [list(p) for p in SENSORS_XY],
            "sensor_height": SENSOR_HEIGHT,
            "mixture_x_points": N_POINTS,
            "mixture_components": N_COMPONENTS,
        },
        "datasets": {name: _dataset(name) for name in STREAMS},
        "results_tables": RESULTS_TABLES,
    }


def simulate_block(task: str, n: int, seed: int):
    """Fresh draws from a task's generative process for accelerator extensions.

    ``seed`` must differ from ``SEED``; the streams never touch the stored data.
    Shapes return (int images 0..255, labels); others return (inputs, targets).
    """
    if int(seed) == SEED:
        raise ValueError("simulate() needs a seed different from the unit seed")
    rng = np.random.default_rng([int(seed), 100 + STREAMS[task]])
    maker = {"shapes_supervised": shapes_block, "shapes_ssl": shapes_block,
             "inverse": inverse_block, "mixture": mixture_block}[task]
    return maker(int(n), rng)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="regenerate and compare with the stored file")
    args = parser.parse_args(argv)
    payload = build_payload()
    text = json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"
    if args.check:
        if not DATA_PATH.is_file():
            print(f"missing {DATA_PATH}", file=sys.stderr)
            return 1
        stored = DATA_PATH.read_text(encoding="utf-8")
        if stored != text:
            print("capstone_datasets.json does not match a fresh regeneration", file=sys.stderr)
            return 1
        for name, entry in payload["datasets"].items():
            sizes = {k: len(v) for k, v in entry["splits"].items()}
            print(f"{name}: {sizes} digest {entry['digest'][:16]}")
        print("check ok")
        return 0
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {DATA_PATH} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
