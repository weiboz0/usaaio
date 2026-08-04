from pathlib import Path

import pytest

from tools.checks.blueprint import check_blueprint
from tools.checks.new_mocktest import scaffold_mocktest
from tools.model import load_mock_manifests

ROOT = Path(__file__).resolve().parents[1]


def seed_repo(root: Path) -> None:
    (root / "mocktests").mkdir()
    (root / "mocktests" / "blueprint.yaml").write_text((ROOT / "mocktests/blueprint.yaml").read_text())
    (root / "syllabus.md").write_text((ROOT / "syllabus.md").read_text())


def test_new_mocktest_scaffolds_defaults(tmp_path):
    seed_repo(tmp_path)
    test_dir = scaffold_mocktest(tmp_path, "r1-002", "2026-08-15")
    manifest = load_mock_manifests(tmp_path)[0]
    assert test_dir.joinpath("theory").is_dir()
    assert test_dir.joinpath("problems").is_dir()
    assert test_dir.joinpath("solutions").is_dir()
    assert test_dir.joinpath("data").is_dir()
    assert test_dir.joinpath("test.md").exists()
    assert test_dir.joinpath("rubric.md").exists()
    assert manifest.status == "draft"
    assert manifest.generated == "2026-08-15"
    assert manifest.generation_parameters["arc_clusters"] == ["cnn-vision", "pytorch", "numpy"]
    assert manifest.problems == []


def test_new_mocktest_rotation_wraps(tmp_path):
    seed_repo(tmp_path)
    scaffold_mocktest(tmp_path, "r1-004", "2026-08-15")
    manifest = load_mock_manifests(tmp_path)[0]
    assert manifest.generation_parameters["arc_clusters"] == [
        "nlp-embeddings",
        "linear-algebra",
        "numpy",
    ]


def test_new_mocktest_refuses_overwrite(tmp_path):
    seed_repo(tmp_path)
    scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")
    with pytest.raises(FileExistsError):
        scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")


def test_draft_manifest_loud_skipped_by_blueprint_check(tmp_path):
    seed_repo(tmp_path)
    scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")
    report = check_blueprint(tmp_path)
    assert report.skipped
    assert any("DRAFT manifest" in warning for warning in report.warnings)


def test_absent_status_treated_as_final(tmp_path):
    seed_repo(tmp_path)
    scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")
    path = tmp_path / "mocktests" / "r1-001" / "manifest.yaml"
    path.write_text(path.read_text().replace("status: draft\n", ""))
    report = check_blueprint(tmp_path)
    assert report.skipped is None
    assert not report.ok
    assert any("points sum" in error for error in report.errors)


def test_scaffold_time_budget_sums_to_duration(tmp_path):
    seed_repo(tmp_path)
    scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")
    manifest = load_mock_manifests(tmp_path)[0]
    assert sum(manifest.time_budget.values()) == manifest.duration_minutes == 180
