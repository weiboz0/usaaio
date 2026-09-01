from __future__ import annotations

import importlib.util
import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path

import nbformat
import pytest
import yaml

from tools import audit_curriculum
from tools.checks.coverage import check_coverage
from tools.checks.hygiene import check_hygiene
from tools.checks.layer_boundary import check_layer_boundary
from tools.model import load_syllabus, load_unit_manifests

ROOT = Path(__file__).resolve().parents[1]
BOOK1_ROOT = ROOT / "book1"
BOOK2_ROOT = ROOT / "book2"
UNIT_ID = "B2-020-language-transformers"
UNIT = BOOK2_ROOT / "units" / UNIT_ID
SEED = 20260812
OWNED = {
    "embedding-model-training",
    "learned-token-embedding",
    "language-transformer",
    "causal-language-modeling",
    "masked-language-modeling",
    "nlp-pretraining-objectives",
    "nlp-fine-tuning-protocol",
    "transformer-nlp-task-design",
}
PREREQ_UNITS = [
    "book1:F1-scientific-python",
    "book1:F3-matrices",
    "book1:C6-pytorch",
    "book1:C7-cnn-transfer",
    "book1:C11-neural-training",
    "B2-019-attention-transformers",
]
IMPORTED = {
    "attention-mask",
    "causal-self-attention",
    "sinusoidal-positional-encoding",
    "transformer-block",
    "book1:random-seeding",
    "book1:matrix-multiplication",
    "book1:torch-tensors",
    "book1:nn-module",
    "book1:requires-grad",
    "book1:tensor-shape-tracing",
    "book1:softmax",
    "book1:cross-entropy-loss",
    "book1:torch-optimizers",
    "book1:autograd-training",
}


def _manifest() -> dict:
    return yaml.safe_load((UNIT / "manifest.yaml").read_text(encoding="utf-8"))


def _notebook(path: Path) -> nbformat.NotebookNode:
    return nbformat.read(path, as_version=4)


def _source(path: Path) -> str:
    return "\n".join(str(cell.source) for cell in _notebook(path).cells)


def _fixture_module():
    path = UNIT / "data/language_fixture.py"
    spec = importlib.util.spec_from_file_location("b2_020_language_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _register_module():
    path = ROOT / "scripts/verify-register.py"
    spec = importlib.util.spec_from_file_location("b2_020_verify_register", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.BOOK_ROOT = BOOK2_ROOT
    return module


def test_manifest_publishes_exact_statement_ledger_and_required_solutions() -> None:
    raw = _manifest()
    parsed = {
        item.unit_id: item
        for item in load_unit_manifests(BOOK2_ROOT, as_of_date=date(2026, 9, 30))
    }[UNIT_ID]

    assert raw["solution_policy"] == "required"
    assert raw["length"] == "double"
    assert raw["prereq_units"] == PREREQ_UNITS
    assert set(raw["concepts_taught"]) == OWNED
    assert set(raw["concepts_used"]) == IMPORTED
    assert raw["concept_prerequisites"] == raw["concepts_used"]
    assert parsed.lesson_sessions == [90] * 5
    assert raw["estimated_minutes"] == {
        "lesson": 450,
        "lesson_sessions": [90] * 5,
        "practice": 1120,
        "review": 60,
    }
    assert [row["id"] for row in raw["practice"]] == [
        f"B2-020-p{number:02}" for number in range(1, 25)
    ]
    assert sum(row["minutes"] for row in raw["practice"]) == 1120
    assert Counter(row["difficulty"] for row in raw["practice"]) == {
        "intro": 7,
        "core": 11,
        "advanced": 6,
    }
    assert Counter(row["type"] for row in raw["practice"]) == {
        "mc": 4,
        "mc-normal-form": 1,
        "constrained-coding": 7,
        "proof": 4,
        "integrative": 4,
        "scenario": 2,
        "challenge": 2,
    }
    assert all(row["compute"] == {"policy": "cpu", "seed": SEED} for row in raw["practice"])
    assert all(row["solution_path"].endswith("_solution.ipynb") for row in raw["practice"])
    assert sorted(path.name for path in UNIT.glob("practice/*_solution.ipynb")) == [
        f"p{number:02}_solution.ipynb" for number in range(1, 25)
    ]


def test_task4_solutions_preserve_headers_answer_register_and_executable_checks() -> None:
    raw = _manifest()
    register = _register_module()
    answer_register = {
        1: 'ANSWER = "B"',
        2: "assert ANSWER == 5",
        3: 'ANSWER = "C"',
        4: 'ANSWER = "B"',
        5: 'ANSWER = "B"',
    }
    implementation_register = {
        6: "def one_hot_embedding_lookup",
        7: "def update_embedding_table",
        8: "def build_causal_batch",
        9: "def tiny_causal_lm_forward",
        10: "def masked_token_cross_entropy",
        11: "def apply_mlm_mask",
        12: "def attach_classification_head",
        17: "def bridge_loss",
        18: "def shift_targets",
        19: "def run_pretraining_protocol",
        20: "RESULT = (encoder, head, metrics)",
        21: "def configure_frozen_stage_optimizer",
        22: "DESIGNS =",
        23: "mutated_logits =",
        24: "def evaluation_indices",
    }
    for number, row in enumerate(raw["practice"], start=1):
        statement_path = UNIT / row["path"]
        solution_path = UNIT / row["solution_path"]
        statement = _notebook(statement_path)
        solution = _notebook(solution_path)
        solution_source = _source(solution_path)

        assert solution.cells[0].source.startswith(
            f"# {UNIT_ID} — Practice p{number:02} — Solution\n"
        )
        assert f"**Type:** {row['type']} · **Difficulty:** {row['difficulty']}" in solution.cells[0].source
        assert f"**Concepts:** {', '.join(row['concepts'])}" in solution.cells[0].source
        assert "Round 2 extension" in solution.cells[0].source
        assert "compute.policy: cpu" in solution.cells[0].source
        assert not register._check_solution_header(UNIT_ID, row)
        assert solution.metadata["usaaio"] == {
            **statement.metadata["usaaio"],
            "surface": f"practice/p{number:02}_solution.ipynb",
        }
        assert solution.cells[-2].cell_type == "markdown"
        assert solution.cells[-2].source.strip() == "### Answer check"
        assert solution.cells[-1].cell_type == "code"
        assert "assert " in solution.cells[-1].source
        assert all(
            cell.execution_count is None and not cell.outputs
            for cell in solution.cells
            if cell.cell_type == "code"
        )
        if number in answer_register:
            assert answer_register[number] in solution_source
        if number in implementation_register:
            assert implementation_register[number] in solution_source


def _copy_book2(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    shutil.copy2(ROOT / "books.yaml", repo / "books.yaml")
    (repo / "book1").mkdir()
    shutil.copy2(BOOK1_ROOT / "syllabus.md", repo / "book1/syllabus.md")
    shutil.copytree(BOOK2_ROOT, repo / "book2")
    return repo / "book2"


def test_task4_policy_and_solution_set_fail_closed(tmp_path: Path) -> None:
    deferred = _copy_book2(tmp_path / "deferred")
    deferred_manifest = deferred / "units" / UNIT_ID / "manifest.yaml"
    raw = yaml.safe_load(deferred_manifest.read_text(encoding="utf-8"))
    raw["solution_policy"] = {
        "status": "deferred",
        "plan": "plan-020",
        "expires": "2026-09-30",
    }
    deferred_manifest.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="must not have a solution file present"):
        audit_curriculum.build_inventory(deferred)
    with pytest.raises(ValueError, match="must not have a solution file present"):
        check_coverage(deferred)
    assert not check_layer_boundary(deferred).ok

    missing = _copy_book2(tmp_path / "missing")
    (missing / "units" / UNIT_ID / "practice/p24_solution.ipynb").unlink()
    with pytest.raises(audit_curriculum.InventoryError, match="declared notebook is missing"):
        audit_curriculum.build_inventory(missing)
    assert any("missing solution path" in error for error in check_coverage(missing).errors)
    assert any(
        "cpu task requires a local solution path" in error
        for error in check_layer_boundary(missing).errors
    )


def test_task4_ci_executes_b2_020_solutions_with_twenty_second_timeout() -> None:
    script = (ROOT / "scripts/ci-local.sh").read_text(encoding="utf-8")
    assert (
        "if [[ $relative == units/B2-020-language-transformers/practice/"
        "p??_solution.ipynb ]]; then"
    ) in script
    assert (
        'timeout 20s uv run --project .. jupyter execute "$relative"'
    ) in script


def test_statement_notebooks_are_complete_unexecuted_and_source_isolated() -> None:
    paths = [
        UNIT / "lesson.ipynb",
        UNIT / "review.ipynb",
        *sorted((UNIT / "lessons").glob("*.ipynb")),
        *sorted((UNIT / "practice").glob("p??.ipynb")),
    ]
    assert len(paths) == 32
    assert check_hygiene(BOOK2_ROOT).ok
    for path in paths:
        notebook = _notebook(path)
        meta = notebook.metadata["usaaio"]
        source = _source(path)
        assert meta["unit"] == UNIT_ID
        assert meta["layer"] == "Round 2 extension"
        assert meta["compute"] == {"policy": "cpu", "seed": SEED}
        assert "Round 2 extension" in source
        assert "compute.policy: cpu" in source
        assert "solution" not in path.name
        assert "tiny_encoder_checkpoint" not in source
        assert "book1/reference" not in source
        assert all(cell.execution_count is None for cell in notebook.cells if cell.cell_type == "code")
        assert all(not cell.outputs for cell in notebook.cells if cell.cell_type == "code")


def test_lessons_have_substantive_sections_checkpoints_and_required_spine() -> None:
    lessons = sorted((UNIT / "lessons").glob("0[1-5]-*.ipynb"))
    assert len(lessons) == 5
    required = [
        ("one-hot", "embedding", "cross-entropy", "gradient"),
        ("sinusoidal", "causal", "shift", "logits"),
        ("masked", "learned positional", "GELU", "AdamW"),
        ("checkpoint", "frozen", "classification", "held-out"),
        ("classify", "tag", "generate", "retrieve"),
    ]
    for path, needles in zip(lessons, required, strict=True):
        source = _source(path)
        section_count = sum(
            1
            for line in source.splitlines()
            if line.startswith("## ") and line[3:4].isdigit()
        )
        assert 6 <= section_count <= 10
        assert source.count("**Checkpoint") >= 2 * section_count
        assert "## Collected checkpoint answers" in source
        assert source.count("**Answer ") >= 2 * section_count
        assert "Common pitfalls" in source
        assert "Exam connections" in source
        assert "Going deeper" in source
        for needle in needles:
            assert needle.lower() in source.lower()
    for name in ("01-train-token-embeddings.ipynb", "04-fine-tune-a-language-transformer.ipynb"):
        source = _source(UNIT / "lessons" / name)
        assert "**Fully worked computation.**" in source
    embedding_source = _source(UNIT / "lessons/01-train-token-embeddings.ipynb")
    assert "E[4] = [0.20, -0.10]" in embedding_source
    assert "softmax([0.30, -0.20, 0.10]) = [0.4123, 0.2501, 0.3376]" in embedding_source
    assert "loss = -log(0.2501) = 1.3859" in embedding_source
    assert "The logit gradient is `[0.4123, -0.7499, 0.3376]`" in embedding_source
    assert "dL/dE[4] = [1.1622, 0.3376]" in embedding_source
    assert "E[4] after = [0.0838, -0.1338]" in embedding_source
    assert "[-1.0000, 0.0000] -> [-0.9850, -0.0075]" in embedding_source
    assert "E[6] = [0.00, 0.00]" in embedding_source

    fine_tune_source = _source(UNIT / "lessons/04-fine-tune-a-language-transformer.ipynb")
    assert "h = [0.40, -0.20]" in fine_tune_source
    assert "logits = [0.22, -0.16]" in fine_tune_source
    assert "softmax([0.22, -0.16]) = [0.5939, 0.4061]" in fine_tune_source
    assert "loss = -log(0.4061) = 0.9011" in fine_tune_source
    assert "dL/dW = [[0.2376, -0.1188], [-0.2376, 0.1188]]" in fine_tune_source
    assert "head_before = [[0.50, -0.10], [-0.20, 0.40]]" in fine_tune_source
    assert "head_after = [[0.4762, -0.0881], [-0.1762, 0.3881]]" in fine_tune_source
    assert "encoder_before = [0.40, -0.20]" in fine_tune_source
    assert "encoder_after = [0.40, -0.20]" in fine_tune_source


def test_pretraining_heldout_rows_and_masked_pairs_are_disjoint_from_training() -> None:
    fixture = _fixture_module()
    causal_train = {tuple(row) for row in fixture.CAUSAL_TRAIN_IDS}
    causal_heldout = {tuple(row) for row in fixture.CAUSAL_HELDOUT_IDS}
    assert causal_train.isdisjoint(causal_heldout)

    mlm_train = {
        (tuple(input_ids), tuple(label_ids))
        for input_ids, label_ids in zip(fixture.MLM_INPUT_IDS, fixture.MLM_LABEL_IDS, strict=True)
    }
    mlm_heldout = {
        (tuple(input_ids), tuple(label_ids))
        for input_ids, label_ids in zip(
            fixture.MLM_HELDOUT_IDS, fixture.MLM_HELDOUT_LABEL_IDS, strict=True
        )
    }
    assert mlm_train.isdisjoint(mlm_heldout)




def test_collected_checkpoint_answers_match_their_numbered_questions() -> None:
    expected = {
        "02-causal-transformer-language-model.ipynb": (
            "**Answer 2A.** `j <= i`.",
            "**Answer 3A.** both inputs and targets have shape `(3,7)`.",
            "**Answer 5A.** the `Linear(8,12)` vocabulary head.",
        ),
        "03-pretraining-objectives.ipynb": (
            "**Answer 2A.** copying preserves true labels",
            "**Answer 6B.** it is the first MLM update with optimizer step 41.",
            "**Answer 7B.** bidirectional.",
        ),
        "05-language-task-design-and-audit.ipynb": (
            "**Answer 2A.** `(B,N,L)` token logits.",
            "**Answer 6B.** train rows only.",
            "**Answer 8A.** p24.",
        ),
    }
    for name, answers in expected.items():
        source = _source(UNIT / "lessons" / name)
        assert all(answer in source for answer in answers)


def test_bridge_distinguishes_remediation_from_attention_prerequisite() -> None:
    source = _source(UNIT / "lessons/00-book1-bridge.ipynb")
    assert "book1:C8-embeddings" in source
    assert "fixed-vector" in source
    assert "token-to-index" in source
    assert "B2-019-attention-transformers" in source
    assert "causal mask" in source
    assert "bridge_feedback" in source


def test_every_owned_concept_has_three_direct_practices_and_tags_are_closed() -> None:
    raw = _manifest()
    counts = Counter(
        concept
        for row in raw["practice"]
        for concept in set(row["concepts"]) & OWNED
    )
    assert all(counts[concept] >= 3 for concept in OWNED)
    closure = OWNED | IMPORTED
    assert all(set(row["concepts"]) <= closure for row in raw["practice"])


def test_five_integrity_function_names_are_pinned_in_statements() -> None:
    expected = {
        "p07": "update_embedding_table",
        "p11": "apply_mlm_mask",
        "p18": "shift_targets",
        "p21": "configure_frozen_stage_optimizer",
        "p24": "evaluation_indices",
    }
    for practice, function in expected.items():
        assert function in _source(UNIT / "practice" / f"{practice}.ipynb")
    assert "run_pretraining_protocol" in _source(UNIT / "practice/p19.ipynb")
    assert "optimizer_step" in _source(UNIT / "practice/p19.ipynb")


def test_training_practices_pin_literal_reproducible_protocols() -> None:
    required = {
        "p17": ("language_fixture.py", "AdamW", "lr=0.03", "40 full-batch updates"),
        "p18": ("language_fixture.py", "AdamW", "lr=0.03", "exactly 80 full-batch updates"),
        "p19": ("[4, 4, 4, 4, 4, 4, 0, 0]", "causal >= 1.020881", "mlm >= 0.969689", "causal_row0_after_red=4", "ATOL=1e-5", "RTOL=1e-5", "padding_idx=0", "key_padding_mask=token_ids.eq(0)", "construct `TinyEncoder` before the distinct `Linear(8,12)` head"),
        "p20": ("language_fixture.py", "AdamW", "lr=0.03", "exactly 40 full-batch updates"),
        "p21": ("language_fixture.py", "AdamW", "lr=0.03", "20 + 20 full-batch updates"),
    }
    for practice, needles in required.items():
        source = _source(UNIT / "practice" / f"{practice}.ipynb")
        for needle in needles:
            assert needle in source


def test_p17_uses_explicit_checked_in_context_target_pairs() -> None:
    fixture = (UNIT / "data/language_fixture.py").read_text(encoding="utf-8")
    statement = _source(UNIT / "practice/p17.ipynb")
    solution = _source(UNIT / "practice/p17_solution.ipynb")
    for name in ("P17_CONTEXT_IDS", "P17_TARGET_IDS"):
        assert name in fixture
        assert name in statement
        assert f"fixture.{name}" in solution


def test_p18_pins_the_full_tiny_causal_transformer_architecture() -> None:
    source = _source(UNIT / "practice/p18.ipynb")
    required = (
        "learned positional embeddings",
        "Linear(8,16)",
        "GELU",
        "LayerNorm eps=1e-5",
        "pre-norm",
        "dropout 0.0",
    )
    assert all(needle in source for needle in required)


def test_fine_tuning_lesson_teaches_recomputed_state_hash_verification() -> None:
    source = _source(UNIT / "lessons/04-fine-tune-a-language-transformer.ipynb")
    assert "canonical_encoder_state_hash" in source
    assert "recompute" in source
    assert "ENCODER_TENSORS" in source


def test_syllabus_and_standards_publish_b2_020_as_double_length() -> None:
    syllabus = load_syllabus(BOOK2_ROOT)
    unit = syllabus.units[UNIT_ID]
    assert unit.prereqs == PREREQ_UNITS
    assert set(unit.teaches) == OWNED
    assert set(unit.concept_prerequisites) == IMPORTED
    assert unit.length == "double"
    standards = (ROOT / "docs/unit-standards.md").read_text(encoding="utf-8")
    assert "F5, F6, C7, C11, C12, B2-019, and B2-020" in standards
    assert standards.count("B2-019") >= 2 and standards.count("B2-020") >= 2


def test_generator_exports_protocol_and_tracked_state_contract() -> None:
    script = UNIT / "scripts/generate_language_data.py"
    spec = importlib.util.spec_from_file_location("b2_020_generator", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    protocol = module.generate_protocol()
    assert len(protocol["trace"]) == 80
    assert [row["phase"] for row in protocol["trace"]] == ["causal"] * 40 + ["mlm"] * 40
    assert [row["optimizer_step"] for row in protocol["trace"]] == list(range(1, 81))
    assert [row["mask_mode"] for row in protocol["trace"]] == ["causal"] * 40 + ["bidirectional"] * 40
    checkpoint = UNIT / "data/tiny_encoder_checkpoint.py"
    state = UNIT / "data/tiny_encoder_state.py"
    assert checkpoint.is_file() and state.is_file()
    checkpoint_ns = module.load_module(checkpoint)
    state_ns = module.load_module(state)
    assert checkpoint_ns.SCHEMA_VERSION == 1
    assert checkpoint_ns.ENCODER_STATE_HASH == state_ns.ENCODER_STATE_HASH
    assert set(vars(state_ns)) & {"INITIAL_LOSSES", "FINAL_LOSSES", "PROBE_EXPECTED_TOP1_IDS"} == set()
    module.verify_committed_artifacts()


def test_generator_instruments_actual_masks_and_one_optimizer(monkeypatch) -> None:
    script = UNIT / "scripts/generate_language_data.py"
    spec = importlib.util.spec_from_file_location("b2_020_generator_instrumented", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    observed_masks: list[str] = []
    optimizers = []
    original_forward = module.TinyEncoder.forward
    original_adamw = module.torch.optim.AdamW

    def observed_forward(self, token_ids, *, mask_mode):
        observed_masks.append(mask_mode)
        return original_forward(self, token_ids, mask_mode=mask_mode)

    class ObservedAdamW(original_adamw):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            optimizers.append(self)

    monkeypatch.setattr(module.TinyEncoder, "forward", observed_forward)
    monkeypatch.setattr(module.torch.optim, "AdamW", ObservedAdamW)
    monkeypatch.setattr(
        module,
        "_heldout_metrics",
        lambda encoder, head, fixture: ({"causal": 2.0, "mlm": 2.0}, {}),
    )

    protocol = module.generate_protocol()

    assert observed_masks == ["causal"] * 40 + ["bidirectional"] * 40
    assert len(optimizers) == 1
    assert [row["optimizer_step"] for row in protocol["trace"]] == list(range(1, 81))


def test_checkpoint_verifier_recomputes_seeded_initial_baseline(monkeypatch) -> None:
    script = UNIT / "scripts/generate_language_data.py"
    spec = importlib.util.spec_from_file_location("b2_020_generator_baseline", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_load = module.load_module

    def inflated_baseline(path: Path):
        loaded = original_load(path)
        if path == module.CHECKPOINT_PATH:
            loaded.INITIAL_LOSSES = {"causal": 1_000_000.0, "mlm": 1_000_000.0}
        return loaded

    monkeypatch.setattr(module, "load_module", inflated_baseline)
    with pytest.raises(AssertionError, match="initial loss"):
        module.verify_committed_artifacts()


def test_checkpoint_verifier_rejects_self_consistent_untrained_checkpoint(monkeypatch) -> None:
    script = UNIT / "scripts/generate_language_data.py"
    spec = importlib.util.spec_from_file_location("b2_020_generator_untrained", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_load = module.load_module
    checkpoint = original_load(module.CHECKPOINT_PATH)
    state = original_load(module.STATE_PATH)
    encoder, head = module.build_models()
    fixture = module._fixture()
    losses, probes = module._heldout_metrics(encoder, head, fixture)
    checkpoint.ENCODER_TENSORS = module._tensor_mapping(encoder)
    checkpoint.HEAD_TENSORS = module._tensor_mapping(head)
    checkpoint.ENCODER_STATE_HASH = module.encoder_state_hash(checkpoint.ENCODER_TENSORS)
    checkpoint.SEMANTIC_HASH = module.semantic_hash(fixture, checkpoint.ENCODER_TENSORS, checkpoint.HEAD_TENSORS)
    checkpoint.INITIAL_LOSSES = losses
    checkpoint.FINAL_LOSSES = losses
    checkpoint.MIN_ABSOLUTE_LOSS_IMPROVEMENTS = {"causal": 0.0, "mlm": 0.0}
    checkpoint.PROBE_EXPECTED_TOP1_IDS = probes
    state.ENCODER_TENSORS = checkpoint.ENCODER_TENSORS
    state.ENCODER_STATE_HASH = checkpoint.ENCODER_STATE_HASH

    def fake_load(path: Path):
        if path == module.CHECKPOINT_PATH:
            return checkpoint
        if path == module.STATE_PATH:
            return state
        return original_load(path)

    monkeypatch.setattr(module, "load_module", fake_load)
    with pytest.raises(AssertionError, match="trusted"):
        module.verify_committed_artifacts()


def test_coverage_promotes_exact_five_rows_without_book1_embedding_evidence() -> None:
    coverage = yaml.safe_load((BOOK2_ROOT / "curriculum/coverage-map.yaml").read_text())
    rows = {row["id"]: row for row in coverage["knowledge_points"]}
    ids = {
        "nlp-word-embeddings",
        "nlp-transformers",
        "nlp-pretraining",
        "nlp-fine-tuning",
        "transformer-nlp-applications",
    }
    assert all(rows[item]["coverage"] == "covered" for item in ids)
    manifest = yaml.safe_load((UNIT / "manifest.yaml").read_text())
    claims = {
        claim["knowledge_point"]: claim
        for claim in manifest["coverage_claims"]
    }
    practice_concepts = {
        practice["id"]: set(practice["concepts"])
        for practice in manifest["practice"]
    }
    for item in ids:
        assert claims[item]["evidence_by_modality"] == rows[item]["evidence_by_modality"]
        shipped = set(rows[item]["shipped_concepts"])
        for evidence in rows[item]["evidence_by_modality"].values():
            assert all(
                practice_concepts[practice["id"]] & shipped
                for practice in evidence["practices"]
            )
    assert claims["nlp-transformers"]["evidence_by_modality"]["model-training"]["practices"] == [
        {"id": "B2-020-p18", "role": "primary"}
    ]
    assert claims["nlp-pretraining"]["evidence_by_modality"]["model-training"]["practices"] == [
        {"id": "B2-020-p19", "role": "primary"}
    ]
    assert rows["nlp-word-embeddings"]["destination"] == UNIT_ID
    assert rows["nlp-word-embeddings"]["disposition"] == "new-unit"
    assert rows["nlp-word-embeddings"]["shipped_concepts"] == ["learned-token-embedding"]
    assert rows["nlp-word-embeddings"]["deficits"]["modalities_missing"] == []
    assert "book1:C8-embeddings" not in json.dumps(rows["nlp-word-embeddings"])


def test_live_schedule_appends_exact_second_six_week_ledger() -> None:
    schedule = yaml.safe_load((BOOK2_ROOT / "curriculum/course-schedule.yaml").read_text())
    assert schedule["total_book_weeks"] == 12
    assert schedule["total_minutes"] == 3320
    assert schedule["final_assessment"]["after_book_week"] == 12
    weeks = schedule["weeks"][6:]
    assert [row["book_week"] for row in weeks] == list(range(7, 13))
    assert [row["global_week"] for row in weeks] == list(range(47, 53))
    assert [sum(item["minutes"] for item in row["allocations"]) for row in weeks] == [255, 275, 420, 270, 380, 60]
