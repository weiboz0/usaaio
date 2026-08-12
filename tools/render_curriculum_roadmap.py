"""Render the generated curriculum coverage audit and layered roadmap."""

from __future__ import annotations

import argparse
import math
import os
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tools.books import BookSpec, load_book_catalog
from tools.checks.schedule import load_validated_schedule, scheduled_baseline_minutes
from tools.checks.scope import LAYERS, MINIMUM_QUALIFYING_PRACTICES, check_scope
from tools.model import CourseSchedule, KnowledgePoint, Roadmap, load_roadmap

AUDIT_PATH = Path("docs/audits/015-coverage-audit.md")
ROADMAP_PATH = Path("docs/curriculum-roadmap.md")
EDITORIAL_EXISTING_UNIT_ESTIMATES = {
    "convolutional-neural-network-basics": ("C7", 8.0, 12.0, "C7 CNN training"),
}
ScheduleLoader = Callable[[str | Path], CourseSchedule]

TRANCHE_QUEUE = (
    (
        "B2-019-attention-transformers",
        (
            "Query-key-value attention, scaled dot products, masks, multi-head attention, "
            "positional encoding, complexity, from-scratch training, and Transformer blocks."
        ),
    ),
    (
        "B2-020-language-transformers",
        (
            "Complete word-embedding model training, then add NLP Transformers, pretraining, "
            "fine-tuning, and language applications."
        ),
    ),
    (
        "B2-021-cross-modal-transformers-vision",
        (
            "Vision-transformer and graph-neural-network applications, object detection, "
            "and UNet."
        ),
    ),
    (
        "B2-022-probabilistic-latent-models",
        (
            "Multivariate Gaussian foundations, reparameterization, KL divergence, "
            "autoencoders, and variational autoencoders."
        ),
    ),
    (
        "B2-023-generative-models-diffusion",
        "GAN, denoising diffusion, and Stable Diffusion after the latent-model prerequisites.",
    ),
    (
        "B2-024-gpu-scientific-ml-capstone",
        (
            "Semi-supervised/pseudo-label image learning, inverse problems, mixture-parameter "
            "estimation, experiment design, reproducibility, GPU workflow, and model evaluation."
        ),
    ),
)


@dataclass(frozen=True)
class TimeBaseline:
    manifested_minutes: int
    scheduled_minutes: int


def _yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path}: expected a YAML mapping")
    return raw


def _cell(value: object) -> str:
    text = str(value) if value not in (None, "") else "—"
    return text.replace("|", "\\|").replace("\n", " ")


def _joined(values: list[str]) -> str:
    return ", ".join(sorted(values, key=str.encode)) if values else "—"


def _practice_shortfall(point: KnowledgePoint) -> int:
    practices = {
        item.id
        for evidence in point.evidence_by_modality.values()
        for item in evidence.practices
        if item.role == "primary"
    }
    return max(0, MINIMUM_QUALIFYING_PRACTICES - len(practices))


def _number(value: object) -> int:
    return int(value) if value is not None else 0


def current_time_baseline(
    root: str | Path,
    *,
    _schedule_loader: ScheduleLoader = load_validated_schedule,
    book_spec: BookSpec | None = None,
    expected_book_number: int | None = None,
) -> TimeBaseline:
    root = Path(root).resolve()
    manifested = 0
    for path in sorted(root.glob("units/*/manifest.yaml")):
        raw = _yaml(path)
        estimates = raw.get("estimated_minutes") or {}
        if not isinstance(estimates, dict):
            raise TypeError(f"{path}: estimated_minutes must be a mapping")
        manifested += sum(_number(value) for value in estimates.get("lesson_sessions") or [])
        manifested += _number(estimates.get("practice"))
        manifested += _number(estimates.get("review"))
    if _schedule_loader is load_validated_schedule:
        schedule = _schedule_loader(
            root,
            book_spec=book_spec,
            expected_book_number=expected_book_number,
        )
    else:
        schedule = _schedule_loader(root)
    scheduled = scheduled_baseline_minutes(schedule)
    return TimeBaseline(
        manifested_minutes=manifested,
        scheduled_minutes=scheduled,
    )


def _format_number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _time_section(roadmap: Roadmap, baseline: TimeBaseline) -> list[str]:
    hour_values = {layer: ([], []) for layer in LAYERS}
    for unit in roadmap.planned_units:
        hour_values[unit.layer][0].append(unit.estimated_hours.minimum)
        hour_values[unit.layer][1].append(unit.estimated_hours.maximum)
    by_layer = {
        layer: (
            math.fsum(sorted(values[0])),
            math.fsum(sorted(values[1])),
        )
        for layer, values in hour_values.items()
    }
    minimum = math.fsum(sorted(values[0] for values in by_layer.values()))
    maximum = math.fsum(sorted(values[1] for values in by_layer.values()))
    points = {point.id: point for point in roadmap.knowledge_points}
    extensions = [
        estimate
        for point_id, estimate in EDITORIAL_EXISTING_UNIT_ESTIMATES.items()
        if point_id in points and points[point_id].coverage != "covered"
    ]
    extension_minimum = math.fsum(item[1] for item in extensions)
    extension_maximum = math.fsum(item[2] for item in extensions)
    scoped_minimum = math.fsum((minimum, extension_minimum))
    scoped_maximum = math.fsum((maximum, extension_maximum))
    manifested_hours = baseline.manifested_minutes / 60
    scheduled_hours = baseline.scheduled_minutes / 60
    lines = [
        "## Time baseline and planned deltas",
        "",
        (
            f"Current manifested baseline: **{baseline.manifested_minutes} minutes / "
            f"{_format_number(manifested_hours)} hours**."
        ),
        (
            f"Current scheduled baseline: **{baseline.scheduled_minutes} minutes / "
            f"{_format_number(scheduled_hours)} hours**."
        ),
        "Planned hours are estimates and are not manifested time.",
        "",
        "| Layer | Planned minimum hours | Planned maximum hours |",
        "|---|---:|---:|",
    ]
    for layer in LAYERS:
        lines.append(
            f"| {layer} | {_format_number(by_layer[layer][0])} | "
            f"{_format_number(by_layer[layer][1])} |"
        )
    lines.extend(
        [
            (
                f"| **Planned-unit subtotal** | **{_format_number(minimum)}** | "
                f"**{_format_number(maximum)}** |"
            ),
            "",
            (
                "This range is a renderer-owned editorial estimate, not a field in the "
                "canonical coverage map."
            ),
            "",
            (
                "Baseline plus planned-unit subtotal: "
                f"**{_format_number(manifested_hours + minimum)}–"
                f"{_format_number(manifested_hours + maximum)} manifested-baseline hours** "
                f"and **{_format_number(scheduled_hours + minimum)}–"
                f"{_format_number(scheduled_hours + maximum)} scheduled-baseline hours**."
            ),
            "",
        ]
    )
    if extensions:
        lines.extend(
            [
                "### Estimated major existing-unit extensions",
                "",
                "| Existing unit | Minimum hours | Maximum hours |",
                "|---|---:|---:|",
                *(
                    f"| {unit_id} | {_format_number(unit_minimum)} | "
                    f"{_format_number(unit_maximum)} |"
                    for unit_id, unit_minimum, unit_maximum, _ in extensions
                ),
                "",
                *(f"Pending estimate: {label}." for _, _, _, label in extensions),
                "",
                (
                    "Estimated major existing-unit extensions subtotal: "
                    f"**{_format_number(extension_minimum)}–"
                    f"{_format_number(extension_maximum)} hours**."
                ),
                (
                    "Minimum estimated scoped delta: "
                    f"**{_format_number(scoped_minimum)}–"
                    f"{_format_number(scoped_maximum)} hours**."
                ),
                (
                    "Baseline plus minimum estimated scoped delta: "
                    f"**{_format_number(manifested_hours + scoped_minimum)}–"
                    f"{_format_number(manifested_hours + scoped_maximum)} "
                    "manifested-baseline hours** and "
                    f"**{_format_number(scheduled_hours + scoped_minimum)}–"
                    f"{_format_number(scheduled_hours + scoped_maximum)} "
                    "scheduled-baseline hours**."
                ),
                "",
            ]
        )
    embedding_point = points.get("nlp-word-embeddings")
    embedding_unit = next(
        (
            unit
            for unit in roadmap.planned_units
            if unit.id == "B2-020-language-transformers"
            and "nlp-word-embeddings" in unit.knowledge_points
        ),
        None,
    )
    if (
        embedding_point is not None
        and embedding_point.coverage != "covered"
        and embedding_unit is not None
    ):
        lines.extend(
            [
                (
                    f"The Book 2 `{embedding_unit.id}` "
                    f"{_format_number(embedding_unit.estimated_hours.minimum)}–"
                    f"{_format_number(embedding_unit.estimated_hours.maximum)}-hour estimate "
                    "includes completing the `nlp-word-embeddings` model-training bridge; "
                    "no additional Book 1 C8 correction is pending."
                ),
                "",
            ]
        )
    elif embedding_point is not None and embedding_point.coverage != "covered":
        lines.extend(
            [
                "The unestimated C8 `nlp-word-embeddings` model-training correction remains pending.",
                "",
            ]
        )
    return lines


def _append_tranche_queue(lines: list[str], roadmap: Roadmap) -> None:
    lines.extend(["## Dependency-ordered content tranche queue", ""])
    planned = {unit.id: unit for unit in roadmap.planned_units}
    visible = [row for row in TRANCHE_QUEUE if row[0] in planned]
    for number, (unit_id, description) in enumerate(visible, start=1):
        lines.extend([f"{number}. **{planned[unit_id].title}:** {description}", ""])
    lines.append("Each tranche updates the shipped syllabus and roadmap atomically.")


def _qualified(owner: str | None, value: str | None) -> str | None:
    if value is None or owner is None or ":" in value:
        return value
    return f"{owner}:{value}"


def _evidence_lines(point: KnowledgePoint, *, owner: str | None = None) -> list[str]:
    lines: list[str] = []
    for modality in sorted(point.evidence_by_modality, key=str.encode):
        evidence = point.evidence_by_modality[modality]
        lessons = [
            f"{_qualified(owner, anchor.path)} :: {anchor.heading} :: cell {anchor.cell_ordinal}"
            for anchor in evidence.lesson_anchors
        ]
        practices = [_qualified(owner, item.id) for item in evidence.practices]
        assessments = [_qualified(owner, item.id) for item in evidence.assessments]
        lines.extend(
            [
                f"- **{modality} lessons:** {_joined(sorted(lessons, key=str.encode))}",
                f"- **{modality} practices:** {_joined(sorted(set(practices), key=str.encode))}",
                (
                    f"- **{modality} assessments:** "
                    f"{_joined(sorted(set(assessments), key=str.encode))}"
                ),
            ]
        )
    return lines


def _append_non_required_candidates(lines: list[str], topics: dict) -> None:
    candidates = sorted(
        (
            row
            for row in topics.get("non_required_candidates") or []
            if isinstance(row, dict)
        ),
        key=lambda row: str(row.get("id", "")).encode("utf-8"),
    )
    show_owners = any(row.get("book") is not None for row in candidates)
    if show_owners:
        header = "| Book | Candidate | Related category | Decision | Source refs |"
        separator = "|---|---|---|---|---|"
        empty = "| — | — | — | — | — |"
    else:
        header = "| Candidate | Related category | Decision | Source refs |"
        separator = "|---|---|---|---|"
        empty = "| — | — | — | — |"
    lines.extend(
        [
            "## Non-required candidates",
            "",
            (
                "These topics were adjudicated explicitly but remain outside atomic required "
                "coverage unless a future source or consumer promotes them."
            ),
            "",
            header,
            separator,
        ]
    )
    if not candidates:
        lines.append(empty)
    for row in candidates:
        owner = row.get("book")
        values = (
            _qualified(str(owner), str(row.get("id"))) if owner is not None else row.get("id"),
            row.get("related_category"),
            "optional; not an atomic audit target",
            _joined([str(value) for value in row.get("source_refs") or []]),
        )
        if show_owners:
            values = (owner, *values)
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in values
            )
            + " |"
        )
    lines.append("")


def _render_audit(
    roadmap: Roadmap,
    inventory: dict,
    baseline: TimeBaseline,
    topics: dict,
    *,
    point_owners: dict[str, str] | None = None,
    owner_order: dict[str, int] | None = None,
) -> str:
    counts = inventory.get("counts") or {}
    point_owners = point_owners or {}
    owner_order = owner_order or {}
    points = sorted(
        roadmap.knowledge_points,
        key=lambda item: (
            owner_order.get(point_owners.get(item.id, ""), 0),
            item.id.encode("utf-8"),
        ),
    )
    requirement_counts = {name: 0 for name in ("required", "bridge", "optional")}
    coverage_counts = {name: 0 for name in ("covered", "partial", "missing")}
    for point in points:
        requirement_counts[point.requirement] = requirement_counts.get(point.requirement, 0) + 1
        coverage_counts[point.coverage] = coverage_counts.get(point.coverage, 0) + 1
    if point_owners:
        introduction = [
            "The shipped-content contracts live in `book1/syllabus.md` and `book2/syllabus.md`,",
            "registered in dependency order by `books.yaml`.",
            "This aggregate report renders the book-local adjudications in",
            "`book1/curriculum/coverage-map.yaml` and `book2/curriculum/coverage-map.yaml`",
            "against their book-local deterministic evidence inventories.",
            "This report is not a third source of truth.",
        ]
    else:
        introduction = [
            "This report renders the adjudication in `curriculum/coverage-map.yaml` against the",
            "deterministic evidence inventory in `curriculum/material-inventory.yaml`.",
        ]
    lines = [
        "<!-- GENERATED by tools/render_curriculum_roadmap.py; do not edit. -->",
        "# Plan 015 coverage audit",
        "",
        *introduction,
        "Assessment ids are reported separately and never satisfy the unit-practice rule.",
        "",
        "## Corpus and status totals",
        "",
        "| Measure | Count |",
        "|---|---:|",
    ]
    for label, key in (
        ("Unit notebooks", "unit_notebooks"),
        ("Mock notebooks", "mock_notebooks"),
        ("Unit practices", "unit_practices"),
    ):
        lines.append(f"| {label} | {_cell(counts.get(key, 0))} |")
    total_notebooks = _number(counts.get("unit_notebooks")) + _number(
        counts.get("mock_notebooks")
    )
    lines.append(f"| Total inventoried notebooks | {total_notebooks} |")
    for label, values in (("Requirement", requirement_counts), ("Coverage", coverage_counts)):
        for name in sorted(values, key=str.encode):
            lines.append(f"| {label}: {name} | {values[name]} |")
    lines.append("")
    lines.extend(_time_section(roadmap, baseline))
    _append_non_required_candidates(lines, topics)
    lines.extend(["## Atomic-target audit", ""])
    for point in points:
        owner = point_owners.get(point.id)
        lines.extend(
            [
                f"### {point.id}",
                "",
                *( [f"- **Book:** {owner}"] if owner is not None else [] ),
                f"- **Layer:** {point.layer}",
                f"- **Requirement:** {point.requirement}",
                f"- **Coverage:** {point.coverage}",
                f"- **Destination:** {_qualified(owner, point.destination) or '—'}",
                f"- **Dependencies:** {_joined([_qualified(owner, value) or value for value in point.depends_on])}",
                f"- **Shipped concepts:** {_joined([_qualified(owner, value) or value for value in point.shipped_concepts])}",
                f"- **Modalities missing:** {_joined(point.modalities_missing)}",
                f"- **Practice shortfall:** {_practice_shortfall(point)}",
                f"- **Rationale:** {point.rationale}",
                f"- **Consequence:** {point.consequence}",
                "",
            ]
        )
        lines.extend(_evidence_lines(point, owner=owner))
        practices = sorted(
            {
                _qualified(owner, item.id) or item.id
                for evidence in point.evidence_by_modality.values()
                for item in evidence.practices
            },
            key=str.encode,
        )
        assessments = sorted(
            {
                _qualified(owner, item.id) or item.id
                for evidence in point.evidence_by_modality.values()
                for item in evidence.assessments
            },
            key=str.encode,
        )
        lines.extend(
            [
                "",
                f"Practices: {_joined(practices)}",
                "",
                f"Assessments: {_joined(assessments)}",
                "",
            ]
        )
    _append_tranche_queue(lines, roadmap)
    return "\n".join(lines).rstrip() + "\n"


def _required_rounds(topics: dict) -> dict[str, set[str]]:
    return {
        str(row["id"]): {str(value) for value in row.get("required_for") or []}
        for row in topics.get("atomic_targets") or []
    }


def _render_roadmap(
    roadmap: Roadmap,
    baseline: TimeBaseline,
    topics: dict,
    *,
    point_owners: dict[str, str] | None = None,
    unit_owners: dict[str, str] | None = None,
) -> str:
    show_owners = point_owners is not None
    point_owners = point_owners or {}
    unit_owners = unit_owners or {}
    rounds = _required_rounds(topics)
    if point_owners:
        introduction = [
            "The shipped-content contracts live in `book1/syllabus.md` and `book2/syllabus.md`,",
            "registered in dependency order by `books.yaml`.",
            "This aggregate roadmap records acknowledged shipped and planned curriculum state; it is not a third source of truth.",
        ]
    else:
        introduction = [
            "The shipped-content contract remains in `syllabus.md`.",
            "This roadmap records acknowledged shipped and planned curriculum state.",
        ]
    lines = [
        "<!-- GENERATED by tools/render_curriculum_roadmap.py; do not edit. -->",
        "# Curriculum roadmap",
        "",
        *introduction,
        "",
        "## Exit paths",
        "",
        "### Round 1 exit",
        "",
    ]
    r1 = [
        point
        for point in roadmap.knowledge_points
        if "round-1" in rounds.get(point.id, set())
    ]
    r2 = [
        point
        for point in roadmap.knowledge_points
        if "round-2" in rounds.get(point.id, set())
    ]
    for label, points in (("Round 1", r1), ("Round 2", r2)):
        if label == "Round 2":
            lines.extend(["### Round 2 exit", ""])
        gaps = sum(point.coverage != "covered" for point in points)
        lines.extend(
            [
                f"{len(points)} required/bridge atomic targets; {gaps} acknowledged gaps.",
                "",
            ]
        )
    lines.extend(_time_section(roadmap, baseline))
    _append_non_required_candidates(lines, topics)
    lines.extend(["## Layered knowledge points", ""])
    for layer in LAYERS:
        if show_owners:
            header = (
                "| Book | Knowledge point | Requirement | Coverage | Modalities missing | "
                "Practice shortfall | Destination | Dependencies |"
            )
            separator = "|---|---|---|---|---|---:|---|---|"
            empty = "| — | — | — | — | — | — | — | — |"
        else:
            header = (
                "| Knowledge point | Requirement | Coverage | Modalities missing | "
                "Practice shortfall | Destination | Dependencies |"
            )
            separator = "|---|---|---|---|---:|---|---|"
            empty = "| — | — | — | — | — | — | — |"
        lines.extend(
            [
                f"### {layer}",
                "",
                header,
                separator,
            ]
        )
        points = sorted(
            (point for point in roadmap.knowledge_points if point.layer == layer),
            key=lambda item: item.id.encode("utf-8"),
        )
        if not points:
            lines.append(empty)
        for point in points:
            owner = point_owners.get(point.id)
            values = (
                point.id,
                point.requirement,
                point.coverage,
                _joined(point.modalities_missing),
                _practice_shortfall(point),
                _qualified(owner, point.destination),
                _joined(
                    [_qualified(owner, value) or value for value in point.depends_on]
                ),
            )
            if show_owners:
                values = (owner, *values)
            lines.append(
                "| "
                + " | ".join(
                    _cell(value)
                    for value in values
                )
                + " |"
            )
        lines.append("")
    if show_owners:
        planned_header = (
            "| Book | Unit | Title | Layer | Hours | Schedule action | Prerequisites | "
            "Owns | Provisional concepts |"
        )
        planned_separator = "|---|---|---|---|---:|---|---|---|---|"
        planned_empty = "| — | — | — | — | — | — | — | — | — |"
    else:
        planned_header = (
            "| Unit | Title | Layer | Hours | Schedule action | Prerequisites | Owns | "
            "Provisional concepts |"
        )
        planned_separator = "|---|---|---|---:|---|---|---|---|"
        planned_empty = "| — | — | — | — | — | — | — | — |"
    lines.extend(
        [
            "## Planned units",
            "",
            planned_header,
            planned_separator,
        ]
    )
    for unit in sorted(roadmap.planned_units, key=lambda item: item.id.encode("utf-8")):
        owner = unit_owners.get(unit.id)
        hours = f"{unit.estimated_hours.minimum:g}–{unit.estimated_hours.maximum:g}"
        values = (
            _qualified(owner, unit.id),
            unit.title,
            unit.layer,
            hours,
            unit.schedule_action,
            _joined([_qualified(owner, value) or value for value in unit.prerequisites]),
            _joined([_qualified(owner, value) or value for value in unit.knowledge_points]),
            _joined([_qualified(owner, value) or value for value in unit.provisional_concepts]),
        )
        if show_owners:
            values = (owner, *values)
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in values
            )
            + " |"
        )
    if not roadmap.planned_units:
        lines.append(planned_empty)
    lines.append("")
    _append_tranche_queue(lines, roadmap)
    return "\n".join(lines).rstrip() + "\n"


def _registered_inputs(
    repo_root: Path,
    *,
    _schedule_loader: ScheduleLoader,
) -> tuple[
    Roadmap,
    dict[str, Any],
    TimeBaseline,
    dict[str, Any],
    dict[str, str],
    dict[str, str],
    dict[str, int],
]:
    catalog = load_book_catalog(repo_root)
    roadmaps: list[tuple[str, Roadmap]] = []
    inventories: list[dict[str, Any]] = []
    topic_contracts: list[dict[str, Any]] = []
    baselines: list[TimeBaseline] = []
    point_owners: dict[str, str] = {}
    unit_owners: dict[str, str] = {}
    owner_order = {book.id: index for index, book in enumerate(catalog.books)}

    for book in catalog.books:
        roadmap = load_roadmap(book.root)
        inventory = _yaml(book.root / "curriculum" / "material-inventory.yaml")
        topics = _yaml(book.root / "curriculum" / "official-topics.yaml")
        baseline = current_time_baseline(
            book.root,
            _schedule_loader=_schedule_loader,
            book_spec=book,
        )
        for point in roadmap.knowledge_points:
            if point.id in point_owners:
                raise ValueError(
                    f"aggregate knowledge point {point.id!r} is owned by both "
                    f"{point_owners[point.id]} and {book.id}"
                )
            point_owners[point.id] = book.id
        for unit in roadmap.planned_units:
            if unit.id in unit_owners:
                raise ValueError(
                    f"aggregate planned unit {unit.id!r} is owned by both "
                    f"{unit_owners[unit.id]} and {book.id}"
                )
            unit_owners[unit.id] = book.id
        roadmaps.append((book.id, roadmap))
        inventories.append(inventory)
        topic_contracts.append(topics)
        baselines.append(baseline)

    versions = {roadmap.roadmap_version for _, roadmap in roadmaps}
    if versions != {1}:
        raise ValueError(f"aggregate roadmap versions must all be 1, found {sorted(versions)}")
    combined_layers = [
        layer
        for layer in LAYERS
        if any(layer in roadmap.layers for _, roadmap in roadmaps)
    ]
    combined_roadmap = Roadmap(
        roadmap_version=1,
        layers=combined_layers,
        planned_units=[unit for _, roadmap in roadmaps for unit in roadmap.planned_units],
        knowledge_points=[
            point for _, roadmap in roadmaps for point in roadmap.knowledge_points
        ],
    )

    count_keys = sorted(
        {
            key
            for inventory in inventories
            for key in (inventory.get("counts") or {})
        },
        key=str.encode,
    )
    combined_inventory = {
        "counts": {
            key: sum(int((inventory.get("counts") or {}).get(key, 0)) for inventory in inventories)
            for key in count_keys
        }
    }

    combined_topics: dict[str, Any] = {
        "atomic_targets": [],
        "non_required_candidates": [],
    }
    target_owners: dict[str, str] = {}
    candidate_owners: dict[str, str] = {}
    for (book_id, _), topics in zip(roadmaps, topic_contracts, strict=True):
        for target in topics.get("atomic_targets") or []:
            target_id = str(target["id"])
            if target_id in target_owners:
                raise ValueError(
                    f"aggregate official topic {target_id!r} is owned by both "
                    f"{target_owners[target_id]} and {book_id}"
                )
            target_owners[target_id] = book_id
            combined_topics["atomic_targets"].append(target)
        for candidate in topics.get("non_required_candidates") or []:
            candidate_id = str(candidate["id"])
            if candidate_id in candidate_owners:
                raise ValueError(
                    f"aggregate non-required candidate {candidate_id!r} is owned by both "
                    f"{candidate_owners[candidate_id]} and {book_id}"
                )
            candidate_owners[candidate_id] = book_id
            combined_topics["non_required_candidates"].append(
                {**candidate, "book": book_id}
            )
    if set(target_owners) != set(point_owners):
        raise ValueError("aggregate official topics and roadmap knowledge points differ")

    combined_baseline = TimeBaseline(
        manifested_minutes=sum(item.manifested_minutes for item in baselines),
        scheduled_minutes=sum(item.scheduled_minutes for item in baselines),
    )
    return (
        combined_roadmap,
        combined_inventory,
        combined_baseline,
        combined_topics,
        point_owners,
        unit_owners,
        owner_order,
    )


def render_documents(
    root: str | Path,
    *,
    _schedule_loader: ScheduleLoader = load_validated_schedule,
    book_spec: BookSpec | None = None,
    expected_book_number: int | None = None,
) -> dict[Path, str]:
    root = Path(root).resolve()
    if (root / "books.yaml").is_file():
        (
            roadmap,
            inventory,
            baseline,
            topics,
            point_owners,
            unit_owners,
            owner_order,
        ) = _registered_inputs(root, _schedule_loader=_schedule_loader)
        return {
            AUDIT_PATH: _render_audit(
                roadmap,
                inventory,
                baseline,
                topics,
                point_owners=point_owners,
                owner_order=owner_order,
            ),
            ROADMAP_PATH: _render_roadmap(
                roadmap,
                baseline,
                topics,
                point_owners=point_owners,
                unit_owners=unit_owners,
            ),
        }
    roadmap = load_roadmap(root)
    inventory = _yaml(root / "curriculum" / "material-inventory.yaml")
    topics = _yaml(root / "curriculum" / "official-topics.yaml")
    baseline = current_time_baseline(
        root,
        _schedule_loader=_schedule_loader,
        book_spec=book_spec,
        expected_book_number=expected_book_number,
    )
    return {
        AUDIT_PATH: _render_audit(roadmap, inventory, baseline, topics),
        ROADMAP_PATH: _render_roadmap(roadmap, baseline, topics),
    }


def _safe_output_path(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"renderer output must be a relative path inside the repository: {relative}")
    path = root / relative
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"renderer output path may not contain symlinks: {relative}")
    try:
        path.parent.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise ValueError(f"renderer output escapes repository root: {relative}") from exc
    return path


def _atomic_write(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(
    argv: list[str] | None = None,
    *,
    _schedule_loader: ScheduleLoader = load_validated_schedule,
) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        roots = (
            [book.root for book in load_book_catalog(root).books]
            if (root / "books.yaml").is_file()
            else [root]
        )
        for selected_root in roots:
            report = check_scope(selected_root)
            if report.errors:
                for error in report.errors:
                    print(f"ERROR scope-check [{selected_root.name}]: {error}", file=sys.stderr)
                return 1
        rendered = render_documents(root, _schedule_loader=_schedule_loader)
    except (OSError, TypeError, ValueError, KeyError) as exc:
        print(f"ERROR renderer: {exc}", file=sys.stderr)
        return 1
    stale: list[str] = []
    outputs: list[tuple[Path, Path, str]] = []
    try:
        for relative, content in rendered.items():
            path = _safe_output_path(root, relative)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path = _safe_output_path(root, relative)
            outputs.append((relative, path, content))
    except (OSError, ValueError) as exc:
        print(f"ERROR renderer: {exc}", file=sys.stderr)
        return 1
    for relative, path, content in outputs:
        if args.check:
            current = path.read_text(encoding="utf-8") if path.is_file() else None
            if current != content:
                stale.append(relative.as_posix())
            continue
        try:
            _atomic_write(path, content)
        except OSError as exc:
            print(f"ERROR renderer: could not write {relative}: {exc}", file=sys.stderr)
            return 1
    if stale:
        for path in stale:
            print(f"STALE {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
