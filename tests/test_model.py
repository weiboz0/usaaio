import re
from pathlib import Path

import pytest
import yaml

from tools.model import (
    load_blueprint,
    load_mock_manifests,
    load_syllabus,
    load_unit_manifests,
)

ROOT = Path(__file__).resolve().parents[1]


def test_load_syllabus_real_repo():
    syllabus = load_syllabus(ROOT)
    taught = [concept for unit in syllabus.units.values() for concept in unit.teaches]
    assert len(syllabus.units) >= 16
    assert len(syllabus.concepts) >= 100
    assert len(taught) == len(set(taught))
    assert set(taught) == set(syllabus.concepts)
    assert set(syllabus.concepts.values()) <= syllabus.clusters


def test_sentinel_must_be_unique(tmp_path):
    (tmp_path / "syllabus.md").write_text(
        "<!-- syllabus-canonical -->\n```yaml\nbaseline: {}\n```\n<!-- syllabus-canonical -->\n"
    )
    with pytest.raises(ValueError, match="exactly once"):
        load_syllabus(tmp_path)


def test_load_blueprint_real_repo():
    blueprint = load_blueprint(ROOT)
    assert sum(row["target"] for row in blueprint.topic_distribution.values()) == blueprint.total_points


def test_missing_dirs_yield_empty_lists(tmp_path):
    assert load_unit_manifests(tmp_path) == []
    assert load_mock_manifests(tmp_path) == []


def test_unit_manifest_roundtrip(tmp_path):
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F1-scientific-python
concepts_taught: [numpy-arrays]
concepts_used: [variables-and-types]
prereq_units: []
practice:
  - id: F1-p01
    concepts: [numpy-arrays]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
"""
    )
    manifests = load_unit_manifests(tmp_path)
    assert manifests[0].unit_id == "F1-scientific-python"
    assert manifests[0].lesson_sessions is None
    assert manifests[0].practice[0].solution_path == "practice/p01_solution.ipynb"
    assert manifests[0].practice[0].minutes is None


def test_unit_manifest_parses_optional_positive_practice_minutes(tmp_path):
    unit_dir = tmp_path / "units" / "C11-neural-training"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: C11-neural-training
concepts_taught: [softmax]
concepts_used: []
prereq_units: []
practice:
  - id: C11-p01
    concepts: [softmax]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
    minutes: 15
"""
    )

    manifests = load_unit_manifests(tmp_path)

    assert manifests[0].practice[0].minutes == 15


@pytest.mark.parametrize("yaml_value", ["0", "-1", "true", "1.5", "'15'", "null"])
def test_unit_manifest_rejects_non_positive_integer_practice_minutes(
    tmp_path, yaml_value
):
    unit_dir = tmp_path / "units" / "C11-neural-training"
    unit_dir.mkdir(parents=True)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_path.write_text(
        f"""
unit: C11-neural-training
concepts_taught: [softmax]
concepts_used: []
prereq_units: []
practice:
  - id: C11-p01
    concepts: [softmax]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
    minutes: {yaml_value}
"""
    )

    message = rf"{re.escape(str(manifest_path))}: practice row 0 minutes must be a positive integer"
    with pytest.raises(ValueError, match=message):
        load_unit_manifests(tmp_path)


def test_unit_manifest_parses_lesson_sessions(tmp_path):
    unit_dir = tmp_path / "units" / "F6-svd-spectral"
    unit_dir.mkdir(parents=True)
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F6-svd-spectral
concepts_taught: []
concepts_used: []
prereq_units: []
estimated_minutes:
  lesson: 425
  lesson_sessions: [85, 85, 85, 85, 85]
practice: []
"""
    )

    manifests = load_unit_manifests(tmp_path)

    assert manifests[0].lesson_sessions == [85, 85, 85, 85, 85]


@pytest.mark.parametrize("yaml_value", ["85", "[85]", "null"])
def test_unit_manifest_rejects_non_mapping_estimated_minutes(tmp_path, yaml_value):
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    unit_dir.mkdir(parents=True)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_path.write_text(
        f"""
unit: F1-scientific-python
concepts_taught: []
concepts_used: []
prereq_units: []
estimated_minutes: {yaml_value}
practice: []
"""
    )

    message = rf"{re.escape(str(manifest_path))}: estimated_minutes must be a mapping when present"
    with pytest.raises(ValueError, match=message):
        load_unit_manifests(tmp_path)


@pytest.mark.parametrize(
    ("yaml_value", "detail"),
    [
        ("85", "must be a list"),
        ("true", "must be a list"),
        ("[true, 85]", "item 0 must be an integer"),
        ("[85, 42.5]", "item 1 must be an integer"),
        ("[85, 0]", "item 1 must be positive"),
        ("[-1, 85]", "item 0 must be positive"),
    ],
)
def test_unit_manifest_rejects_malformed_lesson_sessions(
    tmp_path, yaml_value, detail
):
    unit_dir = tmp_path / "units" / "F6-svd-spectral"
    unit_dir.mkdir(parents=True)
    manifest_path = unit_dir / "manifest.yaml"
    manifest_path.write_text(
        f"""
unit: F6-svd-spectral
concepts_taught: []
concepts_used: []
prereq_units: []
estimated_minutes:
  lesson_sessions: {yaml_value}
practice: []
"""
    )

    message = rf"{re.escape(str(manifest_path))}: estimated_minutes\.lesson_sessions {detail}"
    with pytest.raises(ValueError, match=message):
        load_unit_manifests(tmp_path)


def _write_session_manifest(tmp_path, *, concept_sessions, practice):
    unit_dir = tmp_path / "units" / "C12-classical-models"
    unit_dir.mkdir(parents=True)
    manifest = {
        "unit": "C12-classical-models",
        "concepts_taught": ["logistic-regression", "svm"],
        "concepts_used": [],
        "prereq_units": [],
        "estimated_minutes": {
            "lesson": 180,
            "lesson_sessions": [90, 90],
            "practice": sum(row.get("minutes", 0) for row in practice),
            "review": 60,
        },
        "concept_sessions": concept_sessions,
        "practice": practice,
    }
    (unit_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))


def _session_problem(*, concepts=None, after_session=1):
    row = {
        "id": "C12-p01",
        "concepts": concepts or ["logistic-regression"],
        "path": "practice/p01.ipynb",
        "solution_path": "practice/p01_solution.ipynb",
        "minutes": 20,
    }
    if after_session is not None:
        row["after_session"] = after_session
    return row


def test_unit_manifest_parses_optional_concept_sessions_and_after_session(tmp_path):
    _write_session_manifest(
        tmp_path,
        concept_sessions={"logistic-regression": 1, "svm": 2},
        practice=[_session_problem()],
    )

    manifest = load_unit_manifests(tmp_path)[0]

    assert manifest.concept_sessions == {"logistic-regression": 1, "svm": 2}
    assert manifest.practice[0].after_session == 1


@pytest.mark.parametrize(
    ("concept_sessions", "practice"),
    [
        pytest.param([], [_session_problem()], id="not-a-mapping"),
        pytest.param(
            {"logistic-regression": 1},
            [_session_problem()],
            id="keys-do-not-equal-owned-concepts",
        ),
        pytest.param(
            {"logistic-regression": True, "svm": 2},
            [_session_problem()],
            id="boolean-session",
        ),
        pytest.param(
            {"logistic-regression": 0, "svm": 2},
            [_session_problem()],
            id="zero-session",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 3},
            [_session_problem()],
            id="session-past-lesson-count",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(concepts=["foreign-concept"])],
            id="practice-without-owned-concept",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(after_session=None)],
            id="missing-after-session",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(after_session=True)],
            id="boolean-after-session",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(after_session=0)],
            id="zero-after-session",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(after_session=3)],
            id="after-session-past-lesson-count",
        ),
        pytest.param(
            {"logistic-regression": 1, "svm": 2},
            [_session_problem(concepts=["svm"], after_session=1)],
            id="after-session-before-concept-floor",
        ),
    ],
)
def test_unit_manifest_rejects_malformed_or_closure_invalid_session_contracts(
    tmp_path, concept_sessions, practice
):
    _write_session_manifest(
        tmp_path,
        concept_sessions=concept_sessions,
        practice=practice,
    )

    with pytest.raises(ValueError):
        load_unit_manifests(tmp_path)


BOOK2_UNIT = "B2-019-attention-transformers"
BOOK2_CONCEPTS = [
    "matrix-transpose",
    "query-key-value-attention",
    "scaled-dot-product-attention",
    "attention-mask",
    "causal-self-attention",
    "multi-head-attention",
    "sinusoidal-positional-encoding",
    "attention-complexity",
    "transformer-residual-layernorm",
    "position-wise-feed-forward",
    "transformer-block",
]
BOOK2_UNIT_PREREQS = [
    "C6-pytorch",
    "C7-cnn-transfer",
    "C8-embeddings",
    "C11-neural-training",
]
BOOK2_CONCEPT_PREREQS = [
    "softmax",
    "matrix-multiplication",
    "broadcasting",
    "variance",
    "torch-tensors",
    "nn-module",
    "torch-optimizers",
    "autograd-training",
]
BOOK2_CLAIMS = [
    "attention-mechanism-foundations",
    "self-attention",
    "multi-head-attention",
    "positional-encoding",
    "attention-complexity-analysis",
    "attention-from-scratch",
    "transformer-architecture-foundations",
]


def _write_book2_model_fixture(root: Path) -> None:
    root.joinpath("syllabus.md").write_text(
        "# Fixture\n\n<!-- syllabus-canonical -->\n```yaml\n"
        + yaml.safe_dump(
            {
                "baseline": {"math": ["arithmetic"]},
                "clusters": ["fixture"],
                "concepts": [
                    {"id": concept, "cluster": "fixture"}
                    for concept in [*BOOK2_CONCEPT_PREREQS, *BOOK2_CONCEPTS]
                ],
                "units": [
                    {
                        "id": BOOK2_UNIT,
                        "track": "extension",
                        "title": "Attention and Transformer Mechanics",
                        "book": 2,
                        "layer": "round-2-extension",
                        "round": 2,
                        "prereqs": BOOK2_UNIT_PREREQS,
                        "concept_prerequisites": BOOK2_CONCEPT_PREREQS,
                        "teaches": BOOK2_CONCEPTS,
                    }
                ],
            },
            sort_keys=False,
        )
        + "```\n"
    )
    unit_dir = root / "units" / BOOK2_UNIT
    unit_dir.mkdir(parents=True)
    claims = [
        {
            "knowledge_point": point,
            "first_session": index,
            "modalities": ["theory", "derivation", "implementation"],
            "evidence_concepts": [BOOK2_CONCEPTS[min(index - 1, 10)]],
            "evidence_by_modality": {},
        }
        for index, point in enumerate(BOOK2_CLAIMS, start=1)
    ]
    manifest = {
        "unit": BOOK2_UNIT,
        "book": 2,
        "layer": "round-2-extension",
        "round": 2,
        "track": "extension",
        "concepts_taught": BOOK2_CONCEPTS,
        "concepts_used": BOOK2_CONCEPT_PREREQS,
        "concept_prerequisites": BOOK2_CONCEPT_PREREQS,
        "prereq_units": BOOK2_UNIT_PREREQS,
        "bridge_diagnostic": {
            "path": "lessons/00-book1-bridge.ipynb",
            "minutes": 30,
            "referenced_concepts": BOOK2_CONCEPT_PREREQS,
        },
        "estimated_minutes": {
            "lesson_sessions": [90, 90, 90, 90, 90],
            "practice": 60,
            "review": 60,
        },
        "coverage_claims": claims,
        "practice": [
            {
                "id": "B2-019-p01",
                "concepts": BOOK2_CONCEPTS,
                "path": "practice/p01.ipynb",
                "solution_path": "practice/p01_solution.ipynb",
                "minutes": 60,
                "compute": {"policy": "cpu", "seed": 20260808},
            }
        ],
    }
    unit_dir.joinpath("manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False)
    )


def test_model_defaults_existing_book1_records_without_collapsing_the_two_dags(
    tmp_path: Path,
) -> None:
    tmp_path.joinpath("syllabus.md").write_text(
        """<!-- syllabus-canonical -->
```yaml
baseline: {math: [arithmetic]}
clusters: [fixture]
concepts: [{id: prior-concept, cluster: fixture}, {id: owned-concept, cluster: fixture}]
units:
  - id: C1-book1
    track: core
    title: Book 1
    prereqs: []
    teaches: [owned-concept]
```
"""
    )
    unit_dir = tmp_path / "units" / "C1-book1"
    unit_dir.mkdir(parents=True)
    unit_dir.joinpath("manifest.yaml").write_text(
        """unit: C1-book1
concepts_taught: [owned-concept]
concepts_used: [prior-concept]
prereq_units: []
practice:
  - id: C1-p01
    concepts: [owned-concept]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
"""
    )

    unit = load_syllabus(tmp_path).units["C1-book1"]
    manifest = load_unit_manifests(tmp_path)[0]

    assert (unit.book, unit.round, unit.layer) == (1, 1, "round-1-core")
    assert unit.prereqs == []
    assert unit.concept_prerequisites == []
    assert (manifest.book, manifest.round, manifest.layer, manifest.track) == (
        1,
        1,
        "round-1-core",
        "core",
    )
    assert manifest.prereq_units == []
    assert manifest.concept_prerequisites == ["prior-concept"]
    assert manifest.practice[0].compute.policy == "cpu"


def test_model_parses_the_exact_explicit_book2_contract(tmp_path: Path) -> None:
    _write_book2_model_fixture(tmp_path)

    unit = load_syllabus(tmp_path).units[BOOK2_UNIT]
    manifest = load_unit_manifests(tmp_path)[0]

    assert (unit.book, unit.round, unit.layer, unit.track) == (
        2,
        2,
        "round-2-extension",
        "extension",
    )
    assert unit.prereqs == BOOK2_UNIT_PREREQS
    assert unit.concept_prerequisites == BOOK2_CONCEPT_PREREQS
    assert unit.teaches == BOOK2_CONCEPTS
    assert (manifest.book, manifest.round, manifest.layer, manifest.track) == (
        2,
        2,
        "round-2-extension",
        "extension",
    )
    assert manifest.prereq_units == BOOK2_UNIT_PREREQS
    assert manifest.concept_prerequisites == BOOK2_CONCEPT_PREREQS
    assert manifest.concepts_taught == BOOK2_CONCEPTS
    assert manifest.bridge_diagnostic.minutes == 30
    assert manifest.bridge_diagnostic.path == "lessons/00-book1-bridge.ipynb"
    assert [claim.knowledge_point for claim in manifest.coverage_claims] == BOOK2_CLAIMS
    assert manifest.practice[0].compute.policy == "cpu"
    assert manifest.practice[0].compute.seed == 20260808
