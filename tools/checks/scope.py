from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

from tools.model import Report, load_syllabus, load_unit_manifests

LAYERS = [
    "shared-foundation",
    "round-1-core",
    "round-2-extension",
    "optional-enrichment",
]
REQUIREMENTS = {"required", "bridge", "optional"}
COVERAGE_STATES = {"covered", "partial", "missing"}
DISPOSITIONS = {"keep", "extend-existing-unit", "new-unit", "defer-optional"}
SCHEDULE_ACTIONS = {"split", "replace", "extend"}
ROUNDS = {"round-1", "round-2"}
SOURCE_AUTHORITIES = {
    "official-syllabus",
    "official-round-policy",
    "past-paper",
    "design-rationale",
}
CATEGORY_KINDS = {
    "official",
    "official-policy",
    "official-subcategory",
    "pedagogical-bridge",
    "observed",
}
ALLOWED_MODALITIES = [
    "theory",
    "derivation",
    "proof",
    "implementation",
    "model-training",
    "competition-workflow",
]
CANONICAL_PATH_NORMALIZATION = {
    "id": "official-topic-paths-v1",
    "unicode": "NFC",
    "whitespace": "collapse",
    "ordering": "source-order",
    "serialization": 'JSON UTF-8 array; ensure_ascii=false; separators=(",", ":")',
}


def _yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path}: expected a YAML mapping")
    return raw


def _duplicates(values: list[str]) -> set[str]:
    return {value for value, count in Counter(values).items() if count > 1}


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _cycle_nodes(graph: dict[str, list[str]]) -> set[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in visiting:
            start = trail.index(node) if node in trail else 0
            cycles.update(trail[start:])
            return
        if node in visited:
            return
        visiting.add(node)
        trail.append(node)
        for neighbor in graph.get(node, []):
            if neighbor in graph:
                visit(neighbor, trail)
        trail.pop()
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node, [])
    return cycles


def _check_reconciliation(root: Path, errors: list[str]) -> None:
    path = root / "docs" / "audits" / "015-plan014-reconciliation.md"
    if not path.is_file():
        errors.append(f"Plan 014 reconciliation is missing: {path.relative_to(root)}")
        return
    text = path.read_text(encoding="utf-8")
    merged = re.search(r"Plan 014 is \*\*merged\*\*", text, re.IGNORECASE)
    abandoned = re.search(r"Plan 014 is \*\*abandoned\*\*", text, re.IGNORECASE)
    if bool(merged) == bool(abandoned):
        errors.append("Plan 014 reconciliation must name exactly one resolution: merged or abandoned")
        return
    if abandoned:
        fields: dict[str, str] = {}
        for label in ("Branch/PR", "Date", "Reason", "Owner decision"):
            match = re.search(
                rf"(?mi)^[ \t]*-[ \t]*{re.escape(label)}:[ \t]*([^\r\n]*)$",
                text,
            )
            if match is None:
                errors.append(f"Plan 014 reconciliation abandonment is missing {label}:")
                continue
            value = match.group(1).strip()
            if not value:
                errors.append(f"Plan 014 reconciliation abandonment {label} must be nonempty")
                continue
            fields[label] = value
        date_value = fields.get("Date")
        if date_value is not None:
            try:
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
                    raise ValueError
                dt.date.fromisoformat(date_value)
            except ValueError:
                errors.append("Plan 014 reconciliation abandonment Date must be an ISO date")
        return
    match = re.search(r"squash commit is\s+`([0-9a-f]{7,40})`", text, re.IGNORECASE)
    if match is None:
        errors.append("Plan 014 reconciliation merged resolution must name its squash commit")
        return
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", match.group(1), "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        errors.append(
            f"Plan 014 reconciliation squash commit {match.group(1)} is not an ancestor of HEAD"
        )


def _iso_date(
    value: object, label: str, errors: list[str]
) -> dt.date | None:
    if isinstance(value, dt.datetime):
        errors.append(f"{label} has invalid date {value!r}")
        return None
    if isinstance(value, dt.date):
        return value
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        errors.append(f"{label} has invalid date {value!r}")
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} has invalid date {value!r}")
        return None


def _canonical_topic_paths_sha256(paths: list[str]) -> str:
    normalized = [
        " ".join(unicodedata.normalize("NFC", path).split())
        for path in paths
    ]
    serialized = json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _check_sources(raw: dict[str, Any], errors: list[str]) -> set[str]:
    version = raw.get("source_schema_version")
    if type(version) is not int or version != 1:
        errors.append(f"unsupported source_schema_version {version!r}; expected integer 1")
    expected_keys = {"source_schema_version", "canonical_path_normalization", "sources"}
    if set(raw) != expected_keys:
        errors.append(
            f"sources top-level keys must exactly equal {sorted(expected_keys)}, got {sorted(raw)}"
        )
    if raw.get("canonical_path_normalization") != CANONICAL_PATH_NORMALIZATION:
        errors.append(
            "canonical_path_normalization must exactly equal official-topic-paths-v1 contract"
        )
    rows = raw.get("sources")
    if not isinstance(rows, list):
        errors.append("sources must be a list")
        return set()
    ids = [
        str(row.get("id", ""))
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]
    for duplicate in sorted(_duplicates(ids)):
        errors.append(f"duplicate source id {duplicate}")
    today = dt.datetime.now(tz=dt.UTC).date()
    for index, row in enumerate(rows):
        label = f"sources row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be a mapping")
            continue
        for field in ("id", "title"):
            _require_nonempty_string(row, field, label, errors)
        source_id = row.get("id") if isinstance(row.get("id"), str) else f"row-{index}"
        authority = row.get("authority")
        if authority not in SOURCE_AUTHORITIES:
            errors.append(f"source {source_id}: unknown authority {authority!r}")
        for field in ("committed", "local_only"):
            if type(row.get(field)) is not bool:
                errors.append(f"source {source_id}: {field} must be a boolean")
        locations = [
            field
            for field in ("url", "path")
            if isinstance(row.get(field), str) and row[field].strip()
        ]
        if len(locations) != 1:
            errors.append(f"source {source_id}: exactly one of url or path must be nonempty")
        date_fields = [field for field in ("retrieved", "recorded") if field in row]
        if not date_fields and "competition_year" not in row:
            errors.append(
                f"source {source_id}: requires retrieved, recorded, or competition_year"
            )
        for field in date_fields:
            _iso_date(row.get(field), f"source {source_id} invalid {field}", errors)
        if "competition_year" in row:
            year = row.get("competition_year")
            if type(year) is not int or year < 2000:
                errors.append(f"source {source_id}: competition_year must be an integer")
        review_after = _iso_date(
            row.get("review_after"), f"source {source_id} invalid review_after", errors
        )
        if review_after is not None and today > review_after:
            errors.append(
                "curriculum/sources.yaml: source "
                f"{source_id} passed review_after {review_after}; open a source-refresh change "
                "that repeats Task 1 and re-adjudicates affected rows"
            )
        path_fields = {"normalization", "topic_paths_sha256", "topic_paths"}
        present_path_fields = path_fields & set(row)
        if authority in {"official-syllabus", "official-round-policy"} and not present_path_fields:
            errors.append(
                f"source {source_id}: official source requires a canonical topic-path pin"
            )
        if present_path_fields:
            for field in sorted(path_fields - present_path_fields):
                errors.append(f"source {source_id}: {field} is required with topic_paths")
            if row.get("normalization") != "official-topic-paths-v1":
                errors.append(
                    f"source {source_id}: unknown normalization {row.get('normalization')!r}"
                )
            topic_paths = row.get("topic_paths")
            if not _is_string_list(topic_paths) or not topic_paths or any(
                not path.strip() for path in topic_paths
            ):
                errors.append(f"source {source_id}: topic_paths must be nonempty strings")
            else:
                expected_hash = _canonical_topic_paths_sha256(topic_paths)
                declared_hash = row.get("topic_paths_sha256")
                if not isinstance(declared_hash, str) or not re.fullmatch(
                    r"[0-9a-f]{64}", declared_hash
                ):
                    errors.append(f"source {source_id}: topic_paths_sha256 must be lowercase SHA-256")
                elif declared_hash != expected_hash:
                    errors.append(
                        f"source {source_id}: topic_paths_sha256 mismatch; "
                        f"expected {expected_hash}"
                    )
    return {source_id for source_id in ids if source_id}


def _check_source_refs(
    label: str, refs: list[str], known_sources: set[str], errors: list[str]
) -> None:
    for source in refs:
        if source not in known_sources:
            errors.append(f"{label}: unknown source {source}")


def _validate_topics_schema(raw: dict[str, Any], errors: list[str]) -> bool:
    valid = True
    version = raw.get("official_topics_schema_version")
    if type(version) is not int or version != 1:
        errors.append(
            f"unsupported official_topics_schema_version {version!r}; expected integer 1"
        )
        valid = False
    expected_keys = {
        "official_topics_schema_version",
        "allowed_modalities",
        "categories",
        "atomic_targets",
        "non_required_candidates",
    }
    if set(raw) != expected_keys:
        errors.append(
            f"official-topics top-level keys must exactly equal {sorted(expected_keys)}, "
            f"got {sorted(raw)}"
        )
        valid = False
    if raw.get("allowed_modalities") != ALLOWED_MODALITIES:
        errors.append(f"allowed_modalities must exactly equal {ALLOWED_MODALITIES}")
        valid = False
    collections: dict[str, list[Any]] = {}
    for field in ("categories", "atomic_targets", "non_required_candidates"):
        value = raw.get(field)
        if not isinstance(value, list):
            errors.append(f"{field} must be a list")
            valid = False
        else:
            collections[field] = value
    if len(collections) != 3:
        return False

    category_fields = {"id", "parent", "kind", "source_refs", "required_for"}
    for index, row in enumerate(collections["categories"]):
        label = f"categories row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be a mapping")
            valid = False
            continue
        if set(row) != category_fields:
            errors.append(f"{label} fields must exactly equal {sorted(category_fields)}")
            valid = False
        valid &= _require_nonempty_string(row, "id", label, errors)
        parent = row.get("parent")
        if parent is not None and (not isinstance(parent, str) or not parent.strip()):
            errors.append(f"{label}: parent must be a nonempty string or null")
            valid = False
        if row.get("kind") not in CATEGORY_KINDS:
            errors.append(f"{label}: unknown category kind {row.get('kind')!r}")
            valid = False
        for field in ("source_refs", "required_for"):
            if not _require_string_list(row, field, label, errors) or not row.get(field):
                errors.append(f"{label}: {field} must be nonempty")
                valid = False
        if _is_string_list(row.get("required_for")) and not set(row["required_for"]) <= ROUNDS:
            errors.append(f"{label}: unknown required_for value")
            valid = False

    target_fields = {"id", "parent", "source_refs", "required_for", "modalities"}
    for index, row in enumerate(collections["atomic_targets"]):
        label = f"atomic_targets row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be a mapping")
            valid = False
            continue
        allowed = target_fields | {"acceptance"}
        if not target_fields <= set(row) or not set(row) <= allowed:
            errors.append(f"{label} fields must contain {sorted(target_fields)} and only {sorted(allowed)}")
            valid = False
        for field in ("id", "parent"):
            valid &= _require_nonempty_string(row, field, label, errors)
        for field in ("source_refs", "required_for", "modalities"):
            if not _require_string_list(row, field, label, errors) or not row.get(field):
                errors.append(f"{label}: {field} must be nonempty")
                valid = False
        if _is_string_list(row.get("required_for")) and not set(row["required_for"]) <= ROUNDS:
            errors.append(f"{label}: unknown required_for value")
            valid = False
        if _is_string_list(row.get("modalities")) and not set(row["modalities"]) <= set(
            ALLOWED_MODALITIES
        ):
            errors.append(f"{label}: unknown modalities")
            valid = False
        if "acceptance" in row and (
            not _is_string_list(row["acceptance"])
            or not row["acceptance"]
            or any(not item.strip() for item in row["acceptance"])
        ):
            errors.append(f"{label}: acceptance must be a nonempty list of strings")
            valid = False

    candidate_fields = {
        "id",
        "related_category",
        "source_refs",
        "requirement",
        "audit_target",
    }
    for index, row in enumerate(collections["non_required_candidates"]):
        label = f"non_required_candidates row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be a mapping")
            valid = False
            continue
        if set(row) != candidate_fields:
            errors.append(f"{label} fields must exactly equal {sorted(candidate_fields)}")
            valid = False
        for field in ("id", "related_category"):
            valid &= _require_nonempty_string(row, field, label, errors)
        if not _require_string_list(row, "source_refs", label, errors) or not row.get(
            "source_refs"
        ):
            errors.append(f"{label}: source_refs must be nonempty")
            valid = False
        if row.get("requirement") != "optional":
            errors.append(f"{label}: requirement must be optional")
            valid = False
        if row.get("audit_target") is not False:
            errors.append(f"{label}: audit_target must be false")
            valid = False
    return valid


def _check_topics(
    raw: dict[str, Any], known_sources: set[str], errors: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if not _validate_topics_schema(raw, errors):
        return {}, {}
    category_rows = raw["categories"]
    target_rows = raw["atomic_targets"]
    category_ids = [str(row.get("id", "")) for row in category_rows]
    target_ids = [str(row.get("id", "")) for row in target_rows]
    for duplicate in sorted(_duplicates(category_ids)):
        errors.append(f"duplicate official category {duplicate}")
    for duplicate in sorted(_duplicates(target_ids)):
        errors.append(f"duplicate official atomic target {duplicate}")
    categories = {str(row.get("id", "")): row for row in category_rows}
    targets = {str(row.get("id", "")): row for row in target_rows}
    graph: dict[str, list[str]] = {}
    for category_id, row in categories.items():
        _check_source_refs(
            f"category {category_id}", _strings(row.get("source_refs")), known_sources, errors
        )
        declared = set(_strings(row.get("required_for")))
        if not declared <= ROUNDS:
            errors.append(f"category {category_id}: unknown required_for value")
        parent = row.get("parent")
        graph[category_id] = [str(parent)] if parent is not None else []
        if parent is not None and str(parent) not in categories:
            errors.append(
                f"category {category_id}: unknown parent {parent}; inherited required_for unavailable"
            )
    cycles = _cycle_nodes(graph)
    if cycles:
        errors.append(
            "category cycle prevents inherited required_for validation: "
            + ", ".join(sorted(cycles))
        )

    def inherited_rounds(category_id: str, seen: set[str] | None = None) -> set[str]:
        seen = set() if seen is None else seen
        if category_id in seen or category_id not in categories:
            return set()
        seen.add(category_id)
        row = categories[category_id]
        result = set(_strings(row.get("required_for")))
        parent = row.get("parent")
        if parent is not None:
            result |= inherited_rounds(str(parent), seen)
        return result

    for category_id, row in categories.items():
        parent = row.get("parent")
        if parent is None or str(parent) not in categories or cycles:
            continue
        inherited = inherited_rounds(str(parent))
        missing = inherited - set(_strings(row.get("required_for")))
        if missing:
            errors.append(
                f"category {category_id} removes inherited required_for {sorted(missing)}"
            )
    allowed_modalities = set(_strings(raw.get("allowed_modalities")))
    for target_id, row in targets.items():
        _check_source_refs(
            f"atomic target {target_id}",
            _strings(row.get("source_refs")),
            known_sources,
            errors,
        )
        parent = str(row.get("parent", ""))
        if parent not in categories:
            errors.append(f"atomic target {target_id}: unknown category parent {parent}")
            continue
        required_for = set(_strings(row.get("required_for")))
        inherited = inherited_rounds(parent)
        missing = inherited - required_for
        if missing:
            errors.append(
                f"atomic target {target_id} removes inherited required_for {sorted(missing)}"
            )
        modalities = set(_strings(row.get("modalities")))
        unknown_modalities = modalities - allowed_modalities
        if unknown_modalities:
            errors.append(
                f"atomic target {target_id}: unknown modalities {sorted(unknown_modalities)}"
            )
    for row in raw["non_required_candidates"]:
        candidate_id = str(row["id"])
        _check_source_refs(
            f"non-required candidate {candidate_id}",
            row["source_refs"],
            known_sources,
            errors,
        )
        if row["related_category"] not in categories:
            errors.append(
                f"non-required candidate {candidate_id}: unknown related_category "
                f"{row['related_category']}"
            )
    return categories, targets


def _inventory_indexes(raw: dict[str, Any]) -> tuple[set[tuple[str, str, int]], set[str]]:
    anchors: set[tuple[str, str, int]] = set()
    problem_ids: set[str] = set()
    for notebook in raw.get("notebooks") or []:
        if not isinstance(notebook, dict):
            continue
        path = str(notebook.get("path", ""))
        problem_ids.update(_strings(notebook.get("declared_problem_ids")))
        for anchor in notebook.get("anchors") or []:
            if not isinstance(anchor, dict):
                continue
            heading = " > ".join(_strings(anchor.get("heading_path")))
            anchors.add((path, heading, int(anchor.get("cell_ordinal", -1))))
    return anchors, problem_ids


def _mock_problem_ids(root: Path) -> set[str]:
    problem_ids: set[str] = set()
    for path in sorted(root.glob("mocktests/*/manifest.yaml")):
        raw = _yaml(path)
        for problem in raw.get("problems") or []:
            if isinstance(problem, dict) and problem.get("id"):
                problem_ids.add(str(problem["id"]))
    return problem_ids


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _require_string_list(
    row: dict[str, Any], field: str, label: str, errors: list[str]
) -> bool:
    if not _is_string_list(row.get(field)):
        errors.append(f"{label}: {field} must be a list of strings")
        return False
    return True


def _require_nonempty_string(
    row: dict[str, Any], field: str, label: str, errors: list[str]
) -> bool:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} requires nonempty {field}")
        return False
    return True


def _validate_evidence_schema(
    evidence_by_modality: dict[Any, Any], label: str, errors: list[str]
) -> bool:
    valid = True
    for modality, evidence in evidence_by_modality.items():
        if not isinstance(modality, str):
            errors.append(f"{label}: evidence modality names must be strings")
            valid = False
            continue
        modality_label = f"{label}/{modality}"
        if not isinstance(evidence, dict):
            errors.append(f"{modality_label}: evidence must be a mapping")
            valid = False
            continue
        for field in ("lesson_anchors", "practices", "assessments"):
            value = evidence.get(field, [])
            if not isinstance(value, list):
                errors.append(f"{modality_label}: {field} must be a list")
                valid = False
                continue
            for index, item in enumerate(value):
                item_label = f"{modality_label} {field} row {index}"
                if not isinstance(item, dict):
                    errors.append(f"{item_label} must be a mapping")
                    valid = False
                    continue
                if field == "lesson_anchors":
                    for text_field in ("path", "heading", "role"):
                        valid &= _require_nonempty_string(
                            item, text_field, item_label, errors
                        )
                    ordinal = item.get("cell_ordinal")
                    if isinstance(ordinal, bool) or not isinstance(ordinal, int):
                        errors.append(f"{item_label}: cell_ordinal must be an integer")
                        valid = False
                else:
                    for text_field in ("id", "role"):
                        valid &= _require_nonempty_string(
                            item, text_field, item_label, errors
                        )
    return valid


def _validate_roadmap_schema(raw: dict[str, Any], errors: list[str]) -> bool:
    valid = True
    planned_raw = raw.get("planned_units")
    points_raw = raw.get("knowledge_points")
    if not isinstance(planned_raw, list):
        errors.append("planned_units must be a list")
        valid = False
    if not isinstance(points_raw, list):
        errors.append("knowledge_points must be a list")
        valid = False
    if not valid:
        return False

    assert isinstance(planned_raw, list)
    assert isinstance(points_raw, list)
    for index, row in enumerate(planned_raw):
        label = f"planned_units row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be a mapping")
            valid = False
            continue
        for field in ("id", "title", "layer"):
            valid &= _require_nonempty_string(row, field, label, errors)
        for field in ("prerequisites", "knowledge_points", "provisional_concepts"):
            valid &= _require_string_list(row, field, label, errors)
        if not isinstance(row.get("estimated_hours"), dict):
            errors.append(f"{label}: estimated_hours must be a mapping")
            valid = False
        action = row.get("schedule_action")
        if action is not None and not isinstance(action, str):
            errors.append(f"{label}: schedule_action must be a string when present")
            valid = False

    for index, row in enumerate(points_raw):
        label = f"knowledge_points row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be a mapping")
            valid = False
            continue
        for field in (
            "id",
            "layer",
            "requirement",
            "coverage",
            "disposition",
            "rationale",
            "consequence",
        ):
            valid &= _require_nonempty_string(row, field, label, errors)
        for field in ("source_refs", "depends_on", "shipped_concepts"):
            valid &= _require_string_list(row, field, label, errors)
        destination = row.get("destination")
        if destination is not None and not isinstance(destination, str):
            errors.append(f"{label}: destination must be a string or null")
            valid = False
        evidence = row.get("evidence_by_modality")
        if not isinstance(evidence, dict):
            errors.append(f"{label}: evidence_by_modality must be a mapping")
            valid = False
        else:
            valid &= _validate_evidence_schema(evidence, label, errors)
        deficits = row.get("deficits")
        if not isinstance(deficits, dict):
            errors.append(f"{label}: deficits must be a mapping")
            valid = False
        elif not _is_string_list(deficits.get("modalities_missing")):
            errors.append(
                f"{label}: modalities_missing must be a list of strings"
            )
            valid = False
    return valid


def _check_planned_units(
    rows: list[dict[str, Any]],
    known_layers: set[str],
    existing_units: set[str],
    knowledge_ids: set[str],
    shipped_concepts: set[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    ids = [str(row.get("id", "")) for row in rows]
    for duplicate in sorted(_duplicates(ids)):
        errors.append(f"duplicate planned unit {duplicate}")
    planned = {str(row.get("id", "")): row for row in rows}
    all_units = existing_units | set(planned)
    for unit_id, row in planned.items():
        layer = str(row.get("layer", ""))
        if layer not in known_layers:
            errors.append(f"planned unit {unit_id}: unknown layer {layer}")
        for prerequisite in _strings(row.get("prerequisites")):
            if prerequisite not in all_units:
                errors.append(f"planned unit {unit_id}: unknown prerequisite {prerequisite}")
        for point_id in _strings(row.get("knowledge_points")):
            if point_id not in knowledge_ids:
                errors.append(
                    f"planned unit {unit_id}: unknown owned knowledge point {point_id}"
                )
        for concept in _strings(row.get("provisional_concepts")):
            if concept in shipped_concepts:
                errors.append(
                    f"planned unit {unit_id}: provisional concept {concept} already appears "
                    "in syllabus.md or a unit teaches list"
                )
        hours = row.get("estimated_hours")
        minimum = _number(hours.get("min")) if isinstance(hours, dict) else None
        maximum = _number(hours.get("max")) if isinstance(hours, dict) else None
        if minimum is None or maximum is None or minimum < 0 or maximum < minimum:
            errors.append(
                f"planned unit {unit_id}: estimated_hours must be non-negative with max >= min"
            )
        action = row.get("schedule_action")
        if layer in {"shared-foundation", "round-1-core"} and action not in SCHEDULE_ACTIONS:
            errors.append(
                f"planned unit {unit_id}: Round-1 addition requires schedule_action "
                "split, replace, or extend"
            )
        elif action is not None and action not in SCHEDULE_ACTIONS:
            errors.append(f"planned unit {unit_id}: unknown schedule_action {action}")
    prerequisite_graph = {
        unit_id: [
            prerequisite
            for prerequisite in _strings(row.get("prerequisites"))
            if prerequisite in planned
        ]
        for unit_id, row in planned.items()
    }
    cycles = _cycle_nodes(prerequisite_graph)
    if cycles:
        errors.append("planned-unit prerequisite cycle: " + ", ".join(sorted(cycles)))
    early_layers = {"shared-foundation", "round-1-core"}
    later_layers = {"round-2-extension", "optional-enrichment"}
    for unit_id, row in planned.items():
        if row.get("layer") not in early_layers:
            continue
        pending = list(prerequisite_graph[unit_id])
        visited: set[str] = set()
        while pending:
            dependency = pending.pop()
            if dependency in visited:
                continue
            visited.add(dependency)
            dependency_row = planned[dependency]
            if dependency_row.get("layer") in later_layers:
                errors.append(
                    f"planned unit {unit_id} cannot depend on later-layer planned unit "
                    f"{dependency}"
                )
            pending.extend(prerequisite_graph[dependency])
    return planned


def _evidence_role(item: dict[str, Any], label: str, errors: list[str]) -> bool:
    if item.get("role") != "primary":
        errors.append(f"{label}: evidence role must be primary")
        return False
    return True


def _check_point_evidence(
    point: dict[str, Any],
    target: dict[str, Any],
    inventory_anchors: set[tuple[str, str, int]],
    all_problem_ids: set[str],
    practice_tags: dict[str, set[str]],
    unit_teaches: dict[str, set[str]],
    errors: list[str],
    warnings: list[str],
) -> None:
    point_id = str(point.get("id", ""))
    shipped = set(_strings(point.get("shipped_concepts")))
    raw_evidence = point.get("evidence_by_modality") or {}
    if not isinstance(raw_evidence, dict):
        errors.append(f"knowledge point {point_id}: evidence_by_modality must be a mapping")
        raw_evidence = {}
    required_modalities = _strings(target.get("modalities"))
    for modality in sorted(set(raw_evidence) - set(required_modalities)):
        errors.append(f"knowledge point {point_id}: unknown evidence modality {modality}")
    completed_modalities: set[str] = set()
    modalities_with_lesson: set[str] = set()
    qualifying_practices: set[str] = set()
    for modality in required_modalities:
        evidence = raw_evidence.get(modality) or {}
        if not isinstance(evidence, dict):
            errors.append(f"knowledge point {point_id}/{modality}: evidence must be a mapping")
            continue
        valid_lesson = False
        valid_practice = False
        for anchor in evidence.get("lesson_anchors") or []:
            if not isinstance(anchor, dict):
                errors.append(f"knowledge point {point_id}/{modality}: invalid lesson anchor")
                continue
            primary = _evidence_role(
                anchor, f"knowledge point {point_id}/{modality} lesson", errors
            )
            key = (
                str(anchor.get("path", "")),
                str(anchor.get("heading", "")),
                int(anchor.get("cell_ordinal", -1)),
            )
            if key not in inventory_anchors:
                errors.append(f"knowledge point {point_id}/{modality}: unknown lesson anchor {key}")
                continue
            parts = Path(key[0]).parts
            is_lesson_session = (
                len(parts) == 4
                and parts[0] == "units"
                and parts[2] == "lessons"
                and parts[3].endswith(".ipynb")
            )
            if not is_lesson_session:
                errors.append(
                    f"knowledge point {point_id}/{modality}: lesson {key[0]} "
                    "is not a unit lesson-session notebook"
                )
                continue
            unit_id = parts[1]
            if not (unit_teaches.get(unit_id, set()) & shipped):
                errors.append(
                    f"knowledge point {point_id}/{modality}: lesson {key[0]} "
                    "does not teach any shipped_concepts"
                )
                continue
            valid_lesson |= primary
        for practice in evidence.get("practices") or []:
            if not isinstance(practice, dict):
                errors.append(f"knowledge point {point_id}/{modality}: invalid practice evidence")
                continue
            primary = _evidence_role(
                practice, f"knowledge point {point_id}/{modality} practice", errors
            )
            practice_id = str(practice.get("id", ""))
            if practice_id not in practice_tags:
                errors.append(
                    f"knowledge point {point_id}/{modality}: unknown practice evidence {practice_id}"
                )
                continue
            if not (practice_tags[practice_id] & shipped):
                errors.append(
                    f"knowledge point {point_id}/{modality}: practice {practice_id} "
                    "does not tag any shipped_concepts"
                )
                continue
            if primary:
                valid_practice = True
                qualifying_practices.add(practice_id)
        for assessment in evidence.get("assessments") or []:
            if not isinstance(assessment, dict):
                errors.append(f"knowledge point {point_id}/{modality}: invalid assessment evidence")
                continue
            _evidence_role(
                assessment, f"knowledge point {point_id}/{modality} assessment", errors
            )
            assessment_id = str(assessment.get("id", ""))
            if assessment_id not in all_problem_ids:
                errors.append(
                    f"knowledge point {point_id}/{modality}: "
                    f"unknown assessment evidence {assessment_id}"
                )
        if valid_lesson:
            modalities_with_lesson.add(modality)
        if valid_lesson and valid_practice:
            completed_modalities.add(modality)
    missing = [
        modality for modality in required_modalities if modality not in modalities_with_lesson
    ]
    if len(completed_modalities) == len(required_modalities) and len(qualifying_practices) >= 3:
        derived = "covered"
    elif not modalities_with_lesson and not qualifying_practices:
        derived = "missing"
    else:
        derived = "partial"
    declared = str(point.get("coverage", ""))
    if declared in COVERAGE_STATES and declared != derived:
        errors.append(
            f"knowledge point {point_id}: declared coverage {declared}; derived coverage is {derived}"
        )
    deficits = point.get("deficits") or {}
    if isinstance(deficits, dict) and "practice_shortfall" in deficits:
        errors.append(
            f"knowledge point {point_id}: practice_shortfall is checker-derived and must not be stored"
        )
    declared_missing = _strings(
        deficits.get("modalities_missing") if isinstance(deficits, dict) else None
    )
    if declared_missing != missing:
        errors.append(
            f"knowledge point {point_id}: modalities_missing must exactly equal {missing}, "
            f"got {declared_missing}"
        )
    if derived != "covered":
        shortfall = max(0, 3 - len(qualifying_practices))
        warnings.append(
            f"knowledge point {point_id}: {derived}; modalities missing {missing}; "
            f"practice shortfall {shortfall}"
        )


def _check_roadmap(
    root: Path,
    raw: dict[str, Any],
    targets: dict[str, dict[str, Any]],
    known_sources: set[str],
    inventory: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    roadmap_version = raw.get("roadmap_version")
    if type(roadmap_version) is not int or roadmap_version != 1:
        errors.append(f"unsupported roadmap_version {roadmap_version!r}; expected integer 1")
    if raw.get("layers") != LAYERS:
        errors.append(f"layers must exactly equal {LAYERS}")
    expected_keys = {"roadmap_version", "layers", "planned_units", "knowledge_points"}
    if set(raw) != expected_keys:
        errors.append(
            f"coverage-map top-level keys must exactly equal {sorted(expected_keys)}, got {sorted(raw)}"
        )
    if not _validate_roadmap_schema(raw, errors):
        return
    syllabus = load_syllabus(root)
    manifests = load_unit_manifests(root)
    existing_units = set(syllabus.units)
    shipped_concepts = set(syllabus.concepts)
    for unit in syllabus.units.values():
        shipped_concepts.update(unit.teaches)
    practice_tags = {
        practice.id: set(practice.concepts)
        for manifest in manifests
        for practice in manifest.practice
    }
    unit_teaches = {unit_id: set(unit.teaches) for unit_id, unit in syllabus.units.items()}
    inventory_anchors, inventory_problem_ids = _inventory_indexes(inventory)
    all_problem_ids = inventory_problem_ids | _mock_problem_ids(root)

    point_rows = raw["knowledge_points"]
    point_ids = [str(row.get("id", "")) for row in point_rows]
    for duplicate in sorted(_duplicates(point_ids)):
        errors.append(f"duplicate knowledge point {duplicate}")
    point_counts = Counter(point_ids)
    for target_id in targets:
        if point_counts[target_id] == 0:
            errors.append(f"missing official atomic target {target_id}")
    for point_id in sorted(set(point_ids) - set(targets)):
        errors.append(f"extra non-official knowledge point {point_id}")
    points = {str(row.get("id", "")): row for row in point_rows}
    planned_rows = raw["planned_units"]
    planned = _check_planned_units(
        planned_rows,
        set(LAYERS),
        existing_units,
        set(points),
        shipped_concepts,
        errors,
    )
    dependency_graph = {
        point_id: _strings(point.get("depends_on")) for point_id, point in points.items()
    }
    cycles = _cycle_nodes(dependency_graph)
    if cycles:
        errors.append("knowledge-point dependency cycle: " + ", ".join(sorted(cycles)))
    planned_owners: dict[str, list[str]] = defaultdict(list)
    for unit_id, unit in planned.items():
        for point_id in _strings(unit.get("knowledge_points")):
            planned_owners[point_id].append(unit_id)

    for point_id, point in points.items():
        requirement = str(point.get("requirement", ""))
        coverage = str(point.get("coverage", ""))
        disposition = str(point.get("disposition", ""))
        layer = str(point.get("layer", ""))
        if requirement not in REQUIREMENTS:
            errors.append(f"knowledge point {point_id}: unknown requirement {requirement}")
        if coverage not in COVERAGE_STATES:
            errors.append(f"knowledge point {point_id}: unknown coverage {coverage}")
        if disposition not in DISPOSITIONS:
            errors.append(f"knowledge point {point_id}: unknown disposition {disposition}")
        if layer not in LAYERS:
            errors.append(f"knowledge point {point_id}: unknown layer {layer}")
        _check_source_refs(
            f"knowledge point {point_id}",
            _strings(point.get("source_refs")),
            known_sources,
            errors,
        )
        target = targets.get(point_id)
        if target is not None and set(_strings(point.get("source_refs"))) != set(
            _strings(target.get("source_refs"))
        ):
            errors.append(
                f"knowledge point {point_id}: source_refs must exactly match its atomic target"
            )
        for field in ("rationale", "consequence"):
            if not str(point.get(field, "")).strip():
                errors.append(f"knowledge point {point_id}: requires nonempty {field}")
        for concept in _strings(point.get("shipped_concepts")):
            if concept not in shipped_concepts:
                errors.append(f"knowledge point {point_id}: unknown shipped concept {concept}")
        for dependency in dependency_graph[point_id]:
            if dependency not in points and dependency not in shipped_concepts:
                errors.append(f"knowledge point {point_id}: unknown dependency {dependency}")
        destination_value = point.get("destination")
        destination = str(destination_value) if destination_value is not None else None
        if destination is not None and destination not in existing_units | set(planned):
            errors.append(f"knowledge point {point_id}: unknown destination {destination}")
        if coverage in {"partial", "missing"} and not destination:
            errors.append(f"{coverage} {point_id} requires a destination")
        if disposition in {"keep", "extend-existing-unit"} and destination not in existing_units:
            errors.append(
                f"knowledge point {point_id}: {disposition} requires an existing-unit destination"
            )
        if disposition in {"new-unit", "defer-optional"} and (
            destination not in planned or destination not in planned_owners.get(point_id, [])
        ):
            errors.append(
                f"knowledge point {point_id}: {disposition} requires a planned-unit "
                "destination owner"
            )

        owners = list(planned_owners.get(point_id, []))
        if disposition in {"keep", "extend-existing-unit"} and destination in existing_units:
            owners.append(str(destination))
        if len(owners) != 1 or destination not in owners:
            errors.append(
                f"knowledge point {point_id} must have exactly one destination owner; "
                f"destination={destination!r}, owners={sorted(owners)}"
            )

        if target is None:
            continue
        required_for = set(_strings(target.get("required_for")))
        if requirement == "optional":
            errors.append(f"official atomic target {point_id} cannot be optional")
        if "round-1" in required_for:
            if layer in {"round-2-extension", "optional-enrichment"}:
                errors.append(f"Round-1-required {point_id} is assigned to {layer}")
            if destination in planned and str(planned[destination].get("layer")) in {
                "round-2-extension",
                "optional-enrichment",
            }:
                errors.append(f"Round-1-required {point_id} is owned by a Round-2 unit")
            for dependency in dependency_graph[point_id]:
                dependency_target = targets.get(dependency)
                if dependency_target and "round-1" not in set(
                    _strings(dependency_target.get("required_for"))
                ):
                    errors.append(
                        f"Round-1-required {point_id} depends on Round-2-only material {dependency}"
                    )
        _check_point_evidence(
            point,
            target,
            inventory_anchors,
            all_problem_ids,
            practice_tags,
            unit_teaches,
            errors,
            warnings,
        )


def check_scope(root: str | Path) -> Report:
    root = Path(root).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    sources = _yaml(root / "curriculum" / "sources.yaml")
    topics = _yaml(root / "curriculum" / "official-topics.yaml")
    inventory = _yaml(root / "curriculum" / "material-inventory.yaml")
    roadmap = _yaml(root / "curriculum" / "coverage-map.yaml")
    known_sources = _check_sources(sources, errors)
    _, targets = _check_topics(topics, known_sources, errors)
    _check_roadmap(root, roadmap, targets, known_sources, inventory, errors, warnings)
    _check_reconciliation(root, errors)
    return Report(name="scope-check", ok=not errors, errors=errors, warnings=warnings)
