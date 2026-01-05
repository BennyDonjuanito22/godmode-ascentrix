#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <pattern> [path]" >&2
  exit 1
fi

PATTERN="$1"
shift || true
SEARCH_PATHS=("$@")
if [ ${#SEARCH_PATHS[@]} -eq 0 ]; then
  SEARCH_PATHS=(".")
fi

if command -v rg >/dev/null 2>&1; then
  rg -n "$PATTERN" "${SEARCH_PATHS[@]}"
  exit 0
fi

if command -v brew >/dev/null 2>&1; then
  brew install ripgrep
  rg -n "$PATTERN" "${SEARCH_PATHS[@]}"
  exit 0
fi

git grep -n -- "$PATTERN" "${SEARCH_PATHS[@]}"
