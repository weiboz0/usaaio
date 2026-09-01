from __future__ import annotations

import shutil
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"
UNIT = BOOK2_ROOT / "units" / "B2-020-language-transformers"
CI_LOCAL = ROOT / "scripts/ci-local.sh"

FUNCTION_VARIANTS = (
    pytest.param(
        "p07",
        """def update_embedding_table(table, head, context_ids, target_ids):
    optimizer = torch.optim.SGD([table, *head.parameters()], lr=0.1)
    optimizer.zero_grad(set_to_none=True)
    loss = F.cross_entropy(head(table[context_ids]), target_ids, reduction="mean")
    loss.backward()
    optimizer.step()
    fresh_loss = F.cross_entropy(head(table[context_ids]), target_ids, reduction="mean")
    return fresh_loss, table
""",
        """def update_embedding_table(table, head, context_ids, target_ids):
    fresh_loss = F.cross_entropy(head(table[context_ids]), target_ids, reduction="mean")
    return fresh_loss, table
""",
        id="p07-no-table-update",
    ),
    pytest.param(
        "p11",
        """def apply_mlm_mask(token_ids, selected, mask_id=1):
    corrupted = token_ids.clone()
    labels = torch.full_like(token_ids, -100)
    corrupted[selected] = mask_id
    labels[selected] = token_ids[selected]
    return corrupted, labels
""",
        """def apply_mlm_mask(token_ids, selected, mask_id=1):
    corrupted = token_ids.clone()
    labels = torch.full_like(token_ids, -100)
    labels[selected] = token_ids[selected]
    return corrupted, labels
""",
        id="p11-visible-token",
    ),
    pytest.param(
        "p18",
        """def shift_targets(tokens):
    return tokens[:, :-1], tokens[:, 1:]
""",
        """def shift_targets(tokens):
    return tokens[:, :-1], tokens[:, :-1]
""",
        id="p18-unshifted-targets",
    ),
    pytest.param(
        "p21",
        """def configure_frozen_stage_optimizer(encoder, classifier):
    for parameter in encoder.parameters():
        parameter.requires_grad_(False)
    return torch.optim.AdamW(classifier.parameters(), lr=0.03, weight_decay=0, betas=(0.9,0.999), eps=1e-8)
""",
        """def configure_frozen_stage_optimizer(encoder, classifier):
    return torch.optim.AdamW([*encoder.parameters(), *classifier.parameters()], lr=0.03, weight_decay=0, betas=(0.9,0.999), eps=1e-8)
""",
        id="p21-encoder-optimized-while-frozen",
    ),
    pytest.param(
        "p24",
        """def evaluation_indices(train_indices, candidate_indices):
    train = set(train_indices)
    return sorted(index for index in set(candidate_indices) if index not in train)
""",
        """def evaluation_indices(train_indices, candidate_indices):
    return sorted(set(candidate_indices))
""",
        id="p24-train-eval-leakage",
    ),
)

PROTOCOL_VARIANTS = (
    pytest.param(
        "p19",
        'for phase, count in (("causal", 40), ("mlm", 40)):',
        'for phase, count in (("causal", 80),):',
        id="p19-skip-mlm",
    ),
    pytest.param(
        "p19",
        """    for phase, count in (("causal", 40), ("mlm", 40)):
        for update_index in range(1, count + 1):
""",
        """    for phase, count in (("causal", 40), ("mlm", 40)):
        if phase == "mlm":
            optimizer = torch.optim.AdamW(
                [*encoder.parameters(), *head.parameters()], lr=0.03, weight_decay=0,
                betas=(0.9, 0.999), eps=1e-8, amsgrad=False, foreach=False, fused=False,
            )
        for update_index in range(1, count + 1):
""",
        id="p19-reset-optimizer",
    ),
    pytest.param(
        "p19",
        """            else:
                logits = head(encoder(mlm_inputs, mask_mode="bidirectional"))
                loss = F.cross_entropy(logits.reshape(-1,12), mlm_labels.reshape(-1), ignore_index=-100, reduction="mean")
                mask_mode = "bidirectional"
""",
        """            else:
                logits = head(encoder(mlm_inputs, mask_mode="causal"))
                loss = F.cross_entropy(logits.reshape(-1,12), mlm_labels.reshape(-1), ignore_index=-100, reduction="mean")
                mask_mode = "bidirectional"
""",
        id="p19-causal-mask-during-mlm",
    ),
    pytest.param(
        "p20",
        """def loaded_encoder():
    assert state.ENCODER_STATE_HASH == EXPECTED_STATE_HASH
    encoder = TinyEncoder()
    tensor_state = {name: torch.tensor(value, dtype=torch.float32) for name, value in state.ENCODER_TENSORS.items()}
    encoder.load_state_dict(tensor_state, strict=True)
    encoder.loaded_state_verified = all(torch.equal(value, tensor_state[name]) for name, value in encoder.state_dict().items())
    return encoder
""",
        """def loaded_encoder():
    encoder = TinyEncoder()
    encoder.loaded_state_verified = False
    return encoder
""",
        id="p20-no-load-random-encoder",
    ),
    pytest.param(
        "p21",
        """encoder = TinyEncoder()
expected_encoder_state = {name: torch.tensor(value, dtype=torch.float32) for name, value in state.ENCODER_TENSORS.items()}
encoder.load_state_dict(expected_encoder_state, strict=True)
loaded_state_verified = all(torch.equal(value, expected_encoder_state[name]) for name, value in encoder.state_dict().items())
""",
        """encoder = TinyEncoder()
loaded_state_verified = False
""",
        id="p21-no-load-random-encoder",
    ),
)

PRACTICES = tuple(
    sorted({variant.values[0] for variant in (*FUNCTION_VARIANTS, *PROTOCOL_VARIANTS)})
)


def _working_notebook(tmp_path: Path, practice: str) -> Path:
    working_unit = tmp_path / UNIT.name
    shutil.copytree(UNIT, working_unit)
    return working_unit / "practice" / f"{practice}_solution.ipynb"


def _substitute(notebook_path: Path, old: str, new: str) -> None:
    notebook = nbformat.read(notebook_path, as_version=4)
    matches = sum(cell.source.count(old) for cell in notebook.cells if cell.cell_type == "code")
    assert matches == 1, f"expected one substitution seam in {notebook_path.name}, found {matches}"
    for cell in notebook.cells:
        if cell.cell_type == "code" and old in cell.source:
            cell.source = cell.source.replace(old, new)
    nbformat.write(notebook, notebook_path)


def _execute(notebook_path: Path):
    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        resources={"metadata": {"path": str(notebook_path.parent)}},
    )
    return notebook, client


def _assert_answer_check_fails(notebook_path: Path) -> None:
    notebook, client = _execute(notebook_path)
    with pytest.raises(CellExecutionError):
        client.execute()

    failures = [
        (index, output.get("ename"))
        for index, cell in enumerate(notebook.cells)
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    assert failures == [(len(notebook.cells) - 1, "AssertionError")]
    assert notebook.cells[-2].source.strip() == "### Answer check"


@pytest.mark.parametrize("practice", PRACTICES)
def test_untouched_language_transformer_answer_check_passes(
    tmp_path: Path, practice: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _, client = _execute(notebook_path)
    client.execute()


@pytest.mark.parametrize(("practice", "old", "new"), FUNCTION_VARIANTS)
def test_named_function_wrong_answer_fails_final_answer_check(
    tmp_path: Path, practice: str, old: str, new: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _substitute(notebook_path, old, new)
    _assert_answer_check_fails(notebook_path)


@pytest.mark.parametrize(("practice", "old", "new"), PROTOCOL_VARIANTS)
def test_protocol_or_loader_wrong_answer_fails_final_answer_check(
    tmp_path: Path, practice: str, old: str, new: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    _substitute(notebook_path, old, new)
    _assert_answer_check_fails(notebook_path)


@pytest.mark.parametrize("practice", ("p20", "p21"))
def test_tampered_encoder_tensor_fails_recomputed_state_hash(
    tmp_path: Path, practice: str
) -> None:
    notebook_path = _working_notebook(tmp_path, practice)
    state_path = notebook_path.parents[1] / "data" / "tiny_encoder_state.py"
    source = state_path.read_text(encoding="utf-8")
    original = "-0.844856858253479"
    assert source.count(original) == 1
    state_path.write_text(source.replace(original, "-0.744856858253479"), encoding="utf-8")
    notebook, client = _execute(notebook_path)
    with pytest.raises(CellExecutionError):
        client.execute()
    failures = [
        index
        for index, cell in enumerate(notebook.cells)
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error" and output.get("ename") == "AssertionError"
    ]
    assert len(failures) == 1
    assert "canonical_encoder_state_hash" in notebook.cells[failures[0]].source


def test_book2_ci_runs_language_transformer_integrity_suite() -> None:
    source = CI_LOCAL.read_text(encoding="utf-8")
    assert "uv run pytest -q tests/test_language_transformer_checks.py" in source
