#!/usr/bin/env python3
"""Generate and check the seeded B2-022 latent-model datasets.

Three tiny CPU datasets are produced from ``SEED`` with NumPy's PCG64 stream:

* ``mixture2d`` -- 60 rows, 2 features: a three-component full-covariance
  Gaussian mixture (row ``i`` belongs to component ``i % 3``).
* ``mixture8d`` -- 60 rows, 8 features: a three-component 2-D latent mixture
  embedded in 8-D by a literal matrix plus an offset and small isotropic noise.
* ``lowrank8d`` -- 60 rows, 8 features: a rank-2 signal along two literal
  orthonormal directions with distinct variances, an offset, and small noise.

Every stored value is rounded to four decimals and read back as float32.
Splits are immutable literal index tuples: row ``i`` is held out exactly when
``i % 5 == 4`` (12 rows) and is a training row otherwise (48 rows).
The canonical per-row SHA-256 is the digest of the row's little-endian float32
bytes, so any tensor row a model receives can be hashed and looked up.

Running the script writes ``data/latent_datasets.json``. ``--check`` regenerates
everything in memory, compares rows, splits, and hashes with the stored file,
and exits nonzero on any mismatch. The script never trains a model and never
stores weights, losses, or any other result of training.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import MappingProxyType

import numpy as np

SEED = 20260927
N_ROWS = 60
DECIMALS = 4
DATASET_NAMES = ("mixture2d", "mixture8d", "lowrank8d")
DATASET_DIMS = MappingProxyType({"mixture2d": 2, "mixture8d": 8, "lowrank8d": 8})

HELDOUT_IDS = MappingProxyType(
    {name: tuple(i for i in range(N_ROWS) if i % 5 == 4) for name in DATASET_NAMES}
)
TRAIN_IDS = MappingProxyType(
    {name: tuple(i for i in range(N_ROWS) if i % 5 != 4) for name in DATASET_NAMES}
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "latent_datasets.json"

# Literal generation constants (never fitted, never trained).
MIX2D_MEANS = ((-2.0, 0.0), (2.0, 0.0), (0.0, 2.5))
# Each covariance is (s11, s12, s22) for [[s11, s12], [s12, s22]].
MIX2D_COVS = ((0.30, 0.12, 0.20), (0.20, -0.08, 0.30), (0.25, 0.0, 0.15))
MIX8D_LATENT_MEANS = ((-2.0, 0.0), (2.0, 0.0), (0.0, 2.5))
MIX8D_LATENT_STD = 0.45
MIX8D_EMBED = (
    (0.8, 0.1), (-0.5, 0.6), (0.3, -0.7), (0.0, 0.9),
    (0.6, 0.4), (-0.2, -0.3), (0.7, -0.1), (-0.4, 0.5),
)
MIX8D_OFFSET = (0.5, -0.25, 0.0, 1.0, -0.5, 0.25, 0.0, -1.0)
MIX8D_NOISE_STD = 0.05
LOWRANK_U1 = tuple(v / np.sqrt(8.0) for v in (1, -1, 1, -1, 1, -1, 1, -1))
LOWRANK_U2 = tuple(v / np.sqrt(8.0) for v in (1, 1, -1, -1, 1, 1, -1, -1))
LOWRANK_STDS = (2.0, 1.0)
LOWRANK_OFFSET = (0.5, -0.5, 1.0, 0.0, 0.0, 0.25, -0.25, 0.5)
LOWRANK_NOISE_STD = 0.1


def _rng(index: int) -> np.random.Generator:
    return np.random.default_rng([SEED, index])


def _mixture2d() -> np.ndarray:
    rng = _rng(0)
    z = rng.standard_normal((N_ROWS, 2))
    rows = np.empty((N_ROWS, 2), dtype=np.float64)
    for i in range(N_ROWS):
        k = i % 3
        s11, s12, s22 = MIX2D_COVS[k]
        # Explicit 2x2 Cholesky factor: L = [[a, 0], [b, c]].
        a = np.sqrt(s11)
        b = s12 / a
        c = np.sqrt(s22 - b * b)
        rows[i, 0] = MIX2D_MEANS[k][0] + a * z[i, 0]
        rows[i, 1] = MIX2D_MEANS[k][1] + b * z[i, 0] + c * z[i, 1]
    return rows


def _mixture8d() -> np.ndarray:
    rng = _rng(1)
    latent_noise = rng.standard_normal((N_ROWS, 2))
    feature_noise = rng.standard_normal((N_ROWS, 8))
    rows = np.empty((N_ROWS, 8), dtype=np.float64)
    for i in range(N_ROWS):
        k = i % 3
        h0 = MIX8D_LATENT_MEANS[k][0] + MIX8D_LATENT_STD * latent_noise[i, 0]
        h1 = MIX8D_LATENT_MEANS[k][1] + MIX8D_LATENT_STD * latent_noise[i, 1]
        for j in range(8):
            rows[i, j] = (
                MIX8D_OFFSET[j]
                + MIX8D_EMBED[j][0] * h0
                + MIX8D_EMBED[j][1] * h1
                + MIX8D_NOISE_STD * feature_noise[i, j]
            )
    return rows


def _lowrank8d() -> np.ndarray:
    rng = _rng(2)
    scores = rng.standard_normal((N_ROWS, 2))
    noise = rng.standard_normal((N_ROWS, 8))
    rows = np.empty((N_ROWS, 8), dtype=np.float64)
    for i in range(N_ROWS):
        s1 = LOWRANK_STDS[0] * scores[i, 0]
        s2 = LOWRANK_STDS[1] * scores[i, 1]
        for j in range(8):
            rows[i, j] = (
                LOWRANK_OFFSET[j]
                + s1 * LOWRANK_U1[j]
                + s2 * LOWRANK_U2[j]
                + LOWRANK_NOISE_STD * noise[i, j]
            )
    return rows


_BUILDERS = {"mixture2d": _mixture2d, "mixture8d": _mixture8d, "lowrank8d": _lowrank8d}


def canonical_row_sha256(row) -> str:
    """SHA-256 of one row's contiguous little-endian float32 bytes."""
    array = np.ascontiguousarray(np.asarray(row, dtype="<f4")).reshape(-1)
    return hashlib.sha256(array.tobytes()).hexdigest()


def generate_values(name: str) -> list[list[float]]:
    """Return the rounded literal values for one dataset (Python floats)."""
    raw = _BUILDERS[name]()
    return [[round(float(v), DECIMALS) for v in row] for row in raw]


def build_payload() -> dict:
    datasets = {}
    for name in DATASET_NAMES:
        values = generate_values(name)
        hashes = [canonical_row_sha256(row) for row in values]
        if len(set(hashes)) != len(hashes):
            raise ValueError(f"{name}: duplicate row hash")
        train, held = TRAIN_IDS[name], HELDOUT_IDS[name]
        if set(train) & set(held) or sorted(train + held) != list(range(N_ROWS)):
            raise ValueError(f"{name}: splits must partition the rows")
        datasets[name] = {
            "dim": DATASET_DIMS[name],
            "rows": values,
            "train_ids": list(train),
            "heldout_ids": list(held),
            "row_sha256": hashes,
        }
    return {
        "unit": "B2-022-probabilistic-latent-models",
        "seed": SEED,
        "decimals": DECIMALS,
        "hash_convention": "sha256 of little-endian float32 row bytes",
        "datasets": datasets,
    }


ROW_SHA256 = MappingProxyType(
    {name: tuple(canonical_row_sha256(row) for row in generate_values(name)) for name in DATASET_NAMES}
)


def _serialize(payload: dict) -> str:
    return json.dumps(payload, indent=1, sort_keys=True) + "\n"


def check() -> int:
    if not DATA_PATH.is_file():
        print(f"FAIL: missing {DATA_PATH}")
        return 1
    stored = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    fresh = build_payload()
    problems = []
    if stored.get("seed") != SEED:
        problems.append("seed mismatch")
    for name in DATASET_NAMES:
        s, f = stored["datasets"].get(name), fresh["datasets"][name]
        if s is None:
            problems.append(f"{name}: missing")
            continue
        for key in ("dim", "rows", "train_ids", "heldout_ids", "row_sha256"):
            if s.get(key) != f[key]:
                problems.append(f"{name}: {key} mismatch")
        recomputed = [canonical_row_sha256(row) for row in s.get("rows", [])]
        if recomputed != list(ROW_SHA256[name]):
            problems.append(f"{name}: stored rows do not hash to the canonical map")
    if set(stored["datasets"]) != set(DATASET_NAMES):
        problems.append("unexpected dataset names")
    if _serialize(stored) != DATA_PATH.read_text(encoding="utf-8"):
        problems.append("stored file is not in canonical serialization")
    if problems:
        for problem in problems:
            print("FAIL:", problem)
        return 1
    print(
        "PASS: regenerated rows, immutable TRAIN_IDS/HELDOUT_IDS splits, and canonical "
        f"per-row SHA-256 hashes match {DATA_PATH.name} for {', '.join(DATASET_NAMES)}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify the stored data file")
    args = parser.parse_args(argv)
    if args.check:
        return check()
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(_serialize(build_payload()), encoding="utf-8")
    print(f"wrote {DATA_PATH}")
    return 0


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    sys.exit(main())
