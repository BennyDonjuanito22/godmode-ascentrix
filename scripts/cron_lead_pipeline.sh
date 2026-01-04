#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs/cron"
mkdir -p "${LOG_DIR}"

cd "${REPO_ROOT}"
python3 scripts/lead_pipeline.py --output both >> "${LOG_DIR}/lead_pipeline.log" 2>&1
