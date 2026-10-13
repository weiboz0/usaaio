#!/usr/bin/env python3
"""Plan 032 D5: verify that a branch changes notebooks by comments and marked cells only.

Compares every notebook under `book*/units` and `book*/mocktests` in the working tree with
its counterpart at `--base <ref>`:

(a) pre-existing code cells keep an identical `ast.dump` (docstrings would change it);
(b) every comment token at the base survives, in order, in the same cell;
(c) pre-existing markdown cells are byte-identical; new cells start with a marker
    (`<!-- api-card -->`, `<!-- api-teach -->`, or `# api-teach` for code);
(d) pre-existing cells keep their ids and relative order; index-pinned cells (D8) keep their
    index; cards are appended at the end; teaching cells sit after the last pinned cell;
    new cells get fresh ids; `nbformat.validate` passes; student notebooks keep empty outputs;
(e) data, seeds and answer keys are covered by the generated-artifact checks, solution
    execution and mutation checks (nothing to do here);
(f) in statement notebooks, every added comment is one line and names no identifier the
    student must define (shared extractor in tools/checks/api_comments.py).

Exit 0 when clean, 1 on any violation. Not part of ci-local.sh: on `main` after the squash
merge there is no base to compare against.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import nbformat

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.checks.api_comments import (
    _CARD_HEADING,
    CARD_MARKER,
    cell_comments,
    comment_tokens,
    names_word,
    required_identifiers,
)

TEACH_MARKDOWN = "<!-- api-teach -->"
TEACH_CODE = "# api-teach"
_MARKDOWN_HEADING = re.compile(r"(?m)^#{1,6}\s")

# D8: cells referenced by index from tests or the Plan 019 inventory (0-based). Negative
# indices pin the notebook's tail: nothing may be appended after it.
INDEX_PINNED: dict[str, tuple[int, ...]] = {
    "book1/mocktests/r1-001/problems/p05.ipynb": (1,),
    "book1/mocktests/r1-001/problems/p07.ipynb": (1,),
    "book1/mocktests/r1-001/problems/p09.ipynb": (3,),
    "book1/mocktests/r1-001/solutions/p05_solution.ipynb": (1,),
    "book1/mocktests/r1-001/solutions/p07_solution.ipynb": (1,),
    "book1/mocktests/r1-001/solutions/p09_solution.ipynb": (2, 14),
    "book1/units/09-C4-classical-ml-practice/lessons/01-pandas-and-data-loading.ipynb": (22,),
    "book1/units/10-C5-embeddings/lessons/02-matrices-and-similarity.ipynb": (1,),
    "book1/units/10-C5-embeddings/lessons/03-neighbors-and-retrieval.ipynb": (1,),
    "book1/units/16-C9-dimensionality-reduction/lessons/03-truncated-svd-practice.ipynb": (1,),
    "book1/units/17-C10-cnn-transfer/lessons/02-resnet-reading.ipynb": (1,),
    "book1/units/17-C10-cnn-transfer/lessons/03-truncation-and-transfer.ipynb": (1,),
}


def _pinned_practice() -> None:
    cell1 = {
        "10-C5-embeddings": ("p05", "p07", "p08", "p09", "p10", "p13", "p14", "p16", "p17",
                             "p18", "p19", "p20"),
        "16-C9-dimensionality-reduction": ("p07", "p09", "p14"),
    }
    for unit, problems in cell1.items():
        for problem in problems:
            for suffix in ("", "_solution"):
                INDEX_PINNED[f"book1/units/{unit}/practice/{problem}{suffix}.ipynb"] = (1,)
    for unit, problems in {"10-C5-embeddings": ("p11", "p12"),
                           "16-C9-dimensionality-reduction": ("p12",)}.items():
        for problem in problems:
            for suffix in ("", "_solution"):
                INDEX_PINNED[f"book1/units/{unit}/practice/{problem}{suffix}.ipynb"] = (2,)
    c10 = "book1/units/17-C10-cnn-transfer/practice"
    for problem in ("p08", "p09", "p11", "p12", "p15", "p16", "p19"):
        INDEX_PINNED[f"{c10}/{problem}.ipynb"] = (1,)
    for problem in ("p14", "p17"):
        INDEX_PINNED[f"{c10}/{problem}.ipynb"] = (2,)
    for problem in ("p08", "p09", "p11", "p12", "p14", "p15", "p16", "p17", "p19"):
        INDEX_PINNED[f"{c10}/{problem}_solution.ipynb"] = (2,)


_pinned_practice()


def _source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def _is_statement(rel: str) -> bool:
    name = Path(rel).name
    return ("/practice/" in rel or "/problems/" in rel) and not name.endswith("_solution.ipynb")


def _git(*args: str, root: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    ).stdout


def _base_notebooks(base: str, root: Path) -> set[str]:
    listing = _git("ls-tree", "-r", "--name-only", base, "--", "book1", "book2", root=root)
    return {line for line in listing.splitlines() if _in_scope(line)}


def _in_scope(rel: str) -> bool:
    parts = Path(rel).parts
    return (
        rel.endswith(".ipynb")
        and len(parts) > 2
        and parts[1] in {"units", "mocktests"}
        and ".ipynb_checkpoints" not in parts
    )


def _new_cell_ok(cell: dict[str, Any]) -> bool:
    source = _source(cell).lstrip()
    if cell.get("cell_type") == "markdown":
        return source.startswith((CARD_MARKER, TEACH_MARKDOWN))
    if cell.get("cell_type") == "code":
        return source.startswith(TEACH_CODE)
    return False


def _ast_dump(source: str) -> str | None:
    try:
        return ast.dump(ast.parse(source))
    except SyntaxError:
        return None


def _match_cells(
    base_cells: list[dict[str, Any]], head_cells: list[dict[str, Any]]
) -> tuple[dict[int, int], list[int], list[str]]:
    """Map base index -> head index; return the new head indices and structural errors."""
    errors: list[str] = []
    base_ids = [cell.get("id") for cell in base_cells]
    if all(base_ids):
        position = {cell.get("id"): index for index, cell in enumerate(head_cells)}
        mapping: dict[int, int] = {}
        for base_index, cell_id in enumerate(base_ids):
            if cell_id not in position:
                errors.append(f"base cell {base_index} (id {cell_id}) is missing or lost its id")
            else:
                mapping[base_index] = position[cell_id]
        new = [index for index in range(len(head_cells)) if index not in set(mapping.values())]
        return mapping, new, errors
    # nbformat 4.4 notebooks carry no ids: pre-existing cells are the unmarked ones, in order.
    new = [index for index, cell in enumerate(head_cells) if _new_cell_ok(cell)]
    kept = [index for index in range(len(head_cells)) if index not in new]
    if len(kept) != len(base_cells):
        errors.append(
            f"{len(base_cells)} base cells but {len(kept)} unmarked cells on the branch "
            "(id-less notebook)"
        )
    return dict(zip(range(len(base_cells)), kept, strict=False)), new, errors


def _subsequence(base: list[str], head: list[str]) -> tuple[bool, set[int]]:
    """Whether `base` is a subsequence of `head`; also the head positions it consumed."""
    used: set[int] = set()
    cursor = 0
    for token in base:
        while cursor < len(head) and head[cursor] != token:
            cursor += 1
        if cursor == len(head):
            return False, used
        used.add(cursor)
        cursor += 1
    return True, used


def _added_comment_lines(base_source: str, head_source: str) -> list[tuple[int, str, bool]]:
    """(line, text, comment-only) for each head comment token not matched at the base."""
    head = cell_comments(head_source)
    ordered = [
        (line, text, line in head.comment_only)
        for line in sorted(head.by_line)
        for text in head.by_line[line]
    ]
    _ok, used = _subsequence(comment_tokens(base_source), [text for _, text, _ in ordered])
    return [entry for position, entry in enumerate(ordered) if position not in used]


def verify_notebook(
    rel: str, base_nb: dict[str, Any], head_nb: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    base_cells = base_nb.get("cells", [])
    head_cells = head_nb.get("cells", [])
    mapping, new, structural = _match_cells(base_cells, head_cells)
    errors += [f"{rel}: (d) {error}" for error in structural]
    ordered = [mapping[index] for index in sorted(mapping)]
    if ordered != sorted(ordered):
        errors.append(f"{rel}: (d) pre-existing cells changed their relative order")
    statement = _is_statement(rel)
    required = required_identifiers(base_nb) if statement else set()
    for base_index, head_index in mapping.items():
        base_cell, head_cell = base_cells[base_index], head_cells[head_index]
        where = f"{rel}:cell {base_index}"
        if base_cell.get("cell_type") != head_cell.get("cell_type"):
            errors.append(f"{where}: (d) cell type changed")
            continue
        base_source, head_source = _source(base_cell), _source(head_cell)
        if isinstance(base_cell.get("source"), list) != isinstance(head_cell.get("source"), list):
            # D8: some tests read str(cell["source"]); keep the stored representation.
            errors.append(f"{where}: (d) source representation changed (string vs list)")
        if base_cell.get("cell_type") != "code":
            if base_source != head_source:
                errors.append(f"{where}: (c) pre-existing {base_cell.get('cell_type')} cell changed")
            continue
        if _ast_dump(base_source) != _ast_dump(head_source):
            errors.append(f"{where}: (a) code changed (ast.dump differs)")
        ok, _used = _subsequence(comment_tokens(base_source), comment_tokens(head_source))
        if not ok:
            errors.append(f"{where}: (b) a pre-existing comment was removed or reworded")
        if statement:
            errors += _statement_comments(where, base_source, head_source, required)
    pinned = INDEX_PINNED.get(rel, ())
    for index in pinned:
        if index in mapping and mapping[index] != index:
            errors.append(f"{rel}:cell {index}: (d) index-referenced cell moved to {mapping[index]}")
    last_pinned = max(pinned, default=-1)
    seen_ids: set[str] = set()
    for cell in head_cells:
        cell_id = cell.get("id")
        if cell_id in seen_ids:
            errors.append(f"{rel}: (d) duplicate cell id {cell_id}")
        if cell_id:
            seen_ids.add(cell_id)
    base_id_set = {cell.get("id") for cell in base_cells if cell.get("id")}
    id_less = not base_id_set and bool(base_cells)
    answer_checks = [
        index
        for index, cell in enumerate(head_cells)
        if cell.get("cell_type") == "markdown" and _source(cell).strip() == "### Answer check"
    ]
    for head_index in new:
        cell = head_cells[head_index]
        where = f"{rel}:new cell {head_index}"
        if not _new_cell_ok(cell):
            errors.append(f"{where}: (c) new cell lacks an api-card / api-teach marker")
            continue
        if cell.get("id") and cell.get("id") in base_id_set:
            errors.append(f"{where}: (d) new cell reuses a base id")
        if id_less and cell.get("id"):
            errors.append(f"{where}: (d) nbformat 4.4 notebook: new cells must not carry ids")
        source = _source(cell).lstrip()
        if answer_checks and head_index > answer_checks[-1]:
            errors.append(f"{where}: (d) new cell after '### Answer check' (D8)")
        if source.startswith(CARD_MARKER):
            first = next(
                (line for line in source[len(CARD_MARKER):].splitlines() if line.strip()), ""
            )
            if not _CARD_HEADING.match(first):
                errors.append(
                    f"{where}: (d) card must open with an unnumbered '## ' heading (D8)"
                )
            if Path(rel).name not in {"lesson.ipynb", "review.ipynb"}:
                errors.append(f"{where}: (d) API cards belong in lesson.ipynb / review.ipynb")
            if head_index != len(head_cells) - 1:
                errors.append(f"{where}: (d) the API card must be appended at the end")
        elif cell.get("cell_type") == "markdown" and _MARKDOWN_HEADING.search(
            source[len(TEACH_MARKDOWN):]
        ):
            errors.append(f"{where}: (d) teaching markdown must not add headings (D8)")
        elif head_index <= last_pinned:
            errors.append(
                f"{where}: (d) teaching cell inserted before index-referenced cell {last_pinned}"
            )
        if statement:
            errors.append(f"{where}: (f) no new cells in statement notebooks")
        if cell.get("cell_type") == "code" and statement:
            errors += _statement_comments(where, "", _source(cell), required)
    if statement:
        for index, cell in enumerate(head_cells):
            if cell.get("cell_type") == "code" and (
                cell.get("outputs") or cell.get("execution_count") is not None
            ):
                errors.append(f"{rel}:cell {index}: (d) student notebook cell has outputs")
    try:
        nbformat.validate(nbformat.from_dict(head_nb))
    except nbformat.ValidationError as exc:
        errors.append(f"{rel}: (d) nbformat.validate failed: {exc.message}")
    return errors


def _statement_comments(where: str, base: str, head: str, required: set[str]) -> list[str]:
    errors: list[str] = []
    added = _added_comment_lines(base, head)
    added_only = {line for line, _text, comment_only in added if comment_only}
    for line, text, _comment_only in added:
        if line in added_only and (line - 1 in added_only or line + 1 in added_only):
            errors.append(f"{where}:line {line}: (f) added statement comment spans several lines")
        leaked = sorted(name for name in required if names_word(text, name))
        if leaked:
            errors.append(
                f"{where}:line {line}: (f) added comment names required identifier(s) "
                f"{', '.join(leaked)}"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True, help="git ref to compare against (e.g. main)")
    parser.add_argument("--root", default=str(ROOT), help="repository root")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    base_paths = _base_notebooks(args.base, root)
    head_paths = {
        path.relative_to(root).as_posix()
        for book in ("book1", "book2")
        for path in (root / book).rglob("*.ipynb")
        if _in_scope(path.relative_to(root).as_posix())
    }
    errors: list[str] = []
    for rel in sorted(base_paths - head_paths):
        errors.append(f"{rel}: notebook deleted")
    for rel in sorted(head_paths - base_paths):
        errors.append(f"{rel}: new notebook (Plan 032 adds no notebooks)")
    changed = 0
    for rel in sorted(base_paths & head_paths):
        base_text = _git("show", f"{args.base}:{rel}", root=root)
        head_text = (root / rel).read_text(encoding="utf-8")
        if base_text == head_text:
            continue
        changed += 1
        try:
            base_nb, head_nb = json.loads(base_text), json.loads(head_text)
        except ValueError as exc:
            errors.append(f"{rel}: cannot parse notebook JSON: {exc}")
            continue
        errors += verify_notebook(rel, base_nb, head_nb)
    for error in errors:
        print(f"ERROR verify-comment-only: {error}", file=sys.stderr)
    print("(e) data, seeds and answer keys: covered by generated-artifact --check runs, "
          "solution execution and mutation checks")
    if errors:
        print(f"FAIL verify-comment-only: {len(errors)} violation(s) in {changed} changed notebook(s)",
              file=sys.stderr)
        return 1
    print(f"PASS verify-comment-only: {changed} changed notebook(s) against {args.base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
