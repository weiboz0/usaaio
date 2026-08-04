from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from tools.model import (
    Blueprint,
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


def _validate_manifest(
    root: Path,
    blueprint: Blueprint,
    concepts: dict[str, str],
    manifest: MockManifest,
) -> list[str]:
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

    for problem in manifest.problems:
        section_points[problem.section] += problem.points
        difficulty_points[problem.difficulty] += problem.points
        if problem.type == "programming":
            programming_points += problem.points
        if problem.provenance == "original":
            original_points += problem.points
        if problem.provenance == "adapted" and not problem.adapted_from:
            errors.append(f"{manifest.path}: {problem.id} adapted missing adapted-from")
        if not problem.spec:
            errors.append(f"{manifest.path}: {problem.id} missing spec")
        if problem.answer_key in (None, "", {}):
            errors.append(f"{manifest.path}: {problem.id} missing answer_key")
        if problem.data and problem.data.get("generator_script") and not (
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
        if problem.cluster:
            cluster_points[problem.cluster] += problem.points
            section = section_ranges.get(problem.section)
            if section:
                allowed = {fold_cluster(blueprint, cluster) for cluster in section["draws_on_clusters"]}
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
    top_level_problem_ids = {"-".join(problem.id.split("-")[:-1]) for problem in manifest.problems}
    if not _in_range(len(top_level_problem_ids), blueprint.texture["problem_count"]):
        errors.append(f"{manifest.path}: problem_count out of range")
    if total:
        five_point_share = sum(p.points for p in manifest.problems if p.points == 5) / total
        if five_point_share < float(blueprint.texture["five_point_atom_share"]["min"]):
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
    manifests = load_mock_manifests(root)
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
