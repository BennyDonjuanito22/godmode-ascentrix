#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/lib_openai_key.sh"
load_openai_key

cd "$HOME/ascentrix"
export OPENAI_API_KEY
docker compose -p godmode up -d autopilot
echo "Autopilot service is running (docker compose -p godmode logs -f autopilot to follow output)."
