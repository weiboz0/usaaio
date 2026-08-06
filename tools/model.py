from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Unit:
    id: str
    track: str
    title: str
    prereqs: list[str]
    teaches: list[str]
    length: str | None = None


@dataclass
class Syllabus:
    baseline: set[str]
    clusters: set[str]
    concepts: dict[str, str]
    units: dict[str, Unit]


@dataclass
class Blueprint:
    raw: dict[str, Any]

    @property
    def total_points(self) -> int:
        return int(self.raw["total_points"])

    @property
    def texture(self) -> dict[str, Any]:
        return self.raw.get("texture", {})

    @property
    def sections(self) -> list[dict[str, Any]]:
        return self.raw.get("sections", [])

    @property
    def topic_distribution(self) -> dict[str, Any]:
        return self.raw.get("topic_distribution", {})

    @property
    def cluster_fold(self) -> dict[str, str]:
        return self.raw.get("cluster_fold", {})

    @property
    def difficulty_mix(self) -> dict[str, Any]:
        return self.raw.get("difficulty_mix", {})

    @property
    def provenance_rules(self) -> dict[str, Any]:
        return self.raw.get("provenance_rules", {})


@dataclass(frozen=True)
class PracticeProblem:
    id: str
    concepts: list[str]
    path: str
    solution_path: str


@dataclass
class UnitManifest:
    unit_id: str
    concepts_taught: list[str]
    concepts_used: list[str]
    prereq_units: list[str]
    practice: list[PracticeProblem]
    path: Path


@dataclass
class ManifestProblem:
    id: str
    section: str
    units: list[str]
    concepts: list[str]
    points: int
    difficulty: str
    type: str
    answer_form: str
    provenance: str
    adapted_from: str | None
    spec: str
    answer_key: Any
    answer_tolerance: float | None
    data: dict[str, Any] | None
    cluster: str | None
    files: list[str]


def _validated_status(value: object, path: Path) -> str:
    if value not in ("draft", "final"):
        raise ValueError(f"{path}: status must be 'draft' or 'final', got {value!r}")
    return str(value)


@dataclass
class MockManifest:
    test: str
    blueprint_version: int
    generated: str | None
    status: str
    generation_parameters: dict[str, Any]
    duration_minutes: int
    total_points: int
    time_budget: dict[str, int]
    problems: list[ManifestProblem]
    path: Path


@dataclass
class Report:
    name: str
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped: str | None = None


@dataclass(frozen=True)
class EvidenceAnchor:
    path: str
    heading: str
    cell_ordinal: int
    role: str


@dataclass(frozen=True)
class EvidenceReference:
    id: str
    role: str


@dataclass(frozen=True)
class ModalityEvidence:
    lesson_anchors: list[EvidenceAnchor]
    practices: list[EvidenceReference]
    assessments: list[EvidenceReference]


@dataclass(frozen=True)
class HourRange:
    minimum: float
    maximum: float


@dataclass(frozen=True)
class PlannedUnit:
    id: str
    title: str
    layer: str
    prerequisites: list[str]
    knowledge_points: list[str]
    provisional_concepts: list[str]
    estimated_hours: HourRange
    schedule_action: str | None


@dataclass(frozen=True)
class KnowledgePoint:
    id: str
    layer: str
    requirement: str
    coverage: str
    source_refs: list[str]
    depends_on: list[str]
    shipped_concepts: list[str]
    evidence_by_modality: dict[str, ModalityEvidence]
    disposition: str
    destination: str | None
    modalities_missing: list[str]
    rationale: str
    consequence: str


@dataclass(frozen=True)
class Roadmap:
    roadmap_version: int
    layers: list[str]
    planned_units: list[PlannedUnit]
    knowledge_points: list[KnowledgePoint]


def _evidence_reference(raw: dict[str, Any]) -> EvidenceReference:
    return EvidenceReference(id=str(raw["id"]), role=str(raw.get("role", "")))


def _modality_evidence(raw: dict[str, Any]) -> ModalityEvidence:
    return ModalityEvidence(
        lesson_anchors=[
            EvidenceAnchor(
                path=str(item["path"]),
                heading=str(item["heading"]),
                cell_ordinal=int(item["cell_ordinal"]),
                role=str(item.get("role", "")),
            )
            for item in raw.get("lesson_anchors") or []
        ],
        practices=[_evidence_reference(item) for item in raw.get("practices") or []],
        assessments=[_evidence_reference(item) for item in raw.get("assessments") or []],
    )


def load_roadmap(root: str | Path) -> Roadmap:
    raw = _read_manifest(Path(root) / "curriculum" / "coverage-map.yaml")
    planned_units = []
    for item in raw.get("planned_units") or []:
        hours = item.get("estimated_hours") or {}
        planned_units.append(
            PlannedUnit(
                id=str(item["id"]),
                title=str(item["title"]),
                layer=str(item["layer"]),
                prerequisites=[str(value) for value in item.get("prerequisites") or []],
                knowledge_points=[str(value) for value in item.get("knowledge_points") or []],
                provisional_concepts=[
                    str(value) for value in item.get("provisional_concepts") or []
                ],
                estimated_hours=HourRange(
                    minimum=float(hours["min"]), maximum=float(hours["max"])
                ),
                schedule_action=(
                    str(item["schedule_action"])
                    if item.get("schedule_action") is not None
                    else None
                ),
            )
        )
    knowledge_points = []
    for item in raw.get("knowledge_points") or []:
        evidence = {
            str(modality): _modality_evidence(value or {})
            for modality, value in (item.get("evidence_by_modality") or {}).items()
        }
        knowledge_points.append(
            KnowledgePoint(
                id=str(item["id"]),
                layer=str(item["layer"]),
                requirement=str(item["requirement"]),
                coverage=str(item["coverage"]),
                source_refs=[str(value) for value in item.get("source_refs") or []],
                depends_on=[str(value) for value in item.get("depends_on") or []],
                shipped_concepts=[str(value) for value in item.get("shipped_concepts") or []],
                evidence_by_modality=evidence,
                disposition=str(item["disposition"]),
                destination=(str(item["destination"]) if item.get("destination") else None),
                modalities_missing=[
                    str(value)
                    for value in (item.get("deficits") or {}).get("modalities_missing") or []
                ],
                rationale=str(item.get("rationale", "")),
                consequence=str(item.get("consequence", "")),
            )
        )
    return Roadmap(
        roadmap_version=int(raw["roadmap_version"]),
        layers=[str(value) for value in raw.get("layers") or []],
        planned_units=planned_units,
        knowledge_points=knowledge_points,
    )





def _parse_yaml(text: str) -> Any:
    return yaml.safe_load(text)



def _canonical_yaml(markdown: str) -> str:
    sentinel = "<!-- syllabus-canonical -->"
    if markdown.count(sentinel) != 1:
        raise ValueError("syllabus canonical sentinel must appear exactly once")
    after = markdown.split(sentinel, 1)[1]
    match = re.search(r"```yaml\n(.*?)\n```", after, re.DOTALL)
    if match is None:
        raise ValueError("missing syllabus canonical yaml fence")
    return match.group(1)


def load_syllabus(root: str | Path) -> Syllabus:
    root = Path(root)
    raw = _parse_yaml(_canonical_yaml((root / "syllabus.md").read_text()))
    baseline = {item for values in raw["baseline"].values() for item in values}
    concepts = {entry["id"]: entry["cluster"] for entry in raw["concepts"]}
    units = {
        entry["id"]: Unit(
            id=entry["id"],
            track=entry["track"],
            title=entry["title"],
            prereqs=list(entry.get("prereqs", [])),
            teaches=list(entry.get("teaches", [])),
            length=entry.get("length"),
        )
        for entry in raw["units"]
    }
    return Syllabus(baseline=baseline, clusters=set(raw["clusters"]), concepts=concepts, units=units)


def load_blueprint(root: str | Path) -> Blueprint:
    raw = _parse_yaml((Path(root) / "mocktests" / "blueprint.yaml").read_text())
    return Blueprint(raw=raw)


def _read_manifest(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        return json.loads(path.read_text())
    return _parse_yaml(path.read_text())


def load_unit_manifests(root: str | Path) -> list[UnitManifest]:
    manifests = sorted(Path(root).glob("units/*/manifest.yaml"))
    result: list[UnitManifest] = []
    for path in manifests:
        raw = _read_manifest(path)
        result.append(
            UnitManifest(
                unit_id=raw["unit"],
                concepts_taught=list(raw.get("concepts_taught", [])),
                concepts_used=list(raw.get("concepts_used", [])),
                prereq_units=list(raw.get("prereq_units", [])),
                practice=[
                    PracticeProblem(
                        id=item["id"],
                        concepts=list(item.get("concepts", [])),
                        path=item["path"],
                        solution_path=item["solution_path"],
                    )
                    for item in raw.get("practice") or []
                ],
                path=path,
            )
        )
    return result


def _problem_from(item: dict[str, Any]) -> ManifestProblem:
    raw_tolerance = item.get("answer_tolerance")
    answer_tolerance = None if raw_tolerance is None else float(raw_tolerance)
    if answer_tolerance is not None and answer_tolerance < 0:
        raise ValueError("answer_tolerance must be non-negative")
    return ManifestProblem(
        id=item["id"],
        section=item["section"],
        units=list(item.get("units", [])),
        concepts=list(item.get("concepts", [])),
        points=int(item.get("points", 0)),
        difficulty=item.get("difficulty", ""),
        type=item.get("type", ""),
        answer_form=item.get("answer_form", ""),
        provenance=item.get("provenance", ""),
        adapted_from=item.get("adapted-from") or item.get("adapted_from"),
        spec=item.get("spec", ""),
        answer_key=item.get("answer_key"),
        answer_tolerance=answer_tolerance,
        data=item.get("data"),
        cluster=item.get("cluster"),
        files=list(item.get("files", [])),
    )


def load_mock_manifests(root: str | Path) -> list[MockManifest]:
    result: list[MockManifest] = []
    for path in sorted(Path(root).glob("mocktests/r1-*/manifest.yaml")):
        raw = _read_manifest(path)
        problems = []
        for index, item in enumerate(raw.get("problems") or []):
            try:
                problems.append(_problem_from(item))
            except KeyError as exc:
                raise ValueError(
                    f"{path}: problems[{index}] missing required field {exc}"
                ) from exc
        result.append(
            MockManifest(
                test=raw["test"],
                blueprint_version=int(raw.get("blueprint_version", 0)),
                generated=str(raw["generated"]) if raw.get("generated") is not None else None,
                status=_validated_status(raw.get("status", "final"), path),
                generation_parameters=dict(raw.get("generation_parameters", {})),
                duration_minutes=int(raw.get("duration_minutes", 0)),
                total_points=int(raw.get("total_points", 0)),
                time_budget={k: int(v) for k, v in raw.get("time_budget", {}).items()},
                problems=problems,
                path=path,
            )
        )
    return result
