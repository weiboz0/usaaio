"""Independent CI oracle for the B2-021 training integrity checks.

This module deliberately does not import any book, learner, generator, or
solution module.  It reconstructs the literal examples and the four tiny
models from the public exercise contracts, then records scalar traces and
shape probes only.  Trained parameter arrays are never serialized or stored.
"""

from __future__ import annotations

import hashlib
import math
import random
import struct
from collections.abc import Mapping
from types import MappingProxyType

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

SEED = 20260901

TASK_SPLITS = MappingProxyType(
    {
        task: MappingProxyType(
            {
                "train": tuple(f"{task}-train-{index:02}" for index in range(4)),
                "heldout": tuple(f"{task}-heldout-{index:02}" for index in range(2)),
            }
        )
        for task in ("vit", "detection", "segmentation", "graph")
    }
)

EXPECTED_ADAMW_LR = MappingProxyType(
    {
        "vit": 0.05,
        "detection": 0.05,
        "segmentation": 0.03,
        "graph": 0.05,
    }
)

EXPECTED_TRAINING_STEPS = MappingProxyType(
    {
        "vit": 12,
        "detection": 16,
        "segmentation": 16,
        "graph": 12,
    }
)


def canonical_array_fingerprint(
    components: tuple[tuple[str, np.ndarray], ...],
) -> str:
    """Hash ordered field/type/dtype/shape/byte data without book imports."""
    digest = hashlib.sha256()
    for name, value in components:
        if not isinstance(value, np.ndarray):
            raise TypeError("canonical fields must be NumPy arrays")
        array = np.ascontiguousarray(value)
        for text in (name, "numpy.ndarray", array.dtype.str):
            encoded = text.encode("utf-8")
            digest.update(struct.pack(">I", len(encoded)))
            digest.update(encoded)
        digest.update(struct.pack(">I", array.ndim))
        for size in array.shape:
            digest.update(struct.pack(">Q", size))
        payload = array.tobytes(order="C")
        digest.update(struct.pack(">Q", len(payload)))
        digest.update(payload)
    return digest.hexdigest()


def _image_with_box(box: tuple[int, int, int, int]) -> np.ndarray:
    image = np.zeros((1, 8, 8), dtype=np.float32)
    x0, y0, x1, y1 = box
    image[:, y0:y1, x0:x1] = 1
    return image


def _segmentation_example(top: int, left: int, noise_column: int) -> tuple[np.ndarray, np.ndarray]:
    mask = np.zeros((8, 8), dtype=np.int64)
    mask[top : top + 2, left : left + 2] = 1
    image = mask.astype(np.float32)[None, ...]
    image[0, 0, noise_column] = np.float32(0.05)
    return image, mask


def _examples() -> dict[str, tuple[str, dict[str, np.ndarray], dict[str, np.ndarray]]]:
    rows: dict[str, tuple[str, dict[str, np.ndarray], dict[str, np.ndarray]]] = {}
    column_image = np.zeros((1, 4, 4), dtype=np.float32)
    column_image[:, :, 1] = np.float32(0.3)
    first_column = np.zeros((1, 4, 4), dtype=np.float32)
    first_column[:, :, 0] = np.float32(0.2)
    heldout_first_column = np.zeros((1, 4, 4), dtype=np.float32)
    heldout_first_column[:, :, 0] = np.float32(0.25)
    vit_images = (
        first_column,
        column_image,
        np.pad(np.full((1, 1, 4), 0.8, dtype=np.float32), ((0, 0), (0, 3), (0, 0))),
        np.pad(np.ones((1, 1, 4), dtype=np.float32), ((0, 0), (1, 2), (0, 0))),
        heldout_first_column,
        np.pad(np.full((1, 1, 4), 0.9, dtype=np.float32), ((0, 0), (0, 3), (0, 0))),
    )
    vit_ids = (*TASK_SPLITS["vit"]["train"], *TASK_SPLITS["vit"]["heldout"])
    for example_id, image, label in zip(vit_ids, vit_images, (0, 0, 1, 1, 0, 1), strict=True):
        rows[example_id] = (
            "vit",
            {"image": image},
            {"label": np.asarray(label, dtype=np.int64)},
        )

    detection_boxes = (
        (0, 0, 2, 2),
        (2, 1, 4, 3),
        (4, 4, 6, 6),
        (6, 2, 8, 4),
        (2, 4, 4, 6),
        (4, 0, 6, 2),
    )
    detection_ids = (
        *TASK_SPLITS["detection"]["train"],
        *TASK_SPLITS["detection"]["heldout"],
    )
    for example_id, box, label in zip(
        detection_ids, detection_boxes, (0, 1, 0, 1, 0, 1), strict=True
    ):
        rows[example_id] = (
            "detection",
            {"image": _image_with_box(box)},
            {
                "boxes": np.asarray([box], dtype=np.float32),
                "labels": np.asarray([label], dtype=np.int64),
            },
        )

    segmentation_geometry = (
        (1, 1, 6),
        (1, 5, 7),
        (5, 1, 0),
        (5, 5, 1),
        (3, 1, 5),
        (3, 5, 6),
    )
    segmentation_ids = (
        *TASK_SPLITS["segmentation"]["train"],
        *TASK_SPLITS["segmentation"]["heldout"],
    )
    for example_id, geometry in zip(segmentation_ids, segmentation_geometry, strict=True):
        image, mask = _segmentation_example(*geometry)
        rows[example_id] = ("segmentation", {"image": image}, {"mask": mask})

    graph_nodes = (
        ((2, 0, 0), (2, 0, 0), (1, 0, 0), (1, 0, 0)),
        ((1, 0, 0), (2, 0, 0), (2, 0, 0), (1, 0, 0)),
        ((0, 2, 0), (0, 2, 0), (0, 1, 0), (0, 1, 0)),
        ((0, 1, 0), (0, 2, 0), (0, 2, 0), (0, 1, 0)),
        ((2, 0, 0.1), (1, 0, 0), (2, 0, 0), (1, 0, 0)),
        ((0, 2, 0.1), (0, 1, 0), (0, 2, 0), (0, 1, 0)),
    )
    graph_adjacency = (
        ((1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 1, 1), (0, 0, 0, 1)),
        ((1, 0, 1, 0), (0, 1, 0, 1), (0, 1, 1, 0), (0, 0, 0, 1)),
        ((1, 1, 0, 0), (0, 1, 0, 1), (0, 0, 1, 0), (0, 0, 1, 1)),
        ((1, 0, 0, 1), (0, 1, 1, 0), (0, 0, 1, 0), (0, 1, 0, 1)),
        ((1, 1, 1, 0), (0, 1, 0, 0), (0, 0, 1, 1), (0, 0, 0, 1)),
        ((1, 0, 1, 0), (0, 1, 0, 0), (0, 0, 1, 1), (0, 1, 0, 1)),
    )
    graph_ids = (*TASK_SPLITS["graph"]["train"], *TASK_SPLITS["graph"]["heldout"])
    for example_id, nodes, adjacency, label in zip(
        graph_ids, graph_nodes, graph_adjacency, (0, 0, 1, 1, 0, 1), strict=True
    ):
        rows[example_id] = (
            "graph",
            {
                "node_features": np.asarray(nodes, dtype=np.float32),
                "adjacency": np.asarray(adjacency, dtype=np.uint8),
            },
            {"label": np.asarray(label, dtype=np.int64)},
        )
    return rows


EXAMPLES = MappingProxyType(_examples())
FEATURE_FINGERPRINT_TO_ID = MappingProxyType(
    {
        canonical_array_fingerprint(tuple(features.items())): example_id
        for example_id, (_, features, _) in EXAMPLES.items()
    }
)
EXAMPLE_ID_TO_TARGET_FINGERPRINT = MappingProxyType(
    {
        example_id: canonical_array_fingerprint(tuple(targets.items()))
        for example_id, (_, _, targets) in EXAMPLES.items()
    }
)


def build_batch(task: str, role: str) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
    ids = TASK_SPLITS[task][role]
    feature_names = tuple(EXAMPLES[ids[0]][1])
    target_names = tuple(EXAMPLES[ids[0]][2])
    features = {
        name: torch.from_numpy(np.stack([EXAMPLES[example_id][1][name] for example_id in ids]))
        for name in feature_names
    }
    targets = {
        name: torch.from_numpy(np.stack([EXAMPLES[example_id][2][name] for example_id in ids]))
        for name in target_names
    }
    return features, targets


def _numpy_rows(fields: Mapping[str, torch.Tensor]) -> tuple[tuple[str, np.ndarray], ...]:
    converted = []
    for name, value in fields.items():
        if not isinstance(value, torch.Tensor):
            raise TypeError("integrity fields must be Torch tensors")
        converted.append((name, value.detach().cpu().contiguous().numpy()))
    return tuple(converted)


def resolve_feature_rows(task: str, features: Mapping[str, torch.Tensor]) -> tuple[str, ...]:
    rows = _numpy_rows(features)
    if not rows:
        raise ValueError("feature fields must be nonempty")
    expected_names = tuple(EXAMPLES[TASK_SPLITS[task]["train"][0]][1])
    if tuple(name for name, _ in rows) != expected_names:
        raise ValueError("feature fields or order mismatch")
    batch_sizes = {value.shape[0] for _, value in rows}
    if len(batch_sizes) != 1:
        raise ValueError("feature batch dimensions disagree")
    resolved = []
    for index in range(batch_sizes.pop()):
        fingerprint = canonical_array_fingerprint(
            tuple((name, value[index]) for name, value in rows)
        )
        try:
            example_id = FEATURE_FINGERPRINT_TO_ID[fingerprint]
        except KeyError as exc:
            raise ValueError("unknown structured feature identity") from exc
        if EXAMPLES[example_id][0] != task:
            raise ValueError("feature belongs to another task")
        resolved.append(example_id)
    if len(resolved) != len(set(resolved)):
        raise ValueError("duplicate feature row within one batch")
    ids = tuple(resolved)
    if ids not in (TASK_SPLITS[task]["train"], TASK_SPLITS[task]["heldout"]):
        raise ValueError("features are not one immutable split in stored order")
    return ids


def pair_loss_rows(
    task: str,
    features: Mapping[str, torch.Tensor],
    targets: Mapping[str, torch.Tensor],
) -> tuple[str, tuple[str, ...]]:
    ids = resolve_feature_rows(task, features)
    rows = _numpy_rows(targets)
    expected_names = tuple(EXAMPLES[ids[0]][2])
    if tuple(name for name, _ in rows) != expected_names:
        raise ValueError("target fields or order mismatch")
    if any(value.shape[0] != len(ids) for _, value in rows):
        raise ValueError("target batch dimension disagrees with actual features")
    for index, example_id in enumerate(ids):
        actual = canonical_array_fingerprint(
            tuple((name, np.asarray(value[index])) for name, value in rows)
        )
        if actual != EXAMPLE_ID_TO_TARGET_FINGERPRINT[example_id]:
            raise ValueError(f"aligned target mismatch for actual feature {example_id}")
    for role in ("train", "heldout"):
        if ids == TASK_SPLITS[task][role]:
            return role, ids
    raise AssertionError("resolved split role disappeared")


def canonical_target_tensors(
    task: str,
    ids: tuple[str, ...],
    *,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    """Rebuild canonical targets from feature-derived immutable IDs."""
    if ids not in (TASK_SPLITS[task]["train"], TASK_SPLITS[task]["heldout"]):
        raise ValueError("canonical targets require one immutable split")
    target_names = tuple(EXAMPLES[ids[0]][2])
    return {
        name: torch.from_numpy(
            np.stack([EXAMPLES[example_id][2][name] for example_id in ids])
        ).to(device=device)
        for name in target_names
    }


class IntegrityObserver:
    """Independent forward, target, and actual loss-consumption observer."""

    def __init__(self, task: str):
        self.task = task
        self.forward_calls: list[tuple[str, tuple[str, ...]]] = []
        self.loss_calls: list[tuple[str, tuple[str, ...]]] = []
        self._active_loss: dict[str, object] | None = None
        self._loss_functions: dict[str, object] = {}
        self._optimizer_identity: torch.optim.AdamW | None = None
        self._expected_parameter_values: tuple[torch.Tensor, ...] | None = None
        self._expected_optimizer_state: tuple[dict[str, object], ...] | None = None
        self._completed_steps = 0
        self._expected_steps: int | None = None
        self._training_started = False
        self._training_finished = False

    def begin_loss(
        self,
        features: Mapping[str, torch.Tensor],
        targets: Mapping[str, torch.Tensor],
        *,
        training: bool,
        grad_enabled: bool,
        loss_functions: Mapping[str, object],
    ) -> None:
        if self._active_loss is not None:
            raise AssertionError("nested compute_loss transaction")
        role, ids = self.observe_loss(
            features,
            targets,
            training=training,
            grad_enabled=grad_enabled,
        )
        expected_primitives = (
            (
                "binary_cross_entropy_with_logits",
                "cross_entropy",
                "smooth_l1_loss",
            )
            if self.task == "detection"
            else ("cross_entropy",)
        )
        self._active_loss = {
            "role": role,
            "ids": ids,
            "training": training,
            "grad_enabled": grad_enabled,
            "phase": "computing",
            "forwards": [],
            "primitives": [],
            "primitive_results": [],
            "expected_primitives": expected_primitives,
        }
        self._loss_functions = dict(loss_functions)

    def abort_loss(self) -> None:
        if self._active_loss is not None:
            hook_handle = self._active_loss.get("hook_handle")
            if hook_handle is not None:
                hook_handle.remove()
        self._active_loss = None
        self._loss_functions = {}

    @staticmethod
    def _forward_tensors(output: object) -> tuple[torch.Tensor, ...]:
        if isinstance(output, torch.Tensor):
            return (output,)
        if isinstance(output, (tuple, list)):
            return tuple(value for value in output if isinstance(value, torch.Tensor))
        raise AssertionError("authenticated model forward did not return tensors")

    @staticmethod
    def _assert_gradients_equal(
        actual: tuple[torch.Tensor | None, ...],
        expected: tuple[torch.Tensor | None, ...],
        label: str,
    ) -> None:
        if len(actual) != len(expected):
            raise AssertionError(f"{label} gradient count mismatch")
        for index, (actual_gradient, expected_gradient) in enumerate(
            zip(actual, expected, strict=True)
        ):
            if actual_gradient is None or expected_gradient is None:
                if actual_gradient is not expected_gradient:
                    raise AssertionError(f"{label} gradient {index} reachability mismatch")
                continue
            if (
                actual_gradient.shape != expected_gradient.shape
                or actual_gradient.dtype != expected_gradient.dtype
                or actual_gradient.device != expected_gradient.device
                or not torch.allclose(
                    actual_gradient,
                    expected_gradient,
                    rtol=1e-6,
                    atol=1e-7,
                )
            ):
                raise AssertionError(f"{label} gradient {index} mismatch")

    def _expected_composed_loss(self, active: Mapping[str, object]) -> torch.Tensor:
        results = active["primitive_results"]
        if self.task == "detection":
            bce, cross_entropy, smooth_l1 = results
            return bce + cross_entropy + 2 * smooth_l1
        return results[0]

    def finish_loss(self, result: torch.Tensor, model: nn.Module) -> None:
        active = self._require_active_loss()
        forwards = active["forwards"]
        primitives = tuple(active["primitives"])
        expected = active["expected_primitives"]
        try:
            if active["phase"] != "computing":
                raise AssertionError("compute_loss transaction phase mismatch")
            if len(forwards) != 1:
                raise AssertionError(
                    f"compute_loss must consume exactly one model forward, observed {len(forwards)}"
                )
            if primitives != expected:
                raise AssertionError(
                    f"loss primitive sequence mismatch: expected {expected}, observed {primitives}"
                )
            if len(active["primitive_results"]) != len(expected):
                raise AssertionError("loss primitive result count mismatch")
            if not isinstance(result, torch.Tensor) or result.shape != ():
                raise AssertionError("compute_loss must return one scalar tensor")
            expected_loss = self._expected_composed_loss(active)
            if not torch.equal(result.detach(), expected_loss.detach()):
                raise AssertionError("compute_loss scalar does not match authenticated primitives")
            if not active["grad_enabled"]:
                self.abort_loss()
                return
            if not result.requires_grad or not expected_loss.requires_grad:
                raise AssertionError("compute_loss result detached from authenticated primitives")
            forward_tensors = tuple(
                tensor for tensor in self._forward_tensors(forwards[0]) if tensor.requires_grad
            )
            parameters = tuple(parameter for parameter in model.parameters() if parameter.requires_grad)
            actual_forward_gradients = torch.autograd.grad(
                result,
                forward_tensors,
                retain_graph=True,
                allow_unused=True,
            )
            expected_forward_gradients = torch.autograd.grad(
                expected_loss,
                forward_tensors,
                retain_graph=True,
                allow_unused=True,
            )
            self._assert_gradients_equal(
                actual_forward_gradients,
                expected_forward_gradients,
                "returned-loss forward",
            )
            actual_parameter_gradients = torch.autograd.grad(
                result,
                parameters,
                retain_graph=True,
                allow_unused=True,
            )
            expected_parameter_gradients = torch.autograd.grad(
                expected_loss,
                parameters,
                retain_graph=True,
                allow_unused=True,
            )
            self._assert_gradients_equal(
                actual_parameter_gradients,
                expected_parameter_gradients,
                "returned-loss parameter",
            )
            if not active["training"]:
                self.abort_loss()
                return
            active["parameters"] = parameters
            active["expected_parameter_gradients"] = tuple(
                None if gradient is None else gradient.detach().clone()
                for gradient in expected_parameter_gradients
            )
            active["backward_count"] = 0
            active["backward_root_valid"] = True
            active["phase"] = "awaiting-backward-step"

            def _observe_backward(gradient: torch.Tensor) -> torch.Tensor:
                if self._active_loss is not active:
                    raise AssertionError("stale authenticated loss used for backward")
                active["backward_count"] += 1
                root = torch.ones_like(gradient)
                if gradient.shape != () or not torch.equal(gradient, root):
                    active["backward_root_valid"] = False
                return gradient

            active["hook_handle"] = result.register_hook(_observe_backward)
        except BaseException:
            self.abort_loss()
            raise

    def _adamw_config(self) -> dict[str, object]:
        return {
            "lr": EXPECTED_ADAMW_LR[self.task],
            "betas": (0.9, 0.999),
            "eps": 1e-8,
            "weight_decay": 0,
            "amsgrad": False,
            "maximize": False,
            "foreach": False,
            "capturable": False,
            "differentiable": False,
            "fused": False,
            "decoupled_weight_decay": True,
        }

    def _validate_optimizer(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
    ) -> tuple[nn.Parameter, ...]:
        if type(optimizer) is not torch.optim.AdamW:
            raise AssertionError("training must use exactly torch.optim.AdamW")
        if self._optimizer_identity is None:
            self._optimizer_identity = optimizer
        elif optimizer is not self._optimizer_identity:
            raise AssertionError("optimizer object changed during training")
        if len(optimizer.param_groups) != 1:
            raise AssertionError("AdamW must have exactly one parameter group")
        model_parameters = tuple(model.parameters())
        group = optimizer.param_groups[0]
        group_parameters = tuple(group["params"])
        if len(group_parameters) != len(model_parameters) or any(
            expected is not actual
            for expected, actual in zip(model_parameters, group_parameters, strict=True)
        ):
            raise AssertionError("AdamW parameter membership or order mismatch")
        for name, expected in self._adamw_config().items():
            if group.get(name) != expected or optimizer.defaults.get(name) != expected:
                raise AssertionError(f"AdamW {name} configuration mismatch")
        return model_parameters

    @classmethod
    def _clone_state_value(cls, value: object) -> object:
        if isinstance(value, torch.Tensor):
            return value.detach().clone()
        if isinstance(value, dict):
            return {key: cls._clone_state_value(item) for key, item in value.items()}
        if isinstance(value, tuple):
            return tuple(cls._clone_state_value(item) for item in value)
        if isinstance(value, list):
            return [cls._clone_state_value(item) for item in value]
        return value

    @classmethod
    def _assert_state_equal(cls, actual: object, expected: object, label: str) -> None:
        if isinstance(actual, torch.Tensor) or isinstance(expected, torch.Tensor):
            if not isinstance(actual, torch.Tensor) or not isinstance(expected, torch.Tensor):
                raise TypeError(f"{label} tensor type mismatch")
            if (
                actual.shape != expected.shape
                or actual.dtype != expected.dtype
                or actual.device != expected.device
                or not torch.allclose(actual, expected, rtol=1e-6, atol=1e-7)
            ):
                raise AssertionError(f"{label} tensor mismatch")
            return
        if isinstance(actual, dict) or isinstance(expected, dict):
            if not isinstance(actual, dict) or not isinstance(expected, dict):
                raise TypeError(f"{label} mapping type mismatch")
            if actual.keys() != expected.keys():
                raise AssertionError(f"{label} mapping keys mismatch")
            for key in actual:
                cls._assert_state_equal(actual[key], expected[key], f"{label}.{key}")
            return
        if isinstance(actual, (tuple, list)) or isinstance(expected, (tuple, list)):
            if type(actual) is not type(expected) or len(actual) != len(expected):
                raise AssertionError(f"{label} sequence mismatch")
            for index, (actual_item, expected_item) in enumerate(
                zip(actual, expected, strict=True)
            ):
                cls._assert_state_equal(
                    actual_item,
                    expected_item,
                    f"{label}[{index}]",
                )
            return
        if actual != expected:
            raise AssertionError(f"{label} value mismatch")

    def _snapshot_optimizer_state(
        self,
        optimizer: torch.optim.Optimizer,
        parameters: tuple[nn.Parameter, ...],
    ) -> tuple[dict[str, object], ...]:
        parameter_ids = {id(parameter) for parameter in parameters}
        if any(id(parameter) not in parameter_ids for parameter in optimizer.state):
            raise AssertionError("AdamW state contains a non-model parameter")
        return tuple(
            {
                key: self._clone_state_value(value)
                for key, value in optimizer.state.get(parameter, {}).items()
            }
            for parameter in parameters
        )

    @classmethod
    def _assert_parameter_values(
        cls,
        parameters: tuple[nn.Parameter, ...],
        expected: tuple[torch.Tensor, ...],
        label: str,
    ) -> None:
        if len(parameters) != len(expected):
            raise AssertionError(f"{label} parameter count mismatch")
        for index, (parameter, expected_value) in enumerate(
            zip(parameters, expected, strict=True)
        ):
            cls._assert_state_equal(
                parameter.detach(),
                expected_value,
                f"{label} parameter {index}",
            )

    def _independent_initial_parameter_values(self) -> tuple[torch.Tensor, ...]:
        model_types = {
            "vit": _Vit,
            "detection": _Detector,
            "segmentation": _Unet,
            "graph": _Graph,
        }
        python_state = random.getstate()
        numpy_state = np.random.get_state()
        try:
            with torch.random.fork_rng(devices=[]):
                torch.manual_seed(SEED)
                reference_model = model_types[self.task]()
                return tuple(
                    parameter.detach().clone() for parameter in reference_model.parameters()
                )
        finally:
            random.setstate(python_state)
            np.random.set_state(numpy_state)

    def begin_training(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        expected_steps: int,
    ) -> None:
        if self._training_started or self._active_loss is not None:
            raise AssertionError("training integrity transaction already started")
        if expected_steps != EXPECTED_TRAINING_STEPS[self.task]:
            raise AssertionError("training wrapper expected-step count mismatch")
        parameters = self._validate_optimizer(model, optimizer)
        reference_values = self._independent_initial_parameter_values()
        if len(parameters) != len(reference_values):
            raise AssertionError("initial model parameter count mismatch")
        for index, (parameter, expected_value) in enumerate(
            zip(parameters, reference_values, strict=True)
        ):
            if (
                parameter.shape != expected_value.shape
                or parameter.dtype != expected_value.dtype
                or parameter.device != expected_value.device
                or not torch.equal(parameter.detach(), expected_value)
            ):
                raise AssertionError(f"initial model parameter {index} mismatch")
        initial_state = self._snapshot_optimizer_state(optimizer, parameters)
        if any(state for state in initial_state):
            raise AssertionError("AdamW initial state must be empty")
        self._expected_parameter_values = tuple(
            value.detach().clone() for value in reference_values
        )
        self._expected_optimizer_state = tuple({} for _ in parameters)
        self._expected_steps = expected_steps
        self._training_started = True

    def prepare_step(self, model: nn.Module, optimizer: torch.optim.Optimizer) -> None:
        active = self._require_active_loss()
        try:
            if not self._training_started or self._training_finished:
                raise AssertionError("optimizer step occurred outside the training transaction")
            if self._expected_steps is None or self._completed_steps >= self._expected_steps:
                raise AssertionError("optimizer exceeded the exact expected step count")
            if active["phase"] != "awaiting-backward-step":
                raise AssertionError("optimizer step occurred before authenticated loss completion")
            if active["backward_count"] != 1 or not active["backward_root_valid"]:
                raise AssertionError(
                    "authenticated returned loss must be the scalar backward root exactly once"
                )
            parameters = active["parameters"]
            model_parameters = self._validate_optimizer(model, optimizer)
            if len(parameters) != len(model_parameters) or any(
                expected is not actual
                for expected, actual in zip(parameters, model_parameters, strict=True)
            ):
                raise AssertionError("optimizer model parameters changed during loss transaction")
            actual_gradients = tuple(parameter.grad for parameter in parameters)
            self._assert_gradients_equal(
                actual_gradients,
                active["expected_parameter_gradients"],
                "optimizer parameter",
            )
            if self._expected_parameter_values is None:
                raise AssertionError("independent initial parameter baseline is missing")
            expected_pre_parameters = self._expected_parameter_values
            self._assert_parameter_values(
                model_parameters,
                expected_pre_parameters,
                "pre-step",
            )
            actual_pre_state = self._snapshot_optimizer_state(optimizer, model_parameters)
            expected_pre_state = self._expected_optimizer_state
            if expected_pre_state is None:
                raise AssertionError("independent initial AdamW state baseline is missing")
            self._assert_state_equal(actual_pre_state, expected_pre_state, "pre-step AdamW state")

            shadow_parameters = tuple(
                nn.Parameter(value.detach().clone()) for value in expected_pre_parameters
            )
            for shadow_parameter, expected_gradient in zip(
                shadow_parameters,
                active["expected_parameter_gradients"],
                strict=True,
            ):
                if expected_gradient is not None:
                    shadow_parameter.grad = expected_gradient.detach().clone()
            config = self._adamw_config()
            shadow_optimizer = torch.optim.AdamW(
                shadow_parameters,
                lr=config["lr"],
                betas=config["betas"],
                eps=config["eps"],
                weight_decay=config["weight_decay"],
                amsgrad=config["amsgrad"],
                maximize=config["maximize"],
                foreach=config["foreach"],
                capturable=config["capturable"],
                differentiable=config["differentiable"],
                fused=config["fused"],
            )
            for shadow_parameter, state in zip(
                shadow_parameters,
                expected_pre_state,
                strict=True,
            ):
                if state:
                    shadow_optimizer.state[shadow_parameter] = self._clone_state_value(state)
            shadow_optimizer.step()
            active["expected_post_parameters"] = tuple(
                parameter.detach().clone() for parameter in shadow_parameters
            )
            active["expected_post_state"] = self._snapshot_optimizer_state(
                shadow_optimizer,
                shadow_parameters,
            )
            active["phase"] = "awaiting-real-step"
        except BaseException:
            self.abort_loss()
            raise

    def finish_step(self, model: nn.Module, optimizer: torch.optim.Optimizer) -> None:
        active = self._require_active_loss()
        try:
            if active["phase"] != "awaiting-real-step":
                raise AssertionError("real optimizer step was not independently prepared")
            parameters = self._validate_optimizer(model, optimizer)
            self._assert_parameter_values(
                parameters,
                active["expected_post_parameters"],
                "post-step",
            )
            actual_post_state = self._snapshot_optimizer_state(optimizer, parameters)
            self._assert_state_equal(
                actual_post_state,
                active["expected_post_state"],
                "post-step AdamW state",
            )
            self._expected_parameter_values = tuple(
                value.detach().clone() for value in active["expected_post_parameters"]
            )
            self._expected_optimizer_state = self._clone_state_value(
                active["expected_post_state"]
            )
            self._completed_steps += 1
        except BaseException:
            self.abort_loss()
            raise
        self.abort_loss()

    def finish_training(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        expected_steps: int,
    ) -> None:
        if self._active_loss is not None:
            self.abort_loss()
            raise AssertionError("training ended with an unconsumed loss transaction")
        if (
            not self._training_started
            or self._training_finished
            or self._expected_steps is None
            or expected_steps != self._expected_steps
        ):
            raise AssertionError("training completion does not match its outer transaction")
        if self._completed_steps != expected_steps:
            raise AssertionError(
                f"expected {expected_steps} authenticated AdamW transitions, "
                f"observed {self._completed_steps}"
            )
        parameters = self._validate_optimizer(model, optimizer)
        if self._expected_parameter_values is None or self._expected_optimizer_state is None:
            raise AssertionError("training ended without an AdamW transition baseline")
        self._assert_parameter_values(
            parameters,
            self._expected_parameter_values,
            "completed-training",
        )
        actual_state = self._snapshot_optimizer_state(optimizer, parameters)
        self._assert_state_equal(
            actual_state,
            self._expected_optimizer_state,
            "completed-training AdamW state",
        )
        self._training_finished = True

    def _require_active_loss(self) -> dict[str, object]:
        if self._active_loss is None:
            raise AssertionError("loss primitive called outside compute_loss transaction")
        return self._active_loss

    def observe_forward(
        self,
        features: Mapping[str, torch.Tensor],
        *,
        training: bool,
        grad_enabled: bool,
        output: object,
    ) -> tuple[str, ...]:
        ids = resolve_feature_rows(self.task, features)
        role = "train" if ids == TASK_SPLITS[self.task]["train"] else "heldout"
        if training and role != "train":
            raise ValueError("held-out feature reached a training forward")
        if not grad_enabled and role != "heldout":
            raise ValueError("training feature reached held-out evaluation")
        self.forward_calls.append((role, ids))
        active = self._active_loss
        if training and grad_enabled and active is None:
            raise AssertionError("grad-enabled training forward occurred outside compute_loss")
        if active is not None:
            if active["phase"] != "computing":
                raise AssertionError("extra forward occurred outside active compute_loss body")
            if ids != active["ids"] or role != active["role"]:
                raise ValueError("forward feature IDs do not match the active loss")
            if training != active["training"] or grad_enabled != active["grad_enabled"]:
                raise ValueError("forward mode does not match the active loss")
            if active["forwards"]:
                raise AssertionError("compute_loss performed more than one model forward")
            active["forwards"].append(output)
        return ids

    def observe_loss(
        self,
        features: Mapping[str, torch.Tensor],
        targets: Mapping[str, torch.Tensor],
        *,
        training: bool,
        grad_enabled: bool,
    ) -> tuple[str, tuple[str, ...]]:
        role, ids = pair_loss_rows(self.task, features, targets)
        if training and role != "train":
            raise ValueError("held-out feature/target pair reached an optimizer loss")
        if not grad_enabled and role != "heldout":
            raise ValueError("training feature/target pair reached held-out evaluation")
        self.loss_calls.append((role, ids))
        return role, ids

    def _next_primitive(self, name: str) -> dict[str, object]:
        active = self._require_active_loss()
        observed = active["primitives"]
        expected = active["expected_primitives"]
        index = len(observed)
        if index >= len(expected) or expected[index] != name:
            raise AssertionError(
                f"unexpected loss primitive {name} at position {index}; expected {expected}"
            )
        if len(active["forwards"]) != 1:
            raise AssertionError("loss primitive must follow exactly one model forward")
        observed.append(name)
        return active

    @staticmethod
    def _assert_mean_reduction(kwargs: Mapping[str, object]) -> None:
        if kwargs.get("reduction", "mean") != "mean":
            raise AssertionError("loss primitive must use mean reduction")

    @staticmethod
    def _assert_target(actual: torch.Tensor, expected: torch.Tensor, label: str) -> None:
        if (
            actual.shape != expected.shape
            or actual.dtype != expected.dtype
            or actual.device != expected.device
            or not torch.equal(actual.detach(), expected.detach())
        ):
            raise AssertionError(f"{label} is not the canonical aligned target")

    @staticmethod
    def _gradient_probe(value: torch.Tensor) -> torch.Tensor:
        count = value.numel()
        return torch.linspace(
            0.25,
            1.25,
            count,
            dtype=value.dtype,
            device=value.device,
        ).reshape(value.shape)

    @classmethod
    def _assert_input_binding(
        cls,
        actual: torch.Tensor,
        expected: torch.Tensor,
        source: torch.Tensor,
        label: str,
        *,
        require_identity: bool,
    ) -> None:
        if (
            actual.shape != expected.shape
            or actual.dtype != expected.dtype
            or actual.device != expected.device
            or not torch.equal(actual.detach(), expected.detach())
        ):
            raise AssertionError(f"{label} does not match the authenticated forward output")
        if require_identity and actual is not expected:
            raise AssertionError(f"{label} is not the exact authenticated forward tensor")
        if not source.requires_grad:
            return
        if not actual.requires_grad or not expected.requires_grad:
            raise AssertionError(f"{label} detached from the authenticated forward output")
        probe = cls._gradient_probe(actual)
        actual_gradient = torch.autograd.grad(
            actual,
            source,
            grad_outputs=probe,
            retain_graph=True,
            allow_unused=True,
        )[0]
        expected_gradient = torch.autograd.grad(
            expected,
            source,
            grad_outputs=probe,
            retain_graph=True,
            allow_unused=True,
        )[0]
        if actual_gradient is None or expected_gradient is None or not torch.equal(
            actual_gradient, expected_gradient
        ):
            raise AssertionError(f"{label} has a substituted autograd path")

    def _canonical_targets(
        self, active: Mapping[str, object], device: torch.device
    ) -> dict[str, torch.Tensor]:
        return canonical_target_tensors(
            self.task,
            active["ids"],
            device=device,
        )

    def cross_entropy(
        self,
        input_value: torch.Tensor,
        target: torch.Tensor,
        *args,
        **kwargs,
    ) -> torch.Tensor:
        active = self._next_primitive("cross_entropy")
        self._assert_mean_reduction(kwargs)
        output = active["forwards"][0]
        if self.task == "detection":
            _, class_logits, _ = output
            canonical = self._canonical_targets(active, class_logits.device)
            objectness, classes, _ = _encoded_detection_targets(
                canonical["boxes"], canonical["labels"]
            )
            positive = objectness.bool()
            expected_input = class_logits.permute(0, 2, 3, 1)[positive]
            expected_target = classes[positive]
            source = class_logits
            require_identity = False
        else:
            logits = output[0] if isinstance(output, tuple) else output
            canonical = self._canonical_targets(active, logits.device)
            target_name = "mask" if self.task == "segmentation" else "label"
            expected_input = logits
            expected_target = canonical[target_name]
            source = logits
            require_identity = True
        self._assert_input_binding(
            input_value,
            expected_input,
            source,
            "cross-entropy input",
            require_identity=require_identity,
        )
        self._assert_target(target, expected_target, "cross-entropy target")
        result = self._loss_functions["cross_entropy"](
            input_value, target, *args, **kwargs
        )
        active["primitive_results"].append(result)
        return result

    def binary_cross_entropy_with_logits(
        self,
        input_value: torch.Tensor,
        target: torch.Tensor,
        *args,
        **kwargs,
    ) -> torch.Tensor:
        active = self._next_primitive("binary_cross_entropy_with_logits")
        self._assert_mean_reduction(kwargs)
        objectness_logits, _, _ = active["forwards"][0]
        canonical = self._canonical_targets(active, objectness_logits.device)
        expected_target, _, _ = _encoded_detection_targets(
            canonical["boxes"], canonical["labels"]
        )
        self._assert_input_binding(
            input_value,
            objectness_logits,
            objectness_logits,
            "binary-cross-entropy input",
            require_identity=True,
        )
        self._assert_target(target, expected_target, "binary-cross-entropy target")
        result = self._loss_functions["binary_cross_entropy_with_logits"](
            input_value, target, *args, **kwargs
        )
        active["primitive_results"].append(result)
        return result

    def smooth_l1_loss(
        self,
        input_value: torch.Tensor,
        target: torch.Tensor,
        *args,
        **kwargs,
    ) -> torch.Tensor:
        active = self._next_primitive("smooth_l1_loss")
        self._assert_mean_reduction(kwargs)
        _, _, box_logits = active["forwards"][0]
        canonical = self._canonical_targets(active, box_logits.device)
        objectness, _, encoded_boxes = _encoded_detection_targets(
            canonical["boxes"], canonical["labels"]
        )
        positive = objectness.bool()
        expected_input = torch.sigmoid(box_logits.permute(0, 2, 3, 1))[positive]
        expected_target = encoded_boxes.permute(0, 2, 3, 1)[positive]
        self._assert_input_binding(
            input_value,
            expected_input,
            box_logits,
            "smooth-L1 input",
            require_identity=False,
        )
        self._assert_target(target, expected_target, "smooth-L1 target")
        result = self._loss_functions["smooth_l1_loss"](
            input_value, target, *args, **kwargs
        )
        active["primitive_results"].append(result)
        return result


def _seed() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


class _Vit(nn.Module):
    def __init__(self):
        super().__init__()
        self.patch = nn.Linear(4, 8)
        self.class_token = nn.Parameter(torch.zeros(1, 1, 8))
        self.positions = nn.Parameter(torch.zeros(1, 5, 8))
        self.attention = nn.MultiheadAttention(8, 1, dropout=0, batch_first=True)
        self.norm = nn.LayerNorm(8, eps=1e-5)
        self.head = nn.Linear(8, 2)

    def forward(self, images: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        batch = images.shape[0]
        patches = images.reshape(batch, 1, 2, 2, 2, 2).permute(0, 2, 4, 1, 3, 5)
        patches = patches.contiguous().reshape(batch, 4, 4)
        tokens = torch.cat((self.class_token.expand(batch, -1, -1), self.patch(patches)), 1)
        positioned = tokens + self.positions
        attended, _ = self.attention(positioned, positioned, positioned, need_weights=False)
        encoded = self.norm(positioned + attended)
        return self.head(encoded[:, 0]), encoded[:, :1]


class _Detector(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = nn.Conv2d(1, 4, 3, stride=2, padding=1)
        self.objectness = nn.Conv2d(4, 1, 1)
        self.class_head = nn.Conv2d(4, 2, 1)
        self.box = nn.Conv2d(4, 4, 1)

    def forward(self, images: torch.Tensor) -> tuple[torch.Tensor, ...]:
        hidden = F.relu(self.backbone(images))
        return self.objectness(hidden)[:, 0], self.class_head(hidden), self.box(hidden)


class _Unet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Conv2d(1, 4, 3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = nn.Conv2d(4, 8, 3, padding=1)
        self.decoder = nn.ConvTranspose2d(8, 4, 2, stride=2)
        self.fuse = nn.Conv2d(8, 4, 3, padding=1)
        self.head = nn.Conv2d(4, 2, 1)

    def forward(self, images: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        skip = F.relu(self.encoder(images))
        bottleneck = F.relu(self.bottleneck(self.pool(skip)))
        decoder = F.relu(self.decoder(bottleneck))
        concatenated = torch.cat((decoder, skip), dim=1)
        return self.head(self.fuse(concatenated)), concatenated


class _Graph(nn.Module):
    def __init__(self):
        super().__init__()
        self.projection = nn.Linear(3, 8)
        self.class_token = nn.Parameter(torch.zeros(1, 1, 8))
        self.attention = nn.MultiheadAttention(8, 1, dropout=0, batch_first=True)
        self.norm = nn.LayerNorm(8, eps=1e-5)
        self.head = nn.Linear(8, 2)

    def forward(
        self, nodes: torch.Tensor, adjacency: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        degree = adjacency.sum(2, keepdim=True)
        aggregate = torch.bmm(adjacency.float(), nodes) / degree
        projected = self.projection(aggregate)
        tokens = torch.cat((self.class_token.expand(nodes.shape[0], -1, -1), projected), 1)
        attended, _ = self.attention(tokens, tokens, tokens, need_weights=False)
        encoded = self.norm(tokens + attended)
        return self.head(encoded[:, 0]), aggregate, tokens


def _encoded_detection_targets(
    boxes: torch.Tensor, labels: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    batch = boxes.shape[0]
    objectness = torch.zeros((batch, 4, 4), dtype=torch.float32)
    classes = torch.full((batch, 4, 4), -1, dtype=torch.int64)
    encoded = torch.zeros((batch, 4, 4, 4), dtype=torch.float32)
    for row in range(batch):
        x0, y0, x1, y1 = (float(value) for value in boxes[row, 0])
        sx, sy = (x0 + x1) / 4, (y0 + y1) / 4
        column, line = math.floor(sx), math.floor(sy)
        objectness[row, line, column] = 1
        classes[row, line, column] = labels[row, 0]
        encoded[row, :, line, column] = torch.tensor(
            [sx - column, sy - line, (x1 - x0) / 8, (y1 - y0) / 8]
        )
    return objectness, classes, encoded


def _detector_loss(
    model: _Detector, features: Mapping[str, torch.Tensor], targets: Mapping[str, torch.Tensor]
) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
    objectness_logits, class_logits, box_logits = model(features["image"])
    objectness, classes, boxes = _encoded_detection_targets(targets["boxes"], targets["labels"])
    positive = objectness.bool()
    bce = F.binary_cross_entropy_with_logits(objectness_logits, objectness)
    ce = F.cross_entropy(class_logits.permute(0, 2, 3, 1)[positive], classes[positive])
    predicted = torch.sigmoid(box_logits.permute(0, 2, 3, 1))[positive]
    smooth = F.smooth_l1_loss(predicted, boxes.permute(0, 2, 3, 1)[positive])
    return bce + ce + 2 * smooth, (bce, ce, smooth)


def _mean_iou(
    model: _Detector, features: Mapping[str, torch.Tensor], targets: Mapping[str, torch.Tensor]
) -> float:
    objectness, _, box_logits = model(features["image"])
    encoded = torch.sigmoid(box_logits)
    values = []
    for row in range(features["image"].shape[0]):
        best = int(objectness[row].reshape(-1).argmax())
        line, column = divmod(best, 4)
        tx, ty, width_norm, height_norm = (float(value) for value in encoded[row, :, line, column])
        center_x, center_y = (column + tx) * 2, (line + ty) * 2
        width, height = width_norm * 8, height_norm * 8
        predicted = torch.tensor(
            [
                center_x - width / 2,
                center_y - height / 2,
                center_x + width / 2,
                center_y + height / 2,
            ]
        )
        truth = targets["boxes"][row, 0]
        intersection = (
            (torch.minimum(predicted[2:], truth[2:]) - torch.maximum(predicted[:2], truth[:2]))
            .clamp_min(0)
            .prod()
        )
        union = (
            (predicted[2:] - predicted[:2]).prod() + (truth[2:] - truth[:2]).prod() - intersection
        )
        values.append(intersection / union)
    return float(torch.stack(values).mean())


def _round(value: float) -> float:
    if isinstance(value, torch.Tensor):
        value = value.detach()
    return round(float(value), 8)


def reconstruct_reference_results() -> dict[str, object]:
    """Rebuild all four baselines and scalar final traces from first principles."""
    results: dict[str, object] = {}

    _seed()
    vit = _Vit()
    train, train_targets = build_batch("vit", "train")
    heldout, heldout_targets = build_batch("vit", "heldout")
    optimizer = torch.optim.AdamW(
        vit.parameters(),
        lr=0.05,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0,
        foreach=False,
        fused=False,
    )
    vit.eval()
    with torch.no_grad():
        baseline = F.cross_entropy(vit(heldout["image"])[0], heldout_targets["label"])
    trace = []
    vit.train()
    for _ in range(12):
        optimizer.zero_grad(set_to_none=True)
        loss = F.cross_entropy(vit(train["image"])[0], train_targets["label"])
        loss.backward()
        optimizer.step()
        trace.append(_round(loss))
    vit.eval()
    with torch.no_grad():
        logits, class_output = vit(heldout["image"])
        final = F.cross_entropy(logits, heldout_targets["label"])
    results["p17"] = {
        "updates": 12,
        "trace": tuple(trace),
        "heldout_before": _round(baseline),
        "heldout_after": _round(final),
        "heldout_correct": int((logits.argmax(1) == heldout_targets["label"]).sum()),
        "class_output_shape": tuple(class_output.shape),
    }

    _seed()
    detector = _Detector()
    train, train_targets = build_batch("detection", "train")
    heldout, heldout_targets = build_batch("detection", "heldout")
    optimizer = torch.optim.AdamW(
        detector.parameters(),
        lr=0.05,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0,
        foreach=False,
        fused=False,
    )
    detector.eval()
    with torch.no_grad():
        baseline, _ = _detector_loss(detector, heldout, heldout_targets)
    trace = []
    detector.train()
    for _ in range(16):
        optimizer.zero_grad(set_to_none=True)
        loss, components = _detector_loss(detector, train, train_targets)
        loss.backward()
        optimizer.step()
        trace.append(tuple(_round(value) for value in (loss, *components)))
    detector.eval()
    with torch.no_grad():
        final, _ = _detector_loss(detector, heldout, heldout_targets)
        shapes = tuple(tuple(value.shape) for value in detector(heldout["image"]))
        mean_iou = _mean_iou(detector, heldout, heldout_targets)
    results["p18"] = {
        "updates": 16,
        "trace": tuple(trace),
        "heldout_before": _round(baseline),
        "heldout_after": _round(final),
        "heldout_mean_iou": _round(mean_iou),
        "output_shapes": shapes,
    }

    _seed()
    unet = _Unet()
    train, train_targets = build_batch("segmentation", "train")
    heldout, heldout_targets = build_batch("segmentation", "heldout")
    optimizer = torch.optim.AdamW(
        unet.parameters(),
        lr=0.03,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0,
        foreach=False,
        fused=False,
    )
    unet.eval()
    with torch.no_grad():
        baseline = F.cross_entropy(unet(heldout["image"])[0], heldout_targets["mask"])
    trace = []
    unet.train()
    for _ in range(16):
        optimizer.zero_grad(set_to_none=True)
        loss = F.cross_entropy(unet(train["image"])[0], train_targets["mask"])
        loss.backward()
        optimizer.step()
        trace.append(_round(loss))
    unet.eval()
    with torch.no_grad():
        logits, concatenated = unet(heldout["image"])
        final = F.cross_entropy(logits, heldout_targets["mask"])
        predicted = logits.argmax(1) == 1
        truth = heldout_targets["mask"] == 1
        intersection = (predicted & truth).sum(dtype=torch.float32)
        dice = (2 * intersection + 1e-7) / (
            predicted.sum(dtype=torch.float32) + truth.sum(dtype=torch.float32) + 1e-7
        )
    results["p19"] = {
        "updates": 16,
        "trace": tuple(trace),
        "heldout_before": _round(baseline),
        "heldout_after": _round(final),
        "heldout_dice": _round(dice),
        "logits_shape": tuple(logits.shape),
        "concat_shape": tuple(concatenated.shape),
    }

    _seed()
    graph = _Graph()
    train, train_targets = build_batch("graph", "train")
    heldout, heldout_targets = build_batch("graph", "heldout")
    optimizer = torch.optim.AdamW(
        graph.parameters(),
        lr=0.05,
        betas=(0.9, 0.999),
        eps=1e-8,
        weight_decay=0,
        foreach=False,
        fused=False,
    )
    graph.eval()
    with torch.no_grad():
        baseline = F.cross_entropy(
            graph(train["node_features"], train["adjacency"])[0], train_targets["label"]
        )
        baseline_heldout = F.cross_entropy(
            graph(heldout["node_features"], heldout["adjacency"])[0], heldout_targets["label"]
        )
    trace = []
    graph.train()
    for _ in range(12):
        optimizer.zero_grad(set_to_none=True)
        loss = F.cross_entropy(
            graph(train["node_features"], train["adjacency"])[0], train_targets["label"]
        )
        loss.backward()
        optimizer.step()
        trace.append(_round(loss))
    graph.eval()
    with torch.no_grad():
        logits, aggregate, tokens = graph(heldout["node_features"], heldout["adjacency"])
        final = F.cross_entropy(logits, heldout_targets["label"])
    results["p20"] = {
        "updates": 12,
        "trace": tuple(trace),
        "heldout_before": _round(baseline_heldout),
        "heldout_after": _round(final),
        "heldout_correct": int((logits.argmax(1) == heldout_targets["label"]).sum()),
        "aggregation_shape": tuple(aggregate.shape),
        "attention_input_shape": tuple(tokens.shape),
        "train_baseline_probe": _round(baseline),
    }
    return results


# Scalar metrics, ordered scalar update traces, and shape probes only.
EXPECTED_RESULTS: dict[str, object] = {
    "p17": {
        "updates": 12,
        "trace": (
            0.65317273,
            1.56895936,
            0.5708496,
            0.80901212,
            0.63717449,
            0.46891463,
            0.51511133,
            0.53170395,
            0.43144143,
            0.28950655,
            0.19807342,
            0.14975859,
        ),
        "heldout_before": 0.61486667,
        "heldout_after": 0.10122918,
        "heldout_correct": 2,
        "class_output_shape": (2, 1, 8),
    },
    "p18": {
        "updates": 16,
        "trace": (
            (1.45981574, 0.71666795, 0.68438739, 0.02938023),
            (1.38367248, 0.68004942, 0.65351498, 0.02505401),
            (1.30832112, 0.64776665, 0.62267435, 0.01894006),
            (1.22888267, 0.61383814, 0.58872342, 0.0131605),
            (1.15087199, 0.57845926, 0.55492091, 0.00874593),
            (1.08295357, 0.54152179, 0.52905214, 0.00618984),
            (1.02783668, 0.50400168, 0.51395822, 0.00493841),
            (0.97629309, 0.46692896, 0.50077969, 0.00429222),
            (0.9276647, 0.43068397, 0.48889437, 0.00404318),
            (0.88846892, 0.39567173, 0.48496008, 0.00391854),
            (0.85274059, 0.36192104, 0.48347747, 0.00367101),
            (0.81610036, 0.32936314, 0.48001525, 0.00336099),
            (0.7852059, 0.29845414, 0.48050517, 0.00312331),
            (0.75777131, 0.27012292, 0.48188147, 0.00288345),
            (0.72923577, 0.24512254, 0.47920746, 0.00245289),
            (0.7045933, 0.22281145, 0.47804388, 0.001869),
        ),
        "heldout_before": 1.46587586,
        "heldout_after": 0.89997917,
        "heldout_mean_iou": 0.61596799,
        "output_shapes": ((2, 4, 4), (2, 2, 4, 4), (2, 4, 4, 4)),
    },
    "p19": {
        "updates": 16,
        "trace": (
            0.73024845,
            0.64880747,
            0.56479377,
            0.47215867,
            0.38094276,
            0.30356935,
            0.24890621,
            0.21596774,
            0.19737077,
            0.18550161,
            0.17231721,
            0.15526906,
            0.13659871,
            0.11524019,
            0.0940321,
            0.0742332,
        ),
        "heldout_before": 0.73014623,
        "heldout_after": 0.05498765,
        "heldout_dice": 0.85714287,
        "logits_shape": (2, 2, 8, 8),
        "concat_shape": (2, 8, 8, 8),
    },
    "p20": {
        "updates": 12,
        "trace": (
            0.7317192,
            1.14119565,
            0.75053382,
            0.53401697,
            0.47819963,
            0.42228776,
            0.2512067,
            0.11093066,
            0.06394521,
            0.04221673,
            0.02861195,
            0.01949779,
        ),
        "heldout_before": 0.73819923,
        "heldout_after": 0.013461,
        "heldout_correct": 2,
        "aggregation_shape": (2, 4, 3),
        "attention_input_shape": (2, 5, 8),
        "train_baseline_probe": 0.7317192,
    },
}
