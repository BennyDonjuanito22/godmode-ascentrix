#!/usr/bin/env bash
# Start the API using a local LLM backend (ollama/ollama-compatible)
# Usage: ./scripts/run_ai_local.sh
export LLM_BACKEND_DEFAULT=ollama
export OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://localhost:11434}
python3 api/app.py
