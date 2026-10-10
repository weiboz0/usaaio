"""Plan 024 Task 1: zero-choice Book 2 mock-test instantiation from the live blueprint."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from tools.checks.blueprint import check_blueprint
from tools.checks.new_mocktest import DIFFICULTY_DRAW, scaffold_mocktest
from tools.model import load_mock_manifests

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"


def seed_book2(root: Path) -> None:
    (root / "mocktests").mkdir()
    shutil.copyfile(BOOK2_ROOT / "mocktests" / "blueprint.yaml", root / "mocktests" / "blueprint.yaml")
    shutil.copyfile(BOOK2_ROOT / "syllabus.md", root / "syllabus.md")


def test_book2_scaffold_uses_flat_layout_and_default_anchors(tmp_path):
    seed_book2(tmp_path)
    test_dir = scaffold_mocktest(tmp_path, "r2-001", "2026-10-10", book_number=2)
    assert test_dir == tmp_path / "mocktests" / "r2-001"
    for child in ("theory", "problems", "solutions", "data"):
        assert (test_dir / child).is_dir()
    assert not (test_dir / "day1").exists() and not (test_dir / "day2").exists()
    assert (test_dir / "rubric.md").is_file()
    front = (test_dir / "test.md").read_text()
    assert "test: r2-001\n" in front
    assert "days: 2\n" in front
    assert "day_duration_minutes: 240\n" in front
    assert "total_points: 300\n" in front

    raw = yaml.safe_load((test_dir / "manifest.yaml").read_text())
    assert raw["status"] == "draft"
    assert raw["blueprint_version"] == 1
    assert raw["generated"] == "2026-10-10"
    assert raw["day_duration_minutes"] == 240
    assert raw["total_points"] == 300
    assert "duration_minutes" not in raw
    assert raw["time_budget"] == {1: {"d1-arc": 120, "d1-open": 120}, 2: {"d2-arc": 80, "d2-open": 160}}
    assert raw["generation_parameters"] == {
        "rotation_index": 0,
        "section_points": {"d1-arc": 90, "d1-open": 70, "d2-arc": 50, "d2-open": [40, 50]},
        "arc_clusters": {
            "d1": ["attention-transformers", "language-transformers"],
            "d2": ["probabilistic-latent-models"],
        },
        "problem_count": 5,
        "difficulty_draw": {"intro": 0.2, "core": 0.45, "advanced": 0.35},
    }
    assert raw["problems"] == []

    manifest = load_mock_manifests(tmp_path, book_number=2)[0]
    assert manifest.day_duration_minutes == 240
    assert all(sum(day.values()) == 240 for day in manifest.day_time_budget.values())


@pytest.mark.parametrize(
    ("test_id", "index", "d1", "d2"),
    [
        ("r2-002", 1, ["cross-modal-vision", "attention-transformers"], ["generative-models"]),
        ("r2-003", 2, ["language-transformers", "attention-transformers"],
         ["probabilistic-latent-models", "generative-models"]),
        ("r2-004", 0, ["attention-transformers", "language-transformers"],
         ["probabilistic-latent-models"]),
    ],
)
def test_book2_arc_rotation_is_zero_choice(tmp_path, test_id, index, d1, d2):
    seed_book2(tmp_path)
    test_dir = scaffold_mocktest(tmp_path, test_id, "2026-10-10", book_number=2)
    raw = yaml.safe_load((test_dir / "manifest.yaml").read_text())
    assert raw["generation_parameters"]["rotation_index"] == index
    assert raw["generation_parameters"]["arc_clusters"] == {"d1": d1, "d2": d2}


def test_book2_scaffold_is_a_loudly_skipped_draft(tmp_path):
    seed_book2(tmp_path)
    scaffold_mocktest(tmp_path, "r2-001", "2026-10-10", book_number=2)
    report = check_blueprint(tmp_path)
    assert report.skipped
    assert any("DRAFT manifest" in warning for warning in report.warnings)


def test_book2_scaffold_rejects_r1_ids_and_overwrite(tmp_path):
    seed_book2(tmp_path)
    with pytest.raises(ValueError, match="test id must match r2-NNN"):
        scaffold_mocktest(tmp_path, "r1-001", "2026-10-10", book_number=2)
    scaffold_mocktest(tmp_path, "r2-001", "2026-10-10", book_number=2)
    with pytest.raises(FileExistsError):
        scaffold_mocktest(tmp_path, "r2-001", "2026-10-10", book_number=2)


def test_book1_difficulty_constant_is_unchanged():
    assert DIFFICULTY_DRAW == {"intro": 0.23, "core": 0.45, "advanced": 0.32}
