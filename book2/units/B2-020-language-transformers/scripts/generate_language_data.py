#!/usr/bin/env python3
"""Generate and verify B2-020's deterministic tiny language encoder state."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import struct
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

SEED = 20260812
SCHEMA_VERSION = 1
HERE = Path(__file__).resolve().parent
UNIT = HERE.parent
DATA = UNIT / "data"
FIXTURE_PATH = DATA / "language_fixture.py"
CHECKPOINT_PATH = DATA / "tiny_encoder_checkpoint.py"
STATE_PATH = DATA / "tiny_encoder_state.py"

ARCHITECTURE = {
    "vocab_size": 12,
    "sequence_length": 8,
    "width": 8,
    "heads": 2,
    "feed_forward_width": 16,
    "blocks": 1,
    "pre_norm": True,
    "learned_positional_embeddings": True,
    "activation": "gelu",
    "layer_norm_eps": 1e-5,
    "dropout": 0.0,
}
OBJECTIVE = {
    "causal_updates": 40,
    "mlm_updates": 40,
    "optimizer": "AdamW",
    "lr": 0.03,
    "weight_decay": 0.0,
    "betas": [0.9, 0.999],
    "eps": 1e-8,
    "amsgrad": False,
    "foreach": False,
    "fused": False,
    "reduction": "mean_non_padding_non_ignored_tokens",
    "order": "stored_ascending_full_batch",
}
TRUSTED_INITIAL_LOSSES = {"causal": 2.55220652, "mlm": 2.42422199}
TRUSTED_FINAL_LOSSES = {"causal": 0.00000476, "mlm": 0.00000060}
TRUSTED_MINIMUM_IMPROVEMENTS = {"causal": 1.020881, "mlm": 0.969689}
TRUSTED_PROBE_TOP1_IDS = {
    "causal_row0_after_red": 4,
    "causal_row1_after_blue": 5,
    "mlm_row0_position1": 4,
    "mlm_row1_position4": 4,
}
TRUSTED_TRACE_LOSS_SHA256 = "750f4bb861f1d65b7d9f814095345f0fc69f01e23ee9cbf9a524f80c7565dbc4"


def load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"b2_020_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture() -> ModuleType:
    return load_module(FIXTURE_PATH)


def _configure_determinism() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        # Import-time tests may already have initialized the inter-op pool.
        pass
    torch.use_deterministic_algorithms(True)


class TinyEncoder(nn.Module):
    """One pre-norm Transformer block with learned positions."""

    def __init__(self) -> None:
        super().__init__()
        width = ARCHITECTURE["width"]
        self.token_embedding = nn.Embedding(ARCHITECTURE["vocab_size"], width, padding_idx=0)
        self.position_embedding = nn.Embedding(ARCHITECTURE["sequence_length"], width)
        self.norm1 = nn.LayerNorm(width, eps=ARCHITECTURE["layer_norm_eps"])
        self.attention = nn.MultiheadAttention(
            width,
            ARCHITECTURE["heads"],
            dropout=0.0,
            batch_first=True,
        )
        self.norm2 = nn.LayerNorm(width, eps=ARCHITECTURE["layer_norm_eps"])
        self.ff1 = nn.Linear(width, ARCHITECTURE["feed_forward_width"])
        self.ff2 = nn.Linear(ARCHITECTURE["feed_forward_width"], width)

    def forward(self, token_ids: torch.Tensor, *, mask_mode: str) -> torch.Tensor:
        positions = torch.arange(token_ids.shape[1], device=token_ids.device)
        hidden = self.token_embedding(token_ids) + self.position_embedding(positions)[None, :, :]
        normalized = self.norm1(hidden)
        causal_mask = None
        if mask_mode == "causal":
            n = token_ids.shape[1]
            causal_mask = torch.triu(torch.ones(n, n, dtype=torch.bool), diagonal=1)
        elif mask_mode != "bidirectional":
            raise ValueError("mask_mode must be causal or bidirectional")
        padding_mask = token_ids.eq(0)
        attended, _ = self.attention(
            normalized,
            normalized,
            normalized,
            attn_mask=causal_mask,
            key_padding_mask=padding_mask,
            need_weights=False,
        )
        hidden = hidden + attended
        normalized = self.norm2(hidden)
        return hidden + self.ff2(F.gelu(self.ff1(normalized)))


def build_models() -> tuple[TinyEncoder, nn.Linear]:
    _configure_determinism()
    encoder = TinyEncoder()
    head = nn.Linear(ARCHITECTURE["width"], ARCHITECTURE["vocab_size"], bias=True)
    return encoder, head


def _causal_loss(
    encoder: TinyEncoder, head: nn.Linear, rows: list[list[int]]
) -> torch.Tensor:
    token_ids = torch.tensor(rows, dtype=torch.long)
    logits = head(encoder(token_ids, mask_mode="causal"))
    shifted_logits = logits[:, :-1, :].reshape(-1, ARCHITECTURE["vocab_size"])
    targets = token_ids[:, 1:].reshape(-1)
    return F.cross_entropy(shifted_logits, targets, ignore_index=0)


def _mlm_loss(
    encoder: TinyEncoder,
    head: nn.Linear,
    inputs: list[list[int]],
    labels: list[list[int]],
) -> torch.Tensor:
    token_ids = torch.tensor(inputs, dtype=torch.long)
    target_ids = torch.tensor(labels, dtype=torch.long)
    logits = head(encoder(token_ids, mask_mode="bidirectional"))
    return F.cross_entropy(
        logits.reshape(-1, ARCHITECTURE["vocab_size"]),
        target_ids.reshape(-1),
        ignore_index=-100,
    )


def _heldout_metrics(
    encoder: TinyEncoder, head: nn.Linear, fixture: ModuleType
) -> tuple[dict[str, float], dict[str, int]]:
    with torch.no_grad():
        losses = {
            "causal": float(_causal_loss(encoder, head, fixture.CAUSAL_HELDOUT_IDS)),
            "mlm": float(
                _mlm_loss(
                    encoder,
                    head,
                    fixture.MLM_HELDOUT_IDS,
                    fixture.MLM_HELDOUT_LABEL_IDS,
                )
            ),
        }
        causal_ids = torch.tensor(fixture.CAUSAL_HELDOUT_IDS, dtype=torch.long)
        causal_logits = head(encoder(causal_ids, mask_mode="causal"))
        mlm_ids = torch.tensor(fixture.MLM_HELDOUT_IDS, dtype=torch.long)
        mlm_logits = head(encoder(mlm_ids, mask_mode="bidirectional"))
        probes = {
            "causal_row0_after_red": int(causal_logits[0, 1].argmax()),
            "causal_row1_after_blue": int(causal_logits[1, 1].argmax()),
            "mlm_row0_position1": int(mlm_logits[0, 1].argmax()),
            "mlm_row1_position4": int(mlm_logits[1, 4].argmax()),
        }
    return losses, probes


def _tensor_mapping(module: nn.Module) -> dict[str, list[Any]]:
    return {
        name: tensor.detach().cpu().to(torch.float32).tolist()
        for name, tensor in sorted(module.state_dict().items())
    }


def _tensor_rows(mapping: dict[str, list[Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for name in sorted(mapping):
        tensor = torch.tensor(mapping[name], dtype=torch.float32)
        values = [round(float(value), 6) for value in tensor.reshape(-1)]
        rows.append([name, list(tensor.shape), "float32", values])
    return rows


def _state_tensor_rows(mapping: dict[str, list[Any]]) -> list[list[Any]]:
    """Encode each IEEE-754 float32 value exactly for the student-state hash."""
    rows: list[list[Any]] = []
    for name in sorted(mapping):
        tensor = torch.tensor(mapping[name], dtype=torch.float32)
        values = [struct.pack(">f", float(value)).hex() for value in tensor.reshape(-1)]
        rows.append([name, list(tensor.shape), "float32", values])
    return rows


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _trace_loss_digest(trace: list[dict[str, Any]]) -> str:
    losses = [row["loss"] for row in trace]
    return hashlib.sha256(_canonical_json(losses).encode()).hexdigest()


def encoder_state_hash(tensors: dict[str, list[Any]]) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "architecture": [[key, ARCHITECTURE[key]] for key in ARCHITECTURE],
        "tensors": _state_tensor_rows(tensors),
    }
    return hashlib.sha256(_canonical_json(payload).encode()).hexdigest()


def semantic_hash(
    fixture: ModuleType,
    encoder_tensors: dict[str, list[Any]],
    head_tensors: dict[str, list[Any]],
) -> str:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "vocabulary": fixture.TOKEN_TO_ID,
        "splits": {
            "train": fixture.TRAIN_SPLIT_IDS,
            "causal_heldout": fixture.CAUSAL_HELDOUT_IDS,
            "mlm_heldout": fixture.MLM_HELDOUT_IDS,
        },
        "architecture": [[key, ARCHITECTURE[key]] for key in ARCHITECTURE],
        "objective": OBJECTIVE,
        "tensors": {
            "encoder": _tensor_rows(encoder_tensors),
            "head": _tensor_rows(head_tensors),
        },
    }
    return hashlib.sha256(_canonical_json(payload).encode()).hexdigest()


def generate_protocol() -> dict[str, Any]:
    fixture = _fixture()
    encoder, head = build_models()
    initial_losses, initial_probes = _heldout_metrics(encoder, head, fixture)
    optimizer = torch.optim.AdamW(
        [*encoder.parameters(), *head.parameters()],
        lr=OBJECTIVE["lr"],
        betas=tuple(OBJECTIVE["betas"]),
        eps=OBJECTIVE["eps"],
        weight_decay=OBJECTIVE["weight_decay"],
        amsgrad=OBJECTIVE["amsgrad"],
        foreach=OBJECTIVE["foreach"],
        fused=OBJECTIVE["fused"],
    )
    trace: list[dict[str, Any]] = []
    first_parameter = next(encoder.parameters())
    for phase, updates in (("causal", 40), ("mlm", 40)):
        for update_index in range(1, updates + 1):
            optimizer.zero_grad(set_to_none=True)
            if phase == "causal":
                loss = _causal_loss(encoder, head, fixture.CAUSAL_TRAIN_IDS)
                mask_mode = "causal"
            else:
                loss = _mlm_loss(encoder, head, fixture.MLM_INPUT_IDS, fixture.MLM_LABEL_IDS)
                mask_mode = "bidirectional"
            loss.backward()
            optimizer.step()
            step = int(optimizer.state[first_parameter]["step"].item())
            trace.append(
                {
                    "phase": phase,
                    "update_index": update_index,
                    "mask_mode": mask_mode,
                    "optimizer_step": step,
                    "loss": round(float(loss.detach()), 8),
                }
            )
    final_losses, final_probes = _heldout_metrics(encoder, head, fixture)
    improvements = {
        name: initial_losses[name] - final_losses[name] for name in initial_losses
    }
    minimum_improvements = {
        name: round(max(0.01, value * 0.4), 6) for name, value in improvements.items()
    }
    encoder_tensors = _tensor_mapping(encoder)
    head_tensors = _tensor_mapping(head)
    return {
        "encoder": encoder,
        "head": head,
        "encoder_tensors": encoder_tensors,
        "head_tensors": head_tensors,
        "trace": trace,
        "initial_losses": {name: round(value, 8) for name, value in initial_losses.items()},
        "final_losses": {name: round(value, 8) for name, value in final_losses.items()},
        "initial_probes": initial_probes,
        "final_probes": final_probes,
        "minimum_improvements": minimum_improvements,
        "encoder_state_hash": encoder_state_hash(encoder_tensors),
        "semantic_hash": semantic_hash(fixture, encoder_tensors, head_tensors),
    }


def _literal(name: str, value: Any) -> str:
    return f"{name} = {repr(value)}\n"


def _checkpoint_source(result: dict[str, Any], fixture: ModuleType) -> str:
    pieces = [
        '"""Generated author/CI checkpoint for B2-020. Do not edit by hand."""\n\n',
        _literal("SCHEMA_VERSION", SCHEMA_VERSION),
        _literal("TOKEN_TO_ID", fixture.TOKEN_TO_ID),
        _literal("TRAIN_SPLIT_IDS", fixture.TRAIN_SPLIT_IDS),
        _literal("CAUSAL_HELDOUT_IDS", fixture.CAUSAL_HELDOUT_IDS),
        _literal("MLM_HELDOUT_IDS", fixture.MLM_HELDOUT_IDS),
        _literal("MLM_HELDOUT_LABEL_IDS", fixture.MLM_HELDOUT_LABEL_IDS),
        _literal("ARCHITECTURE", ARCHITECTURE),
        _literal("OBJECTIVE", OBJECTIVE),
        _literal("ENCODER_TENSORS", result["encoder_tensors"]),
        _literal("HEAD_TENSORS", result["head_tensors"]),
        _literal("INITIAL_LOSSES", result["initial_losses"]),
        _literal("FINAL_LOSSES", result["final_losses"]),
        _literal("PROBE_EXPECTED_TOP1_IDS", result["final_probes"]),
        _literal("MIN_ABSOLUTE_LOSS_IMPROVEMENTS", result["minimum_improvements"]),
        _literal("PHASE_TRACE", result["trace"]),
        _literal("SEMANTIC_HASH", result["semantic_hash"]),
        _literal("ENCODER_STATE_HASH", result["encoder_state_hash"]),
    ]
    return "".join(pieces)


def _state_source(result: dict[str, Any]) -> str:
    return "".join(
        [
            '"""Generated student-facing trained encoder state for B2-020."""\n\n',
            _literal("SCHEMA_VERSION", SCHEMA_VERSION),
            _literal("ARCHITECTURE", ARCHITECTURE),
            "import hashlib\nimport json\nimport struct\n\n",
            _literal("ENCODER_TENSORS", result["encoder_tensors"]),
            _literal("ENCODER_STATE_HASH", result["encoder_state_hash"]),
            "\n\n"
            "def _flatten(values):\n"
            "    for value in values:\n"
            "        if isinstance(value, list):\n"
            "            yield from _flatten(value)\n"
            "        else:\n"
            "            yield value\n\n"
            "\n"
            "def _shape(values):\n"
            "    shape = []\n"
            "    while isinstance(values, list):\n"
            "        shape.append(len(values))\n"
            "        values = values[0] if values else []\n"
            "    return shape\n\n"
            "\n"
            "def _float32_hex(value):\n"
            "    return struct.pack(\">f\", float(value)).hex()\n\n"
            "\n"
            "def canonical_encoder_state_hash(tensors):\n"
            "    \"\"\"Return the canonical SHA-256 fingerprint of this encoder state.\"\"\"\n"
            "    rows = []\n"
            "    for name in sorted(tensors):\n"
            "        values = tensors[name]\n"
            "        rows.append([name, _shape(values), \"float32\", [_float32_hex(value) for value in _flatten(values)]])\n"
            "    payload = {\n"
            "        \"schema_version\": SCHEMA_VERSION,\n"
            "        \"architecture\": [[key, ARCHITECTURE[key]] for key in ARCHITECTURE],\n"
            "        \"tensors\": rows,\n"
            "    }\n"
            "    encoded = json.dumps(payload, sort_keys=True, separators=(\",\", \":\"), ensure_ascii=True)\n"
            "    return hashlib.sha256(encoded.encode()).hexdigest()\n",
        ]
    )


def refresh_checkpoint() -> dict[str, Any]:
    result = generate_protocol()
    fixture = _fixture()
    new_checkpoint = _checkpoint_source(result, fixture)
    new_state = _state_source(result)
    for path, source in ((CHECKPOINT_PATH, new_checkpoint), (STATE_PATH, new_state)):
        old = path.read_text(encoding="utf-8") if path.exists() else None
        path.write_text(source, encoding="utf-8")
        label = "unchanged" if old == source else "updated"
        print(f"{label}: {path.relative_to(UNIT)}")
    print("measured losses:", result["initial_losses"], "->", result["final_losses"])
    print("minimum improvements:", result["minimum_improvements"])
    print("probes:", result["final_probes"])
    print("semantic hash:", result["semantic_hash"])
    print("encoder state hash:", result["encoder_state_hash"])
    return result


def _load_tensor_mapping(module: ModuleType, name: str) -> dict[str, torch.Tensor]:
    mapping = getattr(module, name)
    return {key: torch.tensor(value, dtype=torch.float32) for key, value in mapping.items()}


def verify_committed_artifacts() -> None:
    checkpoint = load_module(CHECKPOINT_PATH)
    state = load_module(STATE_PATH)
    fixture = _fixture()
    if checkpoint.SCHEMA_VERSION != SCHEMA_VERSION:
        raise AssertionError("checkpoint schema version mismatch")
    if checkpoint.ARCHITECTURE != ARCHITECTURE or state.ARCHITECTURE != ARCHITECTURE:
        raise AssertionError("architecture mismatch")
    if checkpoint.ENCODER_TENSORS != state.ENCODER_TENSORS:
        raise AssertionError("student state is not the checkpoint encoder projection")
    expected_state_hash = encoder_state_hash(checkpoint.ENCODER_TENSORS)
    if checkpoint.ENCODER_STATE_HASH != expected_state_hash or state.ENCODER_STATE_HASH != expected_state_hash:
        raise AssertionError("encoder state hash mismatch")
    expected_semantic = semantic_hash(
        fixture, checkpoint.ENCODER_TENSORS, checkpoint.HEAD_TENSORS
    )
    if checkpoint.SEMANTIC_HASH != expected_semantic:
        raise AssertionError("checkpoint semantic hash mismatch")
    if checkpoint.TOKEN_TO_ID != fixture.TOKEN_TO_ID:
        raise AssertionError("checkpoint vocabulary mismatch")
    if checkpoint.TRAIN_SPLIT_IDS != fixture.TRAIN_SPLIT_IDS:
        raise AssertionError("checkpoint train split mismatch")
    if checkpoint.CAUSAL_HELDOUT_IDS != fixture.CAUSAL_HELDOUT_IDS:
        raise AssertionError("checkpoint causal held-out split mismatch")
    if checkpoint.MLM_HELDOUT_IDS != fixture.MLM_HELDOUT_IDS:
        raise AssertionError("checkpoint MLM held-out split mismatch")
    if checkpoint.MLM_HELDOUT_LABEL_IDS != fixture.MLM_HELDOUT_LABEL_IDS:
        raise AssertionError("checkpoint MLM held-out labels mismatch")
    if checkpoint.OBJECTIVE != OBJECTIVE:
        raise AssertionError("checkpoint objective mismatch")
    if checkpoint.INITIAL_LOSSES != TRUSTED_INITIAL_LOSSES:
        raise AssertionError("checkpoint trusted initial losses mismatch")
    if checkpoint.FINAL_LOSSES != TRUSTED_FINAL_LOSSES:
        raise AssertionError("checkpoint trusted final losses mismatch")
    if checkpoint.MIN_ABSOLUTE_LOSS_IMPROVEMENTS != TRUSTED_MINIMUM_IMPROVEMENTS:
        raise AssertionError("checkpoint trusted improvement margins mismatch")
    if checkpoint.PROBE_EXPECTED_TOP1_IDS != TRUSTED_PROBE_TOP1_IDS:
        raise AssertionError("checkpoint trusted probes mismatch")
    initial_encoder, initial_head = build_models()
    initial_losses, _ = _heldout_metrics(initial_encoder, initial_head, fixture)
    for name, expected in initial_losses.items():
        if not np.isclose(checkpoint.INITIAL_LOSSES[name], expected, atol=1e-5, rtol=1e-5):
            raise AssertionError(f"{name} initial loss mismatch")
    expected_trace_shape = [(phase, update) for phase in ("causal", "mlm") for update in range(1, 41)]
    actual_trace_shape = [(row["phase"], row["update_index"]) for row in checkpoint.PHASE_TRACE]
    if actual_trace_shape != expected_trace_shape:
        raise AssertionError("checkpoint phase trace shape mismatch")
    if [row["optimizer_step"] for row in checkpoint.PHASE_TRACE] != list(range(1, 81)):
        raise AssertionError("checkpoint optimizer steps are not continuous")
    if [row["mask_mode"] for row in checkpoint.PHASE_TRACE] != ["causal"] * 40 + ["bidirectional"] * 40:
        raise AssertionError("checkpoint mask trace mismatch")
    if _trace_loss_digest(checkpoint.PHASE_TRACE) != TRUSTED_TRACE_LOSS_SHA256:
        raise AssertionError("checkpoint trusted trace losses mismatch")
    encoder, head = build_models()
    encoder.load_state_dict(_load_tensor_mapping(checkpoint, "ENCODER_TENSORS"), strict=True)
    head.load_state_dict(_load_tensor_mapping(checkpoint, "HEAD_TENSORS"), strict=True)
    for name, tensor in [*encoder.state_dict().items(), *head.state_dict().items()]:
        if tensor.dtype != torch.float32:
            raise AssertionError(f"{name}: expected float32")
    losses, probes = _heldout_metrics(encoder, head, fixture)
    for name, expected in checkpoint.FINAL_LOSSES.items():
        if not np.isclose(losses[name], expected, atol=1e-5, rtol=1e-5):
            raise AssertionError(f"{name} final loss mismatch: {losses[name]} != {expected}")
        improvement = initial_losses[name] - losses[name]
        if improvement < checkpoint.MIN_ABSOLUTE_LOSS_IMPROVEMENTS[name]:
            raise AssertionError(f"{name} improvement is below frozen margin")
    if probes != checkpoint.PROBE_EXPECTED_TOP1_IDS:
        raise AssertionError(f"probe mismatch: {probes}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refresh-checkpoint", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.refresh_checkpoint:
        refresh_checkpoint()
    else:
        verify_committed_artifacts()
        print("PASS B2-020 committed checkpoint/state contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
