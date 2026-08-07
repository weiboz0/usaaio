"""Validate the canonical week-by-week course allocation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from tools.model import (
    CourseSchedule,
    Report,
    ScheduleAllocation,
    ScheduleWeek,
    load_syllabus,
)

KINDS = {"lesson-session", "practice", "review", "mock", "debrief"}
FINAL_MOCK_WEEK = 35


def _positive_integer(value: object, label: str, errors: list[str]) -> int | None:
    if type(value) is not int:
        errors.append(f"{label} must be an integer")
        return None
    if value <= 0:
        errors.append(f"{label} must be positive")
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
    allowed_keys = {"schedule_version", "weeks", "totals"}
    if not {"schedule_version", "weeks"} <= set(raw) or not set(raw) <= allowed_keys:
        errors.append(
            "course-schedule.yaml keys must be schedule_version, weeks, and optional totals"
        )
    version = raw.get("schedule_version")
    if type(version) is not int or version != 1:
        errors.append("schedule_version must be integer 1")
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
            if set(allocation) != expected_keys:
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
                    )
                )
        if week is not None and semester is not None:
            weeks.append(ScheduleWeek(week, semester, allocations))
    return CourseSchedule(1, weeks, semester_minutes, declared_total)


def _unit_contracts(root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(root.glob("units/*/manifest.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        estimates = raw.get("estimated_minutes") or {}
        result[str(raw["unit"])] = {
            "sessions": list(estimates.get("lesson_sessions") or []),
            "practice": estimates.get("practice"),
            "review": estimates.get("review"),
            "prereqs": list(raw.get("prereq_units") or []),
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
    for week, count in sorted(Counter(week_ids).items()):
        if count > 1:
            errors.append(f"duplicate week {week}")
    if enforce_calendar:
        for expected in range(1, 36):
            if expected not in week_ids:
                errors.append(f"missing week {expected}")
        for unexpected in sorted(set(week_ids) - set(range(1, 36))):
            errors.append(f"unexpected week {unexpected}")
        if week_ids != sorted(week_ids):
            errors.append("week rows must be ordered consecutively 1..35")
    for week in schedule.weeks:
        expected_semester = 1 if week.week <= 16 else 2
        if enforce_calendar and week.semester != expected_semester:
            errors.append(
                f"week {week.week} semester {week.semester}; expected {expected_semester}"
            )
        total = sum(allocation.minutes for allocation in week.allocations)
        if enforce_calendar and not 450 <= total <= 500:
            errors.append(f"week {week.week} totals {total} minutes; requires 450-500")
        # Week 35 is the sole exception: its required final mock and debrief replace
        # regular instruction. Positive allocation minutes make a nonzero session
        # count equivalent to positive lesson time.
        if enforce_calendar and week.week < FINAL_MOCK_WEEK:
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
            errors.append("canonical 35-week schedule requires declared totals")
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
        schedule = _parse_schedule(root, errors)
        if schedule is not None:
            _validate(root, schedule, errors)
    except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        errors.append(f"course-schedule.yaml: {exc}")
    return Report(name="schedule-check", ok=not errors, errors=errors)


def load_validated_schedule(
    root: str | Path, *, enforce_calendar: bool = True
) -> CourseSchedule:
    root = Path(root).resolve()
    errors: list[str] = []
    schedule = _parse_schedule(root, errors)
    if schedule is not None:
        _validate(root, schedule, errors, enforce_calendar=enforce_calendar)
    if schedule is None or errors:
        raise ValueError("course-schedule.yaml: " + "; ".join(errors))
    return schedule
