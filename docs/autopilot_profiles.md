# Autopilot Agent Profiles

Autopilot now schedules different agent personas depending on the task’s `agent_type`. Each profile injects extra guardrails and uses its own retry policy, so future roadmap entries must set `agent_type` appropriately.

| Agent Type | Purpose | Guardrails | Max Attempts |
| --- | --- | --- | --- |
| builder | Ship new features/docs | Focus on working code, update specs, verify changes | 3 |
| fixer | Repair regressions | Diagnose quickly, limit scope to fixes, capture root cause | 2 |
| researcher | Gather context | Prioritize investigation + notes, avoid repo edits unless essential | 2 |
| promoter | Outreach & launches | Work on messaging/content only, track links/hooks, no backend edits | 2 |

## Usage

- Roadmap tasks (`api/tasks/roadmap.jsonl`) include `"agent_type": "<profile>"`.
- During execution, autopilot appends the profile-specific guardrail text to the goal, and enforces the profile’s max retry count before marking the task blocked.
- Autopilot history now records the `agent_type`, enabling HUD or analytics to filter by persona.

## Adding Profiles

To introduce a new agent type:

1. Extend `AGENT_PROFILES` in `api/autopilot.py` with the guardrail text and `max_attempts`.
2. Update docs (this file) with a short description.
3. Assign the new `agent_type` to roadmap tasks.
