from __future__ import annotations

import importlib.util
import json
from collections import Counter
from datetime import date
from pathlib import Path

import nbformat
import pytest
import yaml

from tools.checks.hygiene import check_hygiene
from tools.model import load_syllabus, load_unit_manifests

ROOT = Path(__file__).resolve().parents[1]
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


def test_manifest_publishes_exact_statement_ledger_and_deferred_debt() -> None:
    raw = _manifest()
    parsed = {
        item.unit_id: item
        for item in load_unit_manifests(BOOK2_ROOT, as_of_date=date(2026, 9, 30))
    }[UNIT_ID]

    assert raw["solution_policy"] == {
        "status": "deferred",
        "plan": "plan-020",
        "expires": "2026-09-30",
    }
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
    assert not list(UNIT.glob("practice/*_solution.ipynb"))


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
        assert "Common pitfalls" in source
        assert "Exam connections" in source
        assert "Going deeper" in source
        for needle in needles:
            assert needle.lower() in source.lower()


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
