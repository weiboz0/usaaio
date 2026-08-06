#!/usr/bin/env bash
# The authoritative local gate (design 000 §3). Must be green before any merge.
# Checks whose tools are not yet shipped print "SKIP (plan NNN)" — acceptable only
# while that plan is unshipped.
set -euo pipefail
cd "$(dirname "$0")/.."

step() { echo; echo "=== $1 ==="; }

step "1/7 lint (ruff)"
uv run ruff check tools/ tests/

step "2/7 unit tests (pytest)"
uv run pytest -q

step "3/7 solution- and lesson-notebook execution"
notebooks=$(find units mocktests -path '*/solutions/*.ipynb' -o -path '*/practice/*solution*.ipynb' 2>/dev/null || true)
if [[ -z "$notebooks" ]]; then
  echo "no notebooks yet — nothing to execute"
else
  while IFS= read -r nb; do
    echo "executing: $nb"
    uv run jupyter execute "$nb"
  done <<< "$notebooks"
  # answer-check permanence: every solution notebook must end with assert cells
  uv run python - <<'PYEOF'
import json, glob, sys
bad = [f for f in glob.glob('units/*/practice/*_solution.ipynb') + glob.glob('mocktests/*/solutions/*.ipynb')
       if not any('assert' in ''.join(c['source'])
                  for c in [x for x in json.load(open(f))['cells'] if x['cell_type'] == 'code'][-2:])]
if bad:
    print('FAIL: solutions missing final answer-check asserts:', *bad, sep='\n  ')
    sys.exit(1)
print(f"answer-check asserts present in all {len(glob.glob('units/*/practice/*_solution.ipynb'))} unit solutions")
PYEOF
fi

# Lesson/review/overview execution (plan 014 Task 0 — decided on measurement, not assumption).
# These notebooks carry enforced tolerance contracts and executable narration whose printed
# output the prose must match; leaving them unexecuted made every such contract unguarded.
# Measured cost: 269s over 79 notebooks against a 1681s baseline (+16%), well inside the
# plan's +12-minute ceiling, so the FULL option was taken rather than a sampled subset.
lessons=$(find units -name '*.ipynb' -not -path '*/practice/*' 2>/dev/null || true)
if [[ -n "$lessons" ]]; then
  n_lessons=0
  while IFS= read -r nb; do
    echo "executing: $nb"
    uv run jupyter execute "$nb"
    n_lessons=$((n_lessons + 1))
  done <<< "$lessons"
  echo "executed $n_lessons lesson/review/overview notebooks"
fi
uv run usaaio-tools answerkey-check || { rc=$?; [[ $rc -eq 3 ]] || exit $rc; }

step "4/7 register verification"
python3 scripts/verify-register.py || { rc=$?; [[ $rc -eq 3 ]] || exit $rc; }

step "5/7 manifest + content checks"
for c in prereq-check coverage-check tolerance-check hygiene-check blueprint-check overlap-scan; do
  echo "running: $c"
  uv run usaaio-tools "$c" || { rc=$?; [[ $rc -eq 3 ]] || exit $rc; }
done

step "6/7 PDF build (quarto)"
bash scripts/build-pdf.sh || { rc=$?; [[ $rc -eq 3 ]] || exit $rc; }

step "7/7 pre-merge-guard"
bash scripts/pre-merge-guard.sh

echo
echo "ci-local: ALL GREEN"
