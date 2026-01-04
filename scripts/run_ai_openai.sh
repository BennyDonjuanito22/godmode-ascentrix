#!/usr/bin/env bash
# Start the API using OpenAI (ChatGPT). Set OPENAI_API_KEY in env first.
# Usage: OPENAI_API_KEY=sk... ./scripts/run_ai_openai.sh
export LLM_BACKEND_DEFAULT=openai
if [ -z "$OPENAI_API_KEY" ]; then
  echo "ERROR: OPENAI_API_KEY not set"
  exit 1
fi
python3 api/app.py
