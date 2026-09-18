from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from tools.model import load_roadmap, load_syllabus

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
OWNED_CONCEPTS = [
    "vision-transformers",
    "object-detection",
    "unet",
    "graph-neural-network-transformer-applications",
]
EXPECTED_MODALITIES = {"theory", "implementation", "model-training"}


def _coverage_map() -> dict[str, Any]:
    raw = yaml.safe_load(
        (BOOK2_ROOT / "curriculum" / "coverage-map.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(raw, dict)
    return raw


def test_b2_021_planned_unit_has_exact_registration_contract() -> None:
    raw = _coverage_map()
    matches = [row for row in raw["planned_units"] if row["id"] == UNIT_ID]

    assert len(matches) == 1
    planned = matches[0]
    assert planned["prerequisites"] == PREREQUISITES
    assert planned["provisional_concepts"] == OWNED_CONCEPTS
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
    assert loaded.provisional_concepts == OWNED_CONCEPTS
    assert (loaded.estimated_hours.minimum, loaded.estimated_hours.maximum) == (
        22,
        28,
    )


def test_b2_021_coverage_stays_missing_until_live_sources_exist() -> None:
    raw = _coverage_map()
    rows = {row["id"]: row for row in raw["knowledge_points"]}

    for concept in OWNED_CONCEPTS:
        row = rows[concept]
        assert row["coverage"] == "missing"
        assert row["destination"] == UNIT_ID
        assert row["shipped_concepts"] == []
        assert row["deficits"] == {
            "modalities_missing": ["theory", "implementation", "model-training"]
        }
        assert set(row["evidence_by_modality"]) == EXPECTED_MODALITIES
        assert all(
            evidence
            == {
                "lesson_anchors": [],
                "practices": [],
                "assessments": [],
            }
            for evidence in row["evidence_by_modality"].values()
        )

    assert UNIT_ID not in load_syllabus(BOOK2_ROOT).units
    assert not (BOOK2_ROOT / "units" / UNIT_ID).exists()
    assert UNIT_ID not in (BOOK2_ROOT / "curriculum" / "course-schedule.yaml").read_text(
        encoding="utf-8"
    )
    assert "B2-021" not in (ROOT / "docs" / "unit-standards.md").read_text(encoding="utf-8")
