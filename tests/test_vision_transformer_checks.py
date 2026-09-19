from __future__ import annotations

import ast
import importlib.util
import re
import shutil
import textwrap
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests" / "fixtures" / "b2_021_reference.py"
CI_LOCAL = ROOT / "scripts" / "ci-local.sh"
UNIT = ROOT / "book2" / "units" / "B2-021-cross-modal-transformers-vision"

TRAINING = {
    "p17": ("vit", "TinyViTClassifier", "train_vit_classifier", 12, "mean_ce"),
    "p18": ("detection", "TinyGridDetector", "train_grid_detector", 16, "loss"),
    "p19": ("segmentation", "TinyUNetSegmenter", "train_unet_segmenter", 16, "mean_pixel_ce"),
    "p20": ("graph", "GraphTokenClassifier", "train_graph_token_classifier", 12, "mean_ce"),
}


def _reference_module():
    spec = importlib.util.spec_from_file_location("b2_021_reference", REFERENCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _working_notebook(tmp_path: Path, practice: str) -> Path:
    working_unit = tmp_path / UNIT.name
    shutil.copytree(UNIT, working_unit)
    return working_unit / "practice" / f"{practice}_solution.ipynb"


def _function_location(source: str, name: str) -> tuple[int, int, int]:
    tree = ast.parse(source)
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    assert len(matches) == 1, f"expected exactly one named function {name}, found {len(matches)}"
    node = matches[0]
    assert node.end_lineno is not None
    return node.lineno - 1, node.end_lineno, node.col_offset


def _named_function_source(notebook_path: Path, name: str) -> tuple[int, str]:
    notebook = nbformat.read(notebook_path, as_version=4)
    matches = []
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        try:
            start, end, column = _function_location(str(cell.source), name)
        except AssertionError as exc:
            if "found 0" not in str(exc):
                raise
            continue
        lines = str(cell.source).splitlines()
        matches.append((index, textwrap.dedent("\n".join(lines[start:end])), column))
    assert len(matches) == 1, f"expected one {name} definition in {notebook_path.name}"
    index, source, _ = matches[0]
    return index, source


def _replace_named_function(notebook_path: Path, name: str, replacement: str) -> None:
    notebook = nbformat.read(notebook_path, as_version=4)
    matches = []
    for cell_index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        try:
            start, end, column = _function_location(str(cell.source), name)
        except AssertionError as exc:
            if "found 0" not in str(exc):
                raise
            continue
        matches.append((cell_index, start, end, column))
    assert len(matches) == 1, f"expected one substitution seam for {name}"
    cell_index, start, end, column = matches[0]
    cell = notebook.cells[cell_index]
    lines = str(cell.source).splitlines()
    indented = textwrap.indent(textwrap.dedent(replacement).strip(), " " * column)
    lines[start:end] = indented.splitlines()
    cell.source = "\n".join(lines)
    nbformat.write(notebook, notebook_path)


def _replace_fragment_in_function(notebook_path: Path, name: str, old: str, new: str) -> None:
    _, source = _named_function_source(notebook_path, name)
    assert source.count(old) == 1, f"expected one {old!r} in {name}"
    _replace_named_function(notebook_path, name, source.replace(old, new))


def _rename_definition(source: str, old: str, new: str) -> str:
    renamed, count = re.subn(rf"(?m)^def {re.escape(old)}(?=\s*\()", f"def {new}", source, count=1)
    assert count == 1
    return renamed


def _instrument_training_notebook(notebook_path: Path, practice: str) -> None:
    task, _, train_name, updates, trace_key = TRAINING[practice]
    _, validation_source = _named_function_source(notebook_path, "validate_actual")
    validation_candidate = _rename_definition(
        validation_source, "validate_actual", "_candidate_validate_actual"
    )
    validation_wrapper = f"""
{validation_candidate}

_reference_spec = importlib.util.spec_from_file_location(
    "b2_021_integrity_reference_{practice}", Path({str(REFERENCE)!r})
)
_integrity_reference = importlib.util.module_from_spec(_reference_spec)
sys.modules[_reference_spec.name] = _integrity_reference
_reference_spec.loader.exec_module(_integrity_reference)
_integrity_observer = _integrity_reference.IntegrityObserver({task!r})

def validate_actual(features, targets):
    _integrity_reference.pair_loss_rows({task!r}, features, targets)
    return _candidate_validate_actual(features, targets)
"""
    _replace_named_function(notebook_path, "validate_actual", validation_wrapper)

    _, loss_source = _named_function_source(notebook_path, "compute_loss")
    loss_candidate = _rename_definition(loss_source, "compute_loss", "_candidate_compute_loss")
    loss_wrapper = f"""
{loss_candidate}

def compute_loss(model, features, targets):
    _original_cross_entropy = F.cross_entropy
    _original_binary_cross_entropy_with_logits = F.binary_cross_entropy_with_logits
    _original_smooth_l1_loss = F.smooth_l1_loss
    _integrity_observer.begin_loss(
        features,
        targets,
        training=model.training,
        grad_enabled=torch.is_grad_enabled(),
        loss_functions={{
            "cross_entropy": _original_cross_entropy,
            "binary_cross_entropy_with_logits": _original_binary_cross_entropy_with_logits,
            "smooth_l1_loss": _original_smooth_l1_loss,
        }},
    )
    F.cross_entropy = _integrity_observer.cross_entropy
    F.binary_cross_entropy_with_logits = _integrity_observer.binary_cross_entropy_with_logits
    F.smooth_l1_loss = _integrity_observer.smooth_l1_loss
    try:
        try:
            result = _candidate_compute_loss(model, features, targets)
        except BaseException:
            _integrity_observer.abort_loss()
            raise
    finally:
        F.cross_entropy = _original_cross_entropy
        F.binary_cross_entropy_with_logits = _original_binary_cross_entropy_with_logits
        F.smooth_l1_loss = _original_smooth_l1_loss
    _integrity_observer.finish_loss(result, model)
    return result
"""
    _replace_named_function(notebook_path, "compute_loss", loss_wrapper)

    _, forward_source = _named_function_source(notebook_path, "forward")
    forward_candidate = _rename_definition(forward_source, "forward", "_candidate_forward")
    if practice == "p20":
        forward_wrapper = f"""
{forward_candidate}

def forward(self, nodes, adjacency, return_aux=False):
    result = self._candidate_forward(nodes, adjacency, return_aux=return_aux)
    _integrity_observer.observe_forward(
        {{"node_features": nodes, "adjacency": adjacency}},
        training=self.training,
        grad_enabled=torch.is_grad_enabled(),
        output=result,
    )
    return result
"""
    elif practice in ("p17", "p19"):
        forward_wrapper = f"""
{forward_candidate}

def forward(self, images, return_aux=False):
    result = self._candidate_forward(images, return_aux=return_aux)
    _integrity_observer.observe_forward(
        {{"image": images}},
        training=self.training,
        grad_enabled=torch.is_grad_enabled(),
        output=result,
    )
    return result
"""
    else:
        forward_wrapper = f"""
{forward_candidate}

def forward(self, images):
    result = self._candidate_forward(images)
    _integrity_observer.observe_forward(
        {{"image": images}},
        training=self.training,
        grad_enabled=torch.is_grad_enabled(),
        output=result,
    )
    return result
"""
    _replace_named_function(notebook_path, "forward", forward_wrapper)

    _, train_source = _named_function_source(notebook_path, train_name)
    candidate_name = f"_candidate_{train_name}"
    train_candidate = _rename_definition(train_source, train_name, candidate_name)
    if practice == "p18":
        actual_trace = "tuple(tuple(round(float(row[key]), 8) for key in ('loss','bce_obj','ce_cls','smooth_l1_box')) for row in trace)"
    else:
        actual_trace = f"tuple(round(float(row[{trace_key!r}]), 8) for row in trace)"
    train_wrapper = f"""
{train_candidate}

def {train_name}(model, batch, optimizer):
    _original_step = optimizer.step
    _step_order = []
    def _counted_step(*args, **kwargs):
        _integrity_observer.observe_step(model)
        result = _original_step(*args, **kwargs)
        _step_order.append(len(_step_order) + 1)
        return result
    optimizer.step = _counted_step
    try:
        trace = {candidate_name}(model, batch, optimizer)
    finally:
        optimizer.step = _original_step
        _integrity_observer.abort_loss()
    assert tuple(_step_order) == tuple(range(1, {updates + 1}))
    assert tuple(row["update"] for row in trace) == tuple(range(1, {updates + 1}))
    _actual_trace = {actual_trace}
    _expected_trace = _integrity_reference.EXPECTED_RESULTS[{practice!r}]["trace"]
    assert len(_actual_trace) == len(_expected_trace)
    if {practice!r} == "p18":
        assert all(
            all(abs(actual - expected) <= 1e-6 for actual, expected in zip(actual_row, expected_row))
            for actual_row, expected_row in zip(_actual_trace, _expected_trace)
        )
    else:
        assert all(abs(actual - expected) <= 1e-6 for actual, expected in zip(_actual_trace, _expected_trace))
    return trace
"""
    _replace_named_function(notebook_path, train_name, train_wrapper)


def _instrument_p24_audit(notebook_path: Path) -> None:
    _, audit_source = _named_function_source(notebook_path, "audit_cross_modal_sources")
    audit_candidate = _rename_definition(
        audit_source,
        "audit_cross_modal_sources",
        "_candidate_audit_cross_modal_sources",
    )
    audit_wrapper = f"""
{audit_candidate}

def audit_cross_modal_sources(trace):
    result = _candidate_audit_cross_modal_sources(trace)
    base = deepcopy(trace)
    base["adjacency"] = ((1,1,0,0),(1,1,1,0),(0,1,1,0),(0,0,0,0))
    base["optimizer_ids"] = base["train_ids"]
    base["q_source"] = "image_tokens"
    base["k_source"] = "graph_tokens"
    base["v_source"] = "graph_tokens"
    base["score_shape"] = ("B","N_image","N_graph")
    clean_before = deepcopy(base)
    clean_audit = _candidate_audit_cross_modal_sources(base)
    assert base == clean_before, "audit mutated the independent clean trace"
    assert clean_audit["ok"] is True and clean_audit["violations"] == (), (
        "independent clean trace must pass"
    )

    single_faults = (
        ("q-source", "q_source", "graph_tokens", "reversed-qkv"),
        ("k-source", "k_source", "image_tokens", "reversed-qkv"),
        ("v-source", "v_source", "image_tokens", "reversed-qkv"),
        ("score-shape", "score_shape", ("B","N_graph","N_image"), "reversed-qkv"),
        ("optimizer-leakage", "optimizer_ids", (base["train_ids"][0], base["heldout_ids"][0]), "heldout-optimizer-id"),
    )
    for label, field, bad_value, expected_code in single_faults:
        case = deepcopy(base)
        case[field] = bad_value
        case_before = deepcopy(case)
        observed = _candidate_audit_cross_modal_sources(case)
        assert case == case_before, f"audit mutated the independent {{label}} trace"
        codes = tuple(violation["code"] for violation in observed["violations"])
        assert observed["ok"] is False and codes == (expected_code,), (
            f"independent {{label}} fault expected only {{expected_code}}, observed {{codes}}"
        )
    return result
"""
    _replace_named_function(notebook_path, "audit_cross_modal_sources", audit_wrapper)


def _execute(notebook_path: Path) -> nbformat.NotebookNode:
    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=20,
        kernel_name="python3",
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )
    client.execute()
    return notebook


def _assert_execution_fails(notebook_path: Path) -> None:
    with pytest.raises(CellExecutionError):
        _execute(notebook_path)


def _mutate_no_update(notebook_path: Path, practice: str) -> None:
    train_name = TRAINING[practice][2]
    _replace_fragment_in_function(notebook_path, train_name, "optimizer.step()", "pass")


def _overlap_builder(task: str) -> str:
    return f"""
def build_train_batch(ids):
    train_features, train_targets = vision_fixture.build_task_batch({task!r}, TRAIN_IDS)
    held_features, held_targets = vision_fixture.build_task_batch({task!r}, HELDOUT_IDS)
    features = {{
        name: np.concatenate((held_features[name], train_features[name][:2]), axis=0)
        for name in train_features
    }}
    targets = {{
        name: np.concatenate((held_targets[name], train_targets[name][:2]), axis=0)
        for name in train_targets
    }}
    return _to_torch(features), _to_torch(targets)
"""


def _mutate_train_heldout_overlap(notebook_path: Path, practice: str) -> None:
    _replace_named_function(
        notebook_path, "build_train_batch", _overlap_builder(TRAINING[practice][0])
    )


def _mutate_declared_id_lie(notebook_path: Path, practice: str) -> None:
    _mutate_train_heldout_overlap(notebook_path, practice)
    _replace_named_function(
        notebook_path,
        "validate_actual",
        """
def validate_actual(features, targets):
    return "train", TRAIN_IDS
""",
    )


def _mutate_target_misalignment(notebook_path: Path, practice: str) -> None:
    task = TRAINING[practice][0]
    _replace_named_function(
        notebook_path,
        "build_train_batch",
        f"""
def build_train_batch(ids):
    features, targets = vision_fixture.build_task_batch({task!r}, TRAIN_IDS)
    targets = {{name: value[::-1].copy() for name, value in targets.items()}}
    return _to_torch(features), _to_torch(targets)
""",
    )


def _mutate_unknown_feature(notebook_path: Path, practice: str) -> None:
    assert practice == "p17"
    _replace_named_function(
        notebook_path,
        "build_train_batch",
        """
def build_train_batch(ids):
    features, targets = vision_fixture.build_task_batch('vit', TRAIN_IDS)
    features["image"][0,0,0,0] += np.float32(.123)
    return _to_torch(features), _to_torch(targets)
""",
    )


def _mutate_duplicate_feature(notebook_path: Path, practice: str) -> None:
    assert practice == "p17"
    _replace_named_function(
        notebook_path,
        "build_train_batch",
        """
def build_train_batch(ids):
    features, targets = vision_fixture.build_task_batch('vit', TRAIN_IDS)
    features["image"][1] = features["image"][0]
    targets["label"][1] = targets["label"][0]
    return _to_torch(features), _to_torch(targets)
""",
    )


def _mutate_compensated_direct_ce(notebook_path: Path, practice: str) -> None:
    if practice == "p17":
        replacement = """
def compute_loss(model, features, targets):
    validate_actual(features, targets)
    logits = model(features["image"])
    return F.cross_entropy(logits.flip(-1), 1-targets["label"], reduction="mean")
"""
    elif practice == "p19":
        replacement = """
def compute_loss(model, features, targets):
    validate_actual(features, targets)
    logits = model(features["image"])
    return F.cross_entropy(logits.flip(1), 1-targets["mask"], reduction="mean")
"""
    elif practice == "p20":
        replacement = """
def compute_loss(model, features, targets):
    validate_actual(features, targets)
    logits = model(features["node_features"], features["adjacency"])
    return F.cross_entropy(logits.flip(-1), 1-targets["label"], reduction="mean")
"""
    else:
        raise AssertionError(practice)
    _replace_named_function(notebook_path, "compute_loss", replacement)


def _mutate_final_update_wrong_gradient(notebook_path: Path) -> None:
    _replace_named_function(
        notebook_path,
        "compute_loss",
        """
def compute_loss(model, features, targets):
    validate_actual(features, targets)
    logits = model(features["image"])
    good = F.cross_entropy(logits, targets["label"], reduction="mean")
    if model.training:
        compute_loss.training_calls = getattr(compute_loss, "training_calls", 0) + 1
        if compute_loss.training_calls == 12:
            wrong = F.cross_entropy(logits, targets["label"].roll(1), reduction="mean")
            return good.detach() + wrong - wrong.detach()
    return good
""",
    )


def _mutate_final_update_manual_wrong_gradient(notebook_path: Path) -> None:
    _replace_named_function(
        notebook_path,
        "compute_loss",
        """
def compute_loss(model, features, targets):
    validate_actual(features, targets)
    logits = model(features["image"])
    good = F.cross_entropy(logits, targets["label"], reduction="mean")
    if model.training:
        compute_loss.training_calls = getattr(compute_loss, "training_calls", 0) + 1
        if compute_loss.training_calls == 12:
            wrong = -F.log_softmax(logits,1).gather(1,targets["label"].roll(2)[:,None]).mean()
            return good.detach() + wrong - wrong.detach()
    return good
""",
    )


def _mutate_train_ignores_authenticated_loss(notebook_path: Path) -> None:
    _replace_named_function(
        notebook_path,
        "train_vit_classifier",
        """
def train_vit_classifier(model, batch, optimizer):
    features, targets = batch
    role, ids = validate_actual(features, targets)
    if role != "train" or ids != TRAIN_IDS:
        raise ValueError("optimizer batches must contain only the immutable train split")
    trace = []
    model.train()
    for update in range(1,13):
        optimizer.zero_grad(set_to_none=True)
        loss = compute_loss(model, features, targets)
        if update == 12:
            logits = model(features["image"])
            wrong = -F.log_softmax(logits,1).gather(1,targets["label"].roll(2)[:,None]).mean()
            wrong.backward()
        else:
            loss.backward()
        optimizer.step()
        trace.append({"update":update, "mean_ce":float(loss.detach())})
    return tuple(trace)
""",
    )


def _mutate_final_parameter_gradients(notebook_path: Path) -> None:
    _replace_fragment_in_function(
        notebook_path,
        "train_vit_classifier",
        "loss.backward()",
        """loss.backward()
        if update == 12:
            for parameter in model.parameters():
                if parameter.grad is not None:
                    parameter.grad.neg_()""",
    )


def test_ci_only_reference_reconstructs_fixed_seed_traces_without_final_tensors() -> None:
    reference = _reference_module()
    assert reference.reconstruct_reference_results() == reference.EXPECTED_RESULTS
    assert reference.SEED == 20260901

    def values(value):
        if isinstance(value, dict):
            for nested in value.values():
                yield from values(nested)
        elif isinstance(value, (tuple, list)):
            for nested in value:
                yield from values(nested)
        else:
            yield value

    assert not any(isinstance(value, reference.torch.Tensor) for value in values(reference.EXPECTED_RESULTS))


def test_ci_only_reference_has_no_book_learner_or_solution_imports() -> None:
    source = REFERENCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(REFERENCE))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    assert imported_roots <= {
        "__future__",
        "collections",
        "hashlib",
        "math",
        "random",
        "struct",
        "types",
        "typing",
        "numpy",
        "torch",
    }
    assert "importlib" not in imported_roots
    assert "book1" not in source and "book2" not in source


@pytest.mark.parametrize("practice", tuple(TRAINING))
def test_untouched_training_answers_pass_independent_integrity_execution(
    tmp_path: Path, practice: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _instrument_training_notebook(notebook_path, practice)
    _execute(notebook_path)


@pytest.mark.parametrize("practice", tuple(TRAINING), ids=lambda value: f"{value}-no-update")
def test_no_optimizer_update_mutant_fails(tmp_path: Path, practice: str) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _mutate_no_update(notebook_path, practice)
    _instrument_training_notebook(notebook_path, practice)
    _assert_execution_fails(notebook_path)


@pytest.mark.parametrize(
    "practice", tuple(TRAINING), ids=lambda value: f"{value}-train-heldout-overlap"
)
def test_train_heldout_feature_overlap_mutant_fails(tmp_path: Path, practice: str) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _mutate_train_heldout_overlap(notebook_path, practice)
    _instrument_training_notebook(notebook_path, practice)
    _assert_execution_fails(notebook_path)


@pytest.mark.parametrize(
    "practice", tuple(TRAINING), ids=lambda value: f"{value}-target-row-misalignment"
)
def test_target_row_substitution_or_misalignment_mutant_fails(
    tmp_path: Path, practice: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _mutate_target_misalignment(notebook_path, practice)
    _instrument_training_notebook(notebook_path, practice)
    _assert_execution_fails(notebook_path)


@pytest.mark.parametrize("practice", ("p17", "p19", "p20"))
def test_actual_direct_ce_rejects_compensated_logit_and_target_flip(
    tmp_path: Path, practice: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _mutate_compensated_direct_ce(notebook_path, practice)
    _instrument_training_notebook(notebook_path, practice)
    _assert_execution_fails(notebook_path)


def test_p17_final_update_rejects_value_preserving_wrong_target_gradient(
    tmp_path: Path,
) -> None:
    notebook_path = _working_notebook(tmp_path, "p17")
    _mutate_final_update_wrong_gradient(notebook_path)
    _instrument_training_notebook(notebook_path, "p17")
    _assert_execution_fails(notebook_path)


def test_p17_returned_loss_rejects_manual_value_preserving_wrong_gradient(
    tmp_path: Path,
) -> None:
    notebook_path = _working_notebook(tmp_path, "p17")
    _mutate_final_update_manual_wrong_gradient(notebook_path)
    _instrument_training_notebook(notebook_path, "p17")
    _assert_execution_fails(notebook_path)


def test_p17_optimizer_rejects_ignoring_authenticated_loss_for_extra_forward(
    tmp_path: Path,
) -> None:
    notebook_path = _working_notebook(tmp_path, "p17")
    _mutate_train_ignores_authenticated_loss(notebook_path)
    _instrument_training_notebook(notebook_path, "p17")
    _assert_execution_fails(notebook_path)


def test_p17_optimizer_rejects_direct_parameter_gradient_substitution(
    tmp_path: Path,
) -> None:
    notebook_path = _working_notebook(tmp_path, "p17")
    _mutate_final_parameter_gradients(notebook_path)
    _instrument_training_notebook(notebook_path, "p17")
    _assert_execution_fails(notebook_path)


@pytest.mark.parametrize("practice", tuple(TRAINING), ids=lambda value: f"{value}-declared-id-lie")
def test_declared_train_ids_cannot_hide_heldout_features(tmp_path: Path, practice: str) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _mutate_declared_id_lie(notebook_path, practice)
    _instrument_training_notebook(notebook_path, practice)
    _assert_execution_fails(notebook_path)


@pytest.mark.parametrize(
    ("mutation", "variant"),
    (
        pytest.param(_mutate_unknown_feature, "unknown", id="p17-unknown-feature"),
        pytest.param(_mutate_duplicate_feature, "duplicate", id="p17-duplicate-row-in-batch"),
    ),
)
def test_unknown_or_duplicate_feature_rows_fail(tmp_path: Path, mutation, variant: str) -> None:
    notebook_path = _working_notebook(tmp_path, "p17")
    mutation(notebook_path, "p17")
    _instrument_training_notebook(notebook_path, "p17")
    _assert_execution_fails(notebook_path)


@pytest.mark.parametrize(
    ("function_name", "old", "new"),
    (
        pytest.param(
            "forward",
            "torch.cat((decoder,skip),dim=1)",
            "torch.cat((decoder,decoder),dim=1)",
            id="p19-skip-concatenation-omitted",
        ),
        pytest.param(
            "forward",
            "logits=self.head(fused)",
            "logits=F.avg_pool2d(self.head(fused),2)",
            id="p19-wrong-segmentation-output-resolution",
        ),
    ),
)
def test_p19_skip_and_segmentation_output_mutants_fail(
    tmp_path: Path, function_name: str, old: str, new: str
) -> None:
    notebook_path = _working_notebook(tmp_path, "p19")
    _replace_fragment_in_function(notebook_path, function_name, old, new)
    _instrument_training_notebook(notebook_path, "p19")
    _assert_execution_fails(notebook_path)


def test_p20_invalid_edge_aggregation_mutant_fails(tmp_path: Path) -> None:
    notebook_path = _working_notebook(tmp_path, "p20")
    _replace_fragment_in_function(
        notebook_path,
        "mean_neighbor_aggregate",
        "torch.bmm(adjacency_float,nodes)/degree",
        "torch.bmm(adjacency_float.transpose(1,2),nodes)/degree",
    )
    _instrument_training_notebook(notebook_path, "p20")
    _assert_execution_fails(notebook_path)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        pytest.param(
            "F.binary_cross_entropy_with_logits(objectness_logits,objectness_target,reduction=\"mean\")",
            "F.binary_cross_entropy_with_logits(-objectness_logits,1-objectness_target,reduction=\"mean\")",
            id="p18-compensated-bce-input-target-flip",
        ),
        pytest.param(
            "F.cross_entropy(class_logits.permute(0,2,3,1)[positive],class_target[positive],reduction=\"mean\")",
            "F.cross_entropy(class_logits.flip(1).permute(0,2,3,1)[positive],1-class_target[positive],reduction=\"mean\")",
            id="p18-compensated-class-ce-flip",
        ),
        pytest.param(
            "F.smooth_l1_loss(predicted_boxes,target_boxes,reduction=\"mean\")",
            "F.smooth_l1_loss(1-predicted_boxes,1-target_boxes,reduction=\"mean\")",
            id="p18-compensated-smooth-l1-reflection",
        ),
    ),
)
def test_p18_actual_loss_primitives_reject_compensated_wrong_arguments(
    tmp_path: Path, old: str, new: str
) -> None:
    notebook_path = _working_notebook(tmp_path, "p18")
    _replace_fragment_in_function(notebook_path, "_loss_components", old, new)
    _instrument_training_notebook(notebook_path, "p18")
    _assert_execution_fails(notebook_path)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        pytest.param(
            'heldout_optimizer = set(trace["optimizer_ids"]) & set(trace["heldout_ids"])',
            "heldout_optimizer = set()",
            id="p24-leakage-audit-disabled",
        ),
        pytest.param(
            'trace.get("q_source") == expected["q_source"]',
            'trace.get("q_source") == "graph_tokens"',
            id="p24-cross-modal-q-source-reversed",
        ),
    ),
)
def test_p24_qkv_reversal_or_leakage_audit_mutant_fails(tmp_path: Path, old: str, new: str) -> None:
    notebook_path = _working_notebook(tmp_path, "p24")
    _replace_fragment_in_function(notebook_path, "audit_cross_modal_sources", old, new)
    _instrument_p24_audit(notebook_path)
    _assert_execution_fails(notebook_path)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        pytest.param(
            'and trace.get("q_source") == expected["q_source"]',
            "and True",
            id="p24-delete-q-source-clause",
        ),
        pytest.param(
            'and trace.get("k_source") == expected["k_source"]',
            "and True",
            id="p24-delete-k-source-clause",
        ),
        pytest.param(
            'and trace.get("v_source") == expected["v_source"]',
            "and True",
            id="p24-delete-v-source-clause",
        ),
        pytest.param(
            'and tuple(trace.get("score_shape", ())) == expected["score_shape"]',
            "and True",
            id="p24-delete-score-shape-clause",
        ),
        pytest.param(
            'heldout_optimizer = set(trace["optimizer_ids"]) & set(trace["heldout_ids"])',
            'heldout_optimizer = {"masked-by-q-error"} if trace.get("q_source") == "graph_tokens" else set()',
            id="p24-couple-leakage-to-q-error",
        ),
    ),
)
def test_p24_each_direction_and_leakage_clause_is_independently_required(
    tmp_path: Path, old: str, new: str
) -> None:
    notebook_path = _working_notebook(tmp_path, "p24")
    _replace_fragment_in_function(notebook_path, "audit_cross_modal_sources", old, new)
    _instrument_p24_audit(notebook_path)
    _assert_execution_fails(notebook_path)


def test_untouched_p24_cross_modal_audit_passes(tmp_path: Path) -> None:
    notebook_path = _working_notebook(tmp_path, "p24")
    _instrument_p24_audit(notebook_path)
    _execute(notebook_path)


def test_book2_ci_runs_vision_transformer_integrity_suite() -> None:
    source = CI_LOCAL.read_text(encoding="utf-8")
    assert "uv run pytest -q tests/test_vision_transformer_checks.py" in source
