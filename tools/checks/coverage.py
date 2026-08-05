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
