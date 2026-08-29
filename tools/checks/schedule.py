"""Validate the canonical week-by-week course allocation."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

from tools.books import BookSpec, load_book_catalog, resolve_contained_path
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
    ("B2-019-p11", "B2-019-p17", "B2-019-p18"),
    ("B2-019-p12", "B2-019-p19", "B2-019-p20", "B2-019-p22", "B2-019-p24"),
)
BOOK2_BASELINE_ALLOCATIONS = (
    (
        ("bridge-diagnostic", BOOK2_UNIT, None, None, 30, ()),
        ("lesson-session", BOOK2_UNIT, 1, None, 90, ()),
        ("practice", BOOK2_UNIT, None, 1, 135, BOOK2_WEEK_PROBLEMS[0]),
    ),
    (
        ("lesson-session", BOOK2_UNIT, 2, None, 90, ()),
        ("practice", BOOK2_UNIT, None, 2, 185, BOOK2_WEEK_PROBLEMS[1]),
    ),
    (
        ("lesson-session", BOOK2_UNIT, 3, None, 90, ()),
        ("practice", BOOK2_UNIT, None, 3, 330, BOOK2_WEEK_PROBLEMS[2]),
    ),
    (
        ("lesson-session", BOOK2_UNIT, 4, None, 90, ()),
        ("practice", BOOK2_UNIT, None, 4, 180, BOOK2_WEEK_PROBLEMS[3]),
    ),
    (
        ("lesson-session", BOOK2_UNIT, 5, None, 90, ()),
        ("practice", BOOK2_UNIT, None, 5, 290, BOOK2_WEEK_PROBLEMS[4]),
    ),
    (("review", BOOK2_UNIT, None, 1, 60, ()),),
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

    def __init__(self, expected_book_number: int = 2) -> None:
        self.expected_book_number = expected_book_number

    def load(
        self, root: Path, errors: list[str], *, enforce_calendar: bool = True
    ) -> Book2CourseSchedule | None:
        del enforce_calendar
        return _parse_book2_schedule(
            root,
            errors,
            expected_book_number=self.expected_book_number,
        )


def _registered_book(root: Path) -> BookSpec | None:
    for parent in root.parents:
        if not (parent / "books.yaml").is_file():
            continue
        catalog = load_book_catalog(parent)
        matches = [book for book in catalog.books if book.root == root]
        if len(matches) != 1:
            raise ValueError(f"selected root {root} is not uniquely registered in {parent}")
        return matches[0]
    return None


def _selected_book_identity(
    root: Path,
    *,
    book_spec: BookSpec | None,
    expected_book_number: int | None,
) -> tuple[int, str | None]:
    if book_spec is not None and book_spec.root != root:
        raise ValueError(
            f"BookSpec root {book_spec.root} does not match selected root {root}"
        )
    registered = _registered_book(root)
    if registered is not None:
        if book_spec is not None and book_spec != registered:
            raise ValueError(f"BookSpec for {book_spec.id} does not match books.yaml")
        if (
            expected_book_number is not None
            and expected_book_number != registered.number
        ):
            raise ValueError(
                f"expected book number {expected_book_number}; registered number is "
                f"{registered.number}"
            )
        return registered.number, registered.id
    if book_spec is not None:
        return book_spec.number, book_spec.id
    if type(expected_book_number) is not int or expected_book_number <= 0:
        raise ValueError(
            "unregistered schedule roots require expected_book_number or BookSpec"
        )
    return expected_book_number, None


def schedule_policy(
    root: str | Path,
    *,
    book_spec: BookSpec | None = None,
    expected_book_number: int | None = None,
):
    """Dispatch from trusted registry identity, never mutable schedule shape."""

    selected_root = Path(root).resolve()
    number, book_id = _selected_book_identity(
        selected_root,
        book_spec=book_spec,
        expected_book_number=expected_book_number,
    )
    if (book_id is None and number == 1) or (book_id == "book1" and number == 1):
        return Book1SchedulePolicy()
    if (book_id is None and number == 2) or book_id == "book2":
        return Book2SchedulePolicy(expected_book_number=number)
    raise ValueError(f"registered book number {number} has no schedule policy")


def scheduled_baseline_minutes(schedule: CourseSchedule) -> int:
    """Return only minutes backed by live content for reporting baselines."""

    if isinstance(schedule, Book2CourseSchedule) and schedule.status == "staged":
        return 0
    return schedule.total_minutes


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


def _require_book2_manifest_path(
    root: Path,
    unit_dir: Path,
    relative: object,
    *,
    label: str,
    errors: list[str],
    book_relative: bool = False,
    must_exist: bool = True,
) -> None:
    if not isinstance(relative, str) or not relative:
        errors.append(f"{label}: declared manifest path must be a nonempty string")
        return
    selected = Path(relative) if book_relative else unit_dir.relative_to(root) / relative
    try:
        resolved = resolve_contained_path(
            root,
            selected,
            label=f"{label}: declared manifest path",
            must_exist=must_exist,
        )
    except ValueError as exc:
        errors.append(str(exc))
        return
    if must_exist and not resolved.is_file():
        errors.append(f"{label}: declared manifest path must be a regular file: {relative}")


def _book2_solution_policy(
    unit: str, value: object, errors: list[str]
) -> tuple[bool, bool]:
    """Return whether the policy is valid and whether solutions must exist now."""
    if value == "required":
        return True, True
    expiry_date: date | None = None
    if isinstance(value, dict):
        expiry = value.get("expires")
        if isinstance(expiry, str):
            try:
                expiry_date = date.fromisoformat(expiry)
            except ValueError:
                pass
        if (
            value.get("status") == "deferred"
            and isinstance(value.get("plan"), str)
            and re.fullmatch(r"plan-[0-9]{3}", value["plan"]) is not None
            and isinstance(expiry, str)
            and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", expiry) is not None
            and expiry_date is not None
            and expiry_date >= datetime.now(UTC).date()
        ):
            return True, False
    errors.append(
        f"{unit}: solution_policy must be 'required' or a valid deferred mapping"
    )
    return False, True


def _discover_book2_manifest_contracts(
    root: Path, errors: list[str]
) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    try:
        units_root = resolve_contained_path(root, "units", label="Book 2 units directory")
    except ValueError as exc:
        errors.append(str(exc))
        return contracts
    if not units_root.is_dir():
        errors.append("Book 2 units path must be a regular directory")
        return contracts
    syllabus_units = load_syllabus(root).units
    for unit_dir in sorted(units_root.iterdir(), key=lambda item: item.name.encode()):
        # The tracked empty-directory sentinel is metadata, not a units/* unit entry.
        if unit_dir.name == ".gitkeep":
            if (
                unit_dir.is_symlink()
                or not unit_dir.is_file()
                or unit_dir.stat().st_size != 0
            ):
                errors.append(
                    f"{unit_dir}: .gitkeep sentinel must be a regular, "
                    "nonsymlink, empty file"
                )
            continue
        if unit_dir.is_symlink():
            errors.append(f"{unit_dir}: unit directory symlink is forbidden")
            continue
        if not unit_dir.is_dir():
            errors.append(f"units entry {unit_dir.name} must be a regular directory")
            continue
        try:
            resolve_contained_path(
                root,
                unit_dir.relative_to(root),
                label=f"Book 2 unit directory {unit_dir.name}",
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        candidates = [
            path
            for path in unit_dir.iterdir()
            if path.name.startswith("manifest") and path.suffix in {".yaml", ".yml"}
        ]
        manifest_path = unit_dir / "manifest.yaml"
        if len(candidates) != 1 or manifest_path not in candidates:
            errors.append(
                f"{unit_dir}: must contain exactly one regular manifest.yaml; "
                f"found {len(candidates)}"
            )
            continue
        if manifest_path.is_symlink():
            errors.append(f"{manifest_path}: manifest symlink is forbidden")
            continue
        if not manifest_path.is_file():
            errors.append(f"{manifest_path}: manifest.yaml must be a regular file")
            continue
        try:
            resolved_manifest = resolve_contained_path(
                root,
                manifest_path.relative_to(root),
                label="Book 2 manifest",
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not resolved_manifest.is_file():
            errors.append(f"{manifest_path}: manifest.yaml must be a regular file")
            continue
        if unit_dir.name not in syllabus_units:
            errors.append(f"unregistered Book 2 unit directory {unit_dir.name}")
        try:
            raw = _mapping(_read_yaml(manifest_path), str(manifest_path), errors)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if raw is None:
            continue
        unit = raw.get("unit")
        if unit != unit_dir.name:
            errors.append(
                f"{manifest_path}: manifest unit {unit!r} must match directory {unit_dir.name}"
            )
            continue
        if unit in contracts:
            errors.append(f"duplicate live Book 2 manifest unit {unit}")
            continue

        bridge = raw.get("bridge_diagnostic")
        if not isinstance(bridge, dict):
            errors.append(f"{unit}: manifest requires one bridge_diagnostic mapping")
            bridge = {}
        bridge_minutes = _positive_integer(
            bridge.get("minutes"), f"{unit} bridge_diagnostic.minutes", errors
        )
        _require_book2_manifest_path(
            root,
            unit_dir,
            bridge.get("path"),
            label=f"{unit} bridge_diagnostic.path",
            errors=errors,
        )

        estimated = raw.get("estimated_minutes")
        if not isinstance(estimated, dict):
            errors.append(f"{unit}: estimated_minutes must be a mapping")
            estimated = {}
        raw_sessions = estimated.get("lesson_sessions")
        sessions: list[int] = []
        if not isinstance(raw_sessions, list):
            errors.append(f"{unit}: estimated_minutes.lesson_sessions must be a list")
        else:
            for index, value in enumerate(raw_sessions, start=1):
                minutes = _positive_integer(
                    value, f"{unit} lesson session {index} minutes", errors
                )
                if minutes is not None:
                    sessions.append(minutes)
        lesson_paths = raw.get("lesson_paths")
        if not isinstance(lesson_paths, list) or len(lesson_paths) != len(sessions):
            errors.append(
                f"{unit}: lesson_paths must declare one path for every lesson session"
            )
            lesson_paths = lesson_paths if isinstance(lesson_paths, list) else []
        for index, relative in enumerate(lesson_paths, start=1):
            _require_book2_manifest_path(
                root,
                unit_dir,
                relative,
                label=f"{unit} lesson session {index}",
                errors=errors,
            )
        for field in ("overview_path", "review_path", "generator_path"):
            _require_book2_manifest_path(
                root,
                unit_dir,
                raw.get(field),
                label=f"{unit} {field}",
                errors=errors,
            )

        raw_practice = raw.get("practice")
        problems: dict[str, dict[str, int]] = {}
        if not isinstance(raw_practice, list):
            errors.append(f"{unit}: practice must be a list")
            raw_practice = []
        _, solutions_required = _book2_solution_policy(
            str(unit), raw.get("solution_policy", "required"), errors
        )
        for row_index, row in enumerate(raw_practice):
            if not isinstance(row, dict):
                errors.append(f"{unit} practice row {row_index} must be a mapping")
                continue
            problem_id = row.get("id")
            path_label = (
                problem_id
                if isinstance(problem_id, str) and problem_id
                else f"{unit} practice row {row_index}"
            )
            _require_book2_manifest_path(
                root,
                unit_dir,
                row.get("path"),
                label=f"{path_label} path",
                errors=errors,
            )
            if "solution_path" in row or solutions_required:
                _require_book2_manifest_path(
                    root,
                    unit_dir,
                    row.get("solution_path"),
                    label=f"{path_label} solution_path",
                    errors=errors,
                    must_exist=solutions_required,
                )
            if not isinstance(problem_id, str) or not problem_id:
                errors.append(f"{unit} practice row {row_index} id must be a string")
                continue
            if problem_id in problems:
                errors.append(f"duplicate manifest practice ID {problem_id}")
            minutes = _positive_integer(
                row.get("minutes"), f"{problem_id} manifest minutes", errors
            )
            after_session = _positive_integer(
                row.get("after_session"), f"{problem_id} after_session", errors
            )
            if minutes is not None and after_session is not None:
                problems[problem_id] = {
                    "minutes": minutes,
                    "after_session": after_session,
                }

        claims = raw.get("coverage_claims", [])
        if not isinstance(claims, list):
            errors.append(f"{unit}: coverage_claims must be a list")
            claims = []
        for claim_index, claim in enumerate(claims):
            if not isinstance(claim, dict):
                errors.append(
                    f"{unit}: coverage_claims row {claim_index} must be a mapping"
                )
                continue
            evidence = claim.get("evidence_by_modality", {})
            if not isinstance(evidence, dict):
                errors.append(
                    f"{unit}: coverage_claims row {claim_index} "
                    "evidence_by_modality must be a mapping"
                )
                continue
            for modality_name, modality in evidence.items():
                if not isinstance(modality, dict):
                    errors.append(
                        f"{unit}: coverage_claims row {claim_index} modality "
                        f"{modality_name} must be a mapping"
                    )
                    continue
                anchors = modality.get("lesson_anchors", [])
                if not isinstance(anchors, list):
                    errors.append(
                        f"{unit}: coverage_claims row {claim_index} "
                        "lesson_anchors must be a list"
                    )
                    continue
                for anchor_index, anchor in enumerate(anchors):
                    if not isinstance(anchor, dict):
                        errors.append(
                            f"{unit}: coverage_claims row {claim_index} "
                            f"lesson_anchors row {anchor_index} must be a mapping"
                        )
                        continue
                    _require_book2_manifest_path(
                        root,
                        unit_dir,
                        anchor.get("path"),
                        label=f"{unit} coverage lesson anchor",
                        errors=errors,
                        book_relative=True,
                    )

        expected_practice = sum(problem["minutes"] for problem in problems.values())
        if estimated.get("practice") != expected_practice:
            errors.append(
                f"{unit} manifest estimated practice minutes "
                f"{estimated.get('practice')}; practice rows total {expected_practice}"
            )
        lesson_total = sum(sessions)
        if estimated.get("lesson") != lesson_total:
            errors.append(
                f"{unit} manifest estimated lesson minutes {estimated.get('lesson')}; "
                f"lesson sessions total {lesson_total}"
            )
        review_minutes = _positive_integer(
            estimated.get("review"), f"{unit} estimated review minutes", errors
        )
        contracts[str(unit)] = {
            "bridge": bridge_minutes,
            "sessions": sessions,
            "practice": expected_practice,
            "review": review_minutes,
            "problems": problems,
        }
    return contracts


def _book2_allocation_signature(
    allocation: ScheduleAllocation,
) -> tuple[str, str | None, int | None, int | None, int, tuple[str, ...]]:
    return (
        allocation.kind,
        allocation.unit,
        allocation.session,
        allocation.chunk,
        allocation.minutes,
        tuple(allocation.problem_ids or ()),
    )


def _validate_book2_unit_topology(
    schedule: Book2CourseSchedule,
    unit: str,
    contract: dict[str, Any],
    errors: list[str],
) -> None:
    locations = [
        (week.week, allocation_index, allocation)
        for week in schedule.weeks
        for allocation_index, allocation in enumerate(week.allocations)
        if allocation.unit == unit
    ]
    if not locations:
        return
    session_count = len(contract["sessions"])
    first_week = min(week for week, _, _ in locations)
    expected_weeks = list(range(first_week, first_week + session_count + 1))
    observed_weeks = sorted({week for week, _, _ in locations})
    if observed_weeks != expected_weeks:
        errors.append(
            f"{unit} allocation weeks must be {session_count + 1} consecutive weeks"
        )

    bridge_locations = [
        row for row in locations if row[2].kind == "bridge-diagnostic"
    ]
    lesson_locations = [row for row in locations if row[2].kind == "lesson-session"]
    if len(bridge_locations) == 1 and lesson_locations:
        bridge_week, bridge_index, _ = bridge_locations[0]
        first_lesson_week, first_lesson_index, _ = min(
            lesson_locations, key=lambda row: (row[0], row[1])
        )
        if (
            bridge_week != first_week
            or first_lesson_week != first_week
            or bridge_index >= first_lesson_index
        ):
            errors.append(
                f"{unit} bridge diagnostic must precede instruction in its first week"
            )

    observed_sessions = [
        (week, allocation.session) for week, _, allocation in lesson_locations
    ]
    expected_sessions = [
        (first_week + offset, offset + 1) for offset in range(session_count)
    ]
    if observed_sessions != expected_sessions:
        errors.append(
            f"{unit} lesson sessions must appear once in strictly increasing order, "
            "one per instructional week"
        )

    practice_locations = [row for row in locations if row[2].kind == "practice"]
    observed_practices = [
        (week, allocation.chunk) for week, _, allocation in practice_locations
    ]
    expected_practices = [
        (first_week + offset, offset + 1) for offset in range(session_count)
    ]
    if observed_practices != expected_practices:
        errors.append(
            f"{unit} practice chunks must cover its instructional weeks in order, "
            "one per declared session"
        )

    review_locations = [row for row in locations if row[2].kind == "review"]
    if len(review_locations) == 1:
        review_week, _, review = review_locations[0]
        scheduled_week = next(
            (week for week in schedule.weeks if week.week == review_week), None
        )
        if (
            review_week != first_week + session_count
            or scheduled_week is None
            or scheduled_week.allocations != [review]
        ):
            errors.append(
                f"{unit} review must be the only final allocation in the following "
                "unit week"
            )


def _validate_live_book2_ledger(
    schedule: Book2CourseSchedule,
    contracts: dict[str, dict[str, Any]],
    errors: list[str],
) -> frozenset[str]:
    if BOOK2_UNIT not in contracts:
        errors.append(f"live Book 2 schedule requires the {BOOK2_UNIT} manifest")
    flattened = [
        allocation for week in schedule.weeks for allocation in week.allocations
    ]
    indexed = list(enumerate(flattened))
    global_problem_ids = [
        problem_id
        for allocation in flattened
        for problem_id in allocation.problem_ids or []
    ]
    global_counts = Counter(global_problem_ids)
    for problem_id, count in sorted(global_counts.items()):
        if count > 1:
            errors.append(
                f"{problem_id} must appear exactly once in scheduled problem_ids; found {count}"
            )

    baseline_reviews = [
        index
        for index, allocation in indexed
        if allocation.unit == BOOK2_UNIT and allocation.kind == "review"
    ]
    baseline_review = baseline_reviews[0] if len(baseline_reviews) == 1 else None
    for index, allocation in indexed:
        if (
            allocation.unit is not None
            and allocation.unit != BOOK2_UNIT
            and baseline_review is not None
            and index <= baseline_review
        ):
            errors.append(
                f"{allocation.unit} {allocation.kind} allocation must begin after "
                f"{BOOK2_UNIT} final review"
            )

    covered: set[str] = set()
    for unit, contract in contracts.items():
        _validate_book2_unit_topology(schedule, unit, contract, errors)
        unit_rows = [
            (index, allocation)
            for index, allocation in indexed
            if allocation.unit == unit
        ]
        bridge_rows = [
            (index, allocation)
            for index, allocation in unit_rows
            if allocation.kind == "bridge-diagnostic"
        ]
        if len(bridge_rows) != 1:
            errors.append(f"bridge diagnostic allocation for {unit} must appear exactly once")
        elif bridge_rows[0][1].minutes != contract["bridge"]:
            errors.append(
                f"{unit} bridge diagnostic minutes {bridge_rows[0][1].minutes}; "
                f"expected {contract['bridge']}"
            )

        lesson_rows = [
            (index, allocation)
            for index, allocation in unit_rows
            if allocation.kind == "lesson-session"
        ]
        for session, minutes in enumerate(contract["sessions"], start=1):
            rows = [row for row in lesson_rows if row[1].session == session]
            if not rows:
                errors.append(f"unallocated lesson session {unit}#{session}")
            elif len(rows) != 1:
                errors.append(f"lesson session {unit}#{session} must appear exactly once")
            elif rows[0][1].minutes != minutes:
                errors.append(
                    f"{unit} lesson session {session} minutes {rows[0][1].minutes}; "
                    f"expected {minutes}"
                )
        expected_sessions = set(range(1, len(contract["sessions"]) + 1))
        for session in sorted(
            {allocation.session for _, allocation in lesson_rows if allocation.session is not None}
            - expected_sessions
        ):
            errors.append(f"unknown lesson session {unit}#{session}")

        practice_rows = [
            (index, allocation)
            for index, allocation in unit_rows
            if allocation.kind == "practice"
        ]
        _check_chunks("practice", unit, practice_rows, contract["practice"], errors)
        listed: list[str] = []
        for index, allocation in practice_rows:
            if allocation.problem_ids is None:
                errors.append(
                    f"{unit} practice chunk {allocation.chunk} requires exact problem_ids"
                )
                continue
            listed.extend(allocation.problem_ids)
            unknown = [
                problem_id
                for problem_id in allocation.problem_ids
                if problem_id not in contract["problems"]
            ]
            for problem_id in unknown:
                errors.append(
                    f"{unit} practice chunk {allocation.chunk} has unknown {problem_id}"
                )
            if not unknown:
                expected_minutes = sum(
                    contract["problems"][problem_id]["minutes"]
                    for problem_id in allocation.problem_ids
                )
                if expected_minutes != allocation.minutes:
                    errors.append(
                        f"{unit} practice chunk {allocation.chunk} problem minutes "
                        f"{expected_minutes}; allocation minutes {allocation.minutes}"
                    )
            for problem_id in allocation.problem_ids:
                problem = contract["problems"].get(problem_id)
                if problem is None:
                    continue
                lesson_indexes = [
                    lesson_index
                    for lesson_index, lesson in lesson_rows
                    if lesson.session == problem["after_session"]
                ]
                if not lesson_indexes or lesson_indexes[0] >= index:
                    errors.append(
                        f"{problem_id} requires session {problem['after_session']} before "
                        "its scheduled practice allocation"
                    )
        counts = Counter(listed)
        if counts != Counter(contract["problems"].keys()):
            errors.append(
                "live manifest problem IDs must exactly match scheduled problem_ids"
            )
        for problem_id, problem in contract["problems"].items():
            if counts[problem_id] != 1:
                errors.append(
                    f"{problem_id} must appear exactly once in scheduled problem_ids; "
                    f"found {counts[problem_id]}"
                )
            expected = problem["minutes"]
            if type(expected) is not int:
                errors.append(f"{problem_id} manifest minutes must be an integer")
        covered.update(problem_id for problem_id in contract["problems"] if counts[problem_id] == 1)

        review_rows = [
            (index, allocation)
            for index, allocation in unit_rows
            if allocation.kind == "review"
        ]
        if len(review_rows) != 1:
            errors.append(f"review allocation for {unit} must appear exactly once")
        elif review_rows[0][1].minutes != contract["review"]:
            errors.append(
                f"{unit} review minutes {review_rows[0][1].minutes}; "
                f"expected {contract['review']}"
            )
        if unit_rows and unit_rows[-1][1].kind != "review":
            errors.append(f"{unit} review allocation must be its final scheduled allocation")
    return frozenset(covered)


def _parse_book2_schedule(
    root: Path,
    errors: list[str],
    *,
    expected_book_number: int,
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
    if type(raw.get("book")) is not int:
        errors.append("Book 2 schedule book must be an integer")
    elif raw.get("book") != expected_book_number:
        errors.append(
            f"schedule book {raw.get('book')} does not match registered book number "
            f"{expected_book_number}"
        )
    status = raw.get("status")
    if status not in {"staged", "live"}:
        errors.append("Book 2 schedule status must be staged or live")
    _exact_integer(
        raw.get("starts_after_global_week"),
        "Book 2 schedule starts_after_global_week",
        40,
        errors,
    )
    declared_weeks = _positive_integer(
        raw.get("total_book_weeks"), "Book 2 schedule total_book_weeks", errors
    )
    declared_minutes = _positive_integer(
        raw.get("total_minutes"), "Book 2 schedule total_minutes", errors
    )
    contracts = _discover_book2_manifest_contracts(root, errors)

    marker = raw.get("final_assessment")
    if isinstance(marker, dict):
        marker_week = marker.get("after_book_week")
        if type(marker_week) is not int:
            errors.append("Book 2 final_assessment.after_book_week must be an integer")
        elif declared_weeks is not None and marker_week != declared_weeks:
            errors.append(
                f"planned final assessment marker must follow book week {declared_weeks}"
            )
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
    allowed_units = set(contracts) if status == "live" else {BOOK2_UNIT}
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
            label = f"Book 2 week {book_week or row_index + 1} allocation {allocation_index}"
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
            elif unit not in allowed_units:
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

    expected_local = list(range(1, (declared_weeks or 0) + 1))
    expected_global = list(range(41, 41 + (declared_weeks or 0)))
    if local_weeks != expected_local:
        errors.append(
            f"Book 2 book_week rows must be ordered consecutively 1..{declared_weeks}"
        )
    if global_weeks != expected_global:
        errors.append(
            f"Book 2 global_week rows must be 41..{40 + (declared_weeks or 0)} in order"
        )
    actual_total = sum(
        allocation.minutes for week in weeks for allocation in week.allocations
    )
    if declared_minutes is not None and declared_minutes != actual_total:
        errors.append(f"Book 2 declared total {declared_minutes}; actual {actual_total}")

    schedule = Book2CourseSchedule(
        schedule_version=1,
        weeks=weeks,
        declared_week_count=declared_weeks,
        declared_total_minutes=declared_minutes,
        status=str(status),
        global_weeks=tuple(global_weeks),
    )
    baseline = tuple(
        tuple(_book2_allocation_signature(allocation) for allocation in week.allocations)
        for week in weeks[:6]
    )
    if baseline != BOOK2_BASELINE_ALLOCATIONS:
        errors.append("B2-019 pre-existing ledger must remain unchanged")
    if status == "staged":
        if contracts:
            errors.append("staged Book 2 schedule is forbidden once a live manifest exists")
        if actual_total != 1660:
            errors.append(f"Book 2 staged scheduled total {actual_total}; expected 1660")
        return schedule
    covered = _validate_live_book2_ledger(schedule, contracts, errors)
    return Book2CourseSchedule(
        schedule_version=1,
        weeks=weeks,
        declared_week_count=declared_weeks,
        declared_total_minutes=declared_minutes,
        status=str(status),
        global_weeks=tuple(global_weeks),
        covered_problem_ids=covered,
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


def check_schedule(
    root: str | Path,
    *,
    book_spec: BookSpec | None = None,
    expected_book_number: int | None = None,
) -> Report:
    root = Path(root).resolve()
    errors: list[str] = []
    try:
        schedule_policy(
            root,
            book_spec=book_spec,
            expected_book_number=expected_book_number,
        ).load(root, errors)
    except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        errors.append(f"course-schedule.yaml: {exc}")
    return Report(name="schedule-check", ok=not errors, errors=errors)


def load_validated_schedule(
    root: str | Path,
    *,
    enforce_calendar: bool = True,
    book_spec: BookSpec | None = None,
    expected_book_number: int | None = None,
) -> CourseSchedule:
    root = Path(root).resolve()
    errors: list[str] = []
    schedule = schedule_policy(
        root,
        book_spec=book_spec,
        expected_book_number=expected_book_number,
    ).load(
        root, errors, enforce_calendar=enforce_calendar
    )
    if schedule is None or errors:
        raise ValueError("course-schedule.yaml: " + "; ".join(errors))
    return schedule
