#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs/cron"
mkdir -p "${LOG_DIR}"

LIMIT="${NURTURE_LIMIT:-25}"

cd "${REPO_ROOT}"
python3 scripts/nurture_leads.py send --limit "${LIMIT}" >> "${LOG_DIR}/nurture.log" 2>&1
