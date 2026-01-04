"""Autopilot loop that keeps God Mode moving without human intervention."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_ROOT = os.environ.get("GODMODE_REPO_ROOT")
REPO_ROOT = Path(ENV_ROOT).resolve() if ENV_ROOT else SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.agent_shell import GodModeAgent  # noqa: E402

TASKS_DIR = SCRIPT_DIR / "tasks"
TASKS_PATH = TASKS_DIR / "roadmap.jsonl"
LOG_DIR = SCRIPT_DIR / "logs" / "autopilot_runs"
MEMORY_DIR = REPO_ROOT / "memory"
AUTOPILOT_HISTORY_PATH = MEMORY_DIR / "autopilot_history.jsonl"

AGENT_GUARDRAILS = (
    "Operational guardrails for every task:\n"
    "1. Inspect the repository and existing design docs before creating new files.\n"
    "2. Prefer editing the canonical HUD/API implementations instead of building duplicates.\n"
    "3. Double-check every change by re-reading modified files and summarising the result.\n"
    "4. Use store_note/search_notes aggressively so future runs retain context.\n"
    "5. When you touch revenue, infra, or memory features, update the relevant design_doc.\n"
)

AGENT_PROFILES = {
    "builder": {
        "guardrail": "Ship working code/docs tied to the goal. Write tests when possible and update relevant specs before finishing.",
        "max_attempts": 3,
    },
    "fixer": {
        "guardrail": "Diagnose regressions quickly. Limit scope to repairs, capture root cause, and verify fixes before closing.",
        "max_attempts": 2,
    },
    "researcher": {
        "guardrail": "Gather and summarize context. Avoid repo edits unless essential; store insights via store_note.",
        "max_attempts": 2,
    },
    "promoter": {
        "guardrail": "Focus on outreach/content. Do not modify backend systems; capture messaging variants and tracking links.",
        "max_attempts": 2,
    },
}

DEFAULT_TASKS = [
    {
        "id": 1,
        "name": "Doc: God Mode overview + architecture",
        "goal": (
            "Read the repository structure and any existing design docs. "
            "Create or refine 'design_docs/godmode_overview.md' so that it clearly describes the "
            "God Mode system, including: services (api, hud, postgres, redis, qdrant), agent runtime, "
            "memory, and autopilot. Add sections for: (1) overall mission, (2) technical architecture, "
            "(3) current capabilities, (4) planned capabilities. Use list_dir, read_file, write_file, "
            "search_design_docs, store_note, and search_notes as needed."
        ),
        "agent_type": "builder",
    },
    {
        "id": 2,
        "name": "Doc: Dashboard spec (HUD screens & features)",
        "goal": (
            "Design and document the God Mode dashboard (HUD) in 'design_docs/dashboard_spec.md'. "
            "Define screens for: Home/Overview, Streams/Businesses, Agents, Logs/Memory, and Settings. "
            "For each screen, list the key widgets, data sources, and actions. Ensure the spec can be "
            "used by a future agent run to implement or refine the HUD code."
        ),
        "agent_type": "builder",
    },
    {
        "id": 3,
        "name": "Doc: Businesses & money streams plan",
        "goal": (
            "Create or refine 'design_docs/businesses_plan.md' with a detailed plan for at least four "
            "initial money streams: (B1) affiliate/digital product funnel, (B2) ecommerce micro-store "
            "optimized for upcoming holidays, (B3) content-driven funnel (short-form content + link-in-bio), "
            "and (B4) service-style AI offer (e.g. AI content or lead-gen for clients). For each, describe "
            "the offer, target audience, traffic sources, and how God Mode will support and automate it."
        ),
        "agent_type": "builder",
    },
    {
        "id": 4,
        "name": "Implement core HUD screens from spec",
        "goal": (
            "Using 'design_docs/dashboard_spec.md', implement or refine the core HUD screens in the "
            "existing HUD/frontend code: Home/Overview, Streams/Businesses, Agents, and Logs/Memory. "
            "It is acceptable to use placeholder/static data as long as navigation and layout match the "
            "spec. Document which files you changed in the spec or in a new doc if needed."
        ),
        "agent_type": "builder",
    },
    {
        "id": 5,
        "name": "Implement first revenue funnel (B1)",
        "goal": (
            "Using 'design_docs/businesses_plan.md', implement a minimal version of the first revenue "
            "funnel (B1) inside this codebase. Create a simple landing page or endpoint, wired into the "
            "HUD/API, with a placeholder for an affiliate or product URL and basic copy. Document how to "
            "configure the real URL and change the copy in docs or comments."
        ),
        "agent_type": "builder",
    },
    {
        "id": 6,
        "name": "Implement minimal financial logging",
        "goal": (
            "Implement a minimal financial logging mechanism so that revenue per day and per funnel can "
            "be tracked. You may use a JSONL ledger under 'finance/ledger.jsonl' or a simple table in "
            "Postgres, whichever you can fully implement now. Provide a small script or API endpoint to "
            "append entries with timestamp, amount, currency, source/funnel, and notes, and document how "
            "to use it."
        ),
        "agent_type": "builder",
    },
]

MAX_ATTEMPTS = 3
IDLE_SLEEP = 120
ERROR_SLEEP = 60
BETWEEN_TASK_SLEEP = 30


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass
class RoadmapTask:
    id: int
    name: str
    goal: str
    agent_type: str = "builder"
    status: str = "pending"
    attempts: int = 0
    last_result: Optional[str] = None
    last_error: Optional[str] = None
    updated_at: Optional[str] = None

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "goal": self.goal,
            "agent_type": self.agent_type,
            "status": self.status,
            "attempts": self.attempts,
            "last_result": self.last_result,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_json(cls, payload: dict) -> "RoadmapTask":
        return cls(
            id=int(payload["id"]),
            name=payload.get("name", f"task-{payload['id']}"),
            goal=payload.get("goal", ""),
            status=payload.get("status", "pending"),
            agent_type=payload.get("agent_type", "builder"),
            attempts=int(payload.get("attempts", 0)),
            last_result=payload.get("last_result"),
            last_error=payload.get("last_error"),
            updated_at=payload.get("updated_at"),
        )


class RoadmapStore:
    def __init__(self, path: Path):
        self.path = path

    def ensure_seed(self) -> None:
        if self.path.exists():
            return
        tasks = [RoadmapTask.from_json(item) for item in DEFAULT_TASKS]
        self.save(tasks)

    def load(self) -> List[RoadmapTask]:
        tasks: List[RoadmapTask] = []
        if not self.path.exists():
            return tasks
        with open(self.path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    tasks.append(RoadmapTask.from_json(payload))
                except json.JSONDecodeError:
                    continue
        return tasks

    def save(self, tasks: List[RoadmapTask]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            for task in tasks:
                handle.write(json.dumps(task.to_json()) + "\n")


class AutopilotLogger:
    def __init__(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        self.log_path = LOG_DIR / f"autopilot_{self.run_id}.log"
        self.log("Autopilot booted.")

    def log(self, message: str) -> None:
        timestamp = datetime.now(UTC).isoformat()
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {message}\n")


class AutopilotHistory:
    def __init__(self, path: Path):
        self.path = path

    def record(self, payload: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")


class Autopilot:
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.logger = AutopilotLogger()
        self.store = RoadmapStore(TASKS_PATH)
        self.history = AutopilotHistory(AUTOPILOT_HISTORY_PATH)
        self.logger.log(f"Using tasks file: {TASKS_PATH}")

    def run_forever(self) -> None:
        self.store.ensure_seed()
        self.logger.log("Starting main loop.")
        while True:
            try:
                processed = self._process_next_task()
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.log(f"Fatal autopilot error: {exc}")
                time.sleep(ERROR_SLEEP)
                continue

            if not processed:
                self.logger.log("No pending tasks. Cooling down.")
                time.sleep(IDLE_SLEEP)
            else:
                time.sleep(BETWEEN_TASK_SLEEP)

    def _process_next_task(self) -> bool:
        tasks = self.store.load()
        task = next((t for t in tasks if t.status == "pending"), None)
        if not task:
            return False

        task.status = "running"
        task.updated_at = _timestamp()
        self.store.save(tasks)
        profile = AGENT_PROFILES.get(task.agent_type, AGENT_PROFILES["builder"])
        self.logger.log(f"Running task {task.id}: {task.name} [{task.agent_type}]")

        profile_guardrail = profile.get("guardrail", "")
        goal = (
            f"{task.goal.strip()}\n\n{AGENT_GUARDRAILS}\n\n"
            f"Agent profile ({task.agent_type}): {profile_guardrail}"
        )
        max_attempts = profile.get("max_attempts", MAX_ATTEMPTS)

        try:
            agent = GodModeAgent(goal=goal, repo_root=os.fspath(self.repo_root))
            result = agent.run()
            task.status = "done"
            task.attempts += 1
            task.last_result = str(result)
            task.last_error = None
            task.updated_at = _timestamp()
            self.logger.log(f"Task {task.id} completed.")
            self.history.record(
                {
                    "timestamp": task.updated_at,
                    "task_id": task.id,
                    "agent_type": task.agent_type,
                    "status": "done",
                    "summary": task.last_result,
                }
            )
        except Exception as exc:
            task.attempts += 1
            task.last_result = None
            task.last_error = f"{exc.__class__.__name__}: {exc}"
            task.status = "blocked" if task.attempts >= max_attempts else "pending"
            task.updated_at = _timestamp()
            self.logger.log(f"Task {task.id} failed: {task.last_error}")
            self.history.record(
                {
                    "timestamp": task.updated_at,
                    "task_id": task.id,
                    "agent_type": task.agent_type,
                    "status": task.status,
                    "error": task.last_error,
                }
            )

        self.store.save(tasks)
        return True


def main() -> None:
    autopilot = Autopilot(repo_root=REPO_ROOT)
    try:
        autopilot.run_forever()
    except KeyboardInterrupt:
        print("Autopilot interrupted by user.")


if __name__ == "__main__":
    main()
