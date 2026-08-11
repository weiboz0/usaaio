#!/usr/bin/env bash
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
archive_dir=$(mktemp -d)
trap 'rm -rf "$archive_dir"' EXIT

git -C "$repo_root" archive --format=tar HEAD | tar -xf - -C "$archive_dir"
cd "$archive_dir"

if [[ -n "${USAAIO_REFERENCE_CACHE:-}" && -d "$USAAIO_REFERENCE_CACHE" ]]; then
  mkdir -p book1/reference/cache
  cp -a "$USAAIO_REFERENCE_CACHE"/. book1/reference/cache/
fi

bash scripts/ci-local.sh
