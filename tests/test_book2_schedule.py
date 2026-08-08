from __future__ import annotations

import importlib
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools import render_course_structure as course_renderer

ROOT = Path(__file__).parents[1]


UNIT = "B2-019-attention-transformers"
PRACTICE_MINUTES = [
    20, 20, 20, 20, 20,
    50, 50, 50, 50, 50, 50, 50,
    45, 45, 45, 45,
    65, 65, 65, 65, 65,
    55, 55, 55,
]
PRACTICE_CHUNKS = [
    [1, 2, 6, 13],
    [3, 4, 7, 8, 14],
    [5, 9, 10, 15, 16, 21, 23],
    [11, 17, 18, 22],
    [12, 19, 20, 24],
]


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def _book2_checker():
    try:
        return importlib.import_module("tools.checks.book2_schedule")
    except ModuleNotFoundError as exc:
        if exc.name != "tools.checks.book2_schedule":
            raise
        pytest.fail("tools.checks.book2_schedule must validate the independent Book 2 route")


def _book2_renderer():
    try:
        return importlib.import_module("tools.render_book2_structure")
    except ModuleNotFoundError as exc:
        if exc.name != "tools.render_book2_structure":
            raise
        pytest.fail("tools.render_book2_structure must render Book 2 independently")


def _build_book2_schedule_fixture(root: Path) -> dict[str, Any]:
    unit_dir = root / "units" / UNIT
    unit_dir.mkdir(parents=True)
    practice = []
    for number, minutes in enumerate(PRACTICE_MINUTES, start=1):
        row = {
            "id": f"B2-019-p{number:02}",
            "concepts": ["attention"],
            "path": f"practice/p{number:02}.ipynb",
            "solution_path": f"practice/p{number:02}_solution.ipynb",
            "minutes": minutes,
            "compute": {"policy": "cpu", "seed": 20260808},
        }
        practice.append(row)
        for field in ("path", "solution_path"):
            path = unit_dir / row[field]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}")
    bridge = unit_dir / "lessons" / "00-book1-bridge.ipynb"
    bridge.parent.mkdir(parents=True)
    bridge.write_text("{}")
    _write_yaml(
        unit_dir / "manifest.yaml",
        {
            "unit": UNIT,
            "book": 2,
            "layer": "round-2-extension",
            "round": 2,
            "track": "extension",
            "concepts_taught": ["attention"],
            "concepts_used": ["softmax"],
            "concept_prerequisites": ["softmax"],
            "prereq_units": ["C11-neural-training"],
            "bridge_diagnostic": {
                "path": "lessons/00-book1-bridge.ipynb",
                "minutes": 30,
                "referenced_concepts": ["softmax"],
            },
            "estimated_minutes": {
                "lesson_sessions": [90, 90, 90, 90, 90],
                "practice": 1120,
                "review": 60,
            },
            "coverage_claims": [],
            "practice": practice,
        },
    )

    weeks = []
    for index, chunk in enumerate(PRACTICE_CHUNKS, start=1):
        allocations = []
        if index == 1:
            allocations.append(
                {"kind": "bridge-diagnostic", "unit": UNIT, "minutes": 30}
            )
        allocations.extend(
            [
                {
                    "kind": "lesson-session",
                    "unit": UNIT,
                    "session": index,
                    "minutes": 90,
                },
                {
                    "kind": "practice",
                    "unit": UNIT,
                    "chunk": index,
                    "minutes": sum(PRACTICE_MINUTES[number - 1] for number in chunk),
                    "problem_ids": [f"B2-019-p{number:02}" for number in chunk],
                },
            ]
        )
        weeks.append(
            {"book_week": index, "global_week": 40 + index, "allocations": allocations}
        )
    weeks.append(
        {
            "book_week": 6,
            "global_week": 46,
            "allocations": [{"kind": "review", "unit": UNIT, "minutes": 60}],
        }
    )
    schedule = {
        "schedule_version": 1,
        "book": 2,
        "starts_after_global_week": 40,
        "total_book_weeks": 6,
        "total_minutes": 1660,
        "final_assessment": {
            "kind": "future-r2-mock",
            "status": "planned",
            "after_book_week": 6,
        },
        "weeks": weeks,
    }
    _write_yaml(root / "curriculum" / "book2-schedule.yaml", schedule)
    return schedule


def test_valid_book2_schedule_has_independent_numbering_and_exact_ledger(
    tmp_path: Path,
) -> None:
    _build_book2_schedule_fixture(tmp_path)

    report = _book2_checker().check_book2_schedule(tmp_path)
    schedule = _book2_checker().load_validated_book2_schedule(tmp_path)

    assert report.ok, report.errors
    assert schedule.starts_after_global_week == 40
    assert schedule.total_book_weeks == 6
    assert [week.book_week for week in schedule.weeks] == list(range(1, 7))
    assert [week.global_week for week in schedule.weeks] == list(range(41, 47))
    assert schedule.total_minutes == 1660
    assert schedule.final_assessment.kind == "future-r2-mock"
    assert schedule.final_assessment.status == "planned"
    assert schedule.final_assessment.after_book_week == 6


def _mutate_stale_after_book_week(root: Path, schedule: dict[str, Any]) -> None:
    unit = "B2-020-language-transformers"
    unit_dir = root / "units" / unit
    unit_dir.mkdir(parents=True)
    for relative in ("practice/p01.ipynb", "practice/p01_solution.ipynb"):
        path = unit_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    _write_yaml(
        unit_dir / "manifest.yaml",
        {
            "unit": unit,
            "book": 2,
            "layer": "round-2-extension",
            "round": 2,
            "track": "extension",
            "concepts_taught": ["language-transformer-extension"],
            "concepts_used": ["softmax"],
            "concept_prerequisites": ["softmax"],
            "prereq_units": [UNIT],
            "coverage_claims": [],
            "estimated_minutes": {"lesson_sessions": [90], "practice": 20, "review": 60},
            "practice": [
                {
                    "id": "B2-020-p01",
                    "concepts": ["language-transformer-extension"],
                    "path": "practice/p01.ipynb",
                    "solution_path": "practice/p01_solution.ipynb",
                    "minutes": 20,
                    "compute": {"policy": "cpu", "seed": 20260808},
                }
            ],
        },
    )
    schedule.update(total_book_weeks=7, total_minutes=1830)
    schedule["weeks"].append(
        {
            "book_week": 7,
            "global_week": 47,
            "allocations": [
                {"kind": "lesson-session", "unit": unit, "session": 1, "minutes": 90},
                {
                    "kind": "practice",
                    "unit": unit,
                    "chunk": 1,
                    "minutes": 20,
                    "problem_ids": ["B2-020-p01"],
                },
                {"kind": "review", "unit": unit, "minutes": 60},
            ],
        }
    )


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        pytest.param(
            lambda root, schedule: schedule["weeks"][2].update(book_week=4),
            "book_week values must be contiguous 1..6",
            id="noncontiguous-local-weeks",
        ),
        pytest.param(
            lambda root, schedule: schedule["weeks"][2].update(global_week=99),
            "global_week must equal starts_after_global_week + book_week",
            id="wrong-global-offset",
        ),
        pytest.param(
            lambda root, schedule: schedule.update(starts_after_global_week=39),
            "starts_after_global_week must be 40",
            id="not-after-book1-week-40",
        ),
        pytest.param(
            lambda root, schedule: schedule.pop("final_assessment"),
            "final_assessment is required",
            id="missing-final-assessment-marker",
        ),
        pytest.param(
            lambda root, schedule: schedule["final_assessment"].update(status="final"),
            "final_assessment.status must be planned",
            id="unknown-final-assessment-status",
        ),
        pytest.param(
            _mutate_stale_after_book_week,
            "final_assessment.after_book_week must equal total_book_weeks",
            id="stale-after-book-week-after-extension",
        ),
        pytest.param(
            lambda root, schedule: schedule["weeks"][0]["allocations"][0].update(minutes=29),
            "bridge-diagnostic allocation must match manifest minutes 30",
            id="bridge-diagnostic-reconciliation",
        ),
    ],
)
def test_book2_schedule_rejects_malformed_or_stale_fixtures(
    tmp_path: Path,
    mutate: Callable[[Path, dict[str, Any]], object],
    fragment: str,
) -> None:
    schedule = _build_book2_schedule_fixture(tmp_path)
    mutate(tmp_path, schedule)
    _write_yaml(tmp_path / "curriculum" / "book2-schedule.yaml", schedule)

    report = _book2_checker().check_book2_schedule(tmp_path)

    assert not report.ok
    assert any(fragment in error for error in report.errors), report.errors


def test_book2_renderer_is_separate_and_labels_every_entry_as_round2_extension(
    tmp_path: Path,
) -> None:
    _build_book2_schedule_fixture(tmp_path)
    book1 = tmp_path / "docs" / "course-structure.md"
    book1.parent.mkdir(parents=True)
    book1.write_bytes(b"BOOK 1 BYTES\n")

    rendered = _book2_renderer().render_document(tmp_path)

    assert book1.read_bytes() == b"BOOK 1 BYTES\n"
    assert "Book 2" in rendered
    assert "Round 2 extension" in rendered
    schedule = _book2_checker().load_validated_book2_schedule(tmp_path)
    rendered_entries = [line for line in rendered.splitlines() if UNIT in line]
    assert len(rendered_entries) == len(schedule.weeks)
    assert all("Round 2 extension" in entry for entry in rendered_entries)


def test_valid_book2_fixture_does_not_change_book1_renderer_or_schedule_bytes(
    tmp_path: Path,
) -> None:
    shutil.copy2(ROOT / "syllabus.md", tmp_path / "syllabus.md")
    shutil.copytree(ROOT / "units", tmp_path / "units")
    shutil.copytree(ROOT / "mocktests", tmp_path / "mocktests")
    shutil.copytree(ROOT / "docs", tmp_path / "docs")
    (tmp_path / "curriculum").mkdir()
    shutil.copy2(
        ROOT / "curriculum" / "course-schedule.yaml",
        tmp_path / "curriculum" / "course-schedule.yaml",
    )
    schedule_path = tmp_path / "curriculum" / "course-schedule.yaml"
    source_bytes = schedule_path.read_bytes()
    rendered_before = course_renderer.render_document(tmp_path).encode()

    _build_book2_schedule_fixture(tmp_path)

    rendered_after = course_renderer.render_document(tmp_path).encode()
    assert schedule_path.read_bytes() == source_bytes
    assert rendered_after == rendered_before
