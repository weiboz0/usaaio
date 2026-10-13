"""Plan 032 D1/D3/D4: explain library calls where students first meet them.

The check walks a book's notebooks in teaching order (D1) and finds every call of a
non-baseline callee. Four rules apply to non-harness code:

1. **Book-first**: the first use of a callee in the book carries a comment naming it.
2. **New signature**: a later use that adds a semantic keyword (or a new positional count
   on a positional callee) carries a comment naming the new keyword (or the callee).
3. **Unit-first reminder**: the first use in each later unit names the callee in a comment,
   or the unit's API card lists it under "Also used here" (graduated and no-reminder callees
   are exempt).
4. **Harness code** (`# Checks:` cells, and named-idiom calls inside `# Boilerplate:` blocks) is
   outside the ladder. In a mock statement, `# Checks:` marks only paper-provided cells, which
   also appear byte-identically as code cells of the matching solution.

Book 2 is scanned after its dependencies (Book 1), so a callee Book 1 explains is not new in
Book 2. Cell indices in messages and waivers are 0-based (`nb.cells[i]`).

Report mode: while `enforce: false` in `api_comments_baseline.yaml`, findings print as
warnings and the check passes. Run `python -m tools.checks.api_comments --root <book root>`
for a per-unit summary or a filtered finding list.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import csv
import io
import json
import re
import sys
import tokenize
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from tools.books import load_book_catalog, mocktests_root, unit_id_of
from tools.books import units_root as books_units_root
from tools.checks.tolerance import (
    _canonical_module,
    _dotted_name,
    _import_aliases,
    _resolved_name,
)
from tools.model import Report

NAME = "api-comments-check"
CONFIG_PATH = Path(__file__).with_name("api_comments_baseline.yaml")
WAIVERS_PATH = Path(__file__).with_name("api_comments_waivers.yaml")
GUARD_PROTECTED = "guard-protected"
CARD_MARKER = "<!-- api-card -->"
CHECKS_MARKER = "# Checks:"
BOILERPLATE_MARKER = "# Boilerplate:"
STATEMENT_KINDS = frozenset({"statement", "mock-statement"})
LESSON_KINDS = frozenset({"lesson", "review"})
MOCK_KINDS = frozenset({"mock-statement", "mock-solution"})
BUILTIN_NAMES = frozenset(dir(builtins))
_WORD = r"(?<![A-Za-z0-9_]){}(?![A-Za-z0-9_])"
_IDENT = re.compile(r"[A-Za-z_]\w*")
_PLAIN_SPAN = re.compile(r"(?P<name>[A-Za-z_]\w*)(?:\(.*\))?")
_DEF_SPAN = re.compile(r"\bdef\s+(?P<name>[A-Za-z_]\w*)\s*\(")
_CLASS_SPAN = re.compile(r"\bclass\s+(?P<name>[A-Za-z_]\w*)")
_VERB = re.compile(r"\b(?:Implement|Define|Write)\b")
_NUMBER = re.compile(r"(\d+)")
# D8: lesson and review notebooks often end in an open answer region (tools/publish.py
# answer_regions); the card closes it with its own level-2 heading, never a numbered `## N.`.
_CARD_HEADING = re.compile(r"## (?!\d+\.)\S")


# --------------------------------------------------------------------------- configuration


@dataclass(frozen=True)
class Config:
    enforce: bool
    waiver_cap_percent: float
    mock_rules: frozenset[int]
    module_aliases: dict[str, str]
    baseline_builtins: frozenset[str]
    baseline_methods: frozenset[str]
    semantic_keywords: frozenset[str]
    positional_callees: frozenset[str]
    positional_words: frozenset[str]
    graduation_units: int
    graduated: frozenset[str]
    no_reminder: frozenset[str]
    family_roots: dict[str, str]
    family_keyed: frozenset[str]
    idiom_callees: frozenset[str] = frozenset()


def load_config(raw: dict[str, Any] | None = None) -> Config:
    if raw is None:
        raw = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    baseline = raw.get("baseline") or {}
    families = raw.get("method_families") or {}
    return Config(
        enforce=bool(raw.get("enforce", False)),
        waiver_cap_percent=float(raw.get("waiver_cap_percent", 2)),
        mock_rules=frozenset(int(rule) for rule in raw.get("mock_rules", [1])),
        module_aliases={str(k): str(v) for k, v in (raw.get("module_aliases") or {}).items()},
        baseline_builtins=frozenset(baseline.get("builtins") or ()),
        baseline_methods=frozenset(baseline.get("methods") or ()),
        semantic_keywords=frozenset(raw.get("semantic_keywords") or ()),
        positional_callees=frozenset(raw.get("positional_callees") or ()),
        positional_words=frozenset(raw.get("positional_words") or ()),
        graduation_units=int(raw.get("graduation_units", 3)),
        graduated=frozenset(raw.get("graduated") or ()),
        no_reminder=frozenset(raw.get("no_reminder") or ()),
        family_roots={str(k): str(v) for k, v in (families.get("roots") or {}).items()},
        family_keyed=frozenset(families.get("keyed") or ()),
        idiom_callees=frozenset(
            str(callee)
            for idiom in (raw.get("named_idioms") or {}).values()
            for callee in ((idiom or {}).get("callees") or ())
        ),
    )


@dataclass(frozen=True)
class Waiver:
    path: str
    cell: int | None  # None = every cell
    callee: str | None  # None = every callee
    reason: str

    def matches(self, rel: str, cell: int, callee: str) -> bool:
        return (
            self.path == rel
            and (self.cell is None or self.cell == cell)
            and (self.callee is None or self.callee == callee)
        )


def load_waivers(raw: dict[str, Any] | None = None) -> list[Waiver]:
    if raw is None:
        raw = yaml.safe_load(WAIVERS_PATH.read_text(encoding="utf-8")) or {}
    waivers: list[Waiver] = []
    for entry in raw.get("waivers") or []:
        cell = entry.get("cell", "*")
        callee = entry.get("callee", "*")
        reason = str(entry.get("reason", "")).strip()
        if not reason:
            raise ValueError(f"api-comments waiver for {entry.get('path')} has no reason")
        waivers.append(
            Waiver(
                path=str(entry["path"]),
                cell=None if cell == "*" else int(cell),
                callee=None if callee == "*" else str(callee),
                reason=reason,
            )
        )
    return waivers


# --------------------------------------------------------------------------- notebook order


@dataclass(frozen=True)
class NotebookRef:
    path: Path
    rel: str
    book: str
    unit: str
    kind: str  # lesson | review | statement | solution | mock-statement | mock-solution
    selected: bool


def _natural(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part for part in _NUMBER.split(path.name)]


def _is_solution(path: Path) -> bool:
    return path.stem.endswith("_solution")


def book_sequence(book_root: Path, book_id: str, repo_root: Path, selected: bool) -> list[NotebookRef]:
    """Notebooks of one book in D1 teaching order: units (folder order), then mock tests."""

    def ref(path: Path, unit: str, kind: str) -> NotebookRef:
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            rel = path.as_posix()
        return NotebookRef(path, rel, book_id, unit, kind, selected)

    refs: list[NotebookRef] = []
    units_root = books_units_root(book_root)
    unit_dirs = sorted(
        p for p in units_root.iterdir() if p.is_dir() and not p.name.startswith(".")
    ) if units_root.is_dir() else []
    for unit_dir in unit_dirs:
        unit = unit_id_of(unit_dir.name)
        ordered: list[tuple[Path, str]] = []
        if (unit_dir / "lesson.ipynb").is_file():
            ordered.append((unit_dir / "lesson.ipynb", "lesson"))
        ordered += [(p, "lesson") for p in sorted((unit_dir / "lessons").glob("*.ipynb"))]
        if (unit_dir / "review.ipynb").is_file():
            ordered.append((unit_dir / "review.ipynb", "review"))
        practice = sorted((unit_dir / "practice").glob("*.ipynb"), key=_natural)
        ordered += [(p, "statement") for p in practice if not _is_solution(p)]
        ordered += [(p, "solution") for p in practice if _is_solution(p)]
        known = {p for p, _ in ordered}
        leftovers = sorted(
            p
            for p in unit_dir.rglob("*.ipynb")
            if p not in known and ".ipynb_checkpoints" not in p.parts and "build" not in p.parts
        )
        ordered += [(p, "solution") for p in leftovers]
        refs += [ref(p, unit, kind) for p, kind in ordered]
    mocks_root = mocktests_root(book_root)
    mock_dirs = sorted(p for p in mocks_root.iterdir() if p.is_dir()) if mocks_root.is_dir() else []
    for mock_dir in mock_dirs:
        problems = sorted((mock_dir / "problems").glob("*.ipynb"), key=_natural)
        solutions = sorted((mock_dir / "solutions").glob("*.ipynb"), key=_natural)
        refs += [ref(p, mock_dir.name, "mock-statement") for p in problems]
        refs += [ref(p, mock_dir.name, "mock-solution") for p in solutions]
    return refs


def _scan_plan(root: Path) -> tuple[Path, list[tuple[str, Path]], str]:
    """(repo root, [(book id, book root)] dependencies first, selected book id)."""
    for parent in root.parents:
        if not (parent / "books.yaml").is_file():
            continue
        catalog = load_book_catalog(parent)
        matches = [book for book in catalog.books if Path(book.root).resolve() == root]
        if len(matches) != 1:
            break
        selected = matches[0]
        needed: set[str] = set()
        pending = list(selected.depends_on)
        while pending:
            book_id = pending.pop()
            if book_id not in needed:
                needed.add(book_id)
                pending += list(catalog.by_id(book_id).depends_on)
        books = [
            (book.id, Path(book.root).resolve())
            for book in catalog.books
            if book.id in needed
        ]
        return parent, [*books, (selected.id, root)], selected.id
    return root.parent, [(root.name, root)], root.name


# --------------------------------------------------------------------------- source helpers


def _source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def _has_magic(source: str) -> bool:
    return any(line.lstrip().startswith(("%", "!")) for line in source.splitlines())


@dataclass
class CellComments:
    by_line: dict[int, list[str]] = field(default_factory=dict)
    comment_only: set[int] = field(default_factory=set)


def cell_comments(source: str) -> CellComments:
    """COMMENT tokens from the original source; a `#` inside a string is not a comment."""
    result = CellComments()
    lines = source.splitlines()
    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type != tokenize.COMMENT:
                continue
            line_no, col = token.start
            result.by_line.setdefault(line_no, []).append(token.string)
            text = lines[line_no - 1] if line_no - 1 < len(lines) else ""
            if col == len(text) - len(text.lstrip()):
                result.comment_only.add(line_no)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return result


def comment_tokens(source: str) -> list[str]:
    """Every COMMENT token string, in order (shared with scripts/verify-comment-only.py)."""
    comments = cell_comments(source)
    return [text for line in sorted(comments.by_line) for text in comments.by_line[line]]


def names_word(text: str, word: str) -> bool:
    return bool(word) and re.search(_WORD.format(re.escape(word)), text) is not None


def markdown_code_spans(text: str) -> list[str]:
    """Inline code spans and fenced blocks, skipping anything inside LaTeX math."""
    spans: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "\\" and index + 1 < length and text[index + 1] in "([":
            closer = "\\)" if text[index + 1] == "(" else "\\]"
            end = text.find(closer, index + 2)
            index = length if end < 0 else end + 2
            continue
        if char == "\\":
            index += 2
            continue
        if char == "$":
            delimiter = "$$" if text.startswith("$$", index) else "$"
            end = text.find(delimiter, index + len(delimiter))
            index = length if end < 0 else end + len(delimiter)
            continue
        if char == "`":
            run_end = index
            while run_end < length and text[run_end] == "`":
                run_end += 1
            fence = text[index:run_end]
            end = text.find(fence, run_end)
            if end < 0:
                index = run_end
                continue
            spans.append(text[run_end:end])
            index = end + len(fence)
            continue
        index += 1
    return spans


def required_identifiers(notebook: dict[str, Any]) -> set[str]:
    """Identifiers a statement asks the student to define (D4; shared with the verifier)."""
    required: set[str] = set()
    for cell in notebook.get("cells", []):
        source = _source(cell)
        if cell.get("cell_type") == "markdown":
            for span in markdown_code_spans(source):
                required |= {m["name"] for m in _DEF_SPAN.finditer(span)}
                required |= {m["name"] for m in _CLASS_SPAN.finditer(span)}
            for match in _VERB.finditer(source):
                rest = source[match.end():]
                sentence = re.split(r"\.(?:\s|$)|\n\n", rest, maxsplit=1)[0]
                for span in markdown_code_spans(sentence):
                    plain = _PLAIN_SPAN.fullmatch(span.strip())
                    if plain:
                        required.add(plain["name"])
        elif cell.get("cell_type") == "code":
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ) and _is_stub(node.body):
                    required.add(node.name)
    return {name for name in required if not name.startswith("__")}


def _is_stub(body: list[ast.stmt]) -> bool:
    statements = list(body)
    if (
        statements
        and isinstance(statements[0], ast.Expr)
        and isinstance(statements[0].value, ast.Constant)
        and isinstance(statements[0].value.value, str)
    ):
        statements = statements[1:]
    if len(statements) != 1:
        return False
    only = statements[0]
    if isinstance(only, ast.Pass):
        return True
    if isinstance(only, ast.Expr) and isinstance(only.value, ast.Constant):
        return only.value.value is Ellipsis
    if isinstance(only, ast.Raise) and only.exc is not None:
        target = only.exc.func if isinstance(only.exc, ast.Call) else only.exc
        return isinstance(target, ast.Name) and target.id == "NotImplementedError"
    return False


# --------------------------------------------------------------------------- API cards


@dataclass
class Card:
    rel: str
    cell: int
    is_last: bool
    heading_ok: bool
    new: list[str]
    also: list[str]


def _card_name(line: str) -> str | None:
    spans = markdown_code_spans(line)
    if not spans:
        return None
    name = spans[0].strip()
    if "(" in name:
        name = name[: name.index("(")]
    return name.strip() or None


def parse_card(notebook: dict[str, Any], rel: str) -> Card | None:
    cells = notebook.get("cells", [])
    found = [
        index
        for index, cell in enumerate(cells)
        if cell.get("cell_type") == "markdown" and _source(cell).lstrip().startswith(CARD_MARKER)
    ]
    if not found:
        return None
    index = found[-1]
    new: list[str] = []
    also: list[str] = []
    part: list[str] | None = None
    body = _source(cells[index]).lstrip()[len(CARD_MARKER):]
    first_line = next((line for line in body.splitlines() if line.strip()), "")
    for line in _source(cells[index]).splitlines():
        lowered = line.lower()
        if "new in this unit" in lowered:
            part = new
            continue
        if "also used here" in lowered:
            part = also
            continue
        if part is not None and line.lstrip().startswith(("- ", "* ")):
            name = _card_name(line)
            if name:
                part.append(name)
    return Card(
        rel=rel,
        cell=index,
        is_last=index == len(cells) - 1,
        heading_ok=bool(_CARD_HEADING.match(first_line)),
        new=new,
        also=also,
    )


# --------------------------------------------------------------------------- analysis


@dataclass
class Site:
    rule: int
    rel: str
    book: str
    unit: str
    kind: str
    cell: int
    line: int
    callee: str
    written: str
    element: str | None
    explained: bool
    evidence: str
    exempt: str | None = None  # graduated | no-reminder | waived | guard-protected
    selected: bool = True
    code: str = ""

    @property
    def subject(self) -> bool:
        return self.exempt not in {"graduated", "no-reminder"}

    @property
    def failing(self) -> bool:
        return self.subject and not self.explained and self.exempt is None

    def describe(self) -> str:
        what = f"{self.callee}" + (f" ({self.written})" if self.written not in {"", self.callee} else "")
        if self.rule == 1:
            need = "book-first use has no comment naming it"
        elif self.rule == 2:
            need = f"new {self.element} has no comment naming it"
        else:
            need = "unit-first use has no reminder (inline or card 'Also used here')"
        return f"{self.rel}:cell {self.cell}:line {self.line}: rule {self.rule} [{self.unit}] {what}: {need}"


@dataclass
class Analysis:
    sites: list[Site] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    selected_book: str = ""
    repo_root: Path = Path(".")
    units: list[str] = field(default_factory=list)  # selected book's units, in order
    book_first: dict[str, list[str]] = field(default_factory=dict)  # unit -> callees
    rule3: dict[str, set[str]] = field(default_factory=dict)  # unit -> callees
    harness_only: set[str] = field(default_factory=set)
    forms: dict[str, set[str]] = field(default_factory=dict)
    waived: int = 0
    guard_waived: int = 0
    use_count: Counter[str] = field(default_factory=Counter)

    def subject_sites(self) -> list[Site]:
        return [site for site in self.sites if site.selected and site.subject]


def _parents(tree: ast.AST) -> dict[int, ast.AST]:
    parents: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[id(child)] = node
    return parents


def _enclosing_statement(node: ast.AST, parents: dict[int, ast.AST]) -> ast.stmt | None:
    current: ast.AST | None = node
    while current is not None and not isinstance(current, ast.stmt):
        current = parents.get(id(current))
    return current if isinstance(current, ast.stmt) else None


_LITERALS = (
    ast.List, ast.ListComp, ast.Dict, ast.DictComp, ast.Set, ast.SetComp, ast.Tuple,
    ast.Constant, ast.JoinedStr,
)

_COMPOUND = (
    ast.For, ast.AsyncFor, ast.While, ast.If, ast.With, ast.AsyncWith, ast.Try,
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Match,
)


@dataclass
class _Ctx:
    """One code cell being scanned."""

    ref: NotebookRef
    cell: int
    source: str
    lines: list[str]
    comments: CellComments
    harness_lines: set[int]  # whole `# Checks:` cell
    boilerplate_lines: set[int]  # `# Boilerplate:` blocks (only idiom callees are harness)
    markdown: str
    parents: dict[int, ast.AST]

    def attached(self, call: ast.Call, *, single_above: bool) -> list[str]:
        """Comments on the call's lines, plus the comment block directly above its statement."""
        stmt = _enclosing_statement(call, self.parents)
        line_numbers = set(range(call.lineno, (call.end_lineno or call.lineno) + 1))
        if stmt is not None and not isinstance(stmt, _COMPOUND):
            line_numbers |= set(range(stmt.lineno, (stmt.end_lineno or stmt.lineno) + 1))
        texts = [text for line in sorted(line_numbers) for text in self.comments.by_line.get(line, [])]
        start = stmt.lineno if stmt is not None else call.lineno
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and stmt.decorator_list:
            start = min(start, *(d.lineno for d in stmt.decorator_list))
        above = start - 1
        while above in self.comments.comment_only:
            texts += self.comments.by_line.get(above, [])
            above -= 1
            if single_above:
                break
        return texts


def _checks_lines(source: str) -> set[int]:
    """Every line of a `# Checks:` cell (the marker is the cell's first line)."""
    lines = source.splitlines()
    if lines and lines[0].startswith(CHECKS_MARKER):
        return set(range(1, len(lines) + 1))
    return set()


def _harness_lines(source: str, comments: CellComments) -> set[int]:
    """Lines of `# Boilerplate:` blocks (from the marker line to the next blank line)."""
    harness: set[int] = set()
    lines = source.splitlines()
    for line_no, texts in comments.by_line.items():
        if line_no in comments.comment_only and any(t.startswith(BOILERPLATE_MARKER) for t in texts):
            end = line_no
            while end < len(lines) and lines[end].strip():
                end += 1
            harness |= set(range(line_no, end + 1))
    return harness


def _local_modules(book_roots: list[Path]) -> set[str]:
    local = {"tools", "scripts"}
    for root in book_roots:
        local |= {path.stem for path in root.rglob("*.py")}
    return local


class _Scanner:
    def __init__(self, config: Config, waivers: list[Waiver], repo_root: Path, local: set[str]):
        self.config = config
        self.waivers = waivers
        self.repo_root = repo_root
        self.local = local
        self.first: dict[str, tuple[str, str]] = {}  # callee -> (book, unit)
        self.unit_seen: set[tuple[str, str]] = set()
        self.units_used: dict[str, list[str]] = defaultdict(list)
        self.elements: dict[str, set[str]] = defaultdict(set)
        self.harness: set[str] = set()
        self.nonharness: set[str] = set()
        self.analysis = Analysis(repo_root=repo_root)
        self.cards: dict[tuple[str, str], Card | None] = {}
        self.guard_paths = {w.path for w in waivers if w.reason == GUARD_PROTECTED}

    # ------------------------------------------------------------------ callee resolution

    def _family(self, node: ast.AST, aliases: dict[str, str], vartypes: dict[str, str]) -> str | None:
        while isinstance(node, (ast.Attribute, ast.Subscript, ast.Call)):
            node = node.func if isinstance(node, ast.Call) else node.value
        if isinstance(node, ast.Name):
            if node.id in vartypes:
                return vartypes[node.id]
            if node.id in aliases:
                top = aliases[node.id].split(".", 1)[0]
                return "local" if top in self.local else top
            return None
        if isinstance(node, (ast.Constant, ast.JoinedStr)):
            return "str"
        if isinstance(node, (ast.List, ast.ListComp)):
            return "list"
        if isinstance(node, (ast.Dict, ast.DictComp)):
            return "dict"
        return None

    def _value_family(self, value: ast.AST, aliases: dict[str, str]) -> str | None:
        """Library root of a value built directly by a module function (`np.zeros(...)`).

        Only lower-case module functions type a variable: `nn.Linear(...)` builds a module and
        `model.state_dict()` a dict, so neither is typed by its library root.
        """
        if not isinstance(value, ast.Call):
            return None
        written = _dotted_name(value.func)
        if written is None:
            return None
        root, _, rest = written.partition(".")
        if root not in aliases:
            return None
        top = aliases[root].split(".", 1)[0]
        if top in self.local or top == "importlib":
            return "local"
        last = (rest or aliases[root]).rsplit(".", 1)[-1]
        return top if last[:1].islower() else None

    def resolve(
        self,
        call: ast.Call,
        aliases: dict[str, str],
        vartypes: dict[str, str],
        defs: set[str],
    ) -> tuple[str, str] | None:
        """(callee key, written form) or None when the call is baseline, local or a variable."""
        func = call.func
        config = self.config
        if isinstance(func, ast.Name):
            name = func.id
            if name in defs:
                return None
            if name in aliases:
                target = aliases[name]
                if target.split(".", 1)[0] in self.local:
                    return None
                return _canonical_module(target, config.module_aliases, passthrough=True) or target, name
            if name in BUILTIN_NAMES and name not in config.baseline_builtins:
                return name, name
            return None
        if not isinstance(func, ast.Attribute):
            return None
        written = _dotted_name(func)
        if written is not None:
            root = written.split(".", 1)[0]
            if root in aliases and root not in vartypes:
                if aliases[root].split(".", 1)[0] in self.local:
                    return None
                resolved = _resolved_name(func, aliases, config.module_aliases) or written
                key = _canonical_module(resolved, config.module_aliases, passthrough=True)
                return key or resolved, written
        method = func.attr
        if method.startswith("__") or method in defs:
            return None
        family_root = self._family(func.value, aliases, vartypes)
        if family_root in {"local", "importlib"}:
            return None
        family = config.family_roots.get(family_root or "")
        if family and (method in config.family_keyed or method in config.baseline_methods):
            return f"{family}.{method}", f".{method}"
        if method in config.baseline_methods:
            return None
        return f".{method}", f".{method}"

    # ------------------------------------------------------------------ notebook scan

    def card_for(self, ref: NotebookRef) -> Card | None:
        key = (ref.book, ref.unit)
        if key not in self.cards:
            self.cards[key] = _read_card(_unit_folder(ref.path) / "lesson.ipynb", self.repo_root)
        return self.cards[key]

    def card_lists(self, ref: NotebookRef, callee: str, part: str) -> bool:
        if ref.kind in MOCK_KINDS:
            return False
        card = self.card_for(ref)
        if card is None:
            return False
        names = card.new if part == "new" else card.also
        forms = self.analysis.forms.get(callee, {callee})
        return any(name in forms for name in names)

    def scan(self, ref: NotebookRef) -> None:
        analysis = self.analysis
        try:
            notebook = json.loads(ref.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            if ref.selected:
                analysis.errors.append(f"{ref.rel}: cannot read notebook: {exc}")
            return
        cells = notebook.get("cells", [])
        parsed: dict[int, tuple[str, ast.Module]] = {}
        for index, cell in enumerate(cells):
            if cell.get("cell_type") != "code":
                continue
            source = _source(cell)
            try:
                parsed[index] = (source, ast.parse(source))
            except SyntaxError as exc:
                if ref.selected:
                    if _has_magic(source):
                        analysis.errors.append(
                            f"{ref.rel}:cell {index}: IPython magic or shell line is not allowed"
                        )
                    else:
                        analysis.errors.append(
                            f"{ref.rel}:cell {index}:line {exc.lineno}: cannot parse code: {exc.msg}"
                        )
        defs: set[str] = set()
        for _source_text, tree in parsed.values():
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    defs.add(node.name)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if (
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            defs.add(target.attr)
                        if isinstance(target, ast.Name) and isinstance(node.value, ast.Lambda):
                            defs.add(target.id)
                elif isinstance(node, ast.ImportFrom) and (
                    node.level or (node.module or "").split(".", 1)[0] in self.local
                ):
                    defs |= {alias.asname or alias.name for alias in node.names}
        required = required_identifiers(notebook) if ref.kind in STATEMENT_KINDS else set()
        aliases: dict[str, str] = {}
        vartypes: dict[str, str] = {}

        def markdown(index: int) -> str:
            if 0 <= index < len(cells) and cells[index].get("cell_type") == "markdown":
                text = _source(cells[index])
                # The unit card is evidence (d) for rule 3 only, never markdown evidence (c).
                return "" if text.lstrip().startswith(CARD_MARKER) else text
            return ""

        for index in sorted(parsed):
            source, tree = parsed[index]
            comments = cell_comments(source)
            self._check_markers(ref, index, source, comments)
            aliases.update(
                _import_aliases(tree, self.config.module_aliases, passthrough=True)
            )
            ctx = _Ctx(
                ref=ref,
                cell=index,
                source=source,
                lines=source.splitlines(),
                comments=comments,
                harness_lines=_checks_lines(source),
                boilerplate_lines=_harness_lines(source, comments),
                markdown="\n".join(markdown(j) for j in (index - 1, index + 1, index - 2)),
                parents=_parents(tree),
            )
            # Execution order: a call sees only the bindings made before it. An assignment
            # binds after its value is evaluated, so it is ordered at its end position
            # (`names = torch.tensor(names)` does not type the `names` of earlier calls).
            events: list[tuple[tuple[int, int], int, ast.AST]] = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    events.append(((node.lineno, node.col_offset), 0, node))
                elif isinstance(node, ast.Assign):
                    end = (node.end_lineno or node.lineno, node.end_col_offset or 0)
                    events.append((end, 1, node))
            events.sort(key=lambda event: (event[0], event[1]))
            for _position, kind, node in events:
                if kind == 1:
                    self._bind(node, aliases, vartypes)
                    continue
                resolved = self.resolve(node, aliases, vartypes, defs)
                if resolved is None:
                    continue
                self._use(ctx, node, resolved[0], resolved[1], required)

    def _bind(self, node: ast.Assign, aliases: dict[str, str], vartypes: dict[str, str]) -> None:
        """Type (or untype) the assigned names; the latest binding wins."""
        family = self._value_family(node.value, aliases)
        if family is None and not isinstance(node.value, _LITERALS):
            return  # unknown value: keep what is known (`x = x.reshape(...)`)
        for target in node.targets:
            names = target.elts if isinstance(target, ast.Tuple) else [target]
            for name in names:
                if not isinstance(name, ast.Name):
                    continue
                if family is None:
                    vartypes.pop(name.id, None)
                else:
                    vartypes[name.id] = family

    def _check_markers(self, ref: NotebookRef, index: int, source: str, comments: CellComments) -> None:
        if not ref.selected:
            return
        first_line = source.splitlines()[0] if source else ""
        if first_line.startswith(CHECKS_MARKER) and ref.kind in LESSON_KINDS:
            self.analysis.errors.append(
                f"{ref.rel}:cell {index}: '# Checks:' marker is not allowed in lesson or "
                "review notebooks (D1 rule 4)"
            )
        if (
            first_line.startswith(CHECKS_MARKER)
            and ref.kind == "mock-statement"
            and source.rstrip("\n") not in _mirror_sources(ref.path)
        ):
            self.analysis.errors.append(
                f"{ref.rel}:cell {index}: '# Checks:' in a mock statement is allowed only on a "
                "paper-provided cell (byte-identical to a code cell of its solution, D1 rule 4)"
            )
        for line_no, texts in comments.by_line.items():
            if line_no != 1 and any(text.startswith(CHECKS_MARKER) for text in texts):
                self.analysis.errors.append(
                    f"{ref.rel}:cell {index}:line {line_no}: misplaced '# Checks:' marker "
                    "(it must be the cell's first line)"
                )

    # ------------------------------------------------------------------ rules

    def _rules(self, ref: NotebookRef) -> frozenset[int]:
        if ref.kind in MOCK_KINDS:
            rules = self.config.mock_rules
        else:
            rules = frozenset({1, 2, 3})
        if ref.kind in STATEMENT_KINDS:
            rules = rules - {2}
        return rules

    def _use(self, ctx: _Ctx, call: ast.Call, callee: str, written: str, required: set[str]) -> None:
        ref = ctx.ref
        analysis = self.analysis
        forms = analysis.forms.setdefault(callee, {callee})
        forms.add(written)
        if written.startswith("."):
            forms.add(written)
        if call.lineno in ctx.harness_lines or (
            call.lineno in ctx.boilerplate_lines and callee in self.config.idiom_callees
        ):
            self.harness.add(callee)
            return
        self.nonharness.add(callee)
        if ref.selected:
            analysis.use_count[callee] += 1
        statement = ref.kind in STATEMENT_KINDS
        attached = ctx.attached(call, single_above=statement)
        word = callee.rsplit(".", 1)[-1]
        names_callee = any(names_word(text, word) for text in attached)
        if statement and ref.selected:
            self._statement_restrictions(ctx, call, attached, names_callee, required)
        rules = self._rules(ref)
        keywords = {kw.arg for kw in call.keywords if kw.arg in self.config.semantic_keywords}
        positional = word in self.config.positional_callees
        npos = f"npos={sum(1 for a in call.args if not isinstance(a, ast.Starred))}"
        line = ctx.lines[call.lineno - 1].strip() if call.lineno - 1 < len(ctx.lines) else ""

        def site(rule: int, element: str | None, explained: bool, evidence: str, exempt: str | None = None) -> None:
            if not ref.selected:
                return
            analysis.sites.append(
                Site(
                    rule=rule, rel=ref.rel, book=ref.book, unit=ref.unit, kind=ref.kind,
                    cell=ctx.cell, line=call.lineno, callee=callee, written=written,
                    element=element, explained=explained, evidence=evidence, exempt=exempt,
                    code=line[:120],
                )
            )

        def markdown_names() -> bool:
            return _markdown_names(ctx.markdown, callee, written)

        if callee not in self.first:
            self.first[callee] = (ref.book, ref.unit)
            self.unit_seen.add((callee, ref.unit))
            self.units_used[callee].append(ref.unit)
            self.elements[callee] |= keywords | ({npos} if positional else set())
            if ref.selected and ref.kind not in MOCK_KINDS:
                analysis.book_first.setdefault(ref.unit, [])
                if callee not in analysis.book_first[ref.unit]:
                    analysis.book_first[ref.unit].append(callee)
            if 1 in rules:
                if names_callee:
                    site(1, None, True, "comment")
                elif markdown_names():
                    site(1, None, True, "markdown")
                elif ref.rel in self.guard_paths and self.card_lists(ref, callee, "new"):
                    site(1, None, True, "card-new (guard-protected)")
                else:
                    site(1, None, False, "none")
            return
        if (callee, ref.unit) not in self.unit_seen:
            self.unit_seen.add((callee, ref.unit))
            earlier = len(self.units_used[callee])
            self.units_used[callee].append(ref.unit)
            if ref.selected and ref.kind not in MOCK_KINDS:
                analysis.rule3.setdefault(ref.unit, set()).add(callee)
            if 3 in rules:
                if callee in self.config.no_reminder:
                    site(3, None, True, "exempt", "no-reminder")
                elif callee in self.config.graduated and earlier >= self.config.graduation_units:
                    site(3, None, True, "exempt", "graduated")
                elif names_callee:
                    site(3, None, True, "comment")
                elif markdown_names():
                    site(3, None, True, "markdown")
                elif self.card_lists(ref, callee, "also"):
                    site(3, None, True, "card-also")
                else:
                    site(3, None, False, "none")
        if 2 not in rules:
            return
        new_elements = sorted(keywords - self.elements[callee])
        if positional and npos not in self.elements[callee]:
            new_elements.append(npos)
        for element in new_elements:
            self.elements[callee].add(element)
            if element.startswith("npos="):
                explained = names_callee or any(
                    names_word(text, w) for text in attached for w in self.config.positional_words
                )
            else:
                explained = any(names_word(text, element) for text in attached)
            site(2, element, explained, "comment" if explained else "none")

    def _statement_restrictions(
        self, ctx: _Ctx, call: ast.Call, attached: list[str], names_callee: bool, required: set[str]
    ) -> None:
        ref = ctx.ref
        keywords = {kw.arg for kw in call.keywords if kw.arg in self.config.semantic_keywords}
        word = call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
        for text in attached:
            if not names_word(text, word) and any(names_word(text, k) for k in keywords):
                self.analysis.errors.append(
                    f"{ref.rel}:cell {ctx.cell}:line {call.lineno}: statement comment {text!r} "
                    "explains a keyword only (rule 2 does not apply in statements, D4)"
                )
            elif names_word(text, word):
                leaked = sorted(name for name in required if names_word(text, name))
                if leaked:
                    self.analysis.errors.append(
                        f"{ref.rel}:cell {ctx.cell}:line {call.lineno}: statement comment {text!r} "
                        f"names required identifier(s) {', '.join(leaked)} (D4)"
                    )


def _mirror_path(statement: Path) -> Path:
    """`<mock>/problems/pNN.ipynb` -> `<mock>/solutions/pNN_solution.ipynb`."""
    return statement.parent.parent / "solutions" / f"{statement.stem}_solution.ipynb"


def _mirror_sources(statement: Path) -> set[str]:
    """Code-cell sources of a mock statement's solution (paper-provided cells mirror them).

    Byte-identical apart from trailing newlines, which notebook writers add or drop.
    """
    try:
        notebook = json.loads(_mirror_path(statement).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {
        _source(cell).rstrip("\n")
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    }


def _markdown_names(markdown: str, callee: str, written: str) -> bool:
    if not markdown:
        return False
    spans = markdown_code_spans(markdown)
    if not spans:
        return False
    method = callee.rsplit(".", 1)[-1]
    is_method = written.startswith(".")
    patterns: list[str] = []
    if is_method:
        patterns.append(re.escape(f".{method}("))
        if not callee.startswith("."):
            patterns.append(r"(?<![\w.])" + re.escape(callee) + r"(?!\w)")
    else:
        for form in {callee, written}:
            patterns.append(r"(?<![\w.])" + re.escape(form) + r"(?!\w)")
    regex = re.compile("|".join(patterns))
    return any(regex.search(span) for span in spans)


# --------------------------------------------------------------------------- the check


def analyze(
    root: str | Path,
    *,
    config: Config | None = None,
    waivers: list[Waiver] | None = None,
) -> Analysis:
    root = Path(root).resolve()
    config = config or load_config()
    waivers = load_waivers() if waivers is None else waivers
    repo_root, books, selected_id = _scan_plan(root)
    scanner = _Scanner(config, waivers, repo_root, _local_modules([path for _, path in books]))
    analysis = scanner.analysis
    analysis.selected_book = selected_id
    sequence: list[NotebookRef] = []
    for book_id, book_root in books:
        sequence += book_sequence(book_root, book_id, repo_root, book_id == selected_id)
    for ref in sequence:
        scanner.scan(ref)
    analysis.units = []
    for ref in sequence:
        if ref.selected and ref.kind not in MOCK_KINDS and ref.unit not in analysis.units:
            analysis.units.append(ref.unit)
    analysis.harness_only = scanner.harness - scanner.nonharness
    _apply_waivers(analysis, waivers, root, repo_root)
    _check_cards(analysis, sequence)
    _check_lists(analysis, config, scanner)
    return analysis


def _apply_waivers(analysis: Analysis, waivers: list[Waiver], root: Path, repo_root: Path) -> None:
    try:
        book_prefix = root.relative_to(repo_root).as_posix() + "/"
    except ValueError:
        book_prefix = ""
    used: set[int] = set()
    for site in analysis.sites:
        if not site.selected or not site.failing:
            continue
        for number, waiver in enumerate(waivers):
            if not waiver.matches(site.rel, site.cell, site.callee):
                continue
            if waiver.reason == GUARD_PROTECTED:
                if site.rule == 1:
                    continue  # D8: book-first callees there are explained by the card
                site.exempt = GUARD_PROTECTED
                analysis.guard_waived += 1
            else:
                site.exempt = "waived"
                analysis.waived += 1
            used.add(number)
            break
    for number, waiver in enumerate(waivers):
        if number in used or waiver.reason == GUARD_PROTECTED:
            continue
        if book_prefix and not waiver.path.startswith(book_prefix):
            continue
        analysis.errors.append(
            f"stale waiver: {waiver.path}:cell {waiver.cell if waiver.cell is not None else '*'} "
            f"{waiver.callee or '*'} matches no unexplained site"
        )


def _card_keys(names: list[str], analysis: Analysis) -> tuple[set[str], list[str]]:
    lookup: dict[str, set[str]] = defaultdict(set)
    for callee, forms in analysis.forms.items():
        for form in forms:
            lookup[form].add(callee)
    keys: set[str] = set()
    unknown: list[str] = []
    for name in names:
        matches = lookup.get(name)
        if matches:
            keys |= matches
        else:
            unknown.append(name)
    return keys, unknown


def _check_cards(analysis: Analysis, sequence: list[NotebookRef]) -> None:
    unit_dirs: dict[str, Path] = {}
    for ref in sequence:
        if ref.selected and ref.kind not in MOCK_KINDS and ref.unit not in unit_dirs:
            unit_dirs[ref.unit] = _unit_folder(ref.path)
    for unit in analysis.units:
        folder = unit_dirs[unit]
        rel_folder = _rel(folder, analysis.repo_root)
        lesson = folder / "lesson.ipynb"
        card = _read_card(lesson, analysis.repo_root)
        if card is None:
            analysis.errors.append(f"{rel_folder}/lesson.ipynb: missing API card ('{CARD_MARKER}', D3)")
            continue
        where = f"{card.rel}:cell {card.cell}"
        if not card.is_last:
            analysis.errors.append(f"{where}: the API card must be the notebook's last cell")
        if not card.heading_ok:
            analysis.errors.append(
                f"{where}: the API card must open with an unnumbered '## ' heading after its "
                "marker (it closes an open answer region, D8)"
            )
        new_keys, unknown_new = _card_keys(card.new, analysis)
        also_keys, unknown_also = _card_keys(card.also, analysis)
        for name in unknown_new + unknown_also:
            analysis.errors.append(f"{where}: card names unknown callee `{name}`")
        book_first = set(analysis.book_first.get(unit, []))
        for callee in sorted(book_first - new_keys):
            analysis.errors.append(f"{where}: book-first callee {callee} missing from 'New in this unit'")
        for callee in sorted(new_keys - book_first):
            analysis.errors.append(f"{where}: 'New in this unit' lists {callee}, not book-first in {unit}")
        for callee in sorted(also_keys - analysis.rule3.get(unit, set())):
            analysis.errors.append(f"{where}: 'Also used here' lists {callee}, not a rule-3 callee of {unit}")
        for callee in sorted((new_keys | also_keys) & analysis.harness_only):
            analysis.errors.append(f"{where}: card names harness-only callee {callee}")
        review = folder / "review.ipynb"
        if review.is_file():
            copy = _read_card(review, analysis.repo_root)
            if copy is None:
                analysis.errors.append(f"{rel_folder}/review.ipynb: missing copy of the API card (D3)")
                continue
            if not copy.is_last:
                analysis.errors.append(f"{copy.rel}:cell {copy.cell}: the API card must be the last cell")
            if not copy.heading_ok:
                analysis.errors.append(
                    f"{copy.rel}:cell {copy.cell}: the API card must open with an unnumbered "
                    "'## ' heading after its marker (D8)"
                )
            if (
                _card_keys(copy.new, analysis)[0] != new_keys
                or _card_keys(copy.also, analysis)[0] != also_keys
            ):
                analysis.errors.append(
                    f"{copy.rel}:cell {copy.cell}: review card entries differ from the lesson card"
                )


def _unit_folder(path: Path) -> Path:
    folder = path.parent
    while folder.parent.name != "units" and folder.parent != folder:
        folder = folder.parent
    return folder


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_card(path: Path, repo_root: Path) -> Card | None:
    if not path.is_file():
        return None
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return parse_card(notebook, _rel(path, repo_root))


def _check_lists(analysis: Analysis, config: Config, scanner: _Scanner) -> None:
    for callee in sorted(config.graduated):
        if callee not in scanner.first:
            analysis.errors.append(f"graduated lists {callee}, which no notebook calls")
    overlap = config.graduated & config.no_reminder
    for callee in sorted(overlap):
        analysis.errors.append(f"{callee} is listed as both graduated and no_reminder")


def summary_lines(analysis: Analysis, config: Config) -> list[str]:
    sites = [site for site in analysis.sites if site.selected]
    subject = [site for site in sites if site.subject]
    failing = [site for site in sites if site.failing]
    by_rule = Counter(site.rule for site in subject)
    failing_by_rule = Counter(site.rule for site in failing)
    exempt = Counter(site.exempt for site in sites if site.exempt)
    rule2_noise = Counter(
        site.element for site in subject if site.rule == 2 and site.element in {"size", "dtype", "device"}
    )
    cap = config.waiver_cap_percent / 100 * len(subject)
    book = analysis.selected_book
    return [
        (
            f"{book}: rule-subject sites {len(subject)} "
            f"(rule 1: {by_rule[1]}, rule 2: {by_rule[2]}, rule 3: {by_rule[3]})"
        ),
        (
            f"{book}: unexplained {len(failing)} (rule 1: {failing_by_rule[1]}, "
            f"rule 2: {failing_by_rule[2]}, rule 3: {failing_by_rule[3]})"
        ),
        (
            f"{book}: exempt graduated {exempt['graduated']}, "
            f"no-reminder {exempt['no-reminder']}, guard-protected {analysis.guard_waived}"
        ),
        (
            f"{book}: rule-2 sites for size/dtype/device: "
            f"{rule2_noise['size']}/{rule2_noise['dtype']}/{rule2_noise['device']}"
        ),
        (
            f"{book}: waivers {analysis.waived} of {len(subject)} rule-subject sites "
            f"(cap {config.waiver_cap_percent:g}% = {cap:.1f})"
        ),
    ]


def check_api_comments(
    root: str | Path,
    *,
    config: Config | None = None,
    waivers: list[Waiver] | None = None,
) -> Report:
    config = config or load_config()
    analysis = analyze(root, config=config, waivers=waivers)
    findings = list(analysis.errors)
    findings += [site.describe() for site in analysis.sites if site.selected and site.failing]
    subject = len(analysis.subject_sites())
    if analysis.waived > config.waiver_cap_percent / 100 * subject:
        findings.append(
            f"waivers {analysis.waived} exceed {config.waiver_cap_percent:g}% of "
            f"{subject} rule-subject sites"
        )
    summary = summary_lines(analysis, config)
    if config.enforce:
        return Report(name=NAME, ok=not findings, errors=findings, warnings=summary)
    report_mode = [f"report mode (enforce: false): {len(findings)} finding(s)"]
    return Report(name=NAME, ok=True, warnings=[*findings, *summary, *report_mode])


# --------------------------------------------------------------------------- inventory CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.checks.api_comments",
        description="Per-unit API-comment inventory (Plan 032).",
    )
    parser.add_argument("--root", required=True, help="book root, e.g. book1")
    parser.add_argument("--unit", action="append", default=[], help="only this unit id (repeatable)")
    parser.add_argument("--findings", action="store_true", help="list failing sites and errors")
    parser.add_argument("--csv", help="write every site to this CSV file")
    args = parser.parse_args(argv)
    config = load_config()
    analysis = analyze(args.root, config=config)
    sites = [site for site in analysis.sites if site.selected]
    if args.unit:
        sites = [site for site in sites if site.unit in args.unit]
    units: list[str] = []
    for site in sites:
        if site.unit not in units:
            units.append(site.unit)
    print("| unit | r1 | r1 open | r2 | r2 open | r3 | r3 open | r3 exempt |")
    print("|---|---|---|---|---|---|---|---|")
    for unit in units:
        mine = [site for site in sites if site.unit == unit]
        cells = []
        for rule in (1, 2, 3):
            subject = [s for s in mine if s.rule == rule and s.subject]
            cells += [len(subject), sum(1 for s in subject if s.failing)]
        exempt = sum(1 for s in mine if s.rule == 3 and not s.subject)
        print(f"| {unit} | " + " | ".join(str(c) for c in cells) + f" | {exempt} |")
    for line in summary_lines(analysis, config):
        print(line)
    if args.findings:
        for error in analysis.errors:
            if not args.unit or any(f"/{u}" in error or f"-{u}" in error for u in args.unit):
                print(f"ERROR {error}")
        for site in sites:
            if site.failing:
                print(f"OPEN {site.describe()}  | {site.code}")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["rule", "book", "unit", "notebook", "kind", "cell", "line", "callee", "written",
                 "element", "explained", "evidence", "exempt", "code"]
            )
            for site in sites:
                writer.writerow(
                    [site.rule, site.book, site.unit, site.rel, site.kind, site.cell, site.line,
                     site.callee, site.written, site.element or "", site.explained,
                     site.evidence, site.exempt or "", site.code]
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())
