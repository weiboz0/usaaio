"""Plan 032 D5: tests for scripts/verify-comment-only.py on fixture notebooks."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify-comment-only.py"
_spec = importlib.util.spec_from_file_location("verify_comment_only", SCRIPT)
verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify)

LESSON = "book1/units/01-U1/lesson.ipynb"
STATEMENT = "book1/units/01-U1/practice/p01.ipynb"
SOLUTION = "book1/units/01-U1/practice/p01_solution.ipynb"


def md(source, cell_id=None):
    cell = {"cell_type": "markdown", "metadata": {}, "source": source}
    if cell_id:
        cell["id"] = cell_id
    return cell


def code(source, cell_id=None):
    cell = {"cell_type": "code", "metadata": {}, "source": source, "outputs": [],
            "execution_count": None}
    if cell_id:
        cell["id"] = cell_id
    return cell


def notebook(*cells, minor=5):
    return {"cells": list(cells), "metadata": {}, "nbformat": 4, "nbformat_minor": minor}


BASE = {
    LESSON: notebook(
        md("# Lesson\n\nIntro.", "m0"),
        code("import numpy as np\nx = np.cumsum([1, 2])  # running total", "c1"),
        md("## Checkpoint Answers\n\n1. yes", "m2"),
    ),
    STATEMENT: notebook(
        md("Implement `standardize(x)`.", "s0"),
        code("import numpy as np\nv = np.ones(3)\n", "s1"),
    ),
    SOLUTION: notebook(
        code("import numpy as np\nv = np.ones(3)", "a0"),
        md("### Answer check", "a1"),
        code("assert v.sum() == 3", "a2"),
    ),
}


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def _write(root, notebooks):
    for rel, nb in notebooks.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(nb, indent=1), encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    _write(tmp_path, BASE)
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    return tmp_path


def run(repo, changes, capsys):
    notebooks = copy.deepcopy(BASE)
    for rel, mutate in changes.items():
        mutate(notebooks[rel])
    _write(repo, notebooks)
    code_ = verify.main(["--base", "main", "--root", str(repo)])
    return code_, capsys.readouterr().err


def set_source(index, source):
    def mutate(nb):
        nb["cells"][index]["source"] = source
    return mutate


def append(cell, at=None):
    def mutate(nb):
        nb["cells"].insert(len(nb["cells"]) if at is None else at, cell)
    return mutate


CARD = "<!-- api-card -->\n## Code in this unit\n\n**New in this unit:**\n- `np.cumsum` — totals"


def test_unchanged_tree_passes(repo, capsys):
    assert run(repo, {}, capsys)[0] == 0


def test_added_comments_and_card_pass(repo, capsys):
    status, err = run(repo, {
        LESSON: lambda nb: (
            set_source(1, "import numpy as np\n# np.cumsum: running totals of a list\n"
                          "x = np.cumsum([1, 2])  # running total")(nb),
            append(md(CARD, "card"))(nb),
        ),
        STATEMENT: set_source(1, "import numpy as np\nv = np.ones(3)  # np.ones: all-ones vector\n"),
    }, capsys)
    assert status == 0, err


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({LESSON: set_source(1, "import numpy as np\nx = np.cumsum([1, 3])  # running total")},
         "(a) code changed"),
        ({LESSON: set_source(1, '"""doc"""\nimport numpy as np\nx = np.cumsum([1, 2])  # running total')},
         "(a) code changed"),
        ({LESSON: set_source(1, "import numpy as np\nx = np.cumsum([1, 2])  # running sum")},
         "(b) a pre-existing comment"),
        ({LESSON: set_source(0, "# Lesson\n\nIntro!")}, "(c) pre-existing markdown"),
        ({LESSON: append(md("Extra.", "new"))}, "(c) new cell lacks"),
        ({LESSON: append(md(CARD, "card"), at=1)}, "appended at the end"),
        ({SOLUTION: append(md(CARD, "card"), at=0)}, "API cards belong"),
        ({LESSON: append(md("<!-- api-card -->\n## 4. Code", "card"))}, "unnumbered"),
        ({LESSON: append(md("<!-- api-teach -->\n## New topic", "t"), at=2)}, "must not add headings"),
        ({SOLUTION: append(code("# api-teach\nx = 1", "t"))}, "after '### Answer check'"),
        ({LESSON: lambda nb: nb["cells"].reverse()}, "relative order"),
        ({LESSON: lambda nb: nb["cells"][1].update(id="renamed")}, "missing or lost its id"),
        ({LESSON: set_source(1, ["import numpy as np\n", "x = np.cumsum([1, 2])  # running total"])},
         "source representation"),
        ({STATEMENT: set_source(1, "import numpy as np\n# np.ones: ones\n# second line\nv = np.ones(3)\n")},
         "spans several lines"),
        ({STATEMENT: set_source(1, "import numpy as np\nv = np.ones(3)  # np.ones, then standardize\n")},
         "required identifier(s) standardize"),
        ({STATEMENT: lambda nb: nb["cells"][1].update(outputs=[{"output_type": "stream",
                                                                "name": "stdout", "text": "1"}])},
         "has outputs"),
    ],
)
def test_violations(repo, capsys, changes, expected):
    status, err = run(repo, changes, capsys)
    assert status == 1
    assert expected in err, err


def test_index_pinned_cells_keep_their_index(repo, capsys, monkeypatch):
    monkeypatch.setitem(verify.INDEX_PINNED, LESSON, (1,))
    status, err = run(repo, {LESSON: append(md("<!-- api-teach -->\nMore.", "t"), at=1)}, capsys)
    assert status == 1
    assert "index-referenced cell moved" in err
    assert "inserted before index-referenced cell" in err


def test_teaching_cell_after_pinned_cell_passes(repo, capsys, monkeypatch):
    monkeypatch.setitem(verify.INDEX_PINNED, LESSON, (1,))
    status, err = run(repo, {LESSON: append(md("<!-- api-teach -->\nMore.", "t"), at=2)}, capsys)
    assert status == 0, err


def test_id_less_notebooks(repo, capsys):
    rel = "book1/units/01-U1/practice/p02_solution.ipynb"
    base = notebook(code("x = 1"), md("### Answer check"), code("assert x == 1"), minor=4)
    _write(repo, {rel: base})
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "v44")
    head = copy.deepcopy(base)
    head["cells"][0]["source"] = "x = 1  # x: the answer"
    _write(repo, {rel: head})
    assert verify.main(["--base", "HEAD", "--root", str(repo)]) == 0
    head["cells"].insert(1, code("# api-teach\ny = 2", "fresh"))
    _write(repo, {rel: head})
    assert verify.main(["--base", "HEAD", "--root", str(repo)]) == 1
    assert "must not carry ids" in capsys.readouterr().err


def test_new_and_deleted_notebooks_fail(repo, capsys):
    (repo / SOLUTION).unlink()
    _write(repo, {"book1/units/01-U1/practice/p09.ipynb": notebook(code("x = 1", "z"))})
    assert verify.main(["--base", "main", "--root", str(repo)]) == 1
    err = capsys.readouterr().err
    assert "notebook deleted" in err and "new notebook" in err
