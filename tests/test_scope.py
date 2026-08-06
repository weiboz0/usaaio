from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools import model
from tools import render_curriculum_roadmap as renderer
from tools.checks.scope import check_scope


def test_scope_checker_module_exists() -> None:
    assert (Path(__file__).parents[1] / "tools" / "checks" / "scope.py").is_file()


def test_roadmap_renderer_module_exists() -> None:
    assert (Path(__file__).parents[1] / "tools" / "render_curriculum_roadmap.py").is_file()


def test_load_roadmap_exposes_typed_contract(tmp_path: Path) -> None:
    curriculum = tmp_path / "curriculum"
    curriculum.mkdir()
    curriculum.joinpath("coverage-map.yaml").write_text(
        yaml.safe_dump(
            {
                "roadmap_version": 1,
                "layers": [
                    "shared-foundation",
                    "round-1-core",
                    "round-2-extension",
                    "optional-enrichment",
                ],
                "planned_units": [
                    {
                        "id": "R1-linear-models",
                        "title": "Linear models",
                        "layer": "round-1-core",
                        "prerequisites": ["C2-linear-models"],
                        "knowledge_points": ["normal-equations"],
                        "provisional_concepts": ["normal-equations"],
                        "estimated_hours": {"min": 2, "max": 3.5},
                        "schedule_action": "extend",
                    }
                ],
                "knowledge_points": [
                    {
                        "id": "normal-equations",
                        "layer": "round-1-core",
                        "requirement": "required",
                        "coverage": "partial",
                        "source_refs": ["official"],
                        "depends_on": [],
                        "shipped_concepts": ["linear-regression"],
                        "evidence_by_modality": {
                            "theory": {
                                "lesson_anchors": [
                                    {
                                        "path": "units/C2/lesson.ipynb",
                                        "heading": "Regression",
                                        "cell_ordinal": 1,
                                        "role": "primary",
                                    }
                                ],
                                "practices": [{"id": "C2-p01", "role": "primary"}],
                                "assessments": [{"id": "r1-p01", "role": "primary"}],
                            }
                        },
                        "disposition": "new-unit",
                        "destination": "R1-linear-models",
                        "deficits": {"modalities_missing": ["derivation"]},
                        "rationale": "The derivation remains to be taught.",
                        "consequence": "Students cannot derive the estimator yet.",
                    }
                ],
            },
            sort_keys=False,
        )
    )

    assert hasattr(model, "load_roadmap")
    roadmap = model.load_roadmap(tmp_path)

    assert roadmap.roadmap_version == 1
    assert roadmap.layers[1] == "round-1-core"
    assert roadmap.planned_units[0].estimated_hours.maximum == 3.5
    point = roadmap.knowledge_points[0]
    assert point.destination == "R1-linear-models"
    assert point.evidence_by_modality["theory"].lesson_anchors[0].heading == "Regression"
    assert point.evidence_by_modality["theory"].assessments[0].id == "r1-p01"


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def _base_contract(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    (root / "syllabus.md").write_text(
        """# Syllabus

<!-- syllabus-canonical -->
```yaml
baseline:
  mathematics: [arithmetic]
clusters: [foundation]
concepts:
  - {id: c1, cluster: foundation}
  - {id: c2, cluster: foundation}
units:
  - id: U1-core
    track: foundation
    title: Core
    prereqs: []
    teaches: [c1]
  - id: U2-unrelated
    track: foundation
    title: Unrelated
    prereqs: []
    teaches: [c2]
```
"""
    )
    for unit_id, concept in (("U1-core", "c1"), ("U2-unrelated", "c2")):
        _write_yaml(
            root / "units" / unit_id / "manifest.yaml",
            {
                "unit": unit_id,
                "concepts_taught": [concept],
                "concepts_used": [],
                "prereq_units": [],
                "estimated_minutes": {
                    "lesson_sessions": [60],
                    "practice": 120,
                    "review": 30,
                },
                "practice": [
                    {
                        "id": f"{unit_id}-p{number}",
                        "concepts": [concept],
                        "path": f"practice/p{number}.ipynb",
                        "solution_path": f"practice/p{number}_solution.ipynb",
                    }
                    for number in range(1, 4)
                ],
            },
        )
    sources = {
        "source_schema_version": 1,
        "sources": [
            {
                "id": "source-1",
                "authority": "official-syllabus",
                "review_after": "2099-01-01",
            }
        ],
    }
    topics = {
        "official_topics_schema_version": 1,
        "allowed_modalities": ["theory", "derivation"],
        "categories": [
            {
                "id": "foundation",
                "parent": None,
                "kind": "official",
                "source_refs": ["source-1"],
                "required_for": ["round-1", "round-2"],
            }
        ],
        "atomic_targets": [
            {
                "id": "topic-a",
                "parent": "foundation",
                "source_refs": ["source-1"],
                "required_for": ["round-1", "round-2"],
                "modalities": ["theory"],
            }
        ],
        "non_required_candidates": [],
    }
    inventory_notebooks = [
        {
            "path": "units/U1-core/lessons/01-lesson.ipynb",
            "anchors": [{"heading_path": ["Lesson"], "cell_ordinal": 1}],
            "declared_unit_ids": ["U1-core"],
            "declared_concept_ids": ["c1"],
            "declared_problem_ids": [],
        },
        {
            "path": "units/U2-unrelated/lessons/01-lesson.ipynb",
            "anchors": [{"heading_path": ["Lesson"], "cell_ordinal": 1}],
            "declared_unit_ids": ["U2-unrelated"],
            "declared_concept_ids": ["c2"],
            "declared_problem_ids": [],
        },
    ]
    for unit_id, concept in (("U1-core", "c1"), ("U2-unrelated", "c2")):
        for number in range(1, 4):
            inventory_notebooks.append(
                {
                    "path": f"units/{unit_id}/practice/p{number}.ipynb",
                    "anchors": [{"heading_path": ["Practice"], "cell_ordinal": 1}],
                    "declared_unit_ids": [unit_id],
                    "declared_concept_ids": [concept],
                    "declared_problem_ids": [f"{unit_id}-p{number}"],
                }
            )
    inventory = {"inventory_version": 1, "notebooks": inventory_notebooks}
    roadmap = {
        "roadmap_version": 1,
        "layers": [
            "shared-foundation",
            "round-1-core",
            "round-2-extension",
            "optional-enrichment",
        ],
        "planned_units": [],
        "knowledge_points": [
            {
                "id": "topic-a",
                "layer": "round-1-core",
                "requirement": "required",
                "coverage": "covered",
                "source_refs": ["source-1"],
                "depends_on": [],
                "shipped_concepts": ["c1"],
                "evidence_by_modality": {
                    "theory": {
                        "lesson_anchors": [
                            {
                                "path": "units/U1-core/lessons/01-lesson.ipynb",
                                "heading": "Lesson",
                                "cell_ordinal": 1,
                                "role": "primary",
                            }
                        ],
                        "practices": [
                            {"id": f"U1-core-p{number}", "role": "primary"}
                            for number in range(1, 4)
                        ],
                        "assessments": [],
                    }
                },
                "disposition": "keep",
                "destination": "U1-core",
                "deficits": {"modalities_missing": []},
                "rationale": "Current primary evidence satisfies the contract.",
                "consequence": "No current gap.",
            }
        ],
    }
    _write_yaml(root / "curriculum" / "sources.yaml", sources)
    _write_yaml(root / "curriculum" / "official-topics.yaml", topics)
    _write_yaml(root / "curriculum" / "material-inventory.yaml", inventory)
    _write_yaml(root / "curriculum" / "coverage-map.yaml", roadmap)
    reconciliation = root / "docs" / "audits" / "015-plan014-reconciliation.md"
    reconciliation.parent.mkdir(parents=True)
    reconciliation.write_text(
        """# Plan 014 reconciliation

Plan 014 is **abandoned**.
- Branch/PR: feature/plan-014 / PR #14
- Date: 2026-08-06
- Reason: Superseded by an owner-approved replacement.
- Owner decision: The curriculum owner explicitly abandoned Plan 014.
"""
    )
    (root / "docs" / "course-structure.md").write_text(
        "# Schedule\n\nThe course ends with a 15-minute debrief.\n"
    )
    return {"sources": sources, "topics": topics, "inventory": inventory, "roadmap": roadmap}


def _report_after(root: Path, mutate: Callable[[dict[str, Any]], None]):
    contract = _base_contract(root)
    mutate(contract)
    for name, filename in (
        ("sources", "sources.yaml"),
        ("topics", "official-topics.yaml"),
        ("inventory", "material-inventory.yaml"),
        ("roadmap", "coverage-map.yaml"),
    ):
        _write_yaml(root / "curriculum" / filename, contract[name])
    return check_scope(root)


def _assert_error(report: model.Report, text: str) -> None:
    assert not report.ok
    assert any(text in error for error in report.errors), report.errors


def test_minimal_scope_contract_is_valid(tmp_path: Path) -> None:
    _base_contract(tmp_path)

    report = check_scope(tmp_path)

    assert report.ok, report.errors
    assert not report.errors


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data["roadmap"].update(roadmap_version=2), "unsupported roadmap_version"),
        (
            lambda data: data["roadmap"].update(layers=list(reversed(data["roadmap"]["layers"]))),
            "layers must exactly equal",
        ),
        (
            lambda data: data["sources"]["sources"][0].update(review_after="2020-01-01"),
            "source-refresh change",
        ),
        (
            lambda data: data["roadmap"]["knowledge_points"][0].update(requirement="invented"),
            "unknown requirement",
        ),
        (
            lambda data: data["roadmap"]["knowledge_points"][0].update(coverage="optional"),
            "unknown coverage",
        ),
        (
            lambda data: data["roadmap"]["knowledge_points"][0].update(disposition="invented"),
            "unknown disposition",
        ),
    ],
)
def test_schema_enums_versions_layers_and_source_freshness_fail(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None], message: str
) -> None:
    _assert_error(_report_after(tmp_path, mutate), message)


def test_atomic_target_closure_rejects_missing_and_duplicate_rows(tmp_path: Path) -> None:
    missing = _report_after(tmp_path / "missing", lambda data: data["roadmap"].update(knowledge_points=[]))
    _assert_error(missing, "missing official atomic target topic-a")

    def duplicate(data: dict[str, Any]) -> None:
        data["roadmap"]["knowledge_points"].append(
            dict(data["roadmap"]["knowledge_points"][0])
        )

    _assert_error(_report_after(tmp_path / "duplicate", duplicate), "duplicate knowledge point topic-a")


@pytest.mark.parametrize("broken", ["unknown-parent", "category-cycle", "category-round", "topic-round"])
def test_category_dag_and_full_round_inheritance_fail(tmp_path: Path, broken: str) -> None:
    def mutate(data: dict[str, Any]) -> None:
        categories = data["topics"]["categories"]
        target = data["topics"]["atomic_targets"][0]
        if broken == "unknown-parent":
            categories[0]["parent"] = "nowhere"
        elif broken == "category-cycle":
            categories.append(
                {
                    "id": "child",
                    "parent": "foundation",
                    "kind": "official-subcategory",
                    "source_refs": ["source-1"],
                    "required_for": ["round-1", "round-2"],
                }
            )
            categories[0]["parent"] = "child"
        elif broken == "category-round":
            categories.append(
                {
                    "id": "child",
                    "parent": "foundation",
                    "kind": "official-subcategory",
                    "source_refs": ["source-1"],
                    "required_for": ["round-2"],
                }
            )
        else:
            target["required_for"] = ["round-2"]

    _assert_error(_report_after(tmp_path, mutate), "inherited required_for")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_refs", ["unknown-source"], "unknown source"),
        ("shipped_concepts", ["unknown-concept"], "unknown shipped concept"),
        ("layer", "unknown-layer", "unknown layer"),
        ("depends_on", ["unknown-topic"], "unknown dependency"),
        ("destination", "unknown-unit", "unknown destination"),
    ],
)
def test_unknown_roadmap_references_fail(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"]["knowledge_points"][0][field] = value

    _assert_error(_report_after(tmp_path, mutate), message)


def test_unrelated_but_valid_evidence_does_not_count(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        evidence = data["roadmap"]["knowledge_points"][0]["evidence_by_modality"]["theory"]
        evidence["lesson_anchors"][0]["path"] = (
            "units/U2-unrelated/lessons/01-lesson.ipynb"
        )
        evidence["practices"] = [
            {"id": f"U2-unrelated-p{number}", "role": "primary"} for number in range(1, 4)
        ]

    report = _report_after(tmp_path, mutate)
    _assert_error(report, "does not teach any shipped_concepts")
    _assert_error(report, "does not tag any shipped_concepts")


def test_unknown_and_non_primary_evidence_references_fail(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        evidence = data["roadmap"]["knowledge_points"][0]["evidence_by_modality"]["theory"]
        evidence["lesson_anchors"][0]["cell_ordinal"] = 999
        evidence["practices"][0] = {"id": "missing-practice", "role": "secondary"}
        evidence["assessments"] = [{"id": "missing-assessment", "role": "primary"}]

    report = _report_after(tmp_path, mutate)
    _assert_error(report, "unknown lesson anchor")
    _assert_error(report, "unknown practice evidence")
    _assert_error(report, "unknown assessment evidence")
    _assert_error(report, "role must be primary")


def test_evidence_modalities_and_deficits_are_not_open_ended(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        point["evidence_by_modality"]["invented"] = {
            "lesson_anchors": [],
            "practices": [],
        }
        point["deficits"]["practice_shortfall"] = 0

    report = _report_after(tmp_path, mutate)

    _assert_error(report, "unknown evidence modality invented")
    _assert_error(report, "practice_shortfall is checker-derived")


def test_full_inventory_heading_path_is_the_anchor_identity(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        lesson = data["inventory"]["notebooks"][0]
        lesson["anchors"][0]["heading_path"] = ["Top", "Lesson"]
        anchor = data["roadmap"]["knowledge_points"][0]["evidence_by_modality"]["theory"]
        anchor["lesson_anchors"][0]["heading"] = "Top > Lesson"

    report = _report_after(tmp_path, mutate)

    assert report.ok, report.errors


def test_taught_without_practice_is_partial_with_no_modality_gap(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        point["coverage"] = "partial"
        point["evidence_by_modality"]["theory"]["practices"] = []
        point["deficits"]["modalities_missing"] = []

    report = _report_after(tmp_path, mutate)

    assert report.ok, report.errors
    assert any("practice shortfall 3" in warning for warning in report.warnings)


def test_practice_without_teaching_is_partial_with_modality_gap(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        point["coverage"] = "partial"
        point["evidence_by_modality"]["theory"]["lesson_anchors"] = []
        point["deficits"]["modalities_missing"] = ["theory"]

    report = _report_after(tmp_path, mutate)

    assert report.ok, report.errors


def test_lesson_evidence_rejects_a_valid_same_concept_practice_anchor(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        anchor = data["roadmap"]["knowledge_points"][0]["evidence_by_modality"]["theory"]
        anchor["lesson_anchors"][0] = {
            "path": "units/U1-core/practice/p1.ipynb",
            "heading": "Practice",
            "cell_ordinal": 1,
            "role": "primary",
        }

    _assert_error(_report_after(tmp_path, mutate), "not a unit lesson-session notebook")


def test_markdown_only_mock_problem_is_a_known_assessment(tmp_path: Path) -> None:
    contract = _base_contract(tmp_path)
    _write_yaml(
        tmp_path / "mocktests" / "r1-mini" / "manifest.yaml",
        {
            "test": "r1-mini",
            "duration_minutes": 30,
            "problems": [{"id": "r1-mini-p01", "files": ["problems/p01.md"]}],
        },
    )
    evidence = contract["roadmap"]["knowledge_points"][0]["evidence_by_modality"]["theory"]
    evidence["assessments"] = [{"id": "r1-mini-p01", "role": "primary"}]
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    report = check_scope(tmp_path)

    assert report.ok, report.errors


@pytest.mark.parametrize(
    ("coverage", "lessons", "practices", "deficits", "message"),
    [
        ("covered", True, 2, [], "derived coverage is partial"),
        ("missing", True, 0, [], "derived coverage is partial"),
        ("partial", False, 0, [], "modalities_missing must exactly equal"),
    ],
)
def test_coverage_and_exact_deficits_are_checker_derived(
    tmp_path: Path,
    coverage: str,
    lessons: bool,
    practices: int,
    deficits: list[str],
    message: str,
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        point["coverage"] = coverage
        point["deficits"]["modalities_missing"] = deficits
        evidence = point["evidence_by_modality"]["theory"]
        if not lessons:
            evidence["lesson_anchors"] = []
        evidence["practices"] = evidence["practices"][:practices]

    _assert_error(_report_after(tmp_path, mutate), message)


def test_assessment_evidence_does_not_replace_unit_practice(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        evidence = point["evidence_by_modality"]["theory"]
        evidence["practices"] = []
        evidence["assessments"] = [
            {"id": f"U1-core-p{number}", "role": "primary"} for number in range(1, 4)
        ]
        point["coverage"] = "partial"
        point["deficits"]["modalities_missing"] = []

    report = _report_after(tmp_path, mutate)
    assert report.ok, report.errors
    assert any("practice shortfall 3" in warning for warning in report.warnings)


def _add_r2_point(data: dict[str, Any]) -> None:
    data["topics"]["categories"].append(
        {
            "id": "round-2-category",
            "parent": None,
            "kind": "official",
            "source_refs": ["source-1"],
            "required_for": ["round-2"],
        }
    )
    data["topics"]["atomic_targets"].append(
        {
            "id": "topic-b",
            "parent": "round-2-category",
            "source_refs": ["source-1"],
            "required_for": ["round-2"],
            "modalities": ["theory"],
        }
    )
    data["roadmap"]["planned_units"].append(
        {
            "id": "R2-topic-b",
            "title": "Topic B",
            "layer": "round-2-extension",
            "prerequisites": [],
            "knowledge_points": ["topic-b"],
            "provisional_concepts": ["topic-b-concept"],
            "estimated_hours": {"min": 1, "max": 2},
        }
    )
    data["roadmap"]["knowledge_points"].append(
        {
            "id": "topic-b",
            "layer": "round-2-extension",
            "requirement": "required",
            "coverage": "missing",
            "source_refs": ["source-1"],
            "depends_on": [],
            "shipped_concepts": [],
            "evidence_by_modality": {"theory": {"lesson_anchors": [], "practices": []}},
            "disposition": "new-unit",
            "destination": "R2-topic-b",
            "deficits": {"modalities_missing": ["theory"]},
            "rationale": "Not shipped.",
            "consequence": "Required for Round 2.",
        }
    )


@pytest.mark.parametrize("broken", ["layer", "owner", "dependency"])
def test_round_1_boundary_rejects_round_2_placement_ownership_and_dependency(
    tmp_path: Path, broken: str
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        _add_r2_point(data)
        point = data["roadmap"]["knowledge_points"][0]
        if broken == "layer":
            point["layer"] = "round-2-extension"
        elif broken == "owner":
            point["disposition"] = "new-unit"
            point["destination"] = "R2-topic-b"
            data["roadmap"]["planned_units"][0]["knowledge_points"].append("topic-a")
        else:
            point["depends_on"] = ["topic-b"]

    _assert_error(_report_after(tmp_path, mutate), "Round-1-required topic-a")


def test_official_target_cannot_be_optional(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"]["knowledge_points"][0]["requirement"] = "optional"

    _assert_error(_report_after(tmp_path, mutate), "official atomic target topic-a cannot be optional")


@pytest.mark.parametrize("field", ["rationale", "consequence"])
def test_rationale_and_consequence_are_required(tmp_path: Path, field: str) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"]["knowledge_points"][0][field] = "  "

    _assert_error(_report_after(tmp_path, mutate), f"nonempty {field}")


@pytest.mark.parametrize("field", ["rationale", "consequence"])
def test_roadmap_loader_rejects_omitted_explanations(tmp_path: Path, field: str) -> None:
    contract = _base_contract(tmp_path)
    contract["roadmap"]["knowledge_points"][0].pop(field)
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    with pytest.raises(KeyError, match=field):
        model.load_roadmap(tmp_path)


def test_roadmap_rejects_non_official_knowledge_points(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        extra = dict(data["roadmap"]["knowledge_points"][0])
        extra["id"] = "extra-topic"
        data["roadmap"]["knowledge_points"].append(extra)

    _assert_error(_report_after(tmp_path, mutate), "extra non-official knowledge point")


def test_knowledge_point_source_refs_must_exactly_match_target(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["sources"]["sources"].append(
            {"id": "source-2", "authority": "design-rationale", "review_after": "2099-01-01"}
        )
        data["roadmap"]["knowledge_points"][0]["source_refs"].append("source-2")

    _assert_error(_report_after(tmp_path, mutate), "source_refs must exactly match")


def test_dependency_cycle_fails(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"]["knowledge_points"][0]["depends_on"] = ["topic-a"]

    _assert_error(_report_after(tmp_path, mutate), "knowledge-point dependency cycle")


def test_dependency_may_reference_a_shipped_concept(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"]["knowledge_points"][0]["depends_on"] = ["c1"]

    report = _report_after(tmp_path, mutate)

    assert report.ok, report.errors


def test_partial_and_missing_require_a_destination(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        point["coverage"] = "missing"
        point["evidence_by_modality"]["theory"] = {"lesson_anchors": [], "practices": []}
        point["deficits"]["modalities_missing"] = ["theory"]
        point["destination"] = None

    _assert_error(_report_after(tmp_path, mutate), "missing topic-a requires a destination")


@pytest.mark.parametrize("broken", ["zero-owner", "multiple-owner"])
def test_exactly_one_destination_owner_is_required(tmp_path: Path, broken: str) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        if broken == "zero-owner":
            point["disposition"] = "new-unit"
        else:
            data["roadmap"]["planned_units"].append(
                {
                    "id": "R1-duplicate",
                    "title": "Duplicate",
                    "layer": "round-1-core",
                    "prerequisites": [],
                    "knowledge_points": ["topic-a"],
                    "provisional_concepts": ["future-c"],
                    "estimated_hours": {"min": 1, "max": 1},
                    "schedule_action": "extend",
                }
            )

    _assert_error(_report_after(tmp_path, mutate), "must have exactly one destination owner")


@pytest.mark.parametrize("disposition", ["keep", "extend-existing-unit"])
def test_existing_unit_dispositions_require_existing_destination(
    tmp_path: Path, disposition: str
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        point["disposition"] = disposition
        point["destination"] = "R1-new"
        data["roadmap"]["planned_units"] = [
            {
                "id": "R1-new",
                "title": "New",
                "layer": "round-1-core",
                "prerequisites": [],
                "knowledge_points": ["topic-a"],
                "provisional_concepts": ["future-c"],
                "estimated_hours": {"min": 1, "max": 2},
                "schedule_action": "extend",
            }
        ]

    _assert_error(_report_after(tmp_path, mutate), "requires an existing-unit destination")


def test_new_unit_disposition_requires_planned_destination_owner(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        point["disposition"] = "new-unit"
        point["destination"] = "U1-core"

    _assert_error(_report_after(tmp_path, mutate), "requires a planned-unit destination owner")


@pytest.mark.parametrize("broken", ["negative", "reversed", "missing-action", "bad-action"])
def test_planned_unit_hours_and_round_1_schedule_action_fail(tmp_path: Path, broken: str) -> None:
    def mutate(data: dict[str, Any]) -> None:
        point = data["roadmap"]["knowledge_points"][0]
        point["disposition"] = "new-unit"
        point["destination"] = "R1-topic-a"
        unit = {
            "id": "R1-topic-a",
            "title": "Topic A",
            "layer": "round-1-core",
            "prerequisites": ["U1-core"],
            "knowledge_points": ["topic-a"],
            "provisional_concepts": ["future-c"],
            "estimated_hours": {"min": 1, "max": 2},
            "schedule_action": "split",
        }
        data["roadmap"]["planned_units"] = [unit]
        if broken == "negative":
            unit["estimated_hours"]["min"] = -1
        elif broken == "reversed":
            unit["estimated_hours"] = {"min": 3, "max": 2}
        elif broken == "missing-action":
            unit.pop("schedule_action")
        else:
            unit["schedule_action"] = "delay"

    _assert_error(_report_after(tmp_path, mutate), "planned unit R1-topic-a")


def test_planned_prerequisite_and_owned_knowledge_point_references_are_known(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        _add_r2_point(data)
        unit = data["roadmap"]["planned_units"][0]
        unit["prerequisites"] = ["unknown-unit"]
        unit["knowledge_points"].append("unknown-topic")

    report = _report_after(tmp_path, mutate)
    _assert_error(report, "unknown prerequisite")
    _assert_error(report, "unknown owned knowledge point")


def test_planned_unit_prerequisite_cycle_fails(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        _add_r2_point(data)
        data["roadmap"]["planned_units"][0]["prerequisites"] = ["R2-second"]
        data["roadmap"]["planned_units"].append(
            {
                "id": "R2-second",
                "title": "Second",
                "layer": "round-2-extension",
                "prerequisites": ["R2-topic-b"],
                "knowledge_points": [],
                "provisional_concepts": ["second-concept"],
                "estimated_hours": {"min": 1, "max": 1},
            }
        )

    _assert_error(_report_after(tmp_path, mutate), "planned-unit prerequisite cycle")


def test_provisional_concepts_cannot_ship_early(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        _add_r2_point(data)
        data["roadmap"]["planned_units"][0]["provisional_concepts"] = ["c1"]

    _assert_error(_report_after(tmp_path, mutate), "provisional concept c1 already appears")


@pytest.mark.parametrize("broken", ["missing", "invalid-abandonment"])
def test_plan014_reconciliation_is_required_and_structured(tmp_path: Path, broken: str) -> None:
    _base_contract(tmp_path)
    path = tmp_path / "docs" / "audits" / "015-plan014-reconciliation.md"
    if broken == "missing":
        path.unlink()
    else:
        path.write_text("Plan 014 is **abandoned**.\n")

    _assert_error(check_scope(tmp_path), "Plan 014 reconciliation")


def test_plan014_merged_squash_commit_must_be_ancestor(tmp_path: Path) -> None:
    _base_contract(tmp_path)
    reconciliation = tmp_path / "docs" / "audits" / "015-plan014-reconciliation.md"
    reconciliation.write_text(
        "Plan 014 is **merged**.\nIts squash commit is `deadbeefdeadbeefdeadbeefdeadbeefdeadbeef`.\n"
    )

    _assert_error(check_scope(tmp_path), "is not an ancestor of HEAD")


def test_renderer_owns_both_documents_and_keeps_assessments_separate(tmp_path: Path) -> None:
    contract = _base_contract(tmp_path)
    evidence = contract["roadmap"]["knowledge_points"][0]["evidence_by_modality"]["theory"]
    evidence["assessments"] = [{"id": "U1-core-p1", "role": "primary"}]
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    rendered = renderer.render_documents(tmp_path)

    assert set(rendered) == {
        Path("docs/audits/015-coverage-audit.md"),
        Path("docs/curriculum-roadmap.md"),
    }
    audit = rendered[Path("docs/audits/015-coverage-audit.md")]
    roadmap = rendered[Path("docs/curriculum-roadmap.md")]
    assert "Practices: U1-core-p1, U1-core-p2, U1-core-p3" in audit
    assert "Assessments: U1-core-p1" in audit
    assert "Round 1 exit" in roadmap
    assert "topic-a" in roadmap
    assert "Modalities missing" in roadmap


def test_renderer_recomputes_real_post_plan014_baseline() -> None:
    baseline = renderer.current_time_baseline(Path(__file__).parents[1])

    assert baseline.manifested_minutes == 12347
    assert baseline.scheduled_minutes == 12587


def test_renderer_reports_layer_hour_ranges_total_and_resulting_delta(tmp_path: Path) -> None:
    contract = _base_contract(tmp_path)
    _add_r2_point(contract)
    contract["roadmap"]["planned_units"].append(
        {
            "id": "optional-lab",
            "title": "Optional lab",
            "layer": "optional-enrichment",
            "prerequisites": [],
            "knowledge_points": [],
            "provisional_concepts": ["optional-concept"],
            "estimated_hours": {"min": 0.5, "max": 1.5},
        }
    )
    _write_yaml(tmp_path / "curriculum" / "official-topics.yaml", contract["topics"])
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    rendered = renderer.render_documents(tmp_path)

    for document in rendered.values():
        assert "Current manifested baseline: **420 minutes / 7 hours**" in document
        assert "Current scheduled baseline: **435 minutes / 7.25 hours**" in document
        assert "| round-2-extension | 1 | 2 |" in document
        assert "| optional-enrichment | 0.5 | 1.5 |" in document
        assert "| **Total planned delta** | **1.5** | **3.5** |" in document
        assert "**8.5–10.5 manifested-baseline hours**" in document
        assert "**8.75–10.75 scheduled-baseline hours**" in document


def test_both_documents_end_with_fixed_six_tranche_queue(tmp_path: Path) -> None:
    _base_contract(tmp_path)

    rendered = renderer.render_documents(tmp_path)

    titles = [
        "Round 1 mathematical completion",
        "Round 1 neural-training completion",
        "Round 1 classical-model breadth",
        "Round 2 transformers and NLP",
        "Round 2 advanced vision and generative modeling",
        "Round 2 open-ended/GPU capstone",
    ]
    for document in rendered.values():
        offsets = [document.index(title) for title in titles]
        assert offsets == sorted(offsets)
        assert document.rstrip().endswith(
            "Each tranche updates the shipped syllabus and roadmap atomically."
        )
        assert "F5 extension" in document
        assert "C2 extension" in document
        assert "C9 extension" in document
        assert "C7 CNN training" in document
        assert "Forward propagation is already a shipped prerequisite, not a new gap." in document


def test_renderer_is_input_order_independent(tmp_path: Path) -> None:
    contract = _base_contract(tmp_path)
    _add_r2_point(contract)
    point = contract["roadmap"]["knowledge_points"][0]
    point["depends_on"] = ["c2", "c1"]
    point["shipped_concepts"] = ["c2", "c1"]
    point["deficits"]["modalities_missing"] = ["theory", "derivation"]
    evidence = point["evidence_by_modality"]["theory"]
    evidence["lesson_anchors"].append(dict(evidence["lesson_anchors"][0], cell_ordinal=2))
    evidence["practices"].reverse()
    evidence["assessments"] = [
        {"id": "assessment-b", "role": "primary"},
        {"id": "assessment-a", "role": "primary"},
    ]
    planned = contract["roadmap"]["planned_units"][0]
    planned["prerequisites"] = ["U2-unrelated", "U1-core"]
    planned["knowledge_points"] = ["topic-b", "topic-a"]
    planned["provisional_concepts"] = ["z-concept", "a-concept"]
    _write_yaml(tmp_path / "curriculum" / "official-topics.yaml", contract["topics"])
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])
    first = renderer.render_documents(tmp_path)
    contract["roadmap"]["knowledge_points"].reverse()
    contract["roadmap"]["planned_units"].reverse()
    contract["topics"]["atomic_targets"].reverse()
    point["depends_on"].reverse()
    point["shipped_concepts"].reverse()
    point["deficits"]["modalities_missing"].reverse()
    evidence["lesson_anchors"].reverse()
    evidence["practices"].reverse()
    evidence["assessments"].reverse()
    planned["prerequisites"].reverse()
    planned["knowledge_points"].reverse()
    planned["provisional_concepts"].reverse()
    _write_yaml(tmp_path / "curriculum" / "official-topics.yaml", contract["topics"])
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    assert renderer.render_documents(tmp_path) == first


def test_renderer_check_detects_stale_output_without_overwriting(tmp_path: Path) -> None:
    _base_contract(tmp_path)

    assert renderer.main(["--root", str(tmp_path)]) == 0
    assert renderer.main(["--root", str(tmp_path), "--check"]) == 0
    audit = tmp_path / "docs" / "audits" / "015-coverage-audit.md"
    audit.write_text("stale\n")

    assert renderer.main(["--root", str(tmp_path), "--check"]) == 1
    assert audit.read_text() == "stale\n"
