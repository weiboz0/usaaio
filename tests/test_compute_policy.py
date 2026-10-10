"""Plan 029 Task 1: the Design 019 `optional-colab-l4` compute policy.

`optional-colab-l4` is accepted only with a local CPU solution path and an
`Accelerator extension` heading in the statement; `gpu-required` and unknown
policies stay rejected, and `cpu` behaviour is unchanged.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from tools.checks.layer_boundary import check_layer_boundary

ROOT = Path(__file__).resolve().parents[1]
UNIT_ID = "B2-023-generative-models-diffusion"
PROBLEM_ID = "B2-023-p06"
STATEMENT = "practice/p06.ipynb"
SOLUTION = "practice/p06_solution.ipynb"
IGNORE = shutil.ignore_patterns("build", "__pycache__", ".ipynb_checkpoints")


def _copied_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy2(ROOT / "books.yaml", repo / "books.yaml")
    shutil.copytree(ROOT / "book1", repo / "book1", ignore=IGNORE)
    shutil.copytree(ROOT / "book2", repo / "book2", ignore=IGNORE)
    return repo / "book2"


def _manifest_path(book2: Path) -> Path:
    return book2 / "units" / UNIT_ID / "manifest.yaml"


def _set_policy(book2: Path, policy: str) -> None:
    path = _manifest_path(book2)
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    problem = next(row for row in manifest["practice"] if row["id"] == PROBLEM_ID)
    problem["compute"]["policy"] = policy
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")


def _add_markdown(book2: Path, source: str) -> None:
    path = book2 / "units" / UNIT_ID / STATEMENT
    notebook = json.loads(path.read_text(encoding="utf-8"))
    notebook["cells"].append({"cell_type": "markdown", "metadata": {}, "source": source})
    path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")


def _add_extension_heading(book2: Path) -> None:
    _add_markdown(
        book2,
        "## Accelerator extension\n\nOn a Colab L4, rerun with the larger config dict.",
    )


def _remove_solution(book2: Path) -> None:
    (book2 / "units" / UNIT_ID / SOLUTION).unlink()


def _errors(book2: Path) -> list[str]:
    return check_layer_boundary(book2).errors


def _label(book2: Path) -> str:
    return f"{_manifest_path(book2).resolve()}: practice {PROBLEM_ID}"


def test_shipped_book2_cpu_policy_report_is_unchanged() -> None:
    report = check_layer_boundary(ROOT / "book2")
    assert report.ok, report.errors


def test_cpu_missing_solution_error_is_unchanged(tmp_path: Path) -> None:
    book2 = _copied_repo(tmp_path)
    _remove_solution(book2)
    errors = _errors(book2)
    assert errors == [f"{_label(book2)} cpu task requires a local solution path"]


def test_cpu_policy_ignores_accelerator_heading(tmp_path: Path) -> None:
    book2 = _copied_repo(tmp_path)
    _add_extension_heading(book2)
    assert _errors(book2) == []


def test_optional_colab_l4_with_solution_and_heading_is_accepted(tmp_path: Path) -> None:
    book2 = _copied_repo(tmp_path)
    _set_policy(book2, "optional-colab-l4")
    _add_extension_heading(book2)
    assert _errors(book2) == []


def test_optional_colab_l4_accepts_any_markdown_heading_level(tmp_path: Path) -> None:
    book2 = _copied_repo(tmp_path)
    _set_policy(book2, "optional-colab-l4")
    _add_markdown(book2, "Intro text.\n\n### Accelerator extension\n\nDetails.")
    assert _errors(book2) == []


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        pytest.param(
            lambda book2: None,
            "optional-colab-l4 task requires an 'Accelerator extension' statement heading",
            id="missing-heading",
        ),
        pytest.param(
            lambda book2: _add_markdown(book2, "Accelerator extension is optional."),
            "optional-colab-l4 task requires an 'Accelerator extension' statement heading",
            id="prose-not-heading",
        ),
        pytest.param(
            lambda book2: (_add_extension_heading(book2), _remove_solution(book2)),
            "optional-colab-l4 task requires a local solution path",
            id="missing-solution",
        ),
    ],
)
def test_optional_colab_l4_rejects_incomplete_contract(
    tmp_path: Path, mutate: Callable[[Path], Any], message: str
) -> None:
    book2 = _copied_repo(tmp_path)
    _set_policy(book2, "optional-colab-l4")
    mutate(book2)
    errors = _errors(book2)
    assert errors == [f"{_label(book2)} {message}"]


def test_optional_colab_l4_heading_must_be_in_markdown(tmp_path: Path) -> None:
    book2 = _copied_repo(tmp_path)
    _set_policy(book2, "optional-colab-l4")
    path = book2 / "units" / UNIT_ID / STATEMENT
    notebook = json.loads(path.read_text(encoding="utf-8"))
    notebook["cells"].append(
        {
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": "## Accelerator extension",
        }
    )
    path.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    message = "optional-colab-l4 task requires an 'Accelerator extension' statement heading"
    assert _errors(book2) == [f"{_label(book2)} {message}"]


@pytest.mark.parametrize("policy", ["gpu-required", "tpu", "optional-colab-a100"])
def test_gpu_required_and_unknown_policies_stay_rejected(tmp_path: Path, policy: str) -> None:
    book2 = _copied_repo(tmp_path)
    _set_policy(book2, policy)
    _add_extension_heading(book2)
    errors = _errors(book2)
    assert errors == [f"{_label(book2)} unsupported compute.policy {policy!r}"]
