#!/usr/bin/env python3
"""Append daily skill-practice tasks to api/tasks/roadmap.jsonl."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP_PATH = REPO_ROOT / "api" / "tasks" / "roadmap.jsonl"

AGENT_TASKS: List[Dict[str, str]] = [
    {
        "agent_type": "builder",
        "name": "Builder practice block",
        "goal": (
            "Follow design_docs/agent_continuous_learning.md -> build/run a kata, scan diffs for regressions, "
            "log results under reports/builder_practice_<date>.md. Reference design_docs/research_agent_playbook.md if research is needed."
        ),
    },
    {
        "agent_type": "fixer",
        "name": "Fixer practice block",
        "goal": (
            "Replay past incidents, run smoke tests (scripts/check_ledger_health.py, etc.), "
            "document findings under reports/fixer_practice_<date>.md per the continuous learning doc."
        ),
    },
    {
        "agent_type": "researcher",
        "name": "Researcher practice block",
        "goal": (
            "Pick a new market hypothesis, apply design_docs/research_agent_playbook.md workflow, "
            "log summary + sources in memory/notes.jsonl with tags ['research','practice']."
        ),
    },
    {
        "agent_type": "promoter",
        "name": "Promoter practice block",
        "goal": (
            "Draft 3 new hooks/copy variants, audit CTA performance, save outputs to content/output/b1/practice_<date>.md "
            "per design_docs/agent_continuous_learning.md."
        ),
    },
    {
        "agent_type": "autopilot",
        "name": "Autopilot coordinator practice",
        "goal": (
            "Review roadmap + security posture, simulate attacker mindset, ensure daily checklist from "
            "design_docs/agent_continuous_learning.md is followed. Log a short note in logs/autopilot_runs/."
        ),
    },
]


def load_tasks() -> List[Dict[str, str]]:
    if not ROADMAP_PATH.exists():
        return []
    tasks: List[Dict[str, str]] = []
    with ROADMAP_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            tasks.append(json.loads(line))
    return tasks


def write_tasks(tasks: List[Dict[str, str]]) -> None:
    with ROADMAP_PATH.open("w", encoding="utf-8") as handle:
        for task in tasks:
            handle.write(json.dumps(task) + "\n")


def next_id(tasks: List[Dict[str, str]]) -> int:
    return max(task.get("id", 0) for task in tasks) + 1 if tasks else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Schedule daily skill-practice tasks.")
    parser.add_argument("--date", help="YYYY-MM-DD (default: today)", default=dt.date.today().isoformat())
    args = parser.parse_args()

    tasks = load_tasks()
    current_ids = {task["id"] for task in tasks}
    base_id = next_id(tasks)

    day = args.date
    new_tasks: List[Dict[str, str]] = []
    for idx, template in enumerate(AGENT_TASKS):
        entry = {
            "id": base_id + idx,
            "name": f"{template['name']} – {day}",
            "goal": template["goal"],
            "agent_type": template["agent_type"],
            "status": "pending",
            "attempts": 0,
            "last_result": None,
            "last_error": None,
            "updated_at": None,
        }
        new_tasks.append(entry)

    tasks.extend(new_tasks)
    write_tasks(tasks)
    print(f"Scheduled {len(new_tasks)} practice tasks for {day}. IDs {base_id}-{base_id+len(new_tasks)-1}.")


if __name__ == "__main__":
    main()
