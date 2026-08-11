from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
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


def _discover_pyproject_notebooks(repo: Path) -> list[dict[str, object]]:
    roots = (
        (repo / "units", "units"),
        (repo / "mocktests", "mocktests"),
        (repo / "book1" / "units", "units"),
        (repo / "book1" / "mocktests", "mocktests"),
        (repo / "book2" / "units", "book2/units"),
        (repo / "book2" / "mocktests", "book2/mocktests"),
    )
    rows: list[dict[str, object]] = []
    for root, normalized_prefix in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.ipynb")):
            if "build" in path.parts:
                continue
            cells = _notebook_pyproject_cells(path)
            if cells:
                relative = path.relative_to(root).as_posix()
                rows.append({"path": f"{normalized_prefix}/{relative}", "cells": cells})
    return sorted(rows, key=lambda row: str(row["path"]).encode())


def test_path_inventory_pins_exactly_64_code_cell_pyproject_consumers() -> None:
    rows = _inventory()["notebook_pyproject_discovery"]
    assert len(rows) == 64
    assert len({row["path"] for row in rows}) == 64

    baseline_present = (ROOT / rows[0]["path"]).exists()
    discovered = _discover_pyproject_notebooks(ROOT)
    if baseline_present:
        assert discovered == rows
    else:
        assert discovered == [], discovered
        for row in rows:
            migrated_path = ROOT / "book1" / row["path"]
            assert migrated_path.is_file(), row["path"]
            assert _notebook_pyproject_cells(migrated_path) == []


def test_a_65th_unclassified_pyproject_notebook_is_discovered(tmp_path: Path) -> None:
    rows = _inventory()["notebook_pyproject_discovery"]
    for row in rows:
        path = tmp_path / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        cell_count = max(row["cells"]) + 1
        cells = [{"cell_type": "markdown", "source": ["fixture\n"]} for _ in range(cell_count)]
        for index in row["cells"]:
            cells[index] = {"cell_type": "code", "source": ["Path('pyproject.toml')\n"]}
        path.write_text(json.dumps({"cells": cells}), encoding="utf-8")
    extra = tmp_path / "units" / "C99-unclassified" / "lesson.ipynb"
    extra.parent.mkdir(parents=True)
    extra.write_text(
        json.dumps({"cells": [{"cell_type": "code", "source": ["Path('pyproject.toml')\n"]}]}),
        encoding="utf-8",
    )

    discovered = _discover_pyproject_notebooks(tmp_path)

    assert len(discovered) == 65
    assert discovered != rows
    assert {row["path"] for row in discovered} - {row["path"] for row in rows} == {
        "units/C99-unclassified/lesson.ipynb"
    }


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
    expected_markers = {
        "units/C4-classical-ml-practice/lessons/01-pandas-and-data-loading.ipynb": {
            22: ("fallback: repo root", "units/C4-classical-ml-practice/practice/data")
        },
        "mocktests/r1-001/problems/p09.ipynb": {
            3: ("../data/p09_train.csv", "mocktests/r1-001/data/p09_train.csv")
        },
        "mocktests/r1-001/solutions/p09_solution.ipynb": {
            2: ("../data/p09_train.csv", "mocktests/r1-001/data/p09_train.csv"),
            14: ("../data/gen_p09.py", "mocktests/r1-001/data/gen_p09.py"),
        },
    }
    for relative, cells in expected_markers.items():
        path = ROOT / relative
        legacy = path.exists()
        if not path.exists():
            path = ROOT / "book1" / relative
        assert path.is_file(), relative
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for index, markers in cells.items():
            source = "".join(notebook["cells"][index]["source"])
            if legacy:
                assert all(marker in source for marker in markers), (relative, index)
            else:
                assert not any(marker in source for marker in markers[1:]), (relative, index)
                assert "USAAIO_BOOK_ROOT" in source or "book_root" in source.lower(), (
                    relative,
                    index,
                )
    for relative in inventory["split_token_python_consumers"]:
        path = ROOT / relative
        assert path.is_file()
        assert _python_path_consumers(path), relative


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


def _division_parts(node: ast.AST) -> list[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return [*_division_parts(node.left), *_division_parts(node.right)]
    return [node]


def _repo_root_aliases(tree: ast.AST) -> set[str]:
    aliases = {"ROOT", "repo_root"}
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if isinstance(value, ast.Name) and value.id in aliases:
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in aliases:
                        aliases.add(target.id)
                        changed = True
    return aliases


def _is_repo_root_expression(node: ast.AST, aliases: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in aliases
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"resolve", "absolute"}
    ):
        return _is_repo_root_expression(node.func.value, aliases)
    return False


def _path_literal_values(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Path":
        return [
            arg.value
            for arg in node.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        ]
    return []


def _actual_python_root_accesses(path: Path) -> list[dict[str, object]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    aliases = _repo_root_aliases(tree)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    violations: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            if isinstance(parents.get(node), ast.BinOp):
                continue
            parts = _division_parts(node)
            anchor = parts[0]
            values = [value for part in parts[1:] for value in _path_literal_values(part)]
            if _is_repo_root_expression(anchor, aliases):
                if any(value in {"book1", "book2"} for value in values):
                    violations.append(
                        {"line": node.lineno, "kind": "hardcoded-repo-book-root"}
                    )
                elif any(_looks_like_content_path(value) for value in values):
                    violations.append(
                        {"line": node.lineno, "kind": "repo-root-path-join"}
                    )
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "joinpath"
            and _is_repo_root_expression(node.func.value, aliases)
            and any(
                value in {"book1", "book2"} or _looks_like_content_path(value)
                for arg in node.args
                for value in _path_literal_values(arg)
            )
        ):
            values = [
                value
                for arg in node.args
                for value in _path_literal_values(arg)
            ]
            kind = (
                "hardcoded-repo-book-root"
                if any(value in {"book1", "book2"} for value in values)
                else "repo-root-path-join"
            )
            violations.append({"line": node.lineno, "kind": kind})
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Path"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "syllabus.md"
        ):
            violations.append({"line": node.lineno, "kind": "literal-root-syllabus"})
        if isinstance(node, ast.Call):
            function = node.func
            name = (
                function.id
                if isinstance(function, ast.Name)
                else function.attr
                if isinstance(function, ast.Attribute)
                else ""
            )
            if name.startswith("check_") and any(
                _is_repo_root_expression(value, aliases)
                for value in [*node.args, *(kw.value for kw in node.keywords)]
            ):
                violations.append({"line": node.lineno, "kind": "unselected-checker-root"})
    return sorted(violations, key=lambda row: (int(row["line"]), str(row["kind"])))


def _actual_shell_root_accesses(path: Path) -> list[dict[str, object]]:
    patterns = {
        "root-find-units": re.compile(r"\bfind\s+units(?:\s|$)"),
        "root-find-units-mocktests": re.compile(r"\bfind\s+units\s+mocktests(?:\s|$)"),
        "root-for-units-mocktests": re.compile(
            r"\bfor\s+(?:dir|[A-Za-z_][A-Za-z0-9_]*)\s+in\s+units\s+mocktests\b"
        ),
        "root-find-variable-units": re.compile(
            r"\bfind\s+[\"']?\$(?:ROOT|repo_root)(?:/|\}/)units(?:[/\"'\s]|$)"
        ),
        "hardcoded-repo-book-root": re.compile(
            r"\$(?:ROOT|repo_root)(?:/|\}/)book[12](?:[/\"'\s]|$)"
        ),
    }
    violations: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        for kind, pattern in patterns.items():
            if pattern.search(line):
                violations.append({"line": line_number, "kind": kind})
    return violations


def _actual_repository_root_accesses(
    repo: Path = ROOT,
) -> dict[str, list[dict[str, object]]]:
    violations: dict[str, list[dict[str, object]]] = {}
    contract_tests = set(_inventory()["task0_contract_tests"])
    for base in (repo / "tools", repo / "scripts", repo / "tests"):
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            relative = path.relative_to(repo).as_posix()
            if relative in contract_tests:
                continue
            rows = _actual_python_root_accesses(path)
            if relative.startswith("tests/"):
                rows = [
                    row for row in rows if row["kind"] != "hardcoded-repo-book-root"
                ]
            if rows:
                violations[relative] = rows
    for path in sorted((repo / "scripts").rglob("*.sh")):
        rows = _actual_shell_root_accesses(path)
        if rows:
            violations[path.relative_to(repo).as_posix()] = rows
    return violations


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


@pytest.mark.parametrize(
    ("relative", "source", "line", "kind"),
    [
        ("tools/producer.py", 'ROOT.joinpath("units")\n', 1, "repo-root-path-join"),
        ("tools/producer.py", 'BASE = ROOT\nBASE / "units"\n', 2, "repo-root-path-join"),
        ("tools/producer.py", 'ROOT / Path("units")\n', 1, "repo-root-path-join"),
        ("tools/producer.py", "check_scope(root=ROOT)\n", 1, "unselected-checker-root"),
        (
            "tools/producer.py",
            'repo_root.resolve() / "curriculum"\n',
            1,
            "repo-root-path-join",
        ),
        (
            "scripts/producer.sh",
            'find "$repo_root/units" -name manifest.yaml\n',
            1,
            "root-find-variable-units",
        ),
        (
            "tools/producer.py",
            'ROOT / "book1"\n',
            1,
            "hardcoded-repo-book-root",
        ),
        (
            "scripts/producer.sh",
            'book_root="$repo_root/book1"\n',
            1,
            "hardcoded-repo-book-root",
        ),
    ],
)
def test_actual_scanner_rejects_root_access_mutations_in_discovered_producers(
    tmp_path: Path, relative: str, source: str, line: int, kind: str
) -> None:
    producer = tmp_path / relative
    producer.parent.mkdir(parents=True, exist_ok=True)
    producer.write_text(source, encoding="utf-8")

    assert _actual_repository_root_accesses(tmp_path) == {relative: [{"line": line, "kind": kind}]}


def test_actual_scanner_allows_bookspec_and_book_local_root_joins(tmp_path: Path) -> None:
    producer = tmp_path / "tools" / "producer.py"
    producer.parent.mkdir(parents=True)
    producer.write_text(
        'book.root / "units"\nselected_root.joinpath("curriculum")\n', encoding="utf-8"
    )
    shell = tmp_path / "scripts" / "producer.sh"
    shell.parent.mkdir(parents=True)
    shell.write_text('find "$book_root/units" -name manifest.yaml\n', encoding="utf-8")

    assert _actual_repository_root_accesses(tmp_path) == {}


def test_actual_producers_have_no_repository_root_content_access() -> None:
    actual = _actual_repository_root_accesses()
    expected_transition = _inventory()["repository_root_violations"]
    if (ROOT / "syllabus.md").exists():
        assert actual == expected_transition
        pytest.fail(
            "pre-cutover repository-root consumers remain and must be migrated atomically: "
            + ", ".join(actual)
        )
    assert actual == {}, actual


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


def test_book_local_generated_paths_are_ignored_without_ignoring_sources() -> None:
    ignored = (
        "book1/build/mock.pdf",
        "book2/build/unit.pdf",
        "book1/mocktests/r1-001/build/test.pdf",
        "book1/reference/r1-2026/paper.pdf",
        "book2/reference/r2-2026/day1.pdf",
        "book1/units/C10-competition-craft/data/heldout.csv",
        "book1/units/C10-competition-craft/practice/p15_contract.csv",
        "book1/mocktests/r1-001/data/p09_heldout.csv",
    )
    sources = (
        "book1/syllabus.md",
        "book2/syllabus.md",
        "book1/reference/analysis.md",
        "book2/reference/analysis.md",
        "book1/units/C10-competition-craft/data/make_dataset.py",
        "book1/mocktests/r1-001/data/gen_p09.py",
        "book1/mocktests/r1-001/problems/p09.ipynb",
    )

    for relative in ignored:
        proc = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", relative],
            cwd=ROOT,
            check=False,
        )
        assert proc.returncode == 0, relative
    for relative in sources:
        assert (ROOT / relative).is_file(), relative
        proc = subprocess.run(
            ["git", "check-ignore", "--no-index", "--quiet", relative],
            cwd=ROOT,
            check=False,
        )
        assert proc.returncode == 1, relative


def _solution_notebook(book: str) -> str:
    return json.dumps(
        {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "import os\n",
                        "from pathlib import Path\n",
                        "with Path(os.environ['VERIFY_TRACE']).open('a') as trace:\n",
                        "    trace.write('solution:' + os.environ['NOTEBOOK_PATH'] + '\\n')\n",
                    ],
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    )


def _clean_checkout_fixture(
    tmp_path: Path,
    *,
    verifier_mutator: Callable[[str], str] | None = None,
    ci_mutator: Callable[[str], str] | None = None,
    build_mutator: Callable[[str], str] | None = None,
) -> tuple[Path, Path]:
    repo = tmp_path / "clean-repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    source_verifier = ROOT / "scripts" / "verify-clean-checkout.sh"
    assert source_verifier.is_file(), "scripts/verify-clean-checkout.sh is the missing producer"
    verifier = repo / "scripts" / "verify-clean-checkout.sh"
    verifier.parent.mkdir(parents=True)
    verifier_source = source_verifier.read_text(encoding="utf-8")
    if verifier_mutator is not None:
        verifier_source = verifier_mutator(verifier_source)
    verifier.write_text(verifier_source, encoding="utf-8")
    verifier.chmod(0o755)
    (repo / "books.yaml").write_text(
        "books_version: 1\n"
        "books:\n"
        "  - {id: book1, number: 1, root: book1, depends_on: []}\n"
        "  - {id: book2, number: 2, root: book2, depends_on: [book1]}\n",
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        "[project]\nname = 'clean-checkout-fixture'\nversion = '0.0.0'\n",
        encoding="utf-8",
    )
    ci_source = """#!/usr/bin/env bash
set -euo pipefail
[[ ! -d .git ]]
[[ ! -e UNTRACKED_WORKTREE_SENTINEL ]]
[[ $(cat TRACKED_HEAD_SENTINEL) == "committed bytes" ]]
printf 'archive:no-git\\nci:archive-local\\n' >> "$VERIFY_TRACE"
BOOKS=(book1 book2)
for book in "${BOOKS[@]}"; do
  [[ -d "$book" ]]
  printf 'book:%s\\n' "$book" >> "$VERIFY_TRACE"
  bash scripts/build-pdf.sh "$book"
  [[ -s "$book/build/student.pdf" ]]
done
mapfile -t solutions < <(find book1 book2 -type f -name '*_solution.ipynb' | LC_ALL=C sort)
[[ ${#solutions[@]} -eq 2 ]]
for notebook in "${solutions[@]}"; do
  NOTEBOOK_PATH="$notebook" "$TEST_PYTHON" - "$notebook" <<'PY'
import json
import sys

namespace = {}
raw = json.load(open(sys.argv[1], encoding="utf-8"))
for cell in raw["cells"]:
    if cell["cell_type"] == "code":
        exec("".join(cell["source"]), namespace)
PY
done
"""
    if ci_mutator is not None:
        ci_source = ci_mutator(ci_source)
    ci = repo / "scripts" / "ci-local.sh"
    ci.write_text(ci_source, encoding="utf-8")
    ci.chmod(0o755)
    build_source = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "book=$1\n"
        'mkdir -p "$book/build"\n'
        "printf '%s\\n' '%PDF-1.4 fixture' > \"$book/build/student.pdf\"\n"
        'printf \'pdf:%s\\n\' "$book" >> "$VERIFY_TRACE"\n'
    )
    if build_mutator is not None:
        build_source = build_mutator(build_source)
    build = repo / "scripts" / "build-pdf.sh"
    build.write_text(build_source, encoding="utf-8")
    build.chmod(0o755)
    for book in ("book1", "book2"):
        solution = repo / book / "units" / f"{book}-unit" / "practice" / "p01_solution.ipynb"
        solution.parent.mkdir(parents=True)
        solution.write_text(_solution_notebook(book), encoding="utf-8")
        cache = repo / book / "reference"
        cache.mkdir(parents=True)
    (repo / "book1" / "reference" / "cache").mkdir()
    tracked_sentinel = repo / "TRACKED_HEAD_SENTINEL"
    tracked_sentinel.write_text("committed bytes\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "clean checkout fixture")
    tracked_sentinel.write_text("dirty staged bytes\n", encoding="utf-8")
    _git(repo, "add", tracked_sentinel.name)
    (repo / "UNTRACKED_WORKTREE_SENTINEL").write_text(
        "must not enter the tracked-HEAD archive\n", encoding="utf-8"
    )
    return repo, tmp_path / "trace.log"


def _run_clean_checkout_fixture(repo: Path, trace: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/verify-clean-checkout.sh"],
        cwd=repo,
        env={
            **os.environ,
            "TEST_PYTHON": sys.executable,
            "VERIFY_TRACE": str(trace),
            "USAAIO_REFERENCE_CACHE": str(repo / "book1/reference/cache"),
        },
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_complete_clean_checkout_trace(
    proc: subprocess.CompletedProcess[str], trace: Path
) -> None:
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lines = trace.read_text(encoding="utf-8").splitlines()
    assert lines.count("archive:no-git") == 1
    assert lines.count("ci:archive-local") == 1
    assert {line for line in lines if line.startswith("book:")} == {
        "book:book1",
        "book:book2",
    }
    assert {line for line in lines if line.startswith("pdf:")} == {
        "pdf:book1",
        "pdf:book2",
    }
    assert {line for line in lines if line.startswith("solution:")} == {
        "solution:book1/units/book1-unit/practice/p01_solution.ipynb",
        "solution:book2/units/book2-unit/practice/p01_solution.ipynb",
    }


def test_clean_checkout_verifier_executes_archive_local_ci_pdfs_and_all_solutions(
    tmp_path: Path,
) -> None:
    repo, trace = _clean_checkout_fixture(tmp_path)

    proc = _run_clean_checkout_fixture(repo, trace)

    _assert_complete_clean_checkout_trace(proc, trace)


def _comment_out_ci_invocation(source: str) -> str:
    lines = source.splitlines(keepends=True)
    mutated = [
        f"# mutation removed CI: {line}"
        if "ci-local.sh" in line and line.strip() and not line.lstrip().startswith("#")
        else line
        for line in lines
    ]
    assert mutated != lines, "fixture could not locate the archive-local CI invocation"
    return "".join(mutated)


def _replace_with_worktree_copy_verifier(_source: str) -> str:
    return """#!/usr/bin/env bash
set -euo pipefail
archive_dir=$(mktemp -d)
trap 'rm -rf "$archive_dir"' EXIT
cp -a . "$archive_dir/repo"
rm -rf "$archive_dir/repo/.git"
cd "$archive_dir/repo"
bash scripts/ci-local.sh
"""


def _replace_with_tracked_worktree_copy_verifier(_source: str) -> str:
    return """#!/usr/bin/env bash
set -euo pipefail
archive_dir=$(mktemp -d)
trap 'rm -rf "$archive_dir"' EXIT
git ls-files -z | tar --null -T - -cf - | tar -x -C "$archive_dir"
cd "$archive_dir"
bash scripts/ci-local.sh
"""


def _replace_pdf_output_with_empty_file(source: str) -> str:
    mutated = source.replace(
        "printf '%s\\n' '%PDF-1.4 fixture' > \"$book/build/student.pdf\"",
        'touch "$book/build/student.pdf"',
    )
    assert mutated != source, "fixture could not locate the nonempty PDF write"
    return mutated


@pytest.mark.parametrize(
    ("verifier_mutator", "ci_mutator", "build_mutator"),
    [
        pytest.param(_comment_out_ci_invocation, None, None, id="comment-only-verifier"),
        pytest.param(
            _replace_with_worktree_copy_verifier,
            None,
            None,
            id="worktree-copy-leaks-untracked-sentinel",
        ),
        pytest.param(
            _replace_with_tracked_worktree_copy_verifier,
            None,
            None,
            id="tracked-worktree-copy-leaks-staged-sentinel",
        ),
        pytest.param(
            None,
            lambda source: source.replace("BOOKS=(book1 book2)", "BOOKS=(book1)"),
            None,
            id="omitted-book",
        ),
        pytest.param(
            None,
            lambda source: source.replace("find book1 book2 -type f", "find book1 -type f").replace(
                "[[ ${#solutions[@]} -eq 2 ]]", "[[ ${#solutions[@]} -eq 1 ]]"
            ),
            None,
            id="omitted-solution",
        ),
        pytest.param(
            None,
            None,
            _replace_pdf_output_with_empty_file,
            id="zero-byte-pdf",
        ),
    ],
)
def test_clean_checkout_adversarial_noop_and_omission_mutations_fail(
    tmp_path: Path,
    verifier_mutator: Callable[[str], str] | None,
    ci_mutator: Callable[[str], str] | None,
    build_mutator: Callable[[str], str] | None,
) -> None:
    repo, trace = _clean_checkout_fixture(
        tmp_path,
        verifier_mutator=verifier_mutator,
        ci_mutator=ci_mutator,
        build_mutator=build_mutator,
    )

    proc = _run_clean_checkout_fixture(repo, trace)

    with pytest.raises((AssertionError, FileNotFoundError)):
        _assert_complete_clean_checkout_trace(proc, trace)


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
    existing_token = repo / "tests" / "token-policy.md"
    existing_token.parent.mkdir(parents=True)
    existing_token.write_text("pre-existing token path\n", encoding="utf-8")
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


def test_staged_scope_preflight_accepts_inventoried_top_level_rename(
    tmp_path: Path,
) -> None:
    repo = _init_scope_repo(tmp_path)
    syllabus = repo / "syllabus.md"
    syllabus.write_text("legacy syllabus\n", encoding="utf-8")
    _git(repo, "add", "syllabus.md")
    _git(repo, "commit", "-m", "add legacy syllabus")
    (repo / "book1").mkdir(exist_ok=True)
    _git(repo, "mv", "syllabus.md", "book1/syllabus.md")

    proc = _scope_proc(repo, "--preflight")

    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize(
    ("relative", "category"),
    [
        ("tests/new-token-notes.md", "token"),
        ("tests/.env.local", "env"),
        ("tests/api-secret.md", "secret"),
        ("tests/credential.txt", "credential"),
    ],
)
def test_staged_scope_rejects_new_token_and_secret_paths(
    tmp_path: Path, relative: str, category: str
) -> None:
    repo = _init_scope_repo(tmp_path)
    (repo / relative).write_text("forbidden\n", encoding="utf-8")
    _git(repo, "add", "-f", relative)

    proc = _scope_proc(repo, "--cached")

    assert proc.returncode != 0
    output = proc.stdout + proc.stderr
    assert relative in output
    diagnostic = output.replace(relative, "").lower()
    assert "protected" in diagnostic
    assert category in diagnostic


def test_staged_scope_allows_safe_named_path_under_same_tests_prefix(tmp_path: Path) -> None:
    repo = _init_scope_repo(tmp_path)
    relative = "tests/ordinary-notes.md"
    path = repo / relative
    path.write_text("ordinary test fixture\n", encoding="utf-8")
    _git(repo, "add", relative)

    proc = _scope_proc(repo, "--cached")

    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_staged_scope_rejects_modifying_preexisting_non_c8_token_path(tmp_path: Path) -> None:
    repo = _init_scope_repo(tmp_path)
    existing = repo / "tests" / "token-policy.md"
    existing.write_text("modified token path\n", encoding="utf-8")
    _git(repo, "add", existing.relative_to(repo).as_posix())

    proc = _scope_proc(repo, "--cached")

    assert proc.returncode != 0
    output = proc.stdout + proc.stderr
    assert "tests/token-policy.md" in output
    diagnostic = output.replace("tests/token-policy.md", "").lower()
    assert "protected" in diagnostic
    assert "token" in diagnostic


@pytest.mark.parametrize(
    "mutation",
    ["expected-root-resolution", "other-cell", "arbitrary-path-cell"],
)
def test_exact_c8_token_notebook_exception_is_cell_scoped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    repo = _init_scope_repo(tmp_path)
    old = repo / "units" / "C8-embeddings" / "lessons" / "01-tokens-and-embeddings.ipynb"
    new = repo / "book1" / old.relative_to(repo)
    new.parent.mkdir(parents=True)
    old.rename(new)
    notebook = json.loads(new.read_text(encoding="utf-8"))
    notebook["cells"][1]["source"] = [
        "import os\n",
        "from pathlib import Path\n",
        "ROOT = Path(os.environ['USAAIO_BOOK_ROOT']).resolve()\n",
    ]
    if mutation == "other-cell":
        notebook["cells"][2]["source"] = ["changed teaching body\n"]
    elif mutation == "arbitrary-path-cell":
        notebook["cells"][1]["source"] = [
            "import os\n",
            "from pathlib import Path\n",
            "SECRET = 'unrelated rewrite'\n",
            "ROOT = Path('/tmp/not-the-selected-book')\n",
        ]
    new.write_text(json.dumps(notebook), encoding="utf-8")
    _git(repo, "add", "-A")

    proc = _scope_proc(repo, "--cached")

    if mutation != "expected-root-resolution":
        assert proc.returncode != 0
        assert "cell" in (proc.stdout + proc.stderr).lower()
    else:
        assert proc.returncode == 0, proc.stdout + proc.stderr
        monkeypatch.setenv("USAAIO_BOOK_ROOT", str(repo / "book1"))
        execution = subprocess.run(
            [
                sys.executable,
                "-c",
                "".join(notebook["cells"][1]["source"])
                + f"\nassert ROOT == Path({str(repo / 'book1')!r}).resolve()\n",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert execution.returncode == 0, execution.stdout + execution.stderr
