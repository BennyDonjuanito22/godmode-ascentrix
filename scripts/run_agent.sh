#!/usr/bin/env bash
set -euo pipefail

source "$(dirname "$0")/lib_openai_key.sh"
load_openai_key

cd "$HOME/ascentrix"
# Inside the 'api' container, the code lives directly under /srv,
# so we call the existing run_agent_entry.py there.
docker compose -p godmode exec -T -e OPENAI_API_KEY="$OPENAI_API_KEY" api python run_agent_entry.py
