#!/usr/bin/env bash
# The sole historical verification path: archive a named revision and inject no dates via env.
set -euo pipefail

if (($# != 2)); then
  echo "usage: scripts/verify-historical-deferred-policy.sh <archived-commit> <ISO-date>" >&2
  exit 2
fi

commit=$1
as_of_date=$2
repo_root=$(cd "$(dirname "$0")/.." && pwd)
archive_root=$(mktemp -d)
cleanup() { rm -rf "$archive_root"; }
trap cleanup EXIT

git -C "$repo_root" rev-parse --verify "${commit}^{commit}" >/dev/null
git -C "$repo_root" archive "$commit" | tar -x -C "$archive_root"
(
  uv run --project "$repo_root" python "$repo_root/tools/verify_historical_deferred_policy.py" \
    --root "$archive_root/book2" --as-of-date "$as_of_date"
)
