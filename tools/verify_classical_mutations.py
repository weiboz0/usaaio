"""Execute permanent classical-model mutants and require answer checks to kill them.

Each registered source corruption is applied to a copied solution notebook. The original
practice tree remains read-only input, and the runner fails closed unless the source target
and expected rejecting check each resolve exactly once.
"""

from __future__ import annotations

import argparse
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


class MutationVerificationError(RuntimeError):
    """The mutation contract or observed notebook failure was not exact."""


MUTATIONS = [
    MutationSpec(
        id="c12-p07-logistic-mean-factor",
        notebook="units/C12-classical-models/practice/p07_solution.ipynb",
        mutation_kind="remove-logistic-mean-factor",
        target_marker="PLAN018_MUTATION_TARGET: C12-p07-logistic-mean-factor",
        search=(
            "        # PLAN018_MUTATION_TARGET: C12-p07-logistic-mean-factor\n"
            "        grad_w = X.T @ (probabilities - y) / X.shape[0]"
        ),
        replacement=(
            "        # PLAN018_MUTATION_TARGET: C12-p07-logistic-mean-factor\n"
            "        grad_w = X.T @ (probabilities - y)"
        ),
        expected_failure_marker="PLAN018_ANSWER_CHECK: C12-p07-logistic-training",
    ),
    MutationSpec(
        id="c12-p08-signed-hinge-branch",
        notebook="units/C12-classical-models/practice/p08_solution.ipynb",
        mutation_kind="reverse-signed-hinge-branch",
        target_marker="PLAN018_MUTATION_TARGET: C12-p08-signed-hinge-branch",
        search=(
            "    # PLAN018_MUTATION_TARGET: C12-p08-signed-hinge-branch\n"
            "    margins = t * (X @ w + float(b))"
        ),
        replacement=(
            "    # PLAN018_MUTATION_TARGET: C12-p08-signed-hinge-branch\n"
            "    margins = -t * (X @ w + float(b))"
        ),
        expected_failure_marker="PLAN018_ANSWER_CHECK: C12-p08-hinge-subgradient",
    ),
    MutationSpec(
        id="c12-p10-maximum-impurity-split",
        notebook="units/C12-classical-models/practice/p10_solution.ipynb",
        mutation_kind="select-maximum-impurity-split",
        target_marker="PLAN018_MUTATION_TARGET: C12-p10-best-split",
        search=(
            "    # PLAN018_MUTATION_TARGET: C12-p10-best-split\n"
            "    weighted, feature, threshold, gain = min(candidates, key=lambda item: item[:3])"
        ),
        replacement=(
            "    # PLAN018_MUTATION_TARGET: C12-p10-best-split\n"
            "    weighted, feature, threshold, gain = max(candidates, key=lambda item: item[:3])"
        ),
        expected_failure_marker="PLAN018_ANSWER_CHECK: C12-p10-best-split",
    ),
    MutationSpec(
        id="c12-p29-missing-adaboost-weight-update",
        notebook="units/C12-classical-models/practice/p29_solution.ipynb",
        mutation_kind="remove-adaboost-weight-update",
        target_marker="PLAN018_MUTATION_TARGET: C12-p29-weight-update",
        search=(
            "    # PLAN018_MUTATION_TARGET: C12-p29-weight-update\n"
            "    q2=unnormalized_q2/Z1"
        ),
        replacement=(
            "    # PLAN018_MUTATION_TARGET: C12-p29-weight-update\n"
            "    q2=q1.copy()"
        ),
        expected_failure_marker="PLAN018_ANSWER_CHECK: C12-p29-adaboost-ledger",
    ),
    MutationSpec(
        id="c12-p13-non-centroid-lloyd-update",
        notebook="units/C12-classical-models/practice/p13_solution.ipynb",
        mutation_kind="replace-centroid-with-non-centroid-update",
        target_marker="PLAN018_MUTATION_TARGET: C12-p13-centroid-update",
        search=(
            "        # PLAN018_MUTATION_TARGET: C12-p13-centroid-update\n"
            "        updated = np.vstack([X[labels == cluster].mean(axis=0) "
            "for cluster in range(k)]).astype(np.float64)"
        ),
        replacement=(
            "        # PLAN018_MUTATION_TARGET: C12-p13-centroid-update\n"
            "        updated = np.vstack([X[labels == cluster].sum(axis=0) "
            "for cluster in range(k)]).astype(np.float64)"
        ),
        expected_failure_marker="PLAN018_ANSWER_CHECK: C12-p13-lloyd-update",
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
        raise MutationVerificationError(f"{mutation_id}: {label} matched {count} source locations")
    return next(index for index, source in sources if needle in source)


def _execute_until_failure(
    notebook: nbformat.NotebookNode, execution_path: Path, timeout: int = 1200
) -> int | None:
    kernel_name = notebook.metadata.get("kernelspec", {}).get("name", "python3")
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name=kernel_name,
        resources={"metadata": {"path": str(execution_path)}},
        allow_errors=False,
        extra_arguments=["--log-level=ERROR"],
    )
    with client.setup_kernel():
        for cell_index, cell in enumerate(notebook.cells):
            try:
                client.execute_cell(cell, cell_index, execution_count=None)
            except CellExecutionError:
                return cell_index
            except Exception as exc:
                raise MutationVerificationError(
                    f"kernel execution failed unexpectedly at cell {cell_index}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    return None


def run_mutation(root: Path, spec: MutationSpec) -> MutationResult:
    root = Path(root).resolve()
    notebook_path = root / spec.notebook
    if not notebook_path.is_file():
        raise MutationVerificationError(f"{spec.id}: notebook does not exist: {spec.notebook}")
    if spec.target_marker not in spec.search:
        raise MutationVerificationError(f"{spec.id}: target marker must be contained in search")

    notebook = nbformat.read(notebook_path, as_version=4)
    sources = _code_sources(notebook)
    search_cell = _require_one_source_match(sources, spec.search, "search", spec.id)
    target_cell = _require_one_source_match(sources, spec.target_marker, "target marker", spec.id)
    if target_cell != search_cell:
        raise MutationVerificationError(
            f"{spec.id}: target marker and search resolved to different code cells"
        )
    source = str(notebook.cells[search_cell].source)
    search_start = source.index(spec.search)
    marker_start = source.index(spec.target_marker)
    if not search_start <= marker_start < search_start + len(spec.search):
        raise MutationVerificationError(
            f"{spec.id}: target marker is not bound to the registered search occurrence"
        )
    expected_cell = _require_one_source_match(
        sources,
        spec.expected_failure_marker,
        "expected failure marker",
        spec.id,
    )
    notebook.cells[search_cell].source = source.replace(spec.search, spec.replacement, 1)

    with tempfile.TemporaryDirectory(prefix=f"usaaio-{spec.id}-") as temporary:
        copied_context = Path(temporary) / notebook_path.parent.name
        shutil.copytree(notebook_path.parent, copied_context)
        mutant_path = copied_context / notebook_path.name
        nbformat.write(notebook, mutant_path)
        mutant = nbformat.read(mutant_path, as_version=4)
        failure_cell = _execute_until_failure(mutant, copied_context)

    if failure_cell is None:
        raise MutationVerificationError(f"{spec.id}: mutant executed successfully")
    if failure_cell != expected_cell:
        raise MutationVerificationError(
            f"{spec.id}: failed at cell {failure_cell}; expected failure at cell {expected_cell}"
        )
    return MutationResult(mutation_id=spec.id, failure_cell=failure_cell)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    results: list[MutationResult] = []
    try:
        for spec in MUTATIONS:
            result = run_mutation(args.root, spec)
            results.append(result)
            print(
                f"PASS {result.mutation_id}: {spec.notebook} failed at cell "
                f"{result.failure_cell}"
            )
    except MutationVerificationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    print(f"classical mutation verification: {len(results)}/{len(MUTATIONS)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
