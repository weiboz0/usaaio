"""usaaio-tools CLI."""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

import tools
from tools.checks.blueprint import check_blueprint
from tools.checks.coverage import check_coverage
from tools.checks.hygiene import check_hygiene
from tools.checks.new_mocktest import scaffold_mocktest
from tools.checks.overlap import check_overlap
from tools.checks.prereq import check_prereq
from tools.model import Report

CheckFn = Callable[[str | Path], Report]

SUBCOMMANDS: dict[str, tuple[str, CheckFn | None]] = {
    "blueprint-check": ("verify a mock test against mocktests/blueprint.yaml", check_blueprint),
    "overlap-scan": ("flag problems too similar to the reference corpus", check_overlap),
    "prereq-check": ("verify the unit DAG and concept closure", check_prereq),
    "coverage-check": ("verify every taught concept has a practice problem", check_coverage),
    "hygiene-check": ("verify student notebooks contain no solutions or outputs", check_hygiene),
    "new-mocktest": ("scaffold a mock test from the blueprint", None),
}


def print_report(report: Report) -> int:
    for warning in report.warnings:
        print(f"WARNING {report.name}: {warning}")
    if report.skipped:
        print(f"SKIP {report.name}: {report.skipped}")
    for error in report.errors:
        print(f"ERROR {report.name}: {error}", file=sys.stderr)
    if report.errors:
        print(f"FAIL {report.name}", file=sys.stderr)
        return 1
    if report.skipped:
        return 3
    print(f"PASS {report.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="usaaio-tools")
    parser.add_argument("--version", action="version", version=f"usaaio-tools {tools.__version__}")
    parser.add_argument("--root", default=".", help="repository root")
    sub = parser.add_subparsers(dest="command")
    for name, (help_text, fn) in SUBCOMMANDS.items():
        command_parser = sub.add_parser(name, help=help_text)
        if fn is None:
            command_parser.add_argument("test_id")
            command_parser.add_argument("--date", required=True)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "new-mocktest":
        try:
            path = scaffold_mocktest(args.root, args.test_id, args.date)
        except (FileExistsError, ValueError) as exc:
            print(f"ERROR new-mocktest: {exc}", file=sys.stderr)
            return 1
        print(f"created {path}")
        return 0

    check = SUBCOMMANDS[args.command][1]
    assert check is not None
    try:
        return print_report(check(args.root))
    except (ValueError, KeyError, OSError) as exc:
        # Loader/config failures (bad sentinel, invalid status, malformed manifest,
        # missing files) surface as check errors, not tracebacks; exit 1 still blocks.
        print(f"ERROR {args.command}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
