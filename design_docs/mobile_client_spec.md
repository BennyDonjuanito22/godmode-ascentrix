# God Mode Mobile Client (iPhone) Specification

## Purpose

- Give the operator a pocket view of:
  - Revenue (today / 7d / 30d)
  - Active streams
  - Agent status
  - Alerts / failures
- Allow basic controls:
  - Pause/resume streams
  - Pause/resume agents
  - Acknowledge alerts

The mobile client is a thin front-end over the existing HUD/API. It should **reuse the existing HUD/API structure wherever possible**. If the HUD is ever fully replaced, the mobile client should be updated to target the new canonical API.

## Navigation

- Home
- Streams
- Agents
- Alerts
- Settings

## Home Screen

- KPI cards:
  - Revenue today
  - Revenue last 7 days
  - Revenue this month
- Active streams:
  - Names + status (green/yellow/red)
- Quick actions:
  - “Pause all high-risk streams”
  - “View latest alerts”

## Streams Screen

- List view:
  - Name, type (B1–B4, etc.), status, last 7d revenue
- Detail view:
  - Description
  - Key URLs
  - Notes
  - Link to open in full HUD

## Agents Screen

- List:
  - Agent type, current/last task, status, last run time
- Detail:
  - Summary of last run
  - Link to full log in HUD

## Alerts Screen

- List of:
  - Failed tasks
  - Repeated errors
  - Revenue anomalies (future)
- Actions:
  - Mark alert as acknowledged
  - Open related stream/agent

## Settings

- Targets (day/week/month revenue)
- Stream priority/pauses
- Agent enable/disable toggles
- Device notification preferences

## Implementation Notes

- Phase 1:
  - Mobile app consumes existing HUD/API endpoints.
  - No direct database access from the client.
- Future:
  - Push notifications for alerts.
  - Deeper control over tasks/goals.

## AUTOGEN: Live Status and Task View (Mobile)

The iPhone client must include:

- A compact "Now Running" panel on the Home screen showing:
  - Current task name.
  - Status.
  - Elapsed time.
- A Tasks view (or section) listing:
  - Pending tasks.
  - Recently completed tasks.
  - Failed tasks with a short error summary.

The mobile app should consume the same task status API that the HUD uses and must
not duplicate business logic.
