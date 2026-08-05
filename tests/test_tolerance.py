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


def test_tolerance_rejects_empty_exemption_reason(tmp_path):
    write_notebook(
        tmp_path,
        "mocktests/r1-001/solutions/p01.ipynb",
        "np.isclose(left, right)  # tol-exempt:   ",
    )

    report = check_tolerance(tmp_path)

    assert not report.ok
    assert len(report.errors) == 1


def test_tolerance_parse_failure_maps_to_exit_1(tmp_path, capsys):
    path = tmp_path / "units" / "F1" / "practice" / "p01.ipynb"
    path.parent.mkdir(parents=True)
    path.write_text("not a notebook")

    assert main(["--root", str(tmp_path), "tolerance-check"]) == 1
    assert "cannot read notebook" in capsys.readouterr().err


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
