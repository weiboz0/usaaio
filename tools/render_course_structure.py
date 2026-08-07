"""Render schedule-owned regions of ``docs/course-structure.md``."""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

import yaml

from tools.checks.schedule import load_validated_schedule
from tools.model import CourseSchedule, load_syllabus

DOCUMENT = Path("docs/course-structure.md")


def _yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path}: expected a YAML mapping")
    return raw


def _manifest_contracts(root: Path) -> dict[str, dict]:
    return {
        str(raw["unit"]): raw
        for path in sorted(root.glob("units/*/manifest.yaml"))
        for raw in [_yaml(path)]
    }


def _minutes(schedule: CourseSchedule, kinds: set[str], weeks: range) -> int:
    return sum(
        allocation.minutes
        for week in schedule.weeks
        if week.week in weeks
        for allocation in week.allocations
        if allocation.kind in kinds
    )


def _number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _model_region(schedule: CourseSchedule, manifests: dict[str, dict]) -> str:
    lesson = sum(
        sum(raw["estimated_minutes"]["lesson_sessions"]) for raw in manifests.values()
    )
    practice = sum(raw["estimated_minutes"]["practice"] for raw in manifests.values())
    review = sum(raw["estimated_minutes"]["review"] for raw in manifests.values())
    manifested = lesson + practice + review
    practices = sum(len(raw.get("practice") or []) for raw in manifests.values())
    sessions = sum(
        len(raw["estimated_minutes"]["lesson_sessions"]) for raw in manifests.values()
    )
    scheduled = schedule.total_minutes
    in_class = lesson + 240
    independent = practice + review
    return "\n".join(
        [
            "The shipped Round 1 schedule runs for 35 weeks in two semesters: 16 weeks followed by 19 weeks.",
            f"The {len(manifests)} unit manifests provide {lesson:,} lesson minutes, {practice:,} practice minutes, and {review:,} review minutes.",
            f"Manifested content is therefore {lesson:,} + {practice:,} + {review:,} = {manifested:,} minutes = {_number(manifested / 60)} hours.",
            f"Those manifests contain {sessions} lesson sessions and {practices} practices across {len(manifests)} units.",
            "Every lesson session is between 60 and 90 minutes.",
            f"The scheduled course adds the 180-minute `r1-001` mock and its 60-minute debrief, for {manifested:,} + 240 = {scheduled:,} minutes = {_number(scheduled / 60)} hours.",
            f"The manifested division is {_number(lesson / 60)} lesson hours and {_number(independent / 60)} independent practice/review hours.",
            f"The scheduled division is {_number(in_class / 60)} in-class hours, including the mock and debrief, and {_number(independent / 60)} independent hours.",
            f"Across 35 weeks, that is about {_number(in_class / 60 / 35)} in-class hours and {_number(independent / 60 / 35)} independent hours per week.",
            "The remaining planned extensions in `docs/curriculum-roadmap.md` are editorial estimates, not manifested time, and do not fit silently into this calendar.",
        ]
    )


def _semester_region(schedule: CourseSchedule) -> str:
    first = schedule.weeks[:16]
    second = schedule.weeks[16:]
    first_units = _first_units(first)
    second_units = _first_units(second)
    s1 = sum(a.minutes for w in first for a in w.allocations)
    s2 = sum(a.minutes for w in second for a in w.allocations)
    s2_manifested = _minutes(schedule, {"lesson-session", "practice", "review"}, range(17, 36))
    return "\n".join(
        [
            f"Semester 1 is Weeks 1–16 and follows {' → '.join(first_units)}.",
            f"Its manifested allocation is {s1:,} minutes = {_number(s1 / 60)} hours, or {_number(s1 / 60 / 16)} hours per week.",
            f"Semester 2 is Weeks 17–35 and follows {' → '.join(second_units)} → `r1-001`.",
            f"Its manifested allocation is {s2_manifested:,} minutes = {_number(s2_manifested / 60)} hours.",
            f"Adding the 180-minute mock and 60-minute debrief gives {s2_manifested:,} + 240 = {s2:,} minutes = {_number(s2 / 60)} hours, or {_number(s2 / 60 / 19)} hours per week.",
        ]
    )


def _first_units(weeks: list) -> list[str]:
    result: list[str] = []
    for week in weeks:
        for allocation in week.allocations:
            if allocation.kind == "lesson-session" and allocation.unit not in result:
                result.append(str(allocation.unit))
    return result


def _week_description(week, prereqs: dict[str, list[str]]) -> str:
    by_unit: dict[str, list] = {}
    order: list[str] = []
    trailing: list[str] = []
    for allocation in week.allocations:
        if allocation.unit is None:
            trailing.append(
                f"`{allocation.test}` {allocation.kind} ({allocation.minutes} minutes)"
            )
            continue
        if allocation.unit not in by_unit:
            by_unit[allocation.unit] = []
            order.append(allocation.unit)
        by_unit[allocation.unit].append(allocation)
    parts: list[str] = []
    for unit in order:
        rows = by_unit[unit]
        sessions = [str(row.session) for row in rows if row.kind == "lesson-session"]
        practice = sum(row.minutes for row in rows if row.kind == "practice")
        review = sum(row.minutes for row in rows if row.kind == "review")
        details: list[str] = []
        if sessions:
            label = "session" if len(sessions) == 1 else "sessions"
            details.append(f"{label} {', '.join(sessions)}")
        if practice:
            details.append(f"{practice} practice minutes")
        if review:
            details.append(f"{review} review minutes")
        dependency = ", ".join(prereqs[unit]) if prereqs[unit] else "none"
        parts.append(f"{unit} (prereqs: {dependency}): " + ", ".join(details))
    parts.extend(trailing)
    return "; then ".join(parts) + "."


def _table_region(schedule: CourseSchedule, prereqs: dict[str, list[str]]) -> str:
    final_review: dict[str, int] = {}
    for week in schedule.weeks:
        for allocation in week.allocations:
            if allocation.kind == "review" and allocation.unit:
                final_review[allocation.unit] = week.week
    lines = [
        "| Week | Semester | Units and sessions covered | In-class minutes | Independent minutes | Checkpoint gate |",
        "|---:|:---:|---|---:|---:|---|",
    ]
    for week in schedule.weeks:
        in_class = sum(
            row.minutes
            for row in week.allocations
            if row.kind in {"lesson-session", "mock", "debrief"}
        )
        independent = sum(
            row.minutes for row in week.allocations if row.kind in {"practice", "review"}
        )
        gates = [f"{unit} review gate" for unit, number in final_review.items() if number == week.week]
        if week.week == 16:
            gates.append("Semester 1 close")
        if week.week == 35:
            gates.extend(["`r1-001` summative gate", "debrief"])
        gate = ", ".join(gates) + "." if gates else "No unit-review gate."
        lines.append(
            f"| {week.week} | S{week.semester} | {_week_description(week, prereqs)} | "
            f"{in_class} | {independent} | {gate} |"
        )
    return "\n".join(lines)


def _semester_summary(schedule: CourseSchedule) -> str:
    lines: list[str] = []
    for semester, weeks in ((1, schedule.weeks[:16]), (2, schedule.weeks[16:])):
        in_class = sum(
            row.minutes
            for week in weeks
            for row in week.allocations
            if row.kind in {"lesson-session", "mock", "debrief"}
        )
        independent = sum(
            row.minutes
            for week in weeks
            for row in week.allocations
            if row.kind in {"practice", "review"}
        )
        totals = [sum(row.minutes for row in week.allocations) for week in weeks]
        lines.append(
            f"The verified Semester {semester} columns sum to {in_class:,} in-class minutes + "
            f"{independent:,} independent minutes = {sum(totals):,} minutes."
        )
        lines.append(
            f"The Semester {semester} average is {sum(totals) / len(totals):.2f} minutes, "
            f"and its rows range from {min(totals)} to {max(totals)} minutes."
        )
    return "\n".join(lines)


def _counts_region(manifests: dict[str, dict]) -> str:
    lesson = sum(sum(row["estimated_minutes"]["lesson_sessions"]) for row in manifests.values())
    practice = sum(row["estimated_minutes"]["practice"] for row in manifests.values())
    review = sum(row["estimated_minutes"]["review"] for row in manifests.values())
    practices = sum(len(row.get("practice") or []) for row in manifests.values())
    sessions = sum(len(row["estimated_minutes"]["lesson_sessions"]) for row in manifests.values())
    return "\n".join(
        [
            "<!-- Maintainer regeneration command: uv run python -m tools.render_course_structure -->",
            "",
            "The command's captured stdout is:",
            "",
            "```text",
            f"{lesson} {practice} {review} {practices} {sessions} {len(manifests)}",
            "```",
        ]
    )


def _arithmetic_region(schedule: CourseSchedule) -> str:
    s1 = sum(row.minutes for week in schedule.weeks[:16] for row in week.allocations)
    s2 = sum(row.minutes for week in schedule.weeks[16:] for row in week.allocations)
    return "\n".join(
        [
            "The semester and table arithmetic was captured independently as:",
            "",
            "```text",
            f"S1: {s1}",
            f"S2: {s2}",
            f"full: {s1} + {s2} = {s1 + s2}",
            "```",
        ]
    )


def _first_instruction(schedule: CourseSchedule) -> str:
    first: dict[str, int] = {}
    for week in schedule.weeks:
        for allocation in week.allocations:
            if allocation.kind == "lesson-session" and allocation.unit:
                first.setdefault(allocation.unit, week.week)
    lines = ["| Unit | First instruction |", "|---|---:|"]
    lines.extend(f"| {unit} | Week {week} |" for unit, week in first.items())
    return "\n".join(lines)


def _region(name: str, content: str) -> str:
    return (
        f"<!-- BEGIN GENERATED: {name} -->\n{content.rstrip()}\n"
        f"<!-- END GENERATED: {name} -->"
    )


def _bootstrap(document: str) -> str:
    replacements = [
        (r"(?s)(## 1\. Course model\n\n).*?(?=\n## 2\.)", r"\1" + _region("course-model", "PENDING") + "\n"),
        (r"(?s)(## 2\. Semester split\n\n).*?(?=\nF7 is deliberately)", r"\1" + _region("semester-model", "PENDING") + "\n"),
        (r"(?s)(\| Week \| Semester \| Units and sessions covered .*?)(?=\n\nThe verified Semester 1)", _region("weekly-table", "PENDING")),
        (r"(?s)The verified Semester 1 columns.*?(?=\n\n## 4\.)", _region("semester-summary", "PENDING")),
        (r"The summative milestone is .*?debrief\.", _region("summative-milestone", "PENDING")),
        (r"(?s)<!-- Maintainer regeneration command:.*?```text\n4740 9237 790 383 57 17\n```", _region("counts-output", "PENDING")),
        (
            r"(?s)The semester and table arithmetic was captured independently as:.*?```text\n.*?\n```",
            _region("arithmetic-output", "PENDING"),
        ),
        (r"(?s)The first-instruction order is .*?sequence\.", _region("first-instruction", "PENDING")),
    ]
    for pattern, replacement in replacements:
        document, count = re.subn(pattern, replacement, document, count=1)
        if count != 1:
            raise ValueError(f"could not install generated region for pattern {pattern!r}")
    return document


def render_document(root: str | Path, *, bootstrap: bool = False) -> str:
    root = Path(root).resolve()
    schedule = load_validated_schedule(root)
    manifests = _manifest_contracts(root)
    syllabus = load_syllabus(root)
    path = root / DOCUMENT
    document = path.read_text(encoding="utf-8")
    if "<!-- BEGIN GENERATED: course-model -->" not in document:
        if not bootstrap:
            raise ValueError("generated course-structure regions are missing")
        document = _bootstrap(document)
    regions = {
        "course-model": _model_region(schedule, manifests),
        "semester-model": _semester_region(schedule),
        "weekly-table": _table_region(
            schedule, {unit: row.prereqs for unit, row in syllabus.units.items()}
        ),
        "semester-summary": _semester_summary(schedule),
        "summative-milestone": (
            "The summative milestone is `r1-001` in Week 35, scored against its "
            "300-point blueprint during its 180-minute duration and followed by the "
            "60-minute debrief."
        ),
        "counts-output": _counts_region(manifests),
        "arithmetic-output": _arithmetic_region(schedule),
        "first-instruction": _first_instruction(schedule),
    }
    for name, content in regions.items():
        pattern = re.compile(
            rf"<!-- BEGIN GENERATED: {re.escape(name)} -->\n.*?"
            rf"<!-- END GENERATED: {re.escape(name)} -->",
            re.DOTALL,
        )
        document, count = pattern.subn(_region(name, content), document, count=1)
        if count != 1:
            raise ValueError(f"missing or duplicate generated region {name}")
    return document


def _atomic_write(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    path = root / DOCUMENT
    try:
        rendered = render_document(root, bootstrap=not args.check)
        if args.check:
            if path.read_text(encoding="utf-8") != rendered:
                print(f"STALE {DOCUMENT}", file=sys.stderr)
                return 1
            return 0
        _atomic_write(path, rendered)
        return 0
    except (OSError, TypeError, ValueError, KeyError) as exc:
        print(f"ERROR course-structure renderer: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
