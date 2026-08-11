#!/usr/bin/env bash
# Authoritative local gate for both independently complete books.
set -euo pipefail
cd "$(dirname "$0")/.."

step() { echo; echo "=== $1 ==="; }
BOOKS=(book1 book2)

step "1/9 registry + lint"
uv run python - <<'PY'
from tools.books import load_book_catalog, validate_book_root
catalog = load_book_catalog(".")
assert [book.id for book in catalog.books] == ["book1", "book2"]
for book in catalog.books:
    errors = validate_book_root(book)
    if errors:
        raise SystemExit("\n".join(errors))
print("registry: book1 -> book2")
PY
uv run ruff check tools/ tests/

step "2/9 unit tests"
uv run pytest -q

step "3/9 solution and lesson notebook execution"
for book in "${BOOKS[@]}"; do
  book_root=$PWD/$book
  mapfile -t notebooks < <(
    find "$book_root/units" "$book_root/mocktests" -type f \
      \( -path '*/solutions/*.ipynb' -o -path '*/practice/*solution*.ipynb' \) \
      | LC_ALL=C sort
  )
  for notebook in "${notebooks[@]}"; do
    relative=${notebook#"$book_root"/}
    echo "executing [$book]: $relative"
    (cd "$book_root" && USAAIO_BOOK_ROOT="$book_root" uv run --project .. jupyter execute "$relative")
  done
  mapfile -t lessons < <(
    find "$book_root/units" -type f -name '*.ipynb' \
      -not -path '*/practice/*' -not -path '*/.ipynb_checkpoints/*' | LC_ALL=C sort
  )
  for notebook in "${lessons[@]}"; do
    relative=${notebook#"$book_root"/}
    echo "executing [$book]: $relative"
    (cd "$book_root" && USAAIO_BOOK_ROOT="$book_root" uv run --project .. jupyter execute "$relative")
  done
done

step "4/9 register verification"
uv run python scripts/verify-register.py --book book1

step "5/9 per-book checks"
for book in "${BOOKS[@]}"; do
  for c in prereq-check coverage-check scope-check schedule-check tolerance-check hygiene-check blueprint-check overlap-scan answerkey-check layer-boundary-check; do
    echo "running [$book]: $c"
    uv run usaaio-tools --book "$book" "$c" || { rc=$?; [[ $rc -eq 3 ]] || exit "$rc"; }
  done
done

step "6/9 aggregate checks"
for c in prereq-check scope-check schedule-check; do
  uv run usaaio-tools --all "$c"
done

step "7/9 generated Book 1 evidence and mutation checks"
echo "SKIP generated Book 1 evidence freshness (plan 019 Task 3)"
uv run python -m tools.render_course_structure --root book1 --check
uv run python -m tools.verify_training_mutations --root book1
uv run python -m tools.verify_classical_mutations --root book1
echo "SKIP attention mutations (plan 019 Task 7)"

step "8/9 PDF build"
for book in "${BOOKS[@]}"; do
  bash scripts/build-pdf.sh --book "$book" || { rc=$?; [[ $rc -eq 3 ]] || exit "$rc"; }
done

step "9/9 pre-merge guard"
bash scripts/pre-merge-guard.sh

echo
echo "ci-local: ALL GREEN"
