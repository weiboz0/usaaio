#!/usr/bin/env bash
# Re-downloads the public past-test corpus into a selected book's reference root
# (gitignored, local-only).
# Sources: https://www.usaaio.org/past-problems (public Google Drive links).
# 2025 R1/R2 live in forum threads and are NOT auto-fetched:
#   https://forum.beaver-edge.ai/c/ai-olympiads/usa-north-america-ai-olympiad/8
#   https://forum.beaver-edge.ai/c/ai-olympiads/2025-usa-na-aio-round-2/9
set -euo pipefail
repo_root=$(cd "$(dirname "$0")/.." && pwd)

usage() {
  echo "usage: scripts/fetch-reference.sh (--book book1|--book book2|--all)" >&2
}

selection=""
if [[ ${1:-} == "--all" && $# -eq 1 ]]; then
  selection="all"
elif [[ ${1:-} == "--book" && $# -eq 2 ]]; then
  selection=$2
else
  usage
  exit 2
fi
if [[ $selection != "all" && $selection != "book1" && $selection != "book2" ]]; then
  usage
  exit 2
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

if [[ $selection == "all" || $selection == "book1" ]]; then
  fetch "11z6HzS92y5f6OdeBf7GUtb7PBgF7_RlC" \
    "$repo_root/book1/reference/r1-2026/paper.pdf"
fi
if [[ $selection == "all" || $selection == "book2" ]]; then
  fetch "1YXa62A14vF69ccAQjdWITwTCaCOoyscN" \
    "$repo_root/book2/reference/r2-2026/day1.pdf"
  fetch "1pp3PYo8f-M9HIvEs9VVKwCJAzIL-nmg4" \
    "$repo_root/book2/reference/r2-2026/day2.pdf"
  fetch "1C-2ewSPxNUX6dLL-oxE4FzhJBtjoOIo7" \
    "$repo_root/book2/reference/r2-2026/rationale.pdf"
fi

echo "corpus complete"
