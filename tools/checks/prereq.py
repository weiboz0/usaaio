from __future__ import annotations

from pathlib import Path

from tools.model import Report, Syllabus, load_mock_manifests, load_syllabus, load_unit_manifests


def transitive_prereqs(syllabus: Syllabus, unit_id: str) -> set[str]:
    seen: set[str] = set()

    def visit(uid: str) -> None:
        for prereq in syllabus.units[uid].prereqs:
            if prereq not in seen:
                seen.add(prereq)
                if prereq in syllabus.units:
                    visit(prereq)

    visit(unit_id)
    return seen


def taught_closure(
    syllabus: Syllabus,
    unit_ids: list[str],
    *,
    catalog=None,
    book=None,
) -> set[str]:
    closure_units = set(unit_ids)
    imported_concepts: set[str] = set()
    for unit_id in unit_ids:
        if ":" in unit_id:
            if catalog is None or book is None:
                raise ValueError(f"qualified prerequisite {unit_id!r} requires a book catalog")
            owner_id, local_id = unit_id.split(":", 1)
            if owner_id == book.id:
                raise ValueError(f"qualified prerequisite {unit_id!r} names the wrong owner")
            from tools.books import load_book_imports, resolve_qualified_import

            resolve_qualified_import(catalog, book, unit_id)
            imports = load_book_imports(book)
            if local_id not in imports.units:
                raise ValueError(f"qualified prerequisite {unit_id!r} is outside the allowlist")
            owner = catalog.by_id(owner_id)
            owner_syllabus = load_syllabus(owner.root)
            owner_units = {local_id, *transitive_prereqs(owner_syllabus, local_id)}
            taught = {
                concept
                for owner_unit in owner_units
                for concept in owner_syllabus.units[owner_unit].teaches
            }
            imported_concepts.update(
                f"{owner_id}:{concept}" for concept in taught & set(imports.concepts)
            )
            continue
        if unit_id in syllabus.units:
            closure_units |= transitive_prereqs(syllabus, unit_id)
        elif catalog is not None and book is not None:
            from tools.books import load_book_imports

            imports = load_book_imports(book)
            if unit_id in imports.units:
                raise ValueError(f"imported prerequisite {unit_id!r} must be qualified")
    concepts = set(syllabus.baseline)
    for unit_id in closure_units:
        if unit_id in syllabus.units:
            concepts.update(syllabus.units[unit_id].teaches)
    return concepts | imported_concepts


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
    selected_root = Path(root).resolve()
    syllabus = load_syllabus(selected_root)
    units = load_unit_manifests(selected_root)
    catalog = None
    book = None
    registry = selected_root.parent / "books.yaml"
    if registry.is_file():
        from tools.books import load_book_catalog

        catalog = load_book_catalog(selected_root.parent)
        book = next((candidate for candidate in catalog.books if candidate.root == selected_root), None)
    mocks = load_mock_manifests(selected_root, book_number=book.number if book else None)
    errors: list[str] = []

    errors.extend(_cycle_errors(syllabus))
    taught: list[str] = []
    for unit in syllabus.units.values():
        for prereq in unit.prereqs:
            if prereq not in syllabus.units and ":" not in prereq:
                errors.append(f"{unit.id}: unknown prereq unit {prereq}")
            elif ":" in prereq:
                try:
                    taught_closure(syllabus, [prereq], catalog=catalog, book=book)
                except ValueError as exc:
                    errors.append(f"{unit.id}: {exc}")
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
        allowed = taught_closure(
            syllabus, list(unit.prereqs), catalog=catalog, book=book
        )
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
            allowed = taught_closure(
                syllabus,
                [unit for unit in problem.units if unit in syllabus.units],
                catalog=catalog,
                book=book,
            )
            for concept in problem.concepts:
                if concept not in allowed:
                    errors.append(f"{mock.path}: {problem.id} tests untaught concept {concept}")

    return Report(name="prereq-check", ok=not errors, errors=errors)
