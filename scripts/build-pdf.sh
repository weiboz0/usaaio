#!/usr/bin/env bash
# Render student-facing sources for exactly one registered book.
set -euo pipefail

repo_root=.
book_id=
list_inputs=0
while (($#)); do
  case "$1" in
    --root) repo_root=$2; shift 2 ;;
    --book) book_id=$2; shift 2 ;;
    --list-inputs) list_inputs=1; shift ;;
    *) echo "usage: $0 [--root REPO] --book BOOK_ID [--list-inputs]" >&2; exit 2 ;;
  esac
done
[[ -n "$book_id" ]] || { echo "build-pdf: --book is required" >&2; exit 2; }
repo_root=$(cd "$repo_root" && pwd)
script_repo_root=$(cd "$(dirname "$0")/.." && pwd)
python_bin=${USAAIO_PYTHON:-python3}

if ! registry_record=$(PYTHONPATH="$script_repo_root${PYTHONPATH:+:$PYTHONPATH}" \
  "$python_bin" - "$repo_root" "$book_id" <<'PY'
import sys
from tools.books import load_book_catalog

catalog = load_book_catalog(sys.argv[1])
book = catalog.by_id(sys.argv[2])
print(f"{book.root}\t{book.number}")
PY
); then
  echo "build-pdf: unknown or incomplete book $book_id" >&2
  exit 1
fi
IFS=$'\t' read -r book_root book_number <<<"$registry_record"
[[ -d "$book_root" ]] || {
  echo "build-pdf: unknown or incomplete book $book_id" >&2
  exit 1
}

require_contained_path() { # require_contained_path <path> <must-exist>
  PYTHONPATH="$script_repo_root${PYTHONPATH:+:$PYTHONPATH}" \
    "$python_bin" - "$book_root" "$1" "$2" <<'PY'
import sys
from tools.books import resolve_contained_path

resolve_contained_path(
    sys.argv[1], sys.argv[2], label="build-pdf path", must_exist=sys.argv[3] == "1"
)
PY
}

shopt -s nullglob
inputs=()
if [[ $book_number == 1 ]]; then
  for mocktest_dir in "$book_root"/mocktests/r${book_number}-*/; do
    [[ -f "${mocktest_dir}manifest.yaml" ]] || continue
    [[ -f "${mocktest_dir}test.md" ]] && inputs+=("${mocktest_dir}test.md")
    for path in "${mocktest_dir}"theory/*.md "${mocktest_dir}"problems/*.ipynb; do
      [[ -f "$path" ]] && inputs+=("$path")
    done
  done
elif [[ $book_number == 2 ]]; then
  for manifest in "$book_root"/units/*/manifest.yaml; do
    [[ -f "$manifest" ]] || continue
    unit_dir=${manifest%/manifest.yaml}
    unit_inputs=()
    [[ -f "$unit_dir/lesson.ipynb" ]] && unit_inputs+=("$unit_dir/lesson.ipynb")
    for path in "$unit_dir"/lessons/*.ipynb; do [[ -f "$path" ]] && unit_inputs+=("$path"); done
    [[ -f "$unit_dir/review.ipynb" ]] && unit_inputs+=("$unit_dir/review.ipynb")
    for path in "$unit_dir"/practice/p[0-9][0-9].ipynb; do
      [[ -f "$path" && $path != *_solution.ipynb ]] && unit_inputs+=("$path")
    done
    ((${#unit_inputs[@]})) || {
      echo "build-pdf: live unit ${unit_dir##*/} yielded zero student-facing sources" >&2
      exit 1
    }
    inputs+=("${unit_inputs[@]}")
  done
else
  echo "build-pdf: unsupported book number $book_number for $book_id" >&2
  exit 1
fi

if ((${#inputs[@]})); then
  mapfile -t inputs < <(printf '%s\n' "${inputs[@]}" | sed "s#^$repo_root/##" | LC_ALL=C sort -u)
fi
for relative in "${inputs[@]}"; do
  require_contained_path "$repo_root/$relative" 1
done
if ((list_inputs)); then
  printf '%s\n' "${inputs[@]}"
  exit 0
fi
if ((${#inputs[@]} == 0)); then
  echo "build-pdf: no live student-facing sources for $book_id"
  exit 0
fi
if ! quarto_bin=$(command -v quarto); then
  echo "SKIP build-pdf: QUARTO MISSING — install pinned Quarto 1.6.42" >&2
  exit 3
fi

expected_outputs=()
for relative in "${inputs[@]}"; do
  source="$repo_root/$relative"
  source_dir=$(dirname "$source")
  source_name=$(basename "$source")
  stem=${source_name%.*}
  if [[ $book_number == 1 ]]; then
    within_book=${source#"$book_root/"}
    group=${within_book#mocktests/}; group=${group%%/*}
    output_dir="$book_root/build/$group"
    output="$output_dir/$stem.pdf"
  else
    within_units=${source#"$book_root/units/"}
    unit=${within_units%%/*}
    within_unit=${within_units#"$unit/"}
    parent=$(dirname "$within_unit")
    output_dir="$book_root/build/units/$unit"
    [[ $parent == . ]] || output_dir="$output_dir/$parent"
    output="$output_dir/$stem.pdf"
  fi
  require_contained_path "$output" 0
  expected_outputs+=("$output")
  mkdir -p "$output_dir"
  echo "rendering: $relative"
  (cd "$source_dir" && "$quarto_bin" render "$source_name" --to typst --output-dir "$output_dir" --no-execute)
  [[ -e "$output" ]] || { echo "build-pdf: missing PDF output for $relative" >&2; exit 1; }
  [[ -s "$output" ]] || { echo "build-pdf: zero-byte PDF output for $relative" >&2; exit 1; }
done

mapfile -t actual_outputs < <(find "$book_root/build" -type f -name '*.pdf' | LC_ALL=C sort)
mapfile -t expected_outputs < <(printf '%s\n' "${expected_outputs[@]}" | LC_ALL=C sort -u)
if ((${#actual_outputs[@]} != ${#expected_outputs[@]})); then
  echo "build-pdf: output cardinality ${#actual_outputs[@]} does not match source cardinality ${#expected_outputs[@]}" >&2
  exit 1
fi
for index in "${!expected_outputs[@]}"; do
  [[ ${actual_outputs[$index]} == "${expected_outputs[$index]}" ]] || {
    echo "build-pdf: output set does not exactly match the selected sources" >&2
    exit 1
  }
done
echo "build-pdf: rendered ${#inputs[@]} source(s) for $book_id"
