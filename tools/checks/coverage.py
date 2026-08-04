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
        practiced = {concept for problem in manifest.practice for concept in problem.concepts}
        missing = set(manifest.concepts_taught) - practiced
        if missing:
            errors.append(f"{manifest.path}: taught concepts without practice {sorted(missing)}")
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
