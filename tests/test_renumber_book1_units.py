"""Plan 031 D2/D6: the one-shot Book 1 renumbering rewrite."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "renumber-book1-units.py"


def _load():
    spec = importlib.util.spec_from_file_location("renumber_book1_units", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


renumber = _load()


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("F3-matrices", "F4-matrices"),
        ("F4-multivar-calculus", "F3-multivar-calculus"),
        ("C5-neural-networks", "C6-neural-networks"),
        ("C6-pytorch", "C7-pytorch"),
        ("C7-cnn-transfer", "C10-cnn-transfer"),
        ("C8-embeddings", "C5-embeddings"),
        ("C10-competition-craft", "C11-competition-craft"),
        ("C11-neural-training", "C8-neural-training"),
        ("F1-scientific-python", "F1-scientific-python"),
    ],
)
def test_every_swap_and_cycle_member_maps_once(old: str, new: str) -> None:
    assert renumber.rewrite_text(f"unit: {old}\n", "x.yaml") == f"unit: {new}\n"
    assert renumber.rewrite_text(f"book1:{old}", "x.md") == f"book1:{new}"


def test_swap_and_cycle_in_one_text_are_simultaneous() -> None:
    text = "F3 F4 C5 C6 C7 C8 C10 C11 (C12)"
    assert renumber.rewrite_text(text, "x.md") == "F4 F3 C6 C7 C10 C5 C11 C8 (C12)"


def test_practice_id_and_full_id_each_map_exactly_once() -> None:
    text = "C11-p16 and C11-neural-training and C11-p16-alpha and book1:C7-p10 f\"C8-p{n:02d}\""
    assert renumber.rewrite_text(text, "x.py") == (
        "C8-p16 and C8-neural-training and C8-p16-alpha and book1:C10-p10 f\"C5-p{n:02d}\""
    )


def test_lesson_reference_maps_code() -> None:
    assert renumber.rewrite_text("see F3-02 and C7-01", "x.md") == "see F4-02 and C10-01"


def test_folder_context_becomes_prefixed_folder() -> None:
    text = (
        "[x](../../../../book1/units/C11-neural-training/lesson.ipynb) "
        "book1:units/C8-embeddings/lessons/01.ipynb "
        'root / "units" / "C4-classical-ml-practice" / "data" '
        'root / \\"units\\" / \\"C7-cnn-transfer\\"'
    )
    assert renumber.rewrite_text(text, "x.ipynb") == (
        "[x](../../../../book1/units/15-C8-neural-training/lesson.ipynb) "
        "book1:units/10-C5-embeddings/lessons/01.ipynb "
        'root / "units" / "09-C4-classical-ml-practice" / "data" '
        'root / \\"units\\" / \\"17-C10-cnn-transfer\\"'
    )


@pytest.mark.parametrize(
    "text",
    [
        'plt.plot(x, y, color="C5")',
        "ax.scatter(x, y, c='C7')",
        'ax.plot(x, y, "C6--")',
        "macro-averaged F1 is reported",
        "the F1 score",
    ],
)
def test_deny_contexts_are_never_rewritten(text: str) -> None:
    assert renumber.rewrite_text(text, "x.py") == text


def test_hyphenated_codes_are_not_bare_codes() -> None:
    assert renumber.rewrite_text("C5-only-a-word B2-C7 xC6", "x.md") == "C5-only-a-word B2-C7 xC6"


def test_residue_deny_keeps_python_variable() -> None:
    path = "book1/units/F3-matrices/lessons/02-multiplication-and-gram-matrices.ipynb"
    text = '"C6 = G6 / (norms[:, None] * norms[None, :])\\n",\n"C6 bridge\\n",'
    assert renumber.rewrite_text(text, path) == '"C6 = G6 / (norms[:, None] * norms[None, :])\\n",\n"C7 bridge\\n",'


def test_overrides_apply_in_the_same_pass() -> None:
    assert renumber.rewrite_text("taught by units C5-C7; and C5", "m.yaml") == "taught by units C6, C7 and C10; and C6"
    assert renumber.rewrite_text("drills of F1–F4", "n.ipynb") == "drills of F1–F4"


def test_rewrite_path_maps_unit_folders_and_the_c11_test() -> None:
    assert renumber.rewrite_path("book1/units/C7-cnn-transfer/practice/p10.ipynb") == (
        "book1/units/17-C10-cnn-transfer/practice/p10.ipynb"
    )
    assert renumber.rewrite_path("tests/test_c11_solution_regressions.py") == "tests/test_c8_solution_regressions.py"
    assert renumber.rewrite_path("book2/units/B2-019-x/a.md") == "book2/units/B2-019-x/a.md"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _fresh_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "book1" / "curriculum").mkdir(parents=True)
    (repo / "book1" / "curriculum" / "course-schedule.yaml").write_text(
        "schedule_version: 1\nweeks:\n- week: 1\n  unit: C11-neural-training\n", encoding="utf-8"
    )
    for _, old, _ in renumber.MAPPING:
        unit = repo / "book1" / "units" / old
        unit.mkdir(parents=True)
        (unit / "manifest.yaml").write_text(f"unit: {old}\nproblems: [{old.split('-')[0]}-p01]\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_c11_solution_regressions.py").write_text('P = "units/C11-neural-training"\n')
    (repo / "docs" / "plans").mkdir(parents=True)
    (repo / "docs" / "plans" / "001.md").write_text("C11-neural-training stays\n")
    _git(repo, "init", "-q")
    _git(repo, "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
    return repo


def _snapshot(repo: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(repo)): p.read_bytes()
        for p in sorted(repo.rglob("*"))
        if p.is_file() and ".git" not in p.relative_to(repo).parts
    }


def test_apply_then_second_run_is_a_no_op(tmp_path: Path) -> None:
    repo = _fresh_repo(tmp_path)
    assert renumber.migration_state(repo) == "fresh"
    assert renumber.main(["--repo", str(repo)]) == 0
    assert renumber.migration_state(repo) == "migrated"
    manifest = repo / "book1" / "units" / "15-C8-neural-training" / "manifest.yaml"
    assert manifest.read_text() == "unit: C8-neural-training\nproblems: [C8-p01]\n"
    swap = repo / "book1" / "units" / "04-F4-matrices" / "manifest.yaml"
    assert swap.read_text() == "unit: F4-matrices\nproblems: [F4-p01]\n"
    schedule = (repo / "book1" / "curriculum" / "course-schedule.yaml").read_text()
    assert "teaching_order:\n- F1-scientific-python\n" in schedule
    assert "unit: C8-neural-training" in schedule
    assert (repo / "tests" / "test_c8_solution_regressions.py").read_text() == 'P = "units/15-C8-neural-training"\n'
    assert (repo / "docs" / "plans" / "001.md").read_text() == "C11-neural-training stays\n"
    _git(repo, "add", "-A")
    before = _snapshot(repo)
    assert renumber.main(["--repo", str(repo)]) == 0
    assert _snapshot(repo) == before


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    repo = _fresh_repo(tmp_path)
    before = _snapshot(repo)
    assert renumber.main(["--repo", str(repo), "--dry-run"]) == 0
    assert _snapshot(repo) == before


def test_half_migrated_tree_fails_without_writing(tmp_path: Path) -> None:
    repo = _fresh_repo(tmp_path)
    _git(repo, "mv", "book1/units/F1-scientific-python", "book1/units/01-F1-scientific-python")
    before = _snapshot(repo)
    assert renumber.migration_state(repo) == "half"
    assert renumber.main(["--repo", str(repo)]) != 0
    assert _snapshot(repo) == before


def test_teaching_order_without_prefixes_is_half_migrated(tmp_path: Path) -> None:
    repo = _fresh_repo(tmp_path)
    schedule = repo / "book1" / "curriculum" / "course-schedule.yaml"
    schedule.write_text(renumber.insert_teaching_order(schedule.read_text()))
    assert renumber.migration_state(repo) == "half"
    assert renumber.main(["--repo", str(repo)]) != 0
