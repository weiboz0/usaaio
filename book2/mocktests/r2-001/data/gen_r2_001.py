#!/usr/bin/env python3
"""Generate and check the seeded data for mock test r2-001.

Every array is drawn from ``SEED`` with NumPy PCG64 streams
(``np.random.default_rng([SEED, stream, sub])``).  Three files are written
next to this script:

* ``p01_corpus.json`` -- Problem 1's token corpus.  Each row has 13 token IDs
  in ``0..23``: a start token ``a`` uniform on ``0..23`` and, independently, a
  step ``k`` uniform on ``{1, 2, 3}`` give the row ``t_i = (a + i*k) mod 24``,
  ``i = 0..12``.  256 training rows and 64 validation rows.
* ``p03_vae.json`` -- Problem 3's 8-feature rows (256 training, 64 held-out):
  ``x = A u + 0.25 e`` with a fixed 8x2 matrix ``A``, a 2-D latent ``u`` whose
  first coordinate has standard deviation 1.5 and second 0.3, and ``e`` standard
  normal noise.
* ``r2_001_datasets.json`` -- the three open-ended datasets read by
  ``r2_001_data.py``:

  - ``heat`` (Problem 2): two point heat sources in ``[0.15, 0.85]^2`` (centres
    at least 0.25 apart) with strengths in ``[0.5, 1.5]``; 25 sensors on the
    5x5 grid ``{0.1, 0.3, 0.5, 0.7, 0.9}^2`` read the Gaussian heat kernel at
    times ``t = 0.005`` and ``t = 0.02`` (diffusivity 1) with additive
    N(0, 0.05^2) noise.  Inputs ``(N, 50)``, targets ``(N, 6)`` =
    ``(x1, y1, q1, x2, y2, q2)`` sorted by ``x``.  800 / 200 / 200 rows.
  - ``texture`` (Problem 4): 10x10 grey patches of three texture classes
    (0 = oriented stripes, 1 = checkerboard, 2 = scattered dots) with random
    frequency, phase, orientation, contrast and heavy pixel noise, stored as
    integers 0..255.  40 labelled train, 40 labelled validation, 760 unlabelled
    and 400 test rows.  The unlabelled pool's labels are never written.
  - ``lorentz`` (Problem 5): sums of two Lorentzian peaks
    ``a / (1 + ((x - c) / w)^2)`` sampled at the 40 midpoints
    ``x_j = (j + 0.5) / 40`` with additive N(0, 0.02^2) noise.  Targets
    ``(N, 6)`` = ``(a1, c1, w1, a2, c2, w2)`` sorted by centre.  800 / 200 /
    200 rows.

Non-image values are rounded to four decimals.  ``--check`` regenerates all
three files in memory and exits nonzero if any stored file differs.  The script
never trains a model and never stores weights, losses, or metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

SEED = 20261101
HERE = Path(__file__).resolve().parent
FORMAT_VERSION = 1
DECIMALS = 4

# ------------------------------------------------------------ Problem 1 corpus
P01_VOCAB = 24
P01_LEN = 13
P01_STEPS = (1, 2, 3)
P01_SIZES = {"train": 256, "val": 64}

# ------------------------------------------------------------ Problem 3 rows
P03_SIZES = {"train": 256, "heldout": 64}
P03_A = np.array(
    [
        [0.8, 0.1],
        [-0.6, 0.5],
        [0.4, -0.7],
        [0.9, 0.2],
        [-0.3, -0.4],
        [0.5, 0.6],
        [-0.7, 0.3],
        [0.2, -0.5],
    ]
)
P03_LATENT_STD = (1.5, 0.3)
P03_NOISE = 0.25

# ------------------------------------------------------------ heat (Problem 2)
HEAT_SENSOR_COORDS = (0.1, 0.3, 0.5, 0.7, 0.9)
HEAT_SENSORS = [(x, y) for x in HEAT_SENSOR_COORDS for y in HEAT_SENSOR_COORDS]   # x-major, 25
HEAT_TIMES = (0.005, 0.02)
HEAT_DIFFUSIVITY = 1.0
HEAT_SOURCE_RANGE = (0.15, 0.85)
HEAT_MIN_SEPARATION = 0.25
HEAT_STRENGTH_RANGE = (0.5, 1.5)
HEAT_NOISE_STD = 0.05
HEAT_SIZES = {"train": 800, "val": 200, "test": 200}

# ------------------------------------------------------------ texture (Problem 4)
TEX_SIZE = 10
TEX_NAMES = ("stripes", "checker", "dots")
TEX_PERIOD = (3.0, 5.0)          # pixels per cycle (stripes, checker)
TEX_CONTRAST = (0.30, 0.50)      # half peak-to-trough amplitude
TEX_NOISE_STD = 0.20
TEX_DOTS = (3, 5)                # number of dots
TEX_DOT_RADIUS = (0.8, 1.3)
TEX_SIZES = {"train": 40, "val": 40, "unlabelled": 760, "test": 400}

# ------------------------------------------------------------ lorentz (Problem 5)
LOR_POINTS = 40
LOR_AMP_RANGE = (0.5, 2.0)
LOR_CENTER_RANGE = (0.10, 0.90)
LOR_WIDTH_RANGE = (0.02, 0.08)
LOR_SEPARATION = 1.5              # |c1 - c2| >= 1.5 * (w1 + w2)
LOR_NOISE_STD = 0.02
LOR_SIZES = {"train": 800, "val": 200, "test": 200}
ROUNDING_SLACK = 2.5e-4 + 1e-9   # worst-case shift of the separation margin from 4-dp rounding

STREAMS = {"p01": 1, "p03": 2, "heat": 3, "texture": 4, "lorentz": 5}
SPLIT_ORDER = {
    "heat": ("train", "val", "test"),
    "texture": ("train", "val", "unlabelled", "test"),
    "lorentz": ("train", "val", "test"),
}


def _rng(stream: int, sub: int) -> np.random.Generator:
    return np.random.default_rng([SEED, stream, sub])


# ---------------------------------------------------------------- Problem 1
def p01_block(n: int, rng: np.random.Generator) -> np.ndarray:
    a = rng.integers(0, P01_VOCAB, size=n)
    k = rng.choice(P01_STEPS, size=n)
    i = np.arange(P01_LEN)
    return ((a[:, None] + i[None, :] * k[:, None]) % P01_VOCAB).astype(np.int64)


def p01_payload() -> dict:
    out = {"seed": SEED, "vocab_size": P01_VOCAB, "row_length": P01_LEN}
    for sub, (split, n) in enumerate(P01_SIZES.items()):
        out[split] = p01_block(n, _rng(STREAMS["p01"], sub)).tolist()
    return out


# ---------------------------------------------------------------- Problem 3
def p03_block(n: int, rng: np.random.Generator) -> np.ndarray:
    u = rng.standard_normal((n, 2)) * np.asarray(P03_LATENT_STD)
    x = u @ P03_A.T + P03_NOISE * rng.standard_normal((n, 8))
    return np.round(x, DECIMALS)


def p03_payload() -> dict:
    out = {"seed": SEED, "features": 8}
    for sub, (split, n) in enumerate(P03_SIZES.items()):
        out[split] = p03_block(n, _rng(STREAMS["p03"], sub)).tolist()
    return out


# ---------------------------------------------------------------- heat
def heat_kernel_readings(sources: np.ndarray, strengths: np.ndarray) -> np.ndarray:
    """Noise-free readings (N, 50): time 0.005 for the 25 sensors, then time 0.02."""
    sensors = np.asarray(HEAT_SENSORS, dtype=np.float64)                      # (25, 2)
    d2 = ((sources[:, :, None, :] - sensors[None, None, :, :]) ** 2).sum(-1)   # (N, 2, 25)
    blocks = []
    for t in HEAT_TIMES:
        g = np.exp(-d2 / (4.0 * HEAT_DIFFUSIVITY * t)) / (4.0 * np.pi * HEAT_DIFFUSIVITY * t)
        blocks.append((strengths[:, :, None] * g).sum(1))
    return np.concatenate(blocks, axis=1)


def heat_block(n: int, rng: np.random.Generator):
    src = np.empty((n, 2, 2))
    for i in range(n):
        while True:
            s = rng.uniform(*HEAT_SOURCE_RANGE, size=(2, 2))
            if np.linalg.norm(s[0] - s[1]) >= HEAT_MIN_SEPARATION:
                break
        src[i] = s[np.argsort(s[:, 0], kind="stable")]
    q = rng.uniform(*HEAT_STRENGTH_RANGE, size=(n, 2))
    src = np.round(src, DECIMALS)
    q = np.round(q, DECIMALS)
    clean = heat_kernel_readings(src, q)
    noisy = clean + HEAT_NOISE_STD * rng.standard_normal(clean.shape)
    targets = np.concatenate([src[:, 0], q[:, :1], src[:, 1], q[:, 1:]], axis=1)
    return np.round(noisy, DECIMALS), targets


# ---------------------------------------------------------------- texture
_TY, _TX = np.meshgrid(np.arange(TEX_SIZE) + 0.5, np.arange(TEX_SIZE) + 0.5, indexing="ij")


def render_texture(label: int, rng: np.random.Generator) -> np.ndarray:
    contrast = rng.uniform(*TEX_CONTRAST)
    if label in (0, 1):
        period = rng.uniform(*TEX_PERIOD)
        theta = rng.uniform(0.0, np.pi)
        phase = rng.uniform(0.0, 2.0 * np.pi)
        u = _TX * np.cos(theta) + _TY * np.sin(theta)
        v = -_TX * np.sin(theta) + _TY * np.cos(theta)
        if label == 0:
            pattern = np.sin(2.0 * np.pi * u / period + phase)
        else:
            phase2 = rng.uniform(0.0, 2.0 * np.pi)
            pattern = np.sin(2.0 * np.pi * u / period + phase) * np.sin(2.0 * np.pi * v / period + phase2) * 1.6
    else:
        m = int(rng.integers(TEX_DOTS[0], TEX_DOTS[1] + 1))
        pattern = np.full((TEX_SIZE, TEX_SIZE), -0.6)
        for _ in range(m):
            cx, cy = rng.uniform(0.0, TEX_SIZE, size=2)
            r = rng.uniform(*TEX_DOT_RADIUS)
            pattern = pattern + 2.2 * np.exp(-((_TX - cx) ** 2 + (_TY - cy) ** 2) / (2.0 * r * r))
        pattern = np.clip(pattern, -1.0, 1.0)
    img = 0.5 + contrast * pattern + TEX_NOISE_STD * rng.standard_normal((TEX_SIZE, TEX_SIZE))
    return np.rint(np.clip(img, 0.0, 1.0) * 255.0).astype(np.int64).reshape(-1)


def texture_block(n: int, rng: np.random.Generator):
    labels = rng.permutation(np.arange(n) % 3)
    images = np.stack([render_texture(int(k), rng) for k in labels])
    return images, labels


# ---------------------------------------------------------------- lorentz
def lorentz_x() -> np.ndarray:
    return (np.arange(LOR_POINTS) + 0.5) / LOR_POINTS


def lorentz_values(params: np.ndarray, x: np.ndarray) -> np.ndarray:
    p = params.reshape(-1, 2, 3)
    a, c, w = p[..., 0], p[..., 1], p[..., 2]
    return (a[:, None, :] / (1.0 + ((x[None, :, None] - c[:, None, :]) / w[:, None, :]) ** 2)).sum(-1)


def lorentz_block(n: int, rng: np.random.Generator):
    params = np.empty((n, 2, 3))
    for i in range(n):
        while True:
            widths = rng.uniform(*LOR_WIDTH_RANGE, size=2)
            centers = np.sort(rng.uniform(*LOR_CENTER_RANGE, size=2))
            if centers[1] - centers[0] >= LOR_SEPARATION * widths.sum():
                break
        amps = rng.uniform(*LOR_AMP_RANGE, size=2)
        params[i] = np.stack([amps, centers, widths], axis=1)
    params = np.round(params.reshape(n, -1), DECIMALS)
    p3 = params.reshape(n, 2, 3)
    # Rounding each of c1, c2, w1, w2 to DECIMALS places moves the separation margin
    # (c2 - c1) - 1.5 (w1 + w2) by at most (2 + 2 * 1.5) * 0.5e-4 = 2.5e-4, so the rule is
    # re-checked after rounding with that slack (the draws themselves satisfy it exactly).
    # The tolerance never changes which values are drawn, so stored data are unchanged.
    if not np.all(p3[:, 1, 1] - p3[:, 0, 1] >= LOR_SEPARATION * p3[..., 2].sum(1) - ROUNDING_SLACK):
        raise ValueError("rounding broke the separation rule")
    values = lorentz_values(params, lorentz_x()) + LOR_NOISE_STD * rng.standard_normal((n, LOR_POINTS))
    return np.round(values, DECIMALS), params


# ---------------------------------------------------------------- packaging
def input_rows_float32(name: str, inputs) -> np.ndarray:
    arr = np.asarray(inputs)
    if name == "texture":
        return arr.astype("<f4") / np.float32(255.0)
    return arr.astype("<f4")


def row_sha256(row) -> str:
    array = np.ascontiguousarray(np.asarray(row, dtype="<f4")).reshape(-1)
    return hashlib.sha256(array.tobytes()).hexdigest()


SIZES = {"heat": HEAT_SIZES, "texture": TEX_SIZES, "lorentz": LOR_SIZES}
MAKERS = {"heat": heat_block, "texture": texture_block, "lorentz": lorentz_block}


def _dataset(name: str) -> dict:
    inputs, targets, splits, start = [], [], {}, 0
    for sub, split in enumerate(SPLIT_ORDER[name]):
        x, y = MAKERS[name](SIZES[name][split], _rng(STREAMS[name], sub))
        inputs.extend(np.asarray(x).tolist())
        if split == "unlabelled":
            targets.extend([None] * len(x))
        else:
            targets.extend(np.asarray(y).tolist())
        splits[split] = list(range(start, start + len(x)))
        start += len(x)
    hashes = [row_sha256(r) for r in input_rows_float32(name, inputs)]
    if len(set(hashes)) != len(hashes):
        raise ValueError(f"{name}: duplicate input rows")
    digest = hashlib.sha256("".join(hashes).encode()).hexdigest()
    return {"inputs": inputs, "targets": targets, "splits": splits, "digest": digest}


def datasets_payload() -> dict:
    return {
        "seed": SEED,
        "format_version": FORMAT_VERSION,
        "constants": {
            "heat_sensors_xy": [list(p) for p in HEAT_SENSORS],
            "heat_times": list(HEAT_TIMES),
            "heat_diffusivity": HEAT_DIFFUSIVITY,
            "texture_names": list(TEX_NAMES),
            "lorentz_points": LOR_POINTS,
        },
        "datasets": {name: _dataset(name) for name in SPLIT_ORDER},
    }


def simulate_block(task: str, n: int, seed: int):
    """Fresh draws from a task's generative process (accelerator extensions).

    ``seed`` must differ from ``SEED``; these streams never touch stored rows.
    """
    if int(seed) == SEED:
        raise ValueError("simulate() needs a seed different from the test seed")
    rng = np.random.default_rng([int(seed), 100 + STREAMS[task]])
    return MAKERS[task](int(n), rng)


def _dump(payload: dict) -> str:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"


OUTPUTS = {
    "p01_corpus.json": p01_payload,
    "p03_vae.json": p03_payload,
    "r2_001_datasets.json": datasets_payload,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="regenerate in memory and compare with the stored files")
    args = parser.parse_args(argv)
    status = 0
    for filename, build in OUTPUTS.items():
        text = _dump(build())
        path = HERE / filename
        if args.check:
            if not path.is_file():
                print(f"missing {filename}", file=sys.stderr)
                status = 1
            elif path.read_text(encoding="utf-8") != text:
                print(f"{filename} does not match a fresh regeneration", file=sys.stderr)
                status = 1
            else:
                print(f"{filename}: ok ({hashlib.sha256(text.encode()).hexdigest()[:16]})")
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {filename} ({len(text)} bytes)")
    if args.check:
        print("check ok" if status == 0 else "check FAILED")
    return status


if __name__ == "__main__":
    sys.exit(main())
