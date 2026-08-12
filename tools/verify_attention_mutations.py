"""Execute the five permanent attention mutants against real answer checks."""

from __future__ import annotations

import argparse
import ast
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError


@dataclass(frozen=True)
class MutationSpec:
    id: str
    notebook: str
    mutation_kind: str
    target_marker: str
    search: str
    replacement: str
    expected_failure_marker: str


@dataclass(frozen=True)
class MutationResult:
    mutation_id: str
    failure_cell: int


@dataclass(frozen=True)
class FailureObservation:
    cell: int
    error_name: str
    error_value: str


class MutationVerificationError(RuntimeError):
    """The mutation binding or observed notebook failure was not exact."""


MUTATIONS = [
    MutationSpec(
        id="b2-019-p06-remove-scaling",
        notebook="units/B2-019-attention-transformers/practice/p06_solution.ipynb",
        mutation_kind="remove-score-scaling",
        target_marker="scores = (q @ k.T) / np.sqrt(q.shape[1])",
        search="scores = (q @ k.T) / np.sqrt(q.shape[1])",
        replacement="scores = q @ k.T",
        expected_failure_marker="np.testing.assert_allclose(weights, EXPECTED_WEIGHTS",
    ),
    MutationSpec(
        id="b2-019-p08-post-softmax-mask",
        notebook="units/B2-019-attention-transformers/practice/p08_solution.ipynb",
        mutation_kind="move-mask-after-softmax",
        target_marker="masked_scores = scores + mask",
        search=(
            "masked_scores = scores + mask\n"
            "    shifted = masked_scores - np.max(masked_scores, axis=-1, keepdims=True)\n"
            "    numerators = np.exp(shifted)\n"
            "    weights = numerators / np.sum(numerators, axis=-1, keepdims=True)"
        ),
        replacement=(
            "shifted = scores - np.max(scores, axis=-1, keepdims=True)\n"
            "    numerators = np.exp(shifted)\n"
            "    weights = numerators / np.sum(numerators, axis=-1, keepdims=True)\n"
            "    weights = np.where(allowed, weights, 0.0)"
        ),
        expected_failure_marker="np.testing.assert_allclose(weights, EXPECTED_WEIGHTS",
    ),
    MutationSpec(
        id="b2-019-p10-wrong-concat-axis",
        notebook="units/B2-019-attention-transformers/practice/p10_solution.ipynb",
        mutation_kind="concatenate-heads-on-sequence-axis",
        target_marker="return heads.transpose(0, 2, 1, 3).reshape(b, n, h * d_h)",
        search="return heads.transpose(0, 2, 1, 3).reshape(b, n, h * d_h)",
        replacement="return heads.transpose(0, 2, 1, 3).reshape(b, n * h, d_h)",
        expected_failure_marker="assert recovered.shape == x.shape == (2, 3, 8)",
    ),
    MutationSpec(
        id="b2-019-p17-omit-position",
        notebook="units/B2-019-attention-transformers/practice/p17_solution.ipynb",
        mutation_kind="omit-positional-addition",
        target_marker="inputs = torch.tensor(X[:-1] + 0.1 * POSITIONAL",
        search=(
            "inputs = torch.tensor(X[:-1] + 0.1 * POSITIONAL, "
            "dtype=torch.float64).unsqueeze(0)"
        ),
        replacement="inputs = torch.tensor(X[:-1], dtype=torch.float64).unsqueeze(0)",
        expected_failure_marker="np.testing.assert_allclose(losses[[0, -1]]",
    ),
    MutationSpec(
        id="b2-019-p24-reverse-residual-layernorm",
        notebook="units/B2-019-attention-transformers/practice/p24_solution.ipynb",
        mutation_kind="reverse-residual-layernorm-order",
        target_marker="y = x + attention_output",
        search="y = x + attention_output",
        replacement="y = layer_norm_rows(x + attention_output)",
        expected_failure_marker="np.testing.assert_allclose(f[1, 2], EXPECTED_NORMALIZED_ROW",
    ),
]


def _code_sources(notebook: nbformat.NotebookNode) -> list[tuple[int, str]]:
    return [
        (index, str(cell.source))
        for index, cell in enumerate(notebook.cells)
        if cell.cell_type == "code"
    ]


def _require_one_source_match(
    sources: list[tuple[int, str]], needle: str, label: str, mutation_id: str
) -> int:
    count = sum(source.count(needle) for _, source in sources)
    if count != 1:
        raise MutationVerificationError(
            f"{mutation_id}: {label} matched {count} source locations"
        )
    return next(index for index, source in sources if needle in source)


def _execute_until_failure(
    notebook: nbformat.NotebookNode, execution_path: Path, timeout: int = 1200
) -> FailureObservation | None:
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name=notebook.metadata.get("kernelspec", {}).get("name", "python3"),
        resources={"metadata": {"path": str(execution_path)}},
        allow_errors=False,
        extra_arguments=["--log-level=ERROR"],
    )
    with client.setup_kernel():
        for cell_index, cell in enumerate(notebook.cells):
            try:
                client.execute_cell(cell, cell_index, execution_count=None)
            except CellExecutionError:
                errors = [
                    output
                    for output in cell.get("outputs", [])
                    if output.get("output_type") == "error"
                ]
                if len(errors) != 1:
                    raise MutationVerificationError(
                        f"cell {cell_index} produced {len(errors)} structured errors"
                    )
                return FailureObservation(
                    cell=cell_index,
                    error_name=str(errors[0].get("ename", "")),
                    error_value=str(errors[0].get("evalue", "")),
                )
            except Exception as exc:
                raise MutationVerificationError(
                    f"kernel execution failed unexpectedly at cell {cell_index}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    return None


def _bind_expected_check(source: str, marker: str, mutation_id: str) -> str:
    marker_line = source[: source.index(marker)].count("\n") + 1
    tree = ast.parse(source)
    statements = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.stmt)
        and node.lineno <= marker_line <= (node.end_lineno or node.lineno)
    ]
    innermost = [
        node
        for node in statements
        if not any(
            other is not node
            and other.lineno >= node.lineno
            and (other.end_lineno or other.lineno) <= (node.end_lineno or node.lineno)
            for other in statements
        )
    ]
    if len(innermost) != 1:
        raise MutationVerificationError(
            f"{mutation_id}: expected answer check did not bind to one statement"
        )
    statement = innermost[0]
    lines = source.splitlines(keepends=True)
    start = statement.lineno - 1
    end = statement.end_lineno or statement.lineno
    original = "".join(lines[start:end]).rstrip("\n")
    if original[: len(original) - len(original.lstrip())]:
        raise MutationVerificationError(
            f"{mutation_id}: expected answer check must be a top-level statement"
        )
    token = f"PLAN019_EXPECTED_CHECK::{mutation_id}"
    wrapped = (
        "class _Plan019ExpectedCheckFailure(AssertionError):\n"
        "    pass\n"
        "try:\n"
        + "\n".join(f"    {line}" for line in original.splitlines())
        + "\nexcept Exception as _plan019_check_error:\n"
        f"    raise _Plan019ExpectedCheckFailure({token!r}) from _plan019_check_error\n"
    )
    return "".join(lines[:start]) + wrapped + "".join(lines[end:])


def run_mutation(root: Path, spec: MutationSpec) -> MutationResult:
    root = Path(root).resolve()
    notebook_path = root / spec.notebook
    if not notebook_path.is_file():
        raise MutationVerificationError(
            f"{spec.id}: notebook does not exist: {spec.notebook}"
        )
    if spec.target_marker not in spec.search:
        raise MutationVerificationError(f"{spec.id}: target marker must be contained in search")

    notebook = nbformat.read(notebook_path, as_version=4)
    sources = _code_sources(notebook)
    search_cell = _require_one_source_match(sources, spec.search, "search", spec.id)
    target_cell = _require_one_source_match(
        sources, spec.target_marker, "target marker", spec.id
    )
    if target_cell != search_cell:
        raise MutationVerificationError(
            f"{spec.id}: target marker and search resolved to different code cells"
        )
    expected_cell = _require_one_source_match(
        sources, spec.expected_failure_marker, "expected failure marker", spec.id
    )
    source = str(notebook.cells[search_cell].source)
    notebook.cells[search_cell].source = source.replace(spec.search, spec.replacement, 1)
    expected_source = str(notebook.cells[expected_cell].source)
    notebook.cells[expected_cell].source = _bind_expected_check(
        expected_source, spec.expected_failure_marker, spec.id
    )

    with tempfile.TemporaryDirectory(prefix=f"usaaio-{spec.id}-") as temporary:
        copied_context = Path(temporary) / notebook_path.parent.name
        shutil.copytree(notebook_path.parent, copied_context)
        mutant_path = copied_context / notebook_path.name
        nbformat.write(notebook, mutant_path)
        mutant = nbformat.read(mutant_path, as_version=4)
        failure = _execute_until_failure(mutant, copied_context)

    if failure is None:
        raise MutationVerificationError(f"{spec.id}: mutant executed successfully")
    if failure.cell != expected_cell:
        raise MutationVerificationError(
            f"{spec.id}: failed at cell {failure.cell}; expected failure at cell {expected_cell}"
        )
    expected_value = f"PLAN019_EXPECTED_CHECK::{spec.id}"
    if (
        failure.error_name != "_Plan019ExpectedCheckFailure"
        or failure.error_value != expected_value
    ):
        raise MutationVerificationError(
            f"{spec.id}: did not fail through the registered answer check"
        )
    return MutationResult(spec.id, failure.cell)


def run_untouched(root: Path, spec: MutationSpec) -> None:
    root = Path(root).resolve()
    notebook_path = root / spec.notebook
    if not notebook_path.is_file():
        raise MutationVerificationError(
            f"{spec.id}: notebook does not exist: {spec.notebook}"
        )
    notebook = nbformat.read(notebook_path, as_version=4)
    with tempfile.TemporaryDirectory(prefix=f"usaaio-{spec.id}-untouched-") as temporary:
        copied_context = Path(temporary) / notebook_path.parent.name
        shutil.copytree(notebook_path.parent, copied_context)
        failure = _execute_until_failure(notebook, copied_context)
    if failure is not None:
        raise MutationVerificationError(
            f"{spec.id}: untouched notebook failed at cell {failure.cell}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        for spec in MUTATIONS:
            run_untouched(args.root, spec)
        results = [run_mutation(args.root, spec) for spec in MUTATIONS]
    except MutationVerificationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    for result, spec in zip(results, MUTATIONS, strict=True):
        print(f"PASS {result.mutation_id}: {spec.notebook} failed at cell {result.failure_cell}")
    print("PASS untouched attention notebooks: 5/5")
    print(f"attention mutation verification: {len(results)}/{len(MUTATIONS)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
