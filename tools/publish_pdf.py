"""The per-book syllabus, handout, and mock-test PDFs (Plan 030 D4; py4kids' build-pdf.sh role).

`scripts/build-pdf.sh --book <id>` calls this module. It writes, through `tools.publish_output`
(owner `pdf`), into `output/<book>/`:

- `syllabus.pdf` from `<book>/docs/course-structure.md`;
- `handouts/<unit>.pdf`: one per live unit, its practice statement notebooks in manifest order,
  `<details>` handled as in `student-print` (a pointer, never the body);
- `mocktests/<test>-paper.pdf`: `test.md`, then each item file once, at its first occurrence in
  manifest problem order;
- `mocktests/<test>-solutions.pdf`: `solutions/answers.md`, `rubric.md`, then
  `solutions/pNN_solution.ipynb` in problem order.

Every PDF renders from the publisher's shared converter (`tools.publish`: output stripping,
`<details>` handling, math normalization), then pandoc to `.tex`, then lualatex with the edition
theme's fonts and DejaVu fallback (`tools/publish_theme/fonts.tex`). Each LaTeX log is kept next
to its PDF under `<book>/build/pdf/`; a "Missing character" line fails the build (D5 rule 3).
Every source and output path is resolved inside the registered book root, and symlink components
are refused (`tools.books.resolve_contained_path`).
"""

from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from tools.books import (
    BookSpec,
    ChapterSpec,
    PublicationConfig,
    live_units,
    load_book_catalog,
    load_publication_config,
    resolve_contained_path,
    unit_dir,
)
from tools.publish import (
    THEME,
    Chapter,
    Publisher,
    fence_step,
    mock_paper_sources,
    mock_solution_sources,
)
from tools.publish_output import refresh_output

STATEMENT = re.compile(r"^p\d+\.ipynb$")
MISSING_CHARACTER = "Missing character"
HANDOUT_HEADER = r"""
\setkomafont{disposition}{\normalfont\sffamily\bfseries}
\emergencystretch=3em
\sloppy
"""


class MissingTool(RuntimeError):
    """lualatex or pandoc is not installed (build-pdf exits 3: SKIP)."""


class BuildError(RuntimeError):
    """A PDF build failure (render error, missing or empty output, missing glyph)."""


@dataclass(frozen=True)
class Target:
    kind: str  # syllabus | handout | paper | solutions
    name: str  # output path relative to output/<book>/, e.g. handouts/C3-gradient-descent.pdf
    title: str
    key: str  # unit or mock-test id ('' for the syllabus)
    sources: tuple[Path, ...]


def _contained(book: BookSpec, path: Path, *, must_exist: bool = True) -> Path:
    return resolve_contained_path(book.root, path, label="build-pdf path", must_exist=must_exist)


def _fallback_config(book: BookSpec) -> PublicationConfig:
    """Unit titles for a book without publication.yaml: the unit ids themselves."""
    units = live_units(book)
    return PublicationConfig(
        chapters=tuple(ChapterSpec(unit=unit, title=unit, head=unit[:32]) for unit in units),
        student_answers={"set": ("A",)}, mocktests=(), volume_editions=(), volumes=(), audit={})


def book_config(book: BookSpec) -> PublicationConfig:
    if book.publication and (book.root / "publication.yaml").is_file():
        return load_publication_config(book)
    return _fallback_config(book)


def _manifest(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {}


def handout_statements(book: BookSpec, unit: str) -> list[Path]:
    """A unit's practice statement notebooks: manifest `practice:` order, else `pNN.ipynb` order."""
    unit_root = unit_dir(book.root, unit)
    rows = _manifest(unit_root / "manifest.yaml").get("practice") or []
    statements = [unit_root / str(row["path"]) for row in rows
                  if isinstance(row, dict) and isinstance(row.get("path"), str)]
    if not statements:
        statements = sorted(path for path in (unit_root / "practice").glob("p*.ipynb")
                            if STATEMENT.match(path.name))
    return statements


def targets(book: BookSpec) -> list[Target]:
    config = book_config(book)
    titles = {chapter.unit: chapter.title for chapter in config.chapters}
    result: list[Target] = []
    syllabus = book.root / "docs" / "course-structure.md"
    if syllabus.exists() or syllabus.is_symlink():
        result.append(Target("syllabus", "syllabus.pdf", "Course Structure", "",
                             (_contained(book, syllabus),)))
    for unit in live_units(book):
        statements = handout_statements(book, unit)
        if not statements:
            raise BuildError(f"build-pdf: live unit {unit} yielded zero practice statements")
        result.append(Target("handout", f"handouts/{unit}.pdf", titles.get(unit, unit), unit,
                             tuple(_contained(book, path) for path in statements)))
    for manifest in sorted(book.root.glob("mocktests/*/manifest.yaml")):
        root = _contained(book, manifest).parent
        test = root.name
        result.append(Target("paper", f"mocktests/{test}-paper.pdf", f"Mock Test {test}", test,
                             tuple(_contained(book, path) for path in mock_paper_sources(root))))
        result.append(Target("solutions", f"mocktests/{test}-solutions.pdf",
                             f"Mock Test {test}: Answers and Solutions", test,
                             tuple(_contained(book, path) for path in mock_solution_sources(root))))
    return result


def list_inputs(repo_root: Path, book: BookSpec) -> list[str]:
    """Every source path any PDF reads, repo-relative, sorted and unique."""
    paths = {path.relative_to(repo_root).as_posix()
             for target in targets(book) for path in target.sources}
    return sorted(paths)


def target_markdown(repo_root: Path, book: BookSpec, target: Target) -> str:
    """The Markdown of one PDF, from the publisher's shared converter."""
    publisher = Publisher(repo_root, book, book_config(book), "student-print")
    chapter = Chapter(file=target.name, kind=target.kind, title=target.title)
    if target.kind == "syllabus":
        publisher.emit_markdown_file(chapter, target.sources[0], shift=0, details="pointer")
    elif target.kind == "handout":
        chapter.scaffold(f"# {target.title}: Practice")
        chapter.scaffold("*Answers are not printed in this handout.*")
        for path in target.sources:
            publisher.emit_notebook(chapter, path, level=2, unit=target.key, details="pointer")
    elif target.kind == "paper":
        for path in target.sources:
            if path.suffix == ".md":
                publisher.emit_markdown_file(chapter, path, shift=0, details="pointer")
            else:
                publisher.emit_notebook(chapter, path, level=1, unit=target.key, details="pointer")
    else:
        for path in target.sources:
            if path.suffix == ".md":
                publisher.emit_markdown_file(chapter, path, shift=0, details="panel")
            else:
                chapter.scaffold(f"# Solution: `{path.relative_to(path.parents[1]).as_posix()}`")
                publisher.emit_notebook(chapter, path, level=2, unit=target.key, drop_title=True,
                                        details="panel")
    return chapter.text()


TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
TABLE_WRAP_AT = 72  # pandoc's default --columns: a longer row makes a pipe table wrap
# Line capacity of the letter-page text block (6.7 in at 10 pt, about 110 characters, less a margin for wide glyphs), and the
# per-column padding (two \tabcolsep) in characters. Code characters (Fira Mono) are wider.
LINE_CHARACTERS = 95
CELL_PADDING = 3
CODE_WIDTH = 1.2


def _cells(row: str) -> list[str]:
    inner = row.strip()
    inner = inner.removeprefix("|")
    inner = inner[:-1] if inner.endswith("|") and not inner.endswith("\\|") else inner
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", inner)]


def longest_token(cell: str) -> float:
    """The width, in average characters, of a cell's longest unbreakable token.

    Text breaks at spaces and after hyphens and slashes; inline code also after `_ ( ) , : = +`
    (the theme's break points, panels.lua). Markdown emphasis markers are not printed.
    """
    widest = 0.0
    for index, part in enumerate(re.split(r"`", cell)):
        is_code = index % 2 == 1
        text = part if is_code else part.replace("**", "").replace("*", "")
        pieces = re.split(r"[\s]+|(?<=[-/])" + (r"|(?<=[_(),:=+])" if is_code else ""), text)
        for piece in pieces:
            if piece:
                widest = max(widest, len(piece) * (CODE_WIDTH if is_code else 1.0))
    return widest


def column_shares(rows: list[list[str]], columns: int) -> list[float]:
    """Relative column widths: each column at least as wide as its longest token (header cells
    included), so no word breaks; the rest goes to the columns with the most text. When the
    minimums exceed the line, the shares are proportional to the longest tokens instead."""
    minimums = []
    lengths = []
    for i in range(columns):
        cells = [row[i] for row in rows if i < len(row)]
        token = max([longest_token(cell) for cell in cells] or [1.0])
        minimums.append((token + CELL_PADDING) / LINE_CHARACTERS)
        lengths.append(max([len(cell) for cell in cells] or [1]))
    if sum(minimums) >= 1:
        total = sum(minimums)
        return [minimum / total for minimum in minimums]
    spare = 1 - sum(minimums)
    # Squared, so the long-text column takes most of the spare width.
    extra = [max(0.0, length - (minimum * LINE_CHARACTERS)) ** 2 for length, minimum
             in zip(lengths, minimums, strict=True)]
    total_extra = sum(extra) or 1.0
    return [minimum + spare * part / total_extra for minimum, part
            in zip(minimums, extra, strict=True)]


def widen_tables(markdown: str) -> str:
    """Give each wide pipe table relative column widths (its separator's dash counts), so the
    text-heavy column is not squeezed to the width of its header (Plan 030 D4)."""
    lines = markdown.splitlines(keepends=True)
    out: list[str] = []
    fence: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        is_fence, fence_after = fence_step(line, fence)
        inside = is_fence or fence is not None
        fence = fence_after
        separator = lines[index + 1] if index + 1 < len(lines) else ""
        if inside or "|" not in line or not TABLE_SEPARATOR.match(separator):
            out.append(line)
            index += 1
            continue
        end = index + 2
        while end < len(lines) and lines[end].strip().startswith("|"):
            end += 1
        block = lines[index:end]
        rows = [_cells(row) for row in block[2:]]
        header = _cells(line)
        aligns = _cells(separator)
        if max(len(row.rstrip("\n")) for row in block) <= TABLE_WRAP_AT or len(aligns) != len(header):
            out.extend(block)
            index = end
            continue
        shares = column_shares([header, *rows], len(header))
        parts = []
        for align, share in zip(aligns, shares, strict=True):
            dashes = "-" * max(3, math.ceil(share * 200))
            left = ":" if align.startswith(":") else ""
            right = ":" if align.endswith(":") else ""
            parts.append(left + dashes + right)
        out.append(line)
        out.append("|" + "|".join(parts) + "|\n")
        out.extend(block[2:])
        index = end
    return "".join(out)


def pandoc_command() -> list[str]:
    configured = os.environ.get("USAAIO_PANDOC")
    if configured:
        return [configured]
    if shutil.which("quarto"):
        return ["quarto", "pandoc"]
    if shutil.which("pandoc"):
        return ["pandoc"]
    raise MissingTool("pandoc")


def _header(workdir: Path) -> Path:
    header = workdir / "pdf-header.tex"
    fonts = (THEME / "fonts.tex").read_text(encoding="utf-8")
    header.write_text(fonts + HANDOUT_HEADER, encoding="utf-8")
    return header


def render(book: BookSpec, target: Target, markdown: str, build_root: Path, *,
           title: str, subtitle: str, env: dict[str, str]) -> Path:
    """Markdown -> .tex (pandoc) -> PDF (lualatex, two passes); return the PDF path."""
    relative = Path(target.name)
    workdir = _contained(book, build_root / relative.parent, must_exist=False)
    workdir.mkdir(parents=True, exist_ok=True)
    stem = relative.stem
    source = workdir / f"{stem}.md"
    source.write_text(markdown, encoding="utf-8")
    tex = workdir / f"{stem}.tex"
    header = _header(workdir)
    command = [*pandoc_command(), str(source), "-f",
               "markdown+tex_math_single_backslash-raw_tex", "-t", "latex", "-s",
               "-o", str(tex), "--lua-filter", str(THEME / "panels.lua"), "-H", str(header),
               "-V", "documentclass=scrartcl", "-V", "papersize=letter",
               "-V", "geometry:margin=0.9in", "-V", "fontsize=10pt", "-V", "colorlinks=true",
               "-M", f"title={title}", "-M", f"subtitle={subtitle}"]
    proc = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    if proc.returncode != 0:
        raise BuildError(f"build-pdf: pandoc failed for {target.name}: {proc.stderr.strip()}")
    pdf = workdir / f"{stem}.pdf"
    log = workdir / f"{stem}.log"
    pdf.unlink(missing_ok=True)
    for _ in range(2):
        proc = subprocess.run(
            ["lualatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
            cwd=workdir, capture_output=True, text=True, env=env, check=False)
        if proc.returncode != 0:
            tail = "\n".join(proc.stdout.splitlines()[-25:])
            raise BuildError(f"build-pdf: lualatex failed for {target.name} (log {log}):\n{tail}")
    if not pdf.exists():
        raise BuildError(f"build-pdf: missing PDF output for {target.name}")
    if pdf.stat().st_size == 0:
        raise BuildError(f"build-pdf: zero-byte PDF output for {target.name}")
    if log.is_file() and MISSING_CHARACTER in log.read_text(encoding="utf-8", errors="replace"):
        missing = [line for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
                   if MISSING_CHARACTER in line]
        raise BuildError(f"build-pdf: {target.name}: {missing[0]} (log {log})")
    return pdf


def build(repo_root: Path, book_id: str, *, jobs: int | None = None) -> list[Path]:
    repo_root = Path(repo_root).resolve()
    book = load_book_catalog(repo_root).by_id(book_id)
    if shutil.which("lualatex") is None:
        raise MissingTool("lualatex")
    pandoc_command()
    plan = targets(book)
    build_root = _contained(book, book.root / "build" / "pdf", must_exist=False)
    if build_root.exists():
        shutil.rmtree(build_root)
    build_root.mkdir(parents=True)
    cache = Path(os.environ.get("TMPDIR", "/tmp")) / "usaaio-book-cache" / book.id / "pdf"
    env = {**os.environ, "TEXMFCACHE": str(cache / "tex"), "XDG_CACHE_HOME": str(cache / "xdg")}
    Path(env["TEXMFCACHE"]).mkdir(parents=True, exist_ok=True)
    title = book.title or book.id

    def one(target: Target) -> Path:
        print(f"rendering: {target.name}", flush=True)
        subtitle = {"syllabus": "Course Structure", "handout": "Practice handout",
                    "paper": "Mock test paper", "solutions": "Mock test answers and solutions"}
        markdown = widen_tables(target_markdown(repo_root, book, target))
        return render(book, target, markdown, build_root,
                      title=title, subtitle=subtitle[target.kind], env=env)

    pdfs: list[Path] = []
    if plan:
        # The first render builds the font cache alone; the rest run in parallel.
        pdfs.append(one(plan[0]))
        workers = jobs or max(1, (os.cpu_count() or 2) - 1)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pdfs.extend(pool.map(one, plan[1:]))
    refresh_output(repo_root, book.id, "pdf", pdfs)
    return pdfs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.publish_pdf")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--book", required=True)
    parser.add_argument("--list-inputs", action="store_true")
    parser.add_argument("--jobs", type=int)
    arguments = parser.parse_args(argv)
    repo_root = arguments.root.resolve()
    try:
        book = load_book_catalog(repo_root).by_id(arguments.book)
        if arguments.list_inputs:
            for path in list_inputs(repo_root, book):
                print(path)
            return 0
        pdfs = build(repo_root, arguments.book, jobs=arguments.jobs)
    except MissingTool as missing:
        print(f"SKIP build-pdf: {str(missing).upper()} MISSING — install TeX Live lualatex "
              "and pandoc (Quarto 1.6.42 bundles pandoc)", file=sys.stderr)
        return 3
    except (BuildError, ValueError, KeyError, OSError) as error:
        print(f"build-pdf: {error}" if not str(error).startswith("build-pdf") else str(error),
              file=sys.stderr)
        return 1
    print(f"build-pdf: rendered {len(pdfs)} PDF(s) for {arguments.book}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
