from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
import yaml

from tools import audit_curriculum
from tools.checks.coverage import check_coverage
from tools.checks.hygiene import check_hygiene
from tools.checks.layer_boundary import check_layer_boundary
from tools.checks.prereq import check_prereq
from tools.model import load_syllabus, load_unit_manifests

ROOT = Path(__file__).resolve().parents[1]
BOOK1_ROOT = ROOT / "book1"
BOOK2_ROOT = ROOT / "book2"
UNIT_ID = "B2-019-attention-transformers"
UNIT = BOOK2_ROOT / "units" / UNIT_ID
SEED = 20260808

LESSONS = [
    "lessons/00-book1-bridge.ipynb",
    "lessons/01-query-key-value-and-scaled-dot-product.ipynb",
    "lessons/02-self-attention-and-masks.ipynb",
    "lessons/03-multi-head-position-and-cost.ipynb",
    "lessons/04-attention-module-and-tiny-training.ipynb",
    "lessons/05-transformer-blocks-and-architecture.ipynb",
]
OWNED_CONCEPTS = [
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
IMPORTED_UNITS = [
    "F1-scientific-python",
    "F2-vectors",
    "F3-matrices",
    "F5-probability",
    "C6-pytorch",
    "C7-cnn-transfer",
    "C8-embeddings",
    "C11-neural-training",
]
LOCAL_PREREQ_UNITS = [
    "book1:C6-pytorch",
    "book1:C7-cnn-transfer",
    "book1:C8-embeddings",
    "book1:C11-neural-training",
]
IMPORTED_CONCEPTS = [
    "numpy-arrays",
    "broadcasting",
    "vectorization",
    "elementwise-ops",
    "aggregation-axis",
    "random-seeding",
    "dot-product",
    "matrix-multiplication",
    "expectation",
    "variance",
    "independence",
    "variance-of-sums",
    "torch-tensors",
    "nn-module",
    "requires-grad",
    "tensor-shape-tracing",
    "softmax",
    "cross-entropy-loss",
    "torch-optimizers",
    "autograd-training",
]
QUALIFIED_CONCEPTS = [f"book1:{concept}" for concept in IMPORTED_CONCEPTS]
MINUTES = [20] * 5 + [50] * 7 + [45] * 4 + [65] * 5 + [55] * 3
SETS = ["A"] * 5 + ["B"] * 11 + ["C"] * 8
TYPES = [
    "mc",
    "mc-normal-form",
    "mc",
    "mc",
    "mc",
    *(["constrained-coding"] * 7),
    *(["proof"] * 4),
    *(["integrative"] * 3),
    "scenario",
    "integrative",
    "scenario",
    "challenge",
    "challenge",
]
DIFFICULTIES = [
    "intro", "intro", "core", "intro", "core", "intro", "intro", "core",
    "intro", "core", "advanced", "core", "core", "core", "advanced", "core",
    "advanced", "core", "advanced", "core", "core", "intro", "advanced", "advanced",
]
AFTER_SESSION = [1, 1, 2, 2, 3, 1, 2, 2, 3, 3, 4, 5, 1, 2, 3, 3, 4, 4, 5, 5, 3, 4, 3, 5]
DIRECT_TAGS = {
    "matrix-transpose": {2, 6, 7},
    "query-key-value-attention": {1, 2, 6},
    "scaled-dot-product-attention": {2, 3, 6, 7, 11, 13, 18},
    "attention-mask": {4, 8, 18, 22},
    "causal-self-attention": {4, 8, 14, 17},
    "multi-head-attention": {10, 15, 23},
    "sinusoidal-positional-encoding": {5, 9, 17},
    "attention-complexity": {16, 21, 23},
    "transformer-residual-layernorm": {12, 19, 24},
    "position-wise-feed-forward": {12, 19, 24},
    "transformer-block": {12, 19, 20, 24},
}


def _raw_manifest() -> dict:
    return yaml.safe_load((UNIT / "manifest.yaml").read_text(encoding="utf-8"))


def _source(path: Path) -> str:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join(
        "".join(cell.get("source", []))
        if isinstance(cell.get("source", ""), list)
        else str(cell.get("source", ""))
        for cell in notebook["cells"]
    )


def _code_source(path: Path) -> str:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return "\n\n".join(
        "".join(cell.get("source", []))
        if isinstance(cell.get("source", ""), list)
        else str(cell.get("source", ""))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )


def test_b2_019_statement_inventory_is_exact_and_contains_no_solutions() -> None:
    expected = {
        "lesson.ipynb",
        "review.ipynb",
        *LESSONS,
        *(f"practice/p{number:02}.ipynb" for number in range(1, 25)),
    }
    actual = {
        path.relative_to(UNIT).as_posix()
        for path in UNIT.rglob("*.ipynb")
    }

    assert actual == expected
    assert len(actual) == 32
    assert not any("solution" in path for path in actual)


def test_b2_019_manifest_pins_identity_imports_minutes_and_paths() -> None:
    raw = _raw_manifest()
    syllabus = load_syllabus(BOOK2_ROOT)
    manifest = load_unit_manifests(BOOK2_ROOT)[0]

    assert raw["unit"] == UNIT_ID
    assert (raw["book"], raw["round"], raw["layer"], raw["track"]) == (
        2, 2, "round-2-extension", "extension"
    )
    assert raw["length"] == syllabus.units[UNIT_ID].length == "double"
    assert raw["concepts_taught"] == OWNED_CONCEPTS
    assert raw["concepts_used"] == raw["concept_prerequisites"] == QUALIFIED_CONCEPTS
    assert raw["prereq_units"] == syllabus.units[UNIT_ID].prereqs == LOCAL_PREREQ_UNITS
    assert manifest.bridge_diagnostic is not None
    assert manifest.bridge_diagnostic.path == LESSONS[0]
    assert manifest.bridge_diagnostic.minutes == 30
    assert manifest.bridge_diagnostic.referenced_concepts == QUALIFIED_CONCEPTS
    assert raw["estimated_minutes"] == {
        "lesson": 450,
        "lesson_sessions": [90, 90, 90, 90, 90],
        "practice": 1120,
        "review": 60,
    }
    assert raw["lesson_paths"] == LESSONS[1:]
    assert raw["overview_path"] == "lesson.ipynb"
    assert raw["review_path"] == "review.ipynb"
    assert raw["generator_path"] == "scripts/generate_attention_data.py"
    assert check_prereq(BOOK2_ROOT).ok


def test_b2_019_practice_ledger_matches_the_frozen_plan() -> None:
    practice = _raw_manifest()["practice"]

    assert [row["id"] for row in practice] == [
        f"B2-019-p{number:02}" for number in range(1, 25)
    ]
    assert [row["minutes"] for row in practice] == MINUTES
    assert [row["set"] for row in practice] == SETS
    assert [row["type"] for row in practice] == TYPES
    assert [row["difficulty"] for row in practice] == DIFFICULTIES
    assert [row["after_session"] for row in practice] == AFTER_SESSION
    assert sum(row["minutes"] for row in practice) == 1120
    assert Counter(row["difficulty"] for row in practice) == {
        "intro": 7, "core": 11, "advanced": 6
    }
    assert Counter(row["type"] for row in practice) == {
        "mc": 4,
        "mc-normal-form": 1,
        "constrained-coding": 7,
        "proof": 4,
        "integrative": 4,
        "scenario": 2,
        "challenge": 2,
    }
    for number, row in enumerate(practice, start=1):
        assert row["provenance"] == "original"
        assert row["path"] == f"practice/p{number:02}.ipynb"
        assert row["solution_path"] == f"practice/p{number:02}_solution.ipynb"
        assert row["compute"] == {"policy": "cpu", "seed": SEED}

    by_concept = {
        concept: {
            number
            for number, row in enumerate(practice, start=1)
            if concept in row["concepts"]
        }
        for concept in OWNED_CONCEPTS
    }
    assert by_concept == DIRECT_TAGS


def test_every_student_surface_is_clean_and_visibly_scoped() -> None:
    report = check_hygiene(BOOK2_ROOT)
    assert report.ok, report.errors

    for path in sorted(UNIT.rglob("*.ipynb")):
        source = _source(path)
        assert "Round 2 extension" in source, path
        assert "compute.policy: cpu" in source, path
        assert "book1:" in source, path
        assert "Remediation:" in source, path
        assert "# SOLUTION" not in source, path
        assert "answer_key" not in source, path
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for cell in notebook["cells"]:
            assert cell.get("execution_count") is None
            assert cell.get("outputs") in (None, [])


def test_every_relative_remediation_link_resolves_from_its_notebook() -> None:
    link_pattern = re.compile(r"\[[^]]+\]\(([^)#]+)(?:#[^)]*)?\)")
    remediation_links = []

    for path in sorted(UNIT.rglob("*.ipynb")):
        source = _source(path)
        for raw_target in link_pattern.findall(source):
            if "book1/units/" not in raw_target:
                continue
            assert raw_target.startswith("."), (path, raw_target)
            target = (path.parent / raw_target).resolve()
            remediation_links.append((path, raw_target, target))
            assert target.is_file(), (path, raw_target, target)
            assert target.is_relative_to(BOOK1_ROOT.resolve()), (path, target)

    assert len(remediation_links) == 141
    assert sum(path.parent == UNIT for path, _, _ in remediation_links) == 8
    assert sum(path.parent != UNIT for path, _, _ in remediation_links) == 133


def test_bridge_diagnoses_every_import_and_links_every_remediation_unit() -> None:
    source = _source(UNIT / LESSONS[0])
    for concept in QUALIFIED_CONCEPTS:
        assert concept in source
    for unit in IMPORTED_UNITS:
        assert f"book1:{unit}" in source
        assert f"book1/units/{unit}/" in source
    for phrase in (
        "NumPy reductions and vectorization",
        "dot products and matrix multiplication",
        "expectation and variance",
        "tensor shapes",
        "cross-entropy",
        "nn.Module",
        "autograd",
        "optimizer",
    ):
        assert phrase in source


def test_lesson_order_and_introduction_sessions_match_concept_contract() -> None:
    raw = _raw_manifest()
    assert raw["lesson_paths"] == LESSONS[1:]
    assert raw["concept_sessions"] == {
        "matrix-transpose": 1,
        "query-key-value-attention": 1,
        "scaled-dot-product-attention": 1,
        "attention-mask": 2,
        "causal-self-attention": 2,
        "multi-head-attention": 3,
        "sinusoidal-positional-encoding": 3,
        "attention-complexity": 3,
        "transformer-residual-layernorm": 5,
        "position-wise-feed-forward": 5,
        "transformer-block": 5,
    }
    for session, relative in enumerate(LESSONS[1:], start=1):
        source = _source(UNIT / relative)
        assert f"Session {session}" in source
        assert "90 minutes" in source
        assert source.count("Checkpoint") >= 4
    joined = "\n".join(_source(UNIT / relative) for relative in LESSONS[1:])
    for heading in ("Common pitfalls", "Exam connections", "Going deeper"):
        assert heading in joined
    assert joined.count("Worked example") >= 2


def test_session4_executes_a_deterministic_attention_training_example() -> None:
    lesson = UNIT / "lessons/04-attention-module-and-tiny-training.ipynb"
    source = _source(lesson)
    code = _code_source(lesson)
    namespace: dict[str, object] = {}

    for marker in (
        "class CausalSelfAttention(nn.Module)",
        "def forward(self, x)",
        "class TinyCausalPredictor(nn.Module)",
        "optimizer.step()",
        "parameter_delta",
        "loss_trace",
        "first_probe",
        "last_probe",
    ):
        assert marker in source

    exec(compile(code, lesson.as_posix(), "exec"), namespace)  # noqa: S102

    torch = pytest.importorskip("torch")
    assert namespace["DEVICE"].type == "cpu"
    assert namespace["PINNED_INPUTS"].shape == (1, 5, 4)
    assert namespace["PINNED_TARGETS"].shape == (1, 5)
    assert namespace["PINNED_ALLOWED"].shape == (5, 5)
    assert torch.equal(namespace["PINNED_ALLOWED"], torch.tril(namespace["PINNED_ALLOWED"]))
    assert namespace["attention_probe_output"].shape == (1, 3, 4)
    assert namespace["attention_probe_weights"].shape == (1, 3, 3)
    assert torch.count_nonzero(
        namespace["attention_probe_weights"].triu(diagonal=1)
    ).item() == 0
    assert len(namespace["loss_trace"]) == 30
    assert namespace["loss_trace"][-1] < namespace["loss_trace"][0]
    assert namespace["parameter_delta"] > 0
    assert namespace["first_probe"].shape == (4,)
    assert namespace["last_probe"].shape == (4,)
    assert namespace["first_probe"].tolist() == pytest.approx(
        namespace["EXPECTED_FIRST_PROBE"], abs=1e-10, rel=1e-10
    )
    assert namespace["last_probe"].tolist() == pytest.approx(
        namespace["EXPECTED_LAST_PROBE"], abs=1e-10, rel=1e-10
    )


@pytest.mark.parametrize("number", [11, 12, 17, 23])
def test_underspecified_practice_setup_cells_are_instantiable(number: int) -> None:
    path = UNIT / f"practice/p{number:02}.ipynb"
    source = _source(path)
    namespace: dict[str, object] = {}

    exec(  # noqa: S102
        compile(_code_source(path), path.as_posix(), "exec"), namespace
    )

    if number == 11:
        assert namespace["q"].shape == (1, 2, 2)
        assert namespace["k"].shape == namespace["v"].shape == (1, 3, 2)
        assert namespace["allowed"].shape == (1, 2, 3)
        assert namespace["expected_weights"].shape == (1, 2, 3)
        assert namespace["expected_output"].shape == (1, 2, 2)
        assert "reject_allowed" in namespace
    elif number == 12:
        assert namespace["x"].shape == (2, 3, 4)
        assert namespace["allowed"].shape == (2, 3, 3)
        assert namespace["ATTENTION_WEIGHT"].shape == (4, 4)
        assert namespace["FFN_WEIGHT_1"].shape == (8, 4)
        assert namespace["FFN_BIAS_1"].shape == (8,)
        assert namespace["FFN_WEIGHT_2"].shape == (4, 8)
        assert namespace["FFN_BIAS_2"].shape == (4,)
        assert "class SuppliedAttention(nn.Module)" in source
    elif number == 17:
        assert namespace["inputs"].shape == (1, 5, 4)
        assert namespace["targets"].shape == (1, 5)
        assert namespace["allowed"].shape == (5, 5)
        assert set(namespace["INITIAL_PARAMETERS"]) == {
            "q.weight", "k.weight", "v.weight", "out.weight",
            "head.weight", "head.bias",
        }
        assert "nn.Embedding" not in source
        assert "embedding-matrices" not in source
        assert "logits_before" in source and "logits_after" in source
    else:
        assert namespace["H0"].shape == namespace["H1"].shape == (3, 2)
        assert namespace["heads"].shape == (2, 3, 2)
        assert namespace["BUDGET"] == 20


def test_coding_statements_pin_reproducibility_and_api_contracts() -> None:
    for number in range(6, 13):
        source = _source(UNIT / f"practice/p{number:02}.ipynb")
        for marker in (
            "seed `20260808`",
            "dtype",
            "shape",
            "Allowed APIs",
            "Banned APIs",
            "atol",
            "rtol",
            "fixed probe",
        ):
            assert marker in source, (number, marker)

    for number in (9, 17):
        source = _source(UNIT / f"practice/p{number:02}.ipynb")
        assert "pinned numeric" in source
        assert "one-hot" in source
        assert "nn.Embedding" not in source
        assert "embedding-matrices" not in source


def test_generator_is_deterministic_cpu_only_and_uses_no_network(tmp_path: Path) -> None:
    script = UNIT / "scripts/generate_attention_data.py"
    source = script.read_text(encoding="utf-8")
    ast.parse(source)
    assert f"SEED = {SEED}" in source
    assert "numpy" in source
    assert not any(token in source for token in ("requests", "urllib", "cuda", "mps"))

    first = tmp_path / "first.npz"
    second = tmp_path / "second.npz"
    subprocess.run([sys.executable, str(script), "--output", str(first)], check=True)
    subprocess.run([sys.executable, str(script), "--output", str(second)], check=True)
    assert first.read_bytes() == second.read_bytes()


def test_unit_standards_names_b2_019_in_double_length_roster() -> None:
    standards = (ROOT / "docs/unit-standards.md").read_text(encoding="utf-8")
    assert "B2-019-attention-transformers" in standards
    assert "F5, F6, C7, C11, C12, and B2-019" in standards


def _copy_registered_statement_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    shutil.copy2(ROOT / "books.yaml", repo / "books.yaml")
    (repo / "book1").mkdir()
    shutil.copy2(BOOK1_ROOT / "syllabus.md", repo / "book1/syllabus.md")
    shutil.copytree(BOOK2_ROOT, repo / "book2")
    return repo / "book2"


def _install_solution_placeholders(book2: Path, count: int) -> None:
    practice = book2 / "units" / UNIT_ID / "practice"
    for number in range(1, count + 1):
        shutil.copy2(
            practice / f"p{number:02}.ipynb",
            practice / f"p{number:02}_solution.ipynb",
        )


def test_task6_solution_paths_follow_exact_all_or_none_phase_rule(tmp_path: Path) -> None:
    zero = _copy_registered_statement_repo(tmp_path / "zero")
    audit_curriculum.build_inventory(zero)
    assert check_coverage(zero).ok
    assert check_layer_boundary(zero).ok

    partial = _copy_registered_statement_repo(tmp_path / "partial")
    _install_solution_placeholders(partial, 1)
    with pytest.raises(audit_curriculum.InventoryError, match="declared notebook is missing"):
        audit_curriculum.build_inventory(partial)
    assert any("missing solution path" in error for error in check_coverage(partial).errors)
    assert any(
        "cpu task requires a local solution path"
        in error for error in check_layer_boundary(partial).errors
    )

    complete = _copy_registered_statement_repo(tmp_path / "complete")
    _install_solution_placeholders(complete, 24)
    audit_curriculum.build_inventory(complete)
    assert check_coverage(complete).ok
    assert check_layer_boundary(complete).ok
