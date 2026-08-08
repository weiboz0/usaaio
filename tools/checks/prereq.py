from __future__ import annotations

from pathlib import Path

from tools.model import Report, Syllabus, load_mock_manifests, load_syllabus, load_unit_manifests


def transitive_prereqs(syllabus: Syllabus, unit_id: str) -> set[str]:
    seen: set[str] = set()

    def visit(uid: str) -> None:
        for prereq in syllabus.units[uid].prereqs:
            if prereq not in seen:
                seen.add(prereq)
                visit(prereq)

    visit(unit_id)
    return seen


def taught_closure(syllabus: Syllabus, unit_ids: list[str]) -> set[str]:
    closure_units = set(unit_ids)
    for unit_id in unit_ids:
        if unit_id in syllabus.units:
            closure_units |= transitive_prereqs(syllabus, unit_id)
    concepts = set(syllabus.baseline)
    for unit_id in closure_units:
        if unit_id in syllabus.units:
            concepts.update(syllabus.units[unit_id].teaches)
    return concepts


def _cycle_errors(syllabus: Syllabus) -> list[str]:
    errors: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(unit_id: str, path: list[str]) -> None:
        if unit_id in visiting:
            errors.append(f"cycle detected: {' -> '.join([*path, unit_id])}")
            return
        if unit_id in visited:
            return
        visiting.add(unit_id)
        for prereq in syllabus.units[unit_id].prereqs:
            if prereq in syllabus.units:
                visit(prereq, [*path, unit_id])
        visiting.remove(unit_id)
        visited.add(unit_id)

    for unit_id in syllabus.units:
        visit(unit_id, [])
    return errors


def check_prereq(root: str | Path) -> Report:
    syllabus = load_syllabus(root)
    units = load_unit_manifests(root)
    mocks = load_mock_manifests(root)
    errors: list[str] = []

    errors.extend(_cycle_errors(syllabus))
    taught: list[str] = []
    for unit in syllabus.units.values():
        for prereq in unit.prereqs:
            if prereq not in syllabus.units:
                errors.append(f"{unit.id}: unknown prereq unit {prereq}")
        taught.extend(unit.teaches)
        for concept in unit.teaches:
            if concept not in syllabus.concepts:
                errors.append(f"{unit.id}: teaches unknown concept {concept}")
    if len(taught) != len(set(taught)):
        errors.append("concepts must be taught exactly once")
    missing = set(syllabus.concepts) - set(taught)
    if missing:
        errors.append(f"concepts never taught: {sorted(missing)}")
    for concept, cluster in syllabus.concepts.items():
        if cluster not in syllabus.clusters:
            errors.append(f"{concept}: unknown cluster {cluster}")
    concept_owners = {
        concept: unit.id for unit in syllabus.units.values() for concept in unit.teaches
    }

    for manifest in units:
        unit = syllabus.units.get(manifest.unit_id)
        if unit is None:
            errors.append(f"{manifest.path}: unknown unit {manifest.unit_id}")
            continue
        if set(manifest.concepts_taught) != set(unit.teaches):
            errors.append(f"{manifest.path}: concepts_taught drift from syllabus")
        if set(manifest.prereq_units) != set(unit.prereqs):
            errors.append(f"{manifest.path}: prereq_units drift from syllabus")
        if manifest.concept_prerequisites != unit.concept_prerequisites:
            errors.append(
                f"{manifest.path}: concept_prerequisites drift from syllabus"
            )
        if manifest.book == 2 and manifest.concept_prerequisites != manifest.concepts_used:
            errors.append(
                f"{manifest.path}: concept_prerequisites must exactly equal concepts_used"
            )
        allowed = taught_closure(syllabus, list(unit.prereqs))
        for concept in manifest.concept_prerequisites:
            if concept not in allowed:
                errors.append(
                    f"{manifest.path}: concept prerequisite {concept} is outside the "
                    "prereq-unit taught closure"
                )
        for concept in manifest.concepts_used:
            if concept not in allowed:
                errors.append(f"{manifest.path}: uses untaught concept {concept}")
        practice_allowed = allowed | set(unit.teaches)
        declared_used = set(manifest.concepts_used)
        for problem in manifest.practice:
            for concept in problem.concepts:
                if concept not in practice_allowed:
                    owner = concept_owners.get(concept, "<unknown>")
                    errors.append(
                        f"{manifest.path}: practice problem {problem.id} tags concept {concept} "
                        f"owned by unit {owner}; not taught by unit {unit.id} or its prerequisites"
                    )
                if concept not in unit.teaches and concept not in declared_used:
                    errors.append(
                        f"{manifest.path}: practice problem {problem.id} tags foreign concept "
                        f"{concept} missing from concepts_used"
                    )

    shipped_units = {manifest.unit_id for manifest in units}
    for mock in mocks:
        for problem in mock.problems:
            unknown_units = [unit for unit in problem.units if unit not in syllabus.units]
            for unit in unknown_units:
                errors.append(f"{mock.path}: {problem.id} unknown unit {unit}")
            for unit in problem.units:
                if unit not in shipped_units:
                    errors.append(f"{mock.path}: {problem.id} unit {unit} has no shipped manifest")
            allowed = taught_closure(syllabus, [unit for unit in problem.units if unit in syllabus.units])
            for concept in problem.concepts:
                if concept not in allowed:
                    errors.append(f"{mock.path}: {problem.id} tests untaught concept {concept}")

    return Report(name="prereq-check", ok=not errors, errors=errors)
