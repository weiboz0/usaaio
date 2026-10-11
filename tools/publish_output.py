"""Copy built PDFs into the root `output/<book>/` folder (Plan 030 D4, D7; ported from py4kids).

Each build script owns its own files and replaces only those:
- `book` (scripts/build-book.sh): `<book>-*.pdf`, the typeset editions (`<book>-<edition>.pdf`
  or `<book>-<edition>-vol<N>.pdf`, named by `tools.books.output_pdf_name`);
- `pdf` (scripts/build-pdf.sh): `syllabus.pdf` and the `handouts/` and `mocktests/` folders.
Nothing clears the whole folder, so running both scripts in either order keeps every file,
and a renamed edition leaves no stale book PDF behind.
"""

from __future__ import annotations

import argparse
import fnmatch
import shutil
import sys
from pathlib import Path

from tools.books import output_pdf_name

PDF_FILES = ("syllabus.pdf",)
PDF_FOLDERS = ("handouts", "mocktests")
OWNERS = ("book", "pdf")


def book_pattern(book_id: str) -> str:
    """The glob of a book's typeset editions: `<book>-*.pdf` (every `output_pdf_name`)."""
    return output_pdf_name(book_id, "*")


def _destination(target: Path, owner: str, source: Path, book_id: str) -> Path:
    if owner == "book":
        pattern = book_pattern(book_id)
        if not fnmatch.fnmatchcase(source.name, pattern):
            raise ValueError(f"build-book owns only {pattern}, not {source.name}")
        return target / source.name
    if source.name in PDF_FILES:
        return target / source.name
    if source.parent.name in PDF_FOLDERS and source.suffix == ".pdf":
        return target / source.parent.name / source.name
    raise ValueError(
        f"build-pdf owns only {', '.join(PDF_FILES)} and "
        f"{', '.join(folder + '/' for folder in PDF_FOLDERS)}, not {source}"
    )


def refresh_output(root: Path, book_id: str, owner: str, sources: list[Path]) -> list[Path]:
    """Delete the owner's files in `output/<book>/`, then copy `sources` there; return the copies."""
    if owner not in OWNERS:
        raise ValueError(f"owner must be one of {', '.join(OWNERS)}")
    missing = [str(source) for source in sources if not source.is_file() or source.stat().st_size == 0]
    if missing:
        raise ValueError(f"missing or empty PDF: {', '.join(missing)}")
    target = root / "output" / book_id
    destinations = [_destination(target, owner, source, book_id) for source in sources]
    if len(set(destinations)) != len(destinations):
        raise ValueError("two sources map to the same output file")
    target.mkdir(parents=True, exist_ok=True)
    if owner == "book":
        for old in target.glob(book_pattern(book_id)):
            old.unlink()
    else:
        for name in PDF_FILES:
            (target / name).unlink(missing_ok=True)
        for folder in PDF_FOLDERS:
            shutil.rmtree(target / folder, ignore_errors=True)
    for source, destination in zip(sources, destinations, strict=True):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return destinations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.publish_output")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--book", required=True)
    parser.add_argument("--owner", required=True, choices=OWNERS)
    parser.add_argument("pdfs", nargs="*", type=Path)
    arguments = parser.parse_args(argv)
    try:
        copies = refresh_output(arguments.root, arguments.book, arguments.owner, arguments.pdfs)
    except ValueError as error:
        print(f"FAIL: output/{arguments.book}: {error}", file=sys.stderr)
        return 1
    for copy in copies:
        print(f"output: {copy.relative_to(arguments.root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
