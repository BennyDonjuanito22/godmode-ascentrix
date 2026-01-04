# Agent Continuous Learning Framework

Goal: keep every autonomous agent sharp by reserving daily time for skill practice, security checks, and knowledge ingestion. This document defines the cadence and the tooling (see `scripts/schedule_skill_tasks.py`).

## Daily Cadence (per agent type)
| Agent | Practice Block | Security & QA | Knowledge Build | Output |
| --- | --- | --- | --- | --- |
| Builder | 1h – code kata / refactor exercise (pick from `/playground/katas`) | 30m – diff scan for regressions | 30m – read spec updates (`design_docs/*`) | `reports/builder_practice_<date>.md` |
| Fixer | 45m – replay past incidents, simulate fixes | 45m – run smoke scripts (`scripts/check_ledger_health.py`, etc.) | 30m – read security advisories | `reports/fixer_practice_<date>.md` |
| Researcher | 1h – new market sweep (follow Research Playbook) | 15m – validate cached sources still accurate | 45m – absorb notebooks/papers | `memory/notes.jsonl` entry + log |
| Promoter | 1h – create new hooks/copy variants | 30m – audit CTA performance | 30m – study platform algorithm notes | `content/output/<stream>/practice_<date>.md` |
| Autopilot Coordinator | 30m – run task-plan retro | 30m – security/self-test (simulate attacker mindset) | 30m – review design_docs roadmap updates | `logs/autopilot_runs/` note |

## Mechanism
1. `scripts/schedule_skill_tasks.py` appends daily practice tasks (one per agent type) to `api/tasks/roadmap.jsonl` with unique IDs + ISO date.
2. Autopilot picks them up like any other task, ensuring every day includes non-revenue skill work.
3. Each practice task references:
   - This document for cadence.
   - `design_docs/research_agent_playbook.md` for R&D loops.
   - Katas/notes folder for exercises.
4. Outputs (reports or notes) saved under `/reports/` (or respective folders) to create a time series of improvements.

## Usage
- Run `python3 scripts/schedule_skill_tasks.py --date YYYY-MM-DD` to generate tasks for that day (default = today).
- Schedule the script via cron/Launchd to run every midnight so the roadmap is restocked automatically.
- Autopilot logs should reflect practice results; manually review weekly to adjust focus areas.

## Future Enhancements
- Add performance scoring to each practice output to quantify improvement.
- Tie into HUD (Settings > Agent Controls) so operators can adjust practice durations per agent type.
- Expand kata library (`playground/katas/`) for builders/fixers.
