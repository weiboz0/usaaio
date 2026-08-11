#!/usr/bin/env bash
set -euo pipefail

script_path=${BASH_SOURCE[0]}
script_rel=${script_path#"$(pwd)"/}
if [[ ! -f tests/fixtures/plan019-path-inventory.yaml ]] && \
   ! git ls-files --error-unmatch "$script_rel" >/dev/null 2>&1; then
  trap 'rm -f "$script_path"; rmdir "$(dirname "$script_path")" 2>/dev/null || true' EXIT
fi

dry_run=0
if [[ ${1:-} == "--dry-run" ]]; then
  dry_run=1
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--dry-run]" >&2
  exit 2
fi

if [[ ! -d reference ]]; then
  [[ -d book1/reference && -d book2/reference ]] || {
    echo "reference migration: neither legacy nor migrated layout exists" >&2
    exit 1
  }
  echo "reference migration already complete: book1/reference book2/reference"
  exit 0
fi

bad=()
while IFS= read -r -d '' entry; do
  name=${entry#reference/}
  case "$name" in
    .gitkeep|analysis.md|r1-*|r2-*|cache|outlines-*) ;;
    *) bad+=("$name") ;;
  esac
done < <(find reference -mindepth 1 -maxdepth 1 -print0)
if (( ${#bad[@]} )); then
  printf 'refusing unknown reference entry: %s\n' "${bad[@]}" >&2
  exit 1
fi

echo "reference migration: reference -> book1/reference + book2/reference"
if (( dry_run )); then
  exit 0
fi

mkdir -p book1/reference book2/reference

move_entry() {
  local source=$1 destination=$2
  if git ls-files --error-unmatch "$source" >/dev/null 2>&1; then
    git mv "$source" "$destination"
  else
    mv "$source" "$destination"
  fi
}

if [[ -e reference/analysis.md ]]; then
  git mv reference/analysis.md book1/reference/analysis.md
fi

python3 - <<'PY'
from pathlib import Path

source = Path("book1/reference/analysis.md")
if source.exists():
    text = source.read_text(encoding="utf-8")
    marker = "## Round 2 shape and topics"
    if marker not in text:
        raise SystemExit(f"{source}: missing semantic split heading {marker!r}")
    pre, r2 = text.split(marker, 1)
    lines = pre.splitlines(keepends=True)
    book1 = "".join(
        line for line in lines if not (line.startswith("|") and "r2-" in line)
    ).rstrip() + "\n\n"

    sources_heading = pre.find("## Sources")
    if sources_heading < 0:
        sources_heading = 0
    prefix_lines = pre[:sources_heading].splitlines(keepends=True)
    source_lines = pre[sources_heading:].splitlines(keepends=True)
    table_end = 0
    seen_table = False
    for index, line in enumerate(source_lines):
        if line.startswith("|"):
            seen_table = True
            table_end = index + 1
        elif seen_table:
            break
    if not seen_table:
        raise SystemExit("semantic reference split could not locate Sources table")
    book2_prefix = "".join(prefix_lines + [
        line for line in source_lines[:table_end]
        if not (line.startswith("|") and "r1-" in line)
    ]).rstrip() + "\n\n"
    book2 = book2_prefix + marker + r2
    if "r2-" in book1 or marker in book1 or "r1-" in book2 or "## Round 1" in book2:
        raise SystemExit("semantic reference split leaked round-specific content")
    source.write_text(book1, encoding="utf-8")
    Path("book2/reference/analysis.md").write_text(book2, encoding="utf-8")
PY

for path in reference/r1-* reference/cache reference/outlines-*; do
  [[ -e "$path" ]] || continue
  move_entry "$path" book1/reference/
done
for path in reference/r2-*; do
  [[ -e "$path" ]] || continue
  move_entry "$path" book2/reference/
done
[[ -e reference/.gitkeep ]] && move_entry reference/.gitkeep book1/reference/.gitkeep
rmdir reference
touch book2/reference/.gitkeep

python3 - <<'PY'
from pathlib import Path

path = Path(".gitignore")
text = path.read_text(encoding="utf-8") if path.exists() else ""
replacements = {
    "reference/r1-": "book1/reference/r1-",
    "reference/r2-": "book2/reference/r2-",
    "reference/cache/": "book1/reference/cache/",
}
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text, encoding="utf-8")
PY
