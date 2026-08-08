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

import yaml

from tools.checks.schedule import load_validated_schedule
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
    scheduled = _schedule_loader(root).total_minutes
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
    c8 = points.get("nlp-word-embeddings")
    if c8 is not None and c8.coverage != "covered":
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


def _evidence_lines(point: KnowledgePoint) -> list[str]:
    lines: list[str] = []
    for modality in sorted(point.evidence_by_modality, key=str.encode):
        evidence = point.evidence_by_modality[modality]
        lessons = [
            f"{anchor.path} :: {anchor.heading} :: cell {anchor.cell_ordinal}"
            for anchor in evidence.lesson_anchors
        ]
        practices = [item.id for item in evidence.practices]
        assessments = [item.id for item in evidence.assessments]
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
    lines.extend(
        [
            "## Non-required candidates",
            "",
            (
                "These topics were adjudicated explicitly but remain outside atomic required "
                "coverage unless a future source or consumer promotes them."
            ),
            "",
            "| Candidate | Related category | Decision | Source refs |",
            "|---|---|---|---|",
        ]
    )
    if not candidates:
        lines.append("| — | — | — | — |")
    for row in candidates:
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    row.get("id"),
                    row.get("related_category"),
                    "optional; not an atomic audit target",
                    _joined([str(value) for value in row.get("source_refs") or []]),
                )
            )
            + " |"
        )
    lines.append("")


def _render_audit(
    roadmap: Roadmap, inventory: dict, baseline: TimeBaseline, topics: dict
) -> str:
    counts = inventory.get("counts") or {}
    points = sorted(roadmap.knowledge_points, key=lambda item: item.id.encode("utf-8"))
    requirement_counts = {name: 0 for name in ("required", "bridge", "optional")}
    coverage_counts = {name: 0 for name in ("covered", "partial", "missing")}
    for point in points:
        requirement_counts[point.requirement] = requirement_counts.get(point.requirement, 0) + 1
        coverage_counts[point.coverage] = coverage_counts.get(point.coverage, 0) + 1
    lines = [
        "<!-- GENERATED by tools/render_curriculum_roadmap.py; do not edit. -->",
        "# Plan 015 coverage audit",
        "",
        "This report renders the adjudication in `curriculum/coverage-map.yaml` against the",
        "deterministic evidence inventory in `curriculum/material-inventory.yaml`.",
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
        lines.extend(
            [
                f"### {point.id}",
                "",
                f"- **Layer:** {point.layer}",
                f"- **Requirement:** {point.requirement}",
                f"- **Coverage:** {point.coverage}",
                f"- **Destination:** {point.destination or '—'}",
                f"- **Dependencies:** {_joined(point.depends_on)}",
                f"- **Shipped concepts:** {_joined(point.shipped_concepts)}",
                f"- **Modalities missing:** {_joined(point.modalities_missing)}",
                f"- **Practice shortfall:** {_practice_shortfall(point)}",
                f"- **Rationale:** {point.rationale}",
                f"- **Consequence:** {point.consequence}",
                "",
            ]
        )
        lines.extend(_evidence_lines(point))
        practices = sorted(
            {
                item.id
                for evidence in point.evidence_by_modality.values()
                for item in evidence.practices
            },
            key=str.encode,
        )
        assessments = sorted(
            {
                item.id
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
    roadmap: Roadmap, baseline: TimeBaseline, topics: dict
) -> str:
    rounds = _required_rounds(topics)
    lines = [
        "<!-- GENERATED by tools/render_curriculum_roadmap.py; do not edit. -->",
        "# Curriculum roadmap",
        "",
        "The shipped-content contract remains in `syllabus.md`.",
        "This roadmap records acknowledged shipped and planned curriculum state.",
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
        lines.extend(
            [
                f"### {layer}",
                "",
                "| Knowledge point | Requirement | Coverage | Modalities missing | Practice shortfall | Destination | Dependencies |",
                "|---|---|---|---|---:|---|---|",
            ]
        )
        points = sorted(
            (point for point in roadmap.knowledge_points if point.layer == layer),
            key=lambda item: item.id.encode("utf-8"),
        )
        if not points:
            lines.append("| — | — | — | — | — | — | — |")
        for point in points:
            lines.append(
                "| "
                + " | ".join(
                    _cell(value)
                    for value in (
                        point.id,
                        point.requirement,
                        point.coverage,
                        _joined(point.modalities_missing),
                        _practice_shortfall(point),
                        point.destination,
                        _joined(point.depends_on),
                    )
                )
                + " |"
            )
        lines.append("")
    lines.extend(
        [
            "## Planned units",
            "",
            "| Unit | Title | Layer | Hours | Schedule action | Prerequisites | Owns | Provisional concepts |",
            "|---|---|---|---:|---|---|---|---|",
        ]
    )
    for unit in sorted(roadmap.planned_units, key=lambda item: item.id.encode("utf-8")):
        hours = f"{unit.estimated_hours.minimum:g}–{unit.estimated_hours.maximum:g}"
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    unit.id,
                    unit.title,
                    unit.layer,
                    hours,
                    unit.schedule_action,
                    _joined(unit.prerequisites),
                    _joined(unit.knowledge_points),
                    _joined(unit.provisional_concepts),
                )
            )
            + " |"
        )
    if not roadmap.planned_units:
        lines.append("| — | — | — | — | — | — | — | — |")
    lines.append("")
    _append_tranche_queue(lines, roadmap)
    return "\n".join(lines).rstrip() + "\n"


def render_documents(
    root: str | Path,
    *,
    _schedule_loader: ScheduleLoader = load_validated_schedule,
) -> dict[Path, str]:
    root = Path(root).resolve()
    roadmap = load_roadmap(root)
    inventory = _yaml(root / "curriculum" / "material-inventory.yaml")
    topics = _yaml(root / "curriculum" / "official-topics.yaml")
    baseline = current_time_baseline(root, _schedule_loader=_schedule_loader)
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
    report = check_scope(root)
    if report.errors:
        for error in report.errors:
            print(f"ERROR scope-check: {error}", file=sys.stderr)
        return 1
    rendered = render_documents(root, _schedule_loader=_schedule_loader)
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
