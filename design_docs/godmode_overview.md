# God Mode Overview

## Mission

God Mode is an autonomous, ever-expanding system designed to research, build, run, and improve multiple income streams with minimal human input. Its mandate:

- Launch durable, diversified businesses that can finance continued expansion.
- Continuously learn from results—every run should leave the repo better documented, better instrumented, and closer to profitability.
- Make replication trivial: any new machine can join the network, inherit memory, and begin executing the shared roadmap via a single command (`gmup`).
- Preserve operational context forever via aggressive memory capture and design documentation so the system can reason with near-total recall.

## Technical Architecture

### Core Services

- **api** – Python backend that now hosts the `GodModeAgent`, autopilot controller, TaskManager-backed FastAPI services, and soon the HUD/finance/vector-memory APIs.
- **hud** – Existing dashboard container that remains the canonical UI. Agents must enhance this HUD in-place unless a design doc explicitly approves a replacement.
- **postgres** – Canonical relational store for ledgers, task/state snapshots, and future HUD data.
- **redis** – In-memory cache/queueing layer reserved for high-throughput coordination.
- **qdrant** – Vector database dedicated to semantic memory (design docs, notes, logs). Not fully wired yet but already provisioned in infra.

### Agent Runtime (`api/agent_shell.py`)

The builder/fixer agent now runs with a hardened shell:

- **Tooling** – `list_dir`, `read_file`, `write_file`, `append_file`, `run_shell` (whitelisted), `git_status`, `git_commit`, `search_design_docs`, `search_repo`, `store_note`, `search_notes`, `recall_notes`.
- **Memory subsystem** – `MemoryStore` lazily caches `memory/notes.jsonl`, enforces append-only writes, and exposes latest/matching-note queries so the agent can recall prior context in milliseconds.
- **Guardrails** – System prompt mandates planning, verification after edits, and persistent note taking. Paths are validated to keep all operations within the repo root.
- **Logging** – Every step is streamed to `logs/agent_runs/agent_run_<timestamp>.log` for auditing/replay.

### Autopilot Orchestration (`api/autopilot.py`)

- Loads/maintains `tasks/roadmap.jsonl` as JSONL `RoadmapTask` objects with `status`, `attempts`, `last_result`, and `last_error`.
- Appends operational guardrails to every goal (double-check edits, touch HUD in place, update docs, etc.).
- Records every attempt outcome to `logs/autopilot_runs/` and a persistent ledger at `memory/autopilot_history.jsonl`, delivering permanent context for dashboards and future agent types.
- Applies retry policy (`MAX_ATTEMPTS`) and re-queues blocked tasks instead of looping endlessly on failures like invalid API keys.

### Task Services (`api/app.py`, `api/agent_engine.py`, `api/task_engine.py`)

All FastAPI worker surfaces now depend on `api/task_runtime.TaskManager` for:

- Thread-safe queueing with resumable history files.
- Graceful startup/shutdown hooks that spawn background workers.
- Consistent payload/response structures so HUD and automation scripts can introspect job state.

### Memory & Knowledge Layers

- **File memory** – `memory/notes.jsonl` remains the high-speed recall log, now backed by `MemoryStore`.
- **Vector memory (planned)** – Qdrant ingestion pipeline will ingest design docs, notes, and logs, with recall endpoints exposed through the API. See `design_docs/implementation_blueprint.md` for the upcoming spec.
- **Autopilot history** – Separate JSONL ledger ensures we can reconstruct roadmap outcomes and feed dashboards/analytics without parsing raw logs.

### Multilingual + Multi-Agent Vision

Beyond the current repo, God Mode grows into a multilingual, memory-augmented platform:

- **LLM core** – high-parameter multilingual transformer with long-context attention (FlashAttention) and optional language-aware MoE experts. See `design_docs/multilingual_platform_blueprint.md` for data/training plans.
- **Hierarchical memory** – parametric weights + short-term buffer + persistent vector store + knowledge graph, orchestrated by a memory manager that embeds new data, performs hybrid retrieval, and periodically summarizes old memories.
- **Agent mesh** – orchestrator dispatches work to persistent/dynamic agents (memory manager, reasoning, automation, critic, learning, interface). Agents communicate via a structured message bus and use planner–executor–verifier loops with a shared skill registry.
- **Tool ecosystem** – registry-driven integrations (search, analytics, CRM, payments, automation) so agents can execute end-to-end workflows.

## Current Capabilities

- `gmup` boots the stack; `./scripts/run_agent.sh` and `./scripts/start_autopilot.sh` run targeted workflows.
- GodModeAgent enforces repository-safe edits, structured logging, and durable note capture.
- Autopilot continuously works through the roadmap with guardrails and writes outcomes to memory.
- Task APIs share the same runtime, so HUD or external callers can schedule background jobs reliably.
- Design docs cover architecture, businesses, dashboards, infra scaling, etc., giving the agent rich context.

## Planned Capabilities

- HUD surfaces wired to live data: task snapshots, autopilot backlog, memory summaries, financial metrics.
- Fully automated revenue funnels (B1–B4) using reusable templates, each tracked via a financial ledger (JSONL or Postgres).
- Vector memory ingestion + recall API so agents can semantically search design docs/logs.
- Autopilot expansions for specialized agents (builder/fixer/researcher/promoter) with tailored prompts and retry logic.
- Observability layer (structured logs/metrics) plus automated backups and replication scripts for new nodes.
- Multilingual core LLM + multi-agent deployment as described in `design_docs/multilingual_platform_blueprint.md`, including cross-lingual alignment, RAG, and tool integrations.

## Files & Conventions

- **Design docs** – `design_docs/*.md` (overview, dashboard spec, business plans, blueprint, etc.).
- **Agent code** – `api/agent_shell.py`.
- **Autopilot** – `api/autopilot.py`.
- **Roadmap** – `api/tasks/roadmap.jsonl` (seeded automatically if missing).
- **Task services** – `api/app.py`, `api/agent_engine.py`, `api/task_engine.py`, with shared runtime in `api/task_runtime.py`.
- **Logs** – `logs/agent_runs/` for agent traces, `api/logs/autopilot_runs/` for autopilot loops.
- **Memory** – `memory/notes.jsonl` (short-form recall) and `memory/autopilot_history.jsonl` (roadmap ledger).

## HUD Strategy (Still Canonical)

The existing HUD container remains the default interface:

- Extend/refactor it before considering replacements.
- If a new implementation is ever approved, mark the old HUD as deprecated, archive unused components, and ensure the new UI covers Home, Streams/Businesses, Agents, Logs/Memory, and Settings views.
