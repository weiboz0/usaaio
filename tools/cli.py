"""usaaio-tools CLI."""

import argparse
import sys
from collections.abc import Callable

import tools
from tools.books import load_book_catalog, validate_book_root
from tools.checks.answerkey import check_answerkey
from tools.checks.blueprint import check_blueprint
from tools.checks.coverage import check_coverage
from tools.checks.hygiene import check_hygiene
from tools.checks.layer_boundary import check_layer_boundary
from tools.checks.new_mocktest import scaffold_mocktest
from tools.checks.overlap import check_overlap
from tools.checks.prereq import check_prereq
from tools.checks.schedule import check_schedule
from tools.checks.scope import check_scope
from tools.checks.tolerance import check_tolerance
from tools.model import Report

CheckFn = Callable[..., Report]

SUBCOMMANDS: dict[str, tuple[str, CheckFn | None]] = {
    "answerkey-check": ("cross-check mock-test answer keys against solutions", check_answerkey),
    "blueprint-check": ("verify a mock test against mocktests/blueprint.yaml", check_blueprint),
    "overlap-scan": ("flag problems too similar to the reference corpus", check_overlap),
    "prereq-check": ("verify the unit DAG and concept closure", check_prereq),
    "coverage-check": ("verify every taught concept has at least three practice problems", check_coverage),
    "scope-check": ("verify the layered curriculum roadmap contract", check_scope),
    "schedule-check": (
        "verify the canonical 40-week allocation or selected book policy",
        check_schedule,
    ),
    "hygiene-check": ("verify student notebooks contain no solutions or outputs", check_hygiene),
    "layer-boundary-check": (
        "verify the Book 1 / Book 2 ownership and evidence boundary",
        check_layer_boundary,
    ),
    "tolerance-check": ("verify calls state absolute and relative tolerances", check_tolerance),
    "new-mocktest": ("scaffold a mock test from the blueprint", None),
}


def add_book_selection_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the future cutover's required, mutually exclusive book selection."""
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--book", metavar="BOOK_ID", help="select one registered book")
    selection.add_argument(
        "--all",
        action="store_true",
        dest="all_books",
        help="select all registered books in dependency order",
    )


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
    add_book_selection_arguments(parser)
    sub = parser.add_subparsers(dest="command")
    for name, (help_text, fn) in SUBCOMMANDS.items():
        command_parser = sub.add_parser(name, help=help_text)
        if fn is None:
            command_parser.add_argument("test_id")
            command_parser.add_argument("--date", required=True)

    arguments = sys.argv[1:] if argv is None else argv
    if not arguments:
        parser.print_help()
        return 0
    args = parser.parse_args(arguments)
    if args.command is None:
        parser.print_help()
        return 0

    try:
        catalog = load_book_catalog(args.root)
    except (ValueError, OSError) as exc:
        print(f"ERROR book-selection: {exc}", file=sys.stderr)
        return 1
    if args.all_books:
        selected = list(catalog.books)
    else:
        try:
            selected = [catalog.by_id(args.book)]
        except KeyError as exc:
            print(f"ERROR book-selection: {exc}", file=sys.stderr)
            return 1
    if args.command == "new-mocktest":
        if args.all_books:
            print("ERROR new-mocktest: --all is not supported", file=sys.stderr)
            return 1
        try:
            structural_errors = validate_book_root(selected[0])
            if structural_errors:
                for error in structural_errors:
                    print(f"ERROR {selected[0].id}: {error}", file=sys.stderr)
                return 1
            path = scaffold_mocktest(
                selected[0].root,
                args.test_id,
                args.date,
                book_number=selected[0].number,
            )
        except (FileExistsError, ValueError) as exc:
            print(f"ERROR new-mocktest: {exc}", file=sys.stderr)
            return 1
        print(f"created {path}")
        return 0

    check = SUBCOMMANDS[args.command][1]
    assert check is not None
    exit_code = 0
    for book in selected:
        try:
            structural_errors = validate_book_root(book)
            if structural_errors:
                for error in structural_errors:
                    print(f"ERROR {book.id}: {error}", file=sys.stderr)
                exit_code = 1
                continue
            if args.command in {"answerkey-check", "overlap-scan"}:
                report = check(book.root, book_number=book.number)
            elif args.command == "schedule-check":
                report = check(book.root, book_spec=book)
            else:
                report = check(book.root)
            if len(selected) > 1:
                report.name = f"{book.id}:{report.name}"
            exit_code = max(exit_code, print_report(report))
        except (ValueError, KeyError, OSError) as exc:
            # One malformed book must not suppress diagnostics for later --all books.
            print(f"ERROR {book.id}:{args.command}: {exc}", file=sys.stderr)
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
