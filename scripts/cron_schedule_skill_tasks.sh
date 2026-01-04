#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs/cron"
mkdir -p "${LOG_DIR}"

if [[ -f "${REPO_ROOT}/scripts/lib_openai_key.sh" ]]; then
  # shellcheck disable=SC1090
  source "${REPO_ROOT}/scripts/lib_openai_key.sh"
  load_openai_key || true
fi

cd "${REPO_ROOT}"
DATE="$(/bin/date +%F)"
python3 scripts/schedule_skill_tasks.py --date "${DATE}" >> "${LOG_DIR}/skill_tasks.log" 2>&1
