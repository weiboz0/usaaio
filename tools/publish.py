"""Turn a `publication: true` book's notebooks into Quarto book projects, one per edition.

Plan 030 (D2, D3), ported from py4kids' `tools/publish.py`. Notebooks are converted without
being executed and every cell output is dropped. Each generated chapter carries a provenance
sidecar (`provenance/<chapter>.json`) that lists every emitted block in order, so the audit
(`tools/publish_audit.py`, Task 5) can re-derive which blocks an edition may print and check
that the chapter text is exactly those blocks plus the publisher's fixed scaffolding.

Chapter text is `"".join(segment["sep"] + segment["text"] for segment in segments)`.
Segment kinds:

- `scaffold`: publisher text (chapter headings, pointers, panel fences, labels, index entries);
- `title`: a notebook's leading `# ...` paragraph, re-leveled (transform `title`);
- `markdown`: a slice `span` of a markdown cell or Markdown file, headings shifted by `shift`;
- `code`: a code cell's source in a fenced block (transform `fence`);
- `details-name`: the display name derived from a `<details>` summary (transform `details-name`);
- `details-body`: a `<details>` body slice, headings shifted by `shift`.

Every non-scaffold segment names its `source` (book-relative path), `cell` (index, or -1 for a
Markdown file) and `span` (character offsets into that cell's or file's text).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from tools.books import (
    EDITION_NAMES,
    BookSpec,
    PublicationConfig,
    load_book_catalog,
    load_publication_config,
    output_pdf_name,
)

THEME = Path(__file__).with_name("publish_theme")

# Edition profiles (D2). Each PDF is `<book>-<edition>.pdf` (tools.books.output_pdf_name).
#   student_family   no teacher material; isolation rules apply
#   practice_cells   'markdown' (statements only, plus a file pointer) or 'all' (starter code too)
#   details          '<details>' policy: 'pointer' (print), 'appendix' (student), 'panel' (teacher)
#   selected_answers the selected-answer solutions go to an answers appendix
#   full_solutions   every practice is followed by its full solution
#   body             'book' (front matter, units, back matter) or 'answers' (the Answer Key)
#   front            front-matter Markdown files; the first becomes index.qmd
#   back_matter      Notation and Glossary
#   index            an index (glossary terms; makeindex step and the Index chapter)
#   mocktests        the final part with every configured mock test
EDITIONS: dict[str, dict[str, Any]] = {
    "student-print": {
        "label": "Student Book — Print Edition", "student_family": True,
        "practice_cells": "markdown", "details": "pointer", "selected_answers": False,
        "full_solutions": False, "body": "book", "front": ("preface.md", "how-to-use.md"),
        "back_matter": True, "index": True, "mocktests": False, "classoption": "open=any",
    },
    "student": {
        "label": "Student Book — Full Edition", "student_family": True,
        "practice_cells": "all", "details": "appendix", "selected_answers": True,
        "full_solutions": False, "body": "book", "front": ("preface.md", "how-to-use.md"),
        "back_matter": True, "index": True, "mocktests": False, "classoption": "open=right",
    },
    "answer-key": {
        "label": "Answer Key", "student_family": True,
        "practice_cells": "none", "details": "none", "selected_answers": True,
        "full_solutions": False, "body": "answers", "front": ("answer-key-intro.md",),
        "back_matter": False, "index": False, "mocktests": False, "classoption": "open=any",
    },
    "teacher": {
        "label": "Teacher's Edition", "student_family": False,
        "practice_cells": "all", "details": "panel", "selected_answers": False,
        "full_solutions": True, "body": "book",
        "front": ("preface.md", "how-to-use.md", "for-teachers.md"),
        "back_matter": True, "index": True, "mocktests": True, "classoption": "open=right",
    },
}
assert tuple(EDITIONS) == EDITION_NAMES

BACK_MATTER = (("notation", "Notation"), ("glossary", "Glossary"))
ANSWERS_APPENDIX_TITLE = "Answers to Checkpoints and Selected Practice"
EDITION_MARK = re.compile(r"<!--\s*/?\s*edition\b")
UNIT_LABEL = re.compile(r"^([A-Z][0-9]+(?:-[0-9]{3})?)")
# A fence opener may follow list markers (`2. ```python`); a closer is the fence alone on its line.
FENCE = re.compile(r"^\s*(?:(?:[-*+]|\d+[.)])\s+)*(`{3,}|~{3,})")
FENCE_CLOSE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")
HEADING = re.compile(r"^(#{1,6})(?=\s|$)")
DETAILS_TOKEN = re.compile(r"<details\b[^>]*>|</details\s*>", re.IGNORECASE)
SUMMARY = re.compile(r"\s*<summary\b[^>]*>(.*?)</summary\s*>", re.IGNORECASE | re.DOTALL)
TAG = re.compile(r"<[^>]+>")
DETAILS_NAME = re.compile(r"^(Checkpoint \d+|Answers \d+[–-]\d+)$")
ANSWER_HEADING = re.compile(
    r"(?i)^#+\s*(collected\s+)?((checkpoint|self-quiz|quiz)\s*\d*\s+)?answers\b")
OLD_FONT_GROUP = re.compile(r"\{\s*\\(rm|bf|it|tt|sf|cal)(?![A-Za-z])\s*([^{}]*)\}")
OLD_FONT_IN_MATH = re.compile(r"\\(rm|bf|it|tt|sf|cal)(?![A-Za-z])(\s*)")
TEXT_IN_MATH = re.compile(r"(\\text(?:tt|rm|it|bf|sf)?\{)([^{}]*)\}")
# An inline answer paragraph (Book 2 lessons): `**Collected answers.** ...` at a paragraph start.
ANSWER_PARAGRAPH = re.compile(r"^\*\*Collected (?:checkpoint )?answers\.\*\*")
FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)

# Fixed scaffolding text (the audit matches these exactly).
POINTER_OPEN = "*Answers"
POINTER_CLOSE = ": open this notebook, or see the Teacher's Edition.*"
PRACTICE_FILE = "*Practice file:* `{path}`"
SELECTED_ANSWER_REF = "*Answer: see page `\\pageref{{{label}}}`{{=latex}}.*"


class PublishError(ValueError):
    """A source the publisher refuses to convert (a malformed marker or `<details>` block)."""


# --- naming ------------------------------------------------------------------------------------


def output_stem(book_id: str, edition: str, volume: int | None = None) -> str:
    """The Quarto output-file stem of an edition: `<book>-<edition>[-vol<N>]`."""
    return output_pdf_name(book_id, edition, volume).removesuffix(".pdf")


def profile(edition: str) -> dict[str, Any]:
    if edition not in EDITIONS:
        raise ValueError(f"edition must be one of {', '.join(EDITIONS)}")
    return EDITIONS[edition]


def unit_label(unit: str) -> str:
    match = UNIT_LABEL.match(unit)
    return f"Unit {match[1] if match else unit}"


def details_label(unit: str, stem: str, ordinal: int) -> str:
    """The stable cross-reference label of a `<details>` block: `<unit>-<stem>-d<ordinal>`."""
    return f"{unit}-{stem}-d{ordinal}"


def answer_label(practice_id: str) -> str:
    return f"ans-{practice_id}"


# --- edition markers (py4kids) -----------------------------------------------------------------


def filter_edition_blocks(text: str, edition: str, source: str = "front matter") -> str:
    """Keep shared text and the blocks marked for this edition; drop the marker lines.

    `<!-- edition: NAME -->` (or `NAME|NAME`) opens a block and `<!-- /edition -->` closes it. A
    marker and every excluded line vanish entirely, so a block inside a list leaves no blank line
    behind; a dropped paragraph-level block leaves one blank line, not two.
    An unknown edition name, a malformed, nested, stray or unclosed marker fails the build.
    """
    out: list[str] = []
    active: list[str] | None = None
    opened = 0
    dropped = False
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        if EDITION_MARK.search(line):
            dropped = True
            stripped = line.strip()
            if stripped == "<!-- /edition -->":
                if active is None:
                    raise PublishError(f"FAIL: {source}:{number}: edition block closed but never opened")
                active = None
                continue
            match = re.fullmatch(r"<!-- edition: ([a-z-]+(?: *\| *[a-z-]+)*) -->", stripped)
            if not match:
                raise PublishError(f"FAIL: {source}:{number}: malformed edition marker: {stripped}")
            if active is not None:
                raise PublishError(f"FAIL: {source}:{number}: edition block opened inside line {opened}")
            names = [name.strip() for name in match[1].split("|")]
            unknown = [name for name in names if name not in EDITIONS]
            if unknown:
                raise PublishError(f"FAIL: {source}:{number}: unknown edition {', '.join(unknown)}")
            active, opened = names, number
            continue
        if active is None or edition in active:
            if not line.strip():
                if dropped and out and not out[-1].strip():
                    continue
            else:
                dropped = False
            out.append(line)
        else:
            dropped = True
    if active is not None:
        raise PublishError(f"FAIL: {source}:{opened}: edition block never closed")
    return "".join(out)


# --- markdown transforms (each one is re-derivable by the audit) ----------------------------


def fence_step(line: str, fence: str | None) -> tuple[bool, str | None]:
    """Track fenced code line by line: `(is a fence line, the open fence after this line)`."""
    if fence is None:
        match = FENCE.match(line)
        if match:
            return True, match[1]
        return False, None
    match = FENCE_CLOSE.match(line)
    if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
        return True, None
    return False, fence


def shift_headings(text: str, shift: int) -> str:
    """Move every ATX heading outside fenced code down by `shift` levels (capped at level 6)."""
    if shift == 0:
        return text
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        is_fence, fence_after = fence_step(line, fence)
        if is_fence or fence is not None:
            fence = fence_after
            out.append(line)
            continue
        if fence is None:
            heading = HEADING.match(line)
            if heading:
                level = min(6, len(heading[1]) + shift)
                line = "#" * level + line[len(heading[1]):]
        out.append(line)
    return "".join(out)


def normalize_math(text: str) -> str:
    """Trim spaces just inside inline `$...$` math, which Jupyter accepts and pandoc does not,
    and turn the Markdown escape `\\*` inside math into `*`.

    Fenced code, inline code spans, `$$...$$` display math and escaped `\\$` are left alone.
    """
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        is_fence, fence_after = fence_step(line, fence)
        out.append(("\x00", line) if is_fence or fence is not None else ("", line))
        fence = fence_after
    # Re-join the prose runs so inline math may span lines; keep fenced lines verbatim.
    result: list[str] = []
    run: list[str] = []
    for flag, line in out:
        if flag:
            if run:
                result.append(_normalize_inline_math("".join(run)))
                run = []
            result.append(line)
        else:
            run.append(line)
    if run:
        result.append(_normalize_inline_math("".join(run)))
    return "".join(result)


def _normalize_inline_math(text: str) -> str:
    out: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "\\" and index + 1 < length and text[index + 1] in "([":
            closer = "\\)" if text[index + 1] == "(" else "\\]"
            close = text.find(closer, index + 2)
            if close >= 0:
                out.append(text[index:index + 2] + _math_escapes(text[index + 2:close]) + closer)
                index = close + 2
                continue
        if char == "\\" and index + 1 < length:
            out.append(text[index:index + 2])
            index += 2
            continue
        if char == "`":
            ticks = len(text[index:]) - len(text[index:].lstrip("`"))
            close = text.find("`" * ticks, index + ticks)
            if close < 0:
                out.append(text[index:index + ticks])
                index += ticks
                continue
            out.append(text[index:close + ticks])
            index = close + ticks
            continue
        if char == "$":
            if text.startswith("$$", index):
                close = text.find("$$", index + 2)
                stop = length if close < 0 else close + 2
                out.append(_math_escapes(text[index:stop]))
                index = stop
                continue
            close = index + 1
            while close < length:
                if text[close] == "\\":
                    close += 2
                    continue
                if text[close] == "$" or text.startswith("\n\n", close):
                    break
                close += 1
            if close < length and text[close] == "$" and not text.startswith("$$", close):
                inner = text[index + 1:close]
                if inner.strip():
                    out.append("$" + _math_escapes(inner.strip()) + "$")
                    index = close + 1
                    continue
            out.append(char)
            index += 1
            continue
        out.append(char)
        index += 1
    return "".join(out)


def _math_escapes(math: str) -> str:
    """Markdown escapes inside math (`x^\\*`, written so Jupyter's Markdown keeps the star) are
    plain characters to MathJax but TeX commands to LaTeX; `\\*` after `^`/`_` breaks LaTeX."""
    math = math.replace("\\*", "*").replace("\\'", "'")
    # Plain-TeX font switches (`Q_{\\rm svd}`), which KOMA-Script classes reject.
    math = OLD_FONT_GROUP.sub(lambda match: "{\\math" + match[1] + "{" + match[2] + "}}", math)
    math = OLD_FONT_IN_MATH.sub(lambda match: "\\math" + match[1] + match[2], math)
    # A bare `_` inside a text-mode argument (`\\texttt{components_}`) is a subscript error in
    # LaTeX but a literal underscore in MathJax.
    return TEXT_IN_MATH.sub(
        lambda match: match[1] + re.sub(r"(?<!\\)_", r"\\_", match[2]) + "}", math)


def markdown_text(piece: str, shift: int) -> str:
    """The `markdown` and `details-body` transform: headings shifted, inline math trimmed."""
    return normalize_math(shift_headings(piece, shift))


def title_text(paragraph: str, unit: str) -> str:
    """A notebook's title paragraph (`# C3-x — Session 01: Name`) as plain heading text."""
    text = " ".join(line.strip() for line in paragraph.strip().splitlines())
    text = re.sub(r"^#+\s*", "", text)
    for prefix in (unit, UNIT_LABEL.match(unit)[1] if UNIT_LABEL.match(unit) else unit):
        if text.startswith(prefix + " — "):
            text = text[len(prefix) + 3:]
            break
    text = re.sub(r"\s*\(Unit Overview\)\s*$", "", text)
    return text.strip()


def details_name(summary: str) -> str:
    plain = " ".join(TAG.sub("", summary).split())
    return plain if DETAILS_NAME.match(plain) else "Self-quiz answers"


def fence_code(source: str) -> str:
    body = source.strip("\n").rstrip()
    longest = max((len(run) for run in re.findall(r"`{3,}", body)), default=2)
    ticks = "`" * max(3, longest + 1)
    return f"{ticks}python\n{body}\n{ticks}"


@dataclass(frozen=True)
class Details:
    start: int  # the `<details>` tag
    end: int  # just after `</details>`
    summary: str
    body_start: int
    body_end: int


def parse_details(text: str, where: str) -> list[Details]:
    """Every top-level `<details>` block outside fenced code; nested or unclosed blocks fail."""
    fenced: list[tuple[int, int]] = []
    position = 0
    fence: str | None = None
    fence_start = 0
    for line in text.splitlines(keepends=True):
        is_fence, fence_after = fence_step(line, fence)
        if is_fence and fence is None:
            fence_start = position
        elif is_fence:
            fenced.append((fence_start, position + len(line)))
        fence = fence_after
        position += len(line)
    if fence is not None:
        fenced.append((fence_start, len(text)))

    blocks: list[Details] = []
    open_at: int | None = None
    open_end = 0
    for token in DETAILS_TOKEN.finditer(text):
        if any(start <= token.start() < stop for start, stop in fenced):
            continue
        closing = token.group().startswith("</")
        if not closing:
            if open_at is not None:
                raise PublishError(f"FAIL: {where}: nested <details> block")
            open_at, open_end = token.start(), token.end()
            continue
        if open_at is None:
            raise PublishError(f"FAIL: {where}: </details> without an opening <details>")
        summary_match = SUMMARY.match(text, open_end)
        summary = summary_match[1] if summary_match else ""
        body_start = summary_match.end() if summary_match else open_end
        blocks.append(Details(open_at, token.end(), summary, body_start, token.start()))
        open_at = None
    if open_at is not None:
        raise PublishError(f"FAIL: {where}: unclosed <details> block")
    return blocks


# --- chapter assembly with provenance -----------------------------------------------------------


@dataclass
class Chapter:
    file: str
    kind: str
    title: str
    unit: str = ""
    segments: list[dict[str, Any]] = field(default_factory=list)

    def scaffold(self, text: str, sep: str = "\n\n") -> None:
        self.segments.append({"kind": "scaffold", "sep": sep, "text": text})

    def block(self, kind: str, source: str, cell: int, span: tuple[int, int], text: str,
              sep: str = "\n\n", **extra: Any) -> None:
        segment = {"kind": kind, "sep": sep, "source": source, "cell": cell,
                   "span": list(span), "text": text}
        segment.update(extra)
        self.segments.append(segment)

    def text(self) -> str:
        body = "".join(segment["sep"] + segment["text"] for segment in self.segments)
        return body.lstrip("\n") + "\n"

    def sources(self) -> list[str]:
        seen: list[str] = []
        for segment in self.segments:
            source = segment.get("source")
            if source and source not in seen:
                seen.append(source)
        return seen


@dataclass
class AnswerEntry:
    """A `<details>` body or selected solution waiting for the student answers appendix."""

    unit: str
    heading: str
    label: str
    emit: Any  # callable(chapter) that writes the body segments


@dataclass
class AnswerUnit:
    """One answer body: a `<details>` block, or an open answer section with its pieces."""

    kind: str  # 'details' or 'section'
    heading: str
    names: list[dict[str, Any]]
    pieces: list[dict[str, Any]]

    def add_text(self, text: str, source: str, cell: int, start: int, end: int) -> None:
        if text[start:end].strip():
            self.pieces.append({"kind": "answer-body", "source": source, "cell": cell,
                                "span": (start, end), "raw": text[start:end]})


@dataclass(frozen=True)
class AnswerRegion:
    """An open answer section: from the end of its heading line to the next heading of the same
    or a higher level (or the end of the notebook). Positions are (cell index, offset)."""

    start: tuple[int, int]
    end: tuple[int, int]
    heading: str
    level: int


def answer_regions(cells: list[dict[str, Any]]) -> list[AnswerRegion]:
    regions: list[AnswerRegion] = []
    current: tuple[tuple[int, int], str, int] | None = None
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "markdown":
            continue
        fence: str | None = None
        offset = 0
        for line in cell["source"].splitlines(keepends=True):
            is_fence, fence_after = fence_step(line, fence)
            inside = is_fence or fence is not None
            fence = fence_after
            if not inside:
                heading = HEADING.match(line)
                if heading:
                    level = len(heading[1])
                    if current is not None and level <= current[2]:
                        regions.append(AnswerRegion(current[0], (index, offset), current[1], current[2]))
                        current = None
                    if current is None and ANSWER_HEADING.match(line):
                        text = line.strip().lstrip("#").strip()
                        current = ((index, offset + len(line)), text, level)
            offset += len(line)
    if current is not None:
        regions.append(AnswerRegion(current[0], (len(cells), 0), current[1], current[2]))
    # Inline answer paragraphs (`**Collected answers.** ...`) outside sections and <details>.
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "markdown":
            continue
        text = cell["source"]
        details = [(block.start, block.end) for block in parse_details(text, f"cell {index}")]
        for start, end in answer_paragraphs(text):
            if any(region.start <= (index, start) < region.end for region in regions):
                continue
            if any(a <= start < b for a, b in details):
                continue
            regions.append(AnswerRegion((index, start), (index, end), "Collected answers", 7))
    return sorted(regions, key=lambda region: region.start)


def answer_paragraphs(text: str) -> list[tuple[int, int]]:
    """`(start, end)` of each paragraph whose first line opens with ANSWER_PARAGRAPH."""
    spans: list[tuple[int, int]] = []
    fence: str | None = None
    offset = 0
    previous_blank = True
    start: int | None = None
    for line in text.splitlines(keepends=True):
        is_fence, fence_after = fence_step(line, fence)
        inside = is_fence or fence is not None
        fence = fence_after
        blank = not line.strip()
        if start is not None and (blank or inside):
            spans.append((start, offset))
            start = None
        if start is None and not inside and previous_blank and ANSWER_PARAGRAPH.match(line):
            start = offset
        previous_blank = blank and not inside
        offset += len(line)
    if start is not None:
        spans.append((start, len(text)))
    return spans


def read_notebook(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cells = []
    for cell in raw.get("cells", []):
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(source)
        # Outputs are never read: the publisher strips every output (D3).
        cells.append({"cell_type": cell.get("cell_type", ""), "source": source})
    return cells


class Publisher:
    def __init__(self, repo_root: Path, book: BookSpec, config: PublicationConfig, edition: str):
        self.repo_root = repo_root
        self.book = book
        self.config = config
        self.edition = edition
        self.profile = profile(edition)
        self.answers: list[AnswerEntry] = []
        self._manifests: dict[str, dict[str, Any]] = {}

    # sources --------------------------------------------------------------------------------

    def rel(self, path: Path) -> str:
        return path.relative_to(self.book.root).as_posix()

    def manifest(self, unit: str) -> dict[str, Any]:
        if unit not in self._manifests:
            path = self.book.root / "units" / unit / "manifest.yaml"
            self._manifests[unit] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return self._manifests[unit]

    def practices(self, unit: str) -> list[dict[str, Any]]:
        return [row for row in self.manifest(unit).get("practice") or [] if isinstance(row, dict)]

    def selected(self, row: dict[str, Any]) -> bool:
        for key, values in self.config.student_answers.items():
            if str(row.get(key)) not in values:
                return False
        return True

    def session_notebooks(self, unit: str) -> list[Path]:
        unit_root = self.book.root / "units" / unit
        notebooks = [unit_root / "lesson.ipynb"]
        notebooks += sorted((unit_root / "lessons").glob("*.ipynb"))
        if (unit_root / "review.ipynb").is_file():
            notebooks.append(unit_root / "review.ipynb")
        return [path for path in notebooks if path.is_file()]

    # cell emission ----------------------------------------------------------------------------

    def emit_markdown(self, chapter: Chapter, text: str, source: str, cell: int, shift: int,
                      *, start: int = 0, end: int | None = None, ctx: dict[str, Any] | None = None,
                      details: str | None = None) -> None:
        """Emit text[start:end] with headings shifted; `<details>` blocks become answer units."""
        end = len(text) if end is None else end
        if ctx is None:
            ctx = self._context(source, "", "", "", shift, details)
        where = f"{source} cell {cell}" if cell >= 0 else source
        blocks = [block for block in parse_details(text, where) if start <= block.start < end]
        cursor = start
        index = 0
        while index < len(blocks):
            # A run of blocks separated only by whitespace shares one pointer paragraph.
            run = [blocks[index]]
            while (index + len(run) < len(blocks)
                   and not text[run[-1].end:blocks[index + len(run)].start].strip()):
                run.append(blocks[index + len(run)])
            self._emit_plain(chapter, text, source, cell, shift, cursor, run[0].start)
            units = [self._details_unit(text, source, cell, block) for block in run]
            self._emit_units(chapter, units, ctx)
            cursor = run[-1].end
            index += len(run)
        self._emit_plain(chapter, text, source, cell, shift, cursor, end)

    @staticmethod
    def _context(source: str, unit: str, stem: str, section: str, shift: int,
                 details: str | None) -> dict[str, Any]:
        return {"source": source, "unit": unit, "stem": stem, "section": section,
                "shift": shift, "mode": details, "ordinal": [0]}

    def _emit_plain(self, chapter: Chapter, text: str, source: str, cell: int, shift: int,
                    start: int, end: int) -> None:
        piece = text[start:end]
        if not piece.strip():
            return
        lead = len(piece) - len(piece.lstrip())
        trail = len(piece.rstrip())
        chapter.block("markdown", source, cell, (start + lead, start + trail),
                      markdown_text(piece.strip(), shift), shift=shift)

    # answer units: a `<details>` block or an open answer section (D3) -------------------------

    @staticmethod
    def _details_unit(text: str, source: str, cell: int, block: Details) -> AnswerUnit:
        name = {"kind": "details-name", "source": source, "cell": cell,
                "span": (block.start, block.body_start), "raw": block.summary}
        body = {"kind": "details-body", "source": source, "cell": cell,
                "span": (block.body_start, block.body_end),
                "raw": text[block.body_start:block.body_end]}
        return AnswerUnit(kind="details", heading=details_name(block.summary),
                          names=[name], pieces=[name, body])

    def _section_pieces(self, unit: AnswerUnit, text: str, source: str, cell: int,
                        start: int, end: int) -> None:
        """Add text[start:end] of an open answer section to `unit` (nested `<details>` too)."""
        where = f"{source} cell {cell}"
        cursor = start
        for block in parse_details(text, where):
            if not (start <= block.start < end):
                continue
            unit.add_text(text, source, cell, cursor, block.start)
            nested = self._details_unit(text, source, cell, block)
            unit.names.extend(nested.names)
            unit.pieces.extend(nested.pieces)
            cursor = block.end
        unit.add_text(text, source, cell, cursor, end)

    def _emit_units(self, chapter: Chapter, units: list[AnswerUnit], ctx: dict[str, Any]) -> None:
        mode = ctx["mode"] or self.profile["details"]
        labels = []
        for _ in units:
            ctx["ordinal"][0] += 1
            labels.append(details_label(ctx["unit"], ctx["stem"], ctx["ordinal"][0]))
        if mode == "none":
            return
        if mode == "pointer":
            names = [name for unit in units for name in unit.names]
            chapter.scaffold(POINTER_OPEN)
            if names:
                chapter.scaffold(" (", sep="")
                for position, name in enumerate(names):
                    if position:
                        chapter.scaffold(", ", sep="")
                    self._emit_piece(chapter, name, 0, sep="")
                chapter.scaffold(")", sep="")
            chapter.scaffold(POINTER_CLOSE, sep="")
            return
        if mode == "appendix":
            chapter.scaffold("*Answers: ")
            for position, (unit, label) in enumerate(zip(units, labels, strict=True)):
                if position:
                    chapter.scaffold("; ", sep="")
                for index, name in enumerate(unit.names):
                    if index:
                        chapter.scaffold(", ", sep="")
                    self._emit_piece(chapter, name, 0, sep="")
                reference = f"page `\\pageref{{{label}}}`{{=latex}}"
                chapter.scaffold(f" ({reference})" if unit.names else reference, sep="")
                self.answers.append(AnswerEntry(
                    unit=ctx["unit"], heading=f"{ctx['section']} — {unit.heading}", label=label,
                    emit=self._unit_emitter(unit, shift=4, bold_details=unit.kind == "section")))
            chapter.scaffold(".*", sep="")
            return
        # panel: each body inline in a labelled "Answers" box.
        for unit in units:
            chapter.scaffold("::: {.answers}")
            self._unit_emitter(unit, shift=ctx["shift"] + 1, bold_details=True)(chapter)
            chapter.scaffold(":::")

    def _unit_emitter(self, unit: AnswerUnit, shift: int, bold_details: bool):
        def emit(chapter: Chapter) -> None:
            for piece in unit.pieces:
                if piece["kind"] == "details-name":
                    if not bold_details:
                        continue
                    chapter.scaffold("**")
                    self._emit_piece(chapter, piece, shift, sep="")
                    chapter.scaffold("**", sep="")
                else:
                    self._emit_piece(chapter, piece, shift)
        return emit

    @staticmethod
    def _emit_piece(chapter: Chapter, piece: dict[str, Any], shift: int, sep: str = "\n\n") -> None:
        kind, raw = piece["kind"], piece["raw"]
        start, stop = piece["span"]
        if kind == "details-name":
            chapter.block(kind, piece["source"], piece["cell"], (start, stop), details_name(raw),
                          sep=sep)
            return
        if kind == "answer-code":
            if raw.strip():
                chapter.block(kind, piece["source"], piece["cell"], (start, stop), fence_code(raw),
                              sep=sep, transform="fence")
            return
        if not raw.strip():
            return
        lead = len(raw) - len(raw.lstrip())
        trail = len(raw.rstrip())
        chapter.block(kind, piece["source"], piece["cell"], (start + lead, start + trail),
                      markdown_text(raw.strip(), shift), sep=sep, shift=shift)

    def emit_code(self, chapter: Chapter, source_text: str, source: str, cell: int) -> None:
        if not source_text.strip():
            return
        chapter.block("code", source, cell, (0, len(source_text)), fence_code(source_text),
                      transform="fence")

    def emit_notebook(self, chapter: Chapter, path: Path, *, level: int, unit: str,
                      title: str | None = None, markdown_only: bool = False,
                      details: str | None = None, drop_title: bool = False,
                      answer_sections: bool = False) -> str:
        """Emit a notebook as a section at heading `level`; return the section title.

        The notebook's leading `# ...` paragraph becomes the section heading (or is dropped with
        `drop_title`); its other headings shift by `level - 1`. With `answer_sections`, every
        open answer section (ANSWER_HEADING) is an answer unit like a `<details>` body.
        """
        source = self.rel(path)
        cells = read_notebook(path)
        shift = level - 1
        ctx = self._context(source, unit, path.stem, title or "", shift, details)
        regions = answer_regions(cells) if answer_sections else []
        open_units: dict[int, AnswerUnit] = {}
        first_markdown = True

        def flush(region_index: int) -> None:
            answer = open_units.pop(region_index)
            self._emit_units(chapter, [answer], ctx)

        for index, cell in enumerate(cells):
            # Sections that ended at the start of this cell.
            for number, region in enumerate(regions):
                if number in open_units and region.end == (index, 0):
                    flush(number)
            text = cell["source"]
            kind = cell["cell_type"]
            start = 0
            if kind == "markdown" and first_markdown:
                first_markdown = False
                lead = len(text) - len(text.lstrip())
                if text[lead:].startswith("# "):
                    paragraph_end = text.find("\n\n", lead)
                    paragraph_end = len(text) if paragraph_end < 0 else paragraph_end
                    parsed = title_text(text[lead:paragraph_end], unit)
                    ctx["section"] = title or parsed
                    if not drop_title:
                        chapter.block("title", source, index, (lead, paragraph_end),
                                      "#" * level + " " + ctx["section"], level=level,
                                      title=title or "")
                    start = paragraph_end
                elif title and not drop_title:
                    chapter.scaffold("#" * level + " " + title)
            # Split this cell into stretches outside and inside answer sections.
            cuts: list[tuple[int, int, int | None]] = []  # (start, end, region index or None)
            position = start
            for number, region in enumerate(regions):
                if region.end <= (index, 0) or region.start >= (index + 1, 0):
                    continue
                inside_start = region.start[1] if region.start[0] == index else 0
                inside_end = region.end[1] if region.end[0] == index else len(text)
                inside_start = max(inside_start, position)
                if inside_start > position:
                    cuts.append((position, inside_start, None))
                cuts.append((inside_start, inside_end, number))
                position = inside_end
            if position < len(text) or not cuts:
                cuts.append((position, len(text), None))
            for cut_start, cut_end, number in cuts:
                if number is None:
                    if kind == "markdown" and text[cut_start:cut_end].strip():
                        self.emit_markdown(chapter, text, source, index, shift, start=cut_start,
                                           end=cut_end, ctx=ctx)
                    elif kind == "code" and not markdown_only:
                        self.emit_code(chapter, text, source, index)
                    continue
                region = regions[number]
                answer = open_units.setdefault(
                    number, AnswerUnit(kind="section", heading=region.heading, names=[], pieces=[]))
                if kind == "markdown":
                    self._section_pieces(answer, text, source, index, cut_start, cut_end)
                elif kind == "code":
                    answer.pieces.append({"kind": "answer-code", "source": source, "cell": index,
                                          "span": (0, len(text)), "raw": text})
                if region.end[0] == index and region.end[1] == cut_end:
                    flush(number)
        for number in sorted(open_units):
            flush(number)
        if first_markdown and title and not drop_title:
            chapter.scaffold("#" * level + " " + title)
        return ctx["section"]

    def emit_markdown_file(self, chapter: Chapter, path: Path, shift: int,
                           details: str = "panel") -> None:
        text = path.read_text(encoding="utf-8")
        start = 0
        match = FRONT_MATTER.match(text)
        if match:
            start = match.end()
        source = self.rel(path)
        self.emit_markdown(chapter, text, source, -1, shift, start=start,
                           ctx=self._context(source, path.parent.parent.name, path.stem, "",
                                             shift, details))

    # chapters ---------------------------------------------------------------------------------

    def unit_heading(self, chapter: Chapter, unit: str, *, mainmatter: bool) -> None:
        spec = self.config.chapter(unit)
        attributes = f'#ch-{unit} pub-label="{unit_label(unit)}"'
        if mainmatter:
            attributes += ' pub-mainmatter="true"'
        chapter.scaffold(f"# {spec.title} {{{attributes}}}")
        chapter.scaffold("```{=latex}\n\\chaptermark{" + tex_escape(spec.head) + "}\n```")

    def unit_chapter(self, unit: str, *, mainmatter: bool) -> Chapter:
        spec = self.config.chapter(unit)
        chapter = Chapter(file=f"{unit}.qmd", kind="unit", title=spec.title, unit=unit)
        self.unit_heading(chapter, unit, mainmatter=mainmatter)
        for path in self.session_notebooks(unit):
            title = "Unit Overview" if path.name == "lesson.ipynb" else (
                "Review" if path.name == "review.ipynb" else None)
            self.emit_notebook(chapter, path, level=2, unit=unit, title=title, answer_sections=True)
        practices = self.practices(unit)
        if practices:
            chapter.scaffold("## Practice")
        for row in practices:
            statement = self.book.root / "units" / unit / str(row["path"])
            markdown_only = self.profile["practice_cells"] == "markdown"
            self.emit_notebook(chapter, statement, level=3, unit=unit,
                               markdown_only=markdown_only)
            if markdown_only:
                chapter.scaffold(PRACTICE_FILE.format(path=self.rel(statement)))
            if self.profile["selected_answers"] and self.selected(row):
                label = answer_label(str(row["id"]))
                chapter.scaffold(SELECTED_ANSWER_REF.format(label=label))
                solution = self.book.root / "units" / unit / str(row["solution_path"])
                self.answers.append(AnswerEntry(
                    unit=unit, heading=practice_title(statement, unit), label=label,
                    emit=self._solution_emitter(solution, unit, level=3)))
            if self.profile["full_solutions"]:
                solution = self.book.root / "units" / unit / str(row["solution_path"])
                chapter.scaffold("#### Solution")
                self.emit_notebook(chapter, solution, level=4, unit=unit, drop_title=True,
                                   details="panel")
        return chapter

    def _solution_emitter(self, solution: Path, unit: str, level: int):
        def emit(chapter: Chapter) -> None:
            self.emit_notebook(chapter, solution, level=level, unit=unit, drop_title=True,
                               details="panel")
        return emit

    def answer_key_chapter(self, unit: str, *, mainmatter: bool) -> Chapter | None:
        rows = [row for row in self.practices(unit) if self.selected(row)]
        if not rows:
            return None
        spec = self.config.chapter(unit)
        chapter = Chapter(file=f"answers-{unit}.qmd", kind="answers", title=spec.title, unit=unit)
        self.unit_heading(chapter, unit, mainmatter=mainmatter)
        for row in rows:
            statement = self.book.root / "units" / unit / str(row["path"])
            solution = self.book.root / "units" / unit / str(row["solution_path"])
            chapter.scaffold(f"## {practice_title(statement, unit)} {{#{answer_label(str(row['id']))}}}")
            self.emit_notebook(chapter, solution, level=2, unit=unit, drop_title=True,
                               details="panel")
        return chapter

    def answers_appendix(self, units: list[str]) -> Chapter:
        chapter = Chapter(file="answers.qmd", kind="answers-appendix", title=ANSWERS_APPENDIX_TITLE)
        chapter.scaffold(f'# {ANSWERS_APPENDIX_TITLE} {{pub-label=""}}')
        for unit in units:
            entries = [entry for entry in self.answers if entry.unit == unit]
            if not entries:
                continue
            chapter.scaffold(f"## {self.config.chapter(unit).title}")
            for entry in entries:
                chapter.scaffold(f"### {entry.heading} {{#{entry.label}}}")
                entry.emit(chapter)
        return chapter

    def mocktest_chapter(self, test: str) -> Chapter:
        root = self.book.root / "mocktests" / test
        chapter = Chapter(file=f"mock-{test}.qmd", kind="mocktest", title=f"Mock Test {test}")
        chapter.scaffold(f'# Mock Test {test} {{#mock-{test} pub-label="Mock test"}}')
        chapter.scaffold("```{=latex}\n\\chaptermark{Mock Test " + tex_escape(test) + "}\n```")
        for path in mock_paper_sources(root):
            if path.suffix == ".md":
                self.emit_markdown_file(chapter, path, shift=1)
            else:
                self.emit_notebook(chapter, path, level=2, unit=test, details="panel")
        chapter.scaffold("## Answers")
        for path in mock_solution_sources(root):
            if path.suffix == ".md":
                self.emit_markdown_file(chapter, path, shift=2)
            else:
                chapter.scaffold(f"### Solution: `{path.relative_to(root).as_posix()}`")
                self.emit_notebook(chapter, path, level=3, unit=test, drop_title=True,
                                   details="panel")
        return chapter


def practice_title(statement: Path, unit: str) -> str:
    for cell in read_notebook(statement):
        if cell["cell_type"] == "markdown":
            text = cell["source"].lstrip()
            if text.startswith("# "):
                end = text.find("\n\n")
                return title_text(text if end < 0 else text[:end], unit)
            break
    return statement.stem


def mock_manifest_files(root: Path) -> list[str]:
    raw = yaml.safe_load((root / "manifest.yaml").read_text(encoding="utf-8")) or {}
    files: list[str] = []
    for problem in raw.get("problems") or []:
        for name in problem.get("files") or []:
            if name not in files:  # first occurrence in manifest order wins
                files.append(str(name))
    return files


def mock_paper_sources(root: Path) -> list[Path]:
    """`test.md`, then each item file once, at its first occurrence in manifest problem order."""
    return [root / "test.md", *(root / name for name in mock_manifest_files(root))]


def mock_solution_sources(root: Path) -> list[Path]:
    """`solutions/answers.md`, `rubric.md`, then `solutions/pNN_solution.ipynb` in problem order."""
    sources = [root / "solutions" / "answers.md", root / "rubric.md"]
    for name in mock_manifest_files(root):
        path = Path(name)
        if path.parts[0] == "problems" and path.suffix == ".ipynb":
            solution = root / "solutions" / f"{path.stem}_solution.ipynb"
            if solution.is_file() and solution not in sources:
                sources.append(solution)
    return sources


# --- glossary and index -----------------------------------------------------------------------

GLOSSARY_ENTRY = re.compile(r"^\*\*(.+?)\*\*\s*[—–:-]")
CONCEPT_NOTE = re.compile(r"<!--\s*concepts?:\s*([^;>]*?)\s*(?:;[^>]*)?-->")


def glossary_terms(text: str, concepts: set[str]) -> list[tuple[str, tuple[str, ...]]]:
    """`(term, concept ids)` for each `**Term** — definition` entry.

    A `<!-- concept: a, b -->` comment on the entry's lines names its concepts; otherwise the
    term's slug is used when it is a concept id.
    """
    entries: list[tuple[str, tuple[str, ...]]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = GLOSSARY_ENTRY.match(line.strip())
        if not match:
            continue
        term = match[1].strip()
        named: tuple[str, ...] = ()
        for following in lines[index:index + 4]:
            if following is not line and GLOSSARY_ENTRY.match(following.strip()):
                break
            note = CONCEPT_NOTE.search(following)
            if note:
                named = tuple(part.strip() for part in re.split(r"[,\s]+", note[1]) if part.strip())
                break
        if not named:
            slug = re.sub(r"[^a-z0-9]+", "-", term.casefold().replace("`", "")).strip("-")
            named = (slug,) if slug in concepts else ()
        entries.append((term, named))
    return entries


def index_entry(term: str) -> str:
    """One case-insensitive makeindex identity with the author's display text (py4kids)."""
    plain = term.replace("`", "")

    def escaped(value: str) -> str:
        return value.replace('"', '""').replace("!", '"!').replace("@", '"@').replace("|", '"|')

    display = tex_escape(plain)
    return escaped(plain.casefold()) + "@" + escaped(display)


def tex_escape(text: str) -> str:
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#",
                    "$": r"\$", "{": r"\{", "}": r"\}", "^": r"\^{}", "~": r"\~{}"}
    return "".join(replacements.get(char, char) for char in text)


def concept_units(book: BookSpec) -> dict[str, str]:
    """concept id -> the unit whose manifest `concepts_taught` introduces it."""
    owners: dict[str, str] = {}
    for manifest in sorted(book.root.glob("units/*/manifest.yaml")):
        raw = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        for concept in raw.get("concepts_taught") or []:
            if ":" in str(concept):  # a qualified import (book1:...) is not introduced here
                continue
            owners.setdefault(str(concept), manifest.parent.name)
    return owners


def index_terms_by_unit(book: BookSpec, glossary_text: str) -> dict[str, list[str]]:
    owners = concept_units(book)
    by_unit: dict[str, list[str]] = {}
    for term, concepts in glossary_terms(glossary_text, set(owners)):
        units = sorted({owners[concept] for concept in concepts if concept in owners})
        for unit in units:
            if term not in by_unit.setdefault(unit, []):
                by_unit[unit].append(term)
    return by_unit


def index_glossary(text: str) -> str:
    """Append `\\index{term}` to each glossary entry line (py4kids)."""
    def repl(match: re.Match[str]) -> str:
        return match[0] + "`\\index{" + index_entry(match[2]) + "}`{=latex}"
    return re.sub(r"(?m)^(\*\*(.+?)\*\*\s*[—–:-].*)$", repl, text)


def yaml_string(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


INDEX_BODY = "\\pubchapterlabel{}\n\n\\printindex\n"


def reset_kicker(text: str) -> str:
    """Give a back-matter chapter's first `# ` heading an empty `pub-label` (py4kids)."""
    return re.sub(r"\A(\s*# [^\n{]*?)[ \t]*$", lambda m: m[1] + ' {pub-label=""}', text, count=1,
                  flags=re.MULTILINE)


# --- project generation -----------------------------------------------------------------------


@dataclass(frozen=True)
class Scope:
    """`full`, or the explicit units and mock tests of a scoped check (D5 rule 1, D6)."""

    mode: str
    units: tuple[str, ...]
    mocktests: tuple[str, ...]

    def as_json(self) -> dict[str, Any]:
        return {"mode": self.mode, "units": list(self.units), "mocktests": list(self.mocktests)}


def resolve_scope(book: BookSpec, config: PublicationConfig, units: list[str] | None,
                  mocktests: list[str] | None) -> Scope:
    if units is None and mocktests is None:
        return Scope("full", config.units, config.mocktests)
    requested_units = list(dict.fromkeys(units or []))
    unknown = [unit for unit in requested_units if unit not in config.units]
    if unknown:
        raise ValueError(f"scoped units are not configured chapters: {unknown}")
    requested_tests = list(dict.fromkeys(mocktests or []))
    for test in requested_tests:
        if not (book.root / "mocktests" / test / "manifest.yaml").is_file():
            raise ValueError(f"scoped mock test {test} does not exist")
    ordered_units = tuple(unit for unit in config.units if unit in requested_units)
    ordered_tests = tuple(
        [test for test in config.mocktests if test in requested_tests]
        + sorted(test for test in requested_tests if test not in config.mocktests)
    )
    return Scope("scoped", ordered_units, ordered_tests)


@dataclass(frozen=True)
class Project:
    edition: str
    volume: int | None
    path: Path
    output_stem: str
    index: bool


def plan_projects(repo_root: Path, book_id: str, scope: Scope) -> list[tuple[str, int | None, tuple[str, ...]]]:
    """`(edition, volume, units)` for every project of this build."""
    book = load_book_catalog(repo_root).by_id(book_id)
    config = load_publication_config(book)
    plans: list[tuple[str, int | None, tuple[str, ...]]] = []
    for edition in EDITIONS:
        if scope.mode == "full" and edition in config.volume_editions:
            for volume in config.volumes:
                plans.append((edition, volume.number, volume.units))
        else:
            plans.append((edition, None, scope.units))
    return plans


def build(repo_root: Path, book_id: str, edition: str, *, units: list[str] | None = None,
          mocktests: list[str] | None = None, volume: int | None = None) -> Project:
    """Generate one edition's Quarto project (one volume of it when `volume` is set)."""
    repo_root = Path(repo_root).resolve()
    edition_profile = profile(edition)
    catalog = load_book_catalog(repo_root)
    book = catalog.by_id(book_id)
    if not book.publication:
        raise ValueError(f"{book_id} is not a publication book (books.yaml publication: true)")
    config = load_publication_config(book)
    scope = resolve_scope(book, config, units, mocktests)
    volume_spec = None
    body_units = scope.units
    if volume is not None:
        if scope.mode != "full" or edition not in config.volume_editions:
            raise ValueError(f"{edition} is not split into volumes in this build")
        volume_spec = next((v for v in config.volumes if v.number == volume), None)
        if volume_spec is None:
            raise ValueError(f"unknown volume {volume}")
        body_units = volume_spec.units
    elif scope.mode == "full" and edition in config.volume_editions:
        raise ValueError(f"{edition} is split into volumes; pass a volume number")

    stem = output_stem(book_id, edition, volume)
    folder = "publish" if scope.mode == "full" else "publish-check"
    project = book.root / "build" / folder / (edition if volume is None else f"{edition}-vol{volume}")
    if project.exists():
        shutil.rmtree(project)
    project.mkdir(parents=True)
    shutil.copytree(THEME, project / "theme")
    (project / "provenance").mkdir()

    subtitle = book.subtitle
    if volume_spec is not None:
        subtitle = f"{book.subtitle} · Volume {volume_spec.number}: {volume_spec.title}"
    theme_tex = project / "theme" / "theme.tex"
    theme_text = theme_tex.read_text(encoding="utf-8").replace(
        "@SHARED@", (THEME / "fonts.tex").read_text(encoding="utf-8").rstrip("\n"))
    for placeholder, value in (("@EDITION@", edition_profile["label"]),
                               ("@TITLE@", tex_escape(book.title)),
                               ("@SUBTITLE@", tex_escape(subtitle)),
                               ("@FOLDER@", tex_escape(book.root.name))):
        theme_text = theme_text.replace(placeholder, value)
    theme_tex.write_text(theme_text, encoding="utf-8")

    publisher = Publisher(repo_root, book, config, edition)
    front: list[Chapter] = []
    for position, name in enumerate(edition_profile["front"]):
        source = book.root / "front-matter" / name
        relative = source.relative_to(book.root).as_posix()
        text = filter_edition_blocks(source.read_text(encoding="utf-8"), edition, relative)
        chapter = Chapter(file="index.qmd" if position == 0 else name.replace(".md", ".qmd"),
                          kind="front", title=_first_heading(text) or name)
        chapter.block("markdown", relative, -1, (0, len(text)), shift_headings_front(text),
                      sep="", transform="front-matter")
        front.append(chapter)

    body: list[Chapter] = []
    if edition_profile["body"] == "answers":
        for unit in body_units:
            chapter = publisher.answer_key_chapter(unit, mainmatter=not body)
            if chapter is not None:
                body.append(chapter)
    else:
        for position, unit in enumerate(body_units):
            body.append(publisher.unit_chapter(unit, mainmatter=position == 0))
        if edition_profile["selected_answers"] and publisher.answers:
            body.append(publisher.answers_appendix(list(body_units)))

    mock_chapters: list[Chapter] = []
    last_volume = volume_spec is None or volume_spec.number == len(config.volumes)
    if edition_profile["mocktests"] and last_volume:
        mock_chapters = [publisher.mocktest_chapter(test) for test in scope.mocktests]

    back: list[Chapter] = []
    glossary_text = ""
    if edition_profile["back_matter"]:
        for name, title in BACK_MATTER:
            source = book.root / "back-matter" / f"{name}.md"
            relative = source.relative_to(book.root).as_posix()
            text = filter_edition_blocks(source.read_text(encoding="utf-8"), edition, relative)
            if name == "glossary":
                glossary_text = text
                rendered = index_glossary(reset_kicker(text)) if edition_profile["index"] else reset_kicker(text)
            else:
                rendered = reset_kicker(text)
            chapter = Chapter(file=f"{name}.qmd", kind="back", title=title)
            chapter.block("markdown", relative, -1, (0, len(text)), rendered, sep="",
                          transform="back-matter")
            back.append(chapter)

    if edition_profile["index"]:
        terms = index_terms_by_unit(book, glossary_text)
        for chapter in body:
            if chapter.kind != "unit" or not terms.get(chapter.unit):
                continue
            entries = "".join("\\index{" + index_entry(term) + "}" for term in terms[chapter.unit])
            # Right after the chapter heading and its \chaptermark block.
            chapter.segments.insert(2, {"kind": "scaffold", "sep": "\n\n",
                                        "text": "```{=latex}\n" + entries + "\n```"})
        index_chapter = Chapter(file="the-index.qmd", kind="index", title="Index")
        index_chapter.scaffold(INDEX_BODY.rstrip("\n"), sep="")
        back.append(index_chapter)

    every = front + body + mock_chapters + back
    inventory: dict[str, Any] = {
        "book": book_id, "edition": edition, "volume": volume, "output_name": stem,
        "scope": scope.as_json(), "body_units": list(body_units), "chapters": []}
    for chapter in every:
        (project / chapter.file).write_text(chapter.text(), encoding="utf-8")
        provenance = {"file": chapter.file, "kind": chapter.kind, "unit": chapter.unit,
                      "joiner": "segments joined as sep + text; leading newlines stripped; one final newline",
                      "segments": chapter.segments}
        (project / "provenance" / (chapter.file.removesuffix(".qmd") + ".json")).write_text(
            json.dumps(provenance, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        inventory["chapters"].append({"file": chapter.file, "kind": chapter.kind,
                                      "unit": chapter.unit, "title": chapter.title,
                                      "sources": chapter.sources()})
    scope_record = scope.as_json() | {"edition": edition, "volume": volume,
                                      "body_units": list(body_units)}
    (project / "scope.json").write_text(json.dumps(scope_record, indent=2) + "\n", encoding="utf-8")
    (project / "inventory.json").write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n",
                                            encoding="utf-8")

    def listing(chapters: list[Chapter], indent: str = "    ") -> list[str]:
        return [f"{indent}- {chapter.file}" for chapter in chapters]

    chapter_lines = listing(body)
    if mock_chapters:
        chapter_lines.append('    - part: "Mock Tests"')
        chapter_lines.append("      chapters:")
        chapter_lines += listing(mock_chapters, "        ")
    chapter_lines += listing(back)
    quarto = (project / "theme" / "_quarto.yml").read_text(encoding="utf-8")
    quarto = quarto.replace("@FRONT@", "\n".join(listing(front)))
    quarto = quarto.replace("@CHAPTERS@", "\n".join(chapter_lines))
    quarto = quarto.replace("@TITLE@", yaml_string(book.title))
    quarto = quarto.replace("@SUBTITLE@", yaml_string(subtitle))
    quarto = quarto.replace("@OUTPUT@", stem)
    quarto = quarto.replace("@CLASSOPTION@", edition_profile["classoption"])
    (project / "_quarto.yml").write_text(quarto, encoding="utf-8")
    return Project(edition, volume, project, stem, bool(edition_profile["index"]))


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def shift_headings_front(text: str) -> str:
    """Front matter keeps its `# ` chapter heading; its `## ` sections become `### ` (py4kids)."""
    return re.sub(r"(?m)^## ", "### ", text)


def build_all(repo_root: Path, book_id: str, *, units: list[str] | None = None,
              mocktests: list[str] | None = None) -> list[Project]:
    repo_root = Path(repo_root).resolve()
    book = load_book_catalog(repo_root).by_id(book_id)
    config = load_publication_config(book)
    scope = resolve_scope(book, config, units, mocktests)
    projects = []
    for edition, volume, _ in plan_projects(repo_root, book_id, scope):
        projects.append(build(repo_root, book_id, edition, units=units, mocktests=mocktests,
                              volume=volume))
    return projects


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.publish")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--book", required=True)
    parser.add_argument("--edition", choices=tuple(EDITIONS))
    parser.add_argument("--volume", type=int)
    parser.add_argument("--units", nargs="*")
    parser.add_argument("--mocktests", nargs="*")
    parser.add_argument("--all-editions", action="store_true",
                        help="generate every project; print 'path stem index' per line")
    arguments = parser.parse_args(argv)
    try:
        if arguments.all_editions:
            for project in build_all(arguments.root, arguments.book, units=arguments.units,
                                     mocktests=arguments.mocktests):
                print(project.path, project.output_stem, int(project.index))
            return 0
        if arguments.edition is None:
            parser.error("--edition or --all-editions is required")
        project = build(arguments.root, arguments.book, arguments.edition, units=arguments.units,
                        mocktests=arguments.mocktests, volume=arguments.volume)
        print(project.path, project.output_stem, int(project.index))
    except (OSError, ValueError, KeyError) as error:
        print(f"FAIL: publish {arguments.book}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
