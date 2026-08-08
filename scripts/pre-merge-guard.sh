#!/usr/bin/env bash
# Guards against artifacts that collide when parallel sessions merge:
# duplicate 3-digit doc numbers and duplicate unit/mocktest IDs.
# --pr: also check against origin/main (the simulated post-merge union).
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${1:-}"
fail=0

collect() {  # collect <git-ref-or-WORKTREE> <glob-dir>
  local ref="$1" dir="$2"
  if [[ "$ref" == "WORKTREE" ]]; then
    [[ -d "$dir" ]] && find "$dir" -maxdepth 1 -mindepth 1 -printf '%f\n' || true
  else
    git ls-tree --name-only "$ref" "$dir/" 2>/dev/null | xargs -rn1 basename || true
  fi
}

check_dupes() {  # check_dupes <label> <newline-separated names> <prefix-regex>
  local label="$1" names="$2" regex="$3"
  local dupes
  # `|| true`: grep exits 1 on no match, which pipefail would otherwise turn fatal
  dupes=$(printf '%s\n' "$names" | grep -oE "$regex" | sort | uniq -d || true)
  if [[ -n "$dupes" ]]; then
    echo "FAIL: duplicate ${label} number(s): $(echo "$dupes" | tr '\n' ' ')"
    fail=1
  fi
}

refs=(WORKTREE)
check_roadmap_union=0
if [[ "$MODE" == "--pr" ]]; then
  if git fetch -q origin main 2>/dev/null; then
    refs+=(origin/main)
    check_roadmap_union=1
  else
    echo "FAIL: origin/main fetch unavailable; --pr union is unverified" >&2
    fail=1
  fi
elif [[ -n "$MODE" ]]; then
  echo "usage: pre-merge-guard.sh [--pr]   (unknown argument: $MODE)" >&2
  exit 2
fi

for dir in docs/proposals docs/designs docs/plans docs/reviews; do
  names=""
  for ref in "${refs[@]}"; do names+="$(collect "$ref" "$dir")"$'\n'; done
  check_dupes "$dir" "$(printf '%s\n' "$names" | sort -u)" '^[0-9]{3}'
done

for dir in units mocktests; do
  names=""
  for ref in "${refs[@]}"; do names+="$(collect "$ref" "$dir")"$'\n'; done
  # unit dirs: NN-name or B2-NNN-name; mocktest dirs: r1-NNN
  if [[ "$dir" == "units" ]]; then
    check_dupes "$dir" "$(printf '%s\n' "$names" | sort -u)" '^(B[0-9]-)?[0-9]+'
  else
    check_dupes "$dir" "$(printf '%s\n' "$names" | sort -u)" '^r[0-9]-[0-9]+'
  fi
done

if [[ $check_roadmap_union -eq 1 ]]; then
  if ! base=$(git merge-base HEAD origin/main 2>/dev/null); then
    echo "FAIL: origin/main merge-base unavailable; --pr union is unverified" >&2
    fail=1
    check_roadmap_union=0
  fi
fi

if [[ $check_roadmap_union -eq 1 ]]; then
  if ! roadmap_collisions=$(uv run python - "$base" <<'PY'
import subprocess
import sys
from pathlib import Path

import yaml

ROADMAP = "curriculum/coverage-map.yaml"


def load_ref(ref):
    if ref == "WORKTREE":
        path = Path(ROADMAP)
        if not path.is_file():
            return {}
        text = path.read_text(encoding="utf-8")
    else:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{ROADMAP}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            return {}
        text = proc.stdout
    raw = yaml.safe_load(text) or {}
    if not isinstance(raw, dict):
        return {}
    return raw


def ownership(raw):
    points = {
        str(row.get("id", "")): str(row.get("destination", ""))
        for row in raw.get("knowledge_points") or []
        if isinstance(row, dict) and row.get("id")
    }
    units = {
        str(row.get("id", "")): tuple(sorted(str(value) for value in row.get("knowledge_points") or []))
        for row in raw.get("planned_units") or []
        if isinstance(row, dict) and row.get("id")
    }
    return points, units


base_ref = sys.argv[1]
base_maps = ownership(load_ref(base_ref))
worktree_maps = ownership(load_ref("WORKTREE"))
main_maps = ownership(load_ref("origin/main"))
for label, base, worktree, main in zip(
    ("knowledge-point", "planned-unit"), base_maps, worktree_maps, main_maps, strict=True
):
    changed_worktree = {key for key in set(base) | set(worktree) if base.get(key) != worktree.get(key)}
    changed_main = {key for key in set(base) | set(main) if base.get(key) != main.get(key)}
    for key in sorted(changed_worktree & changed_main):
        concurrently_added = key not in base
        divergent = worktree.get(key) != main.get(key)
        if concurrently_added or divergent:
            print(
                f"FAIL: roadmap {label} ownership collision: {key} "
                f"(worktree={worktree.get(key)!r}, origin/main={main.get(key)!r})"
            )
PY
); then
    echo "FAIL: origin/main roadmap union could not be evaluated; --pr union is unverified" >&2
    fail=1
    roadmap_collisions=""
  fi
  if [[ -n "$roadmap_collisions" ]]; then
    printf '%s\n' "$roadmap_collisions"
    fail=1
  fi
fi

if git grep -nE '^(<{7}|={7}|>{7})( |$)' -- ':!scripts/pre-merge-guard.sh' >/dev/null 2>&1; then
  echo "FAIL: conflict markers found:"
  git grep -nE '^(<{7}|={7}|>{7})( |$)' -- ':!scripts/pre-merge-guard.sh' | head || true
  fail=1
fi

leaks=$(git ls-files reference/ | grep -vE '^reference/(\.gitkeep|analysis\.md)$' || true)
if [[ -n "$leaks" ]]; then
  echo "FAIL: tracked files under reference/ beyond the public whitelist:"
  printf '%s\n' "$leaks"
  fail=1
fi

if [[ $fail -eq 0 ]]; then echo "pre-merge-guard: OK"; fi
exit $fail
