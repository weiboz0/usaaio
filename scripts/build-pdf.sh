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
book_root="$repo_root/$book_id"
[[ -f "$repo_root/books.yaml" && -d "$book_root" ]] || {
  echo "build-pdf: unknown or incomplete book $book_id" >&2
  exit 1
}

shopt -s nullglob
inputs=()
if [[ $book_id == book1 ]]; then
  for mocktest_dir in "$book_root"/mocktests/r1-*/; do
    [[ -f "${mocktest_dir}manifest.yaml" ]] || continue
    [[ -f "${mocktest_dir}test.md" ]] && inputs+=("${mocktest_dir}test.md")
    for path in "${mocktest_dir}"theory/*.md "${mocktest_dir}"problems/*.ipynb; do
      [[ -f "$path" ]] && inputs+=("$path")
    done
  done
elif [[ $book_id == book2 ]]; then
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
  echo "build-pdf: unsupported book $book_id" >&2
  exit 1
fi

if ((${#inputs[@]})); then
  mapfile -t inputs < <(printf '%s\n' "${inputs[@]}" | sed "s#^$repo_root/##" | LC_ALL=C sort -u)
fi
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

for relative in "${inputs[@]}"; do
  source="$repo_root/$relative"
  source_dir=$(dirname "$source")
  unit_or_mock=${relative#*/}
  unit_or_mock=${unit_or_mock%%/*}
  if [[ $relative == book1/mocktests/* ]]; then
    group=${relative#book1/mocktests/}; group=${group%%/*}
  else
    group=${relative#book2/units/}; group=${group%%/*}
  fi
  output_dir="$book_root/build/$group"
  mkdir -p "$output_dir"
  echo "rendering: $relative"
  (cd "$source_dir" && "$quarto_bin" render "$(basename "$source")" --to typst --output-dir "$output_dir" --no-execute)
done

outputs=$(find "$book_root/build" -type f -name '*.pdf' -size +0c | wc -l)
((outputs > 0)) || { echo "build-pdf: zero nonempty outputs for $book_id" >&2; exit 1; }
echo "build-pdf: rendered ${#inputs[@]} source(s) for $book_id"
