# God Mode Desktop Client Specification (Mac / Windows)

## Purpose

- Provide a full-screen, focused version of the HUD.
- Make it feel like a “command center” app instead of just a browser tab.

The desktop client should primarily be a wrapper around the **existing HUD** (or its successor if replaced). Agents should **build on the current HUD implementation**, and only if a new HUD stack is chosen should they deprecate and remove the old one.

## Layout

- Left sidebar:
  - Home
  - Streams
  - Agents
  - Logs / Memory
  - Settings
- Main content:
  - Mirrors HUD screens from `dashboard_spec.md`.

## Home View

- Same widgets as HUD Home:
  - KPIs
  - Active streams summary
  - Agent activity
  - Alerts
- Extra:
  - System status:
    - Containers up/down
    - Autopilot status (running / idle)

## Streams View

- Table or cards:
  - Same as HUD Streams.
- Extra controls:
  - Buttons to:
    - Open in browser.
    - Mark stream as paused / active.
    - Open related docs or config.

## Agents View

- Same as HUD Agents.
- Extra:
  - Manual “kick” button to rerun specific agent goals (future).

## Logs / Memory View

- File browser for:
  - `logs/agent_runs/`
  - `logs/autopilot_runs/`
- Viewer for:
  - `memory/notes.jsonl` (with tag filters).

## Settings View

- Mirrors HUD Settings.
- Additional:
  - Local app settings (theme, refresh interval).
  - Quick link to open design docs in filesystem.

## Implementation Notes

- Phase 1:
  - Desktop client = Electron/Tauri wrapper around the existing HUD.
- Future:
  - Native OS notifications.
  - Offline-friendly log browsing.

## AUTOGEN: Live Overview (Desktop Client)

The desktop client should emphasize:

- A full "Command Center" live view:
  - Now running task + elapsed time.
  - Queue of pending tasks.
  - Recent tasks and their outcomes.
- Easy access to:
  - Agent logs.
  - Autopilot logs.
  - Design docs and notes.

It should mirror and extend the existing HUD functionality rather than implementing
separate, conflicting behavior.
