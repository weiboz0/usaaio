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
if [[ "$MODE" == "--pr" ]]; then
  if git fetch -q origin main 2>/dev/null; then
    refs+=(origin/main)
  else
    echo "note: origin/main not reachable — checking worktree only"
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
  # unit dirs: NN-name; mocktest dirs: r1-NNN
  check_dupes "$dir" "$(printf '%s\n' "$names" | sort -u)" '^(r[0-9]-)?[0-9]+'
done

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
