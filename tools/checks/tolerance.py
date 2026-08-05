from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path

import nbformat

from tools.model import Report

CALL_TOLERANCES = {
    "np.isclose": ("atol", "rtol"),
    "np.allclose": ("atol", "rtol"),
    "torch.isclose": ("atol", "rtol"),
    "torch.allclose": ("atol", "rtol"),
    "np.testing.assert_allclose": ("atol", "rtol"),
    "math.isclose": ("abs_tol", "rel_tol"),
}
EXEMPTION_RE = re.compile(r"#\s*tol-exempt:\s*(?P<reason>\S.*?)\s*$")


def _notebooks(root: Path) -> list[Path]:
    candidates = {
        *root.glob("units/*/practice/*.ipynb"),
        *root.glob("units/*/practice/*_solution.ipynb"),
        *root.glob("mocktests/*/solutions/*.ipynb"),
        *root.glob("mocktests/*/problems/*.ipynb"),
    }
    return sorted(candidates)


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        if prefix is not None:
            return f"{prefix}.{node.attr}"
    return None


def _exempt_lines(source: str) -> set[int]:
    exempt: set[int] = set()
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.COMMENT and EXEMPTION_RE.fullmatch(token.string):
            exempt.add(token.start[0])
    return exempt


def _cell_errors(path: Path, cell_number: int, source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        location = f":line {exc.lineno}" if exc.lineno is not None else ""
        return [f"{path}:cell {cell_number}{location}: cannot parse code: {exc.msg}"]

    exempt_lines = _exempt_lines(source)
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _dotted_name(node.func)
        required = CALL_TOLERANCES.get(name or "")
        if required is None or node.lineno in exempt_lines:
            continue
        keywords = {keyword.arg for keyword in node.keywords if keyword.arg is not None}
        missing = [keyword for keyword in required if keyword not in keywords]
        if missing:
            errors.append(
                f"{path}:cell {cell_number}:line {node.lineno}: {name} must explicitly "
                f"state {required[0]} and {required[1]} (missing {', '.join(missing)})"
            )
    return errors


def check_tolerance(root: str | Path) -> Report:
    paths = _notebooks(Path(root))
    if not paths:
        return Report(
            name="tolerance-check",
            ok=True,
            skipped="zero scannable notebooks exist repo-wide",
        )

    errors: list[str] = []
    for path in paths:
        validation_errors: dict[str, object] = {}
        try:
            notebook = nbformat.read(
                path,
                as_version=4,
                capture_validation_error=validation_errors,
            )
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{path}: cannot read notebook: {exc}")
            continue
        if validation_error := validation_errors.get("ValidationError"):
            errors.append(f"{path}: invalid notebook: {validation_error}")
            continue
        for cell_number, cell in enumerate(notebook.get("cells", []), start=1):
            if cell.get("cell_type") != "code":
                continue
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            errors.extend(_cell_errors(path, cell_number, str(source)))
    return Report(name="tolerance-check", ok=not errors, errors=errors)
