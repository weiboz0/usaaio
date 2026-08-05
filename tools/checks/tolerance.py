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
MODULE_NAMES = {
    "math": "math",
    "numpy": "np",
    "np": "np",
    "torch": "torch",
}


def _notebooks(root: Path) -> list[Path]:
    candidates = {
        *root.glob("units/*/practice/*.ipynb"),
        *root.glob("units/*/practice/*_solution.ipynb"),
        *root.glob("units/*/lessons/*.ipynb"),
        *root.glob("units/*/review.ipynb"),
        *root.glob("units/*/lesson.ipynb"),
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


def _canonical_module(name: str) -> str | None:
    root, *rest = name.split(".")
    canonical_root = MODULE_NAMES.get(root)
    if canonical_root is None:
        return None
    return ".".join([canonical_root, *rest])


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                canonical = _canonical_module(imported.name)
                if canonical is None:
                    continue
                if imported.asname:
                    aliases[imported.asname] = canonical
                else:
                    local_name = imported.name.split(".", 1)[0]
                    aliases[local_name] = canonical.split(".", 1)[0]
        elif isinstance(node, ast.ImportFrom) and node.module:
            canonical_module = _canonical_module(node.module)
            if canonical_module is None:
                continue
            for imported in node.names:
                if imported.name == "*":
                    continue
                local_name = imported.asname or imported.name
                aliases[local_name] = f"{canonical_module}.{imported.name}"
    return aliases


def _resolved_name(node: ast.expr, aliases: dict[str, str]) -> str | None:
    name = _dotted_name(node)
    if name is None:
        return None
    root, *rest = name.split(".")
    canonical_root = aliases.get(root, MODULE_NAMES.get(root, root))
    return ".".join([canonical_root, *rest])


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
    aliases = _import_aliases(tree)
    errors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _resolved_name(node.func, aliases)
        required = CALL_TOLERANCES.get(name or "")
        last_line = node.end_lineno or node.lineno
        exempt = any(node.lineno <= line <= last_line for line in exempt_lines)
        if required is None or exempt:
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
