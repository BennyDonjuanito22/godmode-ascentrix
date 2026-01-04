# OpenAI / ChatGPT (optional)

This repo runs local-first by default using an Ollama-compatible endpoint. OpenAI is optional and disabled by default to avoid accidental billing.

How to enable OpenAI/ChatGPT mode:

1. Install the OpenAI client in your Python environment:

   .venv311/bin/pip install openai

2. Set your OpenAI API key (securely in env or secret store):

   export OPENAI_API_KEY="sk-..."

3. Switch backend to OpenAI:

   export LLM_BACKEND_DEFAULT=openai

4. Start the API (example):

   .venv311/bin/python -m uvicorn api.app:app --host 127.0.0.1 --port 8000

Notes:
- The codebase will raise a clear error if OpenAI is not configured. The `api/agent_shell.py` file lazy-loads the OpenAI client.
- We remove `openai` from the default venv to prevent accidental remote calls; installing it and setting the key opt-in to OpenAI usage.
- To test without spending quota, use the local Ollama server at `OLLAMA_BASE_URL` (default `http://localhost:11434`).
