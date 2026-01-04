

# God Mode Live Status & Progress Specification

## Purpose

Provide a clear, real-time view of what the system is doing so the operator can see:

- Which tasks are queued, running, done, or failed.
- Which agents are active right now.
- How long tasks are taking and rough ETAs.
- A “now running” view without reading raw logs.

This spec applies to the existing HUD, and any future desktop/mobile clients must expose equivalent live status views.

## Concepts

### Task

A task is an entry from `tasks/roadmap.jsonl` (or future DB):

- `id`
- `name`
- `status` (pending, running, done, failed)
- `goal`
- `last_result`
- `last_error`
- `started_at` (UTC timestamp, when status first switched to running)
- `finished_at` (UTC timestamp, when status switched to done/failed)
- `duration_sec` (numeric, finished_at - started_at)

### Agent Run

- Single execution of `GodModeAgent.run()` for a given task.
- Logged in `logs/agent_runs/`.

## HUD / Client Requirements

- Home:
  - Now Running widget.
  - Task summary widget.
- Streams:
  - Tasks related to each stream (optional).
- Agents:
  - Show which agent is working on which task.
- Logs/Memory:
  - Provide links to relevant logs when viewing tasks.

Agents implementing HUD/clients should add these views incrementally.
