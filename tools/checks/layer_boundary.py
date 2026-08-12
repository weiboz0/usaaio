"""Enforce the Book 1 / Book 2 ownership and evidence boundary."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from tools.books import resolve_contained_path
from tools.checks.prereq import taught_closure
from tools.model import (
    KnowledgePoint,
    Report,
    UnitManifest,
    load_roadmap,
    load_syllabus,
    load_unit_manifests,
)

MINIMUM_DIRECT_PRACTICES = 3
BOOK2_LAYER = "round-2-extension"


def _book2_number(unit_id: str) -> int | None:
    match = re.fullmatch(r"B2-([0-9]{3})-.+", unit_id)
    return int(match.group(1)) if match else None


def _check_bridge(
    root: Path, manifest: UnitManifest, errors: list[str]
) -> None:
    diagnostic = manifest.bridge_diagnostic
    if diagnostic is None:
        errors.append(f"{manifest.path}: bridge_diagnostic is required for Book 2")
        return
    referenced = set(diagnostic.referenced_concepts)
    if not referenced:
        errors.append(f"{manifest.path}: bridge_diagnostic referenced_concepts must be nonempty")
    if not referenced <= set(manifest.concepts_used):
        errors.append(
            f"{manifest.path}: bridge_diagnostic referenced_concepts must be a subset "
            "of concepts_used"
        )
    if referenced & set(manifest.concepts_taught):
        errors.append(
            f"{manifest.path}: bridge_diagnostic referenced_concepts must be disjoint "
            "from concepts_taught"
        )
    try:
        diagnostic_path = resolve_contained_path(
            root,
            manifest.path.parent.relative_to(root) / diagnostic.path,
            label=f"{manifest.path}: bridge_diagnostic",
        )
    except ValueError:
        errors.append(f"{manifest.path}: bridge_diagnostic requires a local existing path")
    else:
        if not diagnostic_path.is_file():
            errors.append(
                f"{manifest.path}: bridge_diagnostic requires a local existing path"
            )


def _check_compute(root: Path, manifest: UnitManifest, errors: list[str]) -> None:
    unit_dir = manifest.path.parent
    declared_solutions = [unit_dir / problem.solution_path for problem in manifest.practice]
    statement_only = declared_solutions and not any(
        path.is_file() for path in declared_solutions
    )
    for problem in manifest.practice:
        label = f"{manifest.path}: practice {problem.id}"
        if problem.compute.seed is None:
            errors.append(f"{label} compute.seed is required")
        if problem.compute.policy != "cpu":
            errors.append(f"{label} unsupported compute.policy {problem.compute.policy!r}")
        if problem.compute.policy == "cpu":
            try:
                solution = resolve_contained_path(
                    root,
                    manifest.path.parent.relative_to(root) / problem.solution_path,
                    label=f"{label} solution",
                )
            except ValueError:
                if not statement_only:
                    errors.append(f"{label} cpu task requires a local solution path")
            else:
                if not solution.is_file() and not statement_only:
                    errors.append(f"{label} cpu task requires a local solution path")


def _check_claims(
    root: Path,
    manifest: UnitManifest,
    roadmap_points: dict[str, KnowledgePoint],
    errors: list[str],
) -> None:
    claims = {claim.knowledge_point: claim for claim in manifest.coverage_claims}
    if len(claims) != len(manifest.coverage_claims):
        errors.append(f"{manifest.path}: duplicate coverage_claims knowledge_point")
    required_claims = {
        point.id
        for point in roadmap_points.values()
        if point.coverage == "covered" and point.destination == manifest.unit_id
    }
    for point_id in sorted(required_claims - set(claims), key=str.encode):
        errors.append(
            f"{manifest.path}: coverage_claims missing covered roadmap point {point_id}"
        )
    for point_id in sorted(set(claims) - required_claims, key=str.encode):
        errors.append(
            f"{manifest.path}: coverage claim {point_id} has no covered roadmap point "
            f"for destination {manifest.unit_id}"
        )
    practice_by_id = {problem.id: problem for problem in manifest.practice}
    taught = set(manifest.concepts_taught)
    session_count = len(manifest.lesson_sessions or [])

    for point_id, claim in claims.items():
        point = roadmap_points.get(point_id)
        if point is None:
            errors.append(f"{manifest.path}: coverage claim {point_id} is not in coverage map")
            continue
        if point.layer != BOOK2_LAYER:
            errors.append(f"{manifest.path}: coverage claim {point_id} is not Round 2")
        if point.destination != manifest.unit_id:
            errors.append(
                f"{manifest.path}: coverage claim {point_id} destination must be "
                f"{manifest.unit_id}"
            )
        evidence_concepts = set(claim.evidence_concepts)
        if not evidence_concepts or not evidence_concepts <= taught:
            errors.append(
                f"{manifest.path}: coverage claim {point_id} evidence_concepts must be "
                "a nonempty subset of concepts_taught"
            )
        required_modalities = set(point.evidence_by_modality)
        if set(claim.modalities) != required_modalities:
            errors.append(
                f"{manifest.path}: coverage claim {point_id} modalities must exactly match "
                "the coverage-map requirement"
            )
        if set(claim.evidence_by_modality) != set(claim.modalities):
            errors.append(
                f"{manifest.path}: coverage claim {point_id} evidence_by_modality keys "
                "must exactly match modalities"
            )
        if claim.evidence_by_modality != point.evidence_by_modality:
            errors.append(
                f"{manifest.path}: coverage claim {point_id} evidence must exactly match "
                "the coverage map"
            )
        if session_count and claim.first_session > session_count:
            errors.append(
                f"{manifest.path}: coverage claim {point_id} first_session is outside "
                "the lesson-session inventory"
            )

        qualifying: set[str] = set()
        for modality, evidence in claim.evidence_by_modality.items():
            if not evidence.lesson_anchors:
                errors.append(
                    f"{manifest.path}: coverage claim {point_id}/{modality} requires "
                    "a lesson anchor"
                )
            for anchor in evidence.lesson_anchors:
                anchor_path = (root / anchor.path).resolve()
                if (
                    anchor.role != "primary"
                    or not anchor.heading.strip()
                    or anchor.cell_ordinal <= 0
                    or not anchor_path.is_relative_to(root)
                    or not anchor_path.is_file()
                ):
                    errors.append(
                        f"{manifest.path}: coverage claim {point_id}/{modality} has "
                        "an invalid primary lesson anchor"
                    )
            for reference in evidence.practices:
                problem = practice_by_id.get(reference.id)
                if (
                    reference.role == "primary"
                    and problem is not None
                    and set(problem.concepts) & evidence_concepts
                ):
                    qualifying.add(reference.id)
        if len(qualifying) < MINIMUM_DIRECT_PRACTICES:
            errors.append(
                f"{manifest.path}: coverage claim {point_id} requires at least 3 "
                "qualifying practice ids"
            )

        for dependency in point.depends_on:
            dependency_claim = claims.get(dependency)
            if dependency_claim is not None and claim.first_session <= dependency_claim.first_session:
                errors.append(
                    f"{manifest.path}: coverage claim {point_id} first_session must follow "
                    "same-unit knowledge-point dependencies"
                )

    tag_counts = Counter(
        concept
        for problem in manifest.practice
        for concept in set(problem.concepts) & taught
    )
    for concept in sorted(taught):
        if tag_counts[concept] < MINIMUM_DIRECT_PRACTICES:
            errors.append(
                f"{manifest.path}: owned concept {concept} requires at least 3 direct "
                "practice tags"
            )


def check_layer_boundary(root: str | Path) -> Report:
    root = Path(root).resolve()
    try:
        syllabus = load_syllabus(root)
        manifests = load_unit_manifests(root)
        roadmap = load_roadmap(root)
        catalog = None
        book = None
        if (root.parent / "books.yaml").is_file():
            from tools.books import load_book_catalog

            catalog = load_book_catalog(root.parent)
            book = next(
                (candidate for candidate in catalog.books if candidate.root == root),
                None,
            )
    except (KeyError, OSError, TypeError, ValueError) as exc:
        return Report(name="layer-boundary-check", ok=False, errors=[str(exc)])
    errors: list[str] = []

    concept_owner = {
        concept: unit for unit in syllabus.units.values() for concept in unit.teaches
    }
    roadmap_points = {point.id: point for point in roadmap.knowledge_points}

    for manifest in manifests:
        unit = syllabus.units.get(manifest.unit_id)
        if unit is None:
            errors.append(f"{manifest.path}: unknown syllabus unit {manifest.unit_id}")
            continue
        if manifest.book == 1:
            for claim in manifest.coverage_claims:
                point = roadmap_points.get(claim.knowledge_point)
                if point is not None and point.layer == BOOK2_LAYER:
                    errors.append(
                        f"{manifest.path}: Book 1 artifact claims Round 2 coverage "
                        f"for {claim.knowledge_point}"
                    )
            continue

        if (manifest.book, manifest.round, manifest.layer, manifest.track) != (
            2,
            2,
            BOOK2_LAYER,
            "extension",
        ):
            errors.append(f"{manifest.path}: invalid Book 2 layer contract")
        if (
            manifest.book,
            manifest.round,
            manifest.layer,
            manifest.track,
        ) != (unit.book, unit.round, unit.layer, unit.track):
            errors.append(f"{manifest.path}: Book/layer/round/track drift from syllabus")
        if manifest.prereq_units != unit.prereqs:
            errors.append(f"{manifest.path}: prereq_units drift from syllabus")
        if manifest.concept_prerequisites != unit.concept_prerequisites:
            errors.append(f"{manifest.path}: concept_prerequisites drift from syllabus")
        if manifest.concept_prerequisites != manifest.concepts_used:
            errors.append(
                f"{manifest.path}: concept_prerequisites must exactly equal concepts_used"
            )
        try:
            allowed = taught_closure(
                syllabus,
                manifest.prereq_units,
                catalog=catalog,
                book=book,
            )
        except ValueError as exc:
            errors.append(f"{manifest.path}: {exc}")
            allowed = set(syllabus.baseline)
        if not set(manifest.concept_prerequisites) <= allowed:
            errors.append(
                f"{manifest.path}: concept_prerequisites must be in the prereq-unit closure"
            )
        if set(manifest.concepts_taught) != set(unit.teaches):
            errors.append(f"{manifest.path}: concepts_taught drift from syllabus")
        for concept in manifest.concepts_taught:
            owner = concept_owner.get(concept)
            if owner is None or owner.book != 2 or owner.id != manifest.unit_id:
                errors.append(
                    f"{manifest.path}: taught concept {concept} is not owned by a Book 2 "
                    "syllabus unit"
                )

        current_number = _book2_number(manifest.unit_id)
        for prerequisite in manifest.prereq_units:
            prereq_unit = syllabus.units.get(prerequisite)
            if prereq_unit is None or prereq_unit.book != 2:
                continue
            prerequisite_number = _book2_number(prerequisite)
            if (
                current_number is None
                or prerequisite_number is None
                or prerequisite_number >= current_number
            ):
                errors.append(
                    f"{manifest.path}: upstream Book 2 unit {prerequisite} must occur earlier"
                )

        _check_bridge(root, manifest, errors)
        _check_compute(root, manifest, errors)
        _check_claims(root, manifest, roadmap_points, errors)

    return Report(name="layer-boundary-check", ok=not errors, errors=errors)
