import json
from pathlib import Path

import nbformat
import pytest

from tools.checks.tolerance import check_tolerance
from tools.cli import main


def write_notebook(root: Path, relative_path: str, source: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    notebook = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(source)])
    path.write_text(nbformat.writes(notebook))
    return path


@pytest.mark.parametrize(
    "call",
    [
        "np.isclose(left, right)",
        "np.allclose(left, right, atol=1e-9)",
        "np.testing.assert_allclose(left, right, rtol=0)",
        "torch.isclose(left, right)",
        "torch.allclose(left, right, atol=1e-9)",
        "math.isclose(left, right, abs_tol=1e-9)",
    ],
)
def test_tolerance_rejects_calls_missing_an_explicit_tolerance(tmp_path, call):
    write_notebook(tmp_path, "units/F1/practice/p01.ipynb", call)

    report = check_tolerance(tmp_path)

    assert not report.ok
    assert len(report.errors) == 1
    assert call.split("(", 1)[0] in report.errors[0]


@pytest.mark.parametrize(
    "call",
    [
        "np.isclose(left, right, atol=1e-9, rtol=0)",
        "np.allclose(left, right, rtol=0, atol=1e-9)",
        "np.testing.assert_allclose(left, right, atol=1e-9, rtol=0)",
        "torch.isclose(left, right, atol=1e-9, rtol=0)",
        "torch.allclose(left, right, atol=1e-9, rtol=0)",
        "math.isclose(left, right, abs_tol=1e-9, rel_tol=0)",
    ],
)
def test_tolerance_accepts_calls_with_both_explicit_tolerances(tmp_path, call):
    write_notebook(tmp_path, "units/F1/practice/p01_solution.ipynb", call)

    report = check_tolerance(tmp_path)

    assert report.ok
    assert report.errors == []


def test_tolerance_accepts_nonempty_exemption_on_call_line(tmp_path):
    write_notebook(
        tmp_path,
        "mocktests/r1-001/problems/p01.ipynb",
        "np.isclose(left, right)  # tol-exempt: library defaults are the exercise",
    )

    assert check_tolerance(tmp_path).ok


def test_tolerance_accepts_nonempty_exemption_on_any_multiline_call_line(tmp_path):
    write_notebook(
        tmp_path,
        "units/F1/practice/p01.ipynb",
        "np.isclose(\n"
        "    left,\n"
        "    right,  # tol-exempt: library defaults are the exercise\n"
        ")",
    )

    assert check_tolerance(tmp_path).ok


def test_tolerance_rejects_empty_exemption_reason(tmp_path):
    write_notebook(
        tmp_path,
        "mocktests/r1-001/solutions/p01.ipynb",
        "np.isclose(left, right)  # tol-exempt:   ",
    )

    report = check_tolerance(tmp_path)

    assert not report.ok
    assert len(report.errors) == 1


@pytest.mark.parametrize(
    ("relative_path", "expected_name"),
    [
        ("units/F1/lessons/01.ipynb", "np.isclose"),
        ("units/F1/review.ipynb", "np.isclose"),
        ("units/F1/lesson.ipynb", "np.isclose"),
    ],
)
def test_tolerance_scans_lesson_and_review_notebooks(
    tmp_path, relative_path, expected_name
):
    write_notebook(tmp_path, relative_path, "np.isclose(left, right)")

    report = check_tolerance(tmp_path)

    assert not report.ok
    assert expected_name in report.errors[0]


@pytest.mark.parametrize(
    ("source", "expected_name"),
    [
        (
            (
                "from numpy.testing import assert_allclose\n"
                "assert_allclose(left, right)"
            ),
            "np.testing.assert_allclose",
        ),
        (
            (
                "from numpy.testing import assert_allclose as assert_close\n"
                "assert_close(left, right)"
            ),
            "np.testing.assert_allclose",
        ),
        (
            ("import numpy.testing as npt\n" "npt.assert_allclose(left, right)"),
            "np.testing.assert_allclose",
        ),
        (
            (
                "import numpy as numpy_alias\n"
                "numpy_alias.testing.assert_allclose(left, right)"
            ),
            "np.testing.assert_allclose",
        ),
    ],
)
def test_tolerance_rejects_aliased_numpy_testing_calls(
    tmp_path, source, expected_name
):
    write_notebook(tmp_path, "units/F1/practice/p01.ipynb", source)

    report = check_tolerance(tmp_path)

    assert not report.ok
    assert expected_name in report.errors[0]


def test_tolerance_accepts_aliased_numpy_testing_call_with_tolerances(tmp_path):
    write_notebook(
        tmp_path,
        "units/F1/practice/p01.ipynb",
        "import numpy.testing as npt\n"
        "npt.assert_allclose(left, right, atol=1e-9, rtol=0)",
    )

    assert check_tolerance(tmp_path).ok


def test_tolerance_parse_failure_maps_to_exit_1(tmp_path, capsys):
    path = tmp_path / "units" / "F1" / "practice" / "p01.ipynb"
    path.parent.mkdir(parents=True)
    path.write_text("not a notebook")

    assert main(["--root", str(tmp_path), "tolerance-check"]) == 1
    assert "cannot read notebook" in capsys.readouterr().err


def test_tolerance_code_syntax_error_maps_to_exit_1(tmp_path, capsys):
    write_notebook(
        tmp_path,
        "units/F1/lessons/01.ipynb",
        "if True print('missing colon')",
    )

    assert main(["--root", str(tmp_path), "tolerance-check"]) == 1
    assert "cannot parse code" in capsys.readouterr().err


def test_tolerance_positional_tolerances_map_to_exit_1(tmp_path, capsys):
    write_notebook(
        tmp_path,
        "units/F1/lessons/01.ipynb",
        "np.allclose(left, right, 1e-9, 0)",
    )

    assert main(["--root", str(tmp_path), "tolerance-check"]) == 1
    assert "missing atol, rtol" in capsys.readouterr().err


def test_tolerance_schema_validation_failure_maps_to_exit_1(tmp_path, capsys):
    path = tmp_path / "units" / "F1" / "practice" / "p01.ipynb"
    path.parent.mkdir(parents=True)
    path.write_text(
        '{"cells":[{"cell_type":"code","metadata":{},"source":"",'
        '"outputs":[],"execution_count":"invalid","id":"cell-1"}],'
        '"metadata":{},"nbformat":4,"nbformat_minor":5}'
    )

    assert main(["--root", str(tmp_path), "tolerance-check"]) == 1
    assert "invalid notebook" in capsys.readouterr().err


def test_tolerance_zero_notebooks_maps_to_exit_3(tmp_path, capsys):
    assert main(["--root", str(tmp_path), "tolerance-check"]) == 3
    assert "SKIP tolerance-check" in capsys.readouterr().out


def test_scans_any_notebook_path_under_content_trees(tmp_path):
    """A notebook at a path no allowlist anticipated must still be guarded."""
    from tools.checks.tolerance import check_tolerance

    novel = tmp_path / "units" / "X1-unit" / "extras" / "supplement.ipynb"
    novel.parent.mkdir(parents=True)
    novel.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "metadata": {},
                        "source": ["import numpy as np\n", "np.isclose(1.0, 1.0)\n"],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
    )
    report = check_tolerance(tmp_path)
    assert not report.ok
    assert any("supplement.ipynb" in e for e in report.errors)


def test_build_artifacts_are_not_scanned(tmp_path):
    from tools.checks.tolerance import check_tolerance

    art = tmp_path / "mocktests" / "r1-001" / "build" / "rendered.ipynb"
    art.parent.mkdir(parents=True)
    art.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "metadata": {},
                        "source": ["import numpy as np\n", "np.isclose(1.0, 1.0)\n"],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        )
    )
    report = check_tolerance(tmp_path)
    assert report.skipped is not None or report.ok
