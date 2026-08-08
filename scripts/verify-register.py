#!/usr/bin/env python3
"""Verify registered statement metadata and every bolded ban's pricing.

All unit manifests are authoritative for problem paths. Header agreement (title,
concepts, difficulty, type) and ban pricing are checked across every unit. Full mode
requires every declared solution path; solution metadata is checked where present. The stricter
multiple-choice option-format checks remain scoped to the tranche-1 units that were
authored against that exact register.

Scope note: "every unit" means every manifest under units/. Mock-test statements under
mocktests/ carry their own per-part header register and are NOT covered here — the count
this script prints is a count of unit practice problems.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTER_UNITS = (
    "F1-scientific-python",
    "F2-vectors",
    "C1-ml-fundamentals",
    "C11-neural-training",
    "C12-classical-models",
)
# Tests may override this inventory; normal runs discover every unit manifest.
UNITS: tuple[str, ...] | None = None
# C7 has no honest historical per-problem minute data. A future capstone budget change must
# update both the student-facing statement and this explicit exception map. Unlike C11's
# manifest-driven budgets, these four values intentionally remain literal and closed-world.
C7_BUDGET_REGISTER = {
    "C7-p10": 75,
    "C7-p24": 75,
    "C7-p26": 75,
    "C7-p27": 75,
}
TYPE_LABELS = {
    "mc": "multiple choice",
    "mc-multipart": "multiple choice (multipart)",
    "mc-normal-form": "multiple choice (numeric, normal form)",
    "constrained-coding": "constrained coding",
    "integrative-constrained": "integrative constrained coding",
    "challenge-constrained": "challenge constrained coding",
    "scenario": "scenario analysis",
}
OPTION_LETTERS = list("ABCDE")
BOLD_BAN_RE = re.compile(
    r"\*\*((?:Additionally\s+)?Banned\b[^:]*:.*?)\*\*",
    re.IGNORECASE | re.DOTALL,
)
HEADER_FIELD_RE = re.compile(r"\*\*(Type|Difficulty|Concepts):\*\*\s*([^·]*?)\s*(?=·|$)")
HEADER_NAME_RE = re.compile(r"\*\*([^:*]+):\*\*")
# Glosses the corpus appends after a type name, keyed BY TYPE. Keying matters: a global list
# let `scenario analysis (parts consume earlier results)` pass, borrowing a gloss that only
# describes integrative problems. Any type not listed here admits no gloss at all.
TYPE_GLOSSES = {
    "integrative": frozenset(
        {
            "",
            " (multi-part; parts consume earlier results)",
            " (parts consume earlier results)",
        }
    ),
    "proof": frozenset({"", " / derivation"}),
}
NO_GLOSS = frozenset({""})
ZERO_POINT_RE = re.compile(r"\b(?:zero|0)[\s-]+points?\b", re.IGNORECASE)


def _source(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else source


def _expected_header(problem: dict) -> str:
    type_label = TYPE_LABELS.get(problem["type"], problem["type"].replace("-", " "))
    concepts = ", ".join(problem["concepts"])
    return (
        f"**Type:** {type_label} · **Difficulty:** {problem['difficulty']} "
        f"· **Concepts:** {concepts}"
    )


def _type_matches(actual: str, type_label: str, raw_type: str) -> bool:
    """The corpus writes a problem's type either as the raw manifest id ("scenario") or as its
    expanded label ("scenario analysis"), optionally followed by one of a few house glosses.

    The permitted glosses are ENUMERATED per type rather than described by shape. Three
    successive gate findings landed here: a bare `startswith` accepted "constrained coding
    ENTIRELY WRONG"; allowing any parenthetical or slash suffix then accepted "scenario
    (actually multiple choice)"; and a single global gloss list then let one type borrow
    another's gloss. A genuinely new house gloss should be added here deliberately, against the
    type it belongs to, rather than admitted by a permissive pattern.
    """
    allowed = TYPE_GLOSSES.get(raw_type, NO_GLOSS)
    for prefix in (type_label, raw_type):
        if actual.startswith(prefix) and actual[len(prefix) :] in allowed:
            return True
    return False


def _check_solution_header(unit: str, problem: dict) -> list[str]:
    """Most solutions carry no metadata header, which is the corpus convention. Where one IS
    present it is a second copy of the manifest's claims, and an unenforced second copy is how
    plan 014 shipped a statement saying "validation" beside a solution still saying "test".
    So: optional, but checked when present.
    """
    relative = problem.get("solution_path")
    if not isinstance(relative, str) or not relative.strip():
        return [f"{problem['id']}: solution_path is missing"]
    path = ROOT / "units" / unit / relative
    if not path.is_file():
        return [f"{problem['id']}: solution_path does not exist"]
    notebook = json.loads(path.read_text())
    markdown = [_source(cell) for cell in notebook["cells"] if cell["cell_type"] == "markdown"]
    if not markdown:
        return []
    # The TITLE is checked on every solution, not only the 5 that carry a metadata header.
    # Every solution has one, so gating mis-attribution coverage behind header presence would
    # have left 338 of 343 unprotected for no structural reason (gate finding, plan 014 r4).
    body = [line for line in markdown[0].splitlines() if line.strip()]
    expected_title = f"# {unit} — Practice {problem['id'].split('-')[-1]} — Solution"
    if not body or body[0] != expected_title:
        return [f"{problem['id']}: solution title does not match the manifest"]

    # The FIELD checks apply only where a header exists. Search every markdown cell, not just
    # the first: scanning only the first let a solution opt out by relocating its header lower
    # down. Absence stays legal — 328 of 343 solutions carry no header — but a header anywhere
    # is checked.
    header = next(
        (line for cell in markdown for line in cell.splitlines() if line.startswith("**Type:**")),
        None,
    )
    if header is None:
        if unit == "C11-neural-training":
            return [f"{problem['id']}: solution metadata header is missing"]
        return []
    if HEADER_NAME_RE.findall(header) != ["Type", "Difficulty", "Concepts"]:
        return [
            f"{problem['id']}: solution header fields must be exactly Type / Difficulty / Concepts"
        ]
    fields = dict(HEADER_FIELD_RE.findall(header))
    if set(fields) != {"Type", "Difficulty", "Concepts"}:
        return [f"{problem['id']}: solution header is missing one of Type / Difficulty / Concepts"]
    errors = []
    if fields["Concepts"] != ", ".join(problem["concepts"]):
        errors.append("solution header concepts do not match the manifest")
    if fields["Difficulty"] != problem["difficulty"]:
        errors.append("solution header difficulty does not match the manifest")
    type_label = TYPE_LABELS.get(problem["type"], problem["type"].replace("-", " "))
    if not _type_matches(fields["Type"], type_label, problem["type"]):
        errors.append("solution header type does not match the manifest")
    return [f"{problem['id']}: {error}" for error in errors]


def _check_problem(unit: str, problem: dict) -> list[str]:
    relative = problem.get("path")
    if not isinstance(relative, str) or not relative.strip():
        return [f"{problem['id']}: statement path is missing"]
    path = ROOT / "units" / unit / relative
    if not path.is_file():
        return [f"{problem['id']}: statement path does not exist"]
    notebook = json.loads(path.read_text())
    markdown = [_source(cell) for cell in notebook["cells"] if cell["cell_type"] == "markdown"]
    errors: list[str] = []

    if not markdown:
        # Report it as a per-problem failure rather than dying on an index error, so the run
        # names the offending problem instead of just exiting (gate finding, plan 014).
        return [f"{problem['id']}: statement has no markdown cell"]

    all_markdown = "\n".join(markdown)

    # Header equality is checked for EVERY unit. It was scoped to REGISTER_UNITS until plan
    # 014, whose gate observed that a "343/343 passed" line covering three of sixteen units
    # reads as far stronger assurance than it was — and this plan's retag pass rests entirely
    # on headers agreeing with manifests.
    expected_title = f"# {unit} — Practice {problem['id'].split('-')[-1]}"
    # Leading and interleaved blank lines vary across tranches and carry no meaning, so compare
    # the first two non-empty lines rather than fixed indices.
    body = [line for line in markdown[0].splitlines() if line.strip()]
    if not body or body[0] != expected_title:
        errors.append("statement title does not match the manifest")
    elif len(body) < 2:
        errors.append("statement has no metadata header under its title")
    else:
        header_names = HEADER_NAME_RE.findall(body[1])
        fields = dict(HEADER_FIELD_RE.findall(body[1]))
        if header_names != ["Type", "Difficulty", "Concepts"]:
            errors.append("header fields must be exactly Type / Difficulty / Concepts")
        elif set(fields) != {"Type", "Difficulty", "Concepts"}:
            errors.append("header is missing one of Type / Difficulty / Concepts")
        else:
            # Concepts and difficulty are load-bearing and compared exactly — the retag pass
            # depends on headers agreeing with manifests. The Type field is prose that the
            # corpus writes either as the raw manifest id ("scenario") or as its expanded
            # label, sometimes with a parenthetical gloss, so it is matched by prefix.
            if fields["Concepts"] != ", ".join(problem["concepts"]):
                errors.append("header concepts do not match the manifest")
            if fields["Difficulty"] != problem["difficulty"]:
                errors.append("header difficulty does not match the manifest")
            type_label = TYPE_LABELS.get(problem["type"], problem["type"].replace("-", " "))
            if not _type_matches(fields["Type"], type_label, problem["type"]):
                errors.append("header type does not match the manifest")

    # The multiple-choice option-format checks stay scoped to the tranche-1 units that were
    # authored against that exact register; widening them is a separate, evidence-led change.
    if unit in REGISTER_UNITS and problem["type"].startswith("mc"):
        if unit in {"C11-neural-training", "C12-classical-models"}:
            if "Reasoning is required." not in all_markdown or (
                "Reasoning is not required." in all_markdown
            ):
                errors.append("MC reasoning flag must say 'Reasoning is required.'")
        elif not re.search(r"\bReasoning is (?:not )?required\.", all_markdown):
            errors.append("MC reasoning flag is missing")
        options = re.findall(r"(?m)^([A-E])\. ", all_markdown)
        legacy = re.search(r"(?m)^-\s+\*\*(?:\([A-E]\)|[A-E]\.)\*\*", all_markdown)
        if options != OPTION_LETTERS or legacy:
            errors.append("MC options are not exactly A.-through-E. in order")
        if (
            unit == "C12-classical-models"
            and problem["id"] == "C12-p05"
            and ("b > 0" not in all_markdown or "gcd(|a|, b) = 1" not in all_markdown)
        ):
            errors.append("normal-form MC must state b > 0 and gcd(|a|, b) = 1")

    minutes = problem.get("minutes")
    if minutes is not None:
        budgets = re.findall(r"(?m)^\*\*Time budget:\*\* ([1-9]\d*) minutes$", all_markdown)
        if budgets != [str(minutes)]:
            errors.append(f"time budget is missing or does not match manifest minutes {minutes}")
    elif unit == "C7-cnn-transfer":
        budgets = re.findall(r"(?m)^\*\*Time budget:\*\* ([1-9]\d*) minutes$", all_markdown)
        if problem["id"] in C7_BUDGET_REGISTER:
            literal_minutes = C7_BUDGET_REGISTER[problem["id"]]
            if budgets != [str(literal_minutes)]:
                errors.append(
                    "time budget is missing or does not match literal register minutes "
                    f"{literal_minutes}"
                )
        elif budgets:
            errors.append(
                "time budget is declared for an id absent from the literal register"
            )

    for match in BOLD_BAN_RE.finditer(all_markdown):
        if not ZERO_POINT_RE.search(match.group(1)):
            errors.append("bolded ban clause lacks a zero-point price")

    return [f"{problem['id']}: {error}" for error in errors]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--statements-only",
        action="store_true",
        help="validate statement/register contracts without requiring solutions",
    )
    args = parser.parse_args([] if argv is None else argv)
    checked = 0
    failures: list[str] = []
    units = UNITS or tuple(
        path.parent.name for path in sorted((ROOT / "units").glob("*/manifest.yaml"))
    )
    for unit in units:
        manifest_path = ROOT / "units" / unit / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        if unit == "C7-cnn-transfer":
            manifest_ids = [problem.get("id") for problem in manifest.get("practice", [])]
            for required_id in C7_BUDGET_REGISTER:
                count = manifest_ids.count(required_id)
                if count == 0:
                    failures.append(
                        "C7-budget-register: C7 budget register required id "
                        f"{required_id} is missing from manifest"
                    )
                elif count > 1:
                    failures.append(
                        "C7-budget-register: C7 budget register required id "
                        f"{required_id} occurs {count} times in manifest"
                    )
        for problem in manifest["practice"]:
            checked += 1
            failures.extend(_check_problem(unit, problem))
            if not args.statements_only:
                failures.extend(_check_solution_header(unit, problem))

    if failures:
        failed_ids = {item.split(":", 1)[0] for item in failures}
        print(
            f"register verification: {checked - len(failed_ids)}/{checked} passed "
            f"({checked} problems checked)"
        )
        for failure in failures:
            print(f"FAIL {failure}")
        return 1

    print(f"register verification: {checked}/{checked} passed ({checked} problems checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
