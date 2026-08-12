#!/usr/bin/env bash
# Collision and public-repository safety guard for legacy and two-book layouts.
set -euo pipefail
cd "$(dirname "$0")/.."

mode=${1:-}
base=
if [[ -n "$mode" && "$mode" != --pr ]]; then
  echo "usage: pre-merge-guard.sh [--pr]   (unknown argument: $mode)" >&2
  exit 2
fi
if [[ "$mode" == --pr ]]; then
  if ! git fetch -q origin main 2>/dev/null; then
    echo "FAIL: origin/main fetch unavailable; --pr union is unverified" >&2
    exit 1
  fi
  if ! base=$(git merge-base HEAD origin/main 2>/dev/null); then
    echo "FAIL: origin/main merge-base unavailable; --pr union is unverified" >&2
    exit 1
  fi
fi

scope_verifier=scripts/verify-staged-scope.py
scope_inventory=tests/fixtures/plan019-path-inventory.yaml
require_enforcement_file() {
  local path=$1 expected_mode=$2 expected_sha256=$3
  local actual_sha256 index_entry index_mode index_sha256
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "FAIL: enforcement file must be a regular non-symlink file: $path" >&2
    exit 1
  fi
  actual_sha256=$(sha256sum "$path" | awk '{print $1}')
  if [[ $actual_sha256 != "$expected_sha256" ]]; then
    echo "FAIL: enforcement file integrity mismatch: $path" >&2
    exit 1
  fi
  index_entry=$(git ls-files -s -- "$path")
  if [[ -z $index_entry ]]; then
    echo "FAIL: enforcement file missing from prospective index: $path" >&2
    exit 1
  fi
  index_mode=${index_entry%% *}
  if [[ $index_mode != "$expected_mode" ]]; then
    echo "FAIL: enforcement file is not a regular file in prospective index: $path " \
      "(mode=$index_mode expected=$expected_mode)" >&2
    exit 1
  fi
  index_sha256=$(git show ":$path" | sha256sum | awk '{print $1}')
  if [[ $index_sha256 != "$expected_sha256" ]]; then
    echo "FAIL: enforcement file prospective-index integrity mismatch: $path" >&2
    exit 1
  fi
}
require_enforcement_file "$scope_verifier" \
  100755 \
  6e8819d2ae6ac5fe5f81aaf43a4a38d6fbf79ac18c394d429a7e59fe27f2f17a
require_enforcement_file "$scope_inventory" \
  100644 \
  9aef677f37d277f218787d9181c737e2c054a1f1916c8c3029acbc185eeb9a1a

uv run python "$scope_verifier" --protected-cached "$scope_inventory"
uv run python "$scope_verifier" --protected-diff "$scope_inventory"
range_base=$base
if [[ -z $range_base ]] && git show-ref --verify --quiet refs/heads/main; then
  range_base=$(git merge-base HEAD main)
fi
if [[ -n $range_base ]]; then
  uv run python "$scope_verifier" --protected-range --base "$range_base" "$scope_inventory"
fi

uv run python - "$mode" "$base" <<'PY'
from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

mode, base = sys.argv[1:]
refs = ["WORKTREE"] + (["origin/main"] if mode == "--pr" else [])
failures: list[str] = []


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)


def paths(ref: str) -> set[str]:
    if ref == "WORKTREE":
        return {
            path.as_posix()
            for path in Path(".").rglob("*")
            if path.is_file() and ".git" not in path.parts
        }
    return set(git("ls-tree", "-r", "--name-only", ref).stdout.splitlines())


def has_post_layout(ref: str) -> bool:
    if ref == "WORKTREE":
        return Path("books.yaml").is_file()
    return git("cat-file", "-e", f"{ref}:books.yaml").returncode == 0


def read(ref: str, relative: str) -> str | None:
    if ref == "WORKTREE":
        path = Path(relative)
        return path.read_text(encoding="utf-8") if path.is_file() else None
    proc = git("show", f"{ref}:{relative}")
    return proc.stdout if proc.returncode == 0 else None


def duplicate_numbers(label: str, names: set[str], pattern: str) -> None:
    numbers = [match.group(0) for name in names if (match := re.match(pattern, name))]
    duplicates = sorted(value for value, count in Counter(numbers).items() if count > 1)
    if duplicates:
        failures.append(f"duplicate {label} number(s): {' '.join(duplicates)}")


all_paths = {ref: paths(ref) for ref in refs}
for directory in ("docs/proposals", "docs/designs", "docs/plans", "docs/reviews"):
    names = {
        path.split("/")[-1]
        for ref in refs
        for path in all_paths[ref]
        if path.startswith(directory + "/") and path.count("/") == directory.count("/") + 1
    }
    duplicate_numbers(directory, names, r"^[0-9]{3}")

for book_id in ("book1", "book2"):
    unit_names: set[str] = set()
    mock_names: set[str] = set()
    for ref in refs:
        post = has_post_layout(ref)
        unit_prefix = f"{book_id}/units/" if post else ("units/" if book_id == "book1" else "")
        mock_prefix = f"{book_id}/mocktests/" if post else ("mocktests/" if book_id == "book1" else "")
        if unit_prefix:
            unit_names.update(
                path[len(unit_prefix):].split("/", 1)[0]
                for path in all_paths[ref]
                if path.startswith(unit_prefix) and "/" in path[len(unit_prefix):]
            )
        if mock_prefix:
            mock_names.update(
                path[len(mock_prefix):].split("/", 1)[0]
                for path in all_paths[ref]
                if path.startswith(mock_prefix) and "/" in path[len(mock_prefix):]
            )
    duplicate_numbers(f"{book_id}/units", unit_names, r"^(?:B[0-9]-)?[A-Z]?[0-9]+")
    duplicate_numbers(f"{book_id}/mocktests", mock_names, rf"^r{book_id[-1]}-[0-9]+")


def roadmap_parts(ref: str) -> tuple[dict[str, str], dict[str, tuple[str, ...]]]:
    import yaml

    candidates = (
        ["book1/curriculum/coverage-map.yaml", "book2/curriculum/coverage-map.yaml"]
        if has_post_layout(ref)
        else ["curriculum/coverage-map.yaml"]
    )
    points: dict[str, str] = {}
    units: dict[str, tuple[str, ...]] = {}
    for relative in candidates:
        text = read(ref, relative)
        if text is None:
            continue
        raw = yaml.safe_load(text) or {}
        selected_book = 2 if relative.startswith("book2/") else 1
        for row in raw.get("knowledge_points") or []:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            is_r2 = row.get("layer") == "round-2-extension" or str(row.get("destination", "")).startswith("B2-")
            if has_post_layout(ref) and is_r2 != (selected_book == 2):
                continue
            points[str(row["id"])] = str(row.get("destination", ""))
        for row in raw.get("planned_units") or []:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            is_r2 = row.get("layer") == "round-2-extension" or str(row["id"]).startswith("B2-")
            if has_post_layout(ref) and is_r2 != (selected_book == 2):
                continue
            units[str(row["id"])] = tuple(sorted(map(str, row.get("knowledge_points") or [])))
    return points, units


if mode == "--pr":
    base_maps = roadmap_parts(base)
    work_maps = roadmap_parts("WORKTREE")
    main_maps = roadmap_parts("origin/main")
    for label, baseline, worktree, main in zip(
        ("knowledge-point", "planned-unit"), base_maps, work_maps, main_maps, strict=True
    ):
        changed_work = {key for key in set(baseline) | set(worktree) if baseline.get(key) != worktree.get(key)}
        changed_main = {key for key in set(baseline) | set(main) if baseline.get(key) != main.get(key)}
        for key in sorted(changed_work & changed_main):
            if key not in baseline or worktree.get(key) != main.get(key):
                failures.append(
                    f"roadmap {label} ownership collision: {key} "
                    f"(worktree={worktree.get(key)!r}, origin/main={main.get(key)!r})"
                )

    if not has_post_layout("origin/main"):
        changed_main_paths = set(
            git("diff", "--name-only", f"{base}..origin/main").stdout.splitlines()
        )
        known_files = {
            "syllabus.md",
            "curriculum/course-schedule.yaml",
            "curriculum/coverage-map.yaml",
            "curriculum/material-inventory.yaml",
            "curriculum/official-topics.yaml",
            "curriculum/sources.yaml",
        }
        for path in sorted(changed_main_paths):
            legacy = path == "syllabus.md" or path.startswith(("units/", "mocktests/", "reference/", "curriculum/"))
            translatable = path in known_files or path.startswith(("units/", "mocktests/", "reference/r1-", "reference/r2-"))
            if legacy and not translatable:
                failures.append(f"untranslatable legacy addition: {path}")

tracked = set(git("ls-files").stdout.splitlines())
for book_id in ("book1", "book2"):
    prefix = f"{book_id}/reference/"
    leaks = sorted(
        path for path in tracked
        if path.startswith(prefix) and path not in {prefix + ".gitkeep", prefix + "analysis.md"}
    )
    if leaks:
        failures.append("tracked raw reference files: " + ", ".join(leaks))

conflicts = git("grep", "-nE", r"^(<{7}|={7}|>{7})( |$)", "--", ":!scripts/pre-merge-guard.sh")
if conflicts.returncode == 0:
    failures.append("conflict markers found")

for failure in failures:
    print(f"FAIL: {failure}")
if not failures:
    print("pre-merge-guard: OK")
raise SystemExit(bool(failures))
PY
