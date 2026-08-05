#!/usr/bin/env python3
"""Verify the Plan 013 Task 2/A3 register on the 65 tranche-1 statements.

The three unit manifests are authoritative for problem paths and header data.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
UNITS = (
    "F1-scientific-python",
    "F2-vectors",
    "C1-ml-fundamentals",
)
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

    expected_title = f"# {unit} — Practice {problem['id'].split('-')[-1]}"
    top_lines = markdown[0].splitlines()
    expected_top = [expected_title, "", _expected_header(problem)]
    if top_lines[:3] != expected_top:
        errors.append("header does not match the manifest at the statement top")

    all_markdown = "\n".join(markdown)
    if problem["type"].startswith("mc"):
        if not re.search(r"\bReasoning is (?:not )?required\.", all_markdown):
            errors.append("MC reasoning flag is missing")
        options = re.findall(r"(?m)^([A-E])\. ", all_markdown)
        legacy = re.search(r"(?m)^-\s+\*\*(?:\([A-E]\)|[A-E]\.)\*\*", all_markdown)
        if options != OPTION_LETTERS or legacy:
            errors.append("MC options are not exactly A.-through-E. in order")

    if "constrained" in problem["type"] and not re.search(
        r"\*\*Banned \(zero points\):.+?\*\*", all_markdown, re.DOTALL
    ):
        errors.append("constrained item lacks a Banned (zero points) clause")

    return [f"{problem['id']}: {error}" for error in errors]


def main() -> int:
    checked = 0
    failures: list[str] = []
    for unit in UNITS:
        manifest_path = ROOT / "units" / unit / "manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text())
        for problem in manifest["practice"]:
            checked += 1
            failures.extend(_check_problem(unit, problem))

    if checked != 65:
        failures.append(f"inventory: expected 65 statements, found {checked}")
    if failures:
        failed_ids = {item.split(":", 1)[0] for item in failures}
        print(f"register verification: {checked - len(failed_ids)}/{checked} passed")
        for failure in failures:
            print(f"FAIL {failure}")
        return 1

    print(f"register verification: {checked}/{checked} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
