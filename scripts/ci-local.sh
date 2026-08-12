#!/usr/bin/env bash
# Authoritative local gate for both independently complete books.
set -euo pipefail
script_repo_root=$(cd "$(dirname "$0")/.." && pwd)
repo_root=$script_repo_root
registry_probe=0
while (($#)); do
  case "$1" in
    --root) repo_root=$2; shift 2 ;;
    --registry-probe) registry_probe=1; shift ;;
    *) echo "usage: scripts/ci-local.sh [--root REPO] [--registry-probe]" >&2; exit 2 ;;
  esac
done
cd "$repo_root"

step() { echo; echo "=== $1 ==="; }
if ! registry_records=$(PYTHONPATH="$script_repo_root${PYTHONPATH:+:$PYTHONPATH}" \
  uv run --project "$script_repo_root" python - <<'PY'
from tools.books import load_book_catalog

for book in load_book_catalog(".").books:
    print(f"{book.id}\t{book.number}\t{book.root}")
PY
); then
  echo "FAIL: cannot load registered books from $repo_root" >&2
  exit 1
fi
mapfile -t BOOK_RECORDS <<<"$registry_records"
BOOK_IDS=()
BOOK_NUMBERS=()
BOOK_ROOTS=()
for record in "${BOOK_RECORDS[@]}"; do
  IFS=$'\t' read -r book_id book_number book_root <<<"$record"
  BOOK_IDS+=("$book_id")
  BOOK_NUMBERS+=("$book_number")
  BOOK_ROOTS+=("$book_root")
done
if ((registry_probe)); then
  printf '%s\n' "${BOOK_RECORDS[@]}"
  exit 0
fi

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
for index in "${!BOOK_IDS[@]}"; do
  book=${BOOK_IDS[$index]}
  book_root=${BOOK_ROOTS[$index]}
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
for book in "${BOOK_IDS[@]}"; do
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
book1_root=
for index in "${!BOOK_IDS[@]}"; do
  [[ ${BOOK_NUMBERS[$index]} == 1 ]] && book1_root=${BOOK_ROOTS[$index]}
done
[[ -n $book1_root ]] || { echo "FAIL: no registered Book 1 root" >&2; exit 1; }
uv run python -m tools.audit_curriculum --root "$book1_root" --check
uv run python -m tools.render_curriculum_roadmap --root "$repo_root" --check
uv run python -m tools.render_course_structure --root "$book1_root" --check
for book_root in "${BOOK_ROOTS[@]}"; do
  [[ $book_root == "$book1_root" ]] && continue
  uv run python -m tools.render_course_structure --root "$book_root" --check
done
uv run python -m tools.verify_training_mutations --root "$book1_root"
uv run python -m tools.verify_classical_mutations --root "$book1_root"
echo "SKIP attention mutations (plan 019 Task 7)"

step "8/9 PDF build"
for book in "${BOOK_IDS[@]}"; do
  bash scripts/build-pdf.sh --book "$book" || { rc=$?; [[ $rc -eq 3 ]] || exit "$rc"; }
done

step "9/9 pre-merge guard"
bash scripts/pre-merge-guard.sh

echo
echo "ci-local: ALL GREEN"
