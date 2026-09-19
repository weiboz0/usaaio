from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import nbformat
import pytest
import yaml

from tools.checks.hygiene import check_hygiene
from tools.checks.tolerance import check_tolerance
from tools.model import load_unit_manifests

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"
UNIT_ID = "B2-021-cross-modal-transformers-vision"
UNIT = BOOK2_ROOT / "units" / UNIT_ID
SEED = 20260901
PREREQ_UNITS = [
    "book1:F1-scientific-python",
    "book1:F3-matrices",
    "book1:C6-pytorch",
    "book1:C7-cnn-transfer",
    "book1:C11-neural-training",
    "B2-019-attention-transformers",
    "B2-020-language-transformers",
]
CONCEPT_PREREQS = [
    "attention-mask",
    "query-key-value-attention",
    "multi-head-attention",
    "attention-complexity",
    "transformer-block",
    "book1:numpy-arrays",
    "book1:broadcasting",
    "book1:aggregation-axis",
    "book1:random-seeding",
    "book1:matrix-multiplication",
    "book1:torch-tensors",
    "book1:nn-module",
    "book1:requires-grad",
    "book1:tensor-shape-tracing",
    "book1:softmax",
    "book1:cross-entropy-loss",
    "book1:torch-optimizers",
    "book1:autograd-training",
    "book1:convolution",
    "book1:feature-maps",
    "book1:cnn-training",
]
OWNED = [
    "vision-transformers",
    "object-detection",
    "unet",
    "graph-neural-network-transformer-applications",
]
LESSONS = [
    "lessons/00-book1-bridge.ipynb",
    "lessons/01-image-patches-and-vision-transformers.ipynb",
    "lessons/02-detection-grids-and-set-prediction.ipynb",
    "lessons/03-unet-segmentation-and-skip-connections.ipynb",
    "lessons/04-graphs-cross-modal-attention.ipynb",
    "lessons/05-vision-system-design-and-audit.ipynb",
]
STATEMENTS = [f"practice/p{number:02}.ipynb" for number in range(1, 25)]
SOLUTIONS = [f"practice/p{number:02}_solution.ipynb" for number in range(1, 25)]
NOTEBOOKS = ["lesson.ipynb", "review.ipynb", *LESSONS, *STATEMENTS, *SOLUTIONS]
EXPECTED_FILES = {
    "manifest.yaml",
    "data/vision_fixture.py",
    "scripts/generate_vision_data.py",
    *NOTEBOOKS,
}
LEDGER = [
    ("A", "mc-normal-form", "intro", 20, "vision-transformers", 1),
    ("A", "mc", "intro", 20, "vision-transformers", 1),
    ("A", "mc", "core", 20, "vision-transformers", 1),
    ("A", "mc", "intro", 20, "object-detection", 2),
    ("A", "mc", "intro", 20, "unet", 3),
    ("B", "constrained-coding", "intro", 50, "vision-transformers", 1),
    ("B", "constrained-coding", "core", 50, "vision-transformers", 1),
    ("B", "constrained-coding", "intro", 50, "object-detection", 2),
    ("B", "constrained-coding", "advanced", 50, "object-detection", 2),
    ("B", "constrained-coding", "core", 50, "unet", 3),
    ("B", "constrained-coding", "intro", 50, "unet", 3),
    ("B", "constrained-coding", "core", 50, "graph-neural-network-transformer-applications", 4),
    ("B", "proof", "core", 45, "vision-transformers", 1),
    ("B", "proof", "core", 45, "object-detection", 2),
    ("B", "proof", "core", 45, "unet", 3),
    ("B", "proof", "core", 45, "graph-neural-network-transformer-applications", 4),
    ("C", "integrative", "advanced", 65, "vision-transformers", 1),
    ("C", "integrative", "advanced", 65, "object-detection", 2),
    ("C", "integrative", "advanced", 65, "unet", 3),
    ("C", "integrative", "core", 65, "graph-neural-network-transformer-applications", 4),
    ("C", "scenario", "core", 55, "vision-transformers", 5),
    ("C", "scenario", "core", 55, "object-detection", 5),
    ("C", "challenge", "advanced", 55, "unet", 5),
    ("C", "challenge", "advanced", 55, "graph-neural-network-transformer-applications", 5),
]
PRACTICE_LITERAL_TOKENS = {
    "p06": ("images = torch.tensor", "patch_side = 2", "[26,27,30,31]", "middle-token swap"),
    "p07": ("projection = nn.Linear(4, 8, bias=True)", "cls_token = nn.Parameter", "positions.copy_", "Expected full output"),
    "p08": ("target_box = torch.tensor([2.,1.,8.,5.]", "image_width = 12", "grid_size = 4", "[2/3,1/2,1/2,1/2]"),
    "p09": ("scores = torch.tensor([.90, .80, .85, .20]", "labels = torch.tensor([0, 0, 1, 0]", "keeps original indices `[0,2]`"),
    "p10": ("bottleneck = torch.arange", "skip = torch.arange", "nn.ConvTranspose2d(8, 4, 2, 2", "concatenation channels 4–7 equal `skip`"),
    "p11": ("logits `(1,2,2,2)`", "target `(1,2,2)`", "valid `(1,2,2)`", "scalar CE `0.16292568`", "Dice `1.0`"),
    "p12": ("adjacency = torch.tensor", "dtype=torch.uint8", "Expected full directed aggregate", "receiver rather than sender axis"),
    "p17": ("build_train_batch(ids)", "build_heldout_batch(ids)", "compute_loss(model, features, targets)", "train_vit_classifier(model,batch,optimizer)", "actual feature fingerprint and aligned target fingerprint"),
    "p18": ("build_train_batch(ids)", "build_heldout_batch(ids)", "train_grid_detector(model,batch,optimizer)", "exact immutable stored-order split", "actual feature and aligned-target fingerprints"),
    "p19": ("build_train_batch(ids)", "build_heldout_batch(ids)", "train_unet_segmenter(model,batch,optimizer)", "fuse with no ReLU", "A ReLU after fuse is expressly prohibited"),
    "p20": ("build_train_batch(ids)", "build_heldout_batch(ids)", "train_graph_token_classifier(model,batch,optimizer)", "directed adjacency", "transposing adjacency"),
    "p23": ("segmentation-train-00", "segmentation-train-03", "segmentation-heldout-00"),
    "p24": ("audit_cross_modal_sources(trace) -> dict", "invalid-padded-edge", "heldout-optimizer-id", "reversed-qkv"),
}


def _manifest() -> dict:
    return yaml.safe_load((UNIT / "manifest.yaml").read_text(encoding="utf-8"))


def _notebook(relative: str) -> nbformat.NotebookNode:
    return nbformat.read(UNIT / relative, as_version=4)


def _source(relative: str, *, kind: str | None = None) -> str:
    notebook = _notebook(relative)
    return "\n".join(
        str(cell.source)
        for cell in notebook.cells
        if kind is None or cell.cell_type == kind
    )


def _fixture_module():
    path = UNIT / "data/vision_fixture.py"
    spec = importlib.util.spec_from_file_location("b2_021_vision_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_exact_59_file_inventory_is_regular_nonsymlink_and_cache_free() -> None:
    actual = {
        path.relative_to(UNIT).as_posix()
        for path in UNIT.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    assert actual == EXPECTED_FILES
    assert len(actual) == 59
    assert not any("__pycache__" in path.parts or path.suffix == ".pyc" for path in UNIT.rglob("*"))
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
    assert raw["concepts_taught"] == OWNED
    assert raw["concept_sessions"] == dict(zip(OWNED, (1, 2, 3, 4), strict=True))
    assert parsed.lesson_sessions == [90] * 5
    assert raw["estimated_minutes"] == {
        "lesson": 450,
        "lesson_sessions": [90] * 5,
        "practice": 1110,
        "review": 60,
    }

    rows = raw["practice"]
    assert len(rows) == 24
    for number, (row, expected) in enumerate(zip(rows, LEDGER, strict=True), 1):
        pset, ptype, difficulty, minutes, concept, after_session = expected
        assert row == {
            "id": f"B2-021-p{number:02}",
            "set": pset,
            "type": ptype,
            "difficulty": difficulty,
            "provenance": "original",
            "concepts": [concept],
            "path": f"practice/p{number:02}.ipynb",
            "solution_path": f"practice/p{number:02}_solution.ipynb",
            "minutes": minutes,
            "after_session": after_session,
            "compute": {"policy": "cpu", "seed": SEED},
        }
    assert sum(row["minutes"] for row in rows) == 1110
    assert Counter(row["type"] for row in rows) == {
        "mc": 4,
        "mc-normal-form": 1,
        "constrained-coding": 7,
        "proof": 4,
        "integrative": 4,
        "scenario": 2,
        "challenge": 2,
    }


def test_all_notebooks_have_valid_unique_cell_ids_and_unexecuted_code() -> None:
    assert check_hygiene(BOOK2_ROOT).ok
    solution_ids: set[str] = set()
    for relative in NOTEBOOKS:
        path = UNIT / relative
        raw = json.loads(path.read_text(encoding="utf-8"))
        nbformat.validate(nbformat.from_dict(raw))
        ids = [cell.get("id") for cell in raw["cells"]]
        assert all(isinstance(cell_id, str) and cell_id for cell_id in ids), relative
        assert len(ids) == len(set(ids)), relative
        if relative in SOLUTIONS:
            assert not solution_ids.intersection(ids), relative
            solution_ids.update(ids)
        for cell in raw["cells"]:
            if cell["cell_type"] == "code":
                assert cell.get("execution_count") is None, relative
                assert cell.get("outputs") == [], relative


def test_student_headers_metadata_and_remediation_contract_are_exact() -> None:
    for relative in ["lesson.ipynb", "review.ipynb", *LESSONS, *STATEMENTS]:
        notebook = _notebook(relative)
        metadata = notebook.metadata["usaaio"]
        source = _source(relative)
        assert metadata == {
            "book": 2,
            "layer": "Round 2 extension",
            "unit": UNIT_ID,
            "surface": relative,
            "compute": {"policy": "cpu", "seed": SEED},
            "qualified_prerequisites": PREREQ_UNITS,
            "concept_prerequisites": CONCEPT_PREREQS,
        }
        assert "**Qualified prerequisites:** " in source
        assert "**Remediation links actually used:** " in source
        header = str(notebook.cells[0].source)
        assert all(f"`{prereq}`" in header for prereq in PREREQ_UNITS)
        assert all(f"[{prereq}]" in header for prereq in PREREQ_UNITS)
        assert "compute.policy: cpu" in header and str(SEED) in header


def test_five_sessions_have_exact_nine_section_lab_checkpoint_structure() -> None:
    for relative in LESSONS[1:]:
        source = _source(relative)
        matches = list(re.finditer(r"(?m)^## (\d+)\. ([^\n]+)$", source))
        assert [int(match.group(1)) for match in matches] == list(range(1, 10)), relative
        titles = [match.group(2) for match in matches]
        assert sum("Worked laboratory" in title for title in titles) == 1
        assert titles[7].startswith("Common pitfalls")
        assert titles[8].startswith("Forward-only deeper topic")
        assert "not assessed" in source[matches[-1].start() :].lower()
        assert source.count("**Checkpoint") >= 18
        assert source.count("**Collected answers.**") >= 9
        body_words = re.findall(r"\b[A-Za-z0-9][A-Za-z0-9_'-]*\b", source.split("## 1.", 1)[1])
        assert len(body_words) >= 1400
        meaningful_code = [
            cell
            for cell in _notebook(relative).cells
            if cell.cell_type == "code" and len(str(cell.source).strip().splitlines()) >= 5
        ]
        assert len(meaningful_code) >= 2


def test_live_tolerance_check_passes_and_rejects_an_omitted_lesson_tolerance(
    tmp_path: Path,
) -> None:
    live = check_tolerance(BOOK2_ROOT)
    assert live.ok, live.errors

    selected = tmp_path / "book2"
    shutil.copytree(UNIT, selected / "units" / UNIT_ID)
    lesson = selected / "units" / UNIT_ID / LESSONS[2]
    notebook = json.loads(lesson.read_text(encoding="utf-8"))
    changed = False
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code" or "atol=1e-6, rtol=1e-6" not in cell["source"]:
            continue
        cell["source"] = cell["source"].replace(
            ", atol=1e-6, rtol=1e-6", "", 1
        )
        changed = True
        break
    assert changed
    lesson.write_text(json.dumps(notebook), encoding="utf-8")

    report = check_tolerance(selected)
    assert not report.ok
    assert any(
        "torch.allclose must explicitly state atol and rtol" in error
        for error in report.errors
    )


def test_p01_has_exact_five_choices_and_positive_reduced_normal_form() -> None:
    source = _source("practice/p01.ipynb")
    compact = source.replace(" ", "")
    assert re.findall(r"(?m)^([A-E])\. ", source) == list("ABCDE")
    assert "gcd(a,b)=1" in compact and "b>0" in compact and "a+b" in compact
    assert "C. 13" in source


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
        assert not re.search(r"(?i)\b(correct answer|correct choice|selected answer)\s*(is|:|=)", source)
        assert row["after_session"] >= max(concept_session[concept] for concept in row["concepts"])
        tree = ast.parse(code or "pass", filename=relative)
        assert not any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Return, ast.Assert))
            for node in ast.walk(tree)
        )


def test_coding_training_and_audit_statements_pin_discriminating_literals() -> None:
    for problem_id, tokens in PRACTICE_LITERAL_TOKENS.items():
        source = _source(f"practice/{problem_id}.ipynb")
        assert all(token in source for token in tokens), problem_id
    for problem_id in ("p17", "p18", "p19", "p20"):
        source = _source(f"practice/{problem_id}.ipynb")
        assert "betas=(.9,.999)" in source
        assert "eps=1e-8" in source and "weight_decay=0" in source
    assert "lr=.05" in _source("practice/p17.ipynb")
    assert "exactly 12 full-batch mean-CE updates" in _source("practice/p17.ipynb")
    assert "lr=.05" in _source("practice/p18.ipynb")
    assert "exactly 16 stored-order full-batch updates" in _source("practice/p18.ipynb")
    assert "lr=.03" in _source("practice/p19.ipynb")
    assert "exactly 16 stored-order full-batch mean pixel-CE updates" in _source("practice/p19.ipynb")
    assert "lr=.05" in _source("practice/p20.ipynb")
    assert "exactly 12 stored-order full-batch mean-CE updates" in _source("practice/p20.ipynb")


def test_fixture_and_generator_are_self_contained_and_prohibit_external_data() -> None:
    allowed_roots = {
        "__future__", "argparse", "dataclasses", "hashlib", "importlib", "json",
        "os", "pathlib", "struct", "sys", "types", "typing", "numpy", "torch",
    }
    for relative in ("data/vision_fixture.py", "scripts/generate_vision_data.py"):
        source = (UNIT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        assert roots <= allowed_roots
        lowered = source.lower()
        assert all(
            forbidden not in lowered
            for forbidden in ("torchvision", "http://", "https://", "requests", "urlopen", "student data")
        )


def test_all_twelve_coverage_modalities_point_to_real_primary_evidence() -> None:
    raw = _manifest()
    practices = {row["id"]: row for row in raw["practice"]}
    claims = raw["coverage_claims"]
    assert [claim["knowledge_point"] for claim in claims] == OWNED
    observed: set[tuple[str, str]] = set()
    for claim in claims:
        concept = claim["knowledge_point"]
        assert claim["modalities"] == ["theory", "implementation", "model-training"]
        assert claim["first_session"] == raw["concept_sessions"][concept]
        for modality, evidence in claim["evidence_by_modality"].items():
            observed.add((concept, modality))
            assert evidence["lesson_anchors"] and evidence["practices"]
            for anchor in evidence["lesson_anchors"]:
                prefix = f"units/{UNIT_ID}/"
                assert anchor["role"] == "primary" and anchor["path"].startswith(prefix)
                relative = anchor["path"][len(prefix) :]
                assert (UNIT / relative).is_file()
                title, heading = anchor["heading"].split(" > ", 1)
                text = _source(relative)
                assert f"# {title}" in text and f"## {heading}" in text
            for practice in evidence["practices"]:
                assert practice["role"] == "primary"
                assert concept in practices[practice["id"]]["concepts"]
    assert len(observed) == 12


def test_literal_fixture_hashes_splits_fingerprints_and_target_guards() -> None:
    fixture = _fixture_module()
    assert fixture.SEED == SEED
    assert fixture.validate_catalog() and fixture.validate_literal_hashes()
    assert len(fixture.FEATURE_FINGERPRINT_TO_ID) == len(fixture.RECORDS)
    assert set(fixture.EXAMPLE_ID_TO_TARGET_FINGERPRINT) == set(fixture.RECORDS)
    assert len(set(fixture.EXAMPLE_ID_TO_TARGET_FINGERPRINT.values())) < len(fixture.RECORDS)
    assert set(fixture.TRAIN_IDS).isdisjoint(fixture.HELDOUT_IDS)
    assert set(fixture.exercise_validation_guards()) == {
        "duplicate-feature",
        "unknown-id",
        "target-mismatch",
        "split-overlap",
        "batch-duplicate",
        "batch-reordered",
        "batch-partial",
        "batch-unknown",
        "batch-wrong-split",
        "actual-target-mismatch",
    }
    with pytest.raises(TypeError):
        fixture.FEATURE_FINGERPRINT_TO_ID["0" * 64] = "forbidden"
    with pytest.raises(KeyError):
        fixture.resolve_example_id("0" * 64)

    for task in ("vit", "detection", "segmentation", "graph"):
        train_features, train_targets = fixture.build_train_batch(task)
        held_features, held_targets = fixture.build_heldout_batch(task)
        assert next(iter(train_features.values())).shape[0] == 4
        assert next(iter(held_features.values())).shape[0] == 2
        assert fixture.validate_actual_batch(task, train_features, train_targets) == (
            "train",
            fixture.TASK_SPLITS[task]["train"],
        )
        assert fixture.validate_actual_batch(task, held_features, held_targets) == (
            "heldout",
            fixture.TASK_SPLITS[task]["heldout"],
        )
        train_ids = fixture.TASK_SPLITS[task]["train"]
        for invalid in (
            (train_ids[0], train_ids[0], *train_ids[2:]),
            tuple(reversed(train_ids)),
            train_ids[:-1],
            (*train_ids[:-1], "unknown-id"),
            fixture.TASK_SPLITS[task]["heldout"] * 2,
        ):
            with pytest.raises((KeyError, ValueError)):
                fixture.build_task_batch(task, invalid)

    for example_id in fixture.RECORDS:
        built = fixture.build_example(example_id)
        fingerprint = fixture.canonical_array_fingerprint(tuple(built["features"].items()))
        assert fixture.resolve_example_id(fingerprint) == example_id
        if "image" in built["features"]:
            assert max(built["features"]["image"].shape[-2:]) <= 8


def test_generator_reconstructs_literal_and_initial_state_contracts() -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, str(UNIT / "scripts/generate_vision_data.py"), "--check"],
        cwd=UNIT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
    assert "literal canonical hashes" in result.stdout
    assert "complete default-initialized model hashes (41 tensors" in result.stdout
    assert "p17-p20 construction order, parameter names, shapes, dtypes, and bytes" in result.stdout
    assert "p17-p20 transient forward paths and output shapes" in result.stdout
    source = (UNIT / "scripts/generate_vision_data.py").read_text(encoding="utf-8")
    assert "trained_weights" not in source and "final_metrics" not in source
    assert all(token in source for token in (
        "positioned = tokens + self.positions",
        "encoded = self.norm(positioned + attended)",
        "fused = self.fuse(concat)",
        "return self.head(fused), concat",
        "torch.bmm(adjacency.float(), node_features)",
    ))
    assert "relu(self.fuse" not in source.lower()


def test_solution_notebooks_are_complete_answer_checked_and_output_free() -> None:
    assert sorted(path.name for path in (UNIT / "practice").glob("p*_solution.ipynb")) == [
        f"p{number:02}_solution.ipynb" for number in range(1, 25)
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
        assert "_solution.ipynb" not in json.dumps(notebook)


@pytest.mark.parametrize("number", range(17, 21))
def test_training_solutions_execute_via_authoritative_jupyter_route_without_inplace(
    number: int,
) -> None:
    relative = f"units/{UNIT_ID}/practice/p{number:02}_solution.ipynb"
    path = BOOK2_ROOT / relative
    before = path.read_bytes()
    proc = subprocess.run(
        ["timeout", "20s", "../.venv/bin/jupyter", "execute", relative],
        cwd=BOOK2_ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert path.read_bytes() == before


def test_ci_timeout_path_match_propagates_timeout_exit(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    timeout_log = tmp_path / "timeout.log"
    timeout = fake_bin / "timeout"
    timeout.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$TIMEOUT_LOG"\nexit 124\n',
        encoding="utf-8",
    )
    timeout.chmod(0o755)
    uv_log = tmp_path / "uv.log"
    uv = fake_bin / "uv"
    uv.write_text(
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$UV_LOG"\nexit 0\n',
        encoding="utf-8",
    )
    uv.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "TIMEOUT_LOG": str(timeout_log),
        "UV_LOG": str(uv_log),
    }
    relative = f"units/{UNIT_ID}/practice/p17_solution.ipynb"
    proc = subprocess.run(
        ["bash", str(ROOT / "scripts/ci-local.sh"), "--solution-probe", str(BOOK2_ROOT), relative],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 124, proc.stdout + proc.stderr
    assert timeout_log.read_text(encoding="utf-8").splitlines() == [
        f"20s uv run --project .. jupyter execute {relative}"
    ]

    ordinary = "units/F1-scientific-python/practice/p17_solution.ipynb"
    proc = subprocess.run(
        ["bash", str(ROOT / "scripts/ci-local.sh"), "--solution-probe", str(BOOK2_ROOT), ordinary],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert timeout_log.read_text(encoding="utf-8").splitlines() == [
        f"20s uv run --project .. jupyter execute {relative}"
    ]
    assert uv_log.read_text(encoding="utf-8").splitlines() == [
        f"run --project .. jupyter execute {ordinary}"
    ]
