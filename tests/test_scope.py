from __future__ import annotations

import os
import re
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from tools import model
from tools import render_curriculum_roadmap as renderer
from tools.checks import scope as scope_checker
from tools.checks.scope import check_scope

ROOT = Path(__file__).parents[1]

PLAN017_CLOSURE = {
    "softmax": (
        "C11-neural-training",
        ["softmax"],
        {"theory": "C11-p01", "derivation": "C11-p11", "implementation": "C11-p05"},
    ),
    "cross-entropy-loss": (
        "C11-neural-training",
        ["cross-entropy-loss"],
        {"theory": "C11-p02", "derivation": "C11-p11", "implementation": "C11-p06"},
    ),
    "backpropagation-by-hand": (
        "C11-neural-training",
        ["manual-backpropagation"],
        {"theory": "C11-p03", "derivation": "C11-p12", "implementation": "C11-p07"},
    ),
    "pytorch-autograd-and-optimizer-training": (
        "C11-neural-training",
        ["requires-grad", "layer-freezing", "autograd-training", "torch-optimizers"],
        {"implementation": "C11-p08", "model-training": "C11-p16"},
    ),
    "multilayer-perceptron-model": (
        "C11-neural-training",
        [
            "mlp-architecture",
            "activation-functions",
            "manual-weights",
            "decision-boundaries-geometric",
            "trained-mlp",
        ],
        {"model-training": "C11-p15"},
    ),
    "fully-connected-network-from-scratch": (
        "C11-neural-training",
        [
            "mlp-architecture",
            "activation-functions",
            "manual-weights",
            "decision-boundaries-geometric",
            "manual-backpropagation",
            "trained-mlp",
        ],
        {"model-training": "C11-p15"},
    ),
    "batch-normalization": (
        "C11-neural-training",
        ["layer-freezing", "requires-grad", "resnet-architecture", "batch-normalization"],
        {
            "derivation": "C11-p13",
            "implementation": "C11-p09",
            "model-training": "C11-p24",
        },
    ),
    "dropout": (
        "C11-neural-training",
        ["dropout"],
        {"theory": "C11-p04", "implementation": "C11-p10", "model-training": "C11-p24"},
    ),
    "pytorch-deep-learning-programming": (
        "C6-pytorch",
        [
            "torch-tensors",
            "nn-module",
            "custom-layers",
            "autograd-training",
            "torch-optimizers",
        ],
        {"model-training": "C11-p16"},
    ),
    "convolutional-neural-network-basics": (
        "C7-cnn-transfer",
        [
            "convolution",
            "feature-maps",
            "receptive-field",
            "feature-hierarchy",
            "cnn-training",
        ],
        {"model-training": "C7-p10"},
    ),
}

PLAN018_CLASSICAL_CLOSURE = {
    "logistic-regression": {
        "concepts": ["logistic-regression"],
        "lesson_files": {"01-logistic-regression.ipynb"},
        "practices": {
            "theory": ["C12-p01", "C12-p14", "C12-p26"],
            "implementation": ["C12-p06", "C12-p07", "C12-p18"],
            "model-training": ["C12-p07", "C12-p18", "C12-p21"],
        },
    },
    "support-vector-machine": {
        "concepts": ["svm", "margin-and-hinge-loss"],
        "lesson_files": {
            "02-linear-svm-margin-and-hinge.ipynb",
            "03-kernel-svm-and-dual-intuition.ipynb",
        },
        "practices": {
            "theory": ["C12-p02", "C12-p15", "C12-p27"],
            "implementation": ["C12-p08", "C12-p09", "C12-p27"],
            "model-training": ["C12-p09", "C12-p18", "C12-p21"],
        },
    },
    "decision-trees": {
        "concepts": ["decision-trees", "tree-split-criteria"],
        "lesson_files": {"04-decision-trees.ipynb"},
        "practices": {
            "theory": ["C12-p03", "C12-p16", "C12-p23"],
            "implementation": ["C12-p10", "C12-p11", "C12-p28"],
            "model-training": ["C12-p11", "C12-p19", "C12-p21"],
        },
    },
    "ensemble-learning": {
        "concepts": ["ensemble-learning", "bagging-and-boosting"],
        "lesson_files": {"05-ensembles.ipynb"},
        "practices": {
            "theory": ["C12-p04", "C12-p24", "C12-p29"],
            "implementation": ["C12-p12", "C12-p19", "C12-p29"],
            "model-training": ["C12-p12", "C12-p19", "C12-p21"],
        },
    },
    "k-means-clustering": {
        "concepts": ["k-means", "lloyd-algorithm"],
        "lesson_files": {"06-kmeans-and-model-comparison.ipynb"},
        "practices": {
            "theory": ["C12-p05", "C12-p17", "C12-p25"],
            "implementation": ["C12-p13", "C12-p20", "C12-p30"],
            "model-training": ["C12-p13", "C12-p20", "C12-p21"],
        },
    },
}


def _fixture_schedule_loader(root: str | Path):
    root = Path(root)
    manifested = 0
    for path in root.glob("units/*/manifest.yaml"):
        estimates = yaml.safe_load(path.read_text()).get("estimated_minutes") or {}
        manifested += sum(estimates.get("lesson_sessions") or [])
        manifested += int(estimates.get("practice", 0))
        manifested += int(estimates.get("review", 0))
    mock = sum(
        int(yaml.safe_load(path.read_text()).get("duration_minutes", 0))
        for path in root.glob("mocktests/*/manifest.yaml")
    )
    course = (root / "docs" / "course-structure.md").read_text()
    match = re.search(r"(\d+)-minute debrief", course)
    return SimpleNamespace(
        total_minutes=manifested + mock + (int(match.group(1)) if match else 0)
    )


def _render_fixture_documents(root: Path):
    return renderer.render_documents(root, _schedule_loader=_fixture_schedule_loader)


def _fixture_renderer_main(argv: list[str]) -> int:
    return renderer.main(argv, _schedule_loader=_fixture_schedule_loader)


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
        "canonical_path_normalization": {
            "id": "official-topic-paths-v1",
            "unicode": "NFC",
            "whitespace": "collapse",
            "ordering": "source-order",
            "serialization": 'JSON UTF-8 array; ensure_ascii=false; separators=(",", ":")',
        },
        "sources": [
            {
                "id": "source-1",
                "title": "Official topic source",
                "authority": "official-syllabus",
                "url": "https://example.invalid/syllabus",
                "retrieved": "2026-08-06",
                "review_after": "2099-01-01",
                "committed": False,
                "local_only": False,
                "normalization": "official-topic-paths-v1",
                "topic_paths_sha256": (
                    "b3301dc168749bdd174ec9cddfc43a78d39f2aad60f25136502ea45fd2a1ce3a"
                ),
                "topic_paths": ["Official > Topic"],
            }
        ],
    }
    topics = {
        "official_topics_schema_version": 1,
        "allowed_modalities": [
            "theory",
            "derivation",
            "proof",
            "implementation",
            "model-training",
            "competition-workflow",
        ],
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


@pytest.mark.parametrize("value", [True, 1.0], ids=["boolean", "float"])
def test_roadmap_version_requires_exact_integer_type(tmp_path: Path, value: object) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"]["roadmap_version"] = value

    _assert_error(_report_after(tmp_path, mutate), "unsupported roadmap_version")


@pytest.mark.parametrize(
    ("document", "field", "value", "message"),
    [
        ("sources", "source_schema_version", True, "source_schema_version"),
        ("sources", "source_schema_version", 1.0, "source_schema_version"),
        ("sources", "source_schema_version", 2, "source_schema_version"),
        ("topics", "official_topics_schema_version", True, "official_topics_schema_version"),
        ("topics", "official_topics_schema_version", 1.0, "official_topics_schema_version"),
        ("topics", "official_topics_schema_version", 2, "official_topics_schema_version"),
    ],
)
def test_source_and_topic_schema_versions_require_exact_integer_one(
    tmp_path: Path,
    document: str,
    field: str,
    value: object,
    message: str,
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data[document][field] = value

    _assert_error(_report_after(tmp_path, mutate), message)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda row: row.update(id=""), "requires nonempty id"),
        (lambda row: row.pop("title"), "requires nonempty title"),
        (lambda row: row.update(authority="blog"), "unknown authority"),
        (lambda row: row.update(committed="false"), "committed must be a boolean"),
        (lambda row: row.update(local_only="false"), "local_only must be a boolean"),
        (lambda row: row.update(retrieved="2026/08/06"), "invalid retrieved"),
        (lambda row: row.pop("url"), "exactly one of url or path"),
        (lambda row: row.pop("topic_paths_sha256"), "topic_paths_sha256 is required"),
        (
            lambda row: [
                row.pop(field)
                for field in ("normalization", "topic_paths_sha256", "topic_paths")
            ],
            "official source requires a canonical topic-path pin",
        ),
        (lambda row: row.update(normalization="free-form"), "unknown normalization"),
        (lambda row: row["topic_paths"].append("Official > Added"), "topic_paths_sha256 mismatch"),
    ],
)
def test_source_rows_strictly_validate_required_fields_enums_and_pinned_hash(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], object],
    message: str,
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        mutation(data["sources"]["sources"][0])

    _assert_error(_report_after(tmp_path, mutate), message)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("sources", {}, "sources must be a list"),
        (
            "canonical_path_normalization",
            {"id": "free-form"},
            "canonical_path_normalization must exactly equal",
        ),
    ],
)
def test_source_manifest_top_level_contract_is_strict(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["sources"][field] = value

    _assert_error(_report_after(tmp_path, mutate), message)


def test_nonofficial_local_source_does_not_require_topic_path_pin(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["sources"]["sources"].append(
            {
                "id": "local-analysis",
                "title": "Local analysis",
                "authority": "design-rationale",
                "path": "reference/analysis.md",
                "retrieved": "2026-08-06",
                "review_after": "2099-01-01",
                "committed": True,
                "local_only": False,
            }
        )

    report = _report_after(tmp_path, mutate)

    assert report.ok, report.errors


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda topics: topics.update(categories={}),
            "categories must be a list",
        ),
        (
            lambda topics: topics["atomic_targets"].append("not-a-mapping"),
            "atomic_targets row 1 must be a mapping",
        ),
        (
            lambda topics: topics.update(allowed_modalities=["theory", "invented"]),
            "allowed_modalities must exactly equal",
        ),
        (
            lambda topics: topics["categories"][0].update(kind="invented"),
            "unknown category kind",
        ),
        (
            lambda topics: topics["categories"][0].update(source_refs="source-1"),
            "source_refs must be a list of strings",
        ),
        (
            lambda topics: topics["atomic_targets"][0].update(modalities="theory"),
            "modalities must be a list of strings",
        ),
        (
            lambda topics: topics["non_required_candidates"].append(
                {
                    "id": "candidate-a",
                    "related_category": "foundation",
                    "source_refs": ["source-1"],
                    "requirement": "required",
                    "audit_target": False,
                }
            ),
            "requirement must be optional",
        ),
        (
            lambda topics: topics["non_required_candidates"].append(
                {
                    "id": "candidate-a",
                    "related_category": "foundation",
                    "source_refs": ["source-1"],
                    "requirement": "optional",
                    "audit_target": True,
                }
            ),
            "audit_target must be false",
        ),
    ],
)
def test_topic_map_strictly_validates_collections_fields_and_enums(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], object],
    message: str,
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        mutation(data["topics"])

    _assert_error(_report_after(tmp_path, mutate), message)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("planned_units", {}, "planned_units must be a list"),
        ("knowledge_points", {}, "knowledge_points must be a list"),
    ],
)
def test_top_level_roadmap_collections_must_be_lists(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"][field] = value

    _assert_error(_report_after(tmp_path, mutate), message)


@pytest.mark.parametrize(
    ("collection", "index"), [("planned_units", 0), ("knowledge_points", 1)]
)
def test_roadmap_collection_rows_must_be_mappings(
    tmp_path: Path, collection: str, index: int
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"][collection].append("not-a-mapping")

    _assert_error(_report_after(tmp_path, mutate), f"{collection} row {index} must be a mapping")


def test_scalar_self_dependency_is_schema_error_not_cycle_bypass(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"]["knowledge_points"][0]["depends_on"] = "topic-a"

    report = _report_after(tmp_path, mutate)

    _assert_error(report, "depends_on must be a list of strings")
    assert not any("dependency cycle" in error for error in report.errors)


def test_scalar_modalities_missing_is_schema_error(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"]["knowledge_points"][0]["deficits"]["modalities_missing"] = "theory"

    _assert_error(_report_after(tmp_path, mutate), "modalities_missing must be a list of strings")


def test_planned_unit_title_is_required(tmp_path: Path) -> None:
    def mutate(data: dict[str, Any]) -> None:
        _add_r2_point(data)
        data["roadmap"]["planned_units"][0].pop("title")

    _assert_error(_report_after(tmp_path, mutate), "planned_units row 0 requires nonempty title")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("prerequisites", "U1-core", "prerequisites must be a list of strings"),
        ("knowledge_points", "topic-b", "knowledge_points must be a list of strings"),
        ("provisional_concepts", "future-c", "provisional_concepts must be a list of strings"),
        ("estimated_hours", [1, 2], "estimated_hours must be a mapping"),
    ],
)
def test_planned_unit_required_field_types_fail(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        _add_r2_point(data)
        data["roadmap"]["planned_units"][0][field] = value

    _assert_error(_report_after(tmp_path, mutate), message)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_refs", "source-1", "source_refs must be a list of strings"),
        ("shipped_concepts", "c1", "shipped_concepts must be a list of strings"),
        ("evidence_by_modality", [], "evidence_by_modality must be a mapping"),
        ("deficits", [], "deficits must be a mapping"),
        ("destination", 7, "destination must be a string or null"),
    ],
)
def test_knowledge_point_required_field_types_fail(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        data["roadmap"]["knowledge_points"][0][field] = value

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


def _add_unestimated_c8_point(data: dict[str, Any], *, covered: bool) -> None:
    data["topics"]["atomic_targets"].append(
        {
            "id": "nlp-word-embeddings",
            "parent": "foundation",
            "source_refs": ["source-1"],
            "required_for": ["round-2"],
            "modalities": ["theory", "model-training"],
        }
    )
    theory = dict(
        data["roadmap"]["knowledge_points"][0]["evidence_by_modality"]["theory"]
    )
    model_training = theory if covered else {"lesson_anchors": [], "practices": []}
    data["roadmap"]["knowledge_points"].append(
        {
            "id": "nlp-word-embeddings",
            "layer": "round-2-extension",
            "requirement": "required",
            "coverage": "covered" if covered else "partial",
            "source_refs": ["source-1"],
            "depends_on": [],
            "shipped_concepts": ["c1"],
            "evidence_by_modality": {
                "theory": theory,
                "model-training": model_training,
            },
            "disposition": "keep" if covered else "existing-unit-extension",
            "destination": "C8-embeddings",
            "deficits": {"modalities_missing": [] if covered else ["model-training"]},
            "rationale": "Word embeddings still need model-training evidence.",
            "consequence": "Round 2 NLP training remains incomplete.",
        }
    )


def _add_pending_c7_training_point(data: dict[str, Any]) -> None:
    data["topics"]["atomic_targets"].append(
        {
            "id": "convolutional-neural-network-basics",
            "parent": "foundation",
            "source_refs": ["source-1"],
            "required_for": ["round-1", "round-2"],
            "modalities": ["model-training"],
        }
    )
    data["roadmap"]["knowledge_points"].append(
        {
            "id": "convolutional-neural-network-basics",
            "layer": "round-1-core",
            "requirement": "required",
            "coverage": "partial",
            "source_refs": ["source-1"],
            "depends_on": [],
            "shipped_concepts": ["c1"],
            "evidence_by_modality": {
                "model-training": {"lesson_anchors": [], "practices": []}
            },
            "disposition": "existing-unit-extension",
            "destination": "C7-cnn-transfer",
            "deficits": {"modalities_missing": ["model-training"]},
            "rationale": "CNN training evidence remains pending.",
            "consequence": "The C7 extension must return to the roadmap.",
        }
    )


def _add_pending_neural_tranche(data: dict[str, Any]) -> None:
    data["roadmap"]["planned_units"].append(
        {
            "id": "P015-R1-NEURAL-TRAINING",
            "title": "Round 1 neural-training completion",
            "layer": "round-1-core",
            "prerequisites": [],
            "knowledge_points": [],
            "provisional_concepts": ["future-neural-training"],
            "estimated_hours": {"min": 30, "max": 44},
            "schedule_action": "extend",
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
            {
                "id": "source-2",
                "title": "Second source",
                "authority": "design-rationale",
                "path": "docs/source-2.md",
                "recorded": "2026-08-06",
                "review_after": "2099-01-01",
                "committed": True,
                "local_only": False,
            }
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


@pytest.mark.parametrize("later_layer", ["round-2-extension", "optional-enrichment"])
@pytest.mark.parametrize("transitive", [False, True], ids=["direct", "transitive"])
def test_round_1_planned_units_cannot_depend_on_later_layer_planned_units(
    tmp_path: Path, transitive: bool, later_layer: str
) -> None:
    def mutate(data: dict[str, Any]) -> None:
        _add_r2_point(data)
        data["roadmap"]["planned_units"][0]["layer"] = later_layer
        prerequisite = "R2-topic-b"
        if transitive:
            data["roadmap"]["planned_units"].append(
                {
                    "id": "R1-bridge",
                    "title": "Round 1 bridge",
                    "layer": "round-1-core",
                    "prerequisites": ["R2-topic-b"],
                    "knowledge_points": [],
                    "provisional_concepts": ["round-1-bridge"],
                    "estimated_hours": {"min": 1, "max": 1},
                    "schedule_action": "extend",
                }
            )
            prerequisite = "R1-bridge"
        data["roadmap"]["planned_units"].append(
            {
                "id": "R1-entry",
                "title": "Round 1 entry",
                "layer": "shared-foundation",
                "prerequisites": [prerequisite],
                "knowledge_points": [],
                "provisional_concepts": ["round-1-entry"],
                "estimated_hours": {"min": 1, "max": 1},
                "schedule_action": "extend",
            }
        )

    _assert_error(
        _report_after(tmp_path, mutate),
        "cannot depend on later-layer planned unit R2-topic-b",
    )


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


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("- Branch/PR:   ", "Branch/PR must be nonempty"),
        ("- Date: 2026/08/06", "Date must be an ISO date"),
        ("- Reason:   ", "Reason must be nonempty"),
        ("- Owner decision:   ", "Owner decision must be nonempty"),
    ],
)
def test_plan014_abandonment_fields_are_nonempty_and_date_is_iso(
    tmp_path: Path, line: str, message: str
) -> None:
    _base_contract(tmp_path)
    path = tmp_path / "docs" / "audits" / "015-plan014-reconciliation.md"
    labels = ("Branch/PR", "Date", "Reason", "Owner decision")
    replacement_label = next(label for label in labels if line.startswith(f"- {label}:"))
    text = path.read_text()
    text = re.sub(
        rf"(?m)^- {re.escape(replacement_label)}:.*$",
        line,
        text,
    )
    path.write_text(text)

    _assert_error(check_scope(tmp_path), message)


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

    rendered = _render_fixture_documents(tmp_path)

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


def test_renderer_labels_unit_and_total_inventoried_notebook_counts(tmp_path: Path) -> None:
    contract = _base_contract(tmp_path)
    contract["inventory"]["counts"] = {
        "unit_notebooks": 765,
        "mock_notebooks": 10,
        "unit_practices": 343,
    }
    _write_yaml(tmp_path / "curriculum" / "material-inventory.yaml", contract["inventory"])

    audit = _render_fixture_documents(tmp_path)[
        Path("docs/audits/015-coverage-audit.md")
    ]

    assert "| Unit notebooks | 765 |" in audit
    assert "| Total inventoried notebooks | 775 |" in audit


def test_renderer_surfaces_checker_derived_practice_shortfall(tmp_path: Path) -> None:
    contract = _base_contract(tmp_path)
    point = contract["roadmap"]["knowledge_points"][0]
    point["coverage"] = "partial"
    point["evidence_by_modality"]["theory"]["practices"] = []
    point["deficits"]["modalities_missing"] = []
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    rendered = _render_fixture_documents(tmp_path)
    audit = rendered[Path("docs/audits/015-coverage-audit.md")]
    roadmap = rendered[Path("docs/curriculum-roadmap.md")]

    assert "- **Practice shortfall:** 3" in audit
    assert "| Knowledge point | Requirement | Coverage | Modalities missing | Practice shortfall |" in roadmap
    assert "| topic-a | required | partial | — | 3 |" in roadmap


def test_renderer_and_scope_checker_share_the_practice_threshold() -> None:
    assert (
        renderer.MINIMUM_QUALIFYING_PRACTICES
        == scope_checker.MINIMUM_QUALIFYING_PRACTICES
    )


def test_roadmap_production_consumer_requires_the_full_canonical_schedule(
    tmp_path: Path,
) -> None:
    _base_contract(tmp_path)

    with pytest.raises(ValueError, match="course-schedule.yaml"):
        renderer.render_documents(tmp_path)


def test_renderer_recomputes_real_plan018_baseline() -> None:
    baseline = renderer.current_time_baseline(ROOT)

    assert baseline.manifested_minutes == 18635
    assert baseline.scheduled_minutes == 18875


def test_plan017_closure_has_exact_destinations_additions_and_primary_practices() -> None:
    report = check_scope(ROOT)
    assert report.ok, report.errors

    roadmap = yaml.safe_load((ROOT / "curriculum" / "coverage-map.yaml").read_text())
    points = {point["id"]: point for point in roadmap["knowledge_points"]}

    for point_id, (destination, shipped_concepts, primary_by_modality) in PLAN017_CLOSURE.items():
        point = points[point_id]
        assert point["coverage"] == "covered"
        assert point["disposition"] == "keep"
        assert point["destination"] == destination
        assert point["shipped_concepts"] == shipped_concepts
        assert point["deficits"] == {"modalities_missing": []}
        for modality, primary_id in primary_by_modality.items():
            evidence = point["evidence_by_modality"][modality]
            assert evidence["lesson_anchors"]
            assert [
                row["id"] for row in evidence["practices"] if row["role"] == "primary"
            ] == [primary_id]


def test_plan018_classical_rows_are_shipped_with_exact_direct_evidence() -> None:
    report = check_scope(ROOT)
    assert report.ok, report.errors
    assert not [
        warning
        for warning in report.warnings
        if any(point_id in warning for point_id in PLAN018_CLASSICAL_CLOSURE)
    ]

    roadmap = yaml.safe_load((ROOT / "curriculum" / "coverage-map.yaml").read_text())
    points = {point["id"]: point for point in roadmap["knowledge_points"]}
    planned = {unit["id"]: unit for unit in roadmap["planned_units"]}

    for point_id, expected in PLAN018_CLASSICAL_CLOSURE.items():
        point = points[point_id]
        assert point["coverage"] == "covered"
        assert point["destination"] == "C12-classical-models"
        assert point["disposition"] == "keep"
        assert point["shipped_concepts"] == expected["concepts"]
        assert point["deficits"] == {"modalities_missing": []}
        for modality, required_ids in expected["practices"].items():
            evidence = point["evidence_by_modality"][modality]
            actual_ids = [row["id"] for row in evidence["practices"]]
            assert set(required_ids) <= set(actual_ids)
            assert evidence["lesson_anchors"]
            assert {
                Path(anchor["path"]).name for anchor in evidence["lesson_anchors"]
            } <= expected["lesson_files"]
            assert evidence["assessments"] == []

    assert "P015-R1-CLASSICAL-BREADTH" not in planned
    capstone_prereqs = planned["P015-R2-CAPSTONE"]["prerequisites"]
    assert "P015-R1-CLASSICAL-BREADTH" not in capstone_prereqs
    assert "C12-classical-models" in capstone_prereqs

    remaining_round1 = {
        point["id"]
        for point in roadmap["knowledge_points"]
        if point["layer"] == "round-1-core" and point["coverage"] != "covered"
    }
    assert remaining_round1 == set()


def test_every_covered_real_roadmap_row_uses_keep_disposition() -> None:
    roadmap = model.load_roadmap(Path(__file__).parents[1])

    covered = [point for point in roadmap.knowledge_points if point.coverage == "covered"]
    assert covered
    assert all(point.disposition == "keep" for point in covered)


def test_completed_plan017_neural_extensions_are_not_rendered_as_pending() -> None:
    rendered = renderer.render_documents(ROOT)

    for document in rendered.values():
        assert "C7 CNN training" not in document
        assert "C6 and C8 are not yet estimated" not in document
        assert "C8" in document


def test_c7_extension_returns_only_when_cnn_training_owner_is_pending(
    tmp_path: Path,
) -> None:
    contract = _base_contract(tmp_path)
    without_pending_owner = _render_fixture_documents(tmp_path)
    assert all("C7 CNN training" not in document for document in without_pending_owner.values())

    _add_pending_c7_training_point(contract)
    _write_yaml(tmp_path / "curriculum" / "official-topics.yaml", contract["topics"])
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])
    with_pending_owner = _render_fixture_documents(tmp_path)

    assert all("C7 CNN training" in document for document in with_pending_owner.values())


def test_neural_tranche_returns_only_when_its_planned_unit_is_restored(
    tmp_path: Path,
) -> None:
    contract = _base_contract(tmp_path)
    without_planned_unit = _render_fixture_documents(tmp_path)
    title = "Round 1 neural-training completion"
    assert all(title not in document for document in without_planned_unit.values())

    _add_pending_neural_tranche(contract)
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])
    with_planned_unit = _render_fixture_documents(tmp_path)

    assert all(title in document for document in with_planned_unit.values())


def test_unestimated_c8_clause_remains_but_estimated_extension_section_is_suppressed(
    tmp_path: Path,
) -> None:
    contract = _base_contract(tmp_path)
    _add_unestimated_c8_point(contract, covered=False)
    _write_yaml(tmp_path / "curriculum" / "official-topics.yaml", contract["topics"])
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    rendered = _render_fixture_documents(tmp_path)

    for document in rendered.values():
        assert "C8" in document
        assert "nlp-word-embeddings" in document
        assert "C6 and C8 are not yet estimated" not in document
        assert "so this is not a complete roadmap total" not in document
        assert "Estimated major existing-unit extensions" not in document
        assert "Minimum estimated scoped delta" not in document
        assert (
            "The unestimated C8 `nlp-word-embeddings` model-training correction remains pending."
            in document
        )


def test_unestimated_c8_clause_disappears_only_after_its_canonical_row_is_covered(
    tmp_path: Path,
) -> None:
    contract = _base_contract(tmp_path)
    _add_unestimated_c8_point(contract, covered=True)
    _write_yaml(tmp_path / "curriculum" / "official-topics.yaml", contract["topics"])
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    rendered = _render_fixture_documents(tmp_path)

    for document in rendered.values():
        assert (
            "The unestimated C8 `nlp-word-embeddings` model-training correction remains pending."
            not in document
        )
        assert "Estimated major existing-unit extensions" not in document


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

    rendered = _render_fixture_documents(tmp_path)

    for document in rendered.values():
        assert "Current manifested baseline: **420 minutes / 7 hours**" in document
        assert "Current scheduled baseline: **435 minutes / 7.25 hours**" in document
        assert "| round-2-extension | 1 | 2 |" in document
        assert "| optional-enrichment | 0.5 | 1.5 |" in document
        assert "| **Planned-unit subtotal** | **1.5** | **3.5** |" in document
        assert (
            "This range is a renderer-owned editorial estimate, not a field in the canonical coverage map."
            in document
        )
        assert "Estimated major existing-unit extensions subtotal" not in document
        assert "Minimum estimated scoped delta" not in document
        assert "C6 and C8 are not yet estimated" not in document
        assert "**8.5–10.5 manifested-baseline hours**" in document
        assert "**8.75–10.75 scheduled-baseline hours**" in document


def test_plan018_renderer_recomputes_the_round2_only_planned_delta() -> None:
    rendered = renderer.render_documents(Path(__file__).parents[1])

    for document in rendered.values():
        assert "| **Planned-unit subtotal** | **126** | **192** |" in document
        assert (
            "This range is a renderer-owned editorial estimate, not a field in the canonical coverage map."
            in document
        )
        assert "Estimated major existing-unit extensions subtotal" not in document
        assert "Minimum estimated scoped delta" not in document
        assert "C6 and C8 are not yet estimated" not in document
        assert "C8" in document
        assert "so this is not a complete roadmap total" not in document
        assert "**436.58–502.58 manifested-baseline hours**" in document
        assert "**440.58–506.58 scheduled-baseline hours**" in document
        assert "student-t-test" in document
        assert "importance-sampling" in document
        assert "Total roadmap delta" not in document


def test_both_documents_end_with_exact_post_plan018_tranche_queue() -> None:
    rendered = renderer.render_documents(ROOT)

    titles = [
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
        assert "Round 1 foundation, workflow, and mathematical completion" not in document
        assert "F5 extension" not in document
        assert "vision-transformer" in document
        assert "graph-neural-network" in document
        assert "C2 extension" not in document
        assert "C9 extension" not in document
        assert "C7 CNN training" not in document
        assert "Round 1 neural-training completion" not in document
        assert "Round 1 classical-model breadth" not in document
        assert "Forward propagation is already a shipped prerequisite, not a new gap." not in document


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
    first = _render_fixture_documents(tmp_path)
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

    assert _render_fixture_documents(tmp_path) == first


def test_renderer_fractional_hour_totals_are_planned_unit_order_independent(
    tmp_path: Path,
) -> None:
    contract = _base_contract(tmp_path)
    units = [
        {
            "id": f"optional-{index}",
            "title": f"Optional {index}",
            "layer": "optional-enrichment",
            "prerequisites": [],
            "knowledge_points": [],
            "provisional_concepts": [f"optional-concept-{index}"],
            "estimated_hours": {"min": hours, "max": hours},
        }
        for index, hours in enumerate((0.001, 0.059, 0.555), start=1)
    ]
    contract["roadmap"]["planned_units"] = units
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])
    first = _render_fixture_documents(tmp_path)
    contract["roadmap"]["planned_units"] = list(reversed(units))
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    second = _render_fixture_documents(tmp_path)

    assert second == first
    for document in second.values():
        assert "| optional-enrichment | 0.61 | 0.61 |" in document


def test_renderer_check_detects_stale_output_without_overwriting(tmp_path: Path) -> None:
    _base_contract(tmp_path)

    assert _fixture_renderer_main(["--root", str(tmp_path)]) == 0
    assert _fixture_renderer_main(["--root", str(tmp_path), "--check"]) == 0
    audit = tmp_path / "docs" / "audits" / "015-coverage-audit.md"
    audit.write_text("stale\n")

    assert _fixture_renderer_main(["--root", str(tmp_path), "--check"]) == 1
    assert audit.read_text() == "stale\n"


def test_renderer_rejects_symlinked_output_file_without_touching_target(tmp_path: Path) -> None:
    _base_contract(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("sentinel\n")
    output = tmp_path / "docs" / "audits" / "015-coverage-audit.md"
    output.symlink_to(outside)

    assert _fixture_renderer_main(["--root", str(tmp_path)]) == 1
    assert outside.read_text() == "sentinel\n"


def test_renderer_rejects_symlinked_output_parent_without_writing_outside(
    tmp_path: Path,
) -> None:
    _base_contract(tmp_path)
    audits = tmp_path / "docs" / "audits"
    reconciliation = audits / "015-plan014-reconciliation.md"
    reconciliation_text = reconciliation.read_text()
    reconciliation.unlink()
    audits.rmdir()
    outside = tmp_path / "outside-audits"
    outside.mkdir()
    outside.joinpath("015-plan014-reconciliation.md").write_text(reconciliation_text)
    audits.symlink_to(outside, target_is_directory=True)

    assert _fixture_renderer_main(["--root", str(tmp_path)]) == 1
    assert not outside.joinpath("015-coverage-audit.md").exists()


def test_renderer_replaces_outputs_atomically_inside_their_parent_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _base_contract(tmp_path)
    replacements: list[tuple[Path, Path]] = []
    real_replace = os.replace

    def record_replace(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
        replacements.append((Path(source), Path(target)))
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", record_replace)

    assert _fixture_renderer_main(["--root", str(tmp_path)]) == 0
    assert {target.relative_to(tmp_path) for _, target in replacements} == {
        Path("docs/audits/015-coverage-audit.md"),
        Path("docs/curriculum-roadmap.md"),
    }
    assert all(source.parent == target.parent for source, target in replacements)


def test_scope_pass_implies_roadmap_loader_and_renderer_accept_contract(tmp_path: Path) -> None:
    _base_contract(tmp_path)

    report = check_scope(tmp_path)

    assert report.ok, report.errors
    loaded = model.load_roadmap(tmp_path)
    rendered = _render_fixture_documents(tmp_path)
    assert loaded.knowledge_points[0].id == "topic-a"
    assert set(rendered) == {
        Path("docs/audits/015-coverage-audit.md"),
        Path("docs/curriculum-roadmap.md"),
    }


BOOK2_ROADMAP_MEMBERSHIP = {
    "B2-019-attention-transformers": [
        "attention-mechanism-foundations",
        "self-attention",
        "multi-head-attention",
        "positional-encoding",
        "attention-complexity-analysis",
        "attention-from-scratch",
        "transformer-architecture-foundations",
    ],
    "B2-020-language-transformers": [
        "nlp-word-embeddings",
        "nlp-transformers",
        "nlp-pretraining",
        "nlp-fine-tuning",
        "transformer-nlp-applications",
    ],
    "B2-021-cross-modal-transformers-vision": [
        "vision-transformers",
        "graph-neural-network-transformer-applications",
        "object-detection",
        "unet",
    ],
    "B2-022-probabilistic-latent-models": [
        "multivariate-gaussian",
        "gaussian-reparameterization",
        "kl-divergence",
        "autoencoder",
        "variational-autoencoder",
    ],
    "B2-023-generative-models-diffusion": [
        "generative-adversarial-network",
        "denoising-diffusion-probabilistic-models",
        "stable-diffusion",
    ],
    "B2-024-gpu-scientific-ml-capstone": [
        "gpu-colab-l4-workflow",
        "semi-supervised-pseudo-labeling",
        "scientific-ml-inverse-problems",
        "mixture-parameter-regression",
        "open-ended-experiment-design",
        "open-ended-model-evaluation",
    ],
}


def _write_book2_roadmap_fixture(root: Path) -> dict[str, Any]:
    contract = _base_contract(root)
    topics = contract["topics"]
    roadmap = contract["roadmap"]
    topics["categories"].append(
        {
            "id": "round2-only",
            "parent": None,
            "kind": "official",
            "source_refs": ["source-1"],
            "required_for": ["round-2"],
        }
    )
    for points in BOOK2_ROADMAP_MEMBERSHIP.values():
        for point in points:
            modalities = ["theory", "model-training"] if point == "nlp-word-embeddings" else ["theory"]
            topics["atomic_targets"].append(
                {
                    "id": point,
                    "parent": "round2-only",
                    "source_refs": ["source-1"],
                    "required_for": ["round-2"],
                    "modalities": modalities,
                }
            )
    roadmap["planned_units"] = [
        {
            "id": unit_id,
            "title": unit_id,
            "layer": "round-2-extension",
            "prerequisites": [],
            "knowledge_points": list(points),
            "provisional_concepts": [f"{unit_id}-concept"],
            "estimated_hours": {"min": 1, "max": 1},
            "schedule_action": "extend",
        }
        for unit_id, points in BOOK2_ROADMAP_MEMBERSHIP.items()
    ]
    for unit_id, points in BOOK2_ROADMAP_MEMBERSHIP.items():
        for point in points:
            row = {
                "id": point,
                "layer": "round-2-extension",
                "requirement": "required",
                "coverage": "missing",
                "source_refs": ["source-1"],
                "depends_on": [],
                "shipped_concepts": [],
                "evidence_by_modality": {},
                "disposition": "new-unit",
                "destination": unit_id,
                "deficits": {"modalities_missing": ["theory"]},
                "rationale": "Book 2 fixture gap.",
                "consequence": "Book 2 fixture consequence.",
            }
            if point == "nlp-word-embeddings":
                row.update(
                    coverage="partial",
                    shipped_concepts=["c2"],
                    evidence_by_modality={
                        "theory": {
                            "lesson_anchors": [
                                {
                                    "path": "units/C8-embeddings/lessons/01-lesson.ipynb",
                                    "heading": "Lesson",
                                    "cell_ordinal": 1,
                                    "role": "primary",
                                }
                            ],
                            "practices": [
                                {"id": f"C8-embeddings-p{number}", "role": "primary"}
                                for number in range(1, 4)
                            ],
                            "assessments": [],
                        }
                    },
                    disposition="extend-existing-unit",
                    destination="C8-embeddings",
                    deficits={"modalities_missing": ["model-training"]},
                )
            roadmap["knowledge_points"].append(row)
    for name, filename in (
        ("sources", "sources.yaml"),
        ("topics", "official-topics.yaml"),
        ("inventory", "material-inventory.yaml"),
        ("roadmap", "coverage-map.yaml"),
    ):
        _write_yaml(root / "curriculum" / filename, contract[name])
    return contract


def test_book2_roadmap_fixture_is_an_exact_six_row_partition_of_all_30_targets(
    tmp_path: Path,
) -> None:
    _write_book2_roadmap_fixture(tmp_path)

    loaded = model.load_roadmap(tmp_path)
    report = check_scope(tmp_path)

    planned = {unit.id: unit.knowledge_points for unit in loaded.planned_units}
    assert planned == BOOK2_ROADMAP_MEMBERSHIP
    assert len({point for points in planned.values() for point in points}) == 30
    assert all(not unit_id.startswith("P015-R2-") for unit_id in planned)
    embedding = next(point for point in loaded.knowledge_points if point.id == "nlp-word-embeddings")
    assert (embedding.coverage, embedding.destination) == ("partial", "C8-embeddings")
    assert report.ok, report.errors


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (
            lambda contract: contract["roadmap"]["planned_units"][1]["knowledge_points"].append(
                "attention-mechanism-foundations"
            ),
            "knowledge point attention-mechanism-foundations must have exactly one destination owner",
        ),
        (
            lambda contract: contract["roadmap"]["planned_units"][0].update(
                id="P015-R2-TRANSFORMERS-NLP"
            ),
            "legacy P015-R2 planned-unit rows are forbidden",
        ),
        (
            lambda contract: next(
                row
                for row in contract["roadmap"]["knowledge_points"]
                if row["id"] == "nlp-word-embeddings"
            ).update(destination="B2-020-language-transformers", disposition="new-unit"),
            "nlp-word-embeddings must retain destination C8-embeddings",
        ),
    ],
)
def test_book2_roadmap_partition_mutations_fail_scope_check(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any]], None],
    fragment: str,
) -> None:
    contract = _write_book2_roadmap_fixture(tmp_path)
    mutate(contract)
    _write_yaml(tmp_path / "curriculum" / "coverage-map.yaml", contract["roadmap"])

    report = check_scope(tmp_path)

    assert not report.ok
    assert any(fragment in error for error in report.errors), report.errors
