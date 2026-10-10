"""Read-only loader for the B2-023 seeded generative-model datasets.

The rows live in ``generative_datasets.json`` next to this file and are produced
by ``scripts/generate_generative_data.py`` (seed 20261015). Importing this
module verifies every stored row against its canonical SHA-256 (little-endian
float32 row bytes), verifies that each split partitions the rows, and verifies
that the frozen ``latent4d`` encoder/decoder pair reconstructs every row exactly.

Public surface:

* ``DATASET_NAMES`` -- ``("mixture2d", "latent4d")``.
* ``TRAIN_IDS`` / ``HELDOUT_IDS`` -- read-only maps from dataset name to an
  immutable tuple of row indices in stored (ascending) order.
* ``ROW_SHA256`` -- read-only map from dataset name to a tuple of row hashes.
* ``row_sha256(row)`` -- canonical hash of one row (Torch tensor, NumPy array,
  or list of numbers).
* ``load_rows(name, ids)`` -- a fresh ``torch.float32`` tensor ``(len(ids), dim)``.
* ``load_labels(name, ids)`` -- a fresh ``torch.int64`` tensor ``(len(ids),)``
  (component index for ``mixture2d``, class index for ``latent4d``).
* ``train_tensor(name)`` / ``heldout_tensor(name)`` and ``train_label_tensor(name)``
  / ``heldout_label_tensor(name)`` -- the same on the stored split IDs.
* ``mixture_centers()`` -- float32 ``(4,2)`` literal ``mixture2d`` centers.
* ``encoder_matrix()`` -- float32 ``(2,4)`` literal frozen encoder ``E`` with
  orthonormal rows; ``encode(x) = x @ E.T`` and ``decode(z) = z @ E``.
* ``latent_centers()`` -- float32 ``(3,2)`` literal class centers in latent space;
  ``class_centers()`` -- float32 ``(3,4)`` the same centers decoded to data space.
* ``LATENT_SCALE`` -- the literal latent scaling factor ``0.25``.

No trained weights, losses, samples, or other training results are stored here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType

import numpy as np
import torch

SEED = 20261015
DATA_PATH = Path(__file__).resolve().with_name("generative_datasets.json")
_PAYLOAD = json.loads(DATA_PATH.read_text(encoding="utf-8"))
if _PAYLOAD.get("seed") != SEED:
    raise ValueError("generative_datasets.json was not generated with seed 20261015")

DATASET_NAMES = ("mixture2d", "latent4d")
if set(_PAYLOAD["datasets"]) != set(DATASET_NAMES):
    raise ValueError("unexpected dataset names")
_CONSTANTS = _PAYLOAD["constants"]
LATENT_SCALE = float(_CONSTANTS["latent_scale"])


def row_sha256(row) -> str:
    """Canonical SHA-256 of one row's contiguous little-endian float32 bytes."""
    if isinstance(row, torch.Tensor):
        row = row.detach().cpu().numpy()
    array = np.ascontiguousarray(np.asarray(row, dtype="<f4")).reshape(-1)
    return hashlib.sha256(array.tobytes()).hexdigest()


def _frozen_rows(name: str) -> tuple[np.ndarray, np.ndarray]:
    entry = _PAYLOAD["datasets"][name]
    array = np.asarray(entry["rows"], dtype="<f4")
    labels = np.asarray(entry["labels"], dtype=np.int64)
    if array.shape != (len(entry["rows"]), entry["dim"]) or labels.shape != (array.shape[0],):
        raise ValueError(f"{name}: unexpected row or label shape")
    hashes = tuple(row_sha256(row) for row in array)
    if hashes != tuple(entry["row_sha256"]):
        raise ValueError(f"{name}: stored rows do not match their canonical hashes")
    if len(set(hashes)) != len(hashes):
        raise ValueError(f"{name}: duplicate rows")
    train, held = entry["train_ids"], entry["heldout_ids"]
    if set(train) & set(held) or sorted(train + held) != list(range(len(hashes))):
        raise ValueError(f"{name}: train and held-out IDs must partition the rows")
    array.setflags(write=False)
    labels.setflags(write=False)
    return array, labels


_DATA = {name: _frozen_rows(name) for name in DATASET_NAMES}
_ENCODER = np.asarray(_CONSTANTS["encoder"], dtype=np.float32)
if not np.array_equal(_ENCODER @ _ENCODER.T, np.eye(2, dtype=np.float32)):
    raise ValueError("frozen encoder rows are not orthonormal")
if not np.array_equal((_DATA["latent4d"][0] @ _ENCODER.T) @ _ENCODER, _DATA["latent4d"][0]):
    raise ValueError("latent4d rows are not exactly reconstructed by the frozen pair")

TRAIN_IDS = MappingProxyType(
    {name: tuple(_PAYLOAD["datasets"][name]["train_ids"]) for name in DATASET_NAMES}
)
HELDOUT_IDS = MappingProxyType(
    {name: tuple(_PAYLOAD["datasets"][name]["heldout_ids"]) for name in DATASET_NAMES}
)
ROW_SHA256 = MappingProxyType(
    {name: tuple(_PAYLOAD["datasets"][name]["row_sha256"]) for name in DATASET_NAMES}
)


def _check_ids(name: str, ids) -> list[int]:
    ids = [int(i) for i in ids]
    n = _DATA[name][0].shape[0]
    if any(i < 0 or i >= n for i in ids):
        raise KeyError(f"{name}: unknown row id in {ids}")
    return ids


def load_rows(name: str, ids) -> torch.Tensor:
    """Fresh float32 tensor of the requested rows, in the requested order."""
    return torch.from_numpy(_DATA[name][0][_check_ids(name, ids)].copy())


def load_labels(name: str, ids) -> torch.Tensor:
    """Fresh int64 tensor of the requested labels, in the requested order."""
    return torch.from_numpy(_DATA[name][1][_check_ids(name, ids)].copy())


def train_tensor(name: str) -> torch.Tensor:
    return load_rows(name, TRAIN_IDS[name])


def heldout_tensor(name: str) -> torch.Tensor:
    return load_rows(name, HELDOUT_IDS[name])


def train_label_tensor(name: str) -> torch.Tensor:
    return load_labels(name, TRAIN_IDS[name])


def heldout_label_tensor(name: str) -> torch.Tensor:
    return load_labels(name, HELDOUT_IDS[name])


def mixture_centers() -> torch.Tensor:
    return torch.tensor(_CONSTANTS["mixture2d_centers"], dtype=torch.float32)


def encoder_matrix() -> torch.Tensor:
    return torch.from_numpy(_ENCODER.copy())


def latent_centers() -> torch.Tensor:
    return torch.tensor(_CONSTANTS["latent_centers"], dtype=torch.float32)


def class_centers() -> torch.Tensor:
    return latent_centers() @ encoder_matrix()
