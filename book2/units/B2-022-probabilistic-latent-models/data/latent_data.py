"""Read-only loader for the B2-022 seeded latent-model datasets.

The rows live in ``latent_datasets.json`` next to this file and are produced by
``scripts/generate_latent_data.py`` (seed 20260927). Importing this module
verifies every stored row against its canonical SHA-256 (little-endian float32
row bytes) and verifies that each split partitions the rows.

Public surface:

* ``DATASET_NAMES`` -- ``("mixture2d", "mixture8d", "lowrank8d")``.
* ``TRAIN_IDS`` / ``HELDOUT_IDS`` -- read-only maps from dataset name to an
  immutable tuple of row indices in stored (ascending) order.
* ``ROW_SHA256`` -- read-only map from dataset name to a tuple of row hashes.
* ``row_sha256(row)`` -- canonical hash of one row (Torch tensor, NumPy array,
  or list of numbers).
* ``load_rows(name, ids)`` -- a fresh ``torch.float32`` tensor ``(len(ids), dim)``
  holding the requested rows in the requested order.
* ``train_tensor(name)`` / ``heldout_tensor(name)`` -- ``load_rows`` on the
  stored train or held-out IDs.

No trained weights, losses, or other training results are stored here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType

import numpy as np
import torch

SEED = 20260927
DATA_PATH = Path(__file__).resolve().with_name("latent_datasets.json")
_PAYLOAD = json.loads(DATA_PATH.read_text(encoding="utf-8"))
if _PAYLOAD.get("seed") != SEED:
    raise ValueError("latent_datasets.json was not generated with seed 20260927")

DATASET_NAMES = tuple(sorted(_PAYLOAD["datasets"], key=("mixture2d", "mixture8d", "lowrank8d").index))


def row_sha256(row) -> str:
    """Canonical SHA-256 of one row's contiguous little-endian float32 bytes."""
    if isinstance(row, torch.Tensor):
        row = row.detach().cpu().numpy()
    array = np.ascontiguousarray(np.asarray(row, dtype="<f4")).reshape(-1)
    return hashlib.sha256(array.tobytes()).hexdigest()


def _frozen_rows(name: str) -> np.ndarray:
    entry = _PAYLOAD["datasets"][name]
    array = np.asarray(entry["rows"], dtype="<f4")
    if array.shape != (len(entry["rows"]), entry["dim"]):
        raise ValueError(f"{name}: unexpected row shape {array.shape}")
    hashes = tuple(row_sha256(row) for row in array)
    if hashes != tuple(entry["row_sha256"]):
        raise ValueError(f"{name}: stored rows do not match their canonical hashes")
    if len(set(hashes)) != len(hashes):
        raise ValueError(f"{name}: duplicate rows")
    train, held = entry["train_ids"], entry["heldout_ids"]
    if set(train) & set(held) or sorted(train + held) != list(range(len(hashes))):
        raise ValueError(f"{name}: train and held-out IDs must partition the rows")
    array.setflags(write=False)
    return array


_ROWS = {name: _frozen_rows(name) for name in DATASET_NAMES}
TRAIN_IDS = MappingProxyType(
    {name: tuple(_PAYLOAD["datasets"][name]["train_ids"]) for name in DATASET_NAMES}
)
HELDOUT_IDS = MappingProxyType(
    {name: tuple(_PAYLOAD["datasets"][name]["heldout_ids"]) for name in DATASET_NAMES}
)
ROW_SHA256 = MappingProxyType(
    {name: tuple(_PAYLOAD["datasets"][name]["row_sha256"]) for name in DATASET_NAMES}
)


def load_rows(name: str, ids) -> torch.Tensor:
    """Fresh float32 tensor of the requested rows, in the requested order."""
    ids = tuple(int(i) for i in ids)
    rows = _ROWS[name]
    if any(i < 0 or i >= rows.shape[0] for i in ids):
        raise KeyError(f"{name}: unknown row id in {ids}")
    return torch.from_numpy(rows[list(ids)].copy())


def train_tensor(name: str) -> torch.Tensor:
    return load_rows(name, TRAIN_IDS[name])


def heldout_tensor(name: str) -> torch.Tensor:
    return load_rows(name, HELDOUT_IDS[name])
