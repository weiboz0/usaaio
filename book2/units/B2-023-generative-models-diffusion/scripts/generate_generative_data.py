#!/usr/bin/env python3
"""Generate and check the seeded B2-023 generative-model datasets.

Two tiny CPU datasets are produced from ``SEED`` with NumPy's PCG64 stream:

* ``mixture2d`` -- 320 rows, 2 features: a four-component isotropic Gaussian
  mixture with literal centers ``MIX2D_CENTERS`` and standard deviation
  ``MIX2D_STD`` (row ``i`` belongs to component ``i % 4``). Values are rounded
  to four decimals.
* ``latent4d`` -- 240 rows, 4 features, with a class label: row ``i`` has class
  ``i % 3``. A 2-D latent is drawn around the literal class center
  ``LATENT_CENTERS[c]`` with standard deviation ``LATENT_STD`` and rounded to a
  multiple of 1/256; the stored row is ``decode(z) = z @ ENCODER``, where
  ``ENCODER`` is the literal ``(2,4)`` matrix with orthonormal rows. Because
  every entry is a dyadic rational, ``decode(encode(x)) == x`` holds exactly in
  float32 for every stored row (``encode(x) = x @ ENCODER.T``).

Splits are immutable literal index tuples: row ``i`` is held out exactly when
``i % 5 == 4`` and is a training row otherwise. That gives 256 train / 64
held-out rows for ``mixture2d`` (64 / 16 per component) and 192 train / 48
held-out rows for ``latent4d`` (64 / 16 per class).
The canonical per-row SHA-256 is the digest of the row's little-endian float32
bytes, so any tensor row a model or seam receives can be hashed and looked up.

Running the script writes ``data/generative_datasets.json``. ``--check``
regenerates everything in memory, compares rows, labels, splits, constants, and
hashes with the stored file, and exits nonzero on any mismatch. The script
never trains a model and never stores weights, losses, samples, or any other
result of training.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import MappingProxyType

import numpy as np

SEED = 20261015
DATASET_NAMES = ("mixture2d", "latent4d")
N_ROWS = MappingProxyType({"mixture2d": 320, "latent4d": 240})
DATASET_DIMS = MappingProxyType({"mixture2d": 2, "latent4d": 4})

HELDOUT_IDS = MappingProxyType(
    {name: tuple(i for i in range(N_ROWS[name]) if i % 5 == 4) for name in DATASET_NAMES}
)
TRAIN_IDS = MappingProxyType(
    {name: tuple(i for i in range(N_ROWS[name]) if i % 5 != 4) for name in DATASET_NAMES}
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "generative_datasets.json"

# Literal generation constants (never fitted, never trained).
MIX2D_CENTERS = ((1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), (1.0, -1.0))
MIX2D_STD = 0.2
MIX2D_DECIMALS = 4

LATENT_CENTERS = ((0.0, 3.0), (-2.5, -1.5), (2.5, -1.5))
LATENT_STD = 1.25
LATENT_GRID = 256  # latents are rounded to multiples of 1/256
# Rows of ENCODER are orthonormal; the decoder is its transpose.
ENCODER = ((0.5, 0.5, 0.5, 0.5), (0.5, -0.5, -0.5, 0.5))
LATENT_SCALE = 0.25


def _rng(index: int) -> np.random.Generator:
    return np.random.default_rng([SEED, index])


def _mixture2d() -> tuple[list[list[float]], list[int]]:
    rng = _rng(0)
    noise = rng.standard_normal((N_ROWS["mixture2d"], 2))
    rows, labels = [], []
    for i in range(N_ROWS["mixture2d"]):
        k = i % 4
        cx, cy = MIX2D_CENTERS[k]
        rows.append([
            round(float(cx + MIX2D_STD * noise[i, 0]), MIX2D_DECIMALS),
            round(float(cy + MIX2D_STD * noise[i, 1]), MIX2D_DECIMALS),
        ])
        labels.append(k)
    return rows, labels


def _latent4d() -> tuple[list[list[float]], list[int]]:
    rng = _rng(1)
    noise = rng.standard_normal((N_ROWS["latent4d"], 2))
    rows, labels = [], []
    for i in range(N_ROWS["latent4d"]):
        c = i % 3
        z = [
            round((LATENT_CENTERS[c][j] + LATENT_STD * float(noise[i, j])) * LATENT_GRID) / LATENT_GRID
            for j in range(2)
        ]
        # decode(z) = z @ ENCODER, computed in exact dyadic arithmetic.
        rows.append([z[0] * ENCODER[0][m] + z[1] * ENCODER[1][m] for m in range(4)])
        labels.append(c)
    return rows, labels


_BUILDERS = {"mixture2d": _mixture2d, "latent4d": _latent4d}


def canonical_row_sha256(row) -> str:
    """SHA-256 of one row's contiguous little-endian float32 bytes."""
    array = np.ascontiguousarray(np.asarray(row, dtype="<f4")).reshape(-1)
    return hashlib.sha256(array.tobytes()).hexdigest()


def _check_exact_roundtrip(rows: list[list[float]]) -> None:
    x = np.asarray(rows, dtype=np.float32)
    enc = np.asarray(ENCODER, dtype=np.float32)
    if not np.array_equal((x @ enc.T) @ enc, x):
        raise ValueError("latent4d: decode(encode(x)) != x in float32")
    if not np.array_equal(enc @ enc.T, np.eye(2, dtype=np.float32)):
        raise ValueError("ENCODER rows are not orthonormal")


def build_payload() -> dict:
    datasets = {}
    for name in DATASET_NAMES:
        rows, labels = _BUILDERS[name]()
        if name == "latent4d":
            _check_exact_roundtrip(rows)
        hashes = [canonical_row_sha256(row) for row in rows]
        if len(set(hashes)) != len(hashes):
            raise ValueError(f"{name}: duplicate row hash")
        train, held = TRAIN_IDS[name], HELDOUT_IDS[name]
        if set(train) & set(held) or sorted(train + held) != list(range(N_ROWS[name])):
            raise ValueError(f"{name}: splits must partition the rows")
        datasets[name] = {
            "dim": DATASET_DIMS[name],
            "rows": rows,
            "labels": labels,
            "train_ids": list(train),
            "heldout_ids": list(held),
            "row_sha256": hashes,
        }
    return {
        "unit": "B2-023-generative-models-diffusion",
        "seed": SEED,
        "hash_convention": "sha256 of little-endian float32 row bytes",
        "constants": {
            "mixture2d_centers": [list(c) for c in MIX2D_CENTERS],
            "mixture2d_std": MIX2D_STD,
            "latent_centers": [list(c) for c in LATENT_CENTERS],
            "latent_std": LATENT_STD,
            "encoder": [list(r) for r in ENCODER],
            "latent_scale": LATENT_SCALE,
        },
        "datasets": datasets,
    }


ROW_SHA256 = MappingProxyType(
    {name: tuple(canonical_row_sha256(row) for row in _BUILDERS[name]()[0]) for name in DATASET_NAMES}
)


def _serialize(payload: dict) -> str:
    return json.dumps(payload, indent=1, sort_keys=True) + "\n"


def check() -> int:
    if not DATA_PATH.is_file():
        print(f"FAIL: missing {DATA_PATH}")
        return 1
    text = DATA_PATH.read_text(encoding="utf-8")
    stored = json.loads(text)
    fresh = build_payload()
    problems = []
    if stored.get("seed") != SEED:
        problems.append("seed mismatch")
    if stored.get("constants") != fresh["constants"]:
        problems.append("constants mismatch")
    if set(stored.get("datasets", {})) != set(DATASET_NAMES):
        problems.append("unexpected dataset names")
    for name in DATASET_NAMES:
        s, f = stored.get("datasets", {}).get(name), fresh["datasets"][name]
        if s is None:
            problems.append(f"{name}: missing")
            continue
        for key in ("dim", "rows", "labels", "train_ids", "heldout_ids", "row_sha256"):
            if s.get(key) != f[key]:
                problems.append(f"{name}: {key} mismatch")
        recomputed = [canonical_row_sha256(row) for row in s.get("rows", [])]
        if recomputed != list(ROW_SHA256[name]):
            problems.append(f"{name}: stored rows do not hash to the canonical map")
    if _serialize(stored) != text:
        problems.append("stored file is not in canonical serialization")
    if problems:
        for problem in problems:
            print("FAIL:", problem)
        return 1
    print(
        "PASS: regenerated rows, labels, immutable TRAIN_IDS/HELDOUT_IDS splits, literal "
        f"constants, and canonical per-row SHA-256 hashes match {DATA_PATH.name} for "
        f"{', '.join(DATASET_NAMES)}"
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
