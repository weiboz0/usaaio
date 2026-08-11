#!/usr/bin/env bash
# Re-downloads the public past-test corpus into a selected book's reference root
# (gitignored, local-only).
# Sources: https://www.usaaio.org/past-problems (public Google Drive links).
# 2025 R1/R2 live in forum threads and are NOT auto-fetched:
#   https://forum.beaver-edge.ai/c/ai-olympiads/usa-north-america-ai-olympiad/8
#   https://forum.beaver-edge.ai/c/ai-olympiads/2025-usa-na-aio-round-2/9
set -euo pipefail
script_repo_root=$(cd "$(dirname "$0")/.." && pwd)
repo_root=$script_repo_root

usage() {
  echo "usage: scripts/fetch-reference.sh [--root REPO] (--book BOOK_ID|--all)" >&2
}

selection=""
while (($#)); do
  case "$1" in
    --root) repo_root=$2; shift 2 ;;
    --book) [[ -z $selection ]] || { usage; exit 2; }; selection=$2; shift 2 ;;
    --all) [[ -z $selection ]] || { usage; exit 2; }; selection=all; shift ;;
    *) usage; exit 2 ;;
  esac
done
[[ -n $selection ]] || { usage; exit 2; }
repo_root=$(cd "$repo_root" && pwd)
python_bin=${USAAIO_PYTHON:-python3}
if ! registry_records=$(PYTHONPATH="$script_repo_root${PYTHONPATH:+:$PYTHONPATH}" \
  "$python_bin" - "$repo_root" "$selection" <<'PY'
import sys
from tools.books import load_book_catalog

catalog = load_book_catalog(sys.argv[1])
books = catalog.books if sys.argv[2] == "all" else (catalog.by_id(sys.argv[2]),)
for book in books:
    print(f"{book.id}\t{book.number}\t{book.root}")
PY
); then
  echo "fetch-reference: unknown or invalid registered book selection $selection" >&2
  exit 1
fi

try_download() {  # try_download <url> <dest>
  curl -fsSL --retry 3 --max-time 120 "$1" -o "$2"
}

valid_pdf() {  # header AND trailer: a truncated stream passes `file` (header-only) but
               # loses the %%EOF trailer, so require both.
  file "$1" 2>/dev/null | grep -q 'PDF document' \
    && tail -c 1024 "$1" 2>/dev/null | grep -q '%%EOF'
}

fetch() {  # fetch <drive-file-id> <dest-path>
  local id="$1" dest="$2"
  local tmp="${dest}.tmp"   # separate line: ${dest} must expand AFTER its assignment (set -u)
  if [[ -s "$dest" ]] && valid_pdf "$dest"; then
    echo "exists: $dest"
    return 0
  fi
  rm -f "$dest"   # cached file failed validation — refetch
  mkdir -p "$(dirname "$dest")"
  # Acceptance requires BOTH curl success (-f, no error bodies) AND structural validity;
  # tmp+mv means $dest only ever holds a validated PDF.
  if ! { try_download "https://drive.google.com/uc?export=download&id=${id}" "$tmp" \
         && valid_pdf "$tmp"; }; then
    # Large/flagged files get an HTML interstitial; retry via the usercontent endpoint.
    if ! { try_download "https://drive.usercontent.google.com/download?id=${id}&export=download&confirm=t" "$tmp" \
           && valid_pdf "$tmp"; }; then
      echo "FAIL: $dest — no complete PDF obtained (blocked, truncated, or link rotated; try gdown)" >&2
      rm -f "$tmp"
      return 1
    fi
  fi
  mv "$tmp" "$dest"
  echo "fetched: $dest ($(file -b "$dest"))"
}

while IFS=$'\t' read -r selected_id book_number book_root; do
  [[ -n $selected_id ]] || continue
  if [[ $book_number == 1 ]]; then
    fetch "11z6HzS92y5f6OdeBf7GUtb7PBgF7_RlC" \
      "$book_root/reference/r1-2026/paper.pdf"
  elif [[ $book_number == 2 ]]; then
    fetch "1YXa62A14vF69ccAQjdWITwTCaCOoyscN" \
      "$book_root/reference/r2-2026/day1.pdf"
    fetch "1pp3PYo8f-M9HIvEs9VVKwCJAzIL-nmg4" \
      "$book_root/reference/r2-2026/day2.pdf"
    fetch "1C-2ewSPxNUX6dLL-oxE4FzhJBtjoOIo7" \
      "$book_root/reference/r2-2026/rationale.pdf"
  else
    echo "fetch-reference: unsupported book number $book_number for $selected_id" >&2
    exit 1
  fi
done <<<"$registry_records"

echo "corpus complete"
