"""Validate the canonical week-by-week course allocation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tools.model import (
    CourseSchedule,
    Report,
    ScheduleAllocation,
    ScheduleWeek,
    load_syllabus,
    load_unit_manifests,
)

KINDS = {"lesson-session", "practice", "review", "mock", "debrief"}
BOOK2_KINDS = {"bridge-diagnostic", "lesson-session", "practice", "review"}
BOOK2_UNIT = "B2-019-attention-transformers"
BOOK2_PROBLEM_MINUTES = {
    **{f"B2-019-p{number:02}": 20 for number in range(1, 6)},
    **{f"B2-019-p{number:02}": 50 for number in range(6, 13)},
    **{f"B2-019-p{number:02}": 45 for number in range(13, 17)},
    **{f"B2-019-p{number:02}": 65 for number in range(17, 22)},
    **{f"B2-019-p{number:02}": 55 for number in range(22, 25)},
}
BOOK2_WEEK_PROBLEMS = (
    ("B2-019-p01", "B2-019-p02", "B2-019-p06", "B2-019-p13"),
    ("B2-019-p03", "B2-019-p04", "B2-019-p07", "B2-019-p08", "B2-019-p14"),
    (
        "B2-019-p05",
        "B2-019-p09",
        "B2-019-p10",
        "B2-019-p15",
        "B2-019-p16",
        "B2-019-p21",
        "B2-019-p23",
    ),
    ("B2-019-p11", "B2-019-p17", "B2-019-p18", "B2-019-p22"),
    ("B2-019-p12", "B2-019-p19", "B2-019-p20", "B2-019-p24"),
)


@dataclass(frozen=True)
class Book2CourseSchedule(CourseSchedule):
    """Validated Book 2 schedule metadata without changing Book 1's model/repr."""

    status: str = "staged"
    global_weeks: tuple[int, ...] = ()
    covered_problem_ids: frozenset[str] = frozenset()


class Book1SchedulePolicy:
    """Validate the unchanged 40-week, two-semester Book 1 contract."""

    def load(
        self, root: Path, errors: list[str], *, enforce_calendar: bool = True
    ) -> CourseSchedule | None:
        schedule = _parse_schedule(root, errors)
        if schedule is not None:
            _validate(root, schedule, errors, enforce_calendar=enforce_calendar)
        return schedule


class Book2SchedulePolicy:
    """Validate Book 2's local/global staged schedule contract."""

    def load(
        self, root: Path, errors: list[str], *, enforce_calendar: bool = True
    ) -> Book2CourseSchedule | None:
        del enforce_calendar
        return _parse_book2_schedule(root, errors)


def schedule_policy(root: str | Path):
    """Dispatch to a book policy from the selected root's schedule schema."""

    root = Path(root).resolve()
    raw = _read_yaml(root / "curriculum" / "course-schedule.yaml")
    if isinstance(raw, dict) and ("book" in raw or "status" in raw):
        return Book2SchedulePolicy()
    return Book1SchedulePolicy()


def _positive_integer(value: object, label: str, errors: list[str]) -> int | None:
    if type(value) is not int:
        errors.append(f"{label} must be an integer")
        return None
    if value <= 0:
        errors.append(f"{label} must be positive")
        return None
    return value


def _exact_integer(
    value: object, label: str, expected: int, errors: list[str]
) -> int | None:
    if type(value) is not int:
        errors.append(f"{label} must be an integer")
        return None
    if value != expected:
        errors.append(f"{label} must be integer {expected}")
        return None
    return value


def _mapping(value: object, label: str, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{label} must be a mapping")
        return None
    return value


def _read_yaml(path: Path) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"{path}: cannot load schedule: {exc}") from exc


def _parse_schedule(root: Path, errors: list[str]) -> CourseSchedule | None:
    path = root / "curriculum" / "course-schedule.yaml"
    raw = _mapping(_read_yaml(path), "course-schedule.yaml", errors)
    if raw is None:
        return None
    allowed_keys = {"schedule_version", "calendar", "weeks", "totals"}
    if not {"schedule_version", "calendar", "weeks"} <= set(raw) or not set(
        raw
    ) <= allowed_keys:
        errors.append(
            "course-schedule.yaml keys must be schedule_version, calendar, weeks, "
            "and optional totals"
        )
    version = raw.get("schedule_version")
    if type(version) is not int or version != 1:
        errors.append("schedule_version must be integer 1")
    semester_week_counts: tuple[int, int] | None = None
    declared_week_count: int | None = None
    calendar = _mapping(raw.get("calendar"), "course-schedule.yaml calendar", errors)
    if calendar is not None:
        expected_calendar_keys = {
            "semester_1_weeks",
            "semester_2_weeks",
            "total_weeks",
        }
        if set(calendar) != expected_calendar_keys:
            errors.append(
                "course-schedule.yaml calendar keys must be semester_1_weeks, "
                "semester_2_weeks, and total_weeks"
            )
        elif all(key in calendar for key in expected_calendar_keys):
            first_weeks = _positive_integer(
                calendar["semester_1_weeks"], "calendar semester_1_weeks", errors
            )
            second_weeks = _positive_integer(
                calendar["semester_2_weeks"], "calendar semester_2_weeks", errors
            )
            declared_week_count = _positive_integer(
                calendar["total_weeks"], "calendar total_weeks", errors
            )
            if first_weeks is not None and second_weeks is not None:
                semester_week_counts = (first_weeks, second_weeks)
                if (
                    declared_week_count is not None
                    and first_weeks + second_weeks != declared_week_count
                ):
                    errors.append(
                        "calendar semester week counts must sum to total_weeks"
                    )
    raw_weeks = raw.get("weeks")
    if not isinstance(raw_weeks, list):
        errors.append("course-schedule.yaml weeks must be a list")
        return None
    semester_minutes: tuple[int, int] | None = None
    declared_total: int | None = None
    totals = raw.get("totals")
    if totals is not None:
        if not isinstance(totals, dict) or set(totals) != {
            "semester_1",
            "semester_2",
            "scheduled",
        }:
            errors.append(
                "course-schedule.yaml totals keys must be semester_1, semester_2, and scheduled"
            )
        else:
            first = _positive_integer(totals["semester_1"], "totals semester_1", errors)
            second = _positive_integer(totals["semester_2"], "totals semester_2", errors)
            declared_total = _positive_integer(
                totals["scheduled"], "totals scheduled", errors
            )
            if first is not None and second is not None:
                semester_minutes = (first, second)
    weeks: list[ScheduleWeek] = []
    for row_index, value in enumerate(raw_weeks):
        row = _mapping(value, f"week row {row_index}", errors)
        if row is None:
            continue
        if set(row) != {"week", "semester", "allocations"}:
            errors.append(
                f"week row {row_index} keys must be week, semester, and allocations"
            )
        week = _positive_integer(row.get("week"), f"week row {row_index} week", errors)
        semester = _positive_integer(
            row.get("semester"), f"week row {row_index} semester", errors
        )
        raw_allocations = row.get("allocations")
        if not isinstance(raw_allocations, list):
            errors.append(f"week {week or row_index + 1} allocations must be a list")
            continue
        allocations: list[ScheduleAllocation] = []
        for allocation_index, value in enumerate(raw_allocations):
            label = f"week {week or row_index + 1} allocation {allocation_index}"
            allocation = _mapping(value, label, errors)
            if allocation is None:
                continue
            kind = allocation.get("kind")
            if kind not in KINDS:
                errors.append(f"{label} has unknown kind {kind}")
                continue
            expected_keys = {
                "lesson-session": {"kind", "unit", "session", "minutes"},
                "practice": {"kind", "unit", "chunk", "minutes"},
                "review": {"kind", "unit", "chunk", "minutes"},
                "mock": {"kind", "test", "minutes"},
                "debrief": {"kind", "test", "minutes"},
            }[str(kind)]
            allowed_keys = [expected_keys]
            if kind == "practice":
                allowed_keys.append(expected_keys | {"problem_ids"})
            if set(allocation) not in allowed_keys:
                errors.append(f"{label} keys must exactly equal {sorted(expected_keys)}")
            minutes = _positive_integer(allocation.get("minutes"), f"{label} minutes", errors)
            session = None
            chunk = None
            if kind == "lesson-session":
                session = _positive_integer(allocation.get("session"), f"{label} session", errors)
            elif kind in {"practice", "review"}:
                chunk = _positive_integer(allocation.get("chunk"), f"{label} chunk", errors)
            unit = allocation.get("unit")
            test = allocation.get("test")
            problem_ids = None
            if "problem_ids" in allocation:
                raw_problem_ids = allocation["problem_ids"]
                if not isinstance(raw_problem_ids, list) or not all(
                    isinstance(problem_id, str) and problem_id
                    for problem_id in raw_problem_ids
                ):
                    errors.append(f"{label} problem_ids must be a list of nonempty strings")
                else:
                    problem_ids = list(raw_problem_ids)
            if kind in {"lesson-session", "practice", "review"} and not isinstance(unit, str):
                errors.append(f"{label} unit must be a string")
                unit = None
            if kind in {"mock", "debrief"} and not isinstance(test, str):
                errors.append(f"{label} test must be a string")
                test = None
            if minutes is not None:
                allocations.append(
                    ScheduleAllocation(
                        kind=str(kind),
                        minutes=minutes,
                        unit=unit if isinstance(unit, str) else None,
                        session=session,
                        chunk=chunk,
                        test=test if isinstance(test, str) else None,
                        problem_ids=problem_ids,
                    )
                )
        if week is not None and semester is not None:
            weeks.append(ScheduleWeek(week, semester, allocations))
    return CourseSchedule(
        schedule_version=1,
        weeks=weeks,
        semester_week_counts=semester_week_counts,
        declared_week_count=declared_week_count,
        semester_minutes=semester_minutes,
        declared_total_minutes=declared_total,
    )


def _parse_book2_schedule(
    root: Path, errors: list[str]
) -> Book2CourseSchedule | None:
    path = root / "curriculum" / "course-schedule.yaml"
    raw = _mapping(_read_yaml(path), "course-schedule.yaml", errors)
    if raw is None:
        return None
    expected_top_level = {
        "schedule_version",
        "book",
        "status",
        "starts_after_global_week",
        "total_book_weeks",
        "total_minutes",
        "final_assessment",
        "weeks",
    }
    if set(raw) != expected_top_level:
        errors.append(
            "staged Book 2 schedule keys must be book, final_assessment, "
            "schedule_version, starts_after_global_week, status, total_book_weeks, "
            "total_minutes, and weeks"
        )
    if raw.get("schedule_version") != 1 or type(raw.get("schedule_version")) is not int:
        errors.append("schedule_version must be integer 1")
    if raw.get("book") != 2 or type(raw.get("book")) is not int:
        errors.append("Book 2 schedule book must be integer 2")
    if raw.get("status") != "staged":
        errors.append("Book 2 schedule status must be staged until Task 5")
    _exact_integer(
        raw.get("starts_after_global_week"),
        "Book 2 schedule starts_after_global_week",
        40,
        errors,
    )
    _exact_integer(
        raw.get("total_book_weeks"),
        "Book 2 schedule total_book_weeks",
        6,
        errors,
    )
    _exact_integer(
        raw.get("total_minutes"),
        "Book 2 schedule total_minutes",
        1660,
        errors,
    )

    marker = raw.get("final_assessment")
    if isinstance(marker, dict):
        marker_week = marker.get("after_book_week")
        if type(marker_week) is not int:
            errors.append(
                "Book 2 final_assessment.after_book_week must be an integer"
            )
            marker_week = None
        elif marker_week != 6:
            errors.append("planned final assessment marker must follow book week 6")
        marker_without_week = {
            key: value for key, value in marker.items() if key != "after_book_week"
        }
        if marker_without_week != {"kind": "future-r2-mock", "status": "planned"}:
            errors.append(
                "Book 2 schedule requires the planned future-r2-mock final assessment marker"
            )
    else:
        errors.append(
            "Book 2 schedule requires the planned future-r2-mock final assessment marker"
        )

    raw_weeks = raw.get("weeks")
    if not isinstance(raw_weeks, list):
        errors.append("course-schedule.yaml weeks must be a list")
        return None

    local_weeks: list[int] = []
    global_weeks: list[int] = []
    weeks: list[ScheduleWeek] = []
    for row_index, value in enumerate(raw_weeks):
        row = _mapping(value, f"Book 2 week row {row_index}", errors)
        if row is None:
            continue
        if set(row) != {"book_week", "global_week", "allocations"}:
            errors.append(
                f"Book 2 week row {row_index} keys must be allocations, book_week, and global_week"
            )
        book_week = _positive_integer(
            row.get("book_week"), f"Book 2 week row {row_index} book_week", errors
        )
        global_week = _positive_integer(
            row.get("global_week"), f"Book 2 week row {row_index} global_week", errors
        )
        if book_week is not None:
            local_weeks.append(book_week)
        if global_week is not None:
            global_weeks.append(global_week)
        raw_allocations = row.get("allocations")
        if not isinstance(raw_allocations, list):
            errors.append(
                f"Book 2 week {book_week or row_index + 1} allocations must be a list"
            )
            continue
        allocations: list[ScheduleAllocation] = []
        for allocation_index, value in enumerate(raw_allocations):
            label = (
                f"Book 2 week {book_week or row_index + 1} allocation "
                f"{allocation_index}"
            )
            allocation = _mapping(value, label, errors)
            if allocation is None:
                continue
            kind = allocation.get("kind")
            if kind not in BOOK2_KINDS:
                errors.append(f"{label} has unknown Book 2 allocation kind {kind}")
                continue
            expected_keys = {
                "bridge-diagnostic": {"kind", "unit", "minutes"},
                "lesson-session": {"kind", "unit", "session", "minutes"},
                "practice": {"kind", "unit", "chunk", "minutes", "problem_ids"},
                "review": {"kind", "unit", "chunk", "minutes"},
            }[str(kind)]
            if set(allocation) != expected_keys:
                errors.append(f"{label} keys must exactly equal {sorted(expected_keys)}")
            minutes = _positive_integer(
                allocation.get("minutes"), f"{label} minutes", errors
            )
            unit = allocation.get("unit")
            if not isinstance(unit, str) or not unit:
                errors.append(f"{label} unit must be a nonempty string")
                unit = None
            elif ":" in unit:
                errors.append(f"cross-book unit reference {unit} is forbidden in Book 2 schedule")
            elif unit != BOOK2_UNIT:
                errors.append(f"unknown Book 2 unit {unit}")
            session = None
            chunk = None
            problem_ids = None
            if kind == "lesson-session":
                session = _positive_integer(
                    allocation.get("session"), f"{label} session", errors
                )
            elif kind in {"practice", "review"}:
                chunk = _positive_integer(
                    allocation.get("chunk"), f"{label} chunk", errors
                )
            if kind == "practice":
                candidate_ids = allocation.get("problem_ids")
                if not isinstance(candidate_ids, list) or not all(
                    isinstance(problem_id, str) and problem_id
                    for problem_id in candidate_ids
                ):
                    errors.append(f"{label} problem_ids must be a list of nonempty strings")
                else:
                    problem_ids = list(candidate_ids)
            if minutes is not None:
                allocations.append(
                    ScheduleAllocation(
                        kind=str(kind),
                        minutes=minutes,
                        unit=unit if isinstance(unit, str) else None,
                        session=session,
                        chunk=chunk,
                        problem_ids=problem_ids,
                    )
                )
        if book_week is not None:
            weeks.append(ScheduleWeek(book_week, 1, allocations))

    if local_weeks != list(range(1, 7)):
        errors.append("Book 2 book_week rows must be ordered consecutively 1..6")
    if global_weeks != list(range(41, 47)):
        errors.append("Book 2 global_week rows must be 41..46 in order")

    expected_kinds = (
        ("bridge-diagnostic", "lesson-session", "practice"),
        ("lesson-session", "practice"),
        ("lesson-session", "practice"),
        ("lesson-session", "practice"),
        ("lesson-session", "practice"),
        ("review",),
    )
    expected_minutes = (
        (30, 90, 135),
        (90, 185),
        (90, 330),
        (90, 235),
        (90, 235),
        (60,),
    )
    listed_problem_ids: list[str] = []
    for index, week in enumerate(weeks[:6]):
        kinds = tuple(allocation.kind for allocation in week.allocations)
        if kinds != expected_kinds[index]:
            errors.append(
                f"Book 2 week {index + 1} allocation kinds {kinds}; "
                f"expected {expected_kinds[index]}"
            )
        for allocation, minutes in zip(week.allocations, expected_minutes[index]):
            if allocation.minutes != minutes:
                errors.append(
                    f"Book 2 week {index + 1} {allocation.kind} allocation minutes "
                    f"{allocation.minutes}; expected {minutes}"
                )
        lesson_rows = [
            allocation for allocation in week.allocations if allocation.kind == "lesson-session"
        ]
        if index < 5 and (
            len(lesson_rows) != 1 or lesson_rows[0].session != index + 1
        ):
            errors.append(
                f"Book 2 week {index + 1} must contain lesson session {index + 1} exactly once"
            )
        practice_rows = [
            allocation for allocation in week.allocations if allocation.kind == "practice"
        ]
        if index < 5:
            if len(practice_rows) != 1 or practice_rows[0].chunk != index + 1:
                errors.append(
                    f"Book 2 week {index + 1} must contain practice chunk {index + 1} exactly once"
                )
            elif practice_rows[0].problem_ids is not None:
                listed_problem_ids.extend(practice_rows[0].problem_ids)
                expected_ids = list(BOOK2_WEEK_PROBLEMS[index])
                if practice_rows[0].problem_ids != expected_ids:
                    errors.append(
                        f"Book 2 practice chunk {index + 1} problem_ids must be {expected_ids}"
                    )
                known_minutes = [
                    BOOK2_PROBLEM_MINUTES[problem_id]
                    for problem_id in practice_rows[0].problem_ids
                    if problem_id in BOOK2_PROBLEM_MINUTES
                ]
                if len(known_minutes) == len(practice_rows[0].problem_ids):
                    actual_problem_minutes = sum(known_minutes)
                    if actual_problem_minutes != practice_rows[0].minutes:
                        errors.append(
                            f"Book 2 practice chunk {index + 1} problem minutes "
                            f"{actual_problem_minutes}; allocation minutes "
                            f"{practice_rows[0].minutes}"
                        )

    counts = Counter(listed_problem_ids)
    for problem_id in BOOK2_PROBLEM_MINUTES:
        if counts[problem_id] != 1:
            errors.append(
                f"{problem_id} must appear exactly once in staged problem_ids; "
                f"found {counts[problem_id]}"
            )
    for problem_id in sorted(set(listed_problem_ids) - set(BOOK2_PROBLEM_MINUTES)):
        errors.append(f"unknown staged Book 2 problem ID {problem_id}")

    actual_total = sum(
        allocation.minutes for week in weeks for allocation in week.allocations
    )
    if actual_total != 1660:
        errors.append(f"Book 2 scheduled total {actual_total}; expected 1660")
    if raw.get("total_minutes") != actual_total:
        errors.append(
            f"Book 2 declared total {raw.get('total_minutes')}; actual {actual_total}"
        )
    if list((root / "units").glob("*/manifest.yaml")):
        errors.append(
            "staged Book 2 schedule is forbidden once a live manifest exists"
        )

    return Book2CourseSchedule(
        schedule_version=1,
        weeks=weeks,
        declared_week_count=6,
        declared_total_minutes=1660,
        status="staged",
        global_weeks=tuple(global_weeks),
        covered_problem_ids=frozenset(),
    )


def _unit_contracts(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    manifests = {manifest.unit_id: manifest for manifest in load_unit_manifests(root)}
    for path in sorted(root.glob("units/*/manifest.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        estimates = raw.get("estimated_minutes") or {}
        unit = str(raw["unit"])
        manifest = manifests[unit]
        problem_contract = None
        if manifest.concept_sessions is not None and all(
            problem.minutes is not None and problem.after_session is not None
            for problem in manifest.practice
        ):
            problem_contract = {
                problem.id: {
                    "minutes": problem.minutes,
                    "after_session": problem.after_session,
                }
                for problem in manifest.practice
            }
        result[unit] = {
            "sessions": list(estimates.get("lesson_sessions") or []),
            "practice": estimates.get("practice"),
            "review": estimates.get("review"),
            "prereqs": list(raw.get("prereq_units") or []),
            "problems": problem_contract,
        }
    return result


def _mock_contracts(root: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    for path in sorted(root.glob("mocktests/*/manifest.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        result[str(raw["test"])] = int(raw["duration_minutes"])
    return result


def _check_chunks(
    kind: str,
    unit: str,
    rows: list[tuple[int, ScheduleAllocation]],
    expected_minutes: object,
    errors: list[str],
) -> None:
    if not rows:
        errors.append(f"missing {kind} allocation for {unit}")
        return
    chunks = [allocation.chunk for _, allocation in rows if allocation.chunk is not None]
    counts = Counter(chunks)
    for chunk, count in sorted(counts.items()):
        if count > 1:
            errors.append(f"duplicate {kind} chunk {unit}#{chunk}")
    expected_chunks = list(range(1, len(set(chunks)) + 1))
    if sorted(set(chunks)) != expected_chunks:
        errors.append(
            f"{kind} chunks for {unit} must be consecutive 1..{len(set(chunks))}"
        )
    actual = sum(allocation.minutes for _, allocation in rows)
    if type(expected_minutes) is not int or actual != expected_minutes:
        errors.append(f"{unit} {kind} minutes total {actual}; expected {expected_minutes}")


def _validate(
    root: Path,
    schedule: CourseSchedule,
    errors: list[str],
    *,
    enforce_calendar: bool = True,
) -> None:
    week_ids = [week.week for week in schedule.weeks]
    observed_last_week = max(week_ids, default=0)
    for week, count in sorted(Counter(week_ids).items()):
        if count > 1:
            errors.append(f"duplicate week {week}")
    if enforce_calendar:
        if (
            schedule.semester_week_counts is None
            or schedule.declared_week_count is None
        ):
            errors.append("canonical schedule requires a declared calendar")
            expected_week_ids: list[int] = []
        else:
            expected_week_ids = list(range(1, schedule.declared_week_count + 1))
            for expected in expected_week_ids:
                if expected not in week_ids:
                    errors.append(f"missing week {expected}")
            for unexpected in sorted(set(week_ids) - set(expected_week_ids)):
                errors.append(f"unexpected week {unexpected}")
            if week_ids != expected_week_ids:
                errors.append(
                    "week rows must be ordered consecutively "
                    f"1..{schedule.declared_week_count}"
                )

    assessment_weeks = {
        week.week
        for week in schedule.weeks
        for allocation in week.allocations
        if allocation.kind in {"mock", "debrief"}
    }
    final_assessment_week = (
        next(iter(assessment_weeks)) if len(assessment_weeks) == 1 else None
    )
    if enforce_calendar:
        if len(assessment_weeks) != 1:
            errors.append("schedule must have exactly one final-assessment week")
        elif final_assessment_week != schedule.declared_week_count:
            errors.append(
                f"final-assessment week {final_assessment_week} must be final week "
                f"{schedule.declared_week_count}"
            )
    for week in schedule.weeks:
        semester_1_weeks = (
            schedule.semester_week_counts[0]
            if schedule.semester_week_counts is not None
            else observed_last_week
        )
        expected_semester = 1 if week.week <= semester_1_weeks else 2
        if enforce_calendar and schedule.semester_week_counts is not None and week.semester != expected_semester:
            errors.append(
                f"week {week.week} semester {week.semester}; expected {expected_semester}"
            )
        total = sum(allocation.minutes for allocation in week.allocations)
        if enforce_calendar and not 450 <= total <= 500:
            errors.append(f"week {week.week} totals {total} minutes; requires 450-500")
        # The derived final-assessment week is the sole exception: its required mock/debrief replace
        # regular instruction. Positive allocation minutes make a nonzero session
        # count equivalent to positive lesson time.
        if enforce_calendar and week.week != final_assessment_week:
            lesson_count = sum(
                allocation.kind == "lesson-session"
                for allocation in week.allocations
            )
            if not 1 <= lesson_count <= 3:
                errors.append(
                    f"week {week.week} has {lesson_count} lesson sessions; "
                    "regular teaching weeks require 1-3"
                )
    if enforce_calendar:
        if schedule.semester_minutes is None or schedule.declared_total_minutes is None:
            errors.append(
                f"canonical {schedule.declared_week_count}-week schedule requires declared totals"
            )
        else:
            actual_first = sum(
                allocation.minutes
                for week in schedule.weeks
                if week.semester == 1
                for allocation in week.allocations
            )
            actual_second = sum(
                allocation.minutes
                for week in schedule.weeks
                if week.semester == 2
                for allocation in week.allocations
            )
            if (actual_first, actual_second) != schedule.semester_minutes:
                errors.append(
                    "semester totals do not match declared totals: "
                    f"actual {(actual_first, actual_second)}, declared {schedule.semester_minutes}"
                )
            if schedule.total_minutes != schedule.declared_total_minutes:
                errors.append(
                    f"scheduled total {schedule.total_minutes}; declared "
                    f"{schedule.declared_total_minutes}"
                )
            if sum(schedule.semester_minutes) != schedule.declared_total_minutes:
                errors.append("declared semester totals do not sum to declared scheduled total")

    units = _unit_contracts(root)
    mocks = _mock_contracts(root)
    flattened = [
        allocation for week in schedule.weeks for allocation in week.allocations
    ]
    indexed = list(enumerate(flattened))
    for _, allocation in indexed:
        if allocation.unit is not None and allocation.unit not in units:
            errors.append(f"unknown unit {allocation.unit}")
        if allocation.test is not None and allocation.test not in mocks:
            errors.append(
                f"{allocation.kind} allocation references unknown test {allocation.test}"
            )

    for unit, contract in units.items():
        lesson_rows = [
            (index, allocation)
            for index, allocation in indexed
            if allocation.kind == "lesson-session" and allocation.unit == unit
        ]
        session_counts = Counter(allocation.session for _, allocation in lesson_rows)
        for session, count in sorted(session_counts.items(), key=lambda item: int(item[0] or 0)):
            if count > 1:
                expected = contract["sessions"][int(session) - 1] if session else None
                rows = [allocation for _, allocation in lesson_rows if allocation.session == session]
                if all(row.minutes == expected for row in rows):
                    errors.append(f"duplicate lesson session {unit}#{session}")
                else:
                    errors.append(f"lesson session {unit}#{session} must appear exactly once")
        expected_sessions = contract["sessions"]
        for session, minutes in enumerate(expected_sessions, start=1):
            rows = [allocation for _, allocation in lesson_rows if allocation.session == session]
            if not rows:
                errors.append(f"unallocated lesson session {unit}#{session}")
            elif len(rows) == 1 and rows[0].minutes != minutes:
                errors.append(
                    f"{unit} lesson session {session} minutes {rows[0].minutes}; expected {minutes}"
                )
        for session in sorted(set(session_counts) - set(range(1, len(expected_sessions) + 1))):
            errors.append(f"unknown lesson session {unit}#{session}")
        session_weeks = {
            allocation.session: week.week
            for week in schedule.weeks
            for allocation in week.allocations
            if allocation.kind == "lesson-session"
            and allocation.unit == unit
            and allocation.session is not None
        }
        for session in range(1, len(expected_sessions)):
            if session not in session_weeks or session + 1 not in session_weeks:
                continue
            gap = session_weeks[session + 1] - session_weeks[session]
            if gap < 0:
                errors.append(
                    f"{unit} lesson session {session + 1} occurs in week "
                    f"{session_weeks[session + 1]} before session {session} in week "
                    f"{session_weeks[session]}"
                )
            elif gap > 2:
                errors.append(
                    f"{unit} lesson sessions {session} and {session + 1} are "
                    f"{gap} weeks apart; maximum gap is 2"
                )
        for kind in ("practice", "review"):
            rows = [
                (index, allocation)
                for index, allocation in indexed
                if allocation.kind == kind and allocation.unit == unit
            ]
            _check_chunks(kind, unit, rows, contract[kind], errors)
        problem_contract = contract["problems"]
        if problem_contract is not None:
            practice_rows = [
                (index, allocation)
                for index, allocation in indexed
                if allocation.kind == "practice" and allocation.unit == unit
            ]
            listed: list[str] = []
            for _, allocation in practice_rows:
                if allocation.problem_ids is None:
                    errors.append(
                        f"{unit} practice chunk {allocation.chunk} requires exact problem_ids"
                    )
                    continue
                listed.extend(allocation.problem_ids)
                known_minutes = [
                    problem_contract[problem_id]["minutes"]
                    for problem_id in allocation.problem_ids
                    if problem_id in problem_contract
                ]
                unknown = [
                    problem_id
                    for problem_id in allocation.problem_ids
                    if problem_id not in problem_contract
                ]
                for problem_id in unknown:
                    errors.append(f"{unit} practice chunk {allocation.chunk} has unknown {problem_id}")
                if not unknown and sum(known_minutes) != allocation.minutes:
                    errors.append(
                        f"{unit} practice chunk {allocation.chunk} problem minutes "
                        f"{sum(known_minutes)}; allocation minutes {allocation.minutes}"
                    )
            counts = Counter(listed)
            for problem_id in problem_contract:
                if counts[problem_id] != 1:
                    errors.append(
                        f"{problem_id} must appear exactly once in scheduled problem_ids; "
                        f"found {counts[problem_id]}"
                    )
            for problem_id in sorted(set(listed) - set(problem_contract)):
                if counts[problem_id] > 1:
                    errors.append(
                        f"{problem_id} must appear exactly once in scheduled problem_ids; "
                        f"found {counts[problem_id]}"
                    )
            session_indexes = {
                allocation.session: index
                for index, allocation in indexed
                if allocation.kind == "lesson-session" and allocation.unit == unit
            }
            for index, allocation in practice_rows:
                for problem_id in allocation.problem_ids or []:
                    if problem_id not in problem_contract:
                        continue
                    required = problem_contract[problem_id]["after_session"]
                    if required not in session_indexes or session_indexes[required] >= index:
                        errors.append(
                            f"{problem_id} requires session {required} before its scheduled "
                            "practice allocation"
                        )
        unit_rows = [
            allocation for _, allocation in indexed if allocation.unit == unit
        ]
        if (
            any(allocation.kind == "review" for allocation in unit_rows)
            and unit_rows[-1].kind != "review"
        ):
            errors.append(
                f"{unit} review allocation must be its final scheduled allocation"
            )

    # Completion includes the final practice/review chunk; prerequisites must be fully done.
    first_lesson: dict[str, int] = {}
    completion: dict[str, int] = {}
    for index, allocation in indexed:
        if allocation.unit in units:
            completion[allocation.unit] = index
            if allocation.kind == "lesson-session":
                first_lesson.setdefault(allocation.unit, index)
    syllabus = load_syllabus(root)
    for unit, start in first_lesson.items():
        for prereq in syllabus.units[unit].prereqs:
            if completion.get(prereq, -1) >= start:
                errors.append(f"prerequisite {prereq} must complete before {unit} starts")

    for test, duration in mocks.items():
        for kind, expected in (("mock", duration), ("debrief", 60)):
            rows = [allocation for allocation in flattened if allocation.kind == kind and allocation.test == test]
            if len(rows) != 1:
                errors.append(f"{kind} allocation for {test} must appear exactly once")
            elif rows[0].minutes != expected:
                verb = "match duration" if kind == "mock" else "be"
                errors.append(
                    f"{kind} allocation for {test} must {verb} {expected} minutes"
                )
    if len(flattened) < 2 or [row.kind for row in flattened[-2:]] != ["mock", "debrief"]:
        errors.append("mock and debrief must be the final scheduled events")


def check_schedule(root: str | Path) -> Report:
    root = Path(root).resolve()
    errors: list[str] = []
    try:
        schedule_policy(root).load(root, errors)
    except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        errors.append(f"course-schedule.yaml: {exc}")
    return Report(name="schedule-check", ok=not errors, errors=errors)


def load_validated_schedule(
    root: str | Path, *, enforce_calendar: bool = True
) -> CourseSchedule:
    root = Path(root).resolve()
    errors: list[str] = []
    schedule = schedule_policy(root).load(
        root, errors, enforce_calendar=enforce_calendar
    )
    if schedule is None or errors:
        raise ValueError("course-schedule.yaml: " + "; ".join(errors))
    return schedule
