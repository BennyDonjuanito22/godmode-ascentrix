# God Mode Roadmap

## Phase 0 – Infrastructure (Done / Maintain)

- Mac mini environment (Docker, Tailscale), `gmup` startup scripts.
- Core services: api, hud, postgres, redis, qdrant.
- `agent_shell.py` (tools + memory + logging) and `autopilot.py` (continuous runner).
- Operational scripts: `scripts/run_agent.sh`, `scripts/start_autopilot.sh`.

## Phase 1 – Design Docs *(Complete)*

- [x] `design_docs/godmode_overview.md`
- [x] `design_docs/dashboard_spec.md`
- [x] `design_docs/businesses_plan.md`

## Phase 2 – HUD Core *(Complete)*

- [x] Rebuilt HUD screens (Home, Streams, Agents, Logs/Memory, Settings) in `hud/index.html`.
- [x] Added `/hud/*` API endpoints (structured data + placeholders).
- [x] Documented canonical HUD strategy.

## Phase 3 – First Revenue Stream (B1) *(Complete)*

- [x] B1 landing endpoints (`/funnels/b1`, `/funnels/b1/landing`) + config file.
- [x] `docs/revenue_funnel_1.md` w/ customization steps.
- [x] Promo scripts/hooks tracked under funnel template + `docs/b1_promo_sprint.md`.

## Phase 4 – Financial Logging *(Complete)*

- [x] JSONL ledger (`finance/ledger.jsonl`) + API endpoints + CLI (`scripts/record_revenue.py`).
- [x] Health script (`scripts/check_ledger_health.py`) + fixer playbook.
- [x] HUD metrics fed by `/finance/summary`.

## Phase 5 – Additional Streams *(Complete)*

- [x] B2 ecommerce scaffolding (`businesses/b2_ecom_holiday/`).
- [x] B3 content pipeline research (`docs/b3_traffic_research.md`).
- [x] B4 AI service offer template (`businesses/b4_ai_service/`).

## Phase 6 – Memory & Intelligence *(In progress)*

- [x] JSONL vector memory + `/memory/*` endpoints + ingestion CLI.
- [ ] Upgrade to Qdrant + richer embeddings (requires future budget).

## Phase 7 – Scaling *(Planning)*

- [ ] Bootstrap scripts for new worker nodes.
- [ ] Multi-node task/log storage.
- [ ] Automated failover once redundant servers are funded.

Agents should use this roadmap plus `api/tasks/roadmap.jsonl` for step-by-step execution.

---

## Short-Term Focus (Weeks 1–6)

1. **Stabilize Autonomy** – provision real LLM/API keys, add smoke tests around agent runs, and wire HUD widgets to the live `/hud/*` endpoints.
2. **Execute Specialized Tasks** – close fixer (#12), researcher (#13), and promoter (#14) tasks to validate the new agent profiles.
3. **Instrument Revenue** – require every sale to hit `scripts/record_revenue.py`, surface rolling metrics in HUD, and use `scripts/check_ledger_health.py` after ledger-affecting commits.
4. **Security Hygiene** – rotate secrets into `.env`/secret stores, document incidents, and track risks in `design_docs/security_plan.md`.

## Long-Term Vision

- **Redundant Infrastructure** – replicate the stack across multiple regions/providers with automated backups and restore drills (`design_docs/infra_scaling_spec.md`).
- **Advanced Security** – move toward encrypted channels, hardened firewalls, and proactive intrusion monitoring; treat Telegram-level resilience as the north star.
- **Intelligence & Telemetry** – graduate to Qdrant embeddings and log pipelines that let autopilot reprioritize based on ROI.
- **Governance** – capture policies/legal docs once revenue grows to protect the operator and family.

## Meeting Cadence

| Frequency | Purpose | Notes |
| --- | --- | --- |
| Weekly | Security & infrastructure debrief | Review secrets, backups, incidents; output action items/tasks. |
| Bi-weekly | Product/expansion review | HUD status, revenue funnels, agent performance, backlog grooming. |
| Monthly | Strategic planning | Budget for infra/security upgrades, new markets, multi-node rollout. |

See `docs/operations_cadence.md` for agenda templates and note-taking guidance.

---

## AUTOGEN: Self-Improvement and Innovation Phase

- [ ] Add a recurring "Self-review: reconcile plans vs implementation" task to the roadmap/tasks.
- [ ] Implement a self-improvement planner agent goal that:
  - Reads all `design_docs/*.md`.
  - Samples recent logs from `logs/agent_runs/` and `logs/autopilot_runs/`.
  - Scans `memory/notes.jsonl` for lessons/patterns.
  - Creates new pending tasks for missing features, UX or reliability gaps, security work, and experiments.

This phase should run periodically so the system continuously closes the gap between plans and reality.
