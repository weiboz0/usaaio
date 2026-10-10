"""Plan 024 Task 3: the published Round 2 mock test r2-001."""

from __future__ import annotations

import ast
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import nbformat
import pytest
import yaml
from nbclient import NotebookClient

from tools.checks.answerkey import check_answerkey
from tools.checks.blueprint import check_blueprint
from tools.checks.hygiene import check_hygiene
from tools.checks.schedule import check_schedule
from tools.model import load_mock_manifests

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
BOOK2_ROOT = ROOT / "book2"
TEST_DIR = BOOK2_ROOT / "mocktests" / "r2-001"
SEED = 20261101

EXPECTED_FILES = {
    ".gitignore",
    "manifest.yaml",
    "rubric.md",
    "test.md",
    "data/gen_r2_001.py",
    "data/p01_corpus.json",
    "data/p03_vae.json",
    "data/r2_001_data.py",
    "data/r2_001_datasets.json",
    "problems/.gitignore",
    *(f"problems/p0{n}.ipynb" for n in range(1, 6)),
    "solutions/answers.md",
    *(f"solutions/p0{n}_solution.ipynb" for n in range(1, 6)),
    "theory/.gitignore",
    "theory/p01.md",
    "theory/p03.md",
}

OPEN_ENDED = {
    "r2-001-p02": ("heat", "p02", "position_error", "lower", 70),
    "r2-001-p04": ("texture", "p04", "accuracy", "higher", 40),
    "r2-001-p05": ("lorentz", "p05", "parameter_error", "lower", 50),
}
NUMBER = r"(\d+\.\d+)"
MARKER = re.compile(
    rf"metric=(?P<metric>[a-z_]+); direction=(?P<direction>lower|higher); B={NUMBER}; R={NUMBER}; "
    rf"tiers={NUMBER},{NUMBER},{NUMBER}"
)


def _manifest() -> dict:
    return yaml.safe_load((TEST_DIR / "manifest.yaml").read_text(encoding="utf-8"))


def _sig4(value: float) -> str:
    return f"{value:#.4g}"


def _significant_digits(text: str) -> int:
    return len(text.replace(".", "").lstrip("0"))


def _marker(problem_id: str) -> dict:
    entry = next(p for p in _manifest()["problems"] if p["id"] == problem_id)
    match = MARKER.fullmatch(entry["answer_key"])
    assert match, entry["answer_key"]
    b_text, r_text, *tier_texts = match.groups()[2:]
    return {
        "metric": match["metric"],
        "direction": match["direction"],
        "texts": [b_text, r_text, *tier_texts],
        "B": float(b_text),
        "R": float(r_text),
        "tiers": [float(t) for t in tier_texts],
        "tier_texts": tier_texts,
    }


def _expected_tiers(direction: str, b: float, r: float) -> list[str]:
    g = abs(b - r)
    if direction == "lower":
        return [_sig4(r + 0.25 * g), _sig4(b), _sig4(b + 0.25 * g)]
    return [_sig4(r - 0.25 * g), _sig4(b), _sig4(b - 0.25 * g)]


def _rel_files() -> set[str]:
    return {
        path.relative_to(TEST_DIR).as_posix()
        for path in TEST_DIR.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and ".quarto" not in path.parts
    }


def _notebook_source(path: Path) -> str:
    notebook = nbformat.read(path, as_version=4)
    return "\n".join(str(cell.source) for cell in notebook.cells)


def _code_cells(path: Path) -> list[str]:
    notebook = nbformat.read(path, as_version=4)
    return [str(cell.source) for cell in notebook.cells if cell.cell_type == "code"]


def test_exact_file_inventory():
    assert _rel_files() == EXPECTED_FILES


def test_manifest_shape_and_answer_keys():
    raw = _manifest()
    manifests = [m for m in load_mock_manifests(BOOK2_ROOT, book_number=2) if m.test == "r2-001"]
    assert len(manifests) == 1
    manifest = manifests[0]
    assert manifest.status == "final"
    assert len(manifest.problems) == 25
    assert sum(p.points for p in manifest.problems) == 300
    assert manifest.day_duration_minutes == 240
    assert manifest.day_time_budget == {1: {"d1-arc": 120, "d1-open": 120},
                                        2: {"d2-arc": 80, "d2-open": 160}}
    open_points = sum(p.points for p in manifest.problems if p.answer_form == "open-ended")
    assert open_points == 160
    assert raw["generation_parameters"]["seed"] == SEED
    assert all(problem.answer_key not in (None, "") for problem in manifest.problems)
    by_day = {1: 0, 2: 0}
    for problem in manifest.problems:
        by_day[problem.day] += problem.points
    assert by_day == {1: 160, 2: 140}


def test_blueprint_conformance():
    report = check_blueprint(BOOK2_ROOT)
    assert report.ok, report.errors
    assert report.warnings == [] and report.skipped is None


def test_answerkey_reproduction():
    report = check_answerkey(BOOK2_ROOT, book_number=2)
    assert report.ok, report.errors
    assert report.skipped is None


def test_hygiene_of_problem_notebooks():
    report = check_hygiene(BOOK2_ROOT)
    assert report.ok, report.errors
    for n in range(1, 6):
        notebook = nbformat.read(TEST_DIR / "problems" / f"p0{n}.ipynb", as_version=4)
        for cell in notebook.cells:
            assert cell.get("outputs", []) == []
            assert cell.get("execution_count") is None


def test_schedule_marks_r2_001_as_the_live_final_assessment():
    schedule = yaml.safe_load((BOOK2_ROOT / "curriculum" / "course-schedule.yaml").read_text())
    assert schedule["final_assessment"] == {
        "kind": "r2-mock", "status": "live", "test": "r2-001", "after_book_week": 37,
    }
    assert check_schedule(BOOK2_ROOT, expected_book_number=2).ok


def test_ci_local_runs_r2_001_solutions_under_the_20_second_timeout():
    text = (ROOT / "scripts" / "ci-local.sh").read_text()
    assert "$relative == mocktests/r2-001/solutions/p??_solution.ipynb" in text


def test_generator_check_is_byte_identical():
    proc = subprocess.run(
        [sys.executable, "-I", str(TEST_DIR / "data" / "gen_r2_001.py"), "--check"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "check ok" in proc.stdout


def _generator():
    spec = importlib.util.spec_from_file_location("_r2_001_gen_test", TEST_DIR / "data" / "gen_r2_001.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_lorentz_simulation_survives_rounding_for_fresh_seeds():
    # Regression for the pre-publication bug: 4-dp rounding used to trip the separation
    # re-check (tolerance 1e-9) for many seeds, so simulate("lorentz", ...) raised.
    generator = _generator()
    for seed in range(1, 21):
        values, params = generator.simulate_block("lorentz", 2000, seed)
        p3 = params.reshape(-1, 2, 3)
        margin = p3[:, 1, 1] - p3[:, 0, 1] - generator.LOR_SEPARATION * p3[..., 2].sum(1)
        assert margin.min() >= -generator.ROUNDING_SLACK
        assert values.shape == (2000, 40)


def _texture_features(x):
    """The published P4 reference's closed-form features (pixel moments, spectral peakiness,
    radial power bands, neighbour correlations): (N, 1, 10, 10) -> (N, 23)."""
    import torch

    k = torch.fft.fftfreq(10, dtype=torch.float64) * 10
    kx, ky = torch.meshgrid(k, k, indexing="ij")
    radius = (kx ** 2 + ky ** 2).sqrt()
    z = x[:, 0].double()
    m, s = z.mean((1, 2)), z.std((1, 2))
    zc = (z - m[:, None, None]) / (s[:, None, None] + 1e-6)
    power = torch.fft.fft2(zc).abs() ** 2
    power[:, 0, 0] = 0
    flat = power.reshape(len(z), -1)
    total = flat.sum(1)
    top = flat.sort(dim=1, descending=True).values[:, :8] / total[:, None]
    bands = [(power * ((radius >= lo) & (radius < hi))).sum((1, 2)) / total
             for lo, hi in [(0, 1.5), (1.5, 2.5), (2.5, 3.5), (3.5, 4.5), (4.5, 8)]]
    c_v = (zc[:, 1:, :] * zc[:, :-1, :]).mean((1, 2))
    c_h = (zc[:, :, 1:] * zc[:, :, :-1]).mean((1, 2))
    c_d = (zc[:, 1:, 1:] * zc[:, :-1, :-1]).mean((1, 2))
    c_a = (zc[:, 1:, :-1] * zc[:, :-1, 1:]).mean((1, 2))
    return torch.stack([m, s, (zc ** 3).mean((1, 2)), (zc ** 4).mean((1, 2)), *top.T, *bands,
                        c_v, c_h, c_d, c_a, (c_v - c_h).abs(), (c_d - c_a).abs()], dim=1)


P4_LABELLED_ONLY_MARGIN = 0.15


def test_p4_labelled_only_probe_stays_well_below_full_credit():
    """P4 must assess use of the unlabelled pool.  Stated probe: the reference's closed-form
    features standardized on the 40 labelled rows, a logistic head (150 Adam steps, lr 0.05,
    weight decay 0.01, seed SEED) trained on the labelled rows only, no pool statistics.  Its
    locked-test accuracy must stay below the full-credit cutoff by at least the stated margin
    (it scores 0.6250 at the frozen seed against the 0.8638 cutoff)."""
    torch = pytest.importorskip("torch")
    spec = importlib.util.spec_from_file_location("_r2_001_data_probe", TEST_DIR / "data" / "r2_001_data.py")
    data = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data)
    torch.set_num_threads(1)
    x_lab, y_lab = data.train_rows("texture")
    features = _texture_features(x_lab)
    mu, sd = features.mean(0), features.std(0)
    torch.manual_seed(SEED)
    head = torch.nn.Linear(features.shape[1], 3, dtype=torch.float32)
    optimizer = torch.optim.Adam(head.parameters(), lr=0.05, weight_decay=1e-2)
    standardized = ((features - mu) / sd).float()
    for _ in range(150):
        optimizer.zero_grad(set_to_none=True)
        torch.nn.functional.cross_entropy(head(standardized), y_lab).backward()
        optimizer.step()

    def predict(x):
        with torch.no_grad():
            return head(((_texture_features(x) - mu) / sd).float()).argmax(dim=1).to(torch.int64)

    score = data.final_test_score(predict, task="texture").score
    full_credit = _marker("r2-001-p04")["tiers"][0]
    assert score <= full_credit - P4_LABELLED_ONLY_MARGIN, (score, full_credit)


@pytest.mark.parametrize("problem_id", sorted(OPEN_ENDED))
def test_open_ended_marker_format_tiers_and_calibration(problem_id):
    marker = _marker(problem_id)
    _, _, metric, direction, _ = OPEN_ENDED[problem_id]
    assert marker["metric"] == metric and marker["direction"] == direction
    assert all(_significant_digits(text) == 4 for text in marker["texts"]), marker["texts"]
    assert marker["tier_texts"] == _expected_tiers(direction, marker["B"], marker["R"])
    b, r = marker["B"], marker["R"]
    if direction == "lower":
        assert r <= 0.8 * b
        assert marker["tiers"][0] < marker["tiers"][1] < marker["tiers"][2]
    else:
        assert r >= b + 0.05
        assert marker["tiers"][0] > marker["tiers"][1] > marker["tiers"][2]


@pytest.mark.parametrize("problem_id", sorted(OPEN_ENDED))
def test_statement_rubric_and_answers_print_the_same_b_r_and_cutoffs(problem_id):
    marker = _marker(problem_id)
    _, stem, _, _, points = OPEN_ENDED[problem_id]
    b_text, r_text, *tiers = marker["texts"]
    g_text = _sig4(abs(marker["B"] - marker["R"]))
    statement = _notebook_source(TEST_DIR / "problems" / f"{stem}.ipynb")
    rubric = (TEST_DIR / "rubric.md").read_text()
    assert f"**R = {r_text}**" in statement and f"**B = {b_text}**" in statement
    assert f"g = |B - R| = {g_text}" in statement
    assert f"**B = {b_text}, R = {r_text}, g = {g_text}.**" in rubric
    for tier in tiers:
        assert re.search(rf"`(<=|>=|<|>) {re.escape(tier)}`", statement), tier
        assert tier in rubric
    answers = (TEST_DIR / "solutions" / "answers.md").read_text()
    assert f"- {problem_id}: answer: {_manifest_key(problem_id)}" in answers
    full = tiers[0]
    solution = _notebook_source(TEST_DIR / "solutions" / f"{stem}_solution.ipynb")
    assert full in solution
    score_points = {70: "42", 40: "24", 50: "30"}[points]
    assert f"**{score_points} points** (100% of the score portion)" in statement


def _manifest_key(problem_id: str) -> str:
    return next(p for p in _manifest()["problems"] if p["id"] == problem_id)["answer_key"]


@pytest.mark.parametrize("problem_id", sorted(OPEN_ENDED))
def test_one_call_protocol_in_reference_solution(problem_id):
    task, stem, _, _, _ = OPEN_ENDED[problem_id]
    cells = _code_cells(TEST_DIR / "solutions" / f"{stem}_solution.ipynb")
    calls = 0
    for source in cells:
        tree = ast.parse(source)
        calls += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "final_test_score"
        )
    assert calls == 1
    answer_check = cells[-1]
    assert f'r2_001_data.test_call_count("{task}") == 1' in answer_check
    statement = _notebook_source(TEST_DIR / "problems" / f"{stem}.ipynb")
    assert "final_test_score" in statement


def _execute_with_probe(path: Path) -> tuple[float, float]:
    notebook = nbformat.read(path, as_version=4)
    notebook.cells.append(nbformat.v4.new_code_cell(
        "import json as _json\n"
        "print('R2PROBE' + _json.dumps([float(result.score), float(baseline.score)]))"
    ))
    env_root = os.environ.get("USAAIO_BOOK_ROOT")
    os.environ["USAAIO_BOOK_ROOT"] = str(BOOK2_ROOT)
    try:
        NotebookClient(
            notebook, timeout=300, kernel_name="python3",
            resources={"metadata": {"path": str(path.parent)}},
        ).execute()
    finally:
        if env_root is None:
            os.environ.pop("USAAIO_BOOK_ROOT", None)
        else:
            os.environ["USAAIO_BOOK_ROOT"] = env_root
    for output in notebook.cells[-1].outputs:
        text = output.get("text", "")
        if "R2PROBE" in text:
            score, base = json.loads(text.split("R2PROBE", 1)[1].strip())
            return score, base
    raise AssertionError("probe output missing")


def _rounding_tolerance(text: str) -> float:
    """Half a unit in the last (4th significant) printed digit."""
    decimals = len(text.split(".")[1])
    return 0.5 * 10 ** (-decimals) + 1e-12


@pytest.mark.parametrize("problem_id", sorted(OPEN_ENDED))
def test_reference_solution_reproduces_r_and_baseline_reproduces_b(problem_id):
    """Stated tolerance: the 4-significant-digit rounding of the printed B and R."""
    marker = _marker(problem_id)
    _, stem, _, _, _ = OPEN_ENDED[problem_id]
    score, base = _execute_with_probe(TEST_DIR / "solutions" / f"{stem}_solution.ipynb")
    b_text, r_text = marker["texts"][:2]
    assert math.isclose(score, marker["R"], rel_tol=0, abs_tol=_rounding_tolerance(r_text)), score
    assert math.isclose(base, marker["B"], rel_tol=0, abs_tol=_rounding_tolerance(b_text)), base
