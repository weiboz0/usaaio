#!/usr/bin/env python3
"""Verify registered statement metadata and every bolded ban's pricing.

All unit manifests are authoritative for problem paths. Header agreement (title,
concepts, difficulty, type) and ban pricing are checked repo-wide; the stricter
multiple-choice option-format checks remain scoped to the tranche-1 units that
were authored against that exact register.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTER_UNITS = (
    "F1-scientific-python",
    "F2-vectors",
    "C1-ml-fundamentals",
)
# Tests may override this inventory; normal runs discover every unit manifest.
UNITS: tuple[str, ...] | None = None
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


def _check_problem(unit: str, problem: dict) -> list[str]:
    path = ROOT / "units" / unit / problem["path"]
    notebook = json.loads(path.read_text())
    markdown = [_source(cell) for cell in notebook["cells"] if cell["cell_type"] == "markdown"]
    errors: list[str] = []

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
        fields = dict(HEADER_FIELD_RE.findall(body[1]))
        if set(fields) != {"Type", "Difficulty", "Concepts"}:
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
            if not (
                fields["Type"].startswith(type_label)
                or fields["Type"].startswith(problem["type"])
            ):
                errors.append("header type does not match the manifest")

    # The multiple-choice option-format checks stay scoped to the tranche-1 units that were
    # authored against that exact register; widening them is a separate, evidence-led change.
    if unit in REGISTER_UNITS:
        if problem["type"].startswith("mc"):
            if not re.search(r"\bReasoning is (?:not )?required\.", all_markdown):
                errors.append("MC reasoning flag is missing")
            options = re.findall(r"(?m)^([A-E])\. ", all_markdown)
            legacy = re.search(
                r"(?m)^-\s+\*\*(?:\([A-E]\)|[A-E]\.)\*\*", all_markdown
            )
            if options != OPTION_LETTERS or legacy:
                errors.append("MC options are not exactly A.-through-E. in order")

    for match in BOLD_BAN_RE.finditer(all_markdown):
        if not ZERO_POINT_RE.search(match.group(1)):
            errors.append("bolded ban clause lacks a zero-point price")

    return [f"{problem['id']}: {error}" for error in errors]


def main() -> int:
    checked = 0
    failures: list[str] = []
    units = UNITS or tuple(
        path.parent.name for path in sorted((ROOT / "units").glob("*/manifest.yaml"))
    )
    for unit in units:
        manifest_path = ROOT / "units" / unit / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        for problem in manifest["practice"]:
            checked += 1
            failures.extend(_check_problem(unit, problem))

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
    raise SystemExit(main())
