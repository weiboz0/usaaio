from __future__ import annotations

import importlib
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools import render_course_structure as course_renderer
from tools.model import load_unit_manifests

ROOT = Path(__file__).parents[1]
BOOK1_ROOT = ROOT / "book1"


def _schedule_checker():
    try:
        return importlib.import_module("tools.checks.schedule")
    except ModuleNotFoundError:
        pytest.fail("tools.checks.schedule must provide the canonical schedule checker")


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def _build_schedule_fixture(
    root: Path,
    *,
    chained_prerequisites: bool = True,
    week_count: int = 35,
    semester_1_weeks: int = 16,
) -> dict[str, Any]:
    units = []
    weeks = []
    for week in range(1, week_count + 1):
        unit_id = f"U{week:02}"
        previous = (
            []
            if week == 1 or not chained_prerequisites
            else [f"U{week - 1:02}"]
        )
        units.append(
            {
                "id": unit_id,
                "track": "core",
                "title": unit_id,
                "prereqs": previous,
                "teaches": [f"concept-{week:02}"],
            }
        )
        final_week = week == week_count
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
                "semester": 1 if week <= semester_1_weeks else 2,
                "allocations": allocations,
            }
        )

    concepts = [
        {"id": f"concept-{week:02}", "cluster": "fixture"}
        for week in range(1, week_count + 1)
    ]
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
        "calendar": {
            "semester_1_weeks": semester_1_weeks,
            "semester_2_weeks": week_count - semester_1_weeks,
            "total_weeks": week_count,
        },
        "totals": {
            "semester_1": sum(
                allocation["minutes"]
                for row in weeks[:semester_1_weeks]
                for allocation in row["allocations"]
            ),
            "semester_2": sum(
                allocation["minutes"]
                for row in weeks[semester_1_weeks:]
                for allocation in row["allocations"]
            ),
            "scheduled": sum(
                allocation["minutes"]
                for row in weeks
                for allocation in row["allocations"]
            ),
        },
        "weeks": weeks,
    }
    _write_yaml(root / "curriculum" / "course-schedule.yaml", schedule)
    return schedule


def _install_problem_id_schedule_contract(root: Path) -> dict[str, Any]:
    schedule = _build_schedule_fixture(root)
    manifest_path = root / "units" / "U01" / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    manifest["estimated_minutes"] = {
        "lesson": 200,
        "lesson_sessions": [100, 100],
        "practice": 200,
        "review": 50,
    }
    manifest["concept_sessions"] = {"concept-01": 1}
    manifest["practice"] = [
        {
            "id": f"U01-p{number:02}",
            "concepts": ["concept-01"],
            "path": f"practice/p{number:02}.ipynb",
            "solution_path": f"practice/p{number:02}_solution.ipynb",
            "minutes": 50,
            "after_session": 1 if number <= 2 else 2,
        }
        for number in range(1, 5)
    ]
    _write_yaml(manifest_path, manifest)
    schedule["weeks"][0]["allocations"] = [
        {"kind": "lesson-session", "unit": "U01", "session": 1, "minutes": 100},
        {
            "kind": "practice",
            "unit": "U01",
            "chunk": 1,
            "minutes": 100,
            "problem_ids": ["U01-p01", "U01-p02"],
        },
        {"kind": "lesson-session", "unit": "U01", "session": 2, "minutes": 100},
        {
            "kind": "practice",
            "unit": "U01",
            "chunk": 2,
            "minutes": 100,
            "problem_ids": ["U01-p03", "U01-p04"],
        },
        {"kind": "review", "unit": "U01", "chunk": 1, "minutes": 50},
    ]
    _write_yaml(root / "curriculum" / "course-schedule.yaml", schedule)
    return schedule


def _check_after(root: Path, mutate: Callable[[dict[str, Any]], None]):
    schedule = _build_schedule_fixture(root)
    mutate(schedule)
    _write_yaml(root / "curriculum" / "course-schedule.yaml", schedule)
    return _schedule_checker().check_schedule(root)


def _set_unit_minutes(
    root: Path,
    unit: str,
    *,
    lesson_sessions: list[int],
    practice: int,
    review: int,
) -> None:
    path = root / "units" / unit / "manifest.yaml"
    manifest = yaml.safe_load(path.read_text())
    manifest["estimated_minutes"] = {
        "lesson": sum(lesson_sessions),
        "lesson_sessions": lesson_sessions,
        "practice": practice,
        "review": review,
    }
    _write_yaml(path, manifest)


def _write_region_document(root: Path) -> str:
    human_sections = [
        "# Fixture course\n\nHuman optional-mock policy.\n\n",
        "\n\nHuman grading policy.\n\n",
        "\n\nHuman explanatory prerequisite prose.\n",
    ]
    regions = [
        course_renderer._region(name, f"old generated {name}")
        for name in course_renderer.OWNED_REGIONS
    ]
    document = (
        human_sections[0]
        + "\n\n".join(regions[:4])
        + human_sections[1]
        + "\n\n".join(regions[4:])
        + human_sections[2]
    )
    path = root / "docs" / "course-structure.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document)
    return document


def _outside_generated(document: str) -> str:
    for name in course_renderer.OWNED_REGIONS:
        document = re.sub(
            rf"<!-- BEGIN GENERATED: {re.escape(name)} -->\n.*?"
            rf"<!-- END GENERATED: {re.escape(name)} -->",
            "",
            document,
            flags=re.DOTALL,
        )
    return document


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


def test_schedule_checker_derives_semester_boundary_from_declared_calendar(
    tmp_path: Path,
) -> None:
    _build_schedule_fixture(tmp_path, semester_1_weeks=15)

    report = _schedule_checker().check_schedule(tmp_path)

    assert report.ok, report.errors


def test_schedule_checker_rejects_calendar_total_that_disagrees_with_semesters(
    tmp_path: Path,
) -> None:
    schedule = _build_schedule_fixture(tmp_path)
    schedule["calendar"]["total_weeks"] = 36
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(
        "calendar semester week counts must sum to total_weeks" in error
        for error in report.errors
    ), report.errors


def test_schedule_checker_rejects_week_beyond_declared_calendar(tmp_path: Path) -> None:
    schedule = _build_schedule_fixture(tmp_path)
    schedule["weeks"].append({"week": 36, "semester": 2, "allocations": []})
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any("unexpected week 36" in error for error in report.errors), report.errors


def test_schedule_checker_rejects_reordered_week_rows(tmp_path: Path) -> None:
    schedule = _build_schedule_fixture(tmp_path)
    schedule["weeks"][0], schedule["weeks"][1] = (
        schedule["weeks"][1],
        schedule["weeks"][0],
    )
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(
        "week rows must be ordered consecutively 1..35" in error
        for error in report.errors
    ), report.errors


def test_schedule_checker_rejects_a_nonterminal_final_assessment_week(
    tmp_path: Path,
) -> None:
    schedule = _build_schedule_fixture(tmp_path, week_count=40)
    final_allocations = schedule["weeks"][-1]["allocations"]
    schedule["weeks"][-2]["allocations"].extend(final_allocations[-2:])
    del final_allocations[-2:]
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(
        "final-assessment week 39 must be final week 40" in error
        for error in report.errors
    ), report.errors


def test_schedule_checker_rejects_a_regular_week_without_instruction(
    tmp_path: Path,
) -> None:
    schedule = _build_schedule_fixture(tmp_path)
    week = schedule["weeks"][16]
    week["allocations"].pop(0)
    week["allocations"][0]["minutes"] = 400
    _set_unit_minutes(
        tmp_path,
        "U17",
        lesson_sessions=[],
        practice=400,
        review=50,
    )
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(
        "week 17 has 0 lesson sessions; regular teaching weeks require 1-3"
        in error
        for error in report.errors
    ), report.errors


def test_schedule_checker_rejects_more_than_three_lesson_sessions_in_a_week(
    tmp_path: Path,
) -> None:
    schedule = _build_schedule_fixture(tmp_path)
    week = schedule["weeks"][16]
    week["allocations"][1]["minutes"] = 40
    week["allocations"][2]["minutes"] = 10
    for session in range(2, 5):
        week["allocations"].insert(
            session - 1,
            {
                "kind": "lesson-session",
                "unit": "U17",
                "session": session,
                "minutes": 100,
            },
        )
    _set_unit_minutes(
        tmp_path,
        "U17",
        lesson_sessions=[100, 100, 100, 100],
        practice=40,
        review=10,
    )
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(
        "week 17 has 4 lesson sessions; regular teaching weeks require 1-3"
        in error
        for error in report.errors
    ), report.errors


def test_schedule_checker_rejects_more_than_two_weeks_between_unit_sessions(
    tmp_path: Path,
) -> None:
    schedule = _build_schedule_fixture(tmp_path, chained_prerequisites=False)
    schedule["weeks"][19]["allocations"].insert(
        0,
        {
            "kind": "lesson-session",
            "unit": "U17",
            "session": 2,
            "minutes": 100,
        },
    )
    schedule["weeks"][19]["allocations"][2]["minutes"] = 200
    _set_unit_minutes(
        tmp_path,
        "U17",
        lesson_sessions=[100, 100],
        practice=300,
        review=50,
    )
    _set_unit_minutes(
        tmp_path,
        "U20",
        lesson_sessions=[100],
        practice=200,
        review=50,
    )
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(
        "U17 lesson sessions 1 and 2 are 3 weeks apart; maximum gap is 2"
        in error
        for error in report.errors
    ), report.errors


def test_schedule_checker_rejects_reversed_numbered_sessions(
    tmp_path: Path,
) -> None:
    schedule = _build_schedule_fixture(tmp_path, chained_prerequisites=False)
    week_17 = schedule["weeks"][16]["allocations"]
    week_17[0]["session"] = 2
    week_17[1]["minutes"] = 350
    week_17.pop(2)
    week_20 = schedule["weeks"][19]["allocations"]
    week_20[1]["minutes"] = 150
    week_20.extend(
        [
            {
                "kind": "lesson-session",
                "unit": "U17",
                "session": 1,
                "minutes": 100,
            },
            {"kind": "review", "unit": "U17", "chunk": 1, "minutes": 50},
        ]
    )
    _set_unit_minutes(
        tmp_path,
        "U17",
        lesson_sessions=[100, 100],
        practice=350,
        review=50,
    )
    _set_unit_minutes(
        tmp_path,
        "U20",
        lesson_sessions=[100],
        practice=150,
        review=50,
    )
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(
        "U17 lesson session 2 occurs in week 17 before session 1 in week 20"
        in error
        for error in report.errors
    ), report.errors


def test_schedule_checker_requires_review_to_be_the_unit_final_allocation(
    tmp_path: Path,
) -> None:
    schedule = _build_schedule_fixture(tmp_path)
    allocations = schedule["weeks"][0]["allocations"]
    allocations[1], allocations[2] = allocations[2], allocations[1]
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(
        "U01 review allocation must be its final scheduled allocation" in error
        for error in report.errors
    ), report.errors


def test_course_renderer_preserves_all_bytes_outside_generated_regions(
    tmp_path: Path,
) -> None:
    _build_schedule_fixture(tmp_path)
    before = _write_region_document(tmp_path)
    outside_before = _outside_generated(before)

    assert course_renderer.main(["--root", str(tmp_path)]) == 0

    after = (tmp_path / "docs" / "course-structure.md").read_text()
    assert _outside_generated(after) == outside_before


@pytest.mark.parametrize("check", [False, True])
def test_course_renderer_rejects_a_duplicate_complete_sentinel_pair(
    tmp_path: Path, check: bool
) -> None:
    _build_schedule_fixture(tmp_path)
    document = _write_region_document(tmp_path)
    duplicate = course_renderer._region("course-model", "duplicate")
    (tmp_path / "docs" / "course-structure.md").write_text(
        document + "\n" + duplicate + "\n"
    )
    args = ["--root", str(tmp_path), *(["--check"] if check else [])]

    assert course_renderer.main(args) == 1


@pytest.mark.parametrize("damage", ["missing", "malformed"])
def test_course_renderer_rejects_missing_or_malformed_sentinels(
    tmp_path: Path, damage: str
) -> None:
    _build_schedule_fixture(tmp_path)
    document = _write_region_document(tmp_path)
    region = course_renderer._region("weekly-table", "old generated weekly-table")
    if damage == "missing":
        document = document.replace(region, "")
    else:
        document = document.replace("<!-- END GENERATED: weekly-table -->", "")
    (tmp_path / "docs" / "course-structure.md").write_text(document)

    assert course_renderer.main(["--root", str(tmp_path), "--check"]) == 1


def test_schedule_checker_accepts_consecutive_multiweek_practice_chunks(
    tmp_path: Path,
) -> None:
    schedule = _build_schedule_fixture(tmp_path)
    first = schedule["weeks"][0]["allocations"][1]
    first["minutes"] = 150
    schedule["weeks"][0]["allocations"].insert(
        2,
        {"kind": "practice", "unit": "U01", "chunk": 2, "minutes": 150}
    )
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


def test_schedule_checker_accepts_exact_problem_id_partition_minutes_and_order(
    tmp_path: Path,
) -> None:
    _install_problem_id_schedule_contract(tmp_path)

    report = _schedule_checker().check_schedule(tmp_path)

    assert report.ok, report.errors


@pytest.mark.parametrize(
    ("mutation", "required_fragments"),
    [
        pytest.param(
            lambda schedule: schedule["weeks"][0]["allocations"][1]["problem_ids"].pop(),
            ("U01-p02", "exactly once"),
            id="missing-problem-id",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][0]["allocations"][3]["problem_ids"].__setitem__(
                1, "U01-p03"
            ),
            ("U01-p03", "exactly once"),
            id="duplicate-problem-id",
        ),
        pytest.param(
            lambda schedule: schedule["weeks"][0]["allocations"][1].update(
                problem_ids=["U01-p01"]
            ),
            ("chunk 1", "50", "100"),
            id="chunk-minute-mismatch",
        ),
        pytest.param(
            lambda schedule: (
                schedule["weeks"][0]["allocations"][1].update(
                    problem_ids=["U01-p01", "U01-p03"]
                ),
                schedule["weeks"][0]["allocations"][3].update(
                    problem_ids=["U01-p02", "U01-p04"]
                ),
            ),
            ("U01-p03", "session 2"),
            id="problem-before-after-session",
        ),
    ],
)
def test_schedule_checker_rejects_invalid_problem_id_contracts(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], object],
    required_fragments: tuple[str, ...],
) -> None:
    schedule = _install_problem_id_schedule_contract(tmp_path)
    mutation(schedule)
    _write_yaml(tmp_path / "curriculum" / "course-schedule.yaml", schedule)

    report = _schedule_checker().check_schedule(tmp_path)

    assert not report.ok
    assert any(
        all(fragment in error for fragment in required_fragments)
        for error in report.errors
    ), report.errors


def test_schedule_checker_derives_week_40_as_the_unique_final_assessment_week(
    tmp_path: Path,
) -> None:
    _build_schedule_fixture(tmp_path, week_count=40)

    report = _schedule_checker().check_schedule(tmp_path)

    assert report.ok, report.errors


def test_course_renderer_derives_40_week_16_plus_24_calendar_and_final_milestone(
    tmp_path: Path,
) -> None:
    _build_schedule_fixture(tmp_path, week_count=40)
    _write_region_document(tmp_path)

    rendered = course_renderer.render_document(tmp_path)

    assert "runs for 40 weeks in two semesters: 16 weeks followed by 24 weeks" in rendered
    assert "Semester 2 is Weeks 17–40" in rendered
    assert "summative milestone is `r1-001` in Week 40" in rendered
    assert "35 weeks" not in rendered
    assert "followed by 19 weeks" not in rendered


def test_course_renderer_places_semester_close_at_declared_boundary(
    tmp_path: Path,
) -> None:
    _build_schedule_fixture(tmp_path, semester_1_weeks=15)
    _write_region_document(tmp_path)

    rendered = course_renderer.render_document(tmp_path)
    week_15 = next(line for line in rendered.splitlines() if line.startswith("| 15 |"))
    week_16 = next(line for line in rendered.splitlines() if line.startswith("| 16 |"))

    assert "Semester 1 close" in week_15
    assert "Semester 1 close" not in week_16


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


def test_real_schedule_has_exact_plan018_calendar_and_complete_allocation() -> None:
    report = _schedule_checker().check_schedule(BOOK1_ROOT)
    assert report.ok, report.errors

    schedule = yaml.safe_load((BOOK1_ROOT / "curriculum" / "course-schedule.yaml").read_text())
    weeks = schedule["weeks"]
    assert schedule["calendar"] == {
        "semester_1_weeks": 16,
        "semester_2_weeks": 24,
        "total_weeks": 40,
    }
    validated = _schedule_checker().load_validated_schedule(BOOK1_ROOT)
    assert validated.semester_week_counts == (16, 24)
    assert validated.declared_week_count == 40
    assert len(weeks) == 40
    assert [week["week"] for week in weeks] == list(range(1, 41))
    assert [week["semester"] for week in weeks] == [1] * 16 + [2] * 24
    totals = [sum(allocation["minutes"] for allocation in week["allocations"]) for week in weeks]
    assert all(450 <= total <= 500 for total in totals)
    assert sum(totals[:16]) == 7915
    assert sum(totals[16:]) == 10960
    assert sum(totals) == 18875
    assert sum(totals[16:33]) == 7780
    assert sum(totals[33:]) == 3180
    assert totals[33:] == [450, 480, 450, 450, 450, 450, 450]
    assert schedule["totals"] == {
        "semester_1": 7915,
        "semester_2": 10960,
        "scheduled": 18875,
    }
    lesson_counts = [
        sum(allocation["kind"] == "lesson-session" for allocation in week["allocations"])
        for week in weeks
    ]
    assert all(1 <= count <= 3 for count in lesson_counts[:-1])
    assert lesson_counts[-1] == 0

    manifested = sum(
        allocation["minutes"]
        for week in weeks
        for allocation in week["allocations"]
        if allocation["kind"] in {"lesson-session", "practice", "review"}
    )
    assert manifested == 18635

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
    assert [
        week["week"]
        for week in weeks
        for allocation in week["allocations"]
        if allocation["kind"] == "lesson-session"
        and allocation.get("unit") == "C11-neural-training"
    ] == [24, 24, 25, 25, 26]
    assert [
        week["week"]
        for week in weeks
        for allocation in week["allocations"]
        if allocation["kind"] == "lesson-session"
        and allocation.get("unit") == "C7-cnn-transfer"
    ] == [29, 30, 31, 32]
    assert [row["kind"] for row in weeks[-1]["allocations"][-2:]] == ["mock", "debrief"]
    assert weeks[-1]["allocations"][-2]["test"] == "r1-001"
    assert weeks[-1]["allocations"][-2]["minutes"] == 180
    assert weeks[-1]["allocations"][-1]["minutes"] == 60
    assert [
        week["week"]
        for week in weeks
        for allocation in week["allocations"]
        if allocation["kind"] == "lesson-session"
        and allocation.get("unit") == "C12-classical-models"
    ] == [34, 35, 36, 37, 38, 39]
    assert [row["kind"] for row in weeks[-1]["allocations"]] == [
        "practice",
        "review",
        "mock",
        "debrief",
    ]


def test_real_c12_schedule_has_exact_problem_ids_minutes_and_partition() -> None:
    schedule = yaml.safe_load((BOOK1_ROOT / "curriculum" / "course-schedule.yaml").read_text())
    expected = {
        34: (["C12-p06", "C12-p14"], 100),
        35: (["C12-p01", "C12-p07", "C12-p08", "C12-p22", "C12-p26"], 225),
        36: (["C12-p09", "C12-p15", "C12-p27"], 150),
        37: (
            ["C12-p03", "C12-p10", "C12-p11", "C12-p16", "C12-p23", "C12-p28"],
            270,
        ),
        38: (["C12-p04", "C12-p12", "C12-p19", "C12-p24", "C12-p29"], 235),
        39: (["C12-p02", "C12-p05", "C12-p18", "C12-p20", "C12-p21", "C12-p25"], 280),
        40: (["C12-p13", "C12-p17", "C12-p30"], 150),
    }

    actual = {}
    for week in schedule["weeks"]:
        rows = [
            allocation
            for allocation in week["allocations"]
            if allocation["kind"] == "practice"
            and allocation.get("unit") == "C12-classical-models"
        ]
        if rows:
            assert len(rows) == 1
            actual[week["week"]] = (rows[0]["problem_ids"], rows[0]["minutes"])

    assert actual == expected
    flattened = [problem_id for problem_ids, _ in actual.values() for problem_id in problem_ids]
    assert sorted(flattened) == [f"C12-p{number:02}" for number in range(1, 31)]
    assert len(flattened) == len(set(flattened)) == 30


def test_c11_practice_never_exceeds_unlocked_problem_minutes() -> None:
    manifest = yaml.safe_load(
        (BOOK1_ROOT / "units" / "C11-neural-training" / "manifest.yaml").read_text()
    )
    concepts_added_by_session = [
        {"softmax", "cross-entropy-loss"},
        {"manual-backpropagation"},
        {"trained-mlp"},
        {"autograd-training", "torch-optimizers"},
        {"batch-normalization", "dropout"},
    ]
    unlocked: set[str] = set()
    capacities: list[int] = []
    for concepts in concepts_added_by_session:
        unlocked.update(concepts)
        capacities.append(
            sum(
                problem["minutes"]
                for problem in manifest["practice"]
                if set(problem["concepts"]) <= unlocked
            )
        )
    assert capacities == [250, 375, 520, 740, 1040]

    schedule = yaml.safe_load(
        (BOOK1_ROOT / "curriculum" / "course-schedule.yaml").read_text()
    )
    delivered_sessions = 0
    scheduled_practice = 0
    for week in schedule["weeks"]:
        for allocation in week["allocations"]:
            if allocation.get("unit") != "C11-neural-training":
                continue
            if allocation["kind"] == "lesson-session":
                delivered_sessions += 1
                assert allocation["session"] == delivered_sessions
            elif allocation["kind"] == "practice":
                scheduled_practice += allocation["minutes"]
                capacity = capacities[delivered_sessions - 1]
                assert scheduled_practice <= capacity, (
                    f"week {week['week']} schedules {scheduled_practice} cumulative "
                    f"C11 practice minutes after {delivered_sessions} sessions; "
                    f"only {capacity} problem minutes are unlocked"
                )


def test_f7_instruction_precedes_high_volume_practice() -> None:
    schedule = yaml.safe_load(
        (BOOK1_ROOT / "curriculum" / "course-schedule.yaml").read_text()
    )
    rows = [
        (week["week"], allocation)
        for week in schedule["weeks"]
        for allocation in week["allocations"]
        if allocation.get("unit") == "F7-kernels-convex-optimization"
    ]
    delivered_sessions = 0
    for week, allocation in rows:
        if allocation["kind"] == "lesson-session":
            delivered_sessions += 1
            assert allocation["session"] == delivered_sessions
        elif allocation["kind"] == "practice" and allocation["minutes"] > 5:
            assert delivered_sessions == 4, (
                f"week {week} schedules {allocation['minutes']} F7 practice minutes "
                f"after only {delivered_sessions} sessions"
            )

    assert [
        week
        for week, allocation in rows
        if allocation["kind"] == "lesson-session"
    ] == [22, 22, 23, 23]
    assert [
        (week, allocation["minutes"])
        for week, allocation in rows
        if allocation["kind"] == "practice"
    ] == [(22, 5), (23, 169), (24, 212), (25, 141), (26, 113)]


def test_course_structure_states_interleaving_and_prerequisite_order_contract() -> None:
    document = course_renderer.render_document(BOOK1_ROOT)

    assert "independent units may interleave" in document
    assert (
        "prerequisite's complete allocation must finish before the dependent unit's "
        "first session"
    ) in document
    assert "earlier unit's remaining work and review finish before the later unit begins" not in document
    assert (
        "earlier unit's remaining practice and review finish before the later unit's "
        "first session"
    ) not in document
    assert "F7 also finishes before C9 begins" not in document


def test_rendered_first_instruction_region_exactly_matches_the_schedule_source() -> None:
    schedule = yaml.safe_load((BOOK1_ROOT / "curriculum" / "course-schedule.yaml").read_text())
    first_week: dict[str, int] = {}
    for week in schedule["weeks"]:
        for allocation in week["allocations"]:
            if allocation["kind"] == "lesson-session":
                first_week.setdefault(allocation["unit"], week["week"])
    expected = list(first_week.items())

    document = course_renderer.render_document(BOOK1_ROOT)
    actual = _rendered_first_instruction_pairs(document)

    assert actual == expected
    positions = {unit: index for index, (unit, _) in enumerate(actual)}
    assert positions["C5-neural-networks"] < positions["C6-pytorch"]
    assert positions["C6-pytorch"] < positions["C11-neural-training"]
    assert positions["C11-neural-training"] < positions["C7-cnn-transfer"]


def test_book2_sidecar_creation_cannot_rewrite_checked_in_book1_schedule(
    tmp_path: Path,
) -> None:
    _build_schedule_fixture(tmp_path)
    source = tmp_path / "curriculum" / "course-schedule.yaml"
    before = source.read_bytes()
    book1_manifests_before = load_unit_manifests(tmp_path)
    _write_yaml(
        tmp_path / "curriculum" / "book2-schedule.yaml",
        {
            "schedule_version": 1,
            "book": 2,
            "starts_after_global_week": 40,
            "total_book_weeks": 6,
            "final_assessment": {
                "kind": "future-r2-mock",
                "status": "planned",
                "after_book_week": 6,
            },
            "weeks": [],
        },
    )
    _write_yaml(
        tmp_path / "units" / "B2-019-attention-transformers" / "manifest.yaml",
        {
            "unit": "B2-019-attention-transformers",
            "book": 2,
            "round": 2,
            "layer": "round-2-extension",
            "track": "extension",
            "concepts_taught": ["attention"],
            "concepts_used": ["softmax"],
            "concept_prerequisites": ["softmax"],
            "prereq_units": ["U35"],
            "bridge_diagnostic": {
                "path": "lessons/00-book1-bridge.ipynb",
                "minutes": 30,
                "referenced_concepts": ["softmax"],
            },
            "coverage_claims": [],
            "practice": [],
        },
    )

    parsed_book2 = next(
        manifest
        for manifest in load_unit_manifests(tmp_path)
        if manifest.unit_id == "B2-019-attention-transformers"
    )

    assert parsed_book2.concepts_taught == ["attention"]
    assert parsed_book2.prereq_units == ["U35"]
    assert {manifest.unit_id for manifest in book1_manifests_before} == {
        manifest.unit_id
        for manifest in load_unit_manifests(tmp_path)
        if not manifest.unit_id.startswith("B2-")
    }
    assert source.read_bytes() == before


def test_schedule_checker_is_bound_to_the_selected_bookspec_root(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write_yaml(
        repo / "books.yaml",
        {
            "books_version": 1,
            "books": [
                {"id": "book1", "number": 1, "root": "book1", "depends_on": []}
            ],
        },
    )
    book_root = repo / "book1"
    book_root.mkdir()
    _build_schedule_fixture(book_root)
    try:
        books = importlib.import_module("tools.books")
    except ModuleNotFoundError as exc:
        if exc.name != "tools.books":
            raise
        pytest.fail("tools.books is the missing Plan 019 registry producer")
    book = books.load_book_catalog(repo).by_id("book1")

    selected = _schedule_checker().check_schedule(book.root)

    assert selected.ok, selected.errors
    try:
        unselected = _schedule_checker().check_schedule(repo)
    except (FileNotFoundError, ValueError):
        pass
    else:
        assert not unselected.ok
