#!/usr/bin/env bash
# Render student-facing mock-test sources to Typst PDFs without executing notebooks.
set -euo pipefail
cd "$(dirname "$0")/.."

shopt -s nullglob
mocktest_dirs=(mocktests/r1-*/)
if [[ ${#mocktest_dirs[@]} -eq 0 ]]; then
  echo "build-pdf: no mocktest directories — nothing to render"
  exit 0
fi

if ! quarto_bin=$(command -v quarto); then
  echo "SKIP build-pdf: QUARTO MISSING — install pinned Quarto 1.6.42" >&2
  exit 3
fi

for mocktest_dir in "${mocktest_dirs[@]}"; do
  build_dir="${mocktest_dir}build"
  mkdir -p "$build_dir"
  echo "rendering: ${mocktest_dir}test.md"
  (
    cd "$mocktest_dir"
    "$quarto_bin" render test.md --to typst --output-dir build --no-execute
  )

  problem_notebooks=("${mocktest_dir}"problems/*.ipynb)
  for notebook in "${problem_notebooks[@]}"; do
    notebook_name=$(basename "$notebook")
    echo "rendering: $notebook"
    (
      cd "${mocktest_dir}problems"
      "$quarto_bin" render "$notebook_name" --to typst --output-dir ../build --no-execute
    )
  done
done

echo "build-pdf: rendered ${#mocktest_dirs[@]} mocktest directory/directories"
