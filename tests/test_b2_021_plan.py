from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from tools.model import load_roadmap, load_syllabus, load_syllabus_contract

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"
UNIT_ID = "B2-021-cross-modal-transformers-vision"
PREREQUISITES = [
    "book1:F1-scientific-python",
    "book1:F3-matrices",
    "book1:C6-pytorch",
    "book1:C7-cnn-transfer",
    "book1:C11-neural-training",
    "B2-019-attention-transformers",
    "B2-020-language-transformers",
]
CONCEPT_PREREQUISITES = [
    "attention-mask",
    "query-key-value-attention",
    "multi-head-attention",
    "attention-complexity",
    "transformer-block",
    "book1:numpy-arrays",
    "book1:broadcasting",
    "book1:aggregation-axis",
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
    "book1:convolution",
    "book1:feature-maps",
    "book1:cnn-training",
]
OWNED_CONCEPTS = [
    "vision-transformers",
    "object-detection",
    "unet",
    "graph-neural-network-transformer-applications",
]
CONCEPT_SESSIONS = dict(zip(OWNED_CONCEPTS, (1, 2, 3, 4), strict=True))
EXPECTED_MODALITIES = {"theory", "implementation", "model-training"}


def _coverage_map() -> dict[str, Any]:
    raw = yaml.safe_load(
        (BOOK2_ROOT / "curriculum" / "coverage-map.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(raw, dict)
    return raw


def test_b2_021_planned_row_is_retained_but_no_longer_provisional() -> None:
    raw = _coverage_map()
    matches = [row for row in raw["planned_units"] if row["id"] == UNIT_ID]

    assert len(matches) == 1
    planned = matches[0]
    assert planned["prerequisites"] == PREREQUISITES
    assert planned["provisional_concepts"] == []
    assert planned["knowledge_points"] == [
        "vision-transformers",
        "graph-neural-network-transformer-applications",
        "object-detection",
        "unet",
    ]
    assert planned["estimated_hours"] == {"min": 22, "max": 28}
    assert planned["schedule_action"] == "extend"

    loaded = next(unit for unit in load_roadmap(BOOK2_ROOT).planned_units if unit.id == UNIT_ID)
    assert loaded.prerequisites == PREREQUISITES
    assert loaded.provisional_concepts == []


def test_b2_021_syllabus_registers_exact_live_owner_and_import_contract() -> None:
    syllabus = load_syllabus(BOOK2_ROOT)
    unit = syllabus.units[UNIT_ID]

    assert unit.prereqs == PREREQUISITES
    assert unit.concept_prerequisites == CONCEPT_PREREQUISITES
    assert unit.teaches == OWNED_CONCEPTS
    assert unit.length == "double"
    contract = load_syllabus_contract(BOOK2_ROOT)
    assert {"convolution", "feature-maps", "cnn-training"} <= set(
        contract["imports"]["concepts"]
    )
    assert {concept: syllabus.concepts[concept] for concept in OWNED_CONCEPTS} == {
        concept: "cross-modal-vision" for concept in OWNED_CONCEPTS
    }


def test_b2_021_promotes_exact_four_coverage_rows_with_live_primary_evidence() -> None:
    raw = _coverage_map()
    rows = {row["id"]: row for row in raw["knowledge_points"]}

    for concept in OWNED_CONCEPTS:
        row = rows[concept]
        assert row["coverage"] == "covered"
        assert row["destination"] == UNIT_ID
        assert row["shipped_concepts"] == [concept]
        assert row["deficits"] == {"modalities_missing": []}
        assert set(row["evidence_by_modality"]) == EXPECTED_MODALITIES
        for evidence in row["evidence_by_modality"].values():
            assert evidence["lesson_anchors"]
            assert evidence["practices"]
            assert all(item["role"] == "primary" for item in evidence["lesson_anchors"])
            assert all(item["role"] == "primary" for item in evidence["practices"])
            assert all(
                item["path"].startswith(f"units/{UNIT_ID}/lessons/")
                for item in evidence["lesson_anchors"]
            )
    assert (BOOK2_ROOT / "units" / UNIT_ID / "manifest.yaml").is_file()


def test_b2_021_manifest_concept_sessions_match_live_ownership() -> None:
    manifest = yaml.safe_load(
        (BOOK2_ROOT / "units" / UNIT_ID / "manifest.yaml").read_text(encoding="utf-8")
    )
    assert manifest["concepts_taught"] == OWNED_CONCEPTS
    assert manifest["concept_sessions"] == CONCEPT_SESSIONS
    assert manifest["concept_prerequisites"] == CONCEPT_PREREQUISITES
