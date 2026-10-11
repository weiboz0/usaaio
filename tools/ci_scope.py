"""Change routing for the edition builds in `scripts/ci-local.sh` (Plan 030 D6; py4kids ci_scope).

`route_books` is a pure function: given the registered books, the changed paths, and the old and
new text of the few files whose diff matters, it decides per book:

- `full`: render every edition (`build-book.sh --book <id>`) and run the full audit;
- `scoped`: render all four editions restricted to the changed units and mock tests
  (`build-book.sh --book <id> --units ... --mocktests ...`) and run the scoped audit;
- `glossary`: no render, only the glossary audit (D5 rule 5);
- `none`: unchanged; ci-local prints `INFO build-book: <book> unchanged (change-routed)`.

Global publication inputs (the publisher, its theme, `tools/books.py`, `build-book.sh`, the
registry, and the Python environment) route every book to `full`. So does `--all-books`, and so
does a missing `origin/main` or merge-base (fail-safe).

The CLI gathers the change set: the committed diff against the merge-base with `origin/main`,
plus staged, unstaged, and untracked files.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

GLOBAL_EXACT = frozenset({
    "tools/books.py", "scripts/build-book.sh", "books.yaml", "pyproject.toml", "uv.lock",
})
GLOBAL_PREFIXES = ("tools/publish_theme/",)
INFO_UNCHANGED = "INFO build-book: {book} unchanged (change-routed)"


def is_global_input(path: str) -> bool:
    if path in GLOBAL_EXACT or path.startswith(GLOBAL_PREFIXES):
        return True
    name = path.removeprefix("tools/")
    return path.startswith("tools/") and "/" not in name and name.startswith("publish") \
        and name.endswith(".py")


@dataclass
class Route:
    mode: str = "none"  # none | glossary | scoped | full
    units: list[str] = field(default_factory=list)
    mocktests: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    def escalate(self, mode: str, reason: str) -> None:
        order = ("none", "glossary", "scoped", "full")
        if order.index(mode) > order.index(self.mode):
            self.mode = mode
        self.reasons.append(reason)

    def add_unit(self, unit: str, reason: str) -> None:
        if unit not in self.units:
            self.units.append(unit)
        self.escalate("scoped", reason)

    def add_mocktest(self, test: str, reason: str) -> None:
        if test not in self.mocktests:
            self.mocktests.append(test)
        self.escalate("scoped", reason)

    def command(self, book: str) -> str:
        """The line ci-local acts on: `<mode> <book> [--units ...] [--mocktests ...]`."""
        if self.mode == "scoped":
            parts = [self.mode, book]
            if self.units:
                parts += ["--units", *sorted(self.units)]
            if self.mocktests:
                parts += ["--mocktests", *sorted(self.mocktests)]
            return " ".join(parts)
        return f"{self.mode} {book}"


def _load(text: str | None) -> Any:
    if text is None:
        return None
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError:
        return None


def added_chapter_units(old_text: str | None, new_text: str | None) -> list[str] | None:
    """The units a `publication.yaml` change only adds as `chapters:` entries, else None.

    The change qualifies when every other key is unchanged and the old chapter entries appear,
    unchanged and in order, within the new list.
    """
    old, new = _load(old_text), _load(new_text)
    if not isinstance(old, dict) or not isinstance(new, dict):
        return None
    if {k: v for k, v in old.items() if k != "chapters"} != {
            k: v for k, v in new.items() if k != "chapters"}:
        return None
    old_chapters, new_chapters = old.get("chapters"), new.get("chapters")
    if not isinstance(old_chapters, list) or not isinstance(new_chapters, list):
        return None
    remaining = iter(new_chapters)
    if not all(any(entry == candidate for candidate in remaining) for entry in old_chapters):
        return None
    added = [entry for entry in new_chapters if entry not in old_chapters]
    units = [entry.get("unit") for entry in added if isinstance(entry, dict)]
    if not added or not all(isinstance(unit, str) for unit in units):
        return None
    return units


def coverage_introductions(text: str | None) -> dict[str, set[str]] | None:
    """`destination unit -> shipped concepts` from a coverage map; None if unreadable.

    A row whose shipped concepts cannot be attributed to a destination unit maps to the key ''.
    """
    raw = _load(text)
    if text is None:
        return {}
    if not isinstance(raw, dict) or not isinstance(raw.get("knowledge_points"), list):
        return None
    result: dict[str, set[str]] = {}
    for row in raw["knowledge_points"]:
        if not isinstance(row, dict):
            return None
        concepts = row.get("shipped_concepts") or []
        if not isinstance(concepts, list):
            return None
        if not concepts:
            continue
        destination = row.get("destination")
        key = destination if isinstance(destination, str) and destination else ""
        result.setdefault(key, set()).update(str(concept) for concept in concepts)
    return result


def coverage_changed_units(old_text: str | None, new_text: str | None,
                           live_units: Iterable[str]) -> list[str] | None:
    """Units whose introduced concepts changed; None when a change cannot be attributed."""
    old, new = coverage_introductions(old_text), coverage_introductions(new_text)
    if old is None or new is None:
        return None
    live = set(live_units)
    changed: list[str] = []
    for unit in sorted(set(old) | set(new)):
        if old.get(unit, set()) == new.get(unit, set()):
            continue
        if unit == "" or unit not in live:
            return None
        changed.append(unit)
    return changed


@dataclass(frozen=True)
class BookInfo:
    id: str
    root: str  # repo-relative, e.g. "book1"
    units: tuple[str, ...]  # live units
    configured_units: tuple[str, ...]  # publication.yaml chapters


def route_books(books: Iterable[BookInfo], changed: Iterable[str], *, all_books: bool = False,
                diff_available: bool = True,
                old_text: Callable[[str], str | None] = lambda _: None,
                new_text: Callable[[str], str | None] = lambda _: None) -> dict[str, Route]:
    """The pure routing decision for every book (see the module docstring)."""
    books = list(books)
    paths = sorted({path.strip().removeprefix("./") for path in changed if path.strip()})
    routes = {book.id: Route() for book in books}
    if all_books or not diff_available:
        reason = "--all-books" if all_books else "origin/main or merge-base unavailable"
        for route in routes.values():
            route.escalate("full", reason)
        return routes
    for path in paths:
        if is_global_input(path):
            for route in routes.values():
                route.escalate("full", f"global publication input {path}")
    for book in books:
        route = routes[book.id]
        prefix = book.root.rstrip("/") + "/"
        for path in paths:
            if not path.startswith(prefix):
                continue
            inner = path[len(prefix):]
            parts = inner.split("/")
            if inner == "publication.yaml":
                units = added_chapter_units(old_text(path), new_text(path))
                if units is None:
                    route.escalate("full", f"{path} changed")
                else:
                    for unit in units:
                        route.add_unit(unit, f"{path} adds chapter {unit}")
            elif parts[0] in ("front-matter", "back-matter"):
                route.escalate("full", f"{path} changed")
            elif parts[0] == "units" and len(parts) > 2:
                unit = parts[1]
                if unit in book.configured_units:
                    route.add_unit(unit, f"{path} changed")
                else:
                    route.escalate("full", f"{path}: unit {unit} is not a configured chapter")
            elif parts[0] == "mocktests" and len(parts) > 2:
                route.add_mocktest(parts[1], f"{path} changed")
            elif inner == "curriculum/coverage-map.yaml":
                units = coverage_changed_units(old_text(path), new_text(path), book.units)
                if units is None:
                    route.escalate("full", f"{path}: changed rows cannot be attributed to units")
                elif not units:
                    route.escalate("glossary", f"{path} changes no unit's introduced concepts")
                else:
                    for unit in units:
                        if unit in book.configured_units:
                            route.add_unit(unit, f"{path} changes {unit}'s introduced concepts")
                        else:
                            route.escalate("full", f"{path}: {unit} is not a configured chapter")
                    route.escalate("glossary", f"{path}: glossary audit")
    for route in routes.values():
        if route.mode == "full":
            route.units, route.mocktests = [], []
    return routes


# --- the impure change-set collection ---------------------------------------------------------


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          check=False)


def change_set(root: Path) -> tuple[list[str], str | None]:
    """(changed paths, merge-base) — committed vs. merge-base with origin/main, plus staged,
    unstaged, and untracked files. The merge-base is None when it is unavailable."""
    base_proc = _git(root, "merge-base", "origin/main", "HEAD")
    base = base_proc.stdout.strip() if base_proc.returncode == 0 else None
    paths: set[str] = set()
    commands = [("diff", "--name-only", "--cached"), ("diff", "--name-only"),
                ("ls-files", "--others", "--exclude-standard")]
    if base:
        commands.insert(0, ("diff", "--name-only", base, "HEAD"))
    for command in commands:
        proc = _git(root, *command)
        if proc.returncode == 0:
            paths.update(line for line in proc.stdout.splitlines() if line.strip())
    return sorted(paths), base


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.ci_scope")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--all-books", action="store_true")
    arguments = parser.parse_args(argv)
    root = arguments.root.resolve()
    from tools.books import live_units, load_book_catalog, load_publication_config

    catalog = load_book_catalog(root)
    infos = []
    for book in catalog.books:
        if not book.publication:
            continue
        try:
            configured = load_publication_config(book).units
        except ValueError:
            configured = ()
        infos.append(BookInfo(book.id, book.root.relative_to(root).as_posix(),
                              live_units(book), configured))
    changed, base = change_set(root)

    def old_text(path: str) -> str | None:
        if not base:
            return None
        proc = _git(root, "show", f"{base}:{path}")
        return proc.stdout if proc.returncode == 0 else None

    def new_text(path: str) -> str | None:
        target = root / path
        return target.read_text(encoding="utf-8") if target.is_file() else None

    routes = route_books(infos, changed, all_books=arguments.all_books,
                         diff_available=base is not None, old_text=old_text, new_text=new_text)
    for book in infos:
        route = routes[book.id]
        print(route.command(book.id))
        for reason in route.reasons[:5]:
            print(f"#   {book.id}: {reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
