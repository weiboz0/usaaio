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
            "prereqs": list(UNIT_PREREQS),
            "concept_prerequisites": list(CONCEPT_PREREQS),
            "teaches": list(BOOK2_CONCEPTS),
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
        "concepts_taught": list(BOOK2_CONCEPTS),
        "concepts_used": list(CONCEPT_PREREQS),
        "concept_prerequisites": list(CONCEPT_PREREQS),
        "prereq_units": list(UNIT_PREREQS),
        "bridge_diagnostic": {
            "path": "lessons/00-book1-bridge.ipynb",
            "minutes": 30,
            "referenced_concepts": list(CONCEPT_PREREQS),
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


def _canonical_syllabus(contract: dict[str, Any]) -> str:
    return (
        "# Fixture\n\n<!-- syllabus-canonical -->\n```yaml\n"
        + yaml.safe_dump(contract, sort_keys=False)
        + "```\n"
    )


def _build_registered_layer_fixture(repo: Path) -> tuple[dict[str, Any], Path]:
    book2 = repo / "book2"
    book2.mkdir(parents=True)
    data = _build_layer_fixture(book2)
    book1 = repo / "book1"
    (book1 / "units").mkdir(parents=True)
    prereq_rows = [
        row for row in data["syllabus"]["units"] if row["id"] in UNIT_PREREQS
    ]
    prereq_concepts = [
        concept
        for row in prereq_rows
        for concept in row["teaches"]
    ]
    (book1 / "syllabus.md").write_text(
        _canonical_syllabus(
            {
                "baseline": {"math": ["arithmetic"]},
                "clusters": ["fixture"],
                "concepts": [
                    {"id": concept, "cluster": "fixture"}
                    for concept in prereq_concepts
                ],
                "units": prereq_rows,
            }
        ),
        encoding="utf-8",
    )
    for unit_id in UNIT_PREREQS:
        (book2 / "units" / unit_id).rename(book1 / "units" / unit_id)

    book2_unit = next(
        row for row in data["syllabus"]["units"] if row["id"] == BOOK2_UNIT
    )
    book2_unit["prereqs"] = [f"book1:{unit}" for unit in UNIT_PREREQS]
    book2_unit["concept_prerequisites"] = [
        f"book1:{concept}" for concept in CONCEPT_PREREQS
    ]
    data["syllabus"] = {
        "baseline": {"math": ["arithmetic"]},
        "clusters": ["fixture"],
        "imports": {
            "book": "book1",
            "units": list(UNIT_PREREQS),
            "concepts": list(CONCEPT_PREREQS),
        },
        "evidence_imports": {
            "book": "book1",
            "concepts": [],
            "lesson_paths": [],
            "practices": [],
            "assessments": [],
        },
        "concepts": [
            {"id": concept, "cluster": "fixture"} for concept in BOOK2_CONCEPTS
        ],
        "units": [book2_unit],
    }
    data["manifest"]["prereq_units"] = list(book2_unit["prereqs"])
    data["manifest"]["concept_prerequisites"] = list(
        book2_unit["concept_prerequisites"]
    )
    data["manifest"]["concepts_used"] = list(book2_unit["concept_prerequisites"])
    data["manifest"]["bridge_diagnostic"]["referenced_concepts"] = list(
        book2_unit["concept_prerequisites"]
    )
    _rewrite_fixture(book2, data)
    _write_yaml(
        repo / "books.yaml",
        {
            "books_version": 1,
            "books": [
                {"id": "book1", "number": 1, "root": "book1", "depends_on": []},
                {
                    "id": "book2",
                    "number": 2,
                    "root": "book2",
                    "depends_on": ["book1"],
                },
            ],
        },
    )
    return data, book2


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


def _mutate_b2_id_as_book1_tuple(data: dict[str, Any], root: Path) -> None:
    del root
    book1_tuple = {
        "book": 1,
        "round": 1,
        "layer": "round-1-core",
        "track": "core",
    }
    syllabus_unit = next(
        row for row in data["syllabus"]["units"] if row["id"] == BOOK2_UNIT
    )
    syllabus_unit.update(book1_tuple)
    data["manifest"].update(book1_tuple)
    data["manifest"]["coverage_claims"] = []


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
    data["manifest"]["practice"][0]["concepts"].remove("matrix-transpose")


def _mutate_missing_covered_claim(data: dict[str, Any], root: Path) -> None:
    del root
    data["manifest"]["coverage_claims"] = [
        claim
        for claim in data["manifest"]["coverage_claims"]
        if claim["knowledge_point"] != "transformer-architecture-foundations"
    ]


def _mutate_claim_for_uncovered_point(data: dict[str, Any], root: Path) -> None:
    del root
    point = next(
        point
        for point in data["roadmap"]["knowledge_points"]
        if point["id"] == "transformer-architecture-foundations"
    )
    point["coverage"] = "partial"


def test_valid_book2_layer_fixture_is_accepted(tmp_path: Path) -> None:
    _build_layer_fixture(tmp_path)

    report = _layer_checker().check_layer_boundary(tmp_path)

    assert report.ok, report.errors
    assert report.errors == []


def test_first_live_registered_book2_layer_resolves_qualified_prereqs(
    tmp_path: Path,
) -> None:
    _, book2 = _build_registered_layer_fixture(tmp_path / "repo")

    report = _layer_checker().check_layer_boundary(book2)

    assert report.ok, report.errors


@pytest.mark.parametrize(
    ("relative_path", "fragment"),
    [
        pytest.param(
            "lessons/00-book1-bridge.ipynb",
            "bridge_diagnostic requires a local existing path",
            id="bridge-diagnostic",
        ),
        pytest.param(
            "practice/p01_solution.ipynb",
            "cpu task requires a local solution path",
            id="cpu-solution",
        ),
    ],
)
def test_layer_boundary_rejects_symlinked_artifact_paths(
    tmp_path: Path, relative_path: str, fragment: str
) -> None:
    _, book2 = _build_registered_layer_fixture(tmp_path / "repo")
    artifact = book2 / "units" / BOOK2_UNIT / relative_path
    target = artifact.parent / "symlink-target.ipynb"
    target.write_text("{}\n", encoding="utf-8")
    artifact.unlink()
    artifact.symlink_to(target)

    report = _layer_checker().check_layer_boundary(book2)

    assert not report.ok
    assert any(fragment in error for error in report.errors), report.errors


@pytest.mark.parametrize(
    ("replacement", "fragment"),
    [
        pytest.param("book9:C6-pytorch", "unknown owner", id="wrong-owner"),
        pytest.param(
            "book1:C5-neural-networks", "allowlist", id="nonallowlisted-unit"
        ),
    ],
)
def test_first_live_registered_book2_layer_rejects_invalid_qualified_prereq(
    tmp_path: Path, replacement: str, fragment: str
) -> None:
    data, book2 = _build_registered_layer_fixture(tmp_path / "repo")
    original = data["manifest"]["prereq_units"][0]
    data["manifest"]["prereq_units"][0] = replacement
    data["syllabus"]["units"][0]["prereqs"][0] = replacement
    assert original != replacement
    _rewrite_fixture(book2, data)

    report = _layer_checker().check_layer_boundary(book2)

    assert not report.ok
    assert any(fragment in error for error in report.errors), report.errors


def test_live_book2_manifest_without_claims_is_valid_while_map_is_not_covered(
    tmp_path: Path,
) -> None:
    data = _build_layer_fixture(tmp_path)
    data["manifest"]["coverage_claims"] = []
    for index, point in enumerate(data["roadmap"]["knowledge_points"]):
        point["coverage"] = "partial" if index == 0 else "missing"
    _rewrite_fixture(tmp_path, data)

    report = _layer_checker().check_layer_boundary(tmp_path)

    assert report.ok, report.errors


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
            _mutate_b2_id_as_book1_tuple,
            "B2-* records must declare the canonical Book 2 tuple",
            id="b2-id-spoofed-as-book1",
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
        pytest.param(
            _mutate_missing_covered_claim,
            (
                "coverage_claims missing covered roadmap point "
                "transformer-architecture-foundations"
            ),
            id="covered-roadmap-point-missing-claim",
        ),
        pytest.param(
            _mutate_claim_for_uncovered_point,
            (
                "coverage claim transformer-architecture-foundations has no covered "
                f"roadmap point for destination {BOOK2_UNIT}"
            ),
            id="uncovered-roadmap-point-has-extra-claim",
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
