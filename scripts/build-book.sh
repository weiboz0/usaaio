#!/usr/bin/env bash
# Build every edition named in tools/publish.py EDITIONS for a `publication: true` book
# (books.yaml), then copy the PDFs (<book>-<edition>[-vol<N>].pdf) to output/<book>/.
# Plan 030 D3 (ported from py4kids' scripts/build-book.sh).
#
#   build-book.sh [--root REPO] --book <id>
#       full build: <book>/build/publish/<project>/, PDFs copied to output/<book>/
#   build-book.sh [--root REPO] --book <id> [--units U...] [--mocktests T...]
#       scoped check (D6): all four editions restricted to the named units and mock tests,
#       plus front and back matter, rendered into <book>/build/publish-check/; nothing is
#       copied to output/.
#
# The editions render in parallel, each with its own TeX and Quarto caches;
# set BOOK_BUILD_PARALLEL=0 to render them one after another.
set -euo pipefail

usage() {
  echo 'usage: build-book.sh [--root REPO] --book <publication book id> [--units UNIT...] [--mocktests TEST...]' >&2
  exit 2
}
repo_root=.
book=
scoped=0
units=()
mocktests=()
while (($#)); do
  case "$1" in
    --root) [[ $# -ge 2 ]] || usage; repo_root=$2; shift 2 ;;
    --book) [[ $# -ge 2 ]] || usage; book=$2; shift 2 ;;
    --units)
      scoped=1; shift
      while (($#)) && [[ $1 != --* ]]; do units+=("$1"); shift; done
      ;;
    --mocktests)
      scoped=1; shift
      while (($#)) && [[ $1 != --* ]]; do mocktests+=("$1"); shift; done
      ;;
    *) usage ;;
  esac
done
[[ -n $book ]] || usage
if ((scoped)) && ((${#units[@]} + ${#mocktests[@]} == 0)); then
  echo "FAIL: build-book: a scoped check needs at least one unit or mock test" >&2
  exit 2
fi
repo_root=$(cd "$repo_root" && pwd -P)
script_repo_root=$(cd "$(dirname "$0")/.." && pwd -P)
export PATH="$HOME/.local/bin:$PATH"

py() {
  PYTHONPATH="$script_repo_root${PYTHONPATH:+:$PYTHONPATH}" \
    uv run --quiet --project "$script_repo_root" python "$@"
}

# A publication book needs a valid <book>/publication.yaml (Plan 030 D1).
if ! py - "$repo_root" "$book" <<'PY'
import sys
from tools.books import publication_config_errors
errors = publication_config_errors(sys.argv[1], sys.argv[2])
for error in errors:
    print("FAIL: " + error, file=sys.stderr)
sys.exit(1 if errors else 0)
PY
then
  exit 2
fi

cache_root="${TMPDIR:-/tmp}/usaaio-book-cache/$book"
build_start=$SECONDS

# Generate every Quarto project first (Python; fast, sequential).
# One line per project: "<project dir> <output stem> <1 if it has an index, else 0>".
publish_args=(--root "$repo_root" --book "$book" --all-editions)
if ((scoped)); then
  publish_args+=(--units "${units[@]}" --mocktests "${mocktests[@]}")
fi
if ! profiles="$(py -m tools.publish "${publish_args[@]}")"; then
  echo "FAIL: build-book: $book: publish" >&2
  exit 1
fi
echo "build-book: generated $(wc -l <<< "$profiles") projects in $((SECONDS-build_start))s"

render() {
  local project="$1" name="$2" index="$3"
  local key
  key=$(basename "$project")
  export TEXMFCACHE="$cache_root/$key/tex" XDG_CACHE_HOME="$cache_root/$key/xdg"
  mkdir -p "$TEXMFCACHE" "$XDG_CACHE_HOME"
  local start=$SECONDS
  if ! quarto render "$project" --to pdf > "$project/render.log" 2>&1; then
    echo "FAIL: $key: quarto render" >&2
    tail -80 "$project/render.log" >&2
    return 1
  fi
  # Draft-mode passes give the audit a clean LaTeX log (labels, references, missing glyphs).
  if ! (cd "$project" && for pass in 1 2; do
      lualatex -draftmode -interaction=nonstopmode -halt-on-error "$name.tex" > latex-audit.log 2>&1 || exit 1
      if [ "$index" = 1 ]; then
        makeindex "$name.idx" >> latex-audit.log 2>&1 || exit 1
      fi
    done); then
    echo "FAIL: $key: LaTeX audit pass" >&2
    tail -80 "$project/latex-audit.log" >&2
    return 1
  fi
  echo "$((SECONDS-start))" > "$project/render-seconds.txt"
}

pids=()
while read -r project name index; do
  if [ "${BOOK_BUILD_PARALLEL:-1}" = 0 ]; then
    render "$project" "$name" "$index"
  else
    render "$project" "$name" "$index" &
    pids+=("$!")
  fi
done <<< "$profiles"
failed=0
for pid in "${pids[@]}"; do
  wait "$pid" || failed=1
done
[ "$failed" = 0 ] || exit 1

pdfs=()
while read -r project name _; do
  pdf="$project/_book/$name.pdf"
  pages="$(pdfinfo "$pdf" | awk '/^Pages:/ {print $2}')"
  echo "$pages" > "$project/pages.txt"
  echo "$(basename "$project") render: $(cat "$project/render-seconds.txt")s, pages: $pages"
  pdfs+=("$pdf")
done <<< "$profiles"

if ((scoped)); then
  echo "build-book: scoped check of $book (units: ${units[*]:-none}; mock tests: ${mocktests[*]:-none}) in $((SECONDS-build_start))s"
  exit 0
fi
py -m tools.publish_output --root "$repo_root" --book "$book" --owner book "${pdfs[@]}"
echo "build-book: ${#pdfs[@]} edition PDFs in $((SECONDS-build_start))s"
