#!/usr/bin/env bash
# The authoritative local gate (design 000 §3). Must be green before any merge.
# Checks whose tools are not yet shipped print "SKIP (plan NNN)" — acceptable only
# while that plan is unshipped.
set -euo pipefail
cd "$(dirname "$0")/.."

step() { echo; echo "=== $1 ==="; }

step "1/6 lint (ruff)"
uv run ruff check tools/ tests/

step "2/6 unit tests (pytest)"
uv run pytest -q

step "3/6 solution-notebook execution"
notebooks=$(find units mocktests -path '*/solutions/*.ipynb' -o -path '*/practice/*solution*.ipynb' 2>/dev/null || true)
if [[ -z "$notebooks" ]]; then
  echo "no notebooks yet — nothing to execute"
else
  while IFS= read -r nb; do
    echo "executing: $nb"
    uv run jupyter execute "$nb"
  done <<< "$notebooks"
fi
echo "PENDING (plan 006): answer-key reproduction"

step "4/6 manifest + content checks"
for c in prereq-check coverage-check hygiene-check blueprint-check overlap-scan; do
  echo "running: $c"
  uv run usaaio-tools "$c" || { rc=$?; [[ $rc -eq 3 ]] || exit $rc; }
done

step "5/6 PDF build (quarto)"
echo "SKIP (plan 006)"

step "6/6 pre-merge-guard"
bash scripts/pre-merge-guard.sh

echo
echo "ci-local: ALL GREEN"
