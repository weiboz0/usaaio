from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from tools.model import (
    Blueprint,
    ManifestProblem,
    MockManifest,
    Report,
    load_blueprint,
    load_mock_manifests,
    load_syllabus,
)

DEFAULT_ANCHORS = {
    "concept-block": 50,
    "math-computation": 45,
    "integrative-arc": 90,
    "engineering": 65,
    "open-ended-notebook": 50,
}
DEFAULT_TIME_BUDGET = {
    "concept-block": 20,
    "math-computation": 25,
    "integrative-arc": 55,
    "engineering": 45,
    "open-ended-notebook": 35,
}
ARC_ROTATION = [
    ["nlp-embeddings", "linear-algebra", "numpy"],
    ["cnn-vision", "pytorch", "numpy"],
    ["applied-ml", "probability-statistics", "numpy"],
]


def fold_cluster(blueprint: Blueprint, cluster: str) -> str:
    return blueprint.cluster_fold.get(cluster, cluster)


def _in_range(value: float, limits: dict[str, Any]) -> bool:
    return value >= float(limits.get("min", float("-inf"))) and value <= float(
        limits.get("max", float("inf"))
    )


def _problem_errors(
    blueprint: Blueprint,
    concepts: dict[str, str],
    manifest: MockManifest,
    problem: ManifestProblem,
) -> list[str]:
    """Per-entry rules shared by both books (provenance tag, spec, key, data, cluster)."""
    errors: list[str] = []
    if problem.provenance == "adapted" and not problem.adapted_from:
        tag = blueprint.provenance_rules.get("adapted_requires_tag", "adapted-from")
        errors.append(f"{manifest.path}: {problem.id} adapted missing {tag}")
    if not problem.spec:
        errors.append(f"{manifest.path}: {problem.id} missing spec")
    if problem.answer_key in (None, "", {}):
        errors.append(f"{manifest.path}: {problem.id} missing answer_key")
    if problem.data and not isinstance(problem.data, dict):
        errors.append(f"{manifest.path}: {problem.id} data must be a mapping")
    elif problem.data and problem.data.get("generator_script") and not (
        manifest.path.parent / problem.data["generator_script"]
    ).exists():
        errors.append(f"{manifest.path}: {problem.id} missing generator_script")

    folded_concept_clusters = {
        fold_cluster(blueprint, concepts[concept])
        for concept in problem.concepts
        if concept in concepts
    }
    if problem.cluster is None:
        errors.append(f"{manifest.path}: {problem.id} missing cluster")
    elif folded_concept_clusters and problem.cluster not in folded_concept_clusters:
        errors.append(f"{manifest.path}: {problem.id} invalid dominant cluster {problem.cluster}")
    return errors


def is_round2(blueprint: Blueprint) -> bool:
    return blueprint.raw.get("target") == "round-2"


def _top_level_problem(problem_id: str) -> str:
    match = re.search(r"(?:^|-)(p\d+)", problem_id)
    return match.group(1) if match else problem_id


# Round 2 section semantics (values taken from r2-001): an open-ended section holds only
# programming entries graded as open-ended tasks; a scaffolded arc never uses that form.
ROUND2_OPEN_ENDED_TYPES = frozenset({"programming"})
ROUND2_OPEN_ENDED_FORMS = frozenset({"open-ended"})
ARC_DEVIATION_FIELD = "arc_deviation_reason"


def _cluster_map(value: Any) -> dict[str, list[str]] | None:
    if not isinstance(value, dict):
        return None
    return {str(key): list(clusters or []) for key, clusters in value.items()}


def _same_clusters(left: dict[str, list[str]], right: dict[str, list[str]]) -> bool:
    return set(left) == set(right) and all(set(left[key]) == set(right[key]) for key in left)


def round2_derived_arc_clusters(blueprint: Blueprint, test: str) -> dict[str, list[str]] | None:
    """The arc clusters the blueprint's rotation assigns to r2-NNN: index (NNN-1) mod n."""
    rotation = blueprint.raw.get("arc_rotation") or []
    match = re.fullmatch(r"r\d+-(\d{3})", test)
    if not rotation or match is None:
        return None
    return _cluster_map(rotation[(int(match.group(1)) - 1) % len(rotation)])


def round2_arc_clusters(
    blueprint: Blueprint, manifest: MockManifest
) -> tuple[dict[str, list[str]], list[str]]:
    """Allowed arc clusters per day, plus any errors about the manifest's recorded choice.

    The clusters are derived from the test number through ``arc_rotation``.  A manifest's
    ``generation_parameters.arc_clusters`` is accepted only when it equals the derived
    clusters, or when ``generation_parameters.arc_deviation_reason`` records why it differs.
    """
    parameters = manifest.generation_parameters or {}
    derived = round2_derived_arc_clusters(blueprint, manifest.test)
    raw_recorded = parameters.get("arc_clusters")
    recorded = _cluster_map(raw_recorded)
    errors: list[str] = []
    if raw_recorded is not None and recorded is None:
        errors.append(f"{manifest.path}: generation_parameters.arc_clusters must map days to clusters")
    if derived is None:
        return recorded or {}, errors
    if recorded is None or _same_clusters(recorded, derived):
        return derived, errors
    reason = parameters.get(ARC_DEVIATION_FIELD)
    if isinstance(reason, str) and reason.strip():
        return recorded, errors
    errors.append(
        f"{manifest.path}: generation_parameters.arc_clusters {recorded} differ from the "
        f"arc_rotation clusters {derived} for {manifest.test} without a recorded "
        f"{ARC_DEVIATION_FIELD}"
    )
    return derived, errors


def _validate_round2_manifest(
    blueprint: Blueprint,
    concepts: dict[str, str],
    manifest: MockManifest,
) -> list[str]:
    """Book 2 (Round 2): day-scoped sections with a kind, per-day budgets, open-ended rules."""
    errors: list[str] = []
    where = manifest.path
    sections = {section["id"]: section for section in blueprint.sections}
    section_points: Counter[str] = Counter()
    section_entries: Counter[str] = Counter()
    section_problems: dict[str, set[str]] = {section_id: set() for section_id in sections}
    difficulty_points: Counter[str] = Counter()
    cluster_points: Counter[str] = Counter()
    original_points = 0
    open_points = 0
    families = set(blueprint.raw.get("open_ended_families") or [])
    arc_clusters, arc_errors = round2_arc_clusters(blueprint, manifest)
    errors.extend(arc_errors)

    total = sum(problem.points for problem in manifest.problems)
    if total != blueprint.total_points:
        errors.append(f"{where}: points sum {total} != {blueprint.total_points}")
    if manifest.total_points and manifest.total_points != blueprint.total_points:
        errors.append(f"{where}: total_points {manifest.total_points} != blueprint total")

    day_minutes = int(blueprint.raw.get("day_duration_minutes", 0))
    if manifest.day_duration_minutes != day_minutes:
        errors.append(
            f"{where}: day_duration_minutes {manifest.day_duration_minutes} differs from "
            f"blueprint {day_minutes}"
        )
    days = list(range(1, int(blueprint.raw.get("days", 0)) + 1))
    if sorted(manifest.day_time_budget) != days:
        errors.append(f"{where}: time_budget days {sorted(manifest.day_time_budget)} != {days}")
    for day in days:
        budget = manifest.day_time_budget.get(day, {})
        expected_sections = {sid for sid, section in sections.items() if section.get("day") == day}
        if set(budget) != expected_sections:
            errors.append(
                f"{where}: time_budget day {day} sections {sorted(budget)} != "
                f"{sorted(expected_sections)}"
            )
        bad = {sid: minutes for sid, minutes in budget.items()
               if type(minutes) is not int or minutes <= 0}
        if bad:
            for sid, minutes in sorted(bad.items()):
                errors.append(
                    f"{where}: time_budget day {day} section {sid} minutes {minutes!r} "
                    f"must be a positive integer"
                )
        elif sum(budget.values()) != manifest.day_duration_minutes:
            errors.append(
                f"{where}: time_budget day {day} sums to {sum(budget.values())}, "
                f"not day_duration_minutes {manifest.day_duration_minutes}"
            )

    for problem in manifest.problems:
        section = sections.get(problem.section)
        if section is None:
            errors.append(f"{where}: {problem.id} unknown section {problem.section!r}")
        if problem.difficulty not in blueprint.difficulty_mix:
            errors.append(f"{where}: {problem.id} unknown difficulty {problem.difficulty!r}")
        if problem.day is None:
            errors.append(f"{where}: {problem.id} missing day")
        elif section is not None and problem.day != section.get("day"):
            errors.append(
                f"{where}: {problem.id} day {problem.day} != section {problem.section} "
                f"day {section.get('day')}"
            )
        section_points[problem.section] += problem.points
        section_entries[problem.section] += 1
        section_problems.setdefault(problem.section, set()).add(_top_level_problem(problem.id))
        difficulty_points[problem.difficulty] += problem.points
        if problem.provenance == "original":
            original_points += problem.points
        errors.extend(_problem_errors(blueprint, concepts, manifest, problem))
        if problem.cluster:
            cluster_points[problem.cluster] += problem.points
        if section is None:
            continue
        if section.get("kind") == "open-ended":
            open_points += problem.points
            if not families & set(problem.concepts):
                errors.append(
                    f"{where}: {problem.id} open-ended problem lacks an open_ended_families concept"
                )
            if problem.type not in ROUND2_OPEN_ENDED_TYPES:
                errors.append(
                    f"{where}: {problem.id} in open-ended section {problem.section} has type "
                    f"{problem.type!r}; expected one of {sorted(ROUND2_OPEN_ENDED_TYPES)}"
                )
            if problem.answer_form not in ROUND2_OPEN_ENDED_FORMS:
                errors.append(
                    f"{where}: {problem.id} in open-ended section {problem.section} has answer_form "
                    f"{problem.answer_form!r}; expected one of {sorted(ROUND2_OPEN_ENDED_FORMS)}"
                )
        elif section.get("kind") == "scaffolded-arc" and problem.answer_form in ROUND2_OPEN_ENDED_FORMS:
            errors.append(
                f"{where}: {problem.id} in scaffolded-arc section {problem.section} uses the "
                f"open-ended answer_form {problem.answer_form!r}"
            )
        if section.get("kind") == "scaffolded-arc" and problem.cluster:
            allowed = arc_clusters.get(f"d{section.get('day')}", [])
            if problem.cluster not in allowed:
                errors.append(
                    f"{where}: {problem.id} cluster {problem.cluster} not in "
                    f"d{section.get('day')} arc rotation {allowed}"
                )

    for section_id, section in sections.items():
        if not _in_range(section_points[section_id], section["points"]):
            errors.append(f"{where}: section {section_id} points out of range")
        if "subparts" in section and not _in_range(section_entries[section_id], section["subparts"]):
            errors.append(f"{where}: section {section_id} subparts out of range")
        if "problems" in section and not _in_range(
            len(section_problems[section_id]), section["problems"]
        ):
            errors.append(f"{where}: section {section_id} problems out of range")

    if not _in_range(len(manifest.problems), blueprint.texture["subparts"]):
        errors.append(f"{where}: subparts out of range")
    top_level = {_top_level_problem(problem.id) for problem in manifest.problems}
    if not _in_range(len(top_level), blueprint.texture["problem_count"]):
        errors.append(f"{where}: problem_count out of range")
    if total:
        open_share = open_points / total
        if not _in_range(open_share, blueprint.texture["open_ended_points_share"]):
            errors.append(f"{where}: open-ended points share {open_share:.3f} out of range")
        if original_points / total < float(blueprint.provenance_rules["original_share_min"]):
            errors.append(f"{where}: original provenance share below minimum")
        for difficulty, limits in blueprint.difficulty_mix.items():
            if not _in_range(difficulty_points[difficulty] / total, limits):
                errors.append(f"{where}: difficulty {difficulty} share out of range")
        for cluster, limits in blueprint.topic_distribution.items():
            if not _in_range(cluster_points[cluster], limits):
                errors.append(f"{where}: topic {cluster} points out of range")
    return errors


def _validate_manifest(
    root: Path,
    blueprint: Blueprint,
    concepts: dict[str, str],
    manifest: MockManifest,
) -> list[str]:
    if is_round2(blueprint):
        return _validate_round2_manifest(blueprint, concepts, manifest)
    # Book 1 (Round 1): the only reader of five_point_atom_share, programming_points_share,
    # draws_on_clusters, duration_minutes, and the integrative-arc rotation special case.
    errors: list[str] = []
    section_ranges = {section["id"]: section for section in blueprint.sections}
    section_points: Counter[str] = Counter()
    difficulty_points: Counter[str] = Counter()
    cluster_points: Counter[str] = Counter()
    programming_points = 0
    original_points = 0

    total = sum(problem.points for problem in manifest.problems)
    if total != blueprint.total_points:
        errors.append(f"{manifest.path}: points sum {total} != {blueprint.total_points}")
    if manifest.total_points and manifest.total_points != blueprint.total_points:
        errors.append(f"{manifest.path}: total_points {manifest.total_points} != blueprint total")
    if sum(manifest.time_budget.values()) != manifest.duration_minutes:
        errors.append(f"{manifest.path}: time_budget does not sum to duration_minutes")
    if manifest.duration_minutes and manifest.duration_minutes != blueprint.raw.get("duration_minutes"):
        errors.append(f"{manifest.path}: duration_minutes differs from blueprint")

    for problem in manifest.problems:
        if problem.section not in section_ranges:
            errors.append(f"{manifest.path}: {problem.id} unknown section {problem.section!r}")
        if problem.difficulty not in blueprint.difficulty_mix:
            errors.append(
                f"{manifest.path}: {problem.id} unknown difficulty {problem.difficulty!r}"
            )
        section_points[problem.section] += problem.points
        difficulty_points[problem.difficulty] += problem.points
        if problem.type == "programming":
            programming_points += problem.points
        if problem.provenance == "original":
            original_points += problem.points
        errors.extend(_problem_errors(blueprint, concepts, manifest, problem))
        if problem.cluster:
            cluster_points[problem.cluster] += problem.points
            section = section_ranges.get(problem.section)
            if section:
                source_clusters = section["draws_on_clusters"]
                if problem.section == "integrative-arc":
                    # the arc rotates per test; the manifest's generation_parameters
                    # declare the rotated allowed set (falls back to the blueprint list)
                    source_clusters = (manifest.generation_parameters or {}).get(
                        "arc_clusters", source_clusters
                    )
                allowed = {fold_cluster(blueprint, cluster) for cluster in source_clusters}
                if problem.cluster not in allowed:
                    errors.append(f"{manifest.path}: {problem.id} cluster not allowed in section")

    for section_id, section in section_ranges.items():
        if not _in_range(section_points[section_id], section["points"]):
            errors.append(f"{manifest.path}: section {section_id} points out of range")
        if "subparts" in section:
            count = sum(1 for problem in manifest.problems if problem.section == section_id)
            if not _in_range(count, section["subparts"]):
                errors.append(f"{manifest.path}: section {section_id} subparts out of range")

    if not _in_range(len(manifest.problems), blueprint.texture["subparts"]):
        errors.append(f"{manifest.path}: subparts out of range")
    # Top-level problem = the pNN token in the id; handles pNN, pNN-M, and pNNa forms
    # (naive last-segment stripping collapsed part-less ids like "r1-001-p01" to "r1-001").
    top_level_problem_ids = set()
    for problem in manifest.problems:
        match = re.search(r"(?:^|-)(p\d+)", problem.id)
        top_level_problem_ids.add(match.group(1) if match else problem.id)
    if not _in_range(len(top_level_problem_ids), blueprint.texture["problem_count"]):
        errors.append(f"{manifest.path}: problem_count out of range")
    if total:
        # COUNT share of sub-parts (analysis: "24 of 37 sub-parts are 5 pts" = 0.65),
        # not a points share (which would be 120/300 = 0.40 and reject the real paper).
        atom_count_share = sum(1 for p in manifest.problems if p.points == 5) / len(manifest.problems)
        if atom_count_share < float(blueprint.texture["five_point_atom_share"]["min"]):
            errors.append(f"{manifest.path}: five-point atom share below minimum")
        programming_share = programming_points / total
        if not _in_range(programming_share, blueprint.texture["programming_points_share"]):
            errors.append(f"{manifest.path}: programming share out of range")
        original_share = original_points / total
        if original_share < float(blueprint.provenance_rules["original_share_min"]):
            errors.append(f"{manifest.path}: original provenance share below minimum")
        for difficulty, limits in blueprint.difficulty_mix.items():
            if not _in_range(difficulty_points[difficulty] / total, limits):
                errors.append(f"{manifest.path}: difficulty {difficulty} share out of range")
        for cluster, limits in blueprint.topic_distribution.items():
            if not _in_range(cluster_points[cluster], limits):
                errors.append(f"{manifest.path}: topic {cluster} points out of range")
    return errors


def check_blueprint(root: str | Path) -> Report:
    root = Path(root)
    blueprint = load_blueprint(root)
    syllabus = load_syllabus(root)
    book_number = blueprint.raw.get("book")
    manifests = load_mock_manifests(
        root, book_number=book_number if type(book_number) is int else None
    )
    if blueprint.raw.get("status") == "planned":
        # Plan 024 retired the planned Book 2 skeleton; a blueprint is live or absent.
        return Report(
            name="blueprint-check",
            ok=False,
            errors=["planned blueprints are no longer supported; Plan 024 made the Book 2 blueprint live"],
        )
    warnings = [
        f"DRAFT manifest skipped by blueprint final gate: {manifest.path}"
        for manifest in manifests
        if manifest.status == "draft"
    ]
    final_manifests = [manifest for manifest in manifests if manifest.status != "draft"]
    errors: list[str] = []
    for manifest in final_manifests:
        errors.extend(_validate_manifest(root, blueprint, syllabus.concepts, manifest))
    skipped = None
    if not final_manifests and warnings:
        skipped = "blueprint-check has only draft manifests; finalize or remove drafts"
    return Report(
        name="blueprint-check",
        ok=not errors,
        errors=errors,
        warnings=warnings,
        skipped=skipped,
    )
