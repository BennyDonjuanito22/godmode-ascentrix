# God Mode Implementation Blueprint

This blueprint captures the remaining surface area required for a functional
`v1.0` of the God Mode network.  It distills the long‑form design explorations
into a practical build plan the autonomous agents can execute iteratively.

---

## 1. Baseline Snapshot

- **Agent runtime** – `api/agent_shell.py` now provides deterministic guardrails,
  improved file/memory tools (search_repo, append_file, recall_notes), and richer
  logging.  It must remain the canonical command surface for the builder agent.
- **Autopilot** – `api/autopilot.py` owns roadmap orchestration, persists results,
  and records every outcome to `memory/autopilot_history.jsonl`.
- **Task services** – `api/app.py`, `api/agent_engine.py`, and `api/task_engine.py`
  all share the same `TaskManager`, ensuring queuing and persistence work the
  same way everywhere.
- **Design docs** – Strategy docs exist but several areas (memory backend, HUD
  data plumbing, finance logging) still need concrete technical specs.

---

## 2. Remaining Build Areas

### 2.1 Memory & Knowledge Stack

- **Vector memory** – Stand up Qdrant (already referenced in infra) and create a
  `memory/vector_store.py` module that can ingest design docs, logs, and notes.
- **Recall API** – Expose a FastAPI endpoint for semantic search so HUD + agents
  can request summaries or nearest notes by tag/topic.
- **Note hygiene** – Implement automated compaction/archiving of `notes.jsonl`
  into monthly files once entries exceed ~5k lines to keep file‑based recall fast.

### 2.2 HUD & Control Plane

- **Data wiring** – HUD must read from the shared task ledger, the financial
  ledger, and the vector memory summaries.  Define a `/hud` API namespace in
  `api/app.py` that delivers pre-aggregated JSON for each dashboard view.
- **Agent console** – Add a panel that visualises autopilot backlog, in-flight
  tasks, and failure reasons (sourced from `tasks/roadmap.jsonl` and the new
  `autopilot_history` file).
- **Settings & credentials** – Centralise API keys/secrets in an encrypted file
  or vault service and surface redacted metadata in HUD so humans know which
  integrations are configured.

### 2.3 Revenue Streams & Automations

- **Funnel templates** – Create a `/funnels` package with reusable assets
  (copy, layouts, automation scripts).  Each stream (B1‑B4) should live under
  `businesses/<stream_id>/` with README + deploy instructions.
- **Traffic monitors** – Add lightweight scrapers or API hooks for the chosen
  ad platforms/content sources so HUD can show live traffic + CPA numbers.
- **Financial ledger** – Implement `finance/ledger.jsonl` writer + reader APIs
  with CLI helpers (`scripts/record_revenue.py`).  Ledger entries must include
  timestamps, amounts, funnels, and memo fields.

### 2.4 Operational Autonomy

- **Agent specialisation** – Extend autopilot to schedule different agent types
  (builder, fixer, researcher, promoter) with their own guardrail presets.
- **Feedback loop** – After each run, automatically open a follow-up task when a
  change introduces errors (parse git status/test failures, attach to roadmap).
- **Environment replication** – Author a `docs/replication.md` guide plus
  automation scripts to bootstrap new nodes with identical configs + secrets.

### 2.5 Data & Infrastructure

- **Observability** – Emit structured logs (JSON) and basic metrics (Prometheus
  or StatsD) from every FastAPI service so uptime + throughput are visible.
- **Database migrations** – Establish Alembic (or similar) migrations for
  Postgres, covering task history tables, financial ledger tables, and HUD data.
- **Backups** – Automate nightly backups for Postgres, Qdrant, and the `memory`
  folder.  Track backup status inside HUD + autopilot logs.

---

## 3. Execution Playbook

1. **Stabilise runtime services** – Finish wiring HUD APIs, confirm task APIs,
   and add smoke tests that run inside CI.
2. **Ship memory upgrades** – Implement vector store ingestion + recall API,
   then teach the agent shell new tools to hit the service before editing.
3. **Deliver first funnel (B1)** – Build the landing page, connect to ledger,
   and surface metrics inside HUD.
4. **Automate QA & rollback** – Teach autopilot to open remediation tasks when
   tests/logs flag regressions, and wire `scripts/run_agent.sh` to run sanity
   checks post-edit.
5. **Expand to remaining streams (B2‑B4)** – Use the reusable funnel template
   package so each launch is mostly configuration + copy updates.

---

## 4. Immediate Agent Tasks

1. Create the vector memory ingestion pipeline (docs + code stub).
2. Add HUD API endpoints for tasks, revenue, and memory summaries.
3. Implement `finance/ledger.jsonl` writer + CLI helper.
4. Document the funnel template structure (`businesses/README.md`).
5. Extend autopilot to support specialised worker types + retries per type.

Once these are complete, the system will have a cohesive end-to-end spine,
unlocking the remainder of the roadmap with far less thrash.
