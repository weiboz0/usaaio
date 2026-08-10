from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).parents[1]
INVENTORY = ROOT / "tests" / "fixtures" / "plan019-path-inventory.yaml"
CONTENT_TOKENS = {
    "units",
    "curriculum",
    "mocktests",
    "reference",
    "syllabus.md",
    "sources.yaml",
    "course-structure.md",
    "build",
}


def _inventory() -> dict[str, Any]:
    return yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))


def _notebook_pyproject_cells(path: Path) -> list[int]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [
        index
        for index, cell in enumerate(raw.get("cells", []))
        if cell.get("cell_type") == "code" and "pyproject.toml" in "".join(cell.get("source", []))
    ]


def test_path_inventory_pins_exactly_64_code_cell_pyproject_consumers() -> None:
    rows = _inventory()["notebook_pyproject_discovery"]
    assert len(rows) == 64
    assert len({row["path"] for row in rows}) == 64

    baseline_present = (ROOT / rows[0]["path"]).exists()
    discovered: list[dict[str, object]] = []
    for row in rows:
        old_path = ROOT / row["path"]
        migrated_path = ROOT / "book1" / row["path"]
        if baseline_present:
            assert old_path.is_file(), row["path"]
            cells = _notebook_pyproject_cells(old_path)
            if cells:
                discovered.append({"path": row["path"], "cells": cells})
        else:
            assert migrated_path.is_file(), row["path"]
            assert _notebook_pyproject_cells(migrated_path) == []
    if baseline_present:
        assert discovered == rows


def test_path_inventory_names_split_token_and_special_relative_consumers() -> None:
    inventory = _inventory()
    assert inventory["split_token_python_consumers"] == [
        "tests/test_c11_solution_regressions.py",
        "tests/test_c12_solution_regressions.py",
        "tests/test_c12_statement_contracts.py",
    ]
    special = {row["path"]: row["cells"] for row in inventory["special_notebook_consumers"]}
    assert special == {
        "units/C4-classical-ml-practice/lessons/01-pandas-and-data-loading.ipynb": [22],
        "mocktests/r1-001/problems/p09.ipynb": [3],
        "mocktests/r1-001/solutions/p09_solution.ipynb": [2, 14],
    }


def _looks_like_content_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return any(
        normalized == token
        or normalized.startswith(f"{token}/")
        or f"/{token}/" in normalized
        or normalized.endswith(f"/{token}")
        for token in CONTENT_TOKENS
    )


def _python_path_consumers(path: Path) -> list[int]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and _looks_like_content_path(node.value)
        ):
            continue
        current: ast.AST | None = node
        structural = False
        for _ in range(6):
            current = parents.get(current)
            if current is None:
                break
            if isinstance(current, ast.BinOp) and isinstance(current.op, ast.Div):
                structural = True
            if isinstance(current, ast.Call):
                function = current.func
                name = (
                    function.attr
                    if isinstance(function, ast.Attribute)
                    else function.id
                    if isinstance(function, ast.Name)
                    else ""
                )
                if name in {
                    "Path",
                    "joinpath",
                    "glob",
                    "rglob",
                    "open",
                    "read_text",
                    "write_text",
                    "mkdir",
                }:
                    structural = True
        if structural:
            lines.add(node.lineno)
    return sorted(lines)


def test_ast_inventory_fails_for_any_new_unclassified_python_consumer() -> None:
    inventory = _inventory()
    classified = set(inventory["python_consumers"]) | set(inventory["task0_contract_tests"])
    discovered = {
        path.relative_to(ROOT).as_posix()
        for base in (ROOT / "tools", ROOT / "scripts", ROOT / "tests")
        for path in base.rglob("*.py")
        if _python_path_consumers(path)
    }
    assert discovered <= classified, sorted(discovered - classified)
    # Before cutover the generated baseline list is exact.  After cutover the same
    # files remain classified even though their joins become selected-book-local.
    if (ROOT / "syllabus.md").exists():
        assert discovered - set(inventory["task0_contract_tests"]) == set(
            inventory["python_consumers"]
        )


def _invalid_root_accesses(source: str, *, language: str) -> list[str]:
    if language == "shell":
        patterns = (
            r"\bfind\s+units\b",
            r"\bfor\s+dir\s+in\s+units\s+mocktests\b",
        )
    else:
        patterns = (
            r"\bPath\(\s*[\"']syllabus\.md[\"']\s*\)",
            r"\bcheck_[a-z_]+\(\s*(?:repo_root|ROOT)\s*\)",
        )
    return [pattern for pattern in patterns if re.search(pattern, source)]


@pytest.mark.parametrize(
    ("source", "language"),
    [
        ("find units -name manifest.yaml", "shell"),
        ("for dir in units mocktests; do echo $dir; done", "shell"),
        ('source = Path("syllabus.md")', "python"),
        ("check_scope(repo_root)", "python"),
    ],
)
def test_static_contract_rejects_repository_root_content_access(source: str, language: str) -> None:
    assert _invalid_root_accesses(source, language=language)


def test_static_contract_allows_selected_book_local_joins() -> None:
    assert _invalid_root_accesses('root / "units"', language="python") == []
    assert (
        _invalid_root_accesses('find "$book_root/units" -name manifest.yaml', language="shell")
        == []
    )


def test_atomic_cutover_has_every_moved_producer_and_no_legacy_root() -> None:
    expected = (
        "syllabus.md",
        "curriculum/course-schedule.yaml",
        "curriculum/coverage-map.yaml",
        "curriculum/material-inventory.yaml",
        "curriculum/official-topics.yaml",
        "curriculum/source-manifest.yaml",
        "units",
        "mocktests/blueprint.yaml",
        "reference",
        "docs/course-structure.md",
    )
    for book in ("book1", "book2"):
        for relative in expected:
            assert (ROOT / book / relative).exists(), f"missing producer {book}/{relative}"
    for legacy in ("syllabus.md", "curriculum", "units", "mocktests", "reference"):
        path = ROOT / legacy
        assert not path.exists(), f"legacy producer remains: {legacy}"
        assert not path.is_symlink(), f"legacy symlink remains: {legacy}"


def test_clean_checkout_verifier_archives_and_runs_every_solution_consumer() -> None:
    script = ROOT / "scripts" / "verify-clean-checkout.sh"
    assert script.is_file(), "scripts/verify-clean-checkout.sh is the missing producer"
    source = script.read_text(encoding="utf-8")
    for contract in (
        "git archive",
        "scripts/ci-local.sh",
        "book1/reference/cache",
        "USAAIO_BOOK_ROOT",
        "_solution.ipynb",
        "book1",
        "book2",
    ):
        assert contract in source


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


def _init_scope_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    token = repo / "units" / "C8-embeddings" / "lessons" / "01-tokens-and-embeddings.ipynb"
    token.parent.mkdir(parents=True)
    token.write_text(
        json.dumps(
            {
                "cells": [
                    {"cell_type": "markdown", "source": ["# Tokens\n"]},
                    {
                        "cell_type": "code",
                        "source": [
                            "from pathlib import Path\n",
                            "ROOT = next(p for p in Path.cwd().parents if (p / 'pyproject.toml').exists())\n",
                        ],
                    },
                    {"cell_type": "markdown", "source": ["unchanged teaching body\n"]},
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    return repo


def _install_scope_verifier(repo: Path) -> Path:
    source = ROOT / "scripts" / "verify-staged-scope.py"
    assert source.is_file(), "scripts/verify-staged-scope.py is the missing producer"
    target = repo / "scripts" / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def _scope_proc(repo: Path, mode: str) -> subprocess.CompletedProcess[str]:
    script = _install_scope_verifier(repo)
    return subprocess.run(
        [sys.executable, str(script), mode, str(INVENTORY)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def test_staged_scope_aborts_on_unrelated_notes_before_staging(tmp_path: Path) -> None:
    repo = _init_scope_repo(tmp_path)
    (repo / "notes.md").write_text("unrelated\n", encoding="utf-8")

    proc = _scope_proc(repo, "--preflight")

    assert proc.returncode != 0
    assert "notes.md" in proc.stdout + proc.stderr
    assert _git(repo, "diff", "--cached", "--name-only").stdout == ""


@pytest.mark.parametrize(
    "relative",
    ["new-token-notes.md", ".env.local", "api-secret.md", "credential.txt"],
)
def test_staged_scope_rejects_new_token_and_secret_paths(tmp_path: Path, relative: str) -> None:
    repo = _init_scope_repo(tmp_path)
    (repo / relative).write_text("forbidden\n", encoding="utf-8")
    _git(repo, "add", "-f", relative)

    proc = _scope_proc(repo, "--cached")

    assert proc.returncode != 0
    assert relative in proc.stdout + proc.stderr


@pytest.mark.parametrize("mutate_other_cell", [False, True], ids=["path-cell-only", "other-cell"])
def test_exact_c8_token_notebook_exception_is_cell_scoped(
    tmp_path: Path, mutate_other_cell: bool
) -> None:
    repo = _init_scope_repo(tmp_path)
    old = repo / "units" / "C8-embeddings" / "lessons" / "01-tokens-and-embeddings.ipynb"
    new = repo / "book1" / old.relative_to(repo)
    new.parent.mkdir(parents=True)
    old.rename(new)
    notebook = json.loads(new.read_text(encoding="utf-8"))
    notebook["cells"][1]["source"] = [
        "from pathlib import Path\n",
        "ROOT = Path(os.environ['USAAIO_BOOK_ROOT'])\n",
    ]
    if mutate_other_cell:
        notebook["cells"][2]["source"] = ["changed teaching body\n"]
    new.write_text(json.dumps(notebook), encoding="utf-8")
    _git(repo, "add", "-A")

    proc = _scope_proc(repo, "--cached")

    if mutate_other_cell:
        assert proc.returncode != 0
        assert "cell" in (proc.stdout + proc.stderr).lower()
    else:
        assert proc.returncode == 0, proc.stdout + proc.stderr
