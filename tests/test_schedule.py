from __future__ import annotations

import importlib
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).parents[1]


def _schedule_checker():
    try:
        return importlib.import_module("tools.checks.schedule")
    except ModuleNotFoundError:
        pytest.fail("tools.checks.schedule must provide the canonical schedule checker")


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def _build_schedule_fixture(root: Path) -> dict[str, Any]:
    units = []
    weeks = []
    for week in range(1, 36):
        unit_id = f"U{week:02}"
        previous = [] if week == 1 else [f"U{week - 1:02}"]
        units.append(
            {
                "id": unit_id,
                "track": "core",
                "title": unit_id,
                "prereqs": previous,
                "teaches": [f"concept-{week:02}"],
            }
        )
        final_week = week == 35
        lesson, practice, review = (100, 100, 10) if final_week else (100, 300, 50)
        _write_yaml(
            root / "units" / unit_id / "manifest.yaml",
            {
                "unit": unit_id,
                "concepts_taught": [f"concept-{week:02}"],
                "concepts_used": [],
                "prereq_units": previous,
                "estimated_minutes": {
                    "lesson": lesson,
                    "lesson_sessions": [lesson],
                    "practice": practice,
                    "review": review,
                },
                "practice": [],
            },
        )
        allocations = [
            {
                "kind": "lesson-session",
                "unit": unit_id,
                "session": 1,
                "minutes": lesson,
            },
            {
                "kind": "practice",
                "unit": unit_id,
                "chunk": 1,
                "minutes": practice,
            },
            {
                "kind": "review",
                "unit": unit_id,
                "chunk": 1,
                "minutes": review,
            },
        ]
        if final_week:
            allocations.extend(
                [
                    {"kind": "mock", "test": "r1-001", "minutes": 180},
                    {"kind": "debrief", "test": "r1-001", "minutes": 60},
                ]
            )
        weeks.append(
            {
                "week": week,
                "semester": 1 if week <= 16 else 2,
                "allocations": allocations,
            }
        )

    concepts = [{"id": f"concept-{week:02}", "cluster": "fixture"} for week in range(1, 36)]
    root.joinpath("syllabus.md").write_text(
        "# Fixture syllabus\n\n<!-- syllabus-canonical -->\n```yaml\n"
        + yaml.safe_dump(
            {
                "baseline": {"mathematics": ["arithmetic"]},
                "clusters": ["fixture"],
                "concepts": concepts,
                "units": units,
            },
            sort_keys=False,
        )
        + "```\n"
    )
    _write_yaml(
        root / "mocktests" / "r1-001" / "manifest.yaml",
        {"test": "r1-001", "duration_minutes": 180, "problems": []},
    )
    schedule = {
        "schedule_version": 1,
        "totals": {"semester_1": 7200, "semester_2": 8550, "scheduled": 15750},
        "weeks": weeks,
    }
    _write_yaml(root / "curriculum" / "course-schedule.yaml", schedule)
    return schedule


def _check_after(root: Path, mutate: Callable[[dict[str, Any]], None]):
    schedule = _build_schedule_fixture(root)
    mutate(schedule)
    _write_yaml(root / "curriculum" / "course-schedule.yaml", schedule)
    return _schedule_checker().check_schedule(root)


def _split_allocation(
    schedule: dict[str, Any], *, index: int, week_index: int = 0
) -> None:
    allocation = schedule["weeks"][week_index]["allocations"][index]
    original_minutes = allocation["minutes"]
    allocation["minutes"] = original_minutes // 2
    schedule["weeks"][week_index]["allocations"].insert(
        index + 1,
        {**allocation, "minutes": original_minutes - allocation["minutes"]}
    )


def _duplicate_allocation(
    schedule: dict[str, Any], *, index: int, week_index: int = 0
) -> None:
    schedule["weeks"][week_index]["allocations"].insert(
        index + 1,
        dict(schedule["weeks"][week_index]["allocations"][index])
    )


def _swap_first_two_weeks(schedule: dict[str, Any]) -> None:
    first = schedule["weeks"][0]["allocations"]
    second = schedule["weeks"][1]["allocations"]
    schedule["weeks"][0]["allocations"] = second
    schedule["weeks"][1]["allocations"] = first


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda schedule: schedule["weeks"][0]["allocations"].pop(0),
            "unallocated lesson session U01#1",
        ),
        (
            lambda schedule: schedule["weeks"][0]["allocations"].append(
                dict(schedule["weeks"][0]["allocations"][0])
            ),
            "duplicate lesson session U01#1",
        ),
        (
            lambda schedule: _split_allocation(schedule, index=0),
            "lesson session U01#1 must appear exactly once",
        ),
        (
            lambda schedule: schedule["weeks"][0]["allocations"][0].update(unit="unknown-unit"),
            "unknown unit unknown-unit",
        ),
        (
            lambda schedule: schedule["weeks"][0]["allocations"][0].update(
                kind="self-study"
            ),
            "week 1 allocation 0 has unknown kind self-study",
        ),
        (
            lambda schedule: _duplicate_allocation(schedule, index=1),
            "duplicate practice chunk U01#1",
        ),
        (
            lambda schedule: _split_allocation(schedule, index=1),
            "duplicate practice chunk U01#1",
        ),
        (
            lambda schedule: _duplicate_allocation(schedule, index=2),
            "duplicate review chunk U01#1",
        ),
        (
            lambda schedule: _split_allocation(schedule, index=2),
            "duplicate review chunk U01#1",
        ),
        (
            lambda schedule: schedule["weeks"][0]["allocations"][1].update(minutes=299),
            "U01 practice minutes",
        ),
        (
            lambda schedule: schedule["weeks"][0]["allocations"][2].update(minutes=49),
            "U01 review minutes",
        ),
        (
            lambda schedule: schedule["weeks"][1].update(week=1),
            "duplicate week 1",
        ),
        (
            _swap_first_two_weeks,
            "prerequisite U01 must complete before U02 starts",
        ),
        (
            lambda schedule: schedule["weeks"][0].update(week="one"),
            "week row 0 week must be an integer",
        ),
        (
            lambda schedule: schedule["weeks"].pop(9),
            "missing week 10",
        ),
        (
            lambda schedule: schedule["weeks"][0]["allocations"][1].update(minutes=299),
            "week 1 totals 449 minutes; requires 450-500",
        ),
        (
            lambda schedule: schedule["weeks"][34]["allocations"].insert(
                0, schedule["weeks"][34]["allocations"].pop(-2)
            ),
            "mock and debrief must be the final scheduled events",
        ),
        (
            lambda schedule: schedule["weeks"][34]["allocations"][3].update(
                test="r1-999"
            ),
            "mock allocation references unknown test r1-999",
        ),
        (
            lambda schedule: schedule["weeks"][34]["allocations"][4].update(
                test="r1-999"
            ),
            "debrief allocation references unknown test r1-999",
        ),
        (
            lambda schedule: schedule["weeks"][34]["allocations"][3].update(
                minutes=179
            ),
            "mock allocation for r1-001 must match duration 180 minutes",
        ),
        (
            lambda schedule: schedule["weeks"][34]["allocations"][4].update(
                minutes=59
            ),
            "debrief allocation for r1-001 must be 60 minutes",
        ),
        (
            lambda schedule: _duplicate_allocation(
                schedule, index=3, week_index=34
            ),
            "mock allocation for r1-001 must appear exactly once",
        ),
        (
            lambda schedule: _split_allocation(schedule, index=3, week_index=34),
            "mock allocation for r1-001 must appear exactly once",
        ),
        (
            lambda schedule: _duplicate_allocation(
                schedule, index=4, week_index=34
            ),
            "debrief allocation for r1-001 must appear exactly once",
        ),
        (
            lambda schedule: _split_allocation(schedule, index=4, week_index=34),
            "debrief allocation for r1-001 must appear exactly once",
        ),
    ],
)
def test_schedule_checker_fails_closed_on_allocation_contracts(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    report = _check_after(tmp_path, mutate)

    assert not report.ok
    assert any(message in error for error in report.errors), report.errors


def test_schedule_checker_accepts_a_fully_allocated_prerequisite_valid_fixture(
    tmp_path: Path,
) -> None:
    _build_schedule_fixture(tmp_path)

    report = _schedule_checker().check_schedule(tmp_path)

    assert report.ok, report.errors


def test_schedule_checker_accepts_consecutive_multiweek_practice_chunks(
    tmp_path: Path,
) -> None:
    schedule = _build_schedule_fixture(tmp_path)
    first = schedule["weeks"][0]["allocations"][1]
    first["minutes"] = 150
    schedule["weeks"][0]["allocations"].append(
        {"kind": "practice", "unit": "U01", "chunk": 2, "minutes": 150}
    )
    schedule["weeks"][0]["allocations"][2]["minutes"] = 50
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert report.ok, report.errors


@pytest.mark.parametrize(
    ("chunk", "message"),
    [
        (1, "duplicate practice chunk U01#1"),
        (3, "practice chunks for U01 must be consecutive 1..2"),
    ],
)
def test_schedule_checker_rejects_duplicate_or_gapped_practice_chunks(
    tmp_path: Path, chunk: int, message: str
) -> None:
    schedule = _build_schedule_fixture(tmp_path)
    schedule["weeks"][0]["allocations"][1]["minutes"] = 150
    schedule["weeks"][0]["allocations"].append(
        {"kind": "practice", "unit": "U01", "chunk": chunk, "minutes": 150}
    )
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(message in error for error in report.errors), report.errors


def _rendered_first_instruction_pairs(document: str) -> list[tuple[str, int]]:
    match = re.search(
        r"<!-- BEGIN GENERATED: first-instruction -->\n(.*?)"
        r"<!-- END GENERATED: first-instruction -->",
        document,
        re.DOTALL,
    )
    assert match is not None, "missing generated first-instruction region"
    return [
        (unit, int(week))
        for unit, week in re.findall(
            r"^\| ([A-Z]\d+[^ |]*) \| Week (\d+) \|$", match.group(1), re.MULTILINE
        )
    ]


def test_real_schedule_has_exact_plan017_calendar_and_complete_allocation() -> None:
    report = _schedule_checker().check_schedule(ROOT)
    assert report.ok, report.errors

    schedule = yaml.safe_load((ROOT / "curriculum" / "course-schedule.yaml").read_text())
    weeks = schedule["weeks"]
    assert len(weeks) == 35
    assert [week["week"] for week in weeks] == list(range(1, 36))
    assert [week["semester"] for week in weeks] == [1] * 16 + [2] * 19
    totals = [sum(allocation["minutes"] for allocation in week["allocations"]) for week in weeks]
    assert all(450 <= total <= 500 for total in totals)
    assert sum(totals[:16]) == 7915
    assert sum(totals[16:]) == 8950
    assert sum(totals) == 16865

    manifested = sum(
        allocation["minutes"]
        for week in weeks
        for allocation in week["allocations"]
        if allocation["kind"] in {"lesson-session", "practice", "review"}
    )
    assert manifested == 16625

    c11_weeks = [
        week["week"]
        for week in weeks
        for allocation in week["allocations"]
        if allocation.get("unit") == "C11-neural-training"
    ]
    c7_weeks = [
        week["week"]
        for week in weeks
        for allocation in week["allocations"]
        if allocation.get("unit") == "C7-cnn-transfer"
    ]
    assert c11_weeks and c7_weeks
    assert max(c11_weeks) < min(c7_weeks)
    assert [row["kind"] for row in weeks[-1]["allocations"][-2:]] == ["mock", "debrief"]
    assert weeks[-1]["allocations"][-2]["test"] == "r1-001"
    assert weeks[-1]["allocations"][-2]["minutes"] == 180
    assert weeks[-1]["allocations"][-1]["minutes"] == 60


def test_rendered_first_instruction_region_exactly_matches_the_schedule_source() -> None:
    schedule = yaml.safe_load((ROOT / "curriculum" / "course-schedule.yaml").read_text())
    first_week: dict[str, int] = {}
    for week in schedule["weeks"]:
        for allocation in week["allocations"]:
            if allocation["kind"] == "lesson-session":
                first_week.setdefault(allocation["unit"], week["week"])
    expected = list(first_week.items())

    document = (ROOT / "docs" / "course-structure.md").read_text()
    actual = _rendered_first_instruction_pairs(document)

    assert actual == expected
    positions = {unit: index for index, (unit, _) in enumerate(actual)}
    assert positions["C5-neural-networks"] < positions["C6-pytorch"]
    assert positions["C6-pytorch"] < positions["C11-neural-training"]
    assert positions["C11-neural-training"] < positions["C7-cnn-transfer"]
