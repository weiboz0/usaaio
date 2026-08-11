from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from tools.checks.schedule import check_schedule, load_validated_schedule

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"


def test_registered_book2_schedule_is_exact_planned_empty_skeleton() -> None:
    raw = yaml.safe_load(
        (BOOK2_ROOT / "curriculum" / "course-schedule.yaml").read_text(encoding="utf-8")
    )

    assert raw == {
        "schedule_version": 1,
        "book": 2,
        "status": "planned",
        "weeks": [],
    }
    report = check_schedule(BOOK2_ROOT)
    assert report.ok, report.errors
    assert load_validated_schedule(BOOK2_ROOT).weeks == []


def test_planned_book2_schedule_rejects_nonempty_weeks(tmp_path: Path) -> None:
    shutil.copytree(BOOK2_ROOT, tmp_path / "book2")
    selected = tmp_path / "book2"
    path = selected / "curriculum" / "course-schedule.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["weeks"] = [{"book_week": 1, "allocations": []}]
    path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")

    report = check_schedule(selected)

    assert not report.ok
    assert any("exact empty skeleton" in error for error in report.errors)


def test_planned_book2_schedule_rejects_first_live_manifest(tmp_path: Path) -> None:
    shutil.copytree(BOOK2_ROOT, tmp_path / "book2")
    selected = tmp_path / "book2"
    manifest = selected / "units" / "B2-019-attention-transformers" / "manifest.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("unit: B2-019-attention-transformers\n", encoding="utf-8")

    report = check_schedule(selected)

    assert not report.ok
    assert any("forbidden once a live manifest exists" in error for error in report.errors)
