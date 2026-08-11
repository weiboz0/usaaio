"""Statically cross-check mock-test answer keys against solution artifacts.

Every direct manifest key must exactly match its ``answers.md`` marker after
whitespace normalization.  The tagged-cell leg applies only to direct numeric keys
whose problem ``files`` name a student notebook with a solution-notebook counterpart;
theory-only problems under ``theory/`` therefore use the universal marker leg alone.
Pointer keys retain their explicit tagged-cell comparison.  Together with solution
execution, this realizes the plan's three-way rule without requiring nonexistent
theory cells.  Prose-string notebook answers remain bound to computation by their
executed in-cell assertions.

Tagged solution cells are never executed here.  The parser walks Python's AST and
uses the last simple ``ANSWER = <literal>`` assignment in the tagged cell.  Accepted
literals are plain ``int``, ``float``, and ``str`` values (including signed numeric
literals); booleans, containers, names, calls, attributes, and expressions are rejected.
"""

from __future__ import annotations

import ast
import math
import re
from pathlib import Path

import nbformat

from tools.model import ManifestProblem, MockManifest, Report, load_mock_manifests

MARKER_RE = re.compile(r"^- (?P<id>\S+): answer: (?P<answer>.+?)\s*$")
POINTER_RE = re.compile(r"^solutions/(?P<file>[^#]+\.ipynb)#(?P<tag>[^#]+)$")
Numeric = int | float


def _is_numeric(value: object) -> bool:
    return type(value) in (int, float)


def _literal(node: ast.expr) -> int | float | str:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float, str):
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.UAdd, ast.USub))
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) in (int, float)
    ):
        value = ast.literal_eval(node)
        assert type(value) in (int, float)
        return value
    raise ValueError("ANSWER must be a plain int, float, or str literal")


def _answer_literal(source: str) -> int | float | str:
    tree = ast.parse(source)
    assignments = [
        statement.value
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "ANSWER"
    ]
    if not assignments:
        raise ValueError("tagged cell has no simple ANSWER = <literal> assignment")
    return _literal(assignments[-1])


def _markers(path: Path) -> tuple[dict[str, str], list[str]]:
    if not path.exists():
        return {}, [f"{path}: missing answers.md"]
    markers: dict[str, str] = {}
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        match = MARKER_RE.fullmatch(line)
        if match is None:
            continue
        problem_id = match.group("id")
        if problem_id in markers:
            errors.append(f"{path}:{line_number}: duplicate answer marker for {problem_id}")
        else:
            markers[problem_id] = match.group("answer")
    return markers, errors


def _tagged_literal(paths: list[Path], tag: str) -> tuple[int | float | str | None, list[str]]:
    matches: list[tuple[Path, int, str]] = []
    errors: list[str] = []
    for path in paths:
        try:
            notebook = nbformat.read(path, as_version=4)
        except (OSError, ValueError) as exc:
            errors.append(f"{path}: cannot read notebook: {exc}")
            continue
        for index, cell in enumerate(notebook.cells, start=1):
            if tag in cell.get("metadata", {}).get("tags", []):
                matches.append((path, index, str(cell.get("source", ""))))
    if not matches:
        return None, [*errors, f"no solution cell tagged {tag}"]
    if len(matches) > 1:
        locations = ", ".join(f"{path}:cell {index}" for path, index, _ in matches)
        return None, [*errors, f"multiple solution cells tagged {tag}: {locations}"]
    path, index, source = matches[0]
    try:
        return _answer_literal(source), errors
    except (SyntaxError, ValueError) as exc:
        return None, [*errors, f"{path}:cell {index}: {exc}"]


def _marker_literal(text: str) -> int | float | str:
    try:
        return _literal(ast.parse(text, mode="eval").body)
    except (SyntaxError, ValueError):
        return text


def _tolerance(problem: ManifestProblem) -> float:
    if problem.answer_tolerance is not None:
        return problem.answer_tolerance
    return 0.0 if type(problem.answer_key) is int else 1e-9


def _numeric_equal(left: Numeric, right: Numeric, tolerance: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def _normalized_text(value: object) -> str:
    return " ".join(str(value).split())


def _solution_notebook_counterparts(
    problem: ManifestProblem, solutions: Path
) -> list[Path]:
    counterparts: list[Path] = []
    for rel in problem.files:
        student_path = Path(rel)
        if student_path.suffix != ".ipynb":
            continue
        candidates = (
            solutions / f"{student_path.stem}_solution.ipynb",
            solutions / student_path.name,
        )
        counterpart = next((path for path in candidates if path.exists()), None)
        if counterpart is not None and counterpart not in counterparts:
            counterparts.append(counterpart)
    return counterparts


def _check_direct_key(
    problem: ManifestProblem,
    marker: str,
    notebooks: list[Path],
) -> list[str]:
    expected = problem.answer_key
    errors: list[str] = []
    if _normalized_text(marker) != _normalized_text(expected):
        errors.append(f"{problem.id}: answers.md has {marker!r}, expected {expected!r}")
    if not _is_numeric(expected) or not notebooks:
        return errors

    tolerance = _tolerance(problem)
    cell_value, cell_errors = _tagged_literal(notebooks, f"answer:{problem.id}")
    errors.extend(f"{problem.id}: {error}" for error in cell_errors)
    if cell_value is not None and (
        not _is_numeric(cell_value) or not _numeric_equal(expected, cell_value, tolerance)
    ):
        errors.append(
            f"{problem.id}: tagged ANSWER is {cell_value!r}, expected {expected!r} "
            f"within atol={tolerance}"
        )
    return errors


def _check_pointer(
    problem: ManifestProblem,
    marker: str,
    solutions: Path,
    pointer: re.Match[str],
) -> list[str]:
    path = solutions / pointer.group("file")
    value, errors = _tagged_literal([path], pointer.group("tag"))
    prefixed = [f"{problem.id}: {error}" for error in errors]
    if value is not None and _marker_literal(marker) != value:
        prefixed.append(
            f"{problem.id}: answers.md has {marker!r}, tagged ANSWER is {value!r}"
        )
    return prefixed


def _check_manifest(manifest: MockManifest) -> list[str]:
    solutions = manifest.path.parent / "solutions"
    answers = solutions / "answers.md"
    markers, errors = _markers(answers)
    for problem in manifest.problems:
        if problem.answer_key is None:
            continue
        marker = markers.get(problem.id)
        if marker is None:
            errors.append(f"{answers}: missing answer marker for {problem.id}")
            continue
        pointer = POINTER_RE.fullmatch(problem.answer_key) if isinstance(problem.answer_key, str) else None
        if pointer is not None:
            errors.extend(_check_pointer(problem, marker, solutions, pointer))
        else:
            notebooks = _solution_notebook_counterparts(problem, solutions)
            errors.extend(_check_direct_key(problem, marker, notebooks))
    return errors


def check_answerkey(
    root: str | Path, *, book_number: int | None = None
) -> Report:
    """Check final mock manifests; drafts do not affect pass/fail results."""

    manifests = load_mock_manifests(root, book_number=book_number)
    finals = [manifest for manifest in manifests if manifest.status == "final"]
    if not finals:
        return Report(
            name="answerkey-check",
            ok=True,
            skipped="no final mocktest manifests exist (drafts are not checked)",
        )
    errors = [error for manifest in finals for error in _check_manifest(manifest)]
    return Report(name="answerkey-check", ok=not errors, errors=errors)
