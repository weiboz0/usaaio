import subprocess
import sys

import tools
from tools.cli import SUBCOMMANDS, main


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "tools.cli", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_version_flag():
    proc = run_cli("--version")
    assert proc.returncode == 0
    assert tools.__version__ in proc.stdout


def test_help_lists_planned_subcommands():
    proc = run_cli("--help")
    assert proc.returncode == 0
    for name in SUBCOMMANDS:
        assert name in proc.stdout


def test_check_subcommand_runs():
    proc = run_cli("--book", "book1", "prereq-check")
    assert proc.returncode == 0
    assert "PASS prereq-check" in proc.stdout


def test_main_no_subcommand_prints_help(capsys):
    assert main([]) == 0
    assert "usage: usaaio-tools" in capsys.readouterr().out


def test_main_check_subcommand_in_process(capsys):
    assert main(["--book", "book1", "prereq-check"]) == 0
    assert "PASS prereq-check" in capsys.readouterr().out


def test_schedule_help_describes_the_canonical_40_week_allocation():
    proc = run_cli("--help")

    assert proc.returncode == 0
    assert "verify the canonical 40-week allocation" in proc.stdout
    assert "canonical 35-week allocation" not in proc.stdout
