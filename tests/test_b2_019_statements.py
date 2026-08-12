from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import warnings
from collections import Counter
from pathlib import Path

import nbformat
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
AFTER_SESSION = [1, 1, 2, 2, 3, 1, 2, 2, 3, 3, 4, 5, 1, 2, 3, 3, 4, 4, 5, 5, 3, 5, 3, 5]
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


def _execute_solution_with_replacements(
    number: int,
    replacements: tuple[tuple[str, str], ...] = (),
) -> dict[str, object]:
    path = UNIT / f"practice/p{number:02}_solution.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    namespace: dict[str, object] = {}
    remaining = list(replacements)

    for cell_index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = (
            "".join(cell.get("source", []))
            if isinstance(cell.get("source", ""), list)
            else str(cell.get("source", ""))
        )
        for old, new in tuple(remaining):
            count = source.count(old)
            if count:
                assert count == 1, (number, old, count)
                source = source.replace(old, new)
                remaining.remove((old, new))
        exec(  # noqa: S102 - execute actual notebook cells and their answer checks
            compile(source, f"p{number:02}_solution.ipynb:cell-{cell_index}", "exec"),
            namespace,
        )

    assert not remaining, (number, remaining)
    return namespace


def _qualified_prerequisites_from_header(path: Path) -> set[str]:
    match = re.search(
        r"\*\*Qualified Book 1 prerequisites:\*\* (?P<items>[^\n]+)",
        _source(path),
    )
    assert match is not None, path
    return set(re.findall(r"`(book1:[^`]+)`", match.group("items")))


def _embedding_api_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    aliases: dict[str, set[str]] = {}
    violations: list[str] = []
    forbidden = {
        "torch.nn.Embedding",
        "torch.nn.modules.sparse.Embedding",
        "torch.nn.functional.embedding",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases.setdefault(alias.asname or alias.name, set()).add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                qualified = f"{module}.{alias.name}" if module else alias.name
                aliases.setdefault(alias.asname or alias.name, set()).add(qualified)
                if qualified in forbidden:
                    violations.append(f"import {qualified}")

    def qualified_names(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Name):
            return aliases.get(node.id, {node.id})
        if isinstance(node, ast.Attribute):
            return {f"{owner}.{node.attr}" for owner in qualified_names(node.value)}
        return set()

    assignments: list[tuple[list[ast.expr], ast.expr]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            assignments.append((node.targets, node.value))
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            assignments.append(([node.target], node.value))
    for _ in range(len(assignments) + 1):
        changed = False
        for targets, value in assignments:
            values = qualified_names(value)
            if not values:
                continue
            for target in targets:
                if isinstance(target, ast.Name):
                    before = len(aliases.get(target.id, set()))
                    aliases.setdefault(target.id, set()).update(values)
                    changed |= len(aliases[target.id]) != before
        if not changed:
            break

    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.Name, ast.Attribute))
            and isinstance(node.ctx, ast.Load)
        ):
            for name in sorted(qualified_names(node) & forbidden):
                violations.append(f"reference {name}")
        if not isinstance(node, ast.Call):
            continue
        names = qualified_names(node.func)
        for name in sorted(names & forbidden):
            violations.append(f"call {name}")
        if (
            "getattr" in names
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            dynamic_names = {
                f"{owner}.{node.args[1].value}"
                for owner in qualified_names(node.args[0])
            }
            for dynamic_name in sorted(dynamic_names & forbidden):
                violations.append(f"dynamic call {dynamic_name}")
    return violations


def _generator_source_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    violations: list[str] = []
    aliases: dict[str, set[str]] = {}
    allowed_import_roots = {"__future__", "argparse", "io", "zipfile", "numpy"}
    forbidden_roots = {
        "os", "subprocess", "pathlib", "requests", "urllib", "socket", "http", "ftplib"
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases.setdefault(alias.asname or alias.name, set()).add(alias.name)
                root = alias.name.split(".")[0]
                if root not in allowed_import_roots:
                    violations.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0]
            if root not in allowed_import_roots:
                violations.append(f"import {module}")
            for alias in node.names:
                qualified = f"{module}.{alias.name}" if module else alias.name
                aliases.setdefault(alias.asname or alias.name, set()).add(qualified)

    def qualified_names(node: ast.AST) -> set[str]:
        if isinstance(node, ast.Name):
            return aliases.get(node.id, {node.id})
        if isinstance(node, ast.Attribute):
            return {f"{owner}.{node.attr}" for owner in qualified_names(node.value)}
        return set()

    assignments: list[tuple[list[ast.expr], ast.expr]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            assignments.append((node.targets, node.value))
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            assignments.append(([node.target], node.value))
    for _ in range(len(assignments) + 1):
        changed = False
        for targets, value in assignments:
            values = qualified_names(value)
            if not values:
                continue
            for target in targets:
                if isinstance(target, ast.Name):
                    before = len(aliases.get(target.id, set()))
                    aliases.setdefault(target.id, set()).update(values)
                    changed |= len(aliases[target.id]) != before
        if not changed:
            break

    dangerous_builtins = {"__import__", "exec", "eval", "compile", "open"}
    dangerous_calls = dangerous_builtins | {
        "importlib.import_module",
        *(f"__builtins__.{name}" for name in dangerous_builtins),
    }

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        names = qualified_names(node.func)
        if "numpy.load" in names:
            allow_pickle = [
                keyword.value
                for keyword in node.keywords
                if keyword.arg == "allow_pickle"
            ]
            if not (
                len(allow_pickle) == 1
                and isinstance(allow_pickle[0], ast.Constant)
                and allow_pickle[0].value is False
            ):
                violations.append("numpy.load requires literal allow_pickle=False")
        for name in sorted(names & dangerous_calls):
            violations.append(f"dynamic execution {name}")
        if (
            "getattr" in names
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            dynamic_names = {
                f"{owner}.{node.args[1].value}"
                for owner in qualified_names(node.args[0])
            }
            for name in sorted(dynamic_names & dangerous_calls):
                violations.append(f"dynamic execution {name}")
        for name in sorted(names):
            if name.split(".")[0] in forbidden_roots:
                violations.append(f"forbidden call {name}")
    return violations


def test_b2_019_notebook_inventory_is_exact_after_task6() -> None:
    expected = {
        "lesson.ipynb",
        "review.ipynb",
        *LESSONS,
        *(f"practice/p{number:02}.ipynb" for number in range(1, 25)),
        *(f"practice/p{number:02}_solution.ipynb" for number in range(1, 25)),
    }
    actual = {
        path.relative_to(UNIT).as_posix()
        for path in UNIT.rglob("*.ipynb")
    }

    assert actual == expected
    assert len(actual) == 56
    assert sum("_solution.ipynb" in path for path in actual) == 24


def test_task6_solutions_preserve_source_isolation_and_answer_register() -> None:
    answer_register = {
        1: 'ANSWER = "B"',
        2: 'ANSWER = "A"',
        3: 'ANSWER = "B"',
        4: 'ANSWER = "B"',
        5: 'ANSWER = "C"',
    }
    implementation_register = {
        6: "def scaled_dot_product_attention_np(q, k, v)",
        7: "def batched_self_attention_np(x)",
        8: "def causal_attention_np(q, k, v)",
        9: "def sinusoidal_table(length, width)",
        10: "def split_heads(x, h)",
        11: "class ScaledMaskedAttention(nn.Module)",
        12: "class PreNormBlock(nn.Module)",
        17: "class CausalPredictor(nn.Module)",
    }
    raw = _raw_manifest()

    for number, problem in enumerate(raw["practice"], start=1):
        statement_path = UNIT / problem["path"]
        solution_path = UNIT / problem["solution_path"]
        solution = json.loads(solution_path.read_text(encoding="utf-8"))
        statement_source = _source(statement_path)
        solution_source = _source(solution_path)
        code = _code_source(solution_path)

        assert solution_path.name == f"p{number:02}_solution.ipynb"
        assert solution_source != statement_source
        assert "## Your response" in statement_source
        assert "## Your response" not in solution_source
        assert "# Write your implementation here." not in solution_source
        assert solution["cells"][-2]["cell_type"] == "markdown"
        assert solution["cells"][-2]["source"].strip() == "### Answer check"
        assert solution["cells"][-1]["cell_type"] == "code"
        assert "assert " in solution["cells"][-1]["source"]
        expected_prerequisites = [
            "book1:F1-scientific-python",
            "book1:F3-matrices",
            "book1:C6-pytorch",
            "book1:C11-neural-training",
        ]
        if number == 13:
            expected_prerequisites.insert(2, "book1:F5-probability")
        assert solution["metadata"]["usaaio"] == {
            "book": 2,
            "layer": "Round 2 extension",
            "unit": UNIT_ID,
            "surface": f"practice/p{number:02}_solution.ipynb",
            "compute": {"policy": "cpu", "seed": SEED},
            "qualified_prerequisites": expected_prerequisites,
        }
        for marker in (
            "Round 2 extension",
            "compute.policy: cpu",
            "Qualified Book 1 prerequisites:",
            "Remediation:",
            "SEED = 20260808",
            "ATOL =",
            "RTOL =",
        ):
            assert marker in solution_source, (number, marker)
        for cell in solution["cells"]:
            assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", cell["id"])
            assert cell.get("execution_count") is None
            assert cell.get("outputs") in (None, [])

        if number in answer_register:
            assert answer_register[number] in code
        if number in implementation_register:
            assert implementation_register[number] in code

    assert "NORMAL_FORM = (1, 1)" in _code_source(UNIT / "practice/p02_solution.ipynb")
    assert "logits_before" in _code_source(UNIT / "practice/p17_solution.ipynb")
    assert "logits_after" in _code_source(UNIT / "practice/p17_solution.ipynb")
    assert "losses = np.asarray(loss_values" in _code_source(
        UNIT / "practice/p17_solution.ipynb"
    )


def test_solution_notebooks_have_valid_ids_without_nbformat_missing_id_warnings() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for number in range(1, 25):
            path = UNIT / f"practice/p{number:02}_solution.ipynb"
            notebook = nbformat.read(path, as_version=4)
            nbformat.validate(notebook)
    assert not [warning for warning in caught if "MissingIDFieldWarning" in str(warning.category)]


def test_task6_real_solution_set_is_all_or_none(tmp_path: Path) -> None:
    book2 = _copy_registered_statement_repo(tmp_path, include_solutions=True)
    missing = (
        book2 / "units" / UNIT_ID / "practice" / "p24_solution.ipynb"
    )
    missing.unlink()

    with pytest.raises(audit_curriculum.InventoryError, match="declared notebook is missing"):
        audit_curriculum.build_inventory(book2)
    assert any("missing solution path" in error for error in check_coverage(book2).errors)
    assert any(
        "cpu task requires a local solution path" in error
        for error in check_layer_boundary(book2).errors
    )


def test_b2_019_manifest_pins_identity_imports_minutes_and_paths() -> None:
    raw = _raw_manifest()
    syllabus = load_syllabus(BOOK2_ROOT)
    manifest = load_unit_manifests(BOOK2_ROOT)[0]

    assert raw["unit"] == UNIT_ID
    assert (raw["book"], raw["round"], raw["layer"], raw["track"]) == (
        2, 2, "round-2-extension", "extension"
    )
    assert raw["length"] == syllabus.units[UNIT_ID].length == "double"
    assert raw["solution_policy"] == manifest.solution_policy == "required"
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

    assert len(remediation_links) == 241
    assert sum(path.parent == UNIT for path, _, _ in remediation_links) == 9
    assert sum(path.parent != UNIT for path, _, _ in remediation_links) == 232


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

    namespace: dict[str, object] = {}
    exec(compile(_code_source(UNIT / LESSONS[0]), LESSONS[0], "exec"), namespace)  # noqa: S102
    assert namespace["bridge_all_checks_pass"] is True
    assert namespace["bridge_feedback"] == "ready for B2-019"


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


def test_lesson_prerequisite_header_exactly_matches_notebook_metadata() -> None:
    for relative in LESSONS:
        path = UNIT / relative
        notebook = json.loads(path.read_text(encoding="utf-8"))
        visible = _qualified_prerequisites_from_header(path)
        metadata = set(notebook["metadata"]["usaaio"]["qualified_prerequisites"])
        assert visible == metadata, path


def test_each_ninety_minute_lesson_has_substantive_progression() -> None:
    required_anchors = {
        1: ("$QK^\\top$", "stable softmax", "convex combination"),
        2: ("padding mask", "causal mask", "row normalization"),
        3: ("$Q=XW_Q$", "$K=XW_K$", "$V=XW_V$", "$QK^\\top", "$AV$"),
        4: ("gradient", "cross-entropy", "parameter update"),
        5: ("encoder self-attention", "decoder causal self-attention", "cross-attention", "mask flow"),
    }
    for session, relative in enumerate(LESSONS[1:], start=1):
        source = _source(UNIT / relative)
        headings = re.findall(r"^## \d+\. ", source, flags=re.MULTILINE)
        assert 6 <= len(headings) <= 10, (relative, len(headings))
        assert source.count("Worked example") >= 2, relative
        assert source.count("Checkpoint") >= 6, relative
        for anchor in required_anchors[session]:
            assert anchor in source, (relative, anchor)


def test_p14_identifies_post_softmax_future_key_denominator_leakage() -> None:
    source = _source(UNIT / "practice/p14.ipynb")
    assert "post-softmax zeroing breaks causal independence" in source
    assert "forbidden future key scores" in source
    assert "breaks row normalization" in source
    assert "[0,0]" in source and "[0,10]" in source
    assert "[1,0]" in source and "[2,999]" in source


def test_final_review_statement_contracts_are_explicit_and_falsifiable() -> None:
    p02 = _source(UNIT / "practice/p02.ipynb")
    assert "before simplifying" not in p02

    p06 = _source(UNIT / "practice/p06.ipynb")
    assert "math path" in p06 and "Validation APIs" in p06

    p08 = _source(UNIT / "practice/p08.ipynb")
    assert "`-np.inf` for forbidden" in p08 and "`0.0` for allowed" in p08

    p09 = _source(UNIT / "practice/p09.ipynb")
    assert "10000" in p09 and "2i/width" in p09

    p13 = _source(UNIT / "practice/p13.ipynb")
    assert "mutually independent" in p13
    assert "coordinate products" in p13
    assert "correlated counterexample" in p13
    assert "book1:F5-probability" in p13

    p17 = _source(UNIT / "practice/p17.ipynb")
    assert "mean cross-entropy" in p17
    assert 'reduction="mean"' in _code_source(UNIT / "practice/p17_solution.ipynb")


def test_final_review_solution_checks_pin_values_and_forbidden_key_columns() -> None:
    p16 = _code_source(UNIT / "practice/p16_solution.ipynb")
    for assertion in (
        "assert qkv_projection_multiplies == 4320",
        "assert output_projection_multiplies == 1440",
        "assert score_product_multiplies == 600",
        "assert weighted_value_multiplies == 600",
        "assert total_multiplies == 6960",
        "assert score_scalars == 150",
    ):
        assert assertion in p16

    p22 = _code_source(UNIT / "practice/p22_solution.ipynb")
    assert "False" in p22
    assert "decoder_broadcast[:, :, :, 3]" in p22
    namespace = _execute_solution_with_replacements(22)
    assert not namespace["target_valid"][1, 3]
    assert not namespace["decoder_broadcast"][1, :, :, 3].any()


@pytest.mark.parametrize(
    ("number", "replacements"),
    [
        pytest.param(
            3,
            (("np.sqrt(X.shape[-1])", "np.sqrt(X.shape[-2])"),),
            id="p03-scale-by-sequence-length",
        ),
        pytest.param(
            7,
            ((
                "weights = numerators / np.sum(numerators, axis=-1, keepdims=True)",
                "weights = np.full_like(numerators, 1.0 / x.shape[1])",
            ),),
            id="p07-uniform-weights-and-output",
        ),
        pytest.param(
            8,
            ((
                "    output = weights @ v",
                (
                    "    weights[1] = np.array([0.75, 0.25, 0.0], "
                    "dtype=np.float64)\n    output = weights @ v"
                ),
            ),),
            id="p08-arbitrary-later-causal-row",
        ),
        pytest.param(
            9,
            (("np.log(10000.0)", "np.log(100.0)"),),
            id="p09-base-100",
        ),
        pytest.param(
            9,
            (("    return table", "    table[2] = 0.0\n    return table"),),
            id="p09-zero-row-two",
        ),
        pytest.param(
            10,
            (
                (
                    "return x.reshape(b, n, h, d // h).transpose(0, 2, 1, 3)",
                    "return x.reshape(b, n, d // h, h).transpose(0, 3, 1, 2)",
                ),
                (
                    "return heads.transpose(0, 2, 1, 3).reshape(b, n, h * d_h)",
                    "return heads.transpose(0, 2, 3, 1).reshape(b, n, h * d_h)",
                ),
            ),
            id="p10-interleaved-head-features",
        ),
        pytest.param(
            15,
            ((
                "concatenated = head_values.transpose(0, 2, 1, 3).reshape(B, N, D)",
                "concatenated = head_values.reshape(B, N, D)",
            ),),
            id="p15-omit-concat-transpose",
        ),
        pytest.param(
            24,
            (("a = layer_norm_rows(x)", "a = x"),),
            id="p24-skip-first-pre-norm",
        ),
    ],
)
def test_task6_answer_checks_reject_quality_review_mutants(
    number: int,
    replacements: tuple[tuple[str, str], ...],
) -> None:
    with pytest.raises(AssertionError):
        _execute_solution_with_replacements(number, replacements)


def test_p14_solution_executes_both_post_and_pre_softmax_counterexamples() -> None:
    namespace = _execute_solution_with_replacements(14)
    assert namespace["postmasked_output_before"] == pytest.approx(1.0)
    assert namespace["postmasked_output_after"] == pytest.approx(9.079573740486879e-05)
    assert namespace["premasked_output_before"] == pytest.approx(2.0)
    assert namespace["premasked_output_after"] == pytest.approx(2.0)


def test_session4_executes_a_deterministic_attention_training_example() -> None:
    lesson = UNIT / "lessons/04-attention-module-and-tiny-training.ipynb"
    source = _source(lesson)
    code = _code_source(lesson)
    namespace: dict[str, object] = {}

    for marker in (
        "class CausalSelfAttention(nn.Module)",
        "def forward(self, x, allowed)",
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
    with pytest.raises(ValueError, match="floating"):
        namespace["attention_probe"](namespace["PROBE_INPUT"].to(torch.int64), namespace["PINNED_ALLOWED"][:3, :3])
    with pytest.raises(ValueError, match="allowed key"):
        namespace["attention_probe"](namespace["PROBE_INPUT"], torch.zeros(3, 3, dtype=torch.bool))
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


@pytest.mark.parametrize("number", [9, 17])
def test_embedding_apis_are_ast_forbidden_and_metadata_stays_independent(
    number: int,
) -> None:
    path = UNIT / f"practice/p{number:02}.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert _embedding_api_violations(_code_source(path)) == []
    assert "book1:C8-embeddings" not in notebook["metadata"]["usaaio"][
        "qualified_prerequisites"
    ]


@pytest.mark.parametrize(
    "source",
    [
        "from torch.nn import Embedding as E\nlayer = E(4, 2)",
        "import torch.nn as layers\nlayer = layers.Embedding(4, 2)",
        "from torch.nn.functional import embedding as lookup\nlookup(ids, weight)",
        "import torch.nn.functional as F\nF.embedding(ids, weight)",
        "import torch.nn as nn\nE = nn.Embedding\nE(4, 2)",
        "import torch.nn as nn\nE = nn.Embedding\nLayer = E\nLayer(4, 2)",
        "import torch\nF = torch.nn.functional\nF.embedding(ids, weight)",
        "from torch import nn as layers\nE = layers.Embedding\nE(4, 2)",
        "from torch.nn import functional as F\nF.embedding(ids, weight)",
        "import torch as framework\nE = framework.nn.Embedding\nE(4, 2)",
        "import torch.nn.modules.sparse as sparse\nsparse.Embedding(4, 2)",
        "from torch.nn.modules.sparse import Embedding as E\nE(4, 2)",
        "import torch.nn as nn\ngetattr(nn, 'Embedding')(4, 2)",
        "import torch.nn.functional as F\ngetattr(F, 'embedding')(ids, weight)",
        "import torch\ngetattr(torch.nn, 'Embedding')(4, 2)",
        "import torch\ngetattr(torch.nn.functional, 'embedding')(ids, weight)",
        "import torch.nn as nn\nresolve = getattr\nresolve(nn, 'Embedding')(4, 2)",
        "import torch.nn.functional as F\nlookup = F.embedding\nlookup(ids, weight)",
        "import torch.nn as nn\nE = nn.Embedding\nE = int\nE(4, 2)",
    ],
)
def test_embedding_api_audit_rejects_imports_aliases_and_calls(source: str) -> None:
    assert _embedding_api_violations(source)


@pytest.mark.parametrize(
    "source",
    [
        "import torch.nn as nn\nE: object = nn.Embedding\nE(4, 2)",
        (
            "import torch.nn.functional as F\n"
            "lookup: object = F.embedding\nlookup(ids, weight)"
        ),
        "import torch.nn as nn\nE = nn.Embedding",
        "import torch.nn.functional as F\nlookup = F.embedding",
        "import torch.nn as nn\nnn.Embedding",
        "import torch.nn.functional as F\nF.embedding",
        "import torch.nn as nn\nE = nn.Embedding\nLayer = E\nFinal = Layer",
        (
            "import torch.nn.functional as F\n"
            "lookup: object = F.embedding\nnext_lookup = lookup\nfinal_lookup = next_lookup"
        ),
    ],
)
def test_embedding_api_audit_rejects_bindings_references_and_annassign(
    source: str,
) -> None:
    assert _embedding_api_violations(source)


@pytest.mark.parametrize(
    "source",
    [
        "import torch.nn as nn\nlayer = nn.EmbeddingBag(4, 2)",
        "import torch.nn.functional as F\nF.embedding_bag(ids, weight)",
        "def embedding_loss(x):\n    return x",
        "class Embedding:\n    pass\nlayer = Embedding()",
        "import torch.nn as nn\ngetattr(nn, 'EmbeddingBag')(4, 2)",
        "import torch.nn.functional as F\ngetattr(F, 'embedding_bag')(ids, weight)",
        "message = 'nn.Embedding and F.embedding are forbidden'",
        "# nn.Embedding(4, 2)\nvalue = 1",
        "from custom_layers import Embedding\nlayer = Embedding()",
        "from project import embedding\nembedding(ids, weight)",
        "class Namespace:\n    pass\nobj = Namespace()\nobj.Embedding = lambda: None\nobj.Embedding()",
        "embedding_projection = lambda x: x\nembedding_projection(ids)",
        "import torch.nn as nn\nE: object = nn.EmbeddingBag\nE(4, 2)",
        (
            "import torch.nn.functional as F\n"
            "lookup: object = F.embedding_bag\nlookup(ids, weight)"
        ),
        "import torch.nn as nn\nnear = nn.EmbeddingBag",
        "import torch.nn.functional as F\nnear = F.embedding_bag",
    ],
)
def test_embedding_api_audit_allows_safe_near_names(source: str) -> None:
    assert _embedding_api_violations(source) == []


@pytest.mark.parametrize(
    "source",
    [
        "import numpy as np\nnp.load('data.npy')",
        "import numpy as np\nnp.load('data.npy', allow_pickle=True)",
        "import numpy as np\nflag = False\nnp.load('data.npy', allow_pickle=flag)",
        "import numpy as np\nnp.load('data.npy', allow_pickle=bool(0))",
        "import numpy\nnumpy.load('data.npy')",
        "from numpy import load as loader\nloader('data.npy', allow_pickle=True)",
        "import numpy as np\nloader = np.load\nloader('data.npy')",
        "import numpy as np\nloader = np.load\nloader = print\nloader('data.npy')",
        "import numpy as np\nnp.load('data.npy', None, False)",
        (
            "import numpy as np\n"
            "np.load('data.npy', allow_pickle=True)  # allow_pickle=False\n"
            "__import__('os')"
        ),
        "__import__('os')",
        "loader = __import__\nloader('os')",
        "import importlib\nimportlib.import_module('os')",
        "from importlib import import_module as load_module\nload_module('os')",
        "eval('1 + 1')",
        "exec('value = 1')",
        "import os\nos.system('true')",
        "import subprocess\nsubprocess.run(['true'])",
        "from pathlib import Path\nPath('data').read_bytes()",
        "import requests\nrequests.get('https://example.com')",
        "import urllib.request\nurllib.request.urlopen('https://example.com')",
        "import socket\nsocket.create_connection(('example.com', 80))",
        "os.system('true')",
        "subprocess.run(['true'])",
        "pathlib.Path('data')",
    ],
)
def test_generator_source_audit_rejects_unsafe_ast_constructs(source: str) -> None:
    assert _generator_source_violations(source)


@pytest.mark.parametrize(
    "source",
    [
        (
            "import numpy as np\nloader: object = np.load\n"
            "loader('data.npy', allow_pickle=True)"
        ),
        "import numpy as np\nloader: object = np.load\nloader('data.npy')",
        (
            "import numpy as np\nloader: object = np.load\nflag = False\n"
            "loader('data.npy', allow_pickle=flag)"
        ),
        "loader: object = __import__\nloader('os')",
        "__builtins__.__import__('os')",
        "__builtins__.exec('value = 1')",
        "__builtins__.eval('1 + 1')",
        "__builtins__.compile('1 + 1', '<test>', 'eval')",
        "__builtins__.open('data.txt')",
        "getattr(__builtins__, '__import__')('os')",
        "getattr(__builtins__, 'exec')('value = 1')",
        "getattr(__builtins__, 'eval')('1 + 1')",
        "getattr(__builtins__, 'compile')('1 + 1', '<test>', 'eval')",
        "getattr(__builtins__, 'open')('data.txt')",
        (
            "builtins_alias = __builtins__\ndanger = builtins_alias.open\n"
            "next_danger = danger\nnext_danger('data.txt')"
        ),
        (
            "builtins_alias: object = __builtins__\nresolve = getattr\n"
            "next_resolve = resolve\nnext_resolve(builtins_alias, 'eval')('1 + 1')"
        ),
    ],
)
def test_generator_source_audit_rejects_annassign_and_dynamic_builtins(
    source: str,
) -> None:
    assert _generator_source_violations(source)


@pytest.mark.parametrize(
    "source",
    [
        "import numpy as np\nnp.load('data.npy', allow_pickle=False)",
        "import numpy\nnumpy.load('data.npy', allow_pickle=False)",
        "from numpy import load as loader\nloader('data.npy', allow_pickle=False)",
        "import numpy as np\nloader = np.load\nloader('data.npy', allow_pickle=False)",
        "# requests subprocess pathlib socket allow_pickle=True\nvalue = 1",
        "message = 'requests urllib socket subprocess pathlib'",
        "socket_count = 0\nsubprocess_label = 'safe'",
        "def evaluate(value):\n    return value",
        "class Embedding:\n    pass",
        "import argparse\nparser = argparse.ArgumentParser()",
        "__builtins__.open_file('data.txt')",
        "getattr(__builtins__, 'open_file')('data.txt')",
        "builtins_alias = __builtins__\nnear = builtins_alias.evaluate\nnear('1 + 1')",
        "class Safe:\n    pass\nsafe = Safe()\nsafe.open('data.txt')",
    ],
)
def test_generator_source_audit_allows_safe_near_names(source: str) -> None:
    assert _generator_source_violations(source) == []


def test_generator_is_deterministic_cpu_only_and_uses_no_network(tmp_path: Path) -> None:
    script = UNIT / "scripts/generate_attention_data.py"
    source = script.read_text(encoding="utf-8")
    assert f"SEED = {SEED}" in source
    assert _generator_source_violations(source) == []

    first = tmp_path / "first.npz"
    second = tmp_path / "second.npz"
    subprocess.run([sys.executable, str(script), "--output", str(first)], check=True)
    subprocess.run([sys.executable, str(script), "--output", str(second)], check=True)
    assert first.read_bytes() == second.read_bytes()
    assert hashlib.sha256(first.read_bytes()).hexdigest() == (
        "2dc13bb31a8e4c85beb40e593416a490e72a6621186c9a316ba2dec1991caad4"
    )

    with __import__("numpy").load(first, allow_pickle=False) as generated:
        assert set(generated.files) == {"q", "k", "v", "one_hot"}
        expected = {
            "q": ((2, 3, 4), "float64", "ed407a452f54cf09037e6dd7f308a26d0e1d1e28a48f215dc08127c54062d998"),
            "k": ((2, 5, 4), "float64", "63ac5d7fd6cf6ed9a118ab2aee682328741a11169b734e65e1608c2f8e46d4d6"),
            "v": ((2, 5, 6), "float64", "331e1fec9a3e53aa8c15ccd6686162de0694c57118cd707d1c8f1250355d1cf8"),
            "one_hot": ((6, 4), "float64", "9543374b25a5ae224ee1ebc7168fab20504f36ef6fcc53bfbe051b6801b6cb64"),
        }
        np = __import__("numpy")
        for name, (shape, dtype, digest) in expected.items():
            value = generated[name]
            assert value.shape == shape
            assert value.dtype == np.dtype(dtype)
            assert np.isfinite(value).all()
            assert value.dtype.hasobject is False
            assert hashlib.sha256(value.tobytes()).hexdigest() == digest
        assert np.array_equal(
            generated["one_hot"],
            np.eye(4, dtype=np.float64)[[0, 1, 2, 1, 3, 0]],
        )
        np.testing.assert_allclose(
            generated["q"][[0, -1], [0, -1]],
            [[-1.13056437, -1.31580832, -0.02180598, 1.89559066],
             [2.41720520, -2.74744196, 0.40116980, 0.68780243]],
            atol=1e-8,
            rtol=0,
        )
        np.testing.assert_allclose(
            generated["k"][[0, -1], [0, -1]],
            [[0.77040645, -0.27747147, -1.86551073, 0.38635912],
             [-0.19901891, 0.26995594, -0.72964401, -0.29161591]],
            atol=1e-8,
            rtol=0,
        )
        np.testing.assert_allclose(
            generated["v"][[0, -1], [0, -1]],
            [[-0.02880813, 0.46364361, -0.56044496, 0.39903905, -0.84198820, 0.10226751],
             [-0.60630631, 0.31154392, -0.39778113, -0.66767981, 1.65415346, -0.23156534]],
            atol=1e-8,
            rtol=0,
        )

    spec = importlib.util.spec_from_file_location("b2_019_generator", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert set(module.arrays()) == {"q", "k", "v", "one_hot"}


def test_unit_standards_names_b2_019_in_double_length_roster() -> None:
    standards = (ROOT / "docs/unit-standards.md").read_text(encoding="utf-8")
    assert "B2-019-attention-transformers" in standards
    assert "F5, F6, C7, C11, C12, and B2-019" in standards


def _copy_registered_statement_repo(
    tmp_path: Path, *, include_solutions: bool = False
) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    shutil.copy2(ROOT / "books.yaml", repo / "books.yaml")
    (repo / "book1").mkdir()
    shutil.copy2(BOOK1_ROOT / "syllabus.md", repo / "book1/syllabus.md")
    shutil.copytree(BOOK2_ROOT, repo / "book2")
    if not include_solutions:
        for path in (repo / "book2").glob("units/*/practice/*_solution.ipynb"):
            path.unlink()
    return repo / "book2"


def _install_solution_placeholders(book2: Path, count: int) -> None:
    practice = book2 / "units" / UNIT_ID / "practice"
    for number in range(1, count + 1):
        shutil.copy2(
            practice / f"p{number:02}.ipynb",
            practice / f"p{number:02}_solution.ipynb",
        )


def test_required_solution_policy_cannot_be_evaded_by_deleting_all_solutions(tmp_path: Path) -> None:
    zero = _copy_registered_statement_repo(tmp_path / "zero")
    with pytest.raises(audit_curriculum.InventoryError, match="declared notebook is missing"):
        audit_curriculum.build_inventory(zero)
    assert any("missing solution path" in error for error in check_coverage(zero).errors)
    assert any(
        "cpu task requires a local solution path" in error
        for error in check_layer_boundary(zero).errors
    )

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


def test_deferred_solution_policy_emits_plan_linked_expiring_debt(tmp_path: Path) -> None:
    book2 = _copy_registered_statement_repo(tmp_path / "deferred")
    manifest_path = book2 / "units" / UNIT_ID / "manifest.yaml"
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    raw["solution_policy"] = {
        "status": "deferred",
        "plan": "plan-020",
        "expires": "2099-12-31",
    }
    manifest_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")

    expected = "solution debt deferred to plan-020 until 2099-12-31"
    coverage = check_coverage(book2)
    boundary = check_layer_boundary(book2)
    inventory = audit_curriculum.build_inventory(book2)

    assert coverage.ok and any(expected in warning for warning in coverage.warnings)
    assert boundary.ok and any(expected in warning for warning in boundary.warnings)
    assert any(expected in warning for warning in inventory["warnings"])
