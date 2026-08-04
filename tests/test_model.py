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
    assert manifests[0].practice[0].solution_path == "practice/p01_solution.ipynb"
