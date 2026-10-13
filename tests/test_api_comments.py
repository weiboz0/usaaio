"""Plan 032 D4: tests for tools/checks/api_comments.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.checks.api_comments import (
    Waiver,
    analyze,
    check_api_comments,
    load_config,
    markdown_code_spans,
    required_identifiers,
)

BASE_CONFIG = {
    "enforce": True,
    "waiver_cap_percent": 2,
    "mock_rules": [1],
    "module_aliases": {"numpy": "np", "matplotlib.pyplot": "plt"},
    "baseline": {"builtins": ["print", "len", "range"], "methods": ["append", "split"]},
    "semantic_keywords": ["axis", "keepdims", "dtype"],
    "positional_callees": ["arange"],
    "positional_words": ["step"],
    "graduation_units": 3,
    "graduated": [],
    "no_reminder": [],
    "method_families": {"roots": {"np": "ndarray"}, "keyed": []},
    "named_idioms": {"book-root-finder": {"callees": ["os.environ.get"]}},
}


def config(**overrides):
    return load_config({**BASE_CONFIG, **overrides})


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def code(source: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "source": source, "outputs": [],
            "execution_count": None}


def write(root: Path, rel: str, *cells: dict) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    notebook = {"cells": list(cells), "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    for index, cell in enumerate(notebook["cells"]):
        cell.setdefault("id", f"c{index}")
    path.write_text(json.dumps(notebook), encoding="utf-8")
    return path


def card(new=(), also=(), heading="Code in this unit") -> dict:
    lines = ["<!-- api-card -->", f"## {heading}", "", "**New in this unit:**"]
    lines += [f"- `{name}` — meaning" for name in new]
    lines += ["", "**Also used here (met earlier):**"]
    lines += [f"- `{name}` — reminder (U1)" for name in also]
    return md("\n".join(lines))


def failing(analysis, rule=None):
    return [s for s in analysis.sites if s.failing and (rule is None or s.rule == rule)]


def run(root, waivers=(), **overrides):
    return analyze(root, config=config(**overrides), waivers=list(waivers))


# --------------------------------------------------------------------------- rule 1


def test_rule1_same_line_comment_names_callee(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb",
          code("import numpy as np\nx = np.argmax([1, 3])  # np.argmax: index of the largest"))
    assert failing(run(tmp_path)) == []


def test_rule1_missing_comment_fails(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code("import numpy as np\nx = np.argmax([1, 3])"))
    sites = failing(run(tmp_path), rule=1)
    assert [(s.callee, s.cell, s.line) for s in sites] == [("np.argmax", 0, 2)]


def test_rule1_unrelated_comment_does_not_count(tmp_path):
    # The survey's false match: a comment next to np.zeros_like that does not name it.
    write(tmp_path, "units/01-U1/lesson.ipynb",
          code("import numpy as np\ny = np.zeros_like([1.0])  # start the running total"))
    assert [s.callee for s in failing(run(tmp_path))] == ["np.zeros_like"]


def test_rule1_comment_block_directly_above(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "import numpy as np\n"
        "# np.linalg.solve: solve A x = b\n"
        "# for the unknown vector x\n"
        "x = np.linalg.solve([[1.0]], [2.0])\n"
        "\n"
        "# a block separated by a blank line does not count\n"
        "\n"
        "y = np.cumsum([1, 2])\n"
    ))
    assert [s.callee for s in failing(run(tmp_path))] == ["np.cumsum"]


def test_hash_inside_string_is_not_a_comment(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb",
          code('import numpy as np\nprint("# argmax"); x = np.argmax([1])'))
    assert [s.callee for s in failing(run(tmp_path))] == ["np.argmax"]


def test_alias_resolution(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "import numpy as numpy_alias\n"
        "from numpy.linalg import solve as linsolve\n"
        "a = numpy_alias.linalg.solve([[1.0]], [1.0])  # solve: A x = b\n"
        "b = linsolve([[1.0]], [1.0])\n"
        "import matplotlib.pyplot\n"
        "matplotlib.pyplot.close('all')\n"
    ))
    analysis = run(tmp_path)
    keys = [(s.rule, s.callee, s.written) for s in analysis.sites]
    assert (1, "np.linalg.solve", "numpy_alias.linalg.solve") in keys
    assert (1, "plt.close", "matplotlib.pyplot.close") in keys
    # The second spelling is the same callee: not a new book-first site.
    assert not any(s.written == "linsolve" for s in analysis.sites)


def test_baseline_and_local_definitions_are_skipped(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "def helper(x):\n    return x\n"
        "items = []\nitems.append(len(range(3)))\nprint(helper(1))\n"
    ))
    assert run(tmp_path).sites == []


# --------------------------------------------------------------------------- markdown windows


@pytest.mark.parametrize(
    ("cells", "explained"),
    [
        ([md("Use `np.argmax` here."), code("import numpy as np\nnp.argmax([1])")], True),
        ([code("import numpy as np\nnp.argmax([1])"), md("`np.argmax(v)` returns an index.")], True),
        ([md("`np.argmax`"), md("text"), code("import numpy as np\nnp.argmax([1])")], True),
        ([md("`np.argmax`"), md("a"), md("b"), code("import numpy as np\nnp.argmax([1])")], False),
        ([md("argmax without backticks"), code("import numpy as np\nnp.argmax([1])")], False),
    ],
)
def test_markdown_windows(tmp_path, cells, explained):
    write(tmp_path, "units/01-U1/lesson.ipynb", *cells)
    assert (failing(run(tmp_path)) == []) is explained


def test_markdown_inside_latex_does_not_count(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb",
          md(r"The rule $`np.argmax`$ and \(`np.argmax`\) are math."),
          code("import numpy as np\nnp.argmax([1])"))
    assert [s.callee for s in failing(run(tmp_path))] == ["np.argmax"]
    assert markdown_code_spans("a $x `y`$ b `z`") == ["z"]


def test_markdown_method_form(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb",
          md("Call `v.cumsum()` for running totals."),
          code("import numpy as np\nv = np.ones(3)  # np.ones: all-ones\nv.cumsum()"))
    assert failing(run(tmp_path)) == []


# --------------------------------------------------------------------------- rule 2


def test_rule2_new_semantic_keyword(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "import numpy as np\n"
        "s = np.sum([1])  # np.sum: total\n"
        "t = np.sum([[1]], axis=0)\n"
        "u = np.sum([[1]], keepdims=True)  # keepdims=True keeps the axis\n"
        "v = np.sum([[1]], axis=1)\n"
    ))
    sites = [(s.element, s.explained) for s in run(tmp_path).sites if s.rule == 2]
    assert sites == [("axis", False), ("keepdims", True)]


def test_rule2_styling_keyword_is_ignored_and_positional_mode_counts(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "import numpy as np\n"
        "a = np.arange(5)  # np.arange: 0..4\n"
        "b = np.arange(2, 9, 3)  # start 2, step 3\n"
        "c = np.arange(1, 4)\n"
        "np.sum([1], where=True, color='r')  # np.sum: total\n"
    ))
    sites = [(s.element, s.explained) for s in run(tmp_path).sites if s.rule == 2]
    assert sites == [("npos=3", True), ("npos=2", False)]


# --------------------------------------------------------------------------- rule 3


def _two_units(tmp_path, second_cells, second_card=None):
    write(tmp_path, "units/01-U1/lesson.ipynb",
          code("import numpy as np\nnp.cumsum([1])  # np.cumsum: running total"))
    cells = list(second_cells) + ([second_card] if second_card else [])
    write(tmp_path, "units/02-U2/lesson.ipynb", *cells)


def test_rule3_unit_first_needs_reminder(tmp_path):
    _two_units(tmp_path, [code("import numpy as np\nnp.cumsum([2])\nnp.cumsum([3])")])
    sites = failing(run(tmp_path), rule=3)
    assert [(s.unit, s.line) for s in sites] == [("U2", 2)]


def test_rule3_inline_reminder(tmp_path):
    _two_units(tmp_path, [code("import numpy as np\nnp.cumsum([2])  # np.cumsum: running total")])
    assert failing(run(tmp_path)) == []


def test_rule3_card_also_used(tmp_path):
    _two_units(tmp_path, [code("import numpy as np\nnp.cumsum([2])")],
               second_card=card(also=["np.cumsum"]))
    analysis = run(tmp_path)
    assert failing(analysis) == []
    assert [s.evidence for s in analysis.sites if s.rule == 3] == ["card-also"]


def test_no_reminder_and_graduated_callees(tmp_path):
    for number in range(1, 6):
        write(tmp_path, f"units/0{number}-U{number}/lesson.ipynb",
              code("import numpy as np\nnp.cumsum([1])  # np.cumsum\nnp.diff([1, 2])"
                   + ("  # np.diff: steps" if number == 1 else "")))
    analysis = run(tmp_path, graduated=["np.cumsum"], no_reminder=["np.diff"])
    rule3 = [(s.unit, s.callee, s.exempt) for s in analysis.sites if s.rule == 3]
    # np.cumsum graduates once it has been used in three earlier units (U4 onward).
    assert ("U2", "np.cumsum", None) in rule3
    assert ("U3", "np.cumsum", None) in rule3
    assert ("U4", "np.cumsum", "graduated") in rule3
    assert all(exempt == "no-reminder" for _, callee, exempt in rule3 if callee == "np.diff")


# --------------------------------------------------------------------------- harness (rule 4)


def test_checks_cell_is_outside_first_use(tmp_path):
    write(tmp_path, "units/01-U1/practice/p01.ipynb",
          code("# Checks: the answer has the right shape\nimport numpy as np\n"
               "assert np.isclose(1.0, 1.0, atol=0, rtol=0)"))
    write(tmp_path, "units/02-U2/lesson.ipynb",
          code("import numpy as np\nnp.isclose(1, 1, atol=0, rtol=0)"))
    analysis = run(tmp_path)
    assert [(s.rule, s.unit) for s in analysis.sites] == [(1, "U2")]


def test_checks_marker_rejected_in_lessons_and_when_misplaced(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code("# Checks: x\nx = 1"))
    write(tmp_path, "units/01-U1/lessons/01-a.ipynb", code("y = 1\n# Checks: late"))
    write(tmp_path, "units/01-U1/practice/p01_solution.ipynb", code("# Checks: fine\nassert True"))
    errors = run(tmp_path).errors
    assert any("lesson.ipynb:cell 0" in e and "not allowed" in e for e in errors)
    assert any("01-a.ipynb:cell 0:line 2" in e and "misplaced" in e for e in errors)
    assert not any("p01_solution" in e for e in errors)


def test_boilerplate_block_ends_at_blank_line(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "# Boilerplate: find the book root\n"
        "import os\n"
        "root = os.environ.get('USAAIO_BOOK_ROOT')\n"
        "\n"
        "import numpy as np\n"
        "np.cumsum([1])\n"
    ))
    analysis = run(tmp_path)
    assert [s.callee for s in analysis.sites] == ["np.cumsum"]
    assert "os.environ.get" in analysis.harness_only


def test_boilerplate_block_exempts_only_idiom_callees(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "# Boilerplate: find the book root\n"
        "import os\n"
        "import numpy as np\n"
        "root = os.environ.get('USAAIO_BOOK_ROOT')\n"
        "np.cumsum([1])\n"
        "np.diff([1])  # np.diff: steps\n"
    ))
    analysis = run(tmp_path)
    # os.environ.get is in the idiom's callee set; the other calls follow rules 1-3.
    assert [(s.callee, s.explained) for s in analysis.sites] == [
        ("np.cumsum", False), ("np.diff", True),
    ]
    assert "os.environ.get" in analysis.harness_only


def test_mock_statement_checks_marker_only_on_paper_provided_cells(tmp_path):
    provided = "# Checks: provided setup\nimport numpy as np\nx = np.zeros(2)"
    write(tmp_path, "mocktests/m1/problems/p01.ipynb",
          code(provided + "\n"),  # trailing newline only: still mirrored
          code("# Checks: contract self-check\nassert True"))
    write(tmp_path, "mocktests/m1/solutions/p01_solution.ipynb",
          code(provided), code("# Checks: answer pin\nANSWER = 3\nassert ANSWER == 3"))
    errors = [e for e in run(tmp_path).errors if "paper-provided" in e]
    assert len(errors) == 1
    assert "problems/p01.ipynb:cell 1:" in errors[0]


def test_receiver_types_follow_execution_order(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "import numpy as np\n"
        "names = []\n"
        "names.append(1)\n"
        "names = np.array(names)  # np.array: list to array\n"
    ), code(
        "grid = np.zeros(2)  # np.zeros: zeros\n"
        "grid.append(0)\n"
        "grid = []\n"
        "grid.append(1)\n"
    ))
    sites = [(s.callee, s.cell, s.line) for s in run(tmp_path).sites]
    # Only the append that runs while `grid` is an array is keyed ndarray.append; the
    # later re-binding of `names` does not reach back to the earlier list append.
    assert sites == [("np.array", 0, 4), ("np.zeros", 1, 1), ("ndarray.append", 1, 2)]


def test_three_argument_where_is_a_new_positional_mode(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "import numpy as np\n"
        "i = np.where([True, False])  # np.where(cond): indices of True\n"
        "a = np.where([True, False], 1, 0)\n"
        "b = np.where([True], [1, 2], 0)\n"
        "c = np.sum([1], where=[True])  # np.sum: total (the where= keyword is not a mode)\n"
    ), code(
        "import numpy as np\n"
        "d = np.where([True], 1, 0)  # np.where(cond, a, b): a where True, else b\n"
    ))
    sites = [(s.element, s.explained) for s in run(tmp_path, positional_callees=["where"]).sites
             if s.rule == 2]
    assert sites == [("npos=3", False)]
    write(tmp_path, "units/01-U1/lesson.ipynb", code(
        "import numpy as np\n"
        "i = np.where([True, False])  # np.where(cond): indices of True\n"
        "a = np.where([True, False], 1, 0)  # np.where(cond, a, b): a if cond, else b\n"
    ))
    sites = [(s.element, s.explained) for s in run(tmp_path, positional_callees=["where"]).sites
             if s.rule == 2]
    assert sites == [("npos=3", True)]


def test_magic_lines_are_rejected(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code("%matplotlib inline\nx = 1"))
    assert any("magic" in error for error in run(tmp_path).errors)


# --------------------------------------------------------------------------- statements


def test_statement_rules(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb",
          code("import numpy as np\nnp.sum([1])  # np.sum: total"))
    write(tmp_path, "units/01-U1/practice/p01.ipynb",
          md("Implement `standardize(x)` and define `def scale(v):`."),
          code(
              "import numpy as np\n"
              "a = np.sum([[1]], axis=0)  # axis=0 sums down columns\n"
              "b = np.cumsum([1])  # np.cumsum feeds standardize\n"
              "# YOUR CODE HERE (call standardize)\n"
              "def standardize(x):\n    ...\n"
          ))
    analysis = run(tmp_path)
    errors = [e for e in analysis.errors if "p01.ipynb" in e]
    assert any("keyword only" in e and "line 2" in e for e in errors)
    assert any("required identifier(s) standardize" in e and "line 3" in e for e in errors)
    assert len(errors) == 2  # the scaffold instruction is not call evidence
    assert not [s for s in analysis.sites if s.rule == 2 and s.kind == "statement"]


def test_required_identifier_extractor():
    notebook = {"cells": [
        md("Write `encode` so that it calls `np.sum`. Then `other`.\n\nUse `def decode(` too."),
        code("class Model:\n    '''doc'''\n    pass\n\ndef helper():\n    return 1\n"
             "def todo():\n    raise NotImplementedError\n"),
    ]}
    assert required_identifiers(notebook) == {"encode", "decode", "Model", "todo"}


# --------------------------------------------------------------------------- waivers and modes


def test_waiver_cap_and_stale_waivers(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb",
          code("import numpy as np\nnp.cumsum([1])\nnp.diff([1])"))
    rel = f"{tmp_path.name}/units/01-U1/lesson.ipynb"
    waivers = [Waiver(rel, 0, "np.cumsum", "too long"), Waiver(rel, 5, "np.diff", "stale")]
    report = check_api_comments(tmp_path, config=config(), waivers=waivers)
    assert not report.ok
    assert any("waivers 1 exceed 2%" in e for e in report.errors)
    assert any("stale waiver" in e for e in report.errors)
    assert any("np.diff" in e and "rule 1" in e for e in report.errors)
    assert not any("np.cumsum" in e and "rule 1" in e for e in report.errors)


def test_report_mode_passes_with_findings(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code("import numpy as np\nnp.cumsum([1])"))
    report = check_api_comments(tmp_path, config=config(enforce=False), waivers=[])
    assert report.ok and not report.errors
    assert any("np.cumsum" in w for w in report.warnings)
    assert any("report mode" in w for w in report.warnings)


def test_guard_protected_notebook_uses_the_card(tmp_path):
    rel_root = tmp_path.name
    write(tmp_path, "units/01-U1/lesson.ipynb", card(new=["np.cumsum"]))
    write(tmp_path, "units/01-U1/lessons/01-tokens.ipynb",
          code("import numpy as np\nnp.cumsum([1])\nnp.sum([1])  # np.sum\nnp.sum([[1]], axis=0)"))
    guard = Waiver(f"{rel_root}/units/01-U1/lessons/01-tokens.ipynb", None, None, "guard-protected")
    analysis = run(tmp_path, waivers=[guard])
    assert failing(analysis) == []
    assert analysis.waived == 0 and analysis.guard_waived == 1


# --------------------------------------------------------------------------- cards


def test_card_checks(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb",
          code("import numpy as np\nnp.cumsum([1])  # np.cumsum\nnp.diff([1])  # np.diff"),
          card(new=["np.cumsum", "np.diff"]))
    write(tmp_path, "units/02-U2/lesson.ipynb",
          code("import numpy as np\nnp.cumsum([1])\nnp.ones(2)  # np.ones: all ones"),
          card(new=["np.cumsum"], also=["np.cumsum", "np.diff", "np.isclose"]))
    write(tmp_path, "units/02-U2/review.ipynb", card(new=["np.ones"], also=["np.cumsum"]))
    write(tmp_path, "units/02-U2/practice/p01.ipynb",
          code("# Checks: harness\nimport numpy as np\nnp.isclose(1, 1, atol=0, rtol=0)"))
    errors = run(tmp_path).errors
    assert not any("01-U1" in e for e in errors)
    u2 = [e for e in errors if "02-U2" in e]
    assert any("book-first callee np.ones missing" in e for e in u2)
    assert any("'New in this unit' lists np.cumsum, not book-first" in e for e in u2)
    assert any("'Also used here' lists np.diff, not a rule-3 callee" in e for e in u2)
    assert any("harness-only callee np.isclose" in e for e in u2)
    assert any("review card entries differ" in e for e in u2)


def test_missing_card_and_card_not_last(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code("x = 1"))
    write(tmp_path, "units/02-U2/lesson.ipynb", card(), code("x = 2"))
    errors = run(tmp_path).errors
    assert any("01-U1/lesson.ipynb: missing API card" in e for e in errors)
    assert any("02-U2/lesson.ipynb:cell 0: the API card must be" in e for e in errors)


# --------------------------------------------------------------------------- whole-book order


def test_first_use_is_computed_across_the_book(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code("x = 1"))
    write(tmp_path, "units/01-U1/review.ipynb", code("import numpy as np\nnp.cumsum([1])"))
    write(tmp_path, "units/01-U1/practice/p02_solution.ipynb",
          code("import numpy as np\nnp.cumsum([1])\nnp.diff([1])"))
    write(tmp_path, "units/01-U1/practice/p10.ipynb", code("import numpy as np\nnp.diff([1])"))
    write(tmp_path, "units/02-U2/lesson.ipynb", code("import numpy as np\nnp.cumsum([1])"))
    sites = [(s.rule, s.callee, Path(s.rel).name) for s in run(tmp_path).sites]
    # Statements (p10) come before solutions (p02_solution) inside a unit.
    assert sites == [
        (1, "np.cumsum", "review.ipynb"),
        (1, "np.diff", "p10.ipynb"),
        (3, "np.cumsum", "lesson.ipynb"),
    ]


def test_book2_counts_book1_explanations(tmp_path):
    (tmp_path / "books.yaml").write_text(
        "books_version: 1\nbooks:\n"
        "  - {id: book1, number: 1, root: book1, depends_on: []}\n"
        "  - {id: book2, number: 2, root: book2, depends_on: [book1]}\n",
        encoding="utf-8",
    )
    write(tmp_path, "book1/units/01-F1/lesson.ipynb",
          code("import numpy as np\nnp.cumsum([1])  # np.cumsum: running total"))
    write(tmp_path, "book2/units/B2-019/lesson.ipynb",
          code("import numpy as np\nnp.cumsum([1])\nnp.diff([1])"))
    write(tmp_path, "book2/mocktests/r2-001/problems/p01.ipynb",
          code("import numpy as np\nnp.diff([1])\nnp.roll([1], 1)"))
    analysis = run(tmp_path / "book2")
    assert [(s.rule, s.callee, s.book) for s in analysis.sites] == [
        (3, "np.cumsum", "book2"),
        (1, "np.diff", "book2"),
        (1, "np.roll", "book2"),  # mocks apply rule 1 only (mock_rules)
    ]
    assert analysis.sites[0].rel == "book2/units/B2-019/lesson.ipynb"


def test_cli_registration():
    from tools.cli import SUBCOMMANDS

    assert SUBCOMMANDS["api-comments-check"][1] is check_api_comments


def test_shipped_configuration_loads():
    loaded = load_config()
    assert loaded.enforce is True
    assert {"axis", "dim", "keepdims", "size", "dtype", "device"} <= loaded.semantic_keywords
    assert not (loaded.graduated & loaded.no_reminder)
    assert loaded.graduation_units == 3  # D1 rule 3: used in at least three earlier units
    assert "where" in loaded.positional_callees
    assert {"os.environ.get", "pathlib.Path"} <= loaded.idiom_callees
    assert "torch.set_num_threads" not in loaded.idiom_callees


def test_card_must_open_with_unnumbered_heading(tmp_path):
    write(tmp_path, "units/01-U1/lesson.ipynb", code("x = 1"), card(heading="Code in this unit"))
    write(tmp_path, "units/02-U2/lesson.ipynb", code("x = 1"), card(heading="9. Code"))
    errors = run(tmp_path).errors
    assert not any("01-U1" in e and "heading" in e for e in errors)
    assert any("02-U2" in e and "unnumbered '## ' heading" in e for e in errors)
