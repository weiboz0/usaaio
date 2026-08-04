from __future__ import annotations

from pathlib import Path

import nbformat

from tools.model import Report

LEAK_MARKERS = ("# SOLUTION", "answer_key")


def _student_notebooks(root: Path) -> list[Path]:
    candidates = [
        *root.glob("mocktests/*/problems/*.ipynb"),
        *root.glob("units/*/practice/*.ipynb"),
    ]
    return sorted(path for path in candidates if "solution" not in path.name)


def check_hygiene(root: str | Path) -> Report:
    root = Path(root)
    errors: list[str] = []
    for path in _student_notebooks(root):
        try:
            notebook = nbformat.reads(path.read_text(), as_version=4)
        except ValueError as exc:  # NotJSONError and validation errors subclass ValueError
            errors.append(f"{path}: invalid notebook: {exc}")
            continue
        for index, cell in enumerate(notebook.get("cells", []), start=1):
            if cell.get("outputs") not in (None, []):
                errors.append(f"{path}: cell {index} has executed outputs")
            if cell.get("execution_count") is not None:
                errors.append(f"{path}: cell {index} has execution_count")
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            tags = set(cell.get("metadata", {}).get("tags", []))
            if any(marker in source for marker in LEAK_MARKERS) or "solution" in tags:
                errors.append(f"{path}: cell {index} contains solution marker")
    return Report(name="hygiene-check", ok=not errors, errors=errors)
