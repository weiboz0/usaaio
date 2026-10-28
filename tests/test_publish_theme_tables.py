"""Plan 033 D3: the theme filter's table fixes (tools/publish_theme/panels.lua).

Run through `quarto pandoc` (the pandoc the editions use); skipped when Quarto is absent.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.books import load_book_catalog, unit_dir

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "tools/publish_theme/panels.lua"
BASE_COMMIT = "60b1247"  # main before Plan 033: the filter without the table fixes
READER = "markdown+tex_math_single_backslash-raw_tex"


def _quarto() -> str | None:
    found = shutil.which("quarto")
    if found:
        return found
    local = Path.home() / ".local/bin/quarto"
    return str(local) if local.is_file() else None


QUARTO = _quarto()
pytestmark = pytest.mark.skipif(QUARTO is None, reason="Quarto (quarto pandoc) is not installed")


def _latex(markdown: str, *extra: str, lua: Path = FILTER) -> str:
    proc = subprocess.run(
        [QUARTO, "pandoc", "-f", READER, "-t", "latex", "--lua-filter", str(lua), *extra],
        input=markdown, capture_output=True, text=True, check=True)
    return proc.stdout


def _widths(latex: str) -> list[float]:
    return [float(value) for value in re.findall(r"\\real\{([\d.]+)\}", latex)]


def _spec(latex: str) -> str:
    match = re.search(r"\\begin\{longtable\}\[\]\{(.*?)\}\n", latex)
    assert match, latex
    return match[1]


def _table(rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(row) + " |" for row in rows]
    lines.insert(1, "|" + "---|" * len(rows[0]))
    return "\n".join(lines) + "\n"


# --- (a) widths ----------------------------------------------------------------------------------

C9_P18 = """\
| Question | Best view | Evidence (your numbers) |
|---|---|---|
| "Are these two points genuine neighbors?" | | |
| "How far apart are these two regions, really?" | | |
| "Is a 1-D summary of this dataset usable for either question?" | | |
"""


def test_overflowing_natural_width_table_gets_wrapping_columns() -> None:
    latex = _latex(C9_P18)
    assert "p{(\\linewidth - 4\\tabcolsep)" in latex
    widths = _widths(latex)
    assert len(widths) == 3
    assert sum(widths) == pytest.approx(1, abs=0.002)
    # Proportional to the longest cell (62, 9, 23 characters), the short column floored at 0.15.
    assert widths[0] > widths[2] > widths[1] >= 0.15 - 0.0001


def test_table_that_fits_keeps_natural_width_columns() -> None:
    latex = _latex("| a | b | c |\n|---|---|---|\n| `np.zeros(3)` | short | text |\n")
    assert _spec(latex) == "@{}lll@{}"
    assert "\\real" not in latex


def test_explicit_widths_are_preserved() -> None:
    long_row = "x" * 80
    markdown = f"| a | b |\n|---|------|\n| {long_row} | 2 |\n"
    assert _widths(_latex(markdown)) == [0.3333, 0.6667]


def _wide(markdown: str, columns: int) -> list[float]:
    # --columns=1000: no line is "too long", so pandoc leaves every width at the default and
    # the filter's estimate decides.
    widths = _widths(_latex(markdown, "--columns=1000"))
    assert len(widths) == columns
    floor = min(0.15, 0.5 / columns)
    assert sum(widths) == pytest.approx(1, abs=0.002)
    assert min(widths) >= floor - 0.0001
    return widths


def test_nine_column_c8_p20_table_gets_feasible_widths() -> None:
    book = load_book_catalog(ROOT).by_id("book1")
    notebook = unit_dir(book.root, "C8-neural-training") / "practice" / "p20.ipynb"
    cell = "".join(json.loads(notebook.read_text())["cells"][0]["source"])
    table = "\n".join(line for line in cell.splitlines() if line.startswith("|")) + "\n"
    widths = _wide(table, 9)
    assert len(set(widths)) > 2  # not collapsed to equal widths


def test_twelve_column_table_gets_feasible_widths() -> None:
    header = [f"column heading {i}" if i % 3 == 0 else f"c{i}" for i in range(12)]
    rows = [header, ["a long cell of explanatory text"] + ["1"] * 11]
    widths = _wide(_table(rows), 12)
    assert widths[0] == max(widths)
    assert len(set(widths)) > 2


# --- (b), (c) break points -----------------------------------------------------------------------


def test_code_breaks_after_a_dot_everywhere() -> None:
    latex = _latex("Call `np.linalg.eig` or `x.5` but not `a. b` or `a..b`; `lr=0.05` keeps "
                   "its number whole.\n", "--wrap=none")
    assert "\\texttt{np.\\allowbreak{}linalg.\\allowbreak{}eig}" in latex
    assert "\\texttt{x.\\allowbreak{}5}" in latex
    assert "\\texttt{a. b}" in latex
    assert "\\texttt{a..\\allowbreak{}b}" in latex
    assert "\\texttt{lr=\\allowbreak{}0.05}" in latex


def test_table_code_breaks_and_small_size() -> None:
    latex = _latex(_table([["code", "more"],
                           ["`labels[heldout][:48]`", "`r2_001_data.val_rows(\"texture\")`"],
                           ["`parameter.requires_grad_(False)`", "`f(x)`"]]))
    assert ("{\\small\\texttt{labels\\allowbreak{}[\\allowbreak{}heldout\\allowbreak{}]"
            "\\allowbreak{}[\\allowbreak{}:\\allowbreak{}48\\allowbreak{}]}}") in latex
    assert ("{\\small\\texttt{r2\\_\\allowbreak{}001\\_\\allowbreak{}data\\allowbreak{}."
            "\\allowbreak{}val\\_\\allowbreak{}rows\\allowbreak{}(\"texture\")}}") in latex
    assert ("{\\small\\texttt{parameter\\allowbreak{}.\\allowbreak{}requires\\_\\allowbreak{}"
            "grad\\_\\allowbreak{}(\\allowbreak{}False)}}") in latex
    assert "{\\small\\texttt{f\\allowbreak{}(\\allowbreak{}x)}}" in latex
    assert "{\\small\\texttt{lr=\\allowbreak{}0.05}}" in _latex(_table([["config"], ["`lr=0.05`"]]))


def test_table_plain_text_breaks_after_slash_and_inner_dash() -> None:
    latex = _latex(_table([["file", "values"],
                           ["lessons/02-normal-eq.ipynb", "-1 and x-1 and a - b"]]), "--wrap=none")
    assert "lessons/\\allowbreak{}02-\\allowbreak{}normal-\\allowbreak{}eq.ipynb" in latex
    assert "-1 and x-\\allowbreak{}1 and a - b" in latex  # a leading minus is never stranded


def test_digit_runs_in_table_cells_do_not_break() -> None:
    """The digit-run break did not ship (Plan 033 D3 (c)): no box over 5 pt survived without it."""
    latex = _latex(_table([["mean", "std"], ["0.028217535155514877", "0.024437102507298938"]]))
    assert "0.028217535155514877 & 0.024437102507298938" in latex


# --- outside tables ------------------------------------------------------------------------------

PROSE = r"""# A heading

Prose with `a_b(c)`, `x=1`, `np.linalg.eig`, `[1, 2]`, `labels[i]` and `a.b(c)`,
lessons/01-x.ipynb, -1, x-1, 50% of $5 & #1 → done ∀x.

- item `f(x, y)` and **bold** `u/v+w`

```python
y = np.dot(a, b)
```

$$a = b$$
"""


def test_outside_tables_only_the_global_dot_rule_changes(tmp_path: Path) -> None:
    """Prose and code outside tables match the pre-Plan-033 filter, apart from the global break
    after `.` before a letter or digit; a table elsewhere in the document changes nothing."""
    git = shutil.which("git")
    old = subprocess.run([git, "show", f"{BASE_COMMIT}:tools/publish_theme/panels.lua"],
                         cwd=ROOT, capture_output=True, text=True, check=False) if git else None
    if old is None or old.returncode != 0:
        pytest.skip(f"git history with {BASE_COMMIT} is not available")
    new = _latex(PROSE, "--wrap=none")
    with_table = _latex(PROSE + "\n" + C9_P18, "--wrap=none")
    assert with_table.startswith(new.rstrip("\n"))
    lua = tmp_path / "panels-before.lua"
    lua.write_text(old.stdout, encoding="utf-8")
    before = _latex(PROSE, "--wrap=none", lua=lua)
    assert new != before  # the dot rule is visible here
    assert new.replace(".\\allowbreak{}", ".") == before.replace(".\\allowbreak{}", ".")
    assert new.replace("np.\\allowbreak{}linalg.\\allowbreak{}eig", "np.linalg.eig") \
        .replace("a.\\allowbreak{}b(", "a.b(") == before
