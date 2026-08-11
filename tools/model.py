from __future__ import annotations

import json
import os
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
    book: int = 1
    layer: str = "round-1-core"
    round: int = 1
    concept_prerequisites: list[str] = field(default_factory=list)
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
class ComputePolicy:
    policy: str
    seed: int | None


@dataclass(frozen=True)
class PracticeProblem:
    id: str
    concepts: list[str]
    path: str
    solution_path: str
    minutes: int | None = None
    after_session: int | None = None
    compute: ComputePolicy = field(
        default_factory=lambda: ComputePolicy(policy="cpu", seed=None)
    )


@dataclass(frozen=True)
class BridgeDiagnostic:
    path: str
    minutes: int
    referenced_concepts: list[str]


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
class CoverageClaim:
    knowledge_point: str
    first_session: int
    modalities: list[str]
    evidence_concepts: list[str]
    evidence_by_modality: dict[str, ModalityEvidence]


@dataclass
class UnitManifest:
    unit_id: str
    concepts_taught: list[str]
    concepts_used: list[str]
    prereq_units: list[str]
    practice: list[PracticeProblem]
    path: Path
    book: int = 1
    layer: str = "round-1-core"
    round: int = 1
    track: str = "core"
    concept_prerequisites: list[str] = field(default_factory=list)
    bridge_diagnostic: BridgeDiagnostic | None = None
    coverage_claims: list[CoverageClaim] = field(default_factory=list)
    lesson_sessions: list[int] | None = None
    concept_sessions: dict[str, int] | None = None


@dataclass(frozen=True)
class ScheduleAllocation:
    kind: str
    minutes: int
    unit: str | None = None
    session: int | None = None
    chunk: int | None = None
    test: str | None = None
    problem_ids: list[str] | None = None


@dataclass(frozen=True)
class ScheduleWeek:
    week: int
    semester: int
    allocations: list[ScheduleAllocation]


@dataclass(frozen=True)
class CourseSchedule:
    schedule_version: int
    weeks: list[ScheduleWeek]
    semester_week_counts: tuple[int, int] | None = None
    declared_week_count: int | None = None
    semester_minutes: tuple[int, int] | None = None
    declared_total_minutes: int | None = None

    @property
    def total_minutes(self) -> int:
        return sum(
            allocation.minutes
            for week in self.weeks
            for allocation in week.allocations
        )


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
                rationale=str(item["rationale"]),
                consequence=str(item["consequence"]),
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


def _validated_content_path(root: str | Path, relative: str) -> Path:
    normalized_root = Path(os.path.abspath(root))
    if (
        normalized_root.is_symlink()
        or normalized_root.resolve(strict=False) != normalized_root
    ):
        raise ValueError(
            f"{normalized_root}: content root is symlinked or noncanonical"
        )
    path = normalized_root / relative
    current = normalized_root
    for part in Path(relative).parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f"{path}: content path contains a symlink")
    if not path.resolve(strict=False).is_relative_to(normalized_root):
        raise ValueError(f"{path}: content path escapes its canonical root")
    return path


def load_syllabus_contract(root: str | Path) -> dict[str, Any]:
    """Return the persisted canonical syllabus mapping for one content root."""
    path = _validated_content_path(root, "syllabus.md")
    raw = _parse_yaml(_canonical_yaml(path.read_text(encoding="utf-8")))
    if not isinstance(raw, dict):
        raise ValueError(  # noqa: TRY004
            f"{path}: canonical syllabus must be a mapping"
        )
    return raw


def _string_list(value: object, *, field_name: str, path: Path) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{path}: {field_name} must be a list of strings")
    return list(value)


def _positive_int(value: object, *, field_name: str, path: Path) -> int:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{path}: {field_name} must be a positive integer")
    return value


def _unit_contract(
    raw: dict[str, Any],
    *,
    path: Path,
    default_track: str,
) -> tuple[int, str, int, str]:
    unit_id = str(raw.get("id", raw.get("unit", "")))
    is_book2 = unit_id.startswith("B2-") or raw.get("book") == 2
    required = ("book", "layer", "round", "track")
    if is_book2:
        missing = [field_name for field_name in required if field_name not in raw]
        if missing:
            raise ValueError(
                f"{path}: Book 2 record {unit_id} missing required field(s) {missing}"
            )
    track = raw.get("track", default_track)
    if not isinstance(track, str) or not track:
        raise ValueError(f"{path}: track must be a nonempty string")
    book = raw.get("book", 1)
    round_number = raw.get("round", 1)
    layer = raw.get(
        "layer", "shared-foundation" if track == "foundation" else "round-1-core"
    )
    if type(book) is not int or book not in {1, 2}:
        raise ValueError(f"{path}: book must be integer 1 or 2")
    if type(round_number) is not int or round_number not in {1, 2}:
        raise ValueError(f"{path}: round must be integer 1 or 2")
    if not isinstance(layer, str) or not layer:
        raise ValueError(f"{path}: layer must be a nonempty string")
    if unit_id.startswith("B2-") and (
        book,
        round_number,
        layer,
        track,
    ) != (2, 2, "round-2-extension", "extension"):
        raise ValueError(
            f"{path}: B2-* records must declare the canonical Book 2 tuple "
            "(book=2, round=2, layer=round-2-extension, track=extension)"
        )
    return book, layer, round_number, track


def load_syllabus(root: str | Path) -> Syllabus:
    root = Path(root)
    path = root / "syllabus.md"
    raw = load_syllabus_contract(root)
    baseline = {item for values in raw["baseline"].values() for item in values}
    concepts = {entry["id"]: entry["cluster"] for entry in raw["concepts"]}
    units: dict[str, Unit] = {}
    for entry in raw["units"]:
        unit_id = str(entry["id"])
        book, layer, round_number, track = _unit_contract(
            entry, path=path, default_track=str(entry.get("track", ""))
        )
        if (unit_id.startswith("B2-") or book == 2) and "concept_prerequisites" not in entry:
            raise ValueError(
                f"{path}: Book 2 record {unit_id} missing required field "
                "concept_prerequisites"
            )
        units[unit_id] = Unit(
            id=unit_id,
            track=track,
            title=str(entry["title"]),
            prereqs=_string_list(entry.get("prereqs", []), field_name="prereqs", path=path),
            teaches=_string_list(entry.get("teaches", []), field_name="teaches", path=path),
            book=book,
            layer=layer,
            round=round_number,
            concept_prerequisites=_string_list(
                entry.get("concept_prerequisites", []),
                field_name="concept_prerequisites",
                path=path,
            ),
            length=entry.get("length"),
        )
    return Syllabus(baseline=baseline, clusters=set(raw["clusters"]), concepts=concepts, units=units)


def load_blueprint(root: str | Path) -> Blueprint:
    raw = _parse_yaml((Path(root) / "mocktests" / "blueprint.yaml").read_text())
    return Blueprint(raw=raw)


def _read_manifest(path: Path) -> dict[str, Any]:
    if path.suffix == ".json":
        return json.loads(path.read_text())
    return _parse_yaml(path.read_text())


def _lesson_sessions(raw: dict[str, Any], path: Path) -> list[int] | None:
    if "estimated_minutes" not in raw:
        return None
    estimated_minutes = raw["estimated_minutes"]
    if not isinstance(estimated_minutes, dict):
        raise ValueError(  # noqa: TRY004
            f"{path}: estimated_minutes must be a mapping when present"
        )
    if "lesson_sessions" not in estimated_minutes:
        return None
    lesson_sessions = estimated_minutes["lesson_sessions"]
    field = "estimated_minutes.lesson_sessions"
    if not isinstance(lesson_sessions, list):
        raise ValueError(f"{path}: {field} must be a list")  # noqa: TRY004
    for index, value in enumerate(lesson_sessions):
        if type(value) is not int:
            raise ValueError(f"{path}: {field} item {index} must be an integer")
        if value <= 0:
            raise ValueError(f"{path}: {field} item {index} must be positive")
    return lesson_sessions


def load_unit_manifests(root: str | Path) -> list[UnitManifest]:
    root = Path(root)
    manifests = sorted(root.glob("units/*/manifest.yaml"))
    syllabus_path = root / "syllabus.md"
    syllabus_units = load_syllabus(root).units if syllabus_path.is_file() else {}
    result: list[UnitManifest] = []
    for path in manifests:
        raw = _read_manifest(path)
        unit_id = str(raw["unit"])
        syllabus_unit = syllabus_units.get(unit_id)
        default_track = syllabus_unit.track if syllabus_unit is not None else (
            "foundation" if unit_id.startswith("F") else "core"
        )
        book, layer, round_number, track = _unit_contract(
            raw, path=path, default_track=default_track
        )
        is_book2 = unit_id.startswith("B2-") or book == 2
        if is_book2:
            required = (
                "concept_prerequisites",
                "bridge_diagnostic",
                "coverage_claims",
            )
            missing = [field_name for field_name in required if field_name not in raw]
            if missing:
                if "bridge_diagnostic" in missing:
                    raise ValueError(
                        f"{path}: bridge_diagnostic is required for Book 2"
                    )
                raise ValueError(
                    f"{path}: Book 2 manifest missing required field(s) {missing}"
                )
        default_concept_prerequisites = (
            syllabus_unit.concept_prerequisites if syllabus_unit is not None else []
        )
        concept_prerequisites = _string_list(
            raw.get("concept_prerequisites", default_concept_prerequisites),
            field_name="concept_prerequisites",
            path=path,
        )
        bridge_diagnostic = _bridge_diagnostic(raw, path)
        coverage_claims = _coverage_claims(raw, path)
        lesson_sessions = _lesson_sessions(raw, path)
        practice = [
            _practice_problem(item, index, path, book=book)
            for index, item in enumerate(raw.get("practice") or [])
        ]
        concepts_taught = _string_list(
            raw.get("concepts_taught", []), field_name="concepts_taught", path=path
        )
        concept_sessions = _concept_sessions(
            raw,
            path,
            concepts_taught=concepts_taught,
            lesson_sessions=lesson_sessions,
            practice=practice,
        )
        result.append(
            UnitManifest(
                unit_id=unit_id,
                concepts_taught=concepts_taught,
                concepts_used=_string_list(
                    raw.get("concepts_used", []), field_name="concepts_used", path=path
                ),
                prereq_units=_string_list(
                    raw.get("prereq_units", []), field_name="prereq_units", path=path
                ),
                practice=practice,
                path=path,
                book=book,
                layer=layer,
                round=round_number,
                track=track,
                concept_prerequisites=concept_prerequisites,
                bridge_diagnostic=bridge_diagnostic,
                coverage_claims=coverage_claims,
                lesson_sessions=lesson_sessions,
                concept_sessions=concept_sessions,
            )
        )
    return result


def _bridge_diagnostic(
    raw: dict[str, Any], path: Path
) -> BridgeDiagnostic | None:
    value = raw.get("bridge_diagnostic")
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(  # noqa: TRY004
            f"{path}: bridge_diagnostic must be a mapping"
        )
    diagnostic_path = value.get("path")
    if not isinstance(diagnostic_path, str) or not diagnostic_path:
        raise ValueError(f"{path}: bridge_diagnostic.path must be a nonempty string")
    return BridgeDiagnostic(
        path=diagnostic_path,
        minutes=_positive_int(
            value.get("minutes"), field_name="bridge_diagnostic.minutes", path=path
        ),
        referenced_concepts=_string_list(
            value.get("referenced_concepts", []),
            field_name="bridge_diagnostic.referenced_concepts",
            path=path,
        ),
    )


def _coverage_claims(raw: dict[str, Any], path: Path) -> list[CoverageClaim]:
    value = raw.get("coverage_claims", [])
    if not isinstance(value, list):
        raise ValueError(f"{path}: coverage_claims must be a list")  # noqa: TRY004
    claims: list[CoverageClaim] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(  # noqa: TRY004
                f"{path}: coverage_claims row {index} must be a mapping"
            )
        point = item.get("knowledge_point")
        if not isinstance(point, str) or not point:
            raise ValueError(
                f"{path}: coverage_claims row {index} knowledge_point must be nonempty"
            )
        evidence = item.get("evidence_by_modality", {})
        if not isinstance(evidence, dict):
            raise ValueError(  # noqa: TRY004
                f"{path}: coverage_claims row {index} evidence_by_modality must be a mapping"
            )
        claims.append(
            CoverageClaim(
                knowledge_point=point,
                first_session=_positive_int(
                    item.get("first_session"),
                    field_name=f"coverage_claims row {index} first_session",
                    path=path,
                ),
                modalities=_string_list(
                    item.get("modalities", []),
                    field_name=f"coverage_claims row {index} modalities",
                    path=path,
                ),
                evidence_concepts=_string_list(
                    item.get("evidence_concepts", []),
                    field_name=f"coverage_claims row {index} evidence_concepts",
                    path=path,
                ),
                evidence_by_modality={
                    str(modality): _modality_evidence(modality_evidence or {})
                    for modality, modality_evidence in evidence.items()
                },
            )
        )
    return claims


def _practice_problem(
    item: dict[str, Any], index: int, path: Path, *, book: int
) -> PracticeProblem:
    minutes = item.get("minutes")
    if "minutes" in item and (type(minutes) is not int or minutes <= 0):
        raise ValueError(f"{path}: practice row {index} minutes must be a positive integer")
    after_session = item.get("after_session")
    if "after_session" in item and (
        type(after_session) is not int or after_session <= 0
    ):
        raise ValueError(
            f"{path}: practice row {index} after_session must be a positive integer"
        )
    compute_value = item.get("compute")
    if book == 2 and compute_value is None:
        raise ValueError(f"{path}: practice row {index} compute is required for Book 2")
    if compute_value is None:
        compute = ComputePolicy(policy="cpu", seed=None)
    else:
        if not isinstance(compute_value, dict):
            raise ValueError(f"{path}: practice row {index} compute must be a mapping")
        policy = compute_value.get("policy")
        if not isinstance(policy, str) or not policy:
            raise ValueError(f"{path}: practice row {index} compute.policy is required")
        seed = compute_value.get("seed")
        if seed is not None and type(seed) is not int:
            raise ValueError(f"{path}: practice row {index} compute.seed must be an integer")
        compute = ComputePolicy(policy=policy, seed=seed)
    problem_path = item.get("path")
    solution_path = item.get("solution_path")
    if not isinstance(problem_path, str) or not problem_path:
        raise ValueError(f"{path}: practice row {index} path must be nonempty")
    if not isinstance(solution_path, str) or not solution_path:
        raise ValueError(f"{path}: practice row {index} solution_path must be nonempty")
    return PracticeProblem(
        id=str(item["id"]),
        concepts=_string_list(
            item.get("concepts", []), field_name=f"practice row {index} concepts", path=path
        ),
        path=problem_path,
        solution_path=solution_path,
        minutes=minutes,
        after_session=after_session,
        compute=compute,
    )


def _concept_sessions(
    raw: dict[str, Any],
    path: Path,
    *,
    concepts_taught: list[str],
    lesson_sessions: list[int] | None,
    practice: list[PracticeProblem],
) -> dict[str, int] | None:
    if "concept_sessions" not in raw:
        return None
    value = raw["concept_sessions"]
    if not isinstance(value, dict):
        raise ValueError(f"{path}: concept_sessions must be a mapping")  # noqa: TRY004
    if set(value) != set(concepts_taught):
        raise ValueError(f"{path}: concept_sessions keys must equal concepts_taught")
    session_count = len(lesson_sessions or [])
    concept_sessions: dict[str, int] = {}
    for concept in concepts_taught:
        session = value[concept]
        if type(session) is not int or session <= 0 or session > session_count:
            raise ValueError(
                f"{path}: concept_sessions[{concept!r}] must be a positive integer "
                f"within 1..{session_count}"
            )
        concept_sessions[concept] = session

    owned = set(concepts_taught)
    for index, problem in enumerate(practice):
        owned_tags = owned.intersection(problem.concepts)
        if not owned_tags:
            raise ValueError(
                f"{path}: practice row {index} must tag at least one concept taught by the unit"
            )
        if problem.after_session is None:
            raise ValueError(
                f"{path}: practice row {index} after_session is required when "
                "concept_sessions is present"
            )
        if problem.after_session > session_count:
            raise ValueError(
                f"{path}: practice row {index} after_session must be within 1..{session_count}"
            )
        floor = max(concept_sessions[concept] for concept in owned_tags)
        if problem.after_session < floor:
            raise ValueError(
                f"{path}: practice row {index} after_session {problem.after_session} "
                f"precedes concept-derived floor {floor}"
            )
    return concept_sessions


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


def _mock_manifest_path_is_unsafe(book_root: Path, manifest_path: Path) -> bool:
    absolute_root = book_root.absolute()
    absolute_manifest = manifest_path.absolute()
    if absolute_root.is_symlink() or absolute_root.resolve(strict=False) != absolute_root:
        return True
    try:
        relative = absolute_manifest.relative_to(absolute_root)
    except ValueError:
        return True
    current = absolute_root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return True
    return not absolute_manifest.resolve(strict=False).is_relative_to(absolute_root)


def load_mock_manifests(
    root: str | Path, *, book_number: int | None = None
) -> list[MockManifest]:
    if book_number is not None and (type(book_number) is not int or book_number <= 0):
        raise ValueError("book_number must be a positive integer")
    mocktests_root = Path(root) / "mocktests"
    if _mock_manifest_path_is_unsafe(Path(root), mocktests_root):
        raise ValueError(
            f"{mocktests_root}: mocktests directory contains a symlink or resolves "
            "outside selected book root"
        )
    if book_number is None:
        # Keep the pre-cutover public behavior until CLI dispatch supplies BookSpec.number.
        manifests = sorted(mocktests_root.glob("r1-*/manifest.yaml"))
    else:
        manifests = sorted(mocktests_root.glob("r*-*/manifest.yaml"))
    unsafe = [path for path in manifests if _mock_manifest_path_is_unsafe(Path(root), path)]
    if unsafe:
        names = ", ".join(str(path) for path in unsafe)
        raise ValueError(
            f"{mocktests_root}: mock manifest path contains a symlink or resolves "
            f"outside selected book root: {names}"
        )
    if book_number is not None:
        wrong_round = [
            path
            for path in manifests
            if not path.parent.name.startswith(f"r{book_number}-")
        ]
        if wrong_round:
            names = ", ".join(path.parent.name for path in wrong_round)
            raise ValueError(
                f"{mocktests_root}: book {book_number} assessments must use "
                f"r{book_number}-* directories; found {names}"
            )
    result: list[MockManifest] = []
    for path in manifests:
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
