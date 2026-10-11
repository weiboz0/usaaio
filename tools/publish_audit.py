"""Audit the generated edition projects of one book (Plan 030 D5).

`python -m tools.publish_audit --book <id> [--units U...] [--mocktests T...] [--glossary-only]`

The expected scope comes from this invocation (full when neither `--units` nor `--mocktests` is
given), never from the projects' own `scope.json`, and a disagreement is an error.

Rules:
1. Chapters: each project's `_quarto.yml` chapter list matches this module's own edition table
   for the scope (full: every configured unit, volumes and the teacher's mock part; scoped:
   exactly the requested units and mock tests).
2. Source isolation:
   - provenance (primary): every chapter's text is exactly the concatenation of its sidecar's
     segments; every scaffold segment matches a fixed pattern; every sourced segment is
     re-derived from its source span and checked against this module's own rule table of
     allowed (edition, chapter, source class, segment kind) blocks. Answer bodies (`<details>`
     bodies and open answer sections) are located by this module's own parser, so a sidecar
     that labels an answer body as ordinary markdown is caught;
   - inventory: no student edition lists a non-selected solution or mock-test material;
   - fingerprints (defense in depth): normalized source lines of 40 or more characters from
     solutions, mock solutions and rubrics, and answer bodies may not appear where forbidden.
3. Glyphs: a "Missing character" line in any LaTeX log (editions and build-pdf) is an error.
4. References: undefined or multiply defined references in the draft-mode log are errors.
5. Glossary: every concept the (in-scope) units introduce has a glossary entry, and every entry
   carries `<!-- concept: <id> -->`.
6. Page counts are reported; over `audit.page_warning` is a warning.

Independence: the allowed-block rule table, the source classification, the answer-region parser,
the selected-answer evaluation and the scaffold patterns are this module's own. It imports only
the publisher's pure text transforms (`markdown_text`, `fence_code`, `title_text`), which map a
source span to its printed form. They cannot add content from outside the span, so they cannot
certify a leak: the audit itself decides which spans may be printed.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from tools.books import BookSpec, PublicationConfig, load_book_catalog, load_publication_config
from tools.publish import fence_code, markdown_text, title_text

# --- the audit's own edition table -----------------------------------------------------------

AUDIT_EDITIONS: dict[str, dict[str, Any]] = {
    "student-print": {"front": ("index", "how-to-use"), "body": "book", "appendix": False,
                      "mock": False, "back": True, "index": True, "student": True,
                      "statement_code": False},
    "student": {"front": ("index", "how-to-use"), "body": "book", "appendix": True,
                "mock": False, "back": True, "index": True, "student": True,
                "statement_code": True},
    "answer-key": {"front": ("index",), "body": "answers", "appendix": False, "mock": False,
                   "back": False, "index": False, "student": True, "statement_code": False},
    "teacher": {"front": ("index", "how-to-use", "for-teachers"), "body": "book",
                "appendix": False, "mock": True, "back": True, "index": True, "student": False,
                "statement_code": True},
}
FRONT_SOURCES = {"index": None, "how-to-use": "how-to-use.md", "for-teachers": "for-teachers.md"}
FRONT_FIRST = {"student-print": "preface.md", "student": "preface.md",
               "answer-key": "answer-key-intro.md", "teacher": "preface.md"}
BACK_CHAPTERS = ("notation", "glossary")
ANSWER_KINDS = frozenset({"details-body", "answer-body", "answer-code"})
FINGERPRINT_MIN = 40

AUDIT_FENCE = re.compile(r"^\s*(?:(?:[-*+]|\d+[.)])\s+)*(`{3,}|~{3,})")
AUDIT_FENCE_CLOSE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")
AUDIT_DETAILS = re.compile(r"<details\b[^>]*>|</details\s*>", re.IGNORECASE)
AUDIT_SUMMARY = re.compile(r"\s*<summary\b[^>]*>(.*?)</summary\s*>", re.IGNORECASE | re.DOTALL)
AUDIT_ANSWER_HEADING = re.compile(
    r"(?i)^#+\s*(collected\s+)?((checkpoint|self-quiz|quiz)\s*\d*\s+)?answers\b")
AUDIT_ANSWER_PARAGRAPH = re.compile(r"\*\*Collected (checkpoint )?answers\.\*\*")
# Safety net (student editions outside the answers appendix): a printed answer lead-in.
ANSWER_LEAD = re.compile(r"(?i)^\**collected (checkpoint )?answers\b")
AUDIT_HEADING = re.compile(r"^(#{1,6})(?=\s|$)")
CONCEPT_NOTE = re.compile(r"<!--\s*concepts?:\s*([^;>]*?)\s*(?:;[^>]*)?-->")
GLOSSARY_ENTRY = re.compile(r"^\*\*(.+?)\*\*\s*[—–:-]")
EDITION_MARK = re.compile(r"^\s*<!--\s*(/edition|edition:\s*([a-z|\s-]+))\s*-->\s*$")
INDEX_SPAN = re.compile(r"`\\index\{[^`]*\}`\{=latex\}")
LABEL = r"[\w.-]+"

# Fixed scaffolding the publisher may write (exact strings and patterns).
SCAFFOLD_EXACT = frozenset({
    "## Practice", "#### Solution", "## Answers", "*Answers", " (", ", ", "; ", ")", ".*", "**",
    "*Answers: ", "::: {.answers}", ":::",
    ": open this notebook, or see the Teacher's Edition.*",
    "\\pubchapterlabel{}\n\n\\printindex",
    '# Answers to Checkpoints and Selected Practice {pub-label=""}',
})
SCAFFOLD_PATTERNS = (
    re.compile(r'# [^\n{}]+ \{#ch-' + LABEL + r' pub-label="Unit ' + LABEL
               + r'"(?: pub-mainmatter="true")?\}'),
    re.compile(r"```\{=latex\}\n\\chaptermark\{[^\n]*\}\n```"),
    re.compile(r"```\{=latex\}\n(?:\\index\{[^\n{}]*\})+\n```"),
    re.compile(r"#{2,4} (?:Unit Overview|Review)"),
    re.compile(r"\*Practice file:\* `units/" + LABEL + r"/practice/p\d+\.ipynb`"),
    re.compile(r"\*Answer: see page `\\pageref\{ans-" + LABEL + r"\}`\{=latex\}\.\*"),
    re.compile(r" \(page `\\pageref\{" + LABEL + r"\}`\{=latex\}\)"),
    re.compile(r"page `\\pageref\{" + LABEL + r"\}`\{=latex\}"),
    re.compile(r"## [^\n]{1,160}"),
    re.compile(r"### [^\n]{1,160} \{#" + LABEL + r"-d\d+\}"),
    re.compile(r"## Practice p\d+ \{#ans-" + LABEL + r"\}"),
    re.compile(r"### Practice p\d+ \{#ans-" + LABEL + r"\}"),
    re.compile(r'# Mock Test ' + LABEL + r' \{#mock-' + LABEL + r' pub-label="Mock test"\}'),
    re.compile(r"### Solution: `solutions/p\d+_solution\.ipynb`"),
)


@dataclass
class AuditResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)


@dataclass(frozen=True)
class AuditScope:
    mode: str
    units: tuple[str, ...]
    mocktests: tuple[str, ...]


# --- the audit's own source parsing -----------------------------------------------------------


def _fence_lines(text: str) -> list[tuple[int, str, bool]]:
    """(offset, line, inside or on a fence) for each line."""
    result = []
    fence: str | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        if fence is None:
            match = AUDIT_FENCE.match(line)
            if match:
                fence = match[1]
                result.append((offset, line, True))
            else:
                result.append((offset, line, False))
        else:
            close = AUDIT_FENCE_CLOSE.match(line)
            if close and close[1][0] == fence[0] and len(close[1]) >= len(fence):
                fence = None
            result.append((offset, line, True))
        offset += len(line)
    return result


@dataclass(frozen=True)
class DetailsSpan:
    start: int
    name_end: int  # end of the <summary> (start of the body)
    body_end: int
    end: int
    summary: str


def audit_details(text: str) -> list[DetailsSpan]:
    fenced = [(offset, offset + len(line)) for offset, line, inside in _fence_lines(text) if inside]
    blocks: list[DetailsSpan] = []
    opened: tuple[int, int] | None = None
    for token in AUDIT_DETAILS.finditer(text):
        if any(a <= token.start() < b for a, b in fenced):
            continue
        if not token.group().startswith("</"):
            opened = (token.start(), token.end())
            continue
        if opened is None:
            continue
        summary = AUDIT_SUMMARY.match(text, opened[1])
        name_end = summary.end() if summary else opened[1]
        blocks.append(DetailsSpan(opened[0], name_end, token.start(), token.end(),
                                  summary[1] if summary else ""))
        opened = None
    return blocks


def audit_details_name(summary: str) -> str:
    plain = " ".join(re.sub(r"<[^>]+>", "", summary).split())
    return plain if re.fullmatch(r"Checkpoint \d+|Answers \d+[–-]\d+", plain) else "Self-quiz answers"


@dataclass
class SourceAnswers:
    """Where a notebook's answers are: forbidden spans per cell, and whole answer cells."""

    spans: dict[int, list[tuple[int, int]]] = field(default_factory=dict)
    details: dict[int, list[DetailsSpan]] = field(default_factory=dict)
    cells: set[int] = field(default_factory=set)  # code cells inside an open answer section

    def add(self, cell: int, start: int, end: int) -> None:
        self.spans.setdefault(cell, []).append((start, end))

    def overlaps(self, cell: int, start: int, end: int) -> bool:
        return any(start < b and a < end for a, b in self.spans.get(cell, []))

    def bodies(self, cells: list[dict[str, Any]]) -> list[str]:
        texts = []
        for cell, spans in self.spans.items():
            source = cells[cell]["source"]
            texts += [source[a:b] for a, b in spans]
        texts += [cells[cell]["source"] for cell in self.cells]
        return texts


def read_cells(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    cells = []
    for cell in raw.get("cells", []):
        source = cell.get("source", "")
        cells.append({"cell_type": cell.get("cell_type", ""),
                      "source": "".join(source) if isinstance(source, list) else source})
    return cells


def notebook_answers(cells: list[dict[str, Any]], *, sections: bool) -> SourceAnswers:
    answers = SourceAnswers()
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "markdown":
            continue
        for block in audit_details(cell["source"]):
            answers.details.setdefault(index, []).append(block)
            answers.add(index, block.name_end, block.end)
    if not sections:
        return answers
    open_level: int | None = None
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "markdown":
            if open_level is not None:
                answers.cells.add(index)
            continue
        text = cell["source"]
        section_start = 0 if open_level is not None else None
        for offset, line, inside in _fence_lines(text):
            if inside:
                continue
            heading = AUDIT_HEADING.match(line)
            if not heading:
                continue
            level = len(heading[1])
            if open_level is not None and level <= open_level:
                answers.add(index, section_start or 0, offset)
                open_level, section_start = None, None
            if open_level is None and AUDIT_ANSWER_HEADING.match(line):
                open_level, section_start = level, offset + len(line)
        if open_level is not None:
            answers.add(index, section_start or 0, len(text))
    # Inline answer paragraphs: a paragraph whose first line opens `**Collected answers.**`.
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "markdown":
            continue
        start: int | None = None
        previous_blank = True
        text = cell["source"]
        for offset, line, inside in _fence_lines(text):
            blank = not line.strip()
            if start is not None and (blank or inside):
                answers.add(index, start, offset)
                start = None
            if start is None and not inside and previous_blank and AUDIT_ANSWER_PARAGRAPH.match(line):
                start = offset
            previous_blank = blank and not inside
        if start is not None:
            answers.add(index, start, len(text))
    return answers


# --- source classes and selected answers ------------------------------------------------------


def classify(source: str) -> tuple[str, str]:
    """(class, owner) for a book-relative source path."""
    parts = source.split("/")
    if parts[0] == "front-matter" and len(parts) == 2:
        return "front", parts[1]
    if parts[0] == "back-matter" and len(parts) == 2:
        return "back", parts[1]
    if parts[0] == "units" and len(parts) >= 3:
        unit = parts[1]
        if parts[2] == "practice" and len(parts) == 4:
            if parts[3].endswith("_solution.ipynb"):
                return "solution", unit
            return "statement", unit
        if parts[2:] in (["lesson.ipynb"], ["review.ipynb"]) or (
                parts[2] == "lessons" and len(parts) == 4):
            return "lesson", unit
    if parts[0] == "mocktests" and len(parts) >= 3:
        if parts[2] in ("solutions", "rubric.md"):
            return "mock-solution", parts[1]
        return "mock-paper", parts[1]
    return "unknown", ""


def selected_solutions(book: BookSpec, config: PublicationConfig) -> set[str]:
    """Book-relative solution paths the student editions may print (own selector evaluation)."""
    result = set()
    for unit in config.units:
        manifest = yaml.safe_load(
            (book.root / "units" / unit / "manifest.yaml").read_text(encoding="utf-8")) or {}
        for row in manifest.get("practice") or []:
            if not isinstance(row, dict):
                continue
            if all(str(row.get(key)) in values for key, values in config.student_answers.items()):
                result.add(f"units/{unit}/{row['solution_path']}")
    return result


def unit_rows(book: BookSpec, unit: str) -> list[dict[str, Any]]:
    manifest = yaml.safe_load(
        (book.root / "units" / unit / "manifest.yaml").read_text(encoding="utf-8")) or {}
    return [row for row in manifest.get("practice") or [] if isinstance(row, dict)]


def allowed(edition: str, chapter_kind: str, chapter_owner: str, source_class: str,
            source_owner: str, segment_kind: str, source: str, selected: set[str]) -> bool:
    """The audit's own table of blocks each edition may print in each chapter."""
    profile = AUDIT_EDITIONS[edition]
    is_answer = segment_kind in ANSWER_KINDS
    if chapter_kind == "front":
        return source_class == "front" and segment_kind == "markdown"
    if chapter_kind == "back":
        return source_class == "back" and segment_kind == "markdown"
    if chapter_kind == "unit":
        if source_owner != chapter_owner:
            return False
        if source_class == "lesson":
            return edition == "teacher" or not is_answer
        if source_class == "statement":
            if segment_kind == "code" and not profile["statement_code"]:
                return False
            return edition == "teacher" or not is_answer
        if source_class == "solution":
            return edition == "teacher"
        return False
    if chapter_kind == "appendix":
        if edition != "student":
            return False
        if source_class in ("lesson", "statement"):
            return is_answer or segment_kind == "details-name"
        if source_class == "solution":
            return source in selected and segment_kind != "title"
        return False
    if chapter_kind == "answers":
        return (edition == "answer-key" and source_class == "solution"
                and source_owner == chapter_owner and source in selected
                and segment_kind != "title")
    if chapter_kind == "mock":
        return edition == "teacher" and source_class in ("mock-paper", "mock-solution") \
            and source_owner == chapter_owner
    return False


# --- rule 1: chapters ---------------------------------------------------------------------------


def chapter_kind(file: str, units: Iterable[str]) -> tuple[str, str]:
    stem = file.removesuffix(".qmd")
    if stem in FRONT_SOURCES:
        return "front", stem
    if stem in BACK_CHAPTERS:
        return "back", stem
    if stem == "the-index":
        return "index", ""
    if stem == "answers":
        return "appendix", ""
    if stem.startswith("answers-") and stem.removeprefix("answers-") in units:
        return "answers", stem.removeprefix("answers-")
    if stem.startswith("mock-"):
        return "mock", stem.removeprefix("mock-")
    if stem in units:
        return "unit", stem
    return "unknown", stem


def has_answer_units(book: BookSpec, unit: str, selected: set[str]) -> bool:
    if any(f"units/{unit}/{row['solution_path']}" in selected for row in unit_rows(book, unit)):
        return True
    unit_root = book.root / "units" / unit
    sources = [unit_root / "lesson.ipynb", *sorted((unit_root / "lessons").glob("*.ipynb")),
               unit_root / "review.ipynb",
               *(unit_root / str(row["path"]) for row in unit_rows(book, unit))]
    for path in sources:
        if path.is_file():
            answers = notebook_answers(read_cells(path), sections="/practice/" not in path.as_posix())
            if answers.spans or answers.cells:
                return True
    return False


def expected_projects(book: BookSpec, config: PublicationConfig,
                      scope: AuditScope) -> dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]]:
    """project directory name -> (edition, body units, mock tests)."""
    projects = {}
    for edition in AUDIT_EDITIONS:
        if scope.mode == "full" and edition in config.volume_editions:
            for volume in config.volumes:
                last = volume.number == len(config.volumes)
                projects[f"{edition}-vol{volume.number}"] = (
                    edition, volume.units, scope.mocktests if last else ())
        else:
            projects[edition] = (edition, scope.units, scope.mocktests)
    return projects


def expected_chapters(book: BookSpec, edition: str, units: tuple[str, ...],
                      mocktests: tuple[str, ...], selected: set[str]) -> list[str]:
    profile = AUDIT_EDITIONS[edition]
    chapters = [f"{name}.qmd" for name in profile["front"]]
    if profile["body"] == "answers":
        for unit in units:
            if any(f"units/{unit}/{row['solution_path']}" in selected
                   for row in unit_rows(book, unit)):
                chapters.append(f"answers-{unit}.qmd")
        return chapters
    chapters += [f"{unit}.qmd" for unit in units]
    if profile["appendix"] and any(has_answer_units(book, unit, selected) for unit in units):
        chapters.append("answers.qmd")
    if profile["mock"]:
        chapters += [f"mock-{test}.qmd" for test in mocktests]
    if profile["back"]:
        chapters += [f"{name}.qmd" for name in BACK_CHAPTERS]
    if profile["index"]:
        chapters.append("the-index.qmd")
    return chapters


def quarto_chapters(project: Path) -> list[str]:
    raw = yaml.safe_load((project / "_quarto.yml").read_text(encoding="utf-8")) or {}
    result: list[str] = []

    def walk(items: Any) -> None:
        for item in items or []:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                walk(item.get("chapters"))
    walk((raw.get("book") or {}).get("chapters"))
    return result


# --- rule 2: provenance -------------------------------------------------------------------------


class SourceCache:
    def __init__(self, book: BookSpec):
        self.book = book
        self.texts: dict[str, Any] = {}
        self.answers: dict[str, SourceAnswers] = {}

    def cells(self, source: str) -> list[dict[str, Any]]:
        if source not in self.texts:
            path = self.book.root / source
            if source.endswith(".ipynb"):
                self.texts[source] = read_cells(path)
            else:
                self.texts[source] = [{"cell_type": "markdown",
                                       "source": path.read_text(encoding="utf-8")}]
        return self.texts[source]

    def text(self, source: str, cell: int) -> str:
        cells = self.cells(source)
        return cells[max(cell, 0)]["source"]

    def answers_of(self, source: str) -> SourceAnswers:
        if source not in self.answers:
            klass, _ = classify(source)
            if source.endswith(".ipynb"):
                self.answers[source] = notebook_answers(self.cells(source),
                                                        sections=klass == "lesson")
            else:
                self.answers[source] = SourceAnswers()
        return self.answers[source]


def _scaffold_ok(text: str) -> bool:
    return text in SCAFFOLD_EXACT or any(pattern.fullmatch(text) for pattern in SCAFFOLD_PATTERNS)


def _matter_lines_ok(text: str, source: str, edition: str) -> list[str]:
    """Front and back matter: every printed line comes from the source, outside other editions'
    marker blocks (index spans and heading levels aside)."""
    problems = []
    allowed_lines: set[str] = set()
    active: list[str] | None = None
    for line in source.splitlines():
        marker = EDITION_MARK.match(line)
        if marker:
            active = None if marker[1] == "/edition" else [
                name.strip() for name in (marker[2] or "").split("|")]
            continue
        if active is None or edition in active:
            allowed_lines.add(line.lstrip("#").strip())
    for line in text.splitlines():
        plain = INDEX_SPAN.sub("", line)
        plain = re.sub(r'\s*\{pub-label=""\}\s*$', "", plain).lstrip("#").strip()
        if plain and plain not in allowed_lines:
            problems.append(plain[:80])
    return problems


def check_chapter(result: AuditResult, project: Path, file: str, edition: str,
                  units: tuple[str, ...], cache: SourceCache, selected: set[str]) -> None:
    where = f"{project.name}/{file}"
    sidecar_path = project / "provenance" / (file.removesuffix(".qmd") + ".json")
    if not sidecar_path.is_file():
        result.error(f"{where}: provenance sidecar missing")
        return
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    segments = sidecar.get("segments") or []
    chapter_text = (project / file).read_text(encoding="utf-8")
    joined = "".join(str(seg.get("sep", "")) + str(seg.get("text", "")) for seg in segments)
    if joined.lstrip("\n") + "\n" != chapter_text:
        result.error(f"{where}: chapter text is not the concatenation of its declared blocks "
                     "(an undeclared block)")
    kind, owner = chapter_kind(file, units)
    for number, segment in enumerate(segments):
        label = f"{where} segment {number}"
        seg_kind = segment.get("kind")
        text = str(segment.get("text", ""))
        if seg_kind == "scaffold":
            if not _scaffold_ok(text):
                result.error(f"{label}: scaffold text is not a fixed publisher pattern: "
                             f"{text[:60]!r}")
            continue
        source = str(segment.get("source", ""))
        source_class, source_owner = classify(source)
        if source_class == "unknown":
            result.error(f"{label}: unknown source {source!r}")
            continue
        if not allowed(edition, kind, owner, source_class, source_owner, str(seg_kind), source,
                       selected):
            result.error(f"{label}: {seg_kind} block from {source} is not allowed in "
                         f"{edition} {kind} chapter")
            continue
        try:
            _check_segment(result, label, segment, source, source_class, edition, cache, kind)
        except (OSError, IndexError, ValueError, KeyError) as error:
            result.error(f"{label}: cannot re-derive from {source}: {error}")


def _check_segment(result: AuditResult, label: str, segment: dict[str, Any], source: str,
                   source_class: str, edition: str, cache: SourceCache, kind: str) -> None:
    seg_kind = segment["kind"]
    cell = int(segment.get("cell", -1))
    start, end = (int(value) for value in segment.get("span", (0, 0)))
    text = str(segment["text"])
    if source_class in ("front", "back"):
        problems = _matter_lines_ok(text, cache.text(source, -1), edition)
        if problems:
            result.error(f"{label}: lines not printable from {source} in {edition}: {problems[:2]}")
        return
    full = cache.text(source, cell)
    piece = full[start:end]
    answers = cache.answers_of(source)
    may_print_answers = edition == "teacher" or kind in ("appendix", "answers")
    if seg_kind in ("markdown", "title"):
        if not may_print_answers and answers.overlaps(cell, start, end):
            result.error(f"{label}: {seg_kind} span overlaps an answer body in {source}")
        if seg_kind == "markdown":
            expected = markdown_text(piece, int(segment.get("shift", 0)))
        else:
            level = int(segment.get("level", 1))
            if not piece.lstrip().startswith("# "):
                result.error(f"{label}: title span is not a notebook title in {source}")
                return
            heading = str(segment.get("title") or "") or title_text(piece, source.split("/")[1]
                                                                   if "/" in source else "")
            expected = "#" * level + " " + heading
        if text != expected:
            result.error(f"{label}: text does not match {source} cell {cell} span {start}:{end}")
    elif seg_kind in ("code", "answer-code"):
        if not may_print_answers and cell in answers.cells:
            result.error(f"{label}: code cell {cell} of {source} is inside an answer section")
        if cache.cells(source)[cell]["cell_type"] != "code" or text != fence_code(full):
            result.error(f"{label}: code text does not match {source} cell {cell}")
    elif seg_kind == "details-name":
        blocks = answers.details.get(cell, [])
        block = next((b for b in blocks if (b.start, b.name_end) == (start, end)), None)
        if block is None or text != audit_details_name(block.summary):
            result.error(f"{label}: details name does not match a <details> summary in {source}")
    elif seg_kind in ("details-body", "answer-body"):
        if not (answers.overlaps(cell, start, end)):
            result.error(f"{label}: {seg_kind} span is not an answer body in {source}")
        if text != markdown_text(piece, int(segment.get("shift", 0))):
            result.error(f"{label}: text does not match {source} cell {cell} span {start}:{end}")
    else:
        result.error(f"{label}: unknown segment kind {seg_kind!r}")


# --- rule 2: fingerprints -----------------------------------------------------------------------


def _normalize(line: str) -> str:
    return " ".join(line.strip().lstrip("#").split())


def _lines(text: str) -> set[str]:
    return {_normalize(line) for line in text.splitlines()}


def fingerprints(book: BookSpec, config: PublicationConfig, selected: set[str],
                 cache: SourceCache) -> dict[str, set[str]]:
    """'selected' / 'solution' (others) / 'mock' / 'details' -> fingerprint lines."""
    result: dict[str, set[str]] = {"selected": set(), "solution": set(), "mock": set(),
                                   "details": set()}

    def long_lines(text: str, minus: set[str]) -> set[str]:
        return {line for line in (_normalize(raw) for raw in text.splitlines())
                if len(line) >= FINGERPRINT_MIN and line not in minus}

    for unit in config.units:
        for row in unit_rows(book, unit):
            statement = f"units/{unit}/{row['path']}"
            solution = f"units/{unit}/{row['solution_path']}"
            if not (book.root / solution).is_file():
                continue
            minus = set()
            if (book.root / statement).is_file():
                minus = _lines("\n".join(cell["source"] for cell in cache.cells(statement)))
            text = "\n".join(cell["source"] for cell in cache.cells(solution))
            key = "selected" if solution in selected else "solution"
            result[key] |= long_lines(text, minus)
        unit_root = book.root / "units" / unit
        for path in [unit_root / "lesson.ipynb", *sorted((unit_root / "lessons").glob("*.ipynb")),
                     unit_root / "review.ipynb"]:
            if not path.is_file():
                continue
            source = path.relative_to(book.root).as_posix()
            cells = cache.cells(source)
            answers = cache.answers_of(source)
            bodies = answers.bodies(cells)
            if not bodies:
                continue
            stripped_cells = []
            for index, cell in enumerate(cells):
                if index in answers.cells:
                    continue
                text = cell["source"]
                for a, b in sorted(answers.spans.get(index, []), reverse=True):
                    text = text[:a] + text[b:]
                stripped_cells.append(text)
            minus = _lines("\n".join(stripped_cells))
            result["details"] |= long_lines("\n".join(bodies), minus)
    public: set[str] = set()  # lines any student edition may print anyway
    for unit in config.units:
        unit_root = book.root / "units" / unit
        sources = [unit_root / "lesson.ipynb", *sorted((unit_root / "lessons").glob("*.ipynb")),
                   unit_root / "review.ipynb",
                   *(unit_root / str(row["path"]) for row in unit_rows(book, unit))]
        for path in sources:
            if not path.is_file():
                continue
            source = path.relative_to(book.root).as_posix()
            cells = cache.cells(source)
            answers = cache.answers_of(source)
            for index, cell in enumerate(cells):
                if index in answers.cells:
                    continue
                text = cell["source"]
                for a, b in sorted(answers.spans.get(index, []), reverse=True):
                    text = text[:a] + text[b:]
                public |= _lines(text)
    for folder in ("front-matter", "back-matter"):
        for path in sorted((book.root / folder).glob("*.md")):
            public |= _lines(path.read_text(encoding="utf-8"))
    for manifest in sorted(book.root.glob("mocktests/*/manifest.yaml")):
        root = manifest.parent
        paper = [path for path in root.rglob("*") if path.is_file()
                 and path.suffix in (".md", ".ipynb")
                 and "solutions" not in path.relative_to(root).parts and path.name != "rubric.md"]
        minus: set[str] = set()
        for path in paper:
            minus |= _lines(_plain(path))
        for path in [*sorted((root / "solutions").glob("*")), root / "rubric.md"]:
            if path.is_file() and path.suffix in (".md", ".ipynb"):
                result["mock"] |= long_lines(_plain(path), minus)
        public |= minus
    # A line that a student edition prints from a student-facing source is no leak; a line a
    # selected solution shares with another solution may print where selected answers may.
    for key in result:
        result[key] -= public
    result["solution"] -= result["selected"]
    result["mock"] -= result["selected"]
    return result


def _plain(path: Path) -> str:
    if path.suffix == ".ipynb":
        return "\n".join(cell["source"] for cell in read_cells(path))
    return path.read_text(encoding="utf-8")


def check_fingerprints(result: AuditResult, project: Path, edition: str,
                       chapters: list[str], prints: dict[str, set[str]]) -> None:
    if not AUDIT_EDITIONS[edition]["student"]:
        return
    for file in chapters:
        path = project / file
        if not path.is_file():
            continue
        if edition != "answer-key" and not (edition == "student" and file == "answers.qmd"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if ANSWER_LEAD.match(line.strip()):
                    result.error(f"{project.name}/{file}: printed answer lead-in "
                                 f"{line.strip()[:60]!r}")
                    break
        lines = _lines(path.read_text(encoding="utf-8"))
        forbidden = {"solution": prints["solution"], "mock": prints["mock"]}
        if not (edition == "student" and file == "answers.qmd") and edition != "answer-key":
            forbidden["selected"] = prints["selected"]
            forbidden["details"] = prints["details"]
        for key, values in forbidden.items():
            hits = lines & values
            if hits:
                result.error(f"{project.name}/{file}: fingerprint of {key} material: "
                             f"{min(hits)[:70]!r}")


# --- rules 3, 4, 6 -------------------------------------------------------------------------------


def check_logs(result: AuditResult, logs: Iterable[Path]) -> None:
    for log in logs:
        text = log.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if "Missing character" in line:
                result.error(f"{log}: {line.strip()}")
                break


def check_references(result: AuditResult, log: Path) -> None:
    if not log.is_file():
        result.error(f"{log}: draft-mode LaTeX log missing")
        return
    text = log.read_text(encoding="utf-8", errors="replace")
    for pattern in (r"LaTeX Warning: Reference `[^']*' on page \d+ undefined",
                    r"There were undefined references", r"LaTeX Warning: Label `[^']*' multiply defined"):
        match = re.search(pattern, text)
        if match:
            result.error(f"{log}: {match.group()}")


def page_count(project: Path, stem: str) -> int | None:
    pages = project / "pages.txt"
    if pages.is_file() and pages.read_text().strip().isdigit():
        return int(pages.read_text().strip())
    pdf = project / "_book" / f"{stem}.pdf"
    if not pdf.is_file():
        return None
    proc = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=False)
    match = re.search(r"^Pages:\s+(\d+)", proc.stdout, re.MULTILINE)
    return int(match[1]) if match else None


# --- rule 5: glossary ---------------------------------------------------------------------------


def check_glossary(result: AuditResult, book: BookSpec, units: Iterable[str]) -> None:
    path = book.root / "back-matter" / "glossary.md"
    if not path.is_file():
        result.error(f"{book.id}: back-matter/glossary.md missing")
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    covered: set[str] = set()
    for index, line in enumerate(lines):
        if not GLOSSARY_ENTRY.match(line.strip()):
            continue
        note = None
        for following in lines[index:index + 4]:
            if following is not line and GLOSSARY_ENTRY.match(following.strip()):
                break
            note = CONCEPT_NOTE.search(following) or note
            if note:
                break
        if note is None:
            result.error(f"{book.id}: glossary entry without <!-- concept: id -->: {line[:60]!r}")
            continue
        covered |= {part for part in re.split(r"[,\s]+", note[1]) if part}
    introduced: set[str] = set()
    for unit in units:
        manifest = yaml.safe_load(
            (book.root / "units" / unit / "manifest.yaml").read_text(encoding="utf-8")) or {}
        introduced |= {str(c) for c in manifest.get("concepts_taught") or [] if ":" not in str(c)}
    missing = sorted(introduced - covered)
    if missing:
        result.error(f"{book.id}: glossary misses introduced concept(s) {missing}")


# --- driver --------------------------------------------------------------------------------------


def audit(repo_root: Path, book_id: str, *, units: list[str] | None = None,
          mocktests: list[str] | None = None, glossary_only: bool = False) -> AuditResult:
    result = AuditResult()
    book = load_book_catalog(Path(repo_root).resolve()).by_id(book_id)
    config = load_publication_config(book)
    if units is None and mocktests is None:
        scope = AuditScope("full", config.units, config.mocktests)
    else:
        scope = AuditScope("scoped", tuple(u for u in config.units if u in (units or [])),
                           tuple(dict.fromkeys(mocktests or [])))
        unknown = sorted(set(units or []) - set(config.units))
        if unknown:
            result.error(f"{book_id}: scoped units are not configured chapters: {unknown}")
    check_glossary(result, book, scope.units)
    if glossary_only:
        return result
    selected = selected_solutions(book, config)
    cache = SourceCache(book)
    prints = fingerprints(book, config, selected, cache)
    base = book.root / "build" / ("publish" if scope.mode == "full" else "publish-check")
    page_warning = int(config.audit.get("page_warning", 0) or 0)
    for name, (edition, body_units, tests) in expected_projects(book, config, scope).items():
        project = base / name
        if not project.is_dir():
            result.error(f"{book_id}: project {project.relative_to(book.root)} missing")
            continue
        recorded = json.loads((project / "scope.json").read_text(encoding="utf-8")) \
            if (project / "scope.json").is_file() else {}
        if (recorded.get("mode"), tuple(recorded.get("units") or ()),
                tuple(recorded.get("mocktests") or ())) != (scope.mode, scope.units,
                                                            scope.mocktests):
            result.error(f"{name}: scope.json {recorded.get('mode')} units="
                         f"{recorded.get('units')} mocktests={recorded.get('mocktests')} disagrees "
                         f"with the invocation scope {scope.mode} units={list(scope.units)} "
                         f"mocktests={list(scope.mocktests)}")
        expected = expected_chapters(book, edition, body_units, tests, selected)
        actual = quarto_chapters(project)
        if actual != expected:
            result.error(f"{name}: chapters {actual} != expected {expected}")
        inventory = json.loads((project / "inventory.json").read_text(encoding="utf-8")) \
            if (project / "inventory.json").is_file() else {"chapters": []}
        if AUDIT_EDITIONS[edition]["student"]:
            for chapter in inventory.get("chapters", []):
                for source in chapter.get("sources", []):
                    klass, _ = classify(source)
                    if klass.startswith("mock"):
                        result.error(f"{name}: student edition lists mock-test material {source}")
                    if klass == "solution" and source not in selected:
                        result.error(f"{name}: student edition lists solution {source}")
        for file in actual:
            if (project / file).is_file():
                check_chapter(result, project, file, edition, config.units, cache, selected)
        check_fingerprints(result, project, edition, actual, prints)
        stem = output_stem_of(project)
        check_logs(result, sorted(project.glob("*.log")))
        if stem:
            check_references(result, project / f"{stem}.log")
            pages = page_count(project, stem)
            result.info.append(f"{name}: {pages} pages")
            if pages and page_warning and pages > page_warning:
                result.warnings.append(f"{name}: {pages} pages is over {page_warning}")
    pdf_logs = sorted((book.root / "build" / "pdf").rglob("*.log")) \
        if (book.root / "build" / "pdf").is_dir() else []
    check_logs(result, pdf_logs)
    return result


def output_stem_of(project: Path) -> str:
    raw = yaml.safe_load((project / "_quarto.yml").read_text(encoding="utf-8")) or {}
    return str((raw.get("book") or {}).get("output-file") or "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.publish_audit")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--book", required=True)
    parser.add_argument("--units", nargs="*")
    parser.add_argument("--mocktests", nargs="*")
    parser.add_argument("--glossary-only", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        result = audit(arguments.root, arguments.book, units=arguments.units,
                       mocktests=arguments.mocktests, glossary_only=arguments.glossary_only)
    except (OSError, ValueError, KeyError) as error:
        print(f"FAIL publish-audit {arguments.book}: {error}", file=sys.stderr)
        return 1
    for line in result.info:
        print(f"publish-audit {arguments.book}: {line}")
    for warning in result.warnings:
        print(f"WARNING publish-audit {arguments.book}: {warning}")
    for error in result.errors:
        print(f"FAIL publish-audit {arguments.book}: {error}", file=sys.stderr)
    if result.errors:
        print(f"publish-audit {arguments.book}: {len(result.errors)} error(s)", file=sys.stderr)
        return 1
    print(f"publish-audit {arguments.book}: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
