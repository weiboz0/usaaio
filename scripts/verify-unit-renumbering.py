#!/usr/bin/env python3
"""Plan 031 Task 4: content-invariance checks (a)-(e) for the Book 1 renumbering.

Compares every file under book1/ and book2/ at a base ref (default: main) with its
counterpart in the working tree, paired through the folder mapping.

(a) round trip: the renumbering script's forward rewrite of each base file equals the
    branch file byte for byte, except the declared structural exceptions;
(b) masked diff: with every (F|C)<n> token and every `units/NN-` prefix masked, base and
    branch agree except on lines a hand-reviewed override touched;
(c) every data/ file is byte-identical (sha256);
(d) the practice-id multiset, with the mapping undone, equals the base's;
(e) every mutation marker resolves to a real target in its notebook.

Usage: python3 scripts/verify-unit-renumbering.py [--base main]
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Declared structural exceptions (Plan 031 Task 4): reviewed by hand, not by (a)/(b).
STRUCTURAL = {
    "book1/publication.yaml": "chapters:/volumes: reordered and recomputed (D4)",
    "book1/curriculum/material-inventory.yaml": "generated (audit_curriculum --check)",
    "book2/curriculum/material-inventory.yaml": "generated (audit_curriculum --check)",
    "book1/docs/course-structure.md": "generated (render_course_structure --check)",
    "book2/docs/course-structure.md": "generated (render_course_structure --check)",
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


renumber = _load("renumber_book1_units", ROOT / "scripts" / "renumber-book1-units.py")


def git_bytes(ref: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, check=True
    ).stdout


def base_files(ref: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", "book1", "book2"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def branch_files() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files", "--", "book1", "book2"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return {line for line in out.splitlines() if line}


def expected_branch_text(path: str, text: str) -> str:
    if renumber.is_excluded(path) or renumber.is_data_payload(path):
        return text
    new = renumber.rewrite_text(text, path)
    if path == renumber.SCHEDULE:
        new = renumber.insert_teaching_order(new)
    return new


MASK = re.compile(r"(?<![A-Za-z0-9_])(?:F[1-7]|C1[0-2]|C[1-9])(?![0-9])")
FOLDER = re.compile(r"units/\d{2}-|units(\\?[\"']\s*/\s*\\?[\"'])\d{2}-")


def masked(text: str) -> list[str]:
    return [MASK.sub("X", FOLDER.sub(lambda m: m.group(0)[:-3], line)) for line in text.splitlines()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--base", default="main")
    args = parser.parse_args(argv)
    failures: list[str] = []
    paired = 0
    masked_residue: list[str] = []
    data_checked = 0
    seen_branch: set[str] = set()
    override_keys = tuple(renumber.OVERRIDES)

    for path in base_files(args.base):
        new_path = renumber.rewrite_path(path)
        seen_branch.add(new_path)
        target = ROOT / new_path
        if not target.is_file():
            failures.append(f"missing branch counterpart: {path} -> {new_path}")
            continue
        old_bytes = git_bytes(args.base, path)
        new_bytes = target.read_bytes()
        paired += 1
        if "/data/" in f"/{path}" and not path.endswith(".py"):
            data_checked += 1
            if hashlib.sha256(old_bytes).digest() != hashlib.sha256(new_bytes).digest():
                failures.append(f"(c) data file changed: {path}")
            continue
        try:
            old_text = old_bytes.decode("utf-8")
            new_text = new_bytes.decode("utf-8")
        except UnicodeDecodeError:
            if old_bytes != new_bytes:
                failures.append(f"(a) binary file changed: {path}")
            continue
        if path in STRUCTURAL:
            continue
        if expected_branch_text(path, old_text) != new_text:
            failures.append(f"(a) round trip differs: {path}")
        # (b) masked comparison, ignoring the schedule's inserted teaching_order block.
        if path == renumber.SCHEDULE:
            new_text = re.sub(r"(?m)^teaching_order:\n(?:- .*\n)+", "", new_text)
        old_lines, new_lines = masked(old_text), masked(new_text)
        if old_lines != new_lines:
            if len(old_lines) != len(new_lines):
                failures.append(f"(b) masked line count differs: {path}")
                continue
            for number, (before, after) in enumerate(zip(old_lines, new_lines, strict=True), 1):
                if before == after:
                    continue
                original = old_text.splitlines()[number - 1]
                if any(key in original for key in override_keys):
                    masked_residue.append(f"{path}:{number} (override)")
                else:
                    failures.append(f"(b) masked diff at {path}:{number}")

    extra = sorted(branch_files() - seen_branch)
    if extra:
        failures.extend(f"branch file with no base counterpart: {path}" for path in extra)

    # (d) practice-id multiset with the mapping undone.
    def practice_ids(read, paths: list[str]) -> collections.Counter:
        ids: collections.Counter = collections.Counter()
        for path in paths:
            raw = yaml.safe_load(read(path)) or {}
            for row in raw.get("practice") or []:
                if isinstance(row, dict) and "id" in row:
                    ids[str(row["id"])] += 1
        return ids

    manifest = re.compile(r"book1/units/[^/]+/manifest\.yaml\Z")
    base_ids = practice_ids(lambda p: git_bytes(args.base, p), [p for p in base_files(args.base) if manifest.match(p)])
    branch_ids = practice_ids(
        lambda p: (ROOT / p).read_bytes(), sorted(p for p in branch_files() if manifest.match(p))
    )
    inverse = {new: old for old, new in renumber.CODE_MAP.items()}
    undone = collections.Counter()
    for practice_id, count in branch_ids.items():
        code, rest = practice_id.split("-", 1)
        undone[f"{inverse[code]}-{rest}"] += count
    if undone != base_ids:
        failures.append("(d) practice-id multiset differs after undoing the mapping")

    # (e) every mutation marker resolves to a real target.
    mutation_count = 0
    for module_name, book in (
        ("verify_training_mutations", "book1"),
        ("verify_classical_mutations", "book1"),
        ("verify_attention_mutations", "book2"),
    ):
        module = _load(f"plan031_{module_name}", ROOT / "tools" / f"{module_name}.py")
        for spec in module.MUTATIONS:
            mutation_count += 1
            notebook = ROOT / book / spec.notebook
            if not notebook.is_file():
                failures.append(f"(e) {spec.id}: notebook missing {book}/{spec.notebook}")
                continue
            text = notebook.read_text(encoding="utf-8")
            import json

            sources = [
                "".join(cell["source"]) for cell in json.loads(text)["cells"] if cell["cell_type"] == "code"
            ]
            hits = sum(source.count(spec.search) for source in sources)
            if hits != 1 or spec.target_marker not in spec.search:
                failures.append(f"(e) {spec.id}: search target found {hits} times")
            if not any(spec.expected_failure_marker in source for source in sources):
                failures.append(f"(e) {spec.id}: failure marker {spec.expected_failure_marker!r} not found")

    print(f"(a) paired files: {paired}; structural exceptions: {len(STRUCTURAL)}")
    print(f"(b) masked-diff override lines: {len(masked_residue)}")
    for line in masked_residue:
        print(f"    {line}")
    print(f"(c) data files byte-identical: {data_checked}")
    print(f"(d) practice ids: base {sum(base_ids.values())}, branch {sum(branch_ids.values())}")
    print(f"(e) mutation markers resolved: {mutation_count}")
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    print("unit-renumbering invariance: " + ("FAIL" if failures else "OK"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
