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
import yaml

from tools.checks.hygiene import check_hygiene
from tools.checks.tolerance import check_tolerance
from tools.model import load_unit_manifests

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"
UNIT_ID = "B2-022-probabilistic-latent-models"
UNIT = BOOK2_ROOT / "units" / UNIT_ID
SEED = 20260927
PREREQ_UNITS = [
    "book1:F1-scientific-python",
    "book1:F3-matrices",
    "book1:F4-multivar-calculus",
    "book1:F5-probability",
    "book1:F6-svd-spectral",
    "book1:C1-ml-fundamentals",
    "book1:C2-linear-models",
    "book1:C5-neural-networks",
    "book1:C6-pytorch",
    "book1:C9-dimensionality-reduction",
    "book1:C11-neural-training",
    "B2-021-cross-modal-transformers-vision",
]
CONCEPT_PREREQS = [
    f"book1:{concept}"
    for concept in (
        "numpy-arrays", "broadcasting", "aggregation-axis", "random-seeding",
        "matrix-multiplication", "gradient", "expectation", "variance", "covariance",
        "gaussian-distribution", "sampling-simulation", "conditional-probability",
        "bayes-rule", "eigenvalues-eigenvectors", "spectral-decomposition", "svd",
        "train-test-split", "mse-loss", "relu-activation", "mlp-architecture",
        "torch-tensors", "nn-module", "requires-grad", "torch-optimizers",
        "autograd-training", "pca",
    )
]
MVG = "multivariate-gaussian"
KL = "kl-divergence"
AE = "autoencoder"
RP = "gaussian-reparameterization"
VAE = "variational-autoencoder"
OWNED = [MVG, KL, AE, RP, VAE]
CONCEPT_SESSIONS = {MVG: 1, KL: 2, AE: 3, RP: 4, VAE: 4}
LESSONS = [
    "lessons/00-book1-bridge.ipynb",
    "lessons/01-multivariate-gaussians.ipynb",
    "lessons/02-kl-divergence.ipynb",
    "lessons/03-autoencoders.ipynb",
    "lessons/04-reparameterization-and-the-elbo.ipynb",
    "lessons/05-training-and-using-vaes.ipynb",
]
STATEMENTS = [f"practice/p{number:02}.ipynb" for number in range(1, 25)]
SOLUTIONS = [f"practice/p{number:02}_solution.ipynb" for number in range(1, 25)]
NOTEBOOKS = ["lesson.ipynb", "review.ipynb", *LESSONS, *STATEMENTS, *SOLUTIONS]
EXPECTED_FILES = {
    "manifest.yaml",
    "data/latent_data.py",
    "data/latent_datasets.json",
    "scripts/generate_latent_data.py",
    *NOTEBOOKS,
}
# (set, type, difficulty, minutes, concepts, after_session) — Plan 027 ledger and schedule.
LEDGER = [
    ("A", "mc-normal-form", "intro", 20, [MVG], 1),
    ("A", "mc", "intro", 20, [MVG], 1),
    ("A", "mc", "intro", 20, [KL], 2),
    ("A", "mc", "intro", 20, [AE], 3),
    ("A", "mc", "core", 20, [RP], 4),
    ("B", "constrained-coding", "intro", 50, [MVG], 1),
    ("B", "constrained-coding", "core", 50, [MVG], 2),
    ("B", "constrained-coding", "intro", 50, [KL], 2),
    ("B", "constrained-coding", "core", 50, [KL], 3),
    ("B", "constrained-coding", "intro", 50, [AE], 3),
    ("B", "constrained-coding", "core", 50, [RP], 4),
    ("B", "constrained-coding", "core", 50, [VAE], 4),
    ("B", "proof", "core", 45, [MVG], 1),
    ("B", "proof", "core", 45, [KL], 2),
    ("B", "proof", "core", 45, [KL], 2),
    ("B", "proof", "advanced", 45, [RP, VAE], 4),
    ("C", "integrative", "core", 65, [AE], 3),
    ("C", "integrative", "advanced", 65, [AE], 3),
    ("C", "integrative", "advanced", 65, [VAE], 5),
    ("C", "integrative", "advanced", 65, [VAE], 5),
    ("C", "scenario", "core", 55, [MVG, AE, VAE], 4),
    ("C", "scenario", "core", 55, [KL, VAE], 5),
    ("C", "challenge", "advanced", 55, [RP, VAE], 5),
    ("C", "challenge", "advanced", 55, [RP], 5),
]
DIRECT_PRACTICES = {
    MVG: {1, 2, 6, 7, 13, 21},
    KL: {3, 8, 9, 14, 15, 22},
    AE: {4, 10, 17, 18, 21},
    RP: {5, 11, 16, 23, 24},
    VAE: {12, 16, 19, 20, 21, 22, 23},
}
ROW_MODALITIES = {
    MVG: ["theory", "derivation", "implementation"],
    KL: ["theory", "derivation", "implementation"],
    AE: ["theory", "implementation", "model-training"],
    RP: ["theory", "derivation", "implementation"],
    VAE: ["theory", "derivation", "implementation", "model-training"],
}
PINNED_FUNCTIONS = {
    "p09": ("kl_to_standard_normal(mu, logvar)",),
    "p11": ("reparameterize(mu, logvar, eps)",),
    "p17": ("train_autoencoder(model, batch, optimizer)", "exactly 400", "lr=0.01"),
    "p18": ("train_linear_autoencoder(model, batch, optimizer)", "exactly 1500", "lr=0.02"),
    "p19": (
        "train_vae(model, batch, optimizer)",
        "negative_elbo(x, x_hat, mu, logvar)",
        "exactly 600",
        "lr=0.01",
    ),
    "p20": ("train_vae_for_sampling(model, batch, optimizer)", "exactly 800", "lr=0.01"),
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


def test_exact_60_file_inventory_is_regular_nonsymlink_and_cache_free() -> None:
    actual = {
        path.relative_to(UNIT).as_posix()
        for path in UNIT.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    assert actual == EXPECTED_FILES
    assert len(actual) == 60
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
        pset, ptype, difficulty, minutes, concepts, after_session = expected
        assert row == {
            "id": f"B2-022-p{number:02}",
            "set": pset,
            "type": ptype,
            "difficulty": difficulty,
            "provenance": "original",
            "concepts": concepts,
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


def test_every_owned_concept_has_its_exact_direct_practices() -> None:
    rows = _manifest()["practice"]
    for concept, numbers in DIRECT_PRACTICES.items():
        tagged = {
            int(row["id"][-2:]) for row in rows if concept in row["concepts"]
        }
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


def test_student_headers_metadata_and_remediation_contract_are_exact() -> None:
    for relative in ["lesson.ipynb", "review.ipynb", *LESSONS, *STATEMENTS]:
        notebook = _notebook(relative)
        assert notebook.metadata["usaaio"] == {
            "book": 2,
            "layer": "Round 2 extension",
            "unit": UNIT_ID,
            "surface": relative,
            "compute": {"policy": "cpu", "seed": SEED},
            "qualified_prerequisites": PREREQ_UNITS,
            "concept_prerequisites": CONCEPT_PREREQS,
        }
        header = str(notebook.cells[0].source)
        assert "**Qualified prerequisites:** " in header
        assert "**Remediation links actually used:** " in header
        assert all(f"`{prereq}`" in header for prereq in PREREQ_UNITS)
        assert all(f"[{prereq}]" in header for prereq in PREREQ_UNITS)
        assert "compute.policy: cpu" in header and str(SEED) in header
        assert "tensor-shape-tracing" not in _source(relative)


def test_five_sessions_have_nine_sections_checkpoints_and_forward_pointer() -> None:
    for relative in LESSONS[1:]:
        source = _source(relative)
        matches = list(re.finditer(r"(?m)^## (\d+)\. ([^\n]+)$", source))
        assert [int(match.group(1)) for match in matches] == list(range(1, 10)), relative
        titles = [match.group(2) for match in matches]
        assert sum("Worked laboratory" in title for title in titles) == 1
        assert titles[7].startswith("Common pitfalls")
        assert titles[8].startswith("Forward-only deeper topic")
        assert "not assessed" in source[matches[-1].start() :].lower()
        assert "B2-023" in source
        assert source.count("**Checkpoint") >= 18
        assert source.count("**Collected answers.**") >= 9
        meaningful_code = [
            cell
            for cell in _notebook(relative).cells
            if cell.cell_type == "code" and len(str(cell.source).strip().splitlines()) >= 5
        ]
        assert len(meaningful_code) >= 2


def test_lessons_teach_the_in_unit_tools_before_practice() -> None:
    session1 = _source(LESSONS[1])
    session2 = _source(LESSONS[2])
    session3 = _source(LESSONS[3])
    session4 = _source(LESSONS[4])
    assert "slogdet" in session1 and "cholesky" in session1.lower()
    assert "Cov" in session1
    assert "log x" in session2.replace("\\log", "log") or "x-1" in session2.replace(" ", "")
    assert "Jensen" in session2
    assert "linalg.solve" in session3
    assert "ELBO" in session4 and "Jensen" in session4


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
        assert row["after_session"] >= max(
            concept_session[concept] for concept in row["concepts"]
        )
        tree = ast.parse(code or "pass", filename=relative)
        assert not any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Return, ast.Assert))
            for node in ast.walk(tree)
        )


def test_coding_and_training_statements_pin_functions_and_protocol() -> None:
    for problem_id, tokens in PINNED_FUNCTIONS.items():
        source = _source(f"practice/{problem_id}.ipynb")
        assert all(token in source for token in tokens), problem_id
    for problem_id in ("p17", "p18", "p19", "p20"):
        source = _source(f"practice/{problem_id}.ipynb")
        assert "train_rows()" in source and "heldout_rows()" in source
        assert "TRAIN_IDS" in source and "HELDOUT_IDS" in source
        assert "betas=(0.9, 0.999)" in source
        assert "eps=1e-8" in source and "weight_decay=0" in source


def test_generator_and_loader_are_self_contained_and_prohibit_external_data() -> None:
    allowed_roots = {
        "__future__", "argparse", "hashlib", "json", "pathlib", "sys", "types",
        "numpy", "torch",
    }
    for relative in ("data/latent_data.py", "scripts/generate_latent_data.py"):
        source = (UNIT / relative).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        assert roots <= allowed_roots, relative
        lowered = source.lower()
        assert all(
            forbidden not in lowered
            for forbidden in ("torchvision", "http://", "https://", "requests", "urlopen")
        )
    payload = json.loads((UNIT / "data/latent_datasets.json").read_text(encoding="utf-8"))
    assert payload["seed"] == SEED
    assert set(payload) == {"unit", "seed", "decimals", "hash_convention", "datasets"}
    for entry in payload["datasets"].values():
        assert set(entry) == {"dim", "rows", "train_ids", "heldout_ids", "row_sha256"}


def test_generator_check_regenerates_rows_splits_and_hashes() -> None:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, str(UNIT / "scripts/generate_latent_data.py"), "--check"],
        cwd=UNIT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith("PASS")
    source = (UNIT / "scripts/generate_latent_data.py").read_text(encoding="utf-8")
    assert "state_dict" not in source and "torch.save" not in source


def test_loader_exposes_immutable_partitioning_splits_and_hash_map() -> None:
    path = UNIT / "data/latent_data.py"
    spec = importlib.util.spec_from_file_location("b2_022_latent_data", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.SEED == SEED
    assert module.DATASET_NAMES == ("mixture2d", "mixture8d", "lowrank8d")
    for name in module.DATASET_NAMES:
        train, held = module.TRAIN_IDS[name], module.HELDOUT_IDS[name]
        assert isinstance(train, tuple) and isinstance(held, tuple)
        assert set(train).isdisjoint(held) and len(train) == 48 and len(held) == 12
        rows = module.train_tensor(name)
        assert [module.row_sha256(row) for row in rows] == [
            module.ROW_SHA256[name][index] for index in train
        ]
    try:
        module.TRAIN_IDS["mixture2d"] = ()
    except TypeError:
        pass
    else:  # pragma: no cover - immutability regression
        raise AssertionError("TRAIN_IDS must be read-only")


def test_coverage_claims_point_to_real_primary_evidence() -> None:
    raw = _manifest()
    practices = {row["id"]: row for row in raw["practice"]}
    claims = raw["coverage_claims"]
    assert [claim["knowledge_point"] for claim in claims] == OWNED
    observed: set[tuple[str, str]] = set()
    for claim in claims:
        concept = claim["knowledge_point"]
        assert claim["modalities"] == ROW_MODALITIES[concept]
        assert claim["first_session"] >= raw["concept_sessions"][concept]
        for modality, evidence in claim["evidence_by_modality"].items():
            observed.add((concept, modality))
            assert evidence["lesson_anchors"] and evidence["practices"]
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
    assert len(observed) == sum(len(value) for value in ROW_MODALITIES.values()) == 16


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


def test_ci_bounds_b2_022_solutions_at_twenty_seconds() -> None:
    script = (ROOT / "scripts/ci-local.sh").read_text(encoding="utf-8")
    assert (
        "|| $relative == units/B2-022-probabilistic-latent-models/practice/p??_solution.ipynb ]]"
        in script
    )
