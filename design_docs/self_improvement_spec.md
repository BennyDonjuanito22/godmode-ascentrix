

# God Mode Self-Improvement & Innovation Specification

## Purpose

Ensure the system can:

- Review its own logs, memory, and design docs.
- Detect gaps between “what exists” and “what the plan says should exist”.
- Create new tasks to improve itself and the businesses it runs.

## Sources of Truth

- Design docs: `design_docs/*.md`
- Tasks: `tasks/roadmap.jsonl` (or future DB).
- Agent logs: `logs/agent_runs/`.
- Autopilot logs: `logs/autopilot_runs/`.
- Notes: `memory/notes.jsonl`.

## Self-Review Behavior

A self-improvement or planner agent should periodically:

1. Read design_docs/*.md.
2. Sample recent logs and notes.
3. Compare planned capabilities vs current implementation.
4. Propose new tasks for:
   - Missing features.
   - UX/performance/security improvements.
   - New business experiments.

New tasks should be added to tasks/roadmap.jsonl with:
- status = "pending"
- clear, detailed goals for GodModeAgent

This creates a loop:
1) Execute tasks.
2) Log outcomes.
3) Self-review and generate new tasks.
4) Repeat.
