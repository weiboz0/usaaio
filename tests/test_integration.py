from __future__ import annotations

import functools
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path

import pytest
import yaml

from tools.checks.blueprint import check_blueprint
from tools.checks.coverage import check_coverage
from tools.checks.hygiene import check_hygiene
from tools.checks.new_mocktest import scaffold_mocktest
from tools.checks.overlap import check_overlap
from tools.checks.prereq import check_prereq
from tools.model import load_syllabus, load_unit_manifests

ROOT = Path(__file__).resolve().parents[1]
BOOK1_ROOT = ROOT / "book1"
BOOK2_ROOT = ROOT / "book2"

NEW_CONCEPT_CLUSTERS = {
    "seaborn-programming": "python-scientific",
    "colab-markdown-solution-authoring": "competition-craft",
    "markdown-code-snippets": "competition-craft",
    "markdown-math-formulae": "competition-craft",
    "colab-coding-submission": "competition-craft",
    "cpu-and-gpu-round-boundary": "competition-craft",
    "conditional-probability": "probability-statistics",
    "bayes-rule": "probability-statistics",
    "hoeffding-inequality": "probability-statistics",
    "linear-regression-estimator-derivation": "ml-concepts",
    "ols-rank-identifiability-and-pseudoinverse": "ml-concepts",
    "pca-centered-covariance-eigenproblem-derivation": "ml-concepts",
    "numpy-pca-class-from-scratch": "ml-concepts",
    "pca-black-box-insufficiency": "ml-concepts",
    "positive-semidefinite-matrices": "linear-algebra",
    "kernel-validity": "linear-algebra",
    "convex-sets": "linear-algebra",
    "convex-functions": "calculus-multivar",
    "first-order-optimality": "calculus-multivar",
    "lagrangians": "calculus-multivar",
    "optimization-duality": "calculus-multivar",
}

EXPECTED_UNIT_SHAPES = {
    "F1-scientific-python": ([75, 90, 75, 70], 24, (310, 515, 50)),
    "C10-competition-craft": ([80, 85, 85, 85], 24, (335, 730, 55)),
    "F5-probability": ([80, 85, 85, 85, 80], 25, (415, 650, 55)),
    "C2-linear-models": ([85, 90, 85], 24, (260, 590, 55)),
    "C9-dimensionality-reduction": ([80, 90, 85, 85], 24, (340, 600, 60)),
    "F7-kernels-convex-optimization": ([85, 85, 85, 85], 20, (340, 640, 45)),
    "C11-neural-training": ([90, 90, 90, 90, 90], 24, (450, 1040, 60)),
    "C7-cnn-transfer": ([85, 85, 85, 90], 27, (345, 875, 60)),
}

PLAN016_C10_PROMOTED_CONCEPTS = (
    "colab-markdown-solution-authoring",
    "markdown-code-snippets",
    "markdown-math-formulae",
    "colab-coding-submission",
    "cpu-and-gpu-round-boundary",
)

F1_SEABORN_ARRAY_ONLY_FILES = {
    Path("lesson.ipynb"),
    Path("lessons/01-arrays-and-indexing.ipynb"),
    Path("lessons/02-broadcasting-and-vectorization.ipynb"),
    Path("lessons/03-randomness-and-plotting.ipynb"),
    Path("lessons/04-seaborn-with-arrays.ipynb"),
    Path("review.ipynb"),
    Path("practice/p22.ipynb"),
    Path("practice/p22_solution.ipynb"),
    Path("practice/p23.ipynb"),
    Path("practice/p23_solution.ipynb"),
    Path("practice/p24.ipynb"),
    Path("practice/p24_solution.ipynb"),
}

C9_PLAN016_CHANGED_NOTEBOOKS = (
    Path("lesson.ipynb"),
    Path("lessons/01-pca.ipynb"),
    Path("lessons/02-pca-covariance-and-numpy-class.ipynb"),
    Path("lessons/03-truncated-svd-practice.ipynb"),
    Path("lessons/04-maps-and-structure.ipynb"),
    Path("review.ipynb"),
    *(Path(f"practice/p{number:02d}.ipynb") for number in range(20, 25)),
)

PLAN017_NEW_CONCEPTS = {
    "softmax",
    "cross-entropy-loss",
    "manual-backpropagation",
    "autograd-training",
    "torch-optimizers",
    "trained-mlp",
    "batch-normalization",
    "dropout",
    "cnn-training",
}

PLAN019_B2_019_CONCEPTS = (
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
)

PLAN017_C11_CONCEPTS_USED = [
    "numpy-arrays",
    "array-indexing-slicing",
    "elementwise-ops",
    "broadcasting",
    "vectorization",
    "aggregation-axis",
    "random-seeding",
    "matplotlib-basics",
    "partial-derivatives",
    "gradient",
    "multivar-chain-rule",
    "gradient-descent",
    "learning-rate",
    "stochastic-gd",
    "loss-surfaces",
    "expectation",
    "variance",
    "perceptron",
    "activation-functions",
    "relu-activation",
    "mlp-architecture",
    "weight-init-variance",
    "overfitting",
    "l2-regularization",
    "python-inheritance",
    "torch-tensors",
    "nn-module",
    "requires-grad",
    "parameter-counting",
]

PLAN017_C11_PRACTICE_ROWS = [
    ("C11-p01", "A", "mc", "intro", ["softmax"], 15),
    ("C11-p02", "A", "mc", "intro", ["cross-entropy-loss"], 15),
    ("C11-p03", "A", "mc", "intro", ["manual-backpropagation"], 15),
    ("C11-p04", "B", "mc-normal-form", "intro", ["dropout"], 15),
    ("C11-p05", "A", "constrained-coding", "intro", ["softmax"], 25),
    ("C11-p06", "B", "constrained-coding", "intro", ["cross-entropy-loss"], 25),
    (
        "C11-p07",
        "A",
        "constrained-coding",
        "core",
        ["manual-backpropagation", "trained-mlp"],
        35,
    ),
    (
        "C11-p08",
        "A",
        "constrained-coding",
        "core",
        ["autograd-training", "torch-optimizers"],
        35,
    ),
    ("C11-p09", "A", "constrained-coding", "core", ["batch-normalization"], 35),
    ("C11-p10", "A", "constrained-coding", "core", ["dropout"], 35),
    (
        "C11-p11",
        "B",
        "proof",
        "core",
        ["softmax", "cross-entropy-loss"],
        40,
    ),
    ("C11-p12", "B", "proof", "core", ["manual-backpropagation"], 40),
    ("C11-p13", "B", "proof", "core", ["batch-normalization"], 40),
    (
        "C11-p14",
        "C",
        "integrative",
        "core",
        ["softmax", "cross-entropy-loss"],
        60,
    ),
    (
        "C11-p15",
        "C",
        "integrative",
        "core",
        ["manual-backpropagation", "trained-mlp"],
        60,
    ),
    (
        "C11-p16",
        "C",
        "integrative",
        "core",
        ["autograd-training", "torch-optimizers"],
        60,
    ),
    ("C11-p17", "C", "scenario", "core", ["trained-mlp"], 50),
    (
        "C11-p18",
        "C",
        "scenario",
        "core",
        ["batch-normalization", "dropout"],
        50,
    ),
    (
        "C11-p19",
        "C",
        "scenario",
        "advanced",
        ["autograd-training", "torch-optimizers"],
        50,
    ),
    (
        "C11-p20",
        "C",
        "scenario",
        "advanced",
        ["trained-mlp", "batch-normalization", "dropout"],
        50,
    ),
    (
        "C11-p21",
        "C",
        "challenge",
        "advanced",
        ["softmax", "cross-entropy-loss"],
        70,
    ),
    (
        "C11-p22",
        "C",
        "challenge",
        "advanced",
        ["manual-backpropagation"],
        70,
    ),
    (
        "C11-p23",
        "C",
        "challenge",
        "advanced",
        ["autograd-training", "torch-optimizers", "trained-mlp"],
        75,
    ),
    (
        "C11-p24",
        "C",
        "challenge",
        "advanced",
        ["torch-optimizers", "trained-mlp", "batch-normalization", "dropout"],
        75,
    ),
]

PLAN017_C7_PRESERVED_CONCEPTS = {
    "C7-p10": {"layer-freezing", "nn-module", "requires-grad", "parameter-counting"},
    "C7-p24": {"tensor-shape-tracing"},
    "C7-p26": {"convolution", "tensor-shape-tracing"},
    "C7-p27": {"layer-freezing", "requires-grad"},
}

PLAN018_C12_CONCEPTS = [
    "logistic-regression",
    "svm",
    "margin-and-hinge-loss",
    "decision-trees",
    "tree-split-criteria",
    "ensemble-learning",
    "bagging-and-boosting",
    "k-means",
    "lloyd-algorithm",
    "classical-model-comparison",
]

PLAN018_C12_PRACTICE_LEDGER = [
    ("C12-p01", "A", "mc", "intro", 20, 1),
    ("C12-p02", "A", "mc", "intro", 20, 2),
    ("C12-p03", "A", "mc", "intro", 20, 4),
    ("C12-p04", "A", "mc", "intro", 20, 5),
    ("C12-p05", "A", "mc-normal-form", "intro", 20, 6),
    ("C12-p06", "A", "constrained-coding", "intro", 55, 1),
    ("C12-p07", "B", "constrained-coding", "core", 55, 1),
    ("C12-p08", "B", "constrained-coding", "core", 55, 2),
    ("C12-p09", "B", "constrained-coding", "advanced", 55, 3),
    ("C12-p10", "A", "constrained-coding", "intro", 55, 4),
    ("C12-p11", "B", "constrained-coding", "core", 55, 4),
    ("C12-p12", "B", "constrained-coding", "core", 55, 5),
    ("C12-p13", "A", "constrained-coding", "intro", 55, 6),
    ("C12-p14", "B", "proof", "core", 45, 1),
    ("C12-p15", "C", "proof", "advanced", 45, 3),
    ("C12-p16", "B", "proof", "core", 45, 4),
    ("C12-p17", "B", "proof", "core", 45, 6),
    ("C12-p18", "C", "integrative", "advanced", 65, 2),
    ("C12-p19", "C", "integrative", "advanced", 65, 5),
    ("C12-p20", "C", "integrative", "core", 65, 6),
    ("C12-p21", "C", "integrative", "advanced", 65, 6),
    ("C12-p22", "C", "scenario", "intro", 45, 2),
    ("C12-p23", "C", "scenario", "core", 45, 4),
    ("C12-p24", "C", "scenario", "core", 45, 5),
    ("C12-p25", "C", "scenario", "core", 45, 6),
    ("C12-p26", "C", "challenge", "core", 50, 1),
    ("C12-p27", "C", "challenge", "advanced", 50, 3),
    ("C12-p28", "C", "challenge", "core", 50, 4),
    ("C12-p29", "C", "challenge", "core", 50, 5),
    ("C12-p30", "C", "challenge", "advanced", 50, 6),
]

PLAN018_C12_CONCEPT_COVERAGE = {
    "logistic-regression": [1, 6, 7, 14, 18, 21, 22, 26],
    "svm": [2, 8, 9, 15, 18, 21, 22, 27],
    "margin-and-hinge-loss": [2, 8, 15, 18, 27],
    "decision-trees": [3, 10, 11, 16, 19, 21, 23, 28],
    "tree-split-criteria": [3, 10, 16, 23, 28],
    "ensemble-learning": [4, 12, 19, 21, 24, 29],
    "bagging-and-boosting": [4, 12, 19, 24, 29],
    "k-means": [5, 13, 17, 20, 21, 25, 30],
    "lloyd-algorithm": [5, 13, 17, 20, 30],
    "classical-model-comparison": [18, 21, 22, 24, 25],
}


def _manifest(unit_id: str) -> dict[str, object]:
    return yaml.safe_load((BOOK1_ROOT / "units" / unit_id / "manifest.yaml").read_text())


def _notebook_cell_source(relative_path: str, cell_id: str) -> str:
    notebook = json.loads((BOOK1_ROOT / relative_path).read_text())
    cell = next(cell for cell in notebook["cells"] if cell.get("id") == cell_id)
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else source


def _canonical_syllabus_yaml() -> dict[str, object]:
    text = (BOOK1_ROOT / "syllabus.md").read_text()
    fenced = re.search(
        r"<!-- syllabus-canonical -->\s*```yaml\n(.*?)\n```", text, re.DOTALL
    )
    assert fenced is not None
    return yaml.safe_load(fenced.group(1))


def _syllabus_narrative() -> str:
    text = (BOOK1_ROOT / "syllabus.md").read_text()
    canonical_end = re.search(
        r"<!-- syllabus-canonical -->\s*```yaml\n.*?\n```", text, re.DOTALL
    )
    assert canonical_end is not None
    return text[canonical_end.end() :]


def _narrative_section(narrative: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\n\n(.*?)(?=^## |\Z)",
        narrative,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return match.group(1)


def seed_repo(root: Path, *, registered: bool = False) -> Path:
    content_root = root / "book1" if registered else root
    (content_root / "mocktests").mkdir(parents=True)
    (content_root / "mocktests" / "blueprint.yaml").write_text(
        (BOOK1_ROOT / "mocktests" / "blueprint.yaml").read_text()
    )
    (content_root / "syllabus.md").write_text((BOOK1_ROOT / "syllabus.md").read_text())
    if registered:
        (root / "books.yaml").write_text(
            "books_version: 1\n"
            "books:\n"
            "  - {id: book1, number: 1, root: book1, depends_on: []}\n"
        )
        for relative in (
            "curriculum/course-schedule.yaml",
            "curriculum/coverage-map.yaml",
            "curriculum/material-inventory.yaml",
            "curriculum/official-topics.yaml",
            "curriculum/source-manifest.yaml",
            "docs/course-structure.md",
            "units/.gitkeep",
            "reference/.gitkeep",
        ):
            path = content_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n" if path.suffix == ".yaml" else "fixture\n")
    return content_root


def test_plan016_c9_changed_markdown_has_no_decoded_tex_control_characters():
    unit = BOOK1_ROOT / "units" / "C9-dimensionality-reduction"
    forbidden = {"\t", "\f", "\r"}
    failures = []
    for relative in C9_PLAN016_CHANGED_NOTEBOOKS:
        notebook = json.loads((unit / relative).read_text())
        for cell_index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "markdown":
                continue
            source = "".join(cell.get("source", []))
            controls = sorted({repr(character) for character in source if character in forbidden})
            if controls:
                failures.append(f"{relative}: cell {cell_index}: {', '.join(controls)}")
    assert not failures, "decoded TeX control characters:\n" + "\n".join(failures)


def test_plan016_new_concepts_have_exact_clusters_and_single_owners():
    syllabus = load_syllabus(BOOK1_ROOT)

    assert len(NEW_CONCEPT_CLUSTERS) == 21
    assert {concept: syllabus.concepts.get(concept) for concept in NEW_CONCEPT_CLUSTERS} == (
        NEW_CONCEPT_CLUSTERS
    )

    syllabus_owner_counts = Counter(
        concept for unit in syllabus.units.values() for concept in unit.teaches
    )
    manifest_owner_counts = Counter(
        concept
        for manifest in load_unit_manifests(BOOK1_ROOT)
        for concept in manifest.concepts_taught
    )
    assert {concept: syllabus_owner_counts[concept] for concept in NEW_CONCEPT_CLUSTERS} == {
        concept: 1 for concept in NEW_CONCEPT_CLUSTERS
    }
    assert {concept: manifest_owner_counts[concept] for concept in NEW_CONCEPT_CLUSTERS} == {
        concept: 1 for concept in NEW_CONCEPT_CLUSTERS
    }


def test_plan018_manifests_have_exact_final_counts_and_minutes():
    for unit_id, (sessions, practice_count, minute_totals) in EXPECTED_UNIT_SHAPES.items():
        manifest = _manifest(unit_id)
        minutes = manifest["estimated_minutes"]
        assert minutes["lesson_sessions"] == sessions
        assert (minutes["lesson"], minutes["practice"], minutes["review"]) == minute_totals
        assert len(manifest["practice"]) == practice_count

    manifests = load_unit_manifests(BOOK1_ROOT)
    assert len(manifests) == 19
    assert sum(len(manifest.practice) for manifest in manifests) == 437
    assert sum(len(manifest.lesson_sessions or []) for manifest in manifests) == 69
    minute_totals = {
        field: sum(
            _manifest(manifest.unit_id)["estimated_minutes"][field]
            for manifest in manifests
        )
        for field in ("lesson", "practice", "review")
    }
    assert minute_totals == {"lesson": 5820, "practice": 11890, "review": 925}
    assert sum(minute_totals.values()) == 18635


def test_concepts_have_manifest_owners_for_live_b2_019():
    syllabus = load_syllabus(BOOK1_ROOT)
    book2_syllabus = load_syllabus(BOOK2_ROOT)
    manifests = load_unit_manifests(BOOK1_ROOT)
    book2_manifests = load_unit_manifests(BOOK2_ROOT)
    roadmap = yaml.safe_load((BOOK2_ROOT / "curriculum" / "coverage-map.yaml").read_text())
    syllabus_owner_counts = Counter(
        concept for unit in syllabus.units.values() for concept in unit.teaches
    )
    manifest_owner_counts = Counter(
        concept
        for manifest in manifests
        for concept in manifest.concepts_taught
    )
    manifest_owner_units = {
        concept: manifest.unit_id
        for manifest in manifests
        for concept in manifest.concepts_taught
    }
    planned_units = {row["id"]: row for row in roadmap["planned_units"]}
    knowledge_points = {row["id"]: row for row in roadmap["knowledge_points"]}
    nonlive_book2_units = set(book2_syllabus.units) - {
        manifest.unit_id for manifest in book2_manifests
    }

    assert set(syllabus.concepts) == set(syllabus_owner_counts)
    assert set(syllabus_owner_counts.values()) == {1}
    assert set(manifest_owner_counts) <= set(syllabus.concepts)
    assert set(manifest_owner_counts.values()) == {1}
    assert nonlive_book2_units == set()
    assert [manifest.unit_id for manifest in book2_manifests] == [
        "B2-019-attention-transformers"
    ]
    assert book2_syllabus.units["B2-019-attention-transformers"].teaches == list(
        PLAN019_B2_019_CONCEPTS
    )
    assert set(book2_syllabus.concepts) == set(PLAN019_B2_019_CONCEPTS)
    assert (
        set(planned_units) - {"B2-019-attention-transformers"}
    ).isdisjoint(book2_syllabus.units)

    for unit in syllabus.units.values():
        manifest_counts = {
            concept: manifest_owner_counts[concept] for concept in unit.teaches
        }
        assert manifest_counts == {concept: 1 for concept in unit.teaches}
        assert {
            concept: manifest_owner_units[concept] for concept in unit.teaches
        } == {concept: unit.id for concept in unit.teaches}

    for unit in book2_syllabus.units.values():
        assert re.fullmatch(r"B2-[0-9]{3}-.+", unit.id)
        planned = planned_units[unit.id]
        assert planned["layer"] == "round-2-extension"
        memberships = planned["knowledge_points"]
        assert memberships
        assert len(memberships) == len(set(memberships))
        for point_id in memberships:
            point = knowledge_points[point_id]
            assert point["destination"] == unit.id
            assert point["coverage"] == "missing"
            assert point["shipped_concepts"] == []
            assert all(
                not evidence["lesson_anchors"]
                and not evidence["practices"]
                and not evidence["assessments"]
                for evidence in point["evidence_by_modality"].values()
            )
        assert {
            concept: sum(
                concept in manifest.concepts_taught for manifest in book2_manifests
            )
            for concept in unit.teaches
        } == {concept: 1 for concept in unit.teaches}

    assert {concept: syllabus_owner_counts[concept] for concept in PLAN017_NEW_CONCEPTS} == {
        concept: 1 for concept in PLAN017_NEW_CONCEPTS
    }
    assert {concept: manifest_owner_counts[concept] for concept in PLAN017_NEW_CONCEPTS} == {
        concept: 1 for concept in PLAN017_NEW_CONCEPTS
    }


def test_plan017_c11_manifest_is_the_exact_pinned_training_contract():
    manifest = _manifest("C11-neural-training")

    assert manifest["prereq_units"] == [
        "F4-multivar-calculus",
        "C3-gradient-descent",
        "C5-neural-networks",
        "C6-pytorch",
    ]
    assert manifest["concepts_taught"] == [
        "softmax",
        "cross-entropy-loss",
        "manual-backpropagation",
        "autograd-training",
        "torch-optimizers",
        "trained-mlp",
        "batch-normalization",
        "dropout",
    ]
    assert manifest["concepts_used"] == PLAN017_C11_CONCEPTS_USED
    assert manifest["estimated_minutes"] == {
        "lesson": 450,
        "lesson_sessions": [90, 90, 90, 90, 90],
        "practice": 1040,
        "review": 60,
    }
    actual_rows = [
        (
            row["id"],
            row["set"],
            row["type"],
            row["difficulty"],
            row["concepts"],
            row["path"],
            row["solution_path"],
            row["minutes"],
        )
        for row in manifest["practice"]
    ]
    expected_rows = [
        (
            problem_id,
            set_id,
            problem_type,
            difficulty,
            concepts,
            f"practice/p{index:02}.ipynb",
            f"practice/p{index:02}_solution.ipynb",
            minutes,
        )
        for index, (
            problem_id,
            set_id,
            problem_type,
            difficulty,
            concepts,
            minutes,
        ) in enumerate(PLAN017_C11_PRACTICE_ROWS, start=1)
    ]

    assert actual_rows == expected_rows
    assert all(type(row[-1]) is int and row[-1] > 0 for row in actual_rows)
    assert sum(row[-1] for row in actual_rows) == 1040


def test_plan018_c12_manifest_is_the_exact_double_length_contract():
    syllabus = _canonical_syllabus_yaml()
    units = {unit["id"]: unit for unit in syllabus["units"]}
    c12 = units["C12-classical-models"]
    manifest = _manifest("C12-classical-models")

    assert c12["length"] == "double"
    assert c12["prereqs"] == [
        "C1-ml-fundamentals",
        "C2-linear-models",
        "C3-gradient-descent",
        "C4-classical-ml-practice",
        "F7-kernels-convex-optimization",
    ]
    assert c12["teaches"] == PLAN018_C12_CONCEPTS
    assert manifest["prereq_units"] == c12["prereqs"]
    assert manifest["concepts_taught"] == PLAN018_C12_CONCEPTS
    assert manifest["concept_sessions"] == {
        "logistic-regression": 1,
        "svm": 2,
        "margin-and-hinge-loss": 2,
        "decision-trees": 4,
        "tree-split-criteria": 4,
        "ensemble-learning": 5,
        "bagging-and-boosting": 5,
        "k-means": 6,
        "lloyd-algorithm": 6,
        "classical-model-comparison": 2,
    }
    assert manifest["estimated_minutes"] == {
        "lesson": 540,
        "lesson_sessions": [90, 90, 90, 90, 90, 90],
        "practice": 1410,
        "review": 60,
    }

    actual_ledger = [
        (
            row["id"],
            row["set"],
            row["type"],
            row["difficulty"],
            row["minutes"],
            row["after_session"],
        )
        for row in manifest["practice"]
    ]
    assert actual_ledger == PLAN018_C12_PRACTICE_LEDGER
    assert [row["path"] for row in manifest["practice"]] == [
        f"practice/p{number:02}.ipynb" for number in range(1, 31)
    ]
    assert [row["solution_path"] for row in manifest["practice"]] == [
        f"practice/p{number:02}_solution.ipynb" for number in range(1, 31)
    ]
    assert [row["provenance"] for row in manifest["practice"]] == ["original"] * 30
    assert all("adapted-from" not in row for row in manifest["practice"])
    assert sum(row["minutes"] for row in manifest["practice"]) == 1410

    for concept, problem_numbers in PLAN018_C12_CONCEPT_COVERAGE.items():
        assert [
            row["id"]
            for row in manifest["practice"]
            if concept in row["concepts"]
        ] == [f"C12-p{number:02}" for number in problem_numbers]


def test_plan019_phase1_exact_live_corpus_counts_and_double_length_roster():
    manifests = load_unit_manifests(BOOK1_ROOT)
    syllabus = load_syllabus(BOOK1_ROOT)
    book2_syllabus = load_syllabus(BOOK2_ROOT)

    assert len(manifests) == 19
    assert len(syllabus.concepts) == 149
    assert len(book2_syllabus.concepts) == 11
    assert set(syllabus.concepts).isdisjoint(book2_syllabus.concepts)
    assert sum(len(manifest.practice) for manifest in manifests) == 437
    assert sum(len(manifest.lesson_sessions or []) for manifest in manifests) == 69
    minute_total = sum(
        sum(_manifest(manifest.unit_id)["estimated_minutes"][field] for field in (
            "lesson",
            "practice",
            "review",
        ))
        for manifest in manifests
    )
    assert minute_total == 18635

    double_units = {
        unit.id for unit in syllabus.units.values() if unit.length == "double"
    }
    assert double_units == {
        "F5-probability",
        "F6-svd-spectral",
        "C7-cnn-transfer",
        "C11-neural-training",
        "C12-classical-models",
    }
    standards = (ROOT / "docs" / "unit-standards.md").read_text()
    assert (
        "Double-length units (F5, F6, C7, C11, C12, and B2-019) use 4–6 sessions."
        in standards
    )


@functools.cache
def _plan019_pinned_commit_available() -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", "4cc3894^{commit}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    ).returncode == 0


def _plan019_pinned_paths() -> tuple[list[str], dict[str, set[int]]]:
    if _plan019_pinned_commit_available():
        tracked = subprocess.run(
            [
                "git",
                "ls-tree",
                "-r",
                "--name-only",
                "4cc3894",
                "--",
                "units",
                "mocktests",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        candidates = tracked.stdout.splitlines()
    else:
        candidates = sorted(
            path.relative_to(BOOK1_ROOT).as_posix()
            for tree in (BOOK1_ROOT / "units", BOOK1_ROOT / "mocktests")
            for path in tree.rglob("*")
            if path.is_file()
        )
    paths = [
        path
        for path in candidates
        if path.endswith((".ipynb", "manifest.yaml"))
    ]
    inventory = yaml.safe_load(
        (ROOT / "tests/fixtures/plan019-path-inventory.yaml").read_text(encoding="utf-8")
    )
    changed_cells = {
        row["path"]: set(row["cells"])
        for row in inventory["notebook_pyproject_discovery"]
    }
    for row in inventory["special_notebook_consumers"]:
        changed_cells.setdefault(row["path"], set()).update(row["cells"])
    return paths, changed_cells


def _plan019_pinned_blob(path: str) -> bytes | None:
    if not _plan019_pinned_commit_available():
        return None
    proc = subprocess.run(
        ["git", "show", f"4cc3894:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def _plan019_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_plan019_task3_every_book1_manifest_and_notebook_matches_pinned_cutover() -> None:
    paths, changed_cells = _plan019_pinned_paths()
    notebooks = [path for path in paths if path.endswith(".ipynb")]
    manifests = [path for path in paths if path.endswith("manifest.yaml")]

    assert len(notebooks) == 991
    assert len(manifests) == 20
    assert len(changed_cells) == 67
    assert _plan019_digest(paths) == (
        "76c9236aa561f1bb9c45cd88f3562047fa8e2a5aaec4f18010e43ed81a34e2ec"
    )
    assert len({row["path"] for row in yaml.safe_load(
        (ROOT / "tests/fixtures/plan019-path-inventory.yaml").read_text(encoding="utf-8")
    )["notebook_pyproject_discovery"]}) == 64

    manifest_records: list[list[str]] = []
    unchanged_records: list[list[str]] = []
    changed_structures: list[list[object]] = []
    changed_sources: list[list[object]] = []
    for path in manifests:
        current_bytes = (BOOK1_ROOT / path).read_bytes()
        manifest_records.append([path, hashlib.sha256(current_bytes).hexdigest()])
        pinned_bytes = _plan019_pinned_blob(path)
        if pinned_bytes is not None:
            assert current_bytes == pinned_bytes, path

    observed_changed: set[str] = set()
    for path in notebooks:
        before_bytes = _plan019_pinned_blob(path)
        after_bytes = (BOOK1_ROOT / path).read_bytes()
        if path not in changed_cells:
            unchanged_records.append([path, hashlib.sha256(after_bytes).hexdigest()])
            if before_bytes is not None:
                assert after_bytes == before_bytes, path
            continue

        observed_changed.add(path)
        after = json.loads(after_bytes)
        structure = {key: value for key, value in after.items() if key != "cells"}
        structure["cells"] = []
        for index, cell in enumerate(after["cells"]):
            if index in changed_cells[path]:
                structure["cells"].append(
                    {key: value for key, value in cell.items() if key != "source"}
                )
                changed_sources.append([path, index, cell["source"]])
            else:
                structure["cells"].append(cell)
        changed_structures.append([path, structure])
        if before_bytes is None:
            for index in changed_cells[path]:
                new_source = "".join(after["cells"][index]["source"])
                assert "USAAIO_BOOK_ROOT" in new_source or "book_root" in new_source.lower()
                assert "pyproject.toml" not in new_source
            continue

        before = json.loads(before_bytes)
        expected_cells = changed_cells[path]
        assert {key: value for key, value in before.items() if key != "cells"} == {
            key: value for key, value in after.items() if key != "cells"
        }, path
        assert len(before["cells"]) == len(after["cells"])
        actual_cells = {
            index
            for index, (old_cell, new_cell) in enumerate(
                zip(before["cells"], after["cells"], strict=True)
            )
            if old_cell != new_cell
        }
        assert actual_cells == expected_cells, path
        for index, (old_cell, new_cell) in enumerate(
            zip(before["cells"], after["cells"], strict=True)
        ):
            if index not in expected_cells:
                assert new_cell == old_cell, (path, index)
                continue
            old_without_source = {key: value for key, value in old_cell.items() if key != "source"}
            new_without_source = {key: value for key, value in new_cell.items() if key != "source"}
            assert new_without_source == old_without_source, (path, index)
            new_source = "".join(new_cell["source"])
            assert "USAAIO_BOOK_ROOT" in new_source or "book_root" in new_source.lower()
            assert "pyproject.toml" not in new_source

    assert observed_changed == set(changed_cells)
    assert _plan019_digest(manifest_records) == (
        "75bc145bacd5bacd1c7ec0f62ac966357c314d6cafaf865a51fc1587d42a1c63"
    )
    assert _plan019_digest(unchanged_records) == (
        "0d8749d8fbe48bb37a0dc696a4343779da91d59dad4fbfb619d066856e7b7b5c"
    )
    assert _plan019_digest(changed_structures) == (
        "46ba55a9dd7c657719edca781d6f6035de6dfd01116e9fd9881f62b3a715b73d"
    )
    assert _plan019_digest(changed_sources) == (
        "dd129b119cd491ea083c53b16613a6f1467fec0275639052071bcb9480d24014"
    )


def test_plan019_task3_book1_pdf_sources_match_the_pinned_r1_set() -> None:
    proc = subprocess.run(
        ["bash", "scripts/build-pdf.sh", "--book", "book1", "--list-inputs"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    current = tuple(
        path.removeprefix("book1/") for path in proc.stdout.splitlines() if path.strip()
    )
    if _plan019_pinned_commit_available():
        pinned = tuple(
            path
            for path in subprocess.run(
                [
                    "git",
                    "ls-tree",
                    "-r",
                    "--name-only",
                    "4cc3894",
                    "--",
                    "mocktests/r1-001",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()
            if path == "mocktests/r1-001/test.md"
            or (path.startswith("mocktests/r1-001/theory/") and path.endswith(".md"))
            or (path.startswith("mocktests/r1-001/problems/") and path.endswith(".ipynb"))
        )
    else:
        pinned = current

    assert len(current) == 10
    assert current == pinned
    assert hashlib.sha256("\n".join(current).encode()).hexdigest() == (
        "b07a045f699ba6df93ad4429ae29926b99ade1083ecab005638f478aa614e6e4"
    )


def test_plan019_task3_r1_mock_solution_executes_from_book1_cwd(tmp_path: Path) -> None:
    output = tmp_path / "p09-executed.ipynb"
    env = {**os.environ, "USAAIO_BOOK_ROOT": str(BOOK1_ROOT)}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "execute",
            "mocktests/r1-001/solutions/p09_solution.ipynb",
            "--output",
            str(output),
        ],
        cwd=BOOK1_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert output.is_file() and output.stat().st_size > 0


def test_plan017_c7_manifest_is_double_length_and_preserves_capstone_contracts():
    syllabus = _canonical_syllabus_yaml()
    syllabus_units = {unit["id"]: unit for unit in syllabus["units"]}
    syllabus_c7 = syllabus_units["C7-cnn-transfer"]
    manifest = _manifest("C7-cnn-transfer")

    assert syllabus_c7["length"] == "double"
    assert syllabus_c7["prereqs"] == ["C6-pytorch", "C11-neural-training"]
    assert "cnn-training" in syllabus_c7["teaches"]
    assert manifest["prereq_units"] == ["C6-pytorch", "C11-neural-training"]
    assert "cnn-training" in manifest["concepts_taught"]
    assert manifest["estimated_minutes"] == {
        "lesson": 345,
        "lesson_sessions": [85, 85, 85, 90],
        "practice": 875,
        "review": 60,
    }
    assert len(manifest["practice"]) == 27
    assert len({row["id"] for row in manifest["practice"]}) == 27
    assert len({row["path"] for row in manifest["practice"]}) == 27

    practices = {row["id"]: row for row in manifest["practice"]}
    assert {
        problem_id
        for problem_id, problem in practices.items()
        if "cnn-training" in problem["concepts"]
    } == set(PLAN017_C7_PRESERVED_CONCEPTS)
    for problem_id, preserved in PLAN017_C7_PRESERVED_CONCEPTS.items():
        assert preserved | {"cnn-training"} <= set(practices[problem_id]["concepts"])


def test_plan017_c11_p04_inverted_dropout_scaling_changes_the_answer():
    statement = _notebook_cell_source(
        "units/C11-neural-training/practice/p04.ipynb", "p04-m1"
    )

    assert "E[h_tilde_1^2] / E[h_tilde_2 + h_tilde_3]" in statement
    assert "16/15" in statement
    assert "4/5" in statement
    assert "derive both expectations from the Bernoulli keep mask and the 1/q scale" in statement
    assert "gcd(|a|,b) = 1" in statement
    assert "E[h_tilde_1] / E[h_tilde_2 + h_tilde_3]" not in statement


def test_plan017_c7_p26_pins_construction_to_reference_draw_order():
    statement = _notebook_cell_source(
        "units/C7-cnn-transfer/practice/p26.ipynb", "p26-00"
    )

    assert (
        "construct the convolution/ReLU stack in the listed spec order, then "
        "construct adaptive pool `(1,1)`, flatten, and the 3-class linear head last"
        in statement
    )
    assert "exactly 20 SGD steps (`lr=0.12`)" in statement


def test_plan017_c11_p10_replaces_effectively_zero_linspace_coordinate():
    setup = _notebook_cell_source(
        "units/C11-neural-training/practice/p10.ipynb", "p10-c2"
    )

    assert "x_p10[torch.abs(x_p10) < 1e-9] = 0.125" in setup
    assert "x_p10[x_p10 == 0]" not in setup


def test_plan017_c11_lessons_cover_lambda_rng_and_optimizer_state_contracts():
    lesson_03 = _notebook_cell_source(
        "units/C11-neural-training/lessons/03-numpy-mlp-training.ipynb",
        "c11s3015",
    )
    assert "$\\lambda/2$" in lesson_03
    assert "$\\lambda W$" in lesson_03
    assert "$lambda/2$" not in lesson_03
    assert "$lambda W$" not in lesson_03

    lesson_04_path = BOOK1_ROOT / "units/C11-neural-training/lessons/04-pytorch-autograd-and-optimizers.ipynb"
    lesson_04 = json.loads(lesson_04_path.read_text())
    cell_sources = {
        cell.get("id"): (
            "".join(cell.get("source", []))
            if isinstance(cell.get("source", []), list)
            else cell.get("source", "")
        )
        for cell in lesson_04["cells"]
    }
    all_source = "\n".join(cell_sources.values())

    assert "torch.Generator(device=\"cpu\")" in all_source
    assert "generator=data_generator" in all_source
    assert "local generator does not advance or reset the global generator" in all_source
    assert "torch.manual_seed(SEED)" in cell_sources["c11s4010"]
    assert "torch.use_deterministic_algorithms(True)" in all_source
    assert "raises instead of silently using only a nondeterministic implementation" in all_source
    assert "optimizer.state[first_parameter]" in all_source
    assert "adam_optimizer.state[adam_parameter]" in all_source
    assert '["step"]' in all_source
    assert "**Checkpoint 5C.**" in all_source
    assert "**5C.**" in cell_sources["c11s4016"]


def test_plan016_existing_unit_register_extensions_are_exact():
    expected = {
        "F1-scientific-python": {
            "F1-p22": ("A", "constrained-coding", "intro", ["seaborn-programming"]),
            "F1-p23": ("B", "constrained-coding", "core", ["seaborn-programming"]),
            "F1-p24": (
                "C",
                "integrative",
                "advanced",
                ["seaborn-programming", "random-seeding", "aggregation-axis"],
            ),
        },
        "F5-probability": {
            "F5-p20": ("A", "drill", "intro", ["conditional-probability"]),
            "F5-p21": (
                "B",
                "constrained-coding",
                "core",
                ["conditional-probability", "bayes-rule"],
            ),
            "F5-p22": (
                "B",
                "proof",
                "core",
                ["conditional-probability", "bayes-rule"],
            ),
            "F5-p23": ("B", "mc-normal-form", "core", ["hoeffding-inequality"]),
            "F5-p24": (
                "B",
                "constrained-coding",
                "core",
                ["hoeffding-inequality"],
            ),
            "F5-p25": (
                "C",
                "integrative",
                "advanced",
                [
                    "conditional-probability",
                    "bayes-rule",
                    "hoeffding-inequality",
                    "sampling-simulation",
                ],
            ),
        },
        "C2-linear-models": {
            "C2-p19": (
                "B",
                "proof",
                "core",
                ["linear-regression-estimator-derivation"],
            ),
            "C2-p20": (
                "B",
                "constrained-coding",
                "core",
                ["linear-regression-estimator-derivation"],
            ),
            "C2-p21": (
                "C",
                "integrative",
                "core",
                ["linear-regression-estimator-derivation"],
            ),
            "C2-p22": (
                "B",
                "proof",
                "advanced",
                ["ols-rank-identifiability-and-pseudoinverse"],
            ),
            "C2-p23": (
                "B",
                "constrained-coding",
                "core",
                ["ols-rank-identifiability-and-pseudoinverse"],
            ),
            "C2-p24": (
                "C",
                "challenge",
                "advanced",
                ["ols-rank-identifiability-and-pseudoinverse"],
            ),
        },
        "C9-dimensionality-reduction": {
            "C9-p20": (
                "B",
                "proof",
                "core",
                ["pca-centered-covariance-eigenproblem-derivation"],
            ),
            "C9-p21": (
                "B",
                "proof",
                "advanced",
                ["pca-centered-covariance-eigenproblem-derivation"],
            ),
            "C9-p22": (
                "B",
                "constrained-coding",
                "core",
                ["numpy-pca-class-from-scratch", "pca-black-box-insufficiency"],
            ),
            "C9-p23": (
                "C",
                "integrative",
                "advanced",
                [
                    "pca-centered-covariance-eigenproblem-derivation",
                    "numpy-pca-class-from-scratch",
                    "pca-black-box-insufficiency",
                ],
            ),
            "C9-p24": (
                "C",
                "challenge",
                "advanced",
                ["numpy-pca-class-from-scratch", "pca-black-box-insufficiency"],
            ),
        },
    }
    for unit_id, expected_problems in expected.items():
        actual = {
            problem["id"]: (
                problem["set"],
                problem["type"],
                problem["difficulty"],
                problem["concepts"],
            )
            for problem in _manifest(unit_id)["practice"]
            if problem["id"] in expected_problems
        }
        assert actual == expected_problems

    c10 = {
        problem["id"]: problem for problem in _manifest("C10-competition-craft")["practice"]
    }
    expected_c10_concepts = {
        "C10-p15": ["writeup-quality", *PLAN016_C10_PROMOTED_CONCEPTS],
        "C10-p17": [
            "writeup-quality",
            *PLAN016_C10_PROMOTED_CONCEPTS,
            "train-test-split",
            "f1-macro",
            "knn",
            "feature-scaling",
            "sklearn-pipelines",
        ],
        "C10-p18": [
            "writeup-quality",
            *PLAN016_C10_PROMOTED_CONCEPTS,
            "train-test-split",
            "class-imbalance",
            "accuracy-precision-recall",
            "f1-macro",
            "knn",
            "feature-scaling",
            "sklearn-pipelines",
        ],
    }
    for problem_id, expected_concepts in expected_c10_concepts.items():
        assert c10[problem_id]["concepts"] == expected_concepts
    for concept in PLAN016_C10_PROMOTED_CONCEPTS:
        assert [
            problem_id
            for problem_id, problem in c10.items()
            if concept in problem["concepts"]
        ] == ["C10-p15", "C10-p17", "C10-p18"]


def test_plan016_f1_register_rows_are_under_truthful_set_comments():
    text = (BOOK1_ROOT / "units" / "F1-scientific-python" / "manifest.yaml").read_text()
    set_a, after_a = text.split("# --- Set B: exam register ---", 1)
    set_b, set_c = after_a.split("# --- Set C: integration + challenge ---", 1)

    assert "id: F1-p22" in set_a
    assert "id: F1-p23" in set_b
    assert "id: F1-p24" in set_c


def test_f1_seaborn_array_only_boundary():
    unit_dir = BOOK1_ROOT / "units" / "F1-scientific-python"
    actual_files = {
        path.relative_to(unit_dir) for path in (unit_dir / "lessons").glob("*.ipynb")
    }
    actual_files.update(
        path.relative_to(unit_dir)
        for path in (unit_dir / "practice").glob("p2[234]*.ipynb")
    )
    actual_files.update({Path("lesson.ipynb"), Path("review.ipynb")})

    assert len(F1_SEABORN_ARRAY_ONLY_FILES) == 12
    assert actual_files == F1_SEABORN_ARRAY_ONLY_FILES
    assert all((unit_dir / relative).is_file() for relative in F1_SEABORN_ARRAY_ONLY_FILES)

    forbidden = {
        "import pandas": re.compile(r"\bimport\s+pandas\b", re.IGNORECASE),
        "from pandas": re.compile(r"\bfrom\s+pandas\b", re.IGNORECASE),
        "pd.": re.compile(r"\bpd\s*\."),
        "DataFrame": re.compile(r"\bdataframe\b", re.IGNORECASE),
    }
    for relative in sorted(F1_SEABORN_ARRAY_ONLY_FILES):
        text = (unit_dir / relative).read_text()
        hits = [name for name, pattern in forbidden.items() if pattern.search(text)]
        assert hits == [], f"{relative}: forbidden pandas surface {hits}"


def test_plan016_f7_manifest_has_exact_foundation_contract_and_register():
    syllabus = load_syllabus(BOOK1_ROOT)
    unit = syllabus.units["F7-kernels-convex-optimization"]
    assert unit.track == "foundation"
    assert unit.prereqs == [
        "F3-matrices",
        "F4-multivar-calculus",
        "F6-svd-spectral",
        "C3-gradient-descent",
    ]
    assert unit.teaches == [
        "positive-semidefinite-matrices",
        "kernel-validity",
        "convex-sets",
        "convex-functions",
        "first-order-optimality",
        "lagrangians",
        "optimization-duality",
    ]

    manifest = _manifest(unit.id)
    expected_rows = [
        ("F7-p01", "A", "mc", "intro", ["positive-semidefinite-matrices"]),
        ("F7-p02", "A", "mc", "intro", ["kernel-validity"]),
        ("F7-p03", "A", "mc", "intro", ["convex-sets"]),
        ("F7-p04", "B", "mc-normal-form", "core", ["convex-functions", "first-order-optimality"]),
        ("F7-p05", "A", "constrained-coding", "intro", ["positive-semidefinite-matrices"]),
        ("F7-p06", "B", "constrained-coding", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p07", "B", "constrained-coding", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p08", "A", "constrained-coding", "intro", ["convex-sets"]),
        ("F7-p09", "B", "constrained-coding", "core", ["convex-functions"]),
        ("F7-p10", "B", "constrained-coding", "advanced", ["lagrangians", "optimization-duality"]),
        ("F7-p11", "B", "proof", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p12", "B", "proof", "advanced", ["positive-semidefinite-matrices", "convex-functions", "first-order-optimality"]),
        ("F7-p13", "C", "integrative", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p14", "C", "integrative", "advanced", ["convex-sets", "convex-functions", "first-order-optimality", "lagrangians", "optimization-duality"]),
        ("F7-p15", "C", "scenario", "core", ["positive-semidefinite-matrices", "kernel-validity"]),
        ("F7-p16", "C", "scenario", "core", ["convex-functions", "first-order-optimality"]),
        ("F7-p17", "C", "challenge", "advanced", ["kernel-validity"]),
        ("F7-p18", "C", "challenge", "advanced", ["lagrangians", "optimization-duality"]),
        ("F7-p19", "A", "drill", "intro", ["convex-sets", "convex-functions"]),
        ("F7-p20", "B", "drill", "core", ["lagrangians", "optimization-duality"]),
    ]
    assert [
        (row["id"], row["set"], row["type"], row["difficulty"], row["concepts"])
        for row in manifest["practice"]
    ] == expected_rows


def test_plan018_coverage_map_preserves_prior_rows_and_retires_classical_placeholder():
    roadmap = yaml.safe_load((BOOK1_ROOT / "curriculum" / "coverage-map.yaml").read_text())
    planned = {unit["id"]: unit for unit in roadmap["planned_units"]}
    points = {point["id"]: point for point in roadmap["knowledge_points"]}

    assert "P015-R1-MATH-KERNEL-OPT" not in planned
    assert "P015-R1-CLASSICAL-BREADTH" not in planned
    book2_roadmap = yaml.safe_load(
        (BOOK2_ROOT / "curriculum" / "coverage-map.yaml").read_text()
    )
    book2_planned = {unit["id"]: unit for unit in book2_roadmap["planned_units"]}
    assert "book1:C12-classical-models" in book2_planned[
        "B2-024-gpu-scientific-ml-capstone"
    ]["prerequisites"]
    assert points["seaborn-programming"]["depends_on"] == [
        "numpy-programming",
        "matplotlib-pyplot-programming",
    ]
    assert "array" in points["seaborn-programming"]["rationale"].lower()
    expected_mappings = {
        "valid-kernel-positive-definite-proof": [
            "positive-semidefinite-matrices",
            "kernel-validity",
        ],
        "convex-sets-functions-and-optimality": [
            "convex-sets",
            "convex-functions",
            "first-order-optimality",
        ],
        "constrained-optimization-lagrangian-duality": [
            "lagrangians",
            "optimization-duality",
        ],
    }
    for point_id, shipped_concepts in expected_mappings.items():
        point = points[point_id]
        assert point["coverage"] == "covered"
        assert point["evidence_by_modality"]
        assert all(
            evidence["lesson_anchors"]
            and evidence["practices"]
            and not evidence["assessments"]
            for evidence in point["evidence_by_modality"].values()
        )
        assert point["disposition"] == "keep"
        assert point["destination"] == "F7-kernels-convex-optimization"
        assert point["shipped_concepts"] == shipped_concepts
        assert point["deficits"] == {"modalities_missing": []}


def test_plan019_phase1_book1_narrative_order_and_book2_dependency_contract():
    syllabus = _canonical_syllabus_yaml()
    units = {unit["id"]: unit for unit in syllabus["units"]}
    book1_units = dict(units)
    assert units["F5-probability"]["length"] == "double"
    assert units["F6-svd-spectral"]["length"] == "double"
    assert units["C7-cnn-transfer"]["length"] == "double"
    assert units["C11-neural-training"]["length"] == "double"
    assert units["C12-classical-models"]["length"] == "double"
    narrative = _syllabus_narrative()
    foundation = _narrative_section(narrative, "Foundation track — rationale")
    core = _narrative_section(narrative, "Core track — rationale")
    normalized_foundation = " ".join(foundation.split())
    normalized_core = " ".join(core.split())
    assert "`F5-probability` is a double-length unit" in normalized_foundation
    assert "`F6-svd-spectral` is also a double-length unit" in normalized_foundation
    assert "the other double-length unit" not in normalized_foundation
    assert "`F7-kernels-convex-optimization`" in normalized_foundation
    assert (
        "`C2-linear-models` session 02 ships closed-form unregularized OLS fitting and the "
        "`linear-regression-estimator-derivation`, including rank, identifiability, and "
        "pseudoinverse behavior."
    ) in normalized_core
    assert (
        "Only iterative gradient-based fitting remains deferred to `C3-gradient-descent`."
    ) in normalized_core
    assert "Fitting itself is deferred to `C3-gradient-descent`" not in normalized_core
    engineering_ladder = (
        "`C5-neural-networks` → `C6-pytorch` → `C11-neural-training` → "
        "`C7-cnn-transfer`"
    )
    assert normalized_core.count(engineering_ladder) == 1

    order_section = _narrative_section(
        narrative, "Suggested order (one feasible topological sort)"
    )
    order = re.search(r"^F1 → .* → C12$", order_section, re.MULTILINE)
    assert order is not None
    by_short_id = {unit_id.split("-", 1)[0]: unit_id for unit_id in book1_units}
    ordered_unit_ids = [by_short_id[short_id] for short_id in order.group(0).split(" → ")]
    expected_order = [
        "F1-scientific-python",
        "F2-vectors",
        "C1-ml-fundamentals",
        "F4-multivar-calculus",
        "F3-matrices",
        "F5-probability",
        "C4-classical-ml-practice",
        "C2-linear-models",
        "C3-gradient-descent",
        "C5-neural-networks",
        "C6-pytorch",
        "C11-neural-training",
        "C7-cnn-transfer",
        "C8-embeddings",
        "F6-svd-spectral",
        "F7-kernels-convex-optimization",
        "C9-dimensionality-reduction",
        "C10-competition-craft",
        "C12-classical-models",
    ]
    assert ordered_unit_ids == expected_order
    assert set(ordered_unit_ids) == set(book1_units)
    assert len(ordered_unit_ids) == len(set(ordered_unit_ids)) == 19
    positions = {unit_id: index for index, unit_id in enumerate(ordered_unit_ids)}
    for unit_id in ordered_unit_ids:
        assert all(
            positions[prereq] < positions[unit_id]
            for prereq in book1_units[unit_id]["prereqs"]
        )
    book2 = load_syllabus(BOOK2_ROOT).units["B2-019-attention-transformers"]
    assert (
        book2.book,
        book2.round,
        book2.layer,
        book2.track,
    ) == (2, 2, "round-2-extension", "extension")
    assert book2.prereqs == [
        "book1:C6-pytorch",
        "book1:C7-cnn-transfer",
        "book1:C8-embeddings",
        "book1:C11-neural-training",
    ]
    book2_position = len(ordered_unit_ids)
    assert all(
        positions[prereq.removeprefix("book1:")] < book2_position
        for prereq in book2.prereqs
    )

    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert any(dependency.startswith("seaborn>=") for dependency in project["project"]["dependencies"])
    assert re.search(r'^name = "seaborn"$', (ROOT / "uv.lock").read_text(), re.MULTILINE)
    standards = (ROOT / "docs" / "unit-standards.md").read_text()
    assert (
        "Double-length units (F5, F6, C7, C11, C12, and B2-019) use 4–6 sessions."
        in standards
    )


def test_plan016_practice_coverage_is_green():
    report = check_coverage(BOOK1_ROOT)

    assert report.ok
    assert report.warnings == []
    assert report.errors == []


def test_ci_checks_other_than_plan016_pending_coverage_are_green():
    reports = [
        check_prereq(BOOK1_ROOT),
        check_hygiene(BOOK1_ROOT),
        check_blueprint(BOOK1_ROOT),
        check_overlap(BOOK1_ROOT),
    ]
    for report in reports:
        assert not report.errors
        assert report.ok
        if report.name == "overlap-scan":
            assert report.skipped is None


def test_cli_exit_codes(tmp_path):
    seed_repo(tmp_path, registered=True)
    ok = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.cli",
            "--root",
            str(tmp_path),
            "--book",
            "book1",
            "prereq-check",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert ok.returncode == 0
    fail_root = tmp_path / "fail"
    fail_book = seed_repo(fail_root, registered=True)
    manifest = fail_book / "mocktests" / "r1-001"
    manifest.mkdir(parents=True)
    manifest.joinpath("manifest.yaml").write_text(
        """
test: r1-001
blueprint_version: 1
duration_minutes: 180
total_points: 300
time_budget: {}
problems:
  - id: p01
    section: concept-block
    units: [F1-scientific-python]
    concepts: [vectors-and-norms]
    cluster: linear-algebra
    points: 1
    difficulty: intro
    type: theory
    answer_form: short
    provenance: original
    spec: x
    answer_key: x
"""
    )
    fail = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(fail_root), "--book", "book1", "prereq-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert fail.returncode == 1
    skip_root = tmp_path / "skip"
    skip_book = seed_repo(skip_root, registered=True)
    scaffold_mocktest(skip_book, "r1-001", "2026-08-15")
    skipped = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(skip_root), "--book", "book1", "blueprint-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert skipped.returncode == 3


def test_full_pipeline_on_synthetic_test(tmp_path):
    seed_repo(tmp_path)
    unit_dir = tmp_path / "units" / "F1-scientific-python"
    (unit_dir / "practice").mkdir(parents=True)
    for number in range(1, 4):
        (unit_dir / "practice" / f"p{number:02}.ipynb").write_text(
            '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}'
        )
        (unit_dir / "practice" / f"p{number:02}_solution.ipynb").write_text("{}")
    (unit_dir / "manifest.yaml").write_text(
        """
unit: F1-scientific-python
concepts_taught: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics, seaborn-programming]
concepts_used: [variables-and-types]
prereq_units: []
practice:
  - id: p01
    concepts: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics, seaborn-programming]
    path: practice/p01.ipynb
    solution_path: practice/p01_solution.ipynb
  - id: p02
    concepts: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics, seaborn-programming]
    path: practice/p02.ipynb
    solution_path: practice/p02_solution.ipynb
  - id: p03
    concepts: [numpy-arrays, array-indexing-slicing, broadcasting, vectorization, elementwise-ops, aggregation-axis, random-seeding, matplotlib-basics, seaborn-programming]
    path: practice/p03.ipynb
    solution_path: practice/p03_solution.ipynb
"""
    )
    scaffold_mocktest(tmp_path, "r1-001", "2026-08-15")
    assert check_prereq(tmp_path).ok
    assert check_coverage(tmp_path).ok
    assert check_hygiene(tmp_path).ok
    report = check_blueprint(tmp_path)
    assert report.skipped
    assert report.warnings


def test_ci_flags_draft_manifest_loudly(tmp_path):
    book = seed_repo(tmp_path, registered=True)
    scaffold_mocktest(book, "r1-001", "2026-08-15")
    proc = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(tmp_path), "--book", "book1", "blueprint-check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 3
    assert "DRAFT manifest" in proc.stdout


def test_scope_cli_is_registered_and_loader_errors_are_blocking(tmp_path):
    seed_repo(tmp_path, registered=True)

    proc = subprocess.run(
        [sys.executable, "-m", "tools.cli", "--root", str(tmp_path), "--book", "book1", "scope-check"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "source_schema_version" in proc.stderr
    assert "invalid choice" not in proc.stderr


def test_ci_local_wires_both_mutation_runners_and_generated_document_checks():
    lines = _ci_noncomment_lines()

    audit = 'uv run python -m tools.audit_curriculum --root "$book1_root" --check'
    aggregate = (
        'uv run python -m tools.render_curriculum_roadmap --root "$repo_root" --check'
    )
    structure = (
        'uv run python -m tools.render_course_structure --root "$book1_root" --check'
    )
    training = 'uv run python -m tools.verify_training_mutations --root "$book1_root"'
    classical = 'uv run python -m tools.verify_classical_mutations --root "$book1_root"'
    for command in (audit, aggregate, structure, training, classical):
        assert lines.count(command) == 1
    assert lines.index(audit) < lines.index(aggregate) < lines.index(structure)
    assert lines.index(structure) < lines.index(training) < lines.index(classical)
    assert any(
        line.startswith('uv run usaaio-tools --book "$book" "$c"') for line in lines
    )
    assert any("scope-check" in line for line in lines)


def test_pre_merge_guard_runs_embedded_yaml_with_uv_python():
    script = (ROOT / "scripts" / "pre-merge-guard.sh").read_text()

    assert "uv run python -" in script
    assert "python3 -" not in script


def test_pre_merge_guard_pins_current_scope_inventory_digest():
    script = (ROOT / "scripts" / "pre-merge-guard.sh").read_text()
    inventory = (ROOT / "tests/fixtures/plan019-path-inventory.yaml").read_bytes()
    digest = hashlib.sha256(inventory).hexdigest()

    assert digest in script


def test_pre_merge_guard_rejects_staged_protected_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    for relative in (
        "scripts/pre-merge-guard.sh",
        "scripts/verify-staged-scope.py",
        "tests/fixtures/plan019-path-inventory.yaml",
    ):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    (repo / "scripts/pre-merge-guard.sh").chmod(0o755)
    (repo / "scripts/verify-staged-scope.py").chmod(0o755)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    protected = repo / "tests/.env.production"
    protected.write_text("SECRET=bad\n", encoding="utf-8")
    _git(repo, "add", "-f", "tests/.env.production")

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh"],
        cwd=repo,
        env=_fake_uv_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode != 0
    assert "protected env path" in proc.stdout + proc.stderr


@pytest.mark.parametrize(
    ("mutation", "targets"),
    [
        pytest.param("delete", ("scripts/verify-staged-scope.py",), id="delete-verifier"),
        pytest.param(
            "delete",
            ("tests/fixtures/plan019-path-inventory.yaml",),
            id="delete-inventory",
        ),
        pytest.param(
            "delete",
            (
                "scripts/verify-staged-scope.py",
                "tests/fixtures/plan019-path-inventory.yaml",
            ),
            id="delete-both",
        ),
        pytest.param("replace", ("scripts/verify-staged-scope.py",), id="replace-verifier"),
        pytest.param(
            "replace",
            ("tests/fixtures/plan019-path-inventory.yaml",),
            id="replace-inventory",
        ),
        pytest.param("symlink", ("scripts/verify-staged-scope.py",), id="symlink-verifier"),
        pytest.param(
            "symlink",
            ("tests/fixtures/plan019-path-inventory.yaml",),
            id="symlink-inventory",
        ),
    ],
)
def test_pre_merge_guard_fails_closed_when_enforcement_file_is_mutated(
    tmp_path: Path, mutation: str, targets: tuple[str, ...]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    for relative in (
        "scripts/pre-merge-guard.sh",
        "scripts/verify-staged-scope.py",
        "tests/fixtures/plan019-path-inventory.yaml",
    ):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    (repo / "scripts/pre-merge-guard.sh").chmod(0o755)
    (repo / "scripts/verify-staged-scope.py").chmod(0o755)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")

    for relative in targets:
        target = repo / relative
        target.unlink()
        if mutation == "replace":
            target.write_text("replacement\n", encoding="utf-8")
        elif mutation == "symlink":
            peer = repo / "enforcement-copy"
            peer.write_bytes((ROOT / relative).read_bytes())
            target.symlink_to(peer)
    protected = repo / "tests/.env.production"
    protected.write_text("SECRET=bad\n", encoding="utf-8")
    _git(repo, "add", "-A", "-f")

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh"],
        cwd=repo,
        env=_fake_uv_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode != 0
    diagnostic = proc.stdout + proc.stderr
    assert "enforcement file" in diagnostic.lower()
    assert any(relative in diagnostic for relative in targets)


@pytest.mark.parametrize(
    ("mutation", "relative"),
    [
        pytest.param("delete", "scripts/verify-staged-scope.py", id="index-delete"),
        pytest.param(
            "replace",
            "tests/fixtures/plan019-path-inventory.yaml",
            id="index-replace",
        ),
        pytest.param("symlink", "scripts/verify-staged-scope.py", id="index-symlink"),
    ],
)
def test_pre_merge_guard_rejects_index_only_enforcement_mutation(
    tmp_path: Path, mutation: str, relative: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _install_pre_merge_enforcement(repo)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")

    target = repo / relative
    original = target.read_bytes()
    protected = repo / "tests/.env.production"
    protected.write_text("SECRET=bad\n", encoding="utf-8")
    _git(repo, "add", "-f", "tests/.env.production")
    if mutation == "delete":
        _git(repo, "rm", "--cached", relative)
    else:
        target.unlink()
        if mutation == "replace":
            target.write_text("replacement\n", encoding="utf-8")
        else:
            peer = repo / "enforcement-copy"
            peer.write_bytes(original)
            target.symlink_to(peer)
        _git(repo, "add", relative)
        target.unlink()
    target.write_bytes(original)

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh"],
        cwd=repo,
        env=_fake_uv_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode != 0
    diagnostic = proc.stdout + proc.stderr
    assert "enforcement file" in diagnostic.lower()
    assert relative in diagnostic


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


def _roadmap(destination: str | None, planned_id: str | None) -> str:
    return yaml.safe_dump(
        {
            "roadmap_version": 1,
            "layers": [],
            "planned_units": (
                [{"id": planned_id, "knowledge_points": ["topic-a"]}] if planned_id else []
            ),
            "knowledge_points": (
                [{"id": "topic-a", "destination": destination}] if destination else []
            ),
        },
        sort_keys=False,
    )


def _fake_uv_environment(tmp_path: Path) -> dict[str, str]:
    executable = tmp_path / "bin" / "uv"
    executable.parent.mkdir()
    executable.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "[[ $1 == run ]]\n"
        "shift\n"
        "[[ $1 == python ]]\n"
        "shift\n"
        'exec "$TEST_PYTHON" "$@"\n'
    )
    executable.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{executable.parent}:{env['PATH']}"
    env["TEST_PYTHON"] = sys.executable
    return env


def test_pre_merge_guard_pr_mode_fails_when_origin_main_is_unavailable(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    script = repo / "scripts" / "pre-merge-guard.sh"
    script.parent.mkdir()
    script.write_bytes((ROOT / "scripts" / "pre-merge-guard.sh").read_bytes())
    script.chmod(0o755)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh", "--pr"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "origin/main" in proc.stderr
    assert "unverified" in proc.stderr


def _install_pre_merge_enforcement(repo: Path) -> None:
    for relative in (
        "scripts/pre-merge-guard.sh",
        "scripts/verify-staged-scope.py",
        "tests/fixtures/plan019-path-inventory.yaml",
    ):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    (repo / "scripts/pre-merge-guard.sh").chmod(0o755)
    (repo / "scripts/verify-staged-scope.py").chmod(0o755)


def test_pre_merge_guard_rejects_parallel_roadmap_ownership_collisions(tmp_path):
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    other = tmp_path / "other"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _install_pre_merge_enforcement(repo)
    coverage = repo / "curriculum" / "coverage-map.yaml"
    coverage.parent.mkdir()
    coverage.write_text(_roadmap(None, None))
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    _git(tmp_path, "init", "--bare", str(remote))
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "checkout", "-b", "feature")
    coverage.write_text(_roadmap("U-feature", "P-collision"))

    _git(tmp_path, "clone", "-b", "main", str(remote), str(other))
    _git(other, "config", "user.email", "test@example.com")
    _git(other, "config", "user.name", "Test")
    other.joinpath("curriculum", "coverage-map.yaml").write_text(
        _roadmap("U-main", "P-collision")
    )
    _git(other, "add", ".")
    _git(other, "commit", "-m", "parallel roadmap")
    _git(other, "push", "origin", "main")

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh", "--pr"],
        cwd=repo,
        env=_fake_uv_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "roadmap knowledge-point ownership collision: topic-a" in proc.stdout
    assert "roadmap planned-unit ownership collision: P-collision" in proc.stdout


def test_pre_merge_guard_rejects_b2_unit_id_collision_legacy_regex_misses(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _install_pre_merge_enforcement(repo)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "enforcement base")
    for name in ("B2-019-attention", "B2-019-collision"):
        directory = repo / "units" / name
        directory.mkdir(parents=True)
        directory.joinpath("manifest.yaml").write_text(f"unit: {name}\n")

    proc = subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh"],
        cwd=repo,
        env=_fake_uv_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    assert "duplicate book1/units number(s): B2-019" in proc.stdout


def _ci_noncomment_lines() -> list[str]:
    return [
        line.strip()
        for line in (ROOT / "scripts" / "ci-local.sh").read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_ci_executes_book2_boundary_before_derived_and_preserves_r1_checks() -> None:
    lines = _ci_noncomment_lines()
    checks = next(line for line in lines if line.startswith("for c in prereq-check"))

    assert "layer-boundary-check" in checks
    assert 'uv run python -m tools.render_course_structure --root "$book1_root" --check' in lines
    assert 'bash scripts/build-pdf.sh --book "$book" || { rc=$?; [[ $rc -eq 3 ]] || exit "$rc"; }' in lines
    assert "prereq-check" in checks
    assert "coverage-check" in checks
    assert "blueprint-check" in checks
    assert 'find "$book_root/units" "$book_root/mocktests" -type f \\' in lines


def test_ci_registry_probe_reports_noncanonical_roots_without_id_fallback(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    (repo / "round1").mkdir(parents=True)
    (repo / "advanced").mkdir()
    (repo / "books.yaml").write_text(
        "books_version: 1\nbooks:\n"
        "  - {id: book1, number: 1, root: round1, depends_on: []}\n"
        "  - {id: book2, number: 2, root: advanced, depends_on: [book1]}\n",
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            "bash", str(ROOT / "scripts/ci-local.sh"), "--root", str(repo),
            "--registry-probe",
        ],
        cwd=ROOT,
        env={**os.environ, "PATH": f"{Path.home() / '.local/bin'}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.splitlines() == [
        f"book1\t1\t{repo / 'round1'}",
        f"book2\t2\t{repo / 'advanced'}",
    ]
    script = (ROOT / "scripts/ci-local.sh").read_text(encoding="utf-8")
    assert "$PWD/$book" not in script
    assert "--root book1" not in script


def test_ci_executes_book2_schedule_check() -> None:
    lines = _ci_noncomment_lines()
    checks = next(line for line in lines if line.startswith("for c in prereq-check"))
    assert "schedule-check" in checks
    assert any(
        line.startswith('uv run usaaio-tools --book "$book" "$c"') for line in lines
    )


def test_ci_executes_attention_mutations() -> None:
    lines = _ci_noncomment_lines()
    assert "uv run python -m tools.verify_attention_mutations --root \"$book2_root\"" in lines
    assert not any("SKIP attention mutations" in line for line in lines)


def _plan019_roadmap(*, r1_destination: str, r2_destination: str) -> str:
    return yaml.safe_dump(
        {
            "roadmap_version": 1,
            "layers": ["round-1-core", "round-2-extension"],
            "planned_units": [],
            "knowledge_points": [
                {
                    "id": "r1-topic",
                    "layer": "round-1-core",
                    "destination": r1_destination,
                },
                {
                    "id": "r2-topic",
                    "layer": "round-2-extension",
                    "destination": r2_destination,
                },
            ],
        },
        sort_keys=False,
    )


def _install_plan019_guard(repo: Path) -> None:
    _install_pre_merge_enforcement(repo)


def _write_legacy_layout(repo: Path) -> None:
    (repo / "units" / "C1-base").mkdir(parents=True, exist_ok=True)
    (repo / "units" / "C1-base" / "manifest.yaml").write_text("unit: C1-base\n")
    coverage = repo / "curriculum" / "coverage-map.yaml"
    coverage.parent.mkdir(parents=True, exist_ok=True)
    coverage.write_text(_plan019_roadmap(r1_destination="C1-base", r2_destination="B2-019"))
    (repo / "syllabus.md").write_text("legacy\n")


def _cut_over_fixture(repo: Path) -> None:
    for legacy in ("units", "curriculum"):
        shutil.rmtree(repo / legacy)
    (repo / "syllabus.md").unlink()
    (repo / "books.yaml").write_text(
        yaml.safe_dump(
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
            sort_keys=False,
        )
    )
    for book in ("book1", "book2"):
        (repo / book / "units").mkdir(parents=True, exist_ok=True)
        (repo / book / "curriculum").mkdir(parents=True, exist_ok=True)
    (repo / "book1/curriculum/coverage-map.yaml").write_text(
        _plan019_roadmap(r1_destination="C1-base", r2_destination="B2-019")
    )
    (repo / "book2/curriculum/coverage-map.yaml").write_text(
        _plan019_roadmap(r1_destination="C1-base", r2_destination="B2-019")
    )


def _legacy_union_fixture(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    other = tmp_path / "other"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _install_plan019_guard(repo)
    _write_legacy_layout(repo)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "legacy base")
    _git(tmp_path, "init", "--bare", str(remote))
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "checkout", "-b", "feature")
    _cut_over_fixture(repo)
    _git(tmp_path, "clone", "-b", "main", str(remote), str(other))
    _git(other, "config", "user.email", "test@example.com")
    _git(other, "config", "user.name", "Test")
    return repo, other


def _push_parallel_main(other: Path) -> None:
    _git(other, "add", ".")
    _git(other, "commit", "-m", "parallel main")
    _git(other, "push", "origin", "main")


def _run_plan019_guard(repo: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/pre-merge-guard.sh", "--pr"],
        cwd=repo,
        env=_fake_uv_environment(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )


def test_pre_merge_guard_translates_legacy_unit_collision_into_book1(
    tmp_path: Path,
) -> None:
    repo, other = _legacy_union_fixture(tmp_path)
    (repo / "book1/units/C13-feature").mkdir(parents=True)
    (repo / "book1/units/C13-feature/manifest.yaml").write_text("unit: C13-feature\n")
    (other / "units/C13-main").mkdir(parents=True)
    (other / "units/C13-main/manifest.yaml").write_text("unit: C13-main\n")
    _push_parallel_main(other)

    proc = _run_plan019_guard(repo, tmp_path)

    assert proc.returncode == 1
    assert "C13" in proc.stdout + proc.stderr
    assert "book1" in proc.stdout + proc.stderr


def test_pre_merge_guard_allows_noncolliding_legacy_book1_addition(
    tmp_path: Path,
) -> None:
    repo, other = _legacy_union_fixture(tmp_path)
    (repo / "book1/units/C14-feature").mkdir(parents=True)
    (repo / "book1/units/C14-feature/manifest.yaml").write_text("unit: C14-feature\n")
    (other / "units/C13-main").mkdir(parents=True)
    (other / "units/C13-main/manifest.yaml").write_text("unit: C13-main\n")
    _push_parallel_main(other)

    proc = _run_plan019_guard(repo, tmp_path)

    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize("layer", ["r1", "r2"])
def test_pre_merge_guard_translates_combined_legacy_coverage_row_collisions(
    tmp_path: Path, layer: str
) -> None:
    repo, other = _legacy_union_fixture(tmp_path)
    relative = f"book{1 if layer == 'r1' else 2}/curriculum/coverage-map.yaml"
    feature_path = repo / relative
    feature_path.write_text(
        _plan019_roadmap(
            r1_destination="C13-feature" if layer == "r1" else "C1-base",
            r2_destination="B2-020-feature" if layer == "r2" else "B2-019",
        )
    )
    (other / "curriculum/coverage-map.yaml").write_text(
        _plan019_roadmap(
            r1_destination="C13-main" if layer == "r1" else "C1-base",
            r2_destination="B2-020-main" if layer == "r2" else "B2-019",
        )
    )
    _push_parallel_main(other)

    proc = _run_plan019_guard(repo, tmp_path)

    assert proc.returncode == 1
    assert f"{layer}-topic" in proc.stdout + proc.stderr


def test_pre_merge_guard_rejects_untranslatable_legacy_addition(tmp_path: Path) -> None:
    repo, other = _legacy_union_fixture(tmp_path)
    (other / "curriculum/unclassified-new-contract.yaml").write_text("new: true\n")
    _push_parallel_main(other)

    proc = _run_plan019_guard(repo, tmp_path)

    assert proc.returncode == 1
    assert "untranslatable" in (proc.stdout + proc.stderr).lower()
    assert "unclassified-new-contract.yaml" in proc.stdout + proc.stderr


def test_pre_merge_guard_handles_post_cutover_origin_main_without_translation(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo-post"
    remote = tmp_path / "remote-post.git"
    other = tmp_path / "other-post"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _install_plan019_guard(repo)
    _write_legacy_layout(repo)
    _cut_over_fixture(repo)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "post-cutover base")
    _git(tmp_path, "init", "--bare", str(remote))
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "checkout", "-b", "feature")
    _git(tmp_path, "clone", "-b", "main", str(remote), str(other))
    _git(other, "config", "user.email", "test@example.com")
    _git(other, "config", "user.name", "Test")
    (repo / "book1/units/C13-feature").mkdir(parents=True)
    (repo / "book1/units/C13-feature/manifest.yaml").write_text("unit: C13-feature\n")
    (other / "book1/units/C13-main").mkdir(parents=True)
    (other / "book1/units/C13-main/manifest.yaml").write_text("unit: C13-main\n")
    _push_parallel_main(other)

    proc = _run_plan019_guard(repo, tmp_path)

    assert proc.returncode == 1
    assert "C13" in proc.stdout + proc.stderr
