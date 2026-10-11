#!/usr/bin/env bash
# Render one registered book's syllabus, per-unit practice handouts, and mock-test papers and
# solutions into output/<book>/ (Plan 030 D4; tools/publish_pdf.py). Intermediate files and the
# kept LaTeX logs stay under <book>/build/pdf/.
#   build-pdf.sh [--root REPO] --book BOOK_ID [--list-inputs]
# --list-inputs prints every source path the PDFs read (repo-relative, sorted) and renders nothing.
# Exit 3 means SKIP: lualatex or pandoc is not installed.
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
export PATH="$HOME/.local/bin:$PATH"

if [[ -n ${USAAIO_PYTHON:-} ]]; then
  python_cmd=("$USAAIO_PYTHON")
elif command -v uv > /dev/null; then
  python_cmd=(uv run --quiet --project "$script_repo_root" python)
else
  python_cmd=(python3)
fi
args=(--root "$repo_root" --book "$book_id")
((list_inputs)) && args+=(--list-inputs)
PYTHONPATH="$script_repo_root${PYTHONPATH:+:$PYTHONPATH}" "${python_cmd[@]}" -m tools.publish_pdf "${args[@]}"
