#!/usr/bin/env python3
"""Plan 031 one-shot rewrite: put Book 1 units in teaching order.

The mapping below is the single source of truth (Plan 031 "The mapping").
One pass:

* renames every Book 1 unit folder to ``NN-<new id>`` with ``git mv``;
* rewrites every tracked text file (outside the exclusion list) with ONE
  longest-first regex alternation over four token classes (Plan 031 D2/D6):

  1. full ids ``<code>-<slug>`` (``book1:`` qualified ids included); after a
     ``units/`` path segment or a ``"units" / "<id>"`` code join the id is a
     folder and becomes ``NN-<new id>``;
  2. practice ids ``<code>-pNN`` (and ``<code>-p{...}`` f-strings);
  3. lesson references ``<code>-NN``;
  4. standalone codes, subject to deny contexts (matplotlib colour strings,
     the F1 metric) and a hand-reviewed residue override table.

  Every match is mapped once from the original text; nothing rewritten is
  re-scanned, so the F3<->F4 swap and the C5..C11 cycle are safe.

* inserts ``teaching_order:`` into ``book1/curriculum/course-schedule.yaml``
  (the migration-state marker);
* renames ``tests/test_c11_solution_regressions.py``.

Idempotence is by migration state, not by text: a migrated tree is a no-op
(exit 0), a half-migrated tree exits non-zero without writing anything.

Usage::

    python3 scripts/renumber-book1-units.py --dry-run   # report only
    python3 scripts/renumber-book1-units.py             # apply
"""

from __future__ import annotations

import argparse
import collections
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# (teaching order, old id, new id) — Plan 031 "The mapping".
MAPPING: tuple[tuple[str, str, str], ...] = (
    ("01", "F1-scientific-python", "F1-scientific-python"),
    ("02", "F2-vectors", "F2-vectors"),
    ("03", "F4-multivar-calculus", "F3-multivar-calculus"),
    ("04", "F3-matrices", "F4-matrices"),
    ("05", "F5-probability", "F5-probability"),
    ("06", "C1-ml-fundamentals", "C1-ml-fundamentals"),
    ("07", "C2-linear-models", "C2-linear-models"),
    ("08", "C3-gradient-descent", "C3-gradient-descent"),
    ("09", "C4-classical-ml-practice", "C4-classical-ml-practice"),
    ("10", "C8-embeddings", "C5-embeddings"),
    ("11", "C5-neural-networks", "C6-neural-networks"),
    ("12", "F6-svd-spectral", "F6-svd-spectral"),
    ("13", "C6-pytorch", "C7-pytorch"),
    ("14", "F7-kernels-convex-optimization", "F7-kernels-convex-optimization"),
    ("15", "C11-neural-training", "C8-neural-training"),
    ("16", "C9-dimensionality-reduction", "C9-dimensionality-reduction"),
    ("17", "C7-cnn-transfer", "C10-cnn-transfer"),
    ("18", "C10-competition-craft", "C11-competition-craft"),
    ("19", "C12-classical-models", "C12-classical-models"),
)

OLD_TO_NEW_ID = {old: new for _, old, new in MAPPING}
OLD_TO_FOLDER = {old: f"{order}-{new}" for order, old, new in MAPPING}
NEW_FOLDERS = tuple(f"{order}-{new}" for order, _, new in MAPPING)
TEACHING_ORDER = tuple(new for _, _, new in MAPPING)


def _code(unit_id: str) -> str:
    return unit_id.split("-", 1)[0]


CODE_MAP = {_code(old): _code(new) for _, old, new in MAPPING}
CHANGED_CODES = frozenset(code for code, new in CODE_MAP.items() if code != new)

# Paths never rewritten: historical records (Plan 031 D2), the hand-migrated
# Plan 019 inventory (D3), and the files that hold the old ids as data.
# docs/designs/ holds per-plan design records (historical, like plans); design
# 017 explains why C11 was NOT renumbered and would read falsely if rewritten.
EXCLUDED_PREFIXES = ("docs/plans/", "docs/designs/")
EXCLUDED_FILES = frozenset(
    {
        "TODO.md",
        "scripts/renumber-book1-units.py",
        "scripts/verify-unit-renumbering.py",
        "tests/test_renumber_book1_units.py",
        "docs/unit-renumbering.md",
        "tests/fixtures/plan019-path-inventory.yaml",
        # The Plan 019 enforcement verifier and its tests hold historical pre-rename paths
        # (D3); they are migrated by hand.
        "scripts/verify-staged-scope.py",
        "tests/test_clean_checkout.py",
        # Plan 031's own guard tests use base-side (old) unit folders as fixtures.
        "tests/test_plan031_guard.py",
        "tests/test_unit_order.py",
    }
)
EXCLUDED_NAMES = frozenset({"ERRATA.md"})
# Data payloads keep their bytes (Plan 031 Task 4 (c)); hits are reported, never written.
DATA_SUFFIXES = frozenset({".csv", ".json", ".txt", ".npz", ".npy", ".pt", ".parquet"})
BINARY_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".woff", ".woff2", ".ttf"})

CODE_ALT = r"F[1-7]|C1[0-2]|C[1-9]"
_ID_ALT = "|".join(sorted(map(re.escape, OLD_TO_NEW_ID), key=len, reverse=True))
# A folder context: `units/<id>` or a code join `"units" / "<id>"` (JSON-escaped
# quotes in notebooks too).
_FOLDER_PREFIX = r"""units/|units\\?["']\s*/\s*\\?["']"""

TOKEN = re.compile(
    rf"(?P<full>(?<![A-Za-z0-9_])(?P<folder>{_FOLDER_PREFIX})?(?P<id>{_ID_ALT})(?![A-Za-z0-9_]))"
    rf"|(?P<practice>(?<![A-Za-z0-9_])(?P<pcode>{CODE_ALT})(?=-p(?:\d|\{{)))"
    rf"|(?P<lesson>(?<![A-Za-z0-9_])(?P<lcode>{CODE_ALT})(?=-\d\d(?!\d)))"
    rf"|(?P<bare>(?<![A-Za-z0-9_:-])(?P<bcode>{CODE_ALT})(?![A-Za-z0-9_-]))"
)

# Hand-reviewed residue (Plan 031 D6): literal overrides applied in the same
# single pass. Each key is matched verbatim (with its surrounding words so it
# is unique) and maps to its replacement; the codes inside are not re-scanned.
OVERRIDES: dict[str, str] = {
    # r1-001 provenance: old C5-C7 (neural networks, PyTorch, CNN transfer)
    # are now C6, C7 and C10 — no longer a contiguous range.
    "taught by units C5-C7;": "taught by units C6, C7 and C10;",
    # A notebook code comment naming the multivariable-calculus convention.
    "# F4-convention residual": "# F3-convention residual",
    # Notation section range: old F1-F3 (Python, vectors, matrices) is now F1, F2, F4.
    "shapes · F1–F3": "shapes · F1, F2, F4",
    # Old F1-F4 is the same set of four units after the swap: keep the range.
    "drills of F1–F4": "drills of F1–F4",
    # The register-check marker carries the code (Plan 031 D5 literal tables).
    "C7-budget-register": "C10-budget-register",
    # The double-length roster stays in ascending code order.
    "F5, F6, C7, C11, C12": "F5, F6, C8, C10, C12",
}

# Hand-reviewed hits that are NOT Book 1 unit codes: (pre-rename path, line
# substring). Populated from the Task 1 dry-run review.
RESIDUE_DENY: frozenset[tuple[str, str]] = frozenset(
    {
        # F3 Session 2 names a cosine-similarity matrix `C6` (a Python variable).
        ("book1/units/F3-matrices/lessons/02-multiplication-and-gram-matrices.ipynb", "C6 = G6"),
        ("book1/units/F3-matrices/lessons/02-multiplication-and-gram-matrices.ipynb", "print(C6)"),
        ("book1/units/F3-matrices/lessons/02-multiplication-and-gram-matrices.ipynb", "round(C6[0, 2]"),
    }
)


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    token_class: str
    context_class: str
    old: str
    new: str
    excerpt: str
    in_code_cell: bool


_CELL_TYPE = re.compile(r'"cell_type":\s*"(\w+)"')
_COLOR_BEFORE = re.compile(r"""(?:colou?rs?|c|fmt)\s*=\s*\[?[^\]\n]*\\?["']$|plot\([^\n]*\\?["']$""")


def _line_bounds(text: str, start: int, end: int) -> tuple[int, int]:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    return line_start, len(text) if line_end < 0 else line_end


def _in_code_cell(text: str, start: int, path: str) -> bool:
    if not path.endswith(".ipynb"):
        return False
    last = None
    for last in _CELL_TYPE.finditer(text, 0, start):
        pass
    return bool(last and last.group(1) == "code")


def _classify_bare(text: str, start: int, end: int, path: str) -> str:
    """Context class of a standalone code (Plan 031 D6)."""
    code = text[start:end]
    before = text[max(0, start - 40):start]
    after = text[end:end + 30]
    line_start, line_end = _line_bounds(text, start, end)
    line = text[line_start:line_end]
    # Deny: matplotlib colour cycle strings "C0".."C9" and "C3--" format strings.
    quoted = re.search(r"""\\?["']$""", before) and re.match(r"""(?:[-.:o^sx*+]{1,3})?\\?["']""", after)
    if quoted and (
        _COLOR_BEFORE.search(before)
        or re.match(r"""[-.:o^sx*+]{1,3}\\?["']""", after)
        or (path.endswith(".ipynb") and ("color" in line or "plot(" in line or "scatter(" in line))
    ):
        return "deny-colour"
    # Deny: the F1 metric (F1 score, macro-averaged F1, f1).
    if code == "F1" and (
        re.match(r"\s*(?:score|-score|metric)", after, re.IGNORECASE)
        or re.search(r"(?:macro|micro|weighted)[- ](?:averaged )?$", before, re.IGNORECASE)
        or re.search(r"(?:macro|micro)-?$", before, re.IGNORECASE)
    ):
        return "deny-metric"
    if path == "docs/unit-standards.md":
        return "accept-unit-standards"
    if path == "tools/render_curriculum_roadmap.py":
        return "accept-roadmap"
    if re.search(r"\*\($", before) and after.startswith(")*"):
        return "accept-glossary-tag"
    if before.endswith(("**", "`")):
        return "accept-bold-or-backtick"
    if re.match(r"(?:'s|’s)", after):
        return "accept-possessive"
    if re.match(r"\s+(?:Session|session|lesson|Lesson|lessons|Lessons|sessions|Sessions)\b", after):
        return "accept-session-or-lesson"
    if before.endswith("(") or re.match(r"\s*\)", after):
        return "accept-parenthesized"
    return "residue"


def rewrite_text(text: str, path: str, hits: list[Hit] | None = None) -> str:
    """Forward rewrite of one file's text (Plan 031 D2/D6). Pure and deterministic."""
    if not text:
        return text
    pieces: list[str] = []
    cursor = 0
    override_alt = "|".join(re.escape(key) for key in sorted(OVERRIDES, key=len, reverse=True))
    pattern = re.compile(f"(?P<override>{override_alt})|{TOKEN.pattern}") if override_alt else TOKEN
    for match in pattern.finditer(text):
        start, end = match.span()
        old = match.group(0)
        context = ""
        token_class = ""
        if match.groupdict().get("override"):
            token_class, context, new = "override", "override", OVERRIDES[old]
        elif match.group("full"):
            unit_id = match.group("id")
            token_class = "full"
            if match.group("folder"):
                context = "folder"
                new = match.group("folder") + OLD_TO_FOLDER[unit_id]
            else:
                context = "id"
                new = OLD_TO_NEW_ID[unit_id]
        elif match.group("practice"):
            token_class, context, new = "practice", "practice-id", CODE_MAP[old]
        elif match.group("lesson"):
            token_class, context, new = "lesson", "lesson-ref", CODE_MAP[old]
        else:
            token_class = "bare"
            context = _classify_bare(text, start, end, path)
            line_start, line_end = _line_bounds(text, start, end)
            line = text[line_start:line_end]
            if context.startswith("deny") or any(
                deny_path == path and fragment in line for deny_path, fragment in RESIDUE_DENY
            ):
                new = old
                if not context.startswith("deny"):
                    context = "residue-deny"
            else:
                new = CODE_MAP[old]
        if hits is not None and (new != old or token_class == "override" or (token_class == "bare" and old in CHANGED_CODES)):
            line_start, line_end = _line_bounds(text, start, end)
            hits.append(
                Hit(
                    path=path,
                    line=text.count("\n", 0, start) + 1,
                    token_class=token_class,
                    context_class=context,
                    old=old,
                    new=new,
                    excerpt=text[line_start:line_end].strip()[:160],
                    in_code_cell=_in_code_cell(text, start, path),
                )
            )
        pieces.append(text[cursor:start])
        pieces.append(new)
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


def rewrite_path(path: str) -> str:
    """Map a repo-relative path from the old layout to the new one."""
    for old, folder in OLD_TO_FOLDER.items():
        prefix = f"book1/units/{old}/"
        if path.startswith(prefix) or path == prefix.rstrip("/"):
            return f"book1/units/{folder}/" + path[len(prefix):] if path.startswith(prefix) else f"book1/units/{folder}"
    if path == "tests/test_c11_solution_regressions.py":
        return "tests/test_c8_solution_regressions.py"
    return path


def is_excluded(path: str) -> bool:
    return (
        path.startswith(EXCLUDED_PREFIXES)
        or path in EXCLUDED_FILES
        or Path(path).name in EXCLUDED_NAMES
        or "/reference/" in f"/{path}"
    )


def is_data_payload(path: str) -> bool:
    return "/data/" in f"/{path}" and Path(path).suffix in DATA_SUFFIXES


def insert_teaching_order(text: str) -> str:
    block = "teaching_order:\n" + "".join(f"- {unit}\n" for unit in TEACHING_ORDER)
    marker = "\nweeks:\n"
    if marker not in text:
        raise SystemExit("course-schedule.yaml has no top-level weeks: key")
    return text.replace(marker, "\n" + block + "weeks:\n", 1)


SCHEDULE = "book1/curriculum/course-schedule.yaml"
_PREFIXED = re.compile(r"\d{2}-")


def migration_state(repo: Path) -> str:
    """'fresh', 'migrated', or 'half' (Plan 031 D2 idempotence)."""
    schedule = repo / SCHEDULE
    has_order = schedule.is_file() and re.search(r"(?m)^teaching_order:", schedule.read_text(encoding="utf-8"))
    units = repo / "book1" / "units"
    folders = {p.name for p in units.iterdir() if p.is_dir()} if units.is_dir() else set()
    prefixed = {name for name in folders if _PREFIXED.match(name)}
    old = {name for name in folders if name in OLD_TO_NEW_ID}
    if not has_order and not prefixed:
        return "fresh" if old == set(OLD_TO_NEW_ID) else "half"
    if has_order and prefixed == set(NEW_FOLDERS) and not old:
        return "migrated"
    return "half"


def tracked_files(repo: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=repo, check=True, capture_output=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


@dataclass
class Plan:
    rewrites: dict[str, str]
    hits: list[Hit]
    data_hits: list[Hit]
    counts: collections.Counter


def build_plan(repo: Path) -> Plan:
    rewrites: dict[str, str] = {}
    hits: list[Hit] = []
    data_hits: list[Hit] = []
    counts: collections.Counter = collections.Counter()
    for path in tracked_files(repo):
        if is_excluded(path) or Path(path).suffix in BINARY_SUFFIXES:
            continue
        file = repo / path
        if not file.is_file():
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        local: list[Hit] = []
        new_text = rewrite_text(text, path, local)
        if is_data_payload(path):
            data_hits.extend(h for h in local if h.old != h.new)
            continue
        if path == SCHEDULE:
            new_text = insert_teaching_order(new_text)
        hits.extend(local)
        if new_text != text:
            rewrites[path] = new_text
            counts[file_class(path)] += 1
    return Plan(rewrites, hits, data_hits, counts)


def file_class(path: str) -> str:
    top = path.split("/", 1)[0]
    if top in {"book1", "book2"}:
        suffix = Path(path).suffix or Path(path).name
        return f"{top} {suffix}"
    return f"{top}/" if "/" in path else path


def report(plan: Plan, out=sys.stdout) -> None:
    print("## Files rewritten per class", file=out)
    for key, value in sorted(plan.counts.items()):
        print(f"  {key}: {value}", file=out)
    print(f"  total: {sum(plan.counts.values())}", file=out)
    by_class = collections.Counter((h.token_class, h.context_class) for h in plan.hits if h.old != h.new)
    print("## Rewritten tokens by class/context", file=out)
    for (token_class, context), value in sorted(by_class.items()):
        print(f"  {token_class}/{context}: {value}", file=out)
    bare = [h for h in plan.hits if h.token_class == "bare" and h.old in CHANGED_CODES]
    bare_by = collections.Counter(h.context_class for h in bare)
    print(f"## Bare changed-code hits: {len(bare)}", file=out)
    for key, value in sorted(bare_by.items()):
        print(f"  {key}: {value}", file=out)
    print(f"  in notebook code cells: {sum(h.in_code_cell for h in bare)}", file=out)
    print("## Residue and deny hits (hand review)", file=out)
    for h in bare:
        if h.context_class.startswith(("residue", "deny")) or h.in_code_cell:
            cell = " [code]" if h.in_code_cell else ""
            print(f"  {h.path}:{h.line}{cell} {h.context_class} {h.old}->{h.new} | {h.excerpt}", file=out)
    print("## Overrides", file=out)
    for h in plan.hits:
        if h.token_class == "override":
            print(f"  {h.path}:{h.line} {h.old!r} -> {h.new!r}", file=out)
    print(f"## Data payload hits (never written): {len(plan.data_hits)}", file=out)
    for h in plan.data_hits:
        print(f"  {h.path}:{h.line} {h.old}", file=out)


def apply(repo: Path, plan: Plan) -> None:
    for order, old, _ in MAPPING:
        subprocess.run(
            ["git", "mv", f"book1/units/{old}", f"book1/units/{OLD_TO_FOLDER[old]}"],
            cwd=repo,
            check=True,
        )
    subprocess.run(
        ["git", "mv", "tests/test_c11_solution_regressions.py", "tests/test_c8_solution_regressions.py"],
        cwd=repo,
        check=True,
    )
    for path, text in plan.rewrites.items():
        (repo / rewrite_path(path)).write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    state = migration_state(args.repo)
    if state == "migrated":
        print("already migrated (teaching_order present, all folders prefixed): no-op")
        return 0
    if state == "half":
        print("half-migrated tree: refusing to write", file=sys.stderr)
        return 2
    plan = build_plan(args.repo)
    report(plan)
    if not args.dry_run:
        apply(args.repo, plan)
        print(f"applied: {len(MAPPING)} folder renames, {len(plan.rewrites)} files rewritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
