from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import nbformat
import torch
import yaml

from tools.checks.hygiene import check_hygiene
from tools.checks.layer_boundary import check_layer_boundary
from tools.checks.tolerance import check_tolerance
from tools.model import load_unit_manifests

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"
UNIT_ID = "B2-024-gpu-scientific-ml-capstone"
UNIT = BOOK2_ROOT / "units" / UNIT_ID
SEED = 20261022
L4 = "optional-colab-l4"
PREREQ_UNITS = [
    "book1:F1-scientific-python",
    "book1:F3-matrices",
    "book1:F4-multivar-calculus",
    "book1:F5-probability",
    "book1:C1-ml-fundamentals",
    "book1:C2-linear-models",
    "book1:C3-gradient-descent",
    "book1:C5-neural-networks",
    "book1:C6-pytorch",
    "book1:C7-cnn-transfer",
    "book1:C10-competition-craft",
    "book1:C11-neural-training",
    "book1:C12-classical-models",
    "B2-023-generative-models-diffusion",
]
CONCEPT_PREREQS = [
    f"book1:{concept}"
    for concept in (
        "numpy-arrays", "broadcasting", "random-seeding", "matrix-multiplication",
        "invertibility-via-rank", "gradient", "sum-of-squares-gradients", "expectation",
        "variance", "variance-of-sums", "independence", "covariance", "gaussian-distribution",
        "sampling-simulation", "train-test-split", "overfitting", "accuracy-precision-recall",
        "class-imbalance", "linear-regression", "mse-loss", "l2-regularization",
        "gradient-descent", "learning-rate", "stochastic-gd", "relu-activation",
        "mlp-architecture", "torch-tensors", "nn-module", "requires-grad", "parameter-counting",
        "convolution", "cnn-training", "hidden-test-protocol", "metric-driven-iteration",
        "writeup-quality", "colab-coding-submission", "cpu-and-gpu-round-boundary", "softmax",
        "cross-entropy-loss", "torch-optimizers", "autograd-training", "trained-mlp", "k-means",
        "lloyd-algorithm",
    )
]
GPU = "gpu-colab-l4-workflow"
DESIGN = "open-ended-experiment-design"
EVAL = "open-ended-model-evaluation"
SSL = "semi-supervised-pseudo-labeling"
INV = "scientific-ml-inverse-problems"
MIX = "mixture-parameter-regression"
OWNED = [GPU, DESIGN, EVAL, SSL, INV, MIX]
CONCEPT_SESSIONS = {GPU: 1, DESIGN: 2, EVAL: 3, SSL: 4, INV: 5, MIX: 6}
LESSONS = [
    "lessons/00-book1-bridge.ipynb",
    "lessons/01-gpu-workflow-on-colab-l4.ipynb",
    "lessons/02-experiment-design-under-budget.ipynb",
    "lessons/03-evaluating-open-ended-models.ipynb",
    "lessons/04-semi-supervised-pseudo-labeling.ipynb",
    "lessons/05-scientific-inverse-problems.ipynb",
    "lessons/06-mixture-parameter-regression.ipynb",
]
STATEMENTS = [f"practice/p{number:02}.ipynb" for number in range(1, 29)]
SOLUTIONS = [f"practice/p{number:02}_solution.ipynb" for number in range(1, 29)]
NOTEBOOKS = ["lesson.ipynb", "review.ipynb", *LESSONS, *STATEMENTS, *SOLUTIONS]
EXPECTED_FILES = {
    "manifest.yaml",
    "data/capstone_data.py",
    "data/capstone_datasets.json",
    "scripts/generate_capstone_data.py",
    *NOTEBOOKS,
}
# (set, type, difficulty, minutes, concepts, after_session, policy) — Plan 029 ledger.
LEDGER = [
    ("A", "mc-normal-form", "intro", 20, [GPU], 1, "cpu"),
    ("A", "mc", "intro", 20, [GPU], 1, "cpu"),
    ("A", "mc", "intro", 20, [DESIGN], 2, "cpu"),
    ("A", "mc", "core", 20, [SSL], 4, "cpu"),
    ("A", "mc", "core", 20, [MIX], 6, "cpu"),
    ("B", "constrained-coding", "intro", 50, [GPU], 1, L4),
    ("B", "constrained-coding", "core", 50, [GPU], 1, L4),
    ("B", "constrained-coding", "core", 50, [EVAL], 3, "cpu"),
    ("B", "constrained-coding", "core", 50, [SSL], 4, "cpu"),
    ("B", "constrained-coding", "core", 50, [INV], 5, "cpu"),
    ("B", "constrained-coding", "core", 50, [MIX], 6, "cpu"),
    ("B", "constrained-coding", "advanced", 50, [DESIGN], 2, "cpu"),
    ("B", "proof", "core", 45, [INV], 5, "cpu"),
    ("B", "proof", "core", 45, [MIX], 6, "cpu"),
    ("B", "proof", "core", 45, [EVAL], 3, "cpu"),
    ("C", "integrative", "core", 65, [GPU], 2, L4),
    ("C", "integrative", "advanced", 65, [SSL], 4, L4),
    ("C", "integrative", "advanced", 65, [SSL], 4, "cpu"),
    ("C", "integrative", "advanced", 65, [INV], 5, L4),
    ("C", "integrative", "advanced", 65, [MIX], 6, L4),
    ("C", "integrative", "core", 65, [EVAL], 3, "cpu"),
    ("C", "integrative", "core", 65, [DESIGN], 3, "cpu"),
    ("C", "scenario", "core", 55, [GPU], 2, "cpu"),
    ("C", "scenario", "core", 55, [DESIGN, EVAL], 3, "cpu"),
    ("C", "scenario", "core", 55, [SSL], 4, "cpu"),
    ("C", "challenge", "advanced", 55, [INV], 6, "cpu"),
    ("C", "challenge", "advanced", 55, [MIX], 6, "cpu"),
    ("C", "challenge", "advanced", 55, [EVAL], 5, "cpu"),
]
DIRECT_PRACTICES = {
    GPU: {1, 2, 6, 7, 16, 23},
    DESIGN: {3, 12, 22, 24},
    EVAL: {8, 15, 21, 24, 28},
    SSL: {4, 9, 17, 18, 25},
    INV: {10, 13, 19, 26},
    MIX: {5, 11, 14, 20, 27},
}
ROW_MODALITIES = {
    GPU: ["implementation", "model-training", "competition-workflow"],
    DESIGN: ["model-training", "competition-workflow"],
    EVAL: ["model-training", "competition-workflow"],
    SSL: ["theory", "implementation", "model-training", "competition-workflow"],
    INV: ["theory", "implementation", "model-training", "competition-workflow"],
    MIX: ["theory", "implementation", "model-training", "competition-workflow"],
}
PRIMARY_PRACTICES = {
    GPU: {"implementation": [6, 7], "model-training": [16], "competition-workflow": [23]},
    DESIGN: {"model-training": [22, 12], "competition-workflow": [24]},
    EVAL: {"model-training": [21], "competition-workflow": [28, 24]},
    SSL: {"theory": [4], "implementation": [9], "model-training": [17, 18],
          "competition-workflow": [25]},
    INV: {"theory": [13], "implementation": [10], "model-training": [19],
          "competition-workflow": [26]},
    MIX: {"theory": [14, 5], "implementation": [11], "model-training": [20],
          "competition-workflow": [27]},
}
PINNED_FUNCTIONS = {
    "p06": ("get_device()", "move_batch(batch, device)",
            "train_step(model, batch, optimizer, device, amp_dtype)"),
    "p07": ("save_checkpoint(path, model, optimizer, step)",
            "load_checkpoint(path, model, optimizer)", "torch.equal"),
    "p08": ("bootstrap_ci(metric_fn, y_true, y_pred, n_boot, alpha, generator)",
            "paired_bootstrap_diff"),
    "p09": ("select_pseudo_labels(probs, threshold, max_per_class)",),
    "p10": ("forward_field(source_xy, strength, sensors_xy", "grid_operator(grid_xy, sensors_xy",
            "tikhonov_solve(A, y, lam)", "torch.linalg.solve"),
    "p11": ("mixture_function(x, weights, centers, widths)", "canonicalize(params)"),
    "p12": ("run_ablation(configs, train_fn, seeds",),
    "p26": ("StepBudget", "fit"),
    "p27": ("StepBudget", "fit"),
}
MODEL_BUILDING = ("p16", "p17", "p18", "p19", "p20", "p21", "p22", "p26", "p27")
SEAMS = {
    "p16": "forward", "p17": "forward", "p19": "forward", "p20": "forward",
    "p18": "features(x)", "p21": "fit(train_x, train_y)", "p22": "fit(train_x, train_y)",
    "p26": "fit", "p27": "fit",
}


def _manifest() -> dict:
    return yaml.safe_load((UNIT / "manifest.yaml").read_text(encoding="utf-8"))


def _notebook(relative: str) -> nbformat.NotebookNode:
    return nbformat.read(UNIT / relative, as_version=4)


def _source(relative: str, *, kind: str | None = None) -> str:
    return "\n".join(
        str(cell.source)
        for cell in _notebook(relative).cells
        if kind is None or cell.cell_type == kind
    )


def _policy(relative: str) -> str:
    match = re.fullmatch(r"practice/p(\d\d)(?:_solution)?\.ipynb", relative)
    return LEDGER[int(match.group(1)) - 1][6] if match else "cpu"


def test_exact_69_file_inventory_is_regular_nonsymlink_and_cache_free() -> None:
    actual = {
        path.relative_to(UNIT).as_posix()
        for path in UNIT.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    assert actual == EXPECTED_FILES
    assert len(actual) == 69
    assert not any(
        "__pycache__" in path.parts or path.suffix == ".pyc" for path in UNIT.rglob("*")
    )
    for relative in EXPECTED_FILES:
        path = UNIT / relative
        assert path.is_file() and not path.is_symlink()
        assert path.stat().st_nlink == 1


def test_manifest_publishes_exact_prerequisites_sessions_ledger_and_minutes() -> None:
    raw = _manifest()
    parsed = {item.unit_id: item for item in load_unit_manifests(BOOK2_ROOT)}[UNIT_ID]

    assert raw["book"] == 2 and raw["layer"] == "round-2-extension"
    assert raw["length"] == "double" and raw["solution_policy"] == "required"
    assert raw["prereq_units"] == PREREQ_UNITS
    assert raw["concept_prerequisites"] == CONCEPT_PREREQS == raw["concepts_used"]
    assert "book1:tensor-shape-tracing" not in raw["concept_prerequisites"]
    assert raw["concepts_taught"] == OWNED
    assert raw["concept_sessions"] == CONCEPT_SESSIONS
    assert raw["bridge_diagnostic"]["minutes"] == 30
    assert parsed.lesson_sessions == [90] * 6
    assert raw["estimated_minutes"] == {
        "lesson": 540,
        "lesson_sessions": [90] * 6,
        "practice": 1370,
        "review": 60,
    }

    rows = raw["practice"]
    assert len(rows) == 28
    for number, (row, expected) in enumerate(zip(rows, LEDGER, strict=True), 1):
        pset, ptype, difficulty, minutes, concepts, after_session, policy = expected
        assert row == {
            "id": f"B2-024-p{number:02}",
            "set": pset,
            "type": ptype,
            "difficulty": difficulty,
            "provenance": "original",
            "concepts": concepts,
            "path": f"practice/p{number:02}.ipynb",
            "solution_path": f"practice/p{number:02}_solution.ipynb",
            "minutes": minutes,
            "after_session": after_session,
            "compute": {"policy": policy, "seed": SEED},
        }
    assert sum(row["minutes"] for row in rows) == 1370
    assert [int(row["id"][-2:]) for row in rows if row["compute"]["policy"] == L4] == [
        6, 7, 16, 17, 19, 20,
    ]
    assert Counter(row["difficulty"] for row in rows) == {"intro": 4, "core": 16, "advanced": 8}
    assert Counter(row["type"] for row in rows) == {
        "mc": 4,
        "mc-normal-form": 1,
        "constrained-coding": 7,
        "proof": 3,
        "integrative": 7,
        "scenario": 3,
        "challenge": 3,
    }


def test_every_owned_concept_has_its_exact_direct_practices() -> None:
    rows = _manifest()["practice"]
    for concept, numbers in DIRECT_PRACTICES.items():
        tagged = {int(row["id"][-2:]) for row in rows if concept in row["concepts"]}
        assert tagged == numbers, concept
        assert len(tagged) >= 3


def test_all_notebooks_have_valid_unique_cell_ids_and_unexecuted_code() -> None:
    assert check_hygiene(BOOK2_ROOT).ok
    for relative in NOTEBOOKS:
        raw = json.loads((UNIT / relative).read_text(encoding="utf-8"))
        nbformat.validate(nbformat.from_dict(raw))
        ids = [cell.get("id") for cell in raw["cells"]]
        assert all(isinstance(cell_id, str) and cell_id for cell_id in ids), relative
        assert len(ids) == len(set(ids)), relative
        for cell in raw["cells"]:
            if cell["cell_type"] == "code":
                assert cell.get("execution_count") is None, relative
                assert cell.get("outputs") == [], relative


def test_headers_metadata_and_compute_policy_are_exact() -> None:
    for relative in NOTEBOOKS:
        notebook = _notebook(relative)
        policy = _policy(relative)
        assert notebook.metadata["usaaio"] == {
            "book": 2,
            "layer": "Round 2 extension",
            "unit": UNIT_ID,
            "surface": relative,
            "compute": {"policy": policy, "seed": SEED},
            "qualified_prerequisites": PREREQ_UNITS,
            "concept_prerequisites": CONCEPT_PREREQS,
        }, relative
        header = str(notebook.cells[0].source)
        assert "**Qualified prerequisites:** " in header
        assert "**Remediation links actually used:** " in header
        assert all(f"`{prereq}`" in header for prereq in PREREQ_UNITS)
        assert all(f"[{prereq}]" in header for prereq in PREREQ_UNITS)
        assert f"compute.policy: {policy}" in header and str(SEED) in header
        assert "tensor-shape-tracing" not in _source(relative)


def test_every_l4_statement_has_an_accelerator_extension_and_cpu_statements_do_not() -> None:
    for number, row in enumerate(LEDGER, 1):
        markdown = _source(f"practice/p{number:02}.ipynb", kind="markdown")
        has_heading = re.search(r"(?m)^## Accelerator extension\s*$", markdown) is not None
        assert has_heading is (row[6] == L4), number
        if has_heading:
            extension = markdown[markdown.index("## Accelerator extension") :]
            assert "config" in extension.lower()
    report = check_layer_boundary(BOOK2_ROOT)
    assert report.ok, report.errors


def test_six_sessions_have_sections_checkpoints_and_forward_pointer() -> None:
    for session, relative in enumerate(LESSONS[1:], 1):
        source = _source(relative)
        matches = list(re.finditer(r"(?m)^## (\d+)\. ([^\n]+)$", source))
        count = 10 if session == 1 else 9
        assert [int(match.group(1)) for match in matches] == list(range(1, count + 1)), relative
        titles = [match.group(2) for match in matches]
        assert sum("Worked laboratory" in title for title in titles) == 1
        assert titles[-2].startswith("Common pitfalls")
        assert titles[-1].startswith("Forward-only deeper topic")
        assert "not assessed" in source[matches[-1].start() :].lower()
        assert source.count("**Checkpoint") >= 2 * count
        assert source.count("**Collected answers.**") >= count
        meaningful_code = [
            cell
            for cell in _notebook(relative).cells
            if cell.cell_type == "code" and len(str(cell.source).strip().splitlines()) >= 5
        ]
        assert len(meaningful_code) >= 2


def test_session1_deeper_topic_is_markdown_only_and_gpu_code_is_guarded() -> None:
    notebook = _notebook(LESSONS[1])
    source = _source(LESSONS[1])
    code = _source(LESSONS[1], kind="code")
    start = source.index("## 10. Forward-only deeper topic")
    cells = notebook.cells
    tail_start = next(
        index for index, cell in enumerate(cells)
        if "## 10. Forward-only deeper topic" in str(cell.source)
    )
    assert all(cell.cell_type == "markdown" for cell in cells[tail_start:])
    assert "not assessed" in source[start:].lower()
    assert "torch.cuda.is_available()" in code
    assert "autocast" in code
    for forbidden in ("from_pretrained", "hf_hub", "huggingface", "diffusers", "torchvision"):
        assert forbidden not in code.lower()


def test_live_tolerance_check_passes() -> None:
    report = check_tolerance(BOOK2_ROOT)
    assert report.ok, report.errors


def test_p01_has_exact_five_choices_and_positive_reduced_normal_form() -> None:
    source = _source("practice/p01.ipynb")
    compact = source.replace(" ", "")
    assert re.findall(r"(?m)^([A-E])\. ", source) == list("ABCDE")
    assert "gcd(a,b)=1" in compact and "b>0" in compact and "a+b" in compact


def test_statements_are_solution_free_and_teaching_precedes_each_practice() -> None:
    manifest = _manifest()
    concept_session = manifest["concept_sessions"]
    for row in manifest["practice"]:
        relative = row["path"]
        source = _source(relative)
        code = _source(relative, kind="code")
        assert "## Your response" in source
        assert "### Answer check" not in source
        assert not re.search(r"(?im)^#{1,4}\s*(solution|answer)\b", source)
        assert not re.search(
            r"(?i)\b(correct answer|correct choice|selected answer)\s*(is|:|=)", source
        )
        assert row["after_session"] >= max(concept_session[c] for c in row["concepts"])
        tree = ast.parse(code or "pass", filename=relative)
        assert not any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Assert))
            for node in ast.walk(tree)
        ), relative


def test_coding_and_model_building_statements_pin_functions_protocol_and_seams() -> None:
    for problem_id, tokens in PINNED_FUNCTIONS.items():
        source = _source(f"practice/{problem_id}.ipynb")
        assert all(token in source for token in tokens), (problem_id, tokens)
    for problem_id in MODEL_BUILDING:
        source = _source(f"practice/{problem_id}.ipynb")
        assert "final_test_score" in source, problem_id
        assert "train_rows" in source and "val_rows" in source, problem_id
        assert SEAMS[problem_id] in source, problem_id
    for problem_id in ("p17", "p18", "p19", "p20", "p26", "p27"):
        assert "baseline_score" in _source(f"practice/{problem_id}.ipynb"), problem_id
    for problem_id in ("p26", "p27"):
        source = _source(f"practice/{problem_id}.ipynb")
        for part in ("Approach", "Alternatives considered", "Evaluation", "Limitations"):
            assert part in source, (problem_id, part)


def test_generator_and_loader_are_self_contained_and_prohibit_external_data() -> None:
    allowed_roots = {
        "__future__", "argparse", "hashlib", "importlib", "itertools", "json", "pathlib",
        "sys", "time", "types", "collections", "numpy", "torch",
    }
    for relative in ("data/capstone_data.py", "scripts/generate_capstone_data.py"):
        source = (UNIT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        assert roots <= allowed_roots, (relative, roots - allowed_roots)
        lowered = source.lower()
        assert all(
            forbidden not in lowered
            for forbidden in ("torchvision", "http://", "https://", "requests", "urlopen")
        )
        assert "torch.save" not in source and "load_state_dict(torch.load" not in source
    payload = json.loads((UNIT / "data/capstone_datasets.json").read_text(encoding="utf-8"))
    assert payload["seed"] == SEED
    assert set(payload) == {"constants", "datasets", "format_version", "results_tables", "seed"}
    assert set(payload["datasets"]) == {"shapes_supervised", "shapes_ssl", "inverse", "mixture"}
    for entry in payload["datasets"].values():
        assert set(entry) == {"digest", "inputs", "splits", "targets"}


def test_generator_check_regenerates_rows_splits_and_hashes() -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, str(UNIT / "scripts/generate_capstone_data.py"), "--check"],
        cwd=UNIT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "check ok" in result.stdout


def test_loader_exposes_immutable_splits_locked_test_and_hidden_pool_labels() -> None:
    path = UNIT / "data/capstone_data.py"
    spec = importlib.util.spec_from_file_location("b2_024_capstone_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.SEED == SEED
    assert module.TASKS == ("shapes_supervised", "shapes_ssl", "inverse", "mixture")
    sizes = {
        "shapes_supervised": (600, 150, 150),
        "shapes_ssl": (30, 30, 300),
        "inverse": (800, 200, 200),
        "mixture": (800, 200, 200),
    }
    for task, expected in sizes.items():
        train, val, test = module.TRAIN_IDS[task], module.VAL_IDS[task], module.TEST_IDS[task]
        assert all(isinstance(ids, tuple) for ids in (train, val, test))
        assert (len(train), len(val), len(test)) == expected
        assert not (set(train) & set(val) or set(train) & set(test) or set(val) & set(test))
        x, _ = module.train_rows(task)
        assert {module.split_of(task, row) for row in x} == {"train"}
        xv, _ = module.val_rows(task)
        assert {module.split_of(task, row) for row in xv} == {"val"}
    assert len(module.UNLABELLED_IDS["shapes_ssl"]) == 600
    pool = module.unlabelled_rows()
    assert tuple(pool.shape) == (600, 1, 8, 8)
    assert {module.split_of("shapes_ssl", row) for row in pool} == {"unlabelled"}
    for name in ("unlabelled_labels", "test_rows", "pool_labels"):
        assert not hasattr(module, name)
    try:
        module.TRAIN_IDS["inverse"] = ()
    except TypeError:
        pass
    else:  # pragma: no cover - immutability regression
        raise AssertionError("TRAIN_IDS must be read-only")
    budget = module.StepBudget(2)
    weight = torch.zeros(1, requires_grad=True)
    optimizer = budget.wrap(torch.optim.SGD([weight], lr=0.1))
    for _ in range(2):
        weight.sum().backward()
        optimizer.step()
    try:
        optimizer.step()
    except module.StepBudgetExceeded:
        pass
    else:  # pragma: no cover - budget regression
        raise AssertionError("StepBudget must refuse a third step")
    assert module.test_call_count("inverse") == 0
    score = module.final_test_score(
        lambda x: torch.full((x.shape[0], 3), 0.5), task="inverse"
    )
    assert module.test_call_count("inverse") == 1
    assert score.ci_low <= score.score <= score.ci_high and score.n_examples == 200


def test_coverage_claims_point_to_real_primary_evidence() -> None:
    raw = _manifest()
    practices = {row["id"]: row for row in raw["practice"]}
    claims = raw["coverage_claims"]
    assert [claim["knowledge_point"] for claim in claims] == OWNED
    observed: set[tuple[str, str]] = set()
    for claim in claims:
        concept = claim["knowledge_point"]
        assert claim["modalities"] == ROW_MODALITIES[concept]
        assert claim["first_session"] == raw["concept_sessions"][concept]
        for modality, evidence in claim["evidence_by_modality"].items():
            observed.add((concept, modality))
            assert [item["id"] for item in evidence["practices"]] == [
                f"B2-024-p{n:02}" for n in PRIMARY_PRACTICES[concept][modality]
            ]
            for anchor in evidence["lesson_anchors"]:
                prefix = f"units/{UNIT_ID}/"
                assert anchor["role"] == "primary" and anchor["path"].startswith(prefix)
                relative = anchor["path"][len(prefix) :]
                title, heading = anchor["heading"].split(" > ", 1)
                text = _source(relative)
                assert f"# {title}" in text and f"## {heading}" in text
            for practice in evidence["practices"]:
                assert practice["role"] == "primary"
                assert concept in practices[practice["id"]]["concepts"]
    assert len(observed) == sum(len(value) for value in ROW_MODALITIES.values()) == 19


def test_solution_notebooks_are_complete_answer_checked_and_output_free() -> None:
    assert sorted(path.name for path in (UNIT / "practice").glob("p*_solution.ipynb")) == [
        f"p{number:02}_solution.ipynb" for number in range(1, 29)
    ]
    for relative in SOLUTIONS:
        notebook = _notebook(relative)
        markdown_indices = [
            index for index, cell in enumerate(notebook.cells) if cell.cell_type == "markdown"
        ]
        answer_index = markdown_indices[-1]
        assert str(notebook.cells[answer_index].source).strip() == "### Answer check"
        assert answer_index + 1 < len(notebook.cells)
        assert all(cell.cell_type == "code" for cell in notebook.cells[answer_index + 1 :])
        assert all(str(cell.source).strip() for cell in notebook.cells[answer_index + 1 :])


def test_ci_bounds_b2_024_solutions_at_twenty_seconds() -> None:
    script = (ROOT / "scripts/ci-local.sh").read_text(encoding="utf-8")
    assert (
        "|| $relative == units/B2-023-generative-models-diffusion/practice/p??_solution.ipynb "
        "|| $relative == units/B2-024-gpu-scientific-ml-capstone/practice/p??_solution.ipynb ]]"
        in script
    )
    assert 'timeout 20s uv run --project .. jupyter execute "$relative"' in script
