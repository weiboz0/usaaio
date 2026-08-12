from __future__ import annotations

from pathlib import Path
from posixpath import normpath

import yaml

from tools.books import resolve_contained_path
from tools.model import Report, load_syllabus, load_unit_manifests


def check_coverage(root: str | Path) -> Report:
    root = Path(root)
    syllabus = load_syllabus(root)
    manifests = load_unit_manifests(root)
    vocabulary = set(syllabus.baseline) | set(syllabus.concepts)
    errors: list[str] = []
    for manifest in manifests:
        practice_minutes = [problem.minutes for problem in manifest.practice]
        declared_minutes = [minutes for minutes in practice_minutes if minutes is not None]
        if declared_minutes and len(declared_minutes) != len(practice_minutes):
            errors.append(
                f"{manifest.path}: practice minutes must be declared for every practice "
                "when any are present"
            )
        elif declared_minutes:
            raw_practice_minutes = _estimated_practice_minutes(manifest.path)
            actual_practice_minutes = sum(declared_minutes)
            if actual_practice_minutes != raw_practice_minutes:
                errors.append(
                    f"{manifest.path}: practice minutes sum to {actual_practice_minutes}; "
                    f"expected estimated_minutes.practice {raw_practice_minutes}"
                )
        unit = syllabus.units.get(manifest.unit_id)
        if unit is not None and unit.length == "double":
            lesson_count = len(manifest.lesson_sessions or [])
            if manifest.lesson_sessions is None:
                errors.append(
                    f"{manifest.path}: double-length unit {manifest.unit_id} has 0 lesson "
                    "sessions (missing estimated_minutes.lesson_sessions); requires 4-6"
                )
            elif not 4 <= lesson_count <= 6:
                errors.append(
                    f"{manifest.path}: double-length unit {manifest.unit_id} has "
                    f"{lesson_count} lesson sessions; requires 4-6"
                )
            distinct_ids = len({problem.id for problem in manifest.practice})
            if not 24 <= distinct_ids <= 30:
                errors.append(
                    f"{manifest.path}: double-length unit {manifest.unit_id} has "
                    f"{distinct_ids} distinct practice ids; requires 24-30"
                )
            distinct_paths = len({normpath(problem.path) for problem in manifest.practice})
            if not 24 <= distinct_paths <= 30:
                errors.append(
                    f"{manifest.path}: double-length unit {manifest.unit_id} has "
                    f"{distinct_paths} distinct practice paths; requires 24-30"
                )
        practice_ids: dict[str, set[str]] = {}
        practice_paths: dict[str, set[str]] = {}
        for problem in manifest.practice:
            for concept in set(problem.concepts):
                practice_ids.setdefault(concept, set()).add(problem.id)
                practice_paths.setdefault(concept, set()).add(problem.path)
        missing = set(manifest.concepts_taught) - set(practice_ids)
        if missing:
            errors.append(f"{manifest.path}: taught concepts without practice {sorted(missing)}")
        for concept in sorted(set(manifest.concepts_taught) - missing):
            count = min(len(practice_ids[concept]), len(practice_paths[concept]))
            if count < 3:
                errors.append(
                    f"{manifest.path}: taught concept {concept} has {count} tagged practice "
                    "problems; requires at least 3"
                )
        unit_dir = manifest.path.parent
        declared_solutions = [unit_dir / problem.solution_path for problem in manifest.practice]
        statement_only_book2 = (
            manifest.book == 2
            and manifest.solution_policy == "deferred"
            and declared_solutions
            and not any(path.is_file() for path in declared_solutions)
        )
        for problem in manifest.practice:
            for kind, relative in (
                ("practice", problem.path),
                ("solution", problem.solution_path),
            ):
                try:
                    resolve_contained_path(
                        root,
                        unit_dir.relative_to(root) / relative,
                        label=f"{manifest.path}: {kind} {problem.id}",
                    )
                except ValueError as exc:
                    if (
                        kind == "solution"
                        and statement_only_book2
                        and "path does not exist" in str(exc)
                    ):
                        continue
                    if "path does not exist" in str(exc):
                        errors.append(f"{manifest.path}: missing {kind} path {relative}")
                    else:
                        errors.append(str(exc))
            for concept in problem.concepts:
                if concept not in vocabulary:
                    errors.append(f"{manifest.path}: practice {problem.id} unknown concept {concept}")
    return Report(name="coverage-check", ok=not errors, errors=errors)


def _estimated_practice_minutes(manifest_path: Path) -> object:
    raw = yaml.safe_load(manifest_path.read_text())
    return (raw.get("estimated_minutes") or {}).get("practice")
