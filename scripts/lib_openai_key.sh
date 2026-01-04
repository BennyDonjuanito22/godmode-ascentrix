#!/usr/bin/env bash

# Shared helper to ensure OPENAI_API_KEY is available for God Mode scripts.

GODMODE_OPENAI_KEY_FILE_DEFAULT="$HOME/.config/godmode/openai_key"

load_openai_key() {
  local key_file="${GODMODE_OPENAI_KEY_FILE:-$GODMODE_OPENAI_KEY_FILE_DEFAULT}"
  if [[ -n "${OPENAI_API_KEY:-}" ]]; then
    return 0
  fi

  if [[ -f "$key_file" ]]; then
    OPENAI_API_KEY="$(head -n 1 "$key_file" | tr -d '[:space:]')"
    if [[ -z "$OPENAI_API_KEY" ]]; then
      echo "ERROR: $key_file exists but is empty. Add your OpenAI API key to the first line." >&2
      return 1
    fi
    export OPENAI_API_KEY
    echo "Loaded OPENAI_API_KEY from $key_file"
    return 0
  fi

  cat >&2 <<EOF
ERROR: OPENAI_API_KEY is not set.
Set it in your shell (export OPENAI_API_KEY=...) or place it in $key_file.
You can override the path with GODMODE_OPENAI_KEY_FILE.
EOF
  return 1
}
