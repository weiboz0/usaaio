from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

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
UNIT_PREREQS = [
    "C6-pytorch",
    "C7-cnn-transfer",
    "C8-embeddings",
    "C11-neural-training",
]
CONCEPT_PREREQS = [
    "softmax",
    "matrix-multiplication",
    "broadcasting",
    "variance",
    "torch-tensors",
    "nn-module",
    "torch-optimizers",
    "autograd-training",
]
CLAIM_CONTRACTS = {
    "attention-mechanism-foundations": (
        1,
        ["theory", "derivation", "implementation"],
        ["query-key-value-attention", "scaled-dot-product-attention"],
        [],
    ),
    "self-attention": (
        2,
        ["theory", "derivation", "implementation"],
        ["scaled-dot-product-attention", "causal-self-attention", "attention-mask"],
        ["attention-mechanism-foundations"],
    ),
    "multi-head-attention": (
        3,
        ["theory", "derivation", "implementation"],
        ["multi-head-attention"],
        ["self-attention"],
    ),
    "positional-encoding": (
        3,
        ["theory", "implementation"],
        ["sinusoidal-positional-encoding"],
        ["self-attention"],
    ),
    "attention-complexity-analysis": (
        3,
        ["theory", "derivation"],
        ["attention-complexity"],
        ["self-attention"],
    ),
    "attention-from-scratch": (
        4,
        ["theory", "implementation", "model-training"],
        ["scaled-dot-product-attention", "causal-self-attention"],
        ["multi-head-attention", "positional-encoding"],
    ),
    "transformer-architecture-foundations": (
        5,
        ["theory", "derivation", "implementation"],
        ["transformer-block", "transformer-residual-layernorm", "position-wise-feed-forward"],
        ["attention-from-scratch"],
    ),
}


def _write_yaml(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def _touch(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}")


def _layer_checker():
    try:
        return importlib.import_module("tools.checks.layer_boundary")
    except ModuleNotFoundError as exc:
        if exc.name != "tools.checks.layer_boundary":
            raise
        pytest.fail(
            "tools.checks.layer_boundary must enforce the Book 1 / Book 2 boundary"
        )


def _evidence(modalities: list[str], session: int) -> dict[str, Any]:
    return {
        modality: {
            "lesson_anchors": [
                {
                    "path": f"units/{BOOK2_UNIT}/lessons/0{session}-fixture.ipynb",
                    "heading": f"Session {session}",
                    "cell_ordinal": 1,
                    "role": "primary",
                }
            ],
            "practices": [
                {"id": f"B2-019-p{number:02}", "role": "primary"}
                for number in range(1, 4)
            ],
            "assessments": [],
        }
        for modality in modalities
    }


def _build_layer_fixture(root: Path) -> dict[str, Any]:
    prereq_ownership = {
        "C6-pytorch": [
            "matrix-multiplication",
            "broadcasting",
            "torch-tensors",
            "nn-module",
        ],
        "C7-cnn-transfer": ["variance"],
        "C8-embeddings": [],
        "C11-neural-training": ["softmax", "torch-optimizers", "autograd-training"],
    }
    units = [
        {
            "id": unit_id,
            "track": "core",
            "title": unit_id,
            "book": 1,
            "layer": "round-1-core",
            "round": 1,
            "prereqs": [],
            "concept_prerequisites": [],
            "teaches": concepts,
        }
        for unit_id, concepts in prereq_ownership.items()
    ]
    units.append(
        {
            "id": BOOK2_UNIT,
            "track": "extension",
            "title": "Attention and Transformer Mechanics",
            "book": 2,
            "layer": "round-2-extension",
            "round": 2,
            "prereqs": UNIT_PREREQS,
            "concept_prerequisites": CONCEPT_PREREQS,
            "teaches": BOOK2_CONCEPTS,
        }
    )
    syllabus = {
        "baseline": {"math": ["arithmetic"]},
        "clusters": ["fixture"],
        "concepts": [
            {"id": concept, "cluster": "fixture"}
            for concept in [*CONCEPT_PREREQS, *BOOK2_CONCEPTS]
        ],
        "units": units,
    }
    root.joinpath("syllabus.md").write_text(
        "# Fixture\n\n<!-- syllabus-canonical -->\n```yaml\n"
        + yaml.safe_dump(syllabus, sort_keys=False)
        + "```\n"
    )

    for unit_id, concepts in prereq_ownership.items():
        _write_yaml(
            root / "units" / unit_id / "manifest.yaml",
            {
                "unit": unit_id,
                "book": 1,
                "layer": "round-1-core",
                "round": 1,
                "track": "core",
                "concepts_taught": concepts,
                "concepts_used": [],
                "concept_prerequisites": [],
                "prereq_units": [],
                "practice": [],
            },
        )

    practices = [
        {
            "id": f"B2-019-p{number:02}",
            "concepts": list(BOOK2_CONCEPTS),
            "path": f"practice/p{number:02}.ipynb",
            "solution_path": f"practice/p{number:02}_solution.ipynb",
            "minutes": 20,
            "after_session": 5,
            "compute": {"policy": "cpu", "seed": 20260808},
        }
        for number in range(1, 4)
    ]
    claims = [
        {
            "knowledge_point": point,
            "first_session": session,
            "modalities": modalities,
            "evidence_concepts": concepts,
            "evidence_by_modality": _evidence(modalities, session),
        }
        for point, (session, modalities, concepts, _) in CLAIM_CONTRACTS.items()
    ]
    manifest = {
        "unit": BOOK2_UNIT,
        "book": 2,
        "layer": "round-2-extension",
        "round": 2,
        "track": "extension",
        "concepts_taught": BOOK2_CONCEPTS,
        "concepts_used": CONCEPT_PREREQS,
        "concept_prerequisites": CONCEPT_PREREQS,
        "prereq_units": UNIT_PREREQS,
        "bridge_diagnostic": {
            "path": "lessons/00-book1-bridge.ipynb",
            "minutes": 30,
            "referenced_concepts": CONCEPT_PREREQS,
        },
        "estimated_minutes": {
            "lesson_sessions": [90, 90, 90, 90, 90],
            "practice": 60,
            "review": 60,
        },
        "concept_sessions": {concept: 1 for concept in BOOK2_CONCEPTS},
        "coverage_claims": claims,
        "practice": practices,
    }
    _write_yaml(root / "units" / BOOK2_UNIT / "manifest.yaml", manifest)
    for path in [
        f"units/{BOOK2_UNIT}/lessons/00-book1-bridge.ipynb",
        *(f"units/{BOOK2_UNIT}/lessons/0{number}-fixture.ipynb" for number in range(1, 6)),
    ]:
        _touch(root, path)
    for row in practices:
        _touch(root / "units" / BOOK2_UNIT, row["path"])
        _touch(root / "units" / BOOK2_UNIT, row["solution_path"])

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
                "id": point,
                "layer": "round-2-extension",
                "requirement": "required",
                "coverage": "covered",
                "source_refs": ["fixture"],
                "depends_on": dependencies,
                "shipped_concepts": concepts,
                "evidence_by_modality": _evidence(modalities, session),
                "disposition": "keep",
                "destination": BOOK2_UNIT,
                "deficits": {"modalities_missing": []},
                "rationale": "Fixture coverage.",
                "consequence": "Fixture consequence.",
            }
            for point, (session, modalities, concepts, dependencies) in CLAIM_CONTRACTS.items()
        ],
    }
    _write_yaml(root / "curriculum" / "coverage-map.yaml", roadmap)
    return {"syllabus": syllabus, "manifest": manifest, "roadmap": roadmap}


def _rewrite_fixture(root: Path, data: dict[str, Any]) -> None:
    root.joinpath("syllabus.md").write_text(
        "# Fixture\n\n<!-- syllabus-canonical -->\n```yaml\n"
        + yaml.safe_dump(data["syllabus"], sort_keys=False)
        + "```\n"
    )
    _write_yaml(root / "units" / BOOK2_UNIT / "manifest.yaml", data["manifest"])
    _write_yaml(root / "curriculum" / "coverage-map.yaml", data["roadmap"])


def _claim(data: dict[str, Any], point: str) -> dict[str, Any]:
    return next(
        row for row in data["manifest"]["coverage_claims"]
        if row["knowledge_point"] == point
    )


def _mutate_book1_round2_leak(data: dict[str, Any], root: Path) -> None:
    path = root / "units" / "C11-neural-training" / "manifest.yaml"
    manifest = yaml.safe_load(path.read_text())
    manifest["coverage_claims"] = [data["manifest"]["coverage_claims"][0]]
    _write_yaml(path, manifest)


def _mutate_wrong_owner(data: dict[str, Any], root: Path) -> None:
    b2 = next(row for row in data["syllabus"]["units"] if row["id"] == BOOK2_UNIT)
    c6 = next(row for row in data["syllabus"]["units"] if row["id"] == "C6-pytorch")
    b2["teaches"].remove("matrix-transpose")
    c6["teaches"].append("matrix-transpose")
    path = root / "units" / "C6-pytorch" / "manifest.yaml"
    manifest = yaml.safe_load(path.read_text())
    manifest["concepts_taught"].append("matrix-transpose")
    _write_yaml(path, manifest)


def _mutate_unit_prereq(data: dict[str, Any], root: Path) -> None:
    del root
    data["manifest"]["prereq_units"].pop()


def _mutate_concept_prereq(data: dict[str, Any], root: Path) -> None:
    del root
    data["manifest"]["concept_prerequisites"].pop()


def _mutate_missing_diagnostic(data: dict[str, Any], root: Path) -> None:
    del root
    data["manifest"].pop("bridge_diagnostic")


def _mutate_non_subset_evidence(data: dict[str, Any], root: Path) -> None:
    del root
    _claim(data, "self-attention")["evidence_concepts"].append("softmax")


def _mutate_missing_derivation(data: dict[str, Any], root: Path) -> None:
    del root
    claim = _claim(data, "self-attention")
    claim["modalities"] = ["theory", "implementation"]
    claim["evidence_by_modality"].pop("derivation")


def _mutate_early_coverage(data: dict[str, Any], root: Path) -> None:
    del root
    _claim(data, "self-attention")["first_session"] = 1


def _mutate_missing_seed(data: dict[str, Any], root: Path) -> None:
    del root
    data["manifest"]["practice"][0]["compute"].pop("seed")


def _mutate_missing_cpu_solution(data: dict[str, Any], root: Path) -> None:
    del root
    data["manifest"]["practice"][0]["solution_path"] = "practice/missing.ipynb"


def _mutate_two_qualifying_practices(data: dict[str, Any], root: Path) -> None:
    del root
    claim = _claim(data, "attention-mechanism-foundations")
    for evidence in claim["evidence_by_modality"].values():
        evidence["practices"] = evidence["practices"][:2]


def _mutate_two_owned_tags(data: dict[str, Any], root: Path) -> None:
    del root
    data["manifest"]["practice"][2]["concepts"].remove("matrix-transpose")


def test_valid_book2_layer_fixture_is_accepted(tmp_path: Path) -> None:
    _build_layer_fixture(tmp_path)

    report = _layer_checker().check_layer_boundary(tmp_path)

    assert report.ok, report.errors
    assert report.errors == []


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        pytest.param(
            _mutate_book1_round2_leak,
            "Book 1 artifact claims Round 2 coverage",
            id="book1-round2-leak",
        ),
        pytest.param(
            _mutate_wrong_owner,
            "is not owned by a Book 2 syllabus unit",
            id="wrong-book2-owner",
        ),
        pytest.param(
            _mutate_unit_prereq,
            "prereq_units drift from syllabus",
            id="unit-prerequisite-mismatch",
        ),
        pytest.param(
            _mutate_concept_prereq,
            "concept_prerequisites drift from syllabus",
            id="concept-prerequisite-mismatch",
        ),
        pytest.param(
            _mutate_missing_diagnostic,
            "bridge_diagnostic is required",
            id="missing-bridge-diagnostic",
        ),
        pytest.param(
            _mutate_non_subset_evidence,
            "evidence_concepts must be a nonempty subset of concepts_taught",
            id="non-subset-evidence-concepts",
        ),
        pytest.param(
            _mutate_missing_derivation,
            "modalities must exactly match the coverage-map requirement",
            id="required-modality-absent",
        ),
        pytest.param(
            _mutate_early_coverage,
            "first_session must follow same-unit knowledge-point dependencies",
            id="early-in-unit-coverage",
        ),
        pytest.param(
            _mutate_missing_seed,
            "compute.seed is required",
            id="missing-compute-seed",
        ),
        pytest.param(
            _mutate_missing_cpu_solution,
            "cpu task requires a local solution path",
            id="cpu-task-missing-local-solution",
        ),
        pytest.param(
            _mutate_two_qualifying_practices,
            "requires at least 3 qualifying practice ids",
            id="fewer-than-three-qualifying-practices",
        ),
        pytest.param(
            _mutate_two_owned_tags,
            "requires at least 3 direct practice tags",
            id="owned-concept-fewer-than-three-direct-tags",
        ),
    ],
)
def test_layer_boundary_rejects_true_book2_mutations(
    tmp_path: Path,
    mutate: Callable[[dict[str, Any], Path], None],
    fragment: str,
) -> None:
    data = _build_layer_fixture(tmp_path)
    mutate(data, tmp_path)
    _rewrite_fixture(tmp_path, data)

    report = _layer_checker().check_layer_boundary(tmp_path)

    assert not report.ok
    assert any(fragment in error for error in report.errors), report.errors
