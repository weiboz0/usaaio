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


def test_unimplemented_subcommand_exits_2():
    proc = run_cli("blueprint-check")
    assert proc.returncode == 2
    assert "plan 004" in proc.stderr


def test_main_no_subcommand_prints_help(capsys):
    assert main([]) == 0
    assert "usage: usaaio-tools" in capsys.readouterr().out


def test_main_unimplemented_subcommand_in_process(capsys):
    assert main(["blueprint-check"]) == 2
    assert "plan 004" in capsys.readouterr().err
