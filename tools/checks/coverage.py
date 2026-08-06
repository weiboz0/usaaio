from __future__ import annotations

from pathlib import Path

from tools.model import Report, load_syllabus, load_unit_manifests


def check_coverage(root: str | Path) -> Report:
    root = Path(root)
    syllabus = load_syllabus(root)
    manifests = load_unit_manifests(root)
    vocabulary = set(syllabus.baseline) | set(syllabus.concepts)
    errors: list[str] = []
    for manifest in manifests:
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
            distinct_paths = len({problem.path for problem in manifest.practice})
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
        for problem in manifest.practice:
            if not (unit_dir / problem.path).exists():
                errors.append(f"{manifest.path}: missing practice path {problem.path}")
            if not (unit_dir / problem.solution_path).exists():
                errors.append(f"{manifest.path}: missing solution path {problem.solution_path}")
            for concept in problem.concepts:
                if concept not in vocabulary:
                    errors.append(f"{manifest.path}: practice {problem.id} unknown concept {concept}")
    return Report(name="coverage-check", ok=not errors, errors=errors)
