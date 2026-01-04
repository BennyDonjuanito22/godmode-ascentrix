# God Mode Dashboard (HUD) Specification

## Purpose

The HUD is the human-facing control center for God Mode. It must give operators immediate visibility into revenue, stream health, agent progress, logs/memory, and high-level configuration while staying tightly coupled to the existing HUD container. Agents should **extend the current HUD** unless stakeholders explicitly approve a wholesale replacement.

---

## Navigation & Global Layout

- **Primary navigation**: Home/Overview, Streams/Businesses, Agents, Logs/Memory, Settings.
- **Global header**: Persistent “Autopilot Status” pill (Idle/Running/Blocked) with task id/name + elapsed timer, plus quick links to run scripts (`run_agent`, `start_autopilot`).
- **Notifications drawer**: Consolidated feed of alerts (failed tasks, missing API keys, ledger gaps, stale data).

---

## Screen Specifications

Each screen lists mandatory widgets, data sources (planned API endpoints), and key actions.

### 1. Home / Overview

| Widget | Data Source | Details / Actions |
| --- | --- | --- |
| **Revenue Summary** | `GET /hud/metrics/revenue` (reads `finance/ledger.jsonl` or Postgres ledger) | Show Today / 7-day / 30-day totals with % deltas vs prior period. Currency toggle, tooltip linking to ledger write instructions. |
| **Active Streams Pulse** | `GET /hud/streams/summary` (business registry + ledger) | Card list: Name, Type (affiliate/ecom/content/service), Status (planned/building/live/paused), sparkline for 7-day revenue trend, link to stream detail. |
| **Autopilot Now Running** | `GET /hud/autopilot/status` (parses `api/tasks/roadmap.jsonl` + `memory/autopilot_history.jsonl`) | Task id/name/goal excerpt, attempt count, elapsed duration timer, CTA to open task history or rerun. |
| **Tasks Summary** | `GET /hud/tasks/summary` | Counts for pending/running/done/blocked. Each chip navigates to Streams (for build tasks) or Agents (for runtime tasks). |
| **Recent Agent Activity** | `GET /hud/agents/recent` (metadata from `logs/agent_runs/`) | Table of last 5 runs: agent type, goal snippet, duration, exit status, link to log viewer. |
| **Alerts Panel** | `GET /hud/alerts` (aggregated) | Show severity, title, description, and “Resolve” link (e.g., open Settings > Integrations). Alerts include: missing OPENAI key, ledger >24h stale, autopilot blocked, HUD API errors. |

### 2. Streams / Businesses

#### Streams Table

- Columns: Name, Type, Status, Owner agent, Last 7-day revenue, Primary traffic sources (tags), Next task ETA.
- Filters: Status (planned/building/live/paused), Type, search.
- Actions: “Add stream” (opens modal referencing `businesses/` template), “Open detail”, “Pause/resume”.
- Data: `GET /hud/streams` (combines `design_docs/businesses_plan.md`, `businesses/*`, ledger stats).

#### Stream Detail Drawer

- **Overview**: Offer description, ICP, funnel diagram (text/markdown), key URLs (landing page, checkout, analytics dashboards).
- **Performance**: Charts built from `GET /hud/streams/<id>/revenue` + `GET /hud/streams/<id>/traffic`.
- **Operational Tasks**: Pulls roadmap tasks tagged with stream id (`api/tasks/roadmap.jsonl`) plus autopilot history entries.
- **Notes & Memory**: `GET /hud/notes?tag=stream:<id>` shows latest notes; allow inline note creation that calls `store_note`.
- **Automation hooks**: Show connected services (email provider, storefront, ad APIs) and credential status (from Settings).

#### Queue View Integration

- Embedded list of pending tasks filtered for the stream, built from `GET /hud/tasks/pending?stream_id=<id>` with priority/attempt badges.

### 3. Agents

#### Agents Grid

- Tiles per agent type (builder, autopilot, fixer, researcher, promoter). Each tile shows:
  - Status (Idle/Running/Blocked), last goal, last run timestamp, average duration, success rate.
  - Controls: “Open log”, “Restart”, “Disable” (where supported).
- Data: `GET /hud/agents/status` combining autopilot state + parsed log metadata.

#### Agent Detail Panel

- Timeline chart of last N runs with color-coded outcomes (done/failed/blocked).
- Log viewer (tail of the latest `logs/agent_runs/*.log` or autopilot log) with search + download.
- Notes captured during runs (`GET /hud/notes?agent_type=builder` etc.).
- Error diagnostics: show recent stack traces, missing secrets, or environment warnings pulled from log parsing.

### 4. Logs / Memory

- **Logs Browser**:
  - Tabs: Agent Logs, Autopilot Logs.
  - Each list item: filename, timestamp, run duration, status, size. Clicking opens modal viewer with syntax highlighting, search, and copy-to-clipboard.
  - Actions: download, delete (if necessary) with confirmation.
  - Data: `GET /hud/logs/agent`, `GET /hud/logs/autopilot`.

- **Memory Search**:
  - Query bar hitting `GET /hud/memory/search?query=...` (wraps `search_notes`; future: vector search fallback).
  - Results show timestamp, tags, excerpt, associated task/stream (if tagged). Provide “View related task” button.
  - Allow creating new notes from HUD via POST endpoint.

- **Autopilot History Timeline**:
  - Derived from `memory/autopilot_history.jsonl`.
  - Visual timeline with entries color-coded by status (done/blocked). Clicking reveals summary, error (if any), attempt count, and link to roadmap entry.

### 5. Settings

- **Goals & Targets**:
  - Inputs for target revenue (daily/weekly/monthly) and OKRs. Persist to config store (JSON or Postgres table). Expose via `GET/PUT /hud/settings/goals`.

- **Stream Controls**:
  - Toggles to pause/resume each stream; updating toggles should mark roadmap tasks accordingly (e.g., set status `paused`). Endpoint: `PATCH /hud/streams/<id>/state`.

- **Agent Controls**:
  - Enable/disable agent types; adjust concurrency limits; configure guardrail presets. Endpoint: `PUT /hud/settings/agents`.

- **Integrations & Secrets**:
  - Read-only table of required credentials (OpenAI, Stripe, storefront, ad platforms). Show location (`.env`, AWS Secrets Manager), last rotated date, and button linking to docs on updating secrets.

- **System Maintenance**:
  - Buttons to trigger smoke tests, snapshot backups, log bundle downloads. Each calls POST endpoints that run scripts via TaskManager.

---

## Implementation Notes

- HUD frontend should consume REST endpoints added to `api/app.py` under `/hud/*`. Until backend wiring is complete, components may use stub data with clear TODOs referencing these endpoints.
- Polling cadence:
  - `Autopilot Now Running` and `Tasks Summary`: every 10 seconds.
  - Revenue/stream metrics: on load + manual refresh.
  - Alerts: every 30 seconds or via WebSocket/event stream when available.
- Charting: reuse the HUD’s existing design system. Favor lightweight sparkline/bar components over heavy libraries unless already bundled.
- Empty states: every widget must explain how to populate missing data (e.g., “No ledger entries yet – run `scripts/record_revenue.py`”).
- Accessibility: ensure colorblind-safe status colors (prefer icon + label).
- Telemetry: log HUD interactions (view detail, run smoke test) so future automation can learn which surfaces need attention.

---

## Existing HUD vs New Implementation

- **Default**: extend/refactor the existing HUD codebase.
- **If replacement occurs**: mark old HUD as deprecated, remove dead code, update docs/configs to point to new implementation, and ensure feature parity across Home, Streams, Agents, Logs/Memory, and Settings views.

---

## Live Status, Queues, and Timers (AUTOGEN Requirement)

HUD must expose:

1. **Now Running widget** – already specified above; must show duration timer and live updates.
2. **Tasks Summary widget** – counts from roadmap, clickable.
3. **Queue View** – pending roadmap tasks sorted by priority/id with metadata (started_at, duration_sec when available).

Agents should pull started/finished timestamps from roadmap entries or augment the task schema to include them. When data is missing, stub sensible defaults and note the gaps in the docs so future agents can implement the backend support.
