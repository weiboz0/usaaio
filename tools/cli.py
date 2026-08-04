"""usaaio-tools CLI.

Subcommand framework only; real implementations land with plan 004.
"""

import argparse
import sys

import tools

# name -> (help text, plan that implements it)
SUBCOMMANDS = {
    "blueprint-check": ("verify a mock test against mocktests/blueprint.yaml", "plan 004"),
    "overlap-scan": ("flag problems too similar to the reference corpus", "plan 004"),
    "prereq-check": ("verify the unit DAG and concept closure", "plan 004"),
    "coverage-check": ("verify every taught concept has a practice problem", "plan 004"),
    "hygiene-check": ("verify student notebooks contain no solutions or outputs", "plan 004"),
    "new-mocktest": ("scaffold a mock test from the blueprint", "plan 004"),
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="usaaio-tools")
    parser.add_argument("--version", action="version", version=f"usaaio-tools {tools.__version__}")
    sub = parser.add_subparsers(dest="command")
    for name, (help_text, _) in SUBCOMMANDS.items():
        sub.add_parser(name, help=help_text)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    plan = SUBCOMMANDS[args.command][1]
    print(f"usaaio-tools {args.command}: not implemented yet ({plan})", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
