"""Execute permanent neural-training mutants and require the registered check to kill each.

Every mutation is a source-level corruption of a copied solution notebook. The original
notebook tree is read-only input: execution happens in a temporary copy of the notebook's
practice directory, so even notebooks that create local files cannot modify the corpus.
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
    """The mutation contract or the observed failure did not match the registry."""


MUTATIONS = [
    MutationSpec(
        id="c11-p16-delay-zero-grad",
        notebook="units/C11-neural-training/practice/p16_solution.ipynb",
        mutation_kind="delay-zero-grad-until-after-backward",
        target_marker="PLAN017_MUTATION_TARGET: C11-p16-zero-grad",
        search=(
            "        optimizer.zero_grad(set_to_none=True)  "
            "# PLAN017_MUTATION_TARGET: C11-p16-zero-grad\n"
            "        logits = model(X)\n"
            "        loss = criterion(logits, y)\n"
            "        losses[epoch] = loss.detach()\n"
            "        loss.backward()"
        ),
        replacement=(
            "        logits = model(X)\n"
            "        loss = criterion(logits, y)\n"
            "        losses[epoch] = loss.detach()\n"
            "        loss.backward()\n"
            "        optimizer.zero_grad(set_to_none=True)  "
            "# PLAN017_MUTATION_TARGET: C11-p16-zero-grad"
        ),
        expected_failure_marker="PLAN017_ANSWER_CHECK: C11-p16-training",
    ),
    MutationSpec(
        id="c11-p23-noop-optimizer-step",
        notebook="units/C11-neural-training/practice/p23_solution.ipynb",
        mutation_kind="replace-optimizer-step-with-no-op",
        target_marker="PLAN017_MUTATION_TARGET: C11-p23-optimizer-step",
        search=("        optimizer.step()  # PLAN017_MUTATION_TARGET: C11-p23-optimizer-step"),
        replacement=(
            "        pass  # optimizer step removed; "
            "PLAN017_MUTATION_TARGET: C11-p23-optimizer-step"
        ),
        expected_failure_marker="PLAN017_ANSWER_CHECK: C11-p23-training",
    ),
    MutationSpec(
        id="c7-p10-forbidden-frozen-update",
        notebook="units/C7-cnn-transfer/practice/p10_solution.ipynb",
        mutation_kind="enable-forbidden-frozen-parameter-update",
        target_marker="PLAN017_MUTATION_TARGET: C7-p10-frozen-update",
        search=(
            'frozen_prefixes = ("conv1", "bn1", "layer1", "layer2")  '
            "# PLAN017_MUTATION_TARGET: C7-p10-frozen-update"
        ),
        replacement=("frozen_prefixes = ()  # PLAN017_MUTATION_TARGET: C7-p10-frozen-update"),
        expected_failure_marker="PLAN017_ANSWER_CHECK: C7-p10-freezing",
    ),
    MutationSpec(
        id="c7-p27-move-committed-predictions",
        notebook="units/C7-cnn-transfer/practice/p27_solution.ipynb",
        mutation_kind="move-committed-predictions-below-verifier",
        target_marker="PLAN017_MUTATION_TARGET: C7-p27-committed-predictions",
        search=(
            "committed_predictions = [prediction_eval, prediction_frozen, "
            "prediction_inference]  # PLAN017_MUTATION_TARGET: "
            "C7-p27-committed-predictions"
        ),
        replacement=(
            "committed_predictions = [prediction_eval, prediction_frozen, "
            "prediction_inference]  # PLAN017_MUTATION_TARGET: "
            "C7-p27-committed-predictions"
        ),
        expected_failure_marker="PLAN017_VERIFIER: C7-p27-committed-predictions",
    ),
    MutationSpec(
        id="c7-p27-train-mode-buffer-audit",
        notebook="units/C7-cnn-transfer/practice/p27_solution.ipynb",
        mutation_kind="replace-eval-mode-with-train-mode-for-buffer-audit",
        target_marker="PLAN017_MUTATION_TARGET: C7-p27-eval-mode",
        search=("train_model.eval()  # PLAN017_MUTATION_TARGET: C7-p27-eval-mode"),
        replacement=("train_model.train()  # PLAN017_MUTATION_TARGET: C7-p27-eval-mode"),
        expected_failure_marker="PLAN017_ANSWER_CHECK: C7-p27-mode-buffer-audit",
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


def _apply_mutation(
    notebook: nbformat.NotebookNode,
    spec: MutationSpec,
    search_cell: int,
    expected_cell: int,
) -> None:
    source = str(notebook.cells[search_cell].source)
    if spec.mutation_kind != "move-committed-predictions-below-verifier":
        notebook.cells[search_cell].source = source.replace(spec.search, spec.replacement, 1)
        return

    # This mutation is intentionally a move, not a deletion: remove the committed answer at
    # its one registered source line, then insert the same line into the next code cell below
    # the verifier. Execution must therefore fail in the verifier before the value is defined.
    notebook.cells[search_cell].source = source.replace(spec.search, "", 1)
    destination = next(
        (
            index
            for index in range(expected_cell + 1, len(notebook.cells))
            if notebook.cells[index].cell_type == "code"
        ),
        None,
    )
    if destination is None:
        raise MutationVerificationError(
            f"{spec.id}: no code cell exists below registered verifier cell {expected_cell}"
        )
    notebook.cells[destination].source = f"{spec.replacement}\n" + str(
        notebook.cells[destination].source
    )


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

    notebook = nbformat.read(notebook_path, as_version=4)
    sources = _code_sources(notebook)
    _require_one_source_match(sources, spec.target_marker, "target marker", spec.id)
    search_cell = _require_one_source_match(sources, spec.search, "search", spec.id)
    expected_cell = _require_one_source_match(
        sources,
        spec.expected_failure_marker,
        "expected failure marker",
        spec.id,
    )
    _apply_mutation(notebook, spec, search_cell, expected_cell)

    with tempfile.TemporaryDirectory(prefix=f"usaaio-{spec.id}-") as temporary:
        temporary_path = Path(temporary)
        copied_context = temporary_path / notebook_path.parent.name
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
                f"PASS {result.mutation_id}: {spec.notebook} failed at cell {result.failure_cell}"
            )
    except MutationVerificationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    print(f"training mutation verification: {len(results)}/{len(MUTATIONS)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
