import re
from pathlib import Path

import pytest

from tools.model import (
    load_blueprint,
    load_mock_manifests,
    load_syllabus,
    load_unit_manifests,
)

ROOT = Path(__file__).resolve().parents[1]


def test_load_syllabus_real_repo():
    syllabus = load_syllabus(ROOT)
    taught = [concept for unit in syllabus.units.values() for concept in unit.teaches]
    assert len(syllabus.units) >= 16
    assert len(syllabus.concepts) >= 100
    assert len(taught) == len(set(taught))
    assert set(taught) == set(syllabus.concepts)
    assert set(syllabus.concepts.values()) <= syllabus.clusters


def test_sentinel_must_be_unique(tmp_path):
    (tmp_path / "syllabus.md").write_text(
        "<!-- syllabus-canonical -->\n```yaml\nbaseline: {}\n```\n<!-- syllabus-canonical -->\n"
    )
    with pytest.raises(ValueError, match="exactly once"):
        load_syllabus(tmp_path)


def test_load_blueprint_real_repo():
    blueprint = load_blueprint(ROOT)
    assert sum(row["target"] for row in blueprint.topic_distribution.values()) == blueprint.total_points


def test_missing_dirs_yield_empty_lists(tmp_path):
    assert load_unit_manifests(tmp_path) == []
    assert load_mock_manifests(tmp_path) == []


def test_unit_manifest_roundtrip(tmp_path):
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F1-scientific-python
concepts_taught: [numpy-arrays]
concepts_used: [variables-and-types]
prereq_units: []
practice:
  - id: F1-p01
    concepts: [numpy-arrays]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
"""
    )
    manifests = load_unit_manifests(tmp_path)
    assert manifests[0].unit_id == "F1-scientific-python"
    assert manifests[0].lesson_sessions is None
    assert manifests[0].practice[0].solution_path == "practice/p01_solution.ipynb"


def test_unit_manifest_parses_lesson_sessions(tmp_path):
    unit_dir = tmp_path / "units" / "F6-svd-spectral"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F6-svd-spectral
concepts_taught: []
concepts_used: []
prereq_units: []
estimated_minutes:
  lesson: 425
  lesson_sessions: [85, 85, 85, 85, 85]
practice: []
"""
    )

    manifests = load_unit_manifests(tmp_path)

    assert manifests[0].lesson_sessions == [85, 85, 85, 85, 85]


@pytest.mark.parametrize("yaml_value", ["85", "[85]", "null"])
def test_unit_manifest_rejects_non_mapping_estimated_minutes(tmp_path, yaml_value):
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    unit_dir.mkdir(parents=True)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_path.write_text(
        f"""
unit: F1-scientific-python
concepts_taught: []
concepts_used: []
prereq_units: []
estimated_minutes: {yaml_value}
practice: []
"""
    )

    message = rf"{re.escape(str(manifest_path))}: estimated_minutes must be a mapping when present"
    with pytest.raises(ValueError, match=message):
        load_unit_manifests(tmp_path)


@pytest.mark.parametrize(
    ("yaml_value", "detail"),
    [
        ("85", "must be a list"),
        ("true", "must be a list"),
        ("[true, 85]", "item 0 must be an integer"),
        ("[85, 42.5]", "item 1 must be an integer"),
        ("[85, 0]", "item 1 must be positive"),
        ("[-1, 85]", "item 0 must be positive"),
    ],
)
def test_unit_manifest_rejects_malformed_lesson_sessions(
    tmp_path, yaml_value, detail
):
    unit_dir = tmp_path / "units" / "F6-svd-spectral"
    unit_dir.mkdir(parents=True)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_path.write_text(
        f"""
unit: F6-svd-spectral
concepts_taught: []
concepts_used: []
prereq_units: []
estimated_minutes:
  lesson_sessions: {yaml_value}
practice: []
"""
    )

    message = rf"{re.escape(str(manifest_path))}: estimated_minutes\.lesson_sessions {detail}"
    with pytest.raises(ValueError, match=message):
        load_unit_manifests(tmp_path)
