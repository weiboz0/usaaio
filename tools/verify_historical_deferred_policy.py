"""Verify deferred-solution policy in an archived checkout at an explicit date."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from tools.model import load_unit_manifests


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{value!r}: expected ISO date YYYY-MM-DD") from exc


def verify(root: Path, as_of_date: date) -> None:
    load_unit_manifests(root, as_of_date=as_of_date)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--as-of-date", required=True)
    args = parser.parse_args()
    try:
        policy_date = parse_iso_date(args.as_of_date)
    except ValueError as exc:
        parser.error(str(exc))
    verify(args.root, policy_date)
    print(f"PASS deferred-policy verification at {policy_date.isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
