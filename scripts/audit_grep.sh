#!/usr/bin/env bash
set -euo pipefail

PATTERN="${1:-TODO|FIXME|XXX}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"${SCRIPT_DIR}/rg_or_grep.sh" "$PATTERN" .
