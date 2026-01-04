"""Autopilot loop that keeps God Mode moving without human intervention."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass
try:  # Python 3.11+
    from datetime import UTC, datetime
except ImportError:  # pragma: no cover - fallback for Python 3.9
    from datetime import datetime, timezone

    UTC = timezone.utc
from pathlib import Path
from typing import Any, Dict, List, Optional
import shutil

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR.parent))

from api.agent_shell import (  # noqa: E402
    GodModeAgent,
    clear_agent_runtime_context,
    set_agent_runtime_context,
)
from api.brain_b import BrainB  # noqa: E402
from api.task_store import (  # noqa: E402
    TASKS_PATH,
    acquire_lock,
    load_tasks_unlocked,
    release_lock,
    save_tasks_unlocked,
    update_task_fields,
)
from godmode.agents.editor import EditorAgent  # noqa: E402
from godmode.blitz import notifications as blitz_notifications  # noqa: E402
from godmode.blitz import opportunities as blitz_opportunities  # noqa: E402
from godmode.blitz import strategy as blitz_strategy  # noqa: E402
from godmode.config import modes  # noqa: E402
from godmode.email import ingestion as email_ingestion  # noqa: E402
from godmode.human_help import reminders as human_reminders  # noqa: E402
from godmode.rnd import build_mode as rnd_build_mode  # noqa: E402
from godmode.rnd import pipeline as rnd_pipeline  # noqa: E402
from godmode.config import get_settings  # noqa: E402
from godmode.core.logging import configure_logging, get_logger  # noqa: E402

try:
    settings = get_settings()
except Exception as exc:  # pragma: no cover - defensive boot guard
    print(f"[autopilot] Failed to load settings: {exc}", file=sys.stderr)
    sys.exit(1)

configure_logging(service_name="autopilot", level=settings.log_level, environment=settings.environment)
LOGGER = get_logger(__name__)

REPO_ROOT = settings.repo_root
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LOG_DIR = settings.logs_dir / "autopilot_runs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR = REPO_ROOT / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
AUTOPILOT_HISTORY_PATH = MEMORY_DIR / "autopilot_history.jsonl"
REQUIRED_ENV_VARS = []

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

# Always-available tasks that keep the system moving when the backlog runs empty.
KEEPALIVE_TASKS = [
    {
        "name": "Backfill roadmap from design docs",
        "goal": (
            "When the backlog is empty, read docs/remaining_tasks.md, IMPLEMENTATION_STATUS.md, "
            "and design_docs/*.md to append at least 3 fresh pending tasks to api/tasks/roadmap.jsonl. "
            "Make sure new tasks have clear goals, agent types, and guardrails."
        ),
        "agent_type": "autopilot",
    },
    {
        "name": "System health + ledger sanity check",
        "goal": (
            "Run scripts/full_system_check.sh and scripts/check_ledger_health.py. "
            "Summarise findings and next steps in reports/godmode_status.md or "
            "docs/security_infra_audit_<date>.md so operators see the current state."
        ),
        "agent_type": "fixer",
    },
]

OPPORTUNITY_AGENT_MAP = {
    "affiliate_offer": "promoter",
    "service": "builder",
    "ecom": "builder",
    "content": "promoter",
}


def _agent_type_for_opportunity(source: str) -> str:
    return OPPORTUNITY_AGENT_MAP.get(str(source).lower(), "promoter")


def _ensure_keepalive_tasks(tasks: List[Dict[str, Any]]) -> bool:
    """When no pending tasks exist, seed a small keepalive backlog."""
    has_pending = any(task.get("status", "pending") == "pending" for task in tasks)
    if has_pending:
        return False

    try:
        max_id = max(int(task.get("id", 0)) for task in tasks)
    except ValueError:
        max_id = 0

    new_tasks: List[Dict[str, Any]] = []
    for idx, template in enumerate(KEEPALIVE_TASKS, start=1):
        task = dict(template)
        task.setdefault("status", "pending")
        task.setdefault("assigned_to", None)
        task.setdefault("attempts", 0)
        task.setdefault("last_result", None)
        task.setdefault("last_error", None)
        task.setdefault("updated_at", None)
        task["id"] = max_id + idx
        new_tasks.append(task)

    if new_tasks:
        LOGGER.info("Backfilling keepalive tasks because the backlog is empty.")
        tasks.extend(new_tasks)
        return True
    return False


def _ensure_blitz_opportunity_tasks(tasks: List[Dict[str, Any]], limit: int = 5) -> bool:
    """Ensure that the top Blitz opportunities exist as pending tasks."""
    blitz_opportunities.sync_funnels_to_opportunities()
    ranked = blitz_opportunities.list_blitz_ranked(limit=limit)
    if not ranked:
        return False

    existing_ids = {
        task.get("opportunity_id")
        for task in tasks
        if task.get("opportunity_id") is not None
    }
    dirty = False
    max_id = 0
    for task in tasks:
        try:
            max_id = max(max_id, int(task.get("id", 0)))
        except (TypeError, ValueError):
            continue

    for payload in ranked:
        opportunity_id = payload["id"]
        if opportunity_id in existing_ids:
            continue

        max_id += 1
        metadata = dict(payload.get("metadata", {}))
        description = metadata.get("description") or payload["label"]
        net = float(payload.get("estimated_net", 0.0))
        goal = (
            f"Deliver '{payload['label']}' before the Blitz deadline to capture at least "
            f"${net:,.0f} net. {description}"
        )
        task = {
            "id": max_id,
            "name": f"[BLITZ] {payload['label']}",
            "goal": goal,
            "agent_type": _agent_type_for_opportunity(payload.get("source", "")),
            "status": "pending",
            "priority": "urgent",
            "type": "blitz_campaign",
            "opportunity_id": opportunity_id,
            "blitz_score": payload.get("score", 0),
            "eta_hours": payload.get("expected_payout_hours"),
            "payout_channel": payload.get("expected_payout_channel"),
            "business_id": payload.get("business_id"),
            "tags": ["blitz", "opportunity"],
            "metadata": {"opportunity": payload},
        }
        tasks.append(task)
        existing_ids.add(opportunity_id)
        dirty = True
    return dirty


MAX_ATTEMPTS = 3
IDLE_SLEEP = 120
ERROR_SLEEP = 60
BETWEEN_TASK_SLEEP = 30


def update_task_status(task_id: Any, new_status: str, worker_id: str) -> None:
    """Public helper to update task status."""
    update_task_fields(task_id, worker_id, {"status": new_status, "assigned_to": worker_id})


def get_next_task(worker_id: str) -> Optional[Dict[str, Any]]:
    """Claim the next pending task for the current worker."""
    acquire_lock()
    try:
        tasks = load_tasks_unlocked()
        dirty = False
        if modes.is_blitz_mode():
            dirty = _ensure_blitz_opportunity_tasks(tasks)
        claimed_task: Optional[Dict[str, Any]] = None
        selected_task: Optional[Dict[str, Any]] = None
        dirty = _ensure_keepalive_tasks(tasks) or dirty
        if modes.is_blitz_mode():
            selected_task = blitz_strategy.select_task(tasks)
        if selected_task is None:
            for task in tasks:
                if task.get("status", "pending") == "pending":
                    selected_task = task
                    break
        if selected_task and selected_task.get("status") == "pending":
            selected_task["status"] = "in_progress"
            selected_task["assigned_to"] = worker_id
            claimed_task = dict(selected_task)
        if claimed_task or dirty:
            save_tasks_unlocked(tasks)
        return claimed_task
    finally:
        release_lock()


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _validate_runtime_env() -> bool:
    """Ensure critical environment variables exist before entering the main loop."""
    # Some env vars are only required for specific LLM backends (e.g. OpenAI).
    missing = [key for key in REQUIRED_ENV_VARS if not os.getenv(key)]
    # Enforce backend-specific requirements
    try:
        from api.agent_shell import _current_backend

        backend = _current_backend()
    except Exception:
        backend = os.getenv("LLM_BACKEND_DEFAULT", "openai").strip().lower()

    if backend == "openai" and not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")

    if not missing:
        return True

    msg = (
        "Autopilot cannot start: missing required environment variables: "
        f"{', '.join(sorted(set(missing)))}. Populate .env or export them before launching."
    )
    # Prefer stderr for visibility if logging is not yet configured.
    print(msg, file=sys.stderr)
    try:
        LOGGER.error(msg)
    except Exception:
        pass
    return False


@dataclass
class RoadmapTask:
    id: int
    name: str
    goal: str
    agent_type: str = "builder"
    status: str = "pending"
    assigned_to: Optional[str] = None
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
            "assigned_to": self.assigned_to,
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
            assigned_to=payload.get("assigned_to"),
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
        tasks: List[Dict[str, Any]] = []
        for item in DEFAULT_TASKS:
            task = dict(item)
            task.setdefault("status", "pending")
            task.setdefault("assigned_to", None)
            task.setdefault("attempts", 0)
            tasks.append(task)
        save_tasks_unlocked(tasks)

    def load(self) -> List[RoadmapTask]:
        return [RoadmapTask.from_json(task) for task in load_tasks_unlocked()]

    def save(self, tasks: List[RoadmapTask]) -> None:
        save_tasks_unlocked([task.to_json() for task in tasks])


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
        # Make history writes best-effort so they never crash the autopilot loop.
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")
        except Exception as exc:  # pragma: no cover - best effort
            LOGGER.exception("Failed to write autopilot history: %s", exc)
            # swallow error intentionally


class Autopilot:
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.logger = AutopilotLogger()
        self.store = RoadmapStore(TASKS_PATH)
        self.history = AutopilotHistory(AUTOPILOT_HISTORY_PATH)
        self.brain = BrainB(repo_root=os.fspath(self.repo_root))
        self.loop_count = 0
        self.store.ensure_seed()
        self.logger.log(f"Using tasks file: {TASKS_PATH}")
        self.ledger_min_pass = 0.9  # ledger health threshold to auto-apply cleaned file

    def _record_health_snapshot(self) -> None:
        """Record a lightweight task status summary for trending."""
        acquire_lock()
        try:
            tasks = load_tasks_unlocked()
        finally:
            release_lock()
        summary = {"pending": 0, "in_progress": 0, "done": 0, "blocked": 0, "failed": 0}
        for task in tasks:
            status = (task.get("status") or "").lower()
            if status in summary:
                summary[status] += 1
        snapshot = {
            "timestamp": _timestamp(),
            "type": "health_snapshot",
            "summary": summary,
        }
        try:  # pragma: no cover - best effort to avoid crashing loop
            self.history.record(snapshot)
        except Exception as exc:
            self.logger.log(f"Failed to record health snapshot: {exc}")
            LOGGER.exception("Failed to record health snapshot: %s", exc)

    def _parse_amount(self, value: Any) -> tuple[bool, float]:
        """Parse amounts like '1,234.56', '$1,234', '(1234)' -> (-1234.0)."""
        if isinstance(value, (int, float)):
            return True, float(value)
        s = str(value).strip()
        if not s:
            return False, 0.0
        negative = False
        if s.startswith("(") and s.endswith(")"):
            negative = True
            s = s[1:-1]
        s = re.sub(r"[^\d.\-]", "", s)
        try:
            v = float(s)
            if negative:
                v = -v
            return True, v
        except Exception:
            return False, 0.0

    def _check_ledger_health(self, apply_when_ok: bool = True, min_pass: Optional[float] = None) -> dict:
        """Validate and best-effort repair finance/ledger.jsonl. Returns summary."""
        min_pass = min_pass if min_pass is not None else self.ledger_min_pass
        ledger_path = REPO_ROOT / "finance" / "ledger.jsonl"
        summary = {
            "path": str(ledger_path),
            "total": 0,
            "valid": 0,
            "fixed": 0,
            "invalid": 0,
            "pass_rate": 0.0,
            "issues": {},
            "applied": False,
            "timestamp": _timestamp(),
        }
        if not ledger_path.exists():
            self.logger.log(f"Ledger not found at {ledger_path}. Skipping ledger health check.")
            return summary

        # read and validate
        cleaned: list[dict] = []
        with ledger_path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line:
                    continue
                summary["total"] += 1
                try:
                    obj = json.loads(line)
                except Exception:
                    summary["invalid"] += 1
                    summary["issues"].setdefault("unparseable_json", 0)
                    summary["issues"]["unparseable_json"] += 1
                    continue

                issues = []
                fixed = dict(obj)

                # timestamp
                ts = obj.get("timestamp")
                if not ts:
                    fixed["timestamp"] = _timestamp()
                    issues.append("added_timestamp")
                else:
                    try:
                        if isinstance(ts, str):
                            datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except Exception:
                        fixed["timestamp"] = _timestamp()
                        issues.append("fixed_timestamp")

                # amount
                ok_amt, parsed = self._parse_amount(obj.get("amount"))
                if not ok_amt:
                    issues.append("invalid_amount")
                else:
                    fixed["amount"] = parsed

                # currency
                if not obj.get("currency"):
                    fixed["currency"] = "USD"
                    issues.append("added_currency")

                # source/purpose heuristic
                if not obj.get("source") and not obj.get("purpose"):
                    issues.append("missing_source")

                # decide classification
                # treat entries with only added_timestamp/added_currency as valid/fixed
                non_trivial = [it for it in issues if it not in ("added_timestamp", "added_currency")]
                if not non_trivial:
                    # valid or minor-fixed
                    if issues:
                        summary["fixed"] += 1
                    else:
                        summary["valid"] += 1
                else:
                    # If amount is parseable we accept as fixed; otherwise mark invalid
                    if "invalid_amount" in non_trivial:
                        summary["invalid"] += 1
                    else:
                        summary["fixed"] += 1
                for it in set(issues):
                    summary["issues"].setdefault(it, 0)
                    summary["issues"][it] += 1
                cleaned.append(fixed)

        # compute pass rate
        total = summary["total"] or 1
        summary["pass_rate"] = (summary["valid"] + summary["fixed"]) / total

        # write cleaned file and backup original
        cleaned_path = ledger_path.with_name(ledger_path.stem + ".cleaned.jsonl")
        with cleaned_path.open("w", encoding="utf-8") as fh:
            for obj in cleaned:
                fh.write(json.dumps(obj, default=str) + "\n")

        backup_path = ledger_path.with_suffix(ledger_path.suffix + f".bak.{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}")
        try:
            shutil.copyfile(ledger_path, backup_path)
            self.logger.log(f"Ledger backup created: {backup_path}")
            summary["backup"] = str(backup_path)
        except Exception as exc:
            LOGGER.exception("Failed to back up ledger: %s", exc)
            summary["backup_error"] = str(exc)

        # apply cleaned ledger only if pass rate meets threshold and apply_when_ok True
        if apply_when_ok and summary["pass_rate"] >= float(min_pass):
            try:
                shutil.copyfile(cleaned_path, ledger_path)
                summary["applied"] = True
                self.logger.log(f"Applied cleaned ledger to {ledger_path} (pass_rate={summary['pass_rate']:.2%})")
            except Exception as exc:
                LOGGER.exception("Failed to apply cleaned ledger: %s", exc)
                summary["apply_error"] = str(exc)
        else:
            self.logger.log(
                f"Cleaned ledger written to {cleaned_path}; not applied (pass_rate={summary['pass_rate']:.2%}, threshold={min_pass:.2%})"
            )

        # record to history best-effort
        try:
            self.history.record(
                {
                    "timestamp": _timestamp(),
                    "type": "ledger_health_check",
                    "summary": summary,
                    "worker_loop": self.loop_count,
                }
            )
        except Exception:
            LOGGER.exception("Failed to record ledger health check to history.")

        return summary

    def run_forever(self, worker_id: str, idle_sleep: float) -> None:
        self.logger.log(f"Starting worker loop as {worker_id}.")
        while True:
            self.loop_count += 1
            # Wrap the full per-iteration work in a defensive try so a single unexpected
            # exception doesn't kill the autopilot process.
            try:
                email_ingestion.poll_code_inboxes()
                blitz_notifications.maybe_emit_hourly_update()
                human_reminders.maybe_send_reminders()
                try:
                    rnd_pipeline.orchestrate_top_ideas(limit=10)
                except Exception as exc:  # pragma: no cover - defensive
                    self.logger.log(f"R&D pipeline sync failed: {exc}")
                if self.loop_count % 10 == 0:
                    self._record_health_snapshot()
                try:
                    task = get_next_task(worker_id)
                except Exception as exc:  # pragma: no cover - defensive
                    self.logger.log(f"Worker {worker_id} unable to fetch task: {exc}")
                    time.sleep(ERROR_SLEEP)
                    continue

                if task is None:
                    self.logger.log(f"No pending tasks for {worker_id}. Sleeping {idle_sleep}s.")
                    time.sleep(idle_sleep)
                    continue

                try:
                    self.run_single_task(task, worker_id=worker_id)
                except Exception as exc:  # pragma: no cover - defensive
                    task_id = task.get("id")
                    self.logger.log(f"Worker {worker_id} fatal error on task {task_id}: {exc}")
                    update_task_fields(
                        task_id,
                        worker_id,
                        {
                            "status": "failed",
                            "last_error": f"{exc.__class__.__name__}: {exc}",
                            "updated_at": _timestamp(),
                        },
                    )
                    time.sleep(ERROR_SLEEP)
                    continue

                time.sleep(BETWEEN_TASK_SLEEP)

            except KeyboardInterrupt:
                # Allow graceful KeyboardInterrupt to propagate for normal shutdown.
                raise
            except Exception as exc:
                # Catch anything unexpected during an iteration, log and record to history,
                # then continue the loop after a short sleep so autopilot recovers automatically.
                err_msg = f"Unexpected autopilot loop error: {exc}"
                self.logger.log(err_msg)
                LOGGER.exception("Unexpected autopilot loop error: %s", exc)
                try:
                    self.history.record(
                        {
                            "timestamp": _timestamp(),
                            "type": "fatal_iteration_exception",
                            "error": err_msg,
                            "worker_id": worker_id,
                            "loop_count": self.loop_count,
                        }
                    )
                except Exception:
                    # already guarded in AutopilotHistory.record, but be extra defensive
                    LOGGER.exception("Failed to record iteration exception to history.")
                time.sleep(ERROR_SLEEP)
                continue

    def run_single_task(self, task: Dict[str, Any], worker_id: str) -> None:
        task_id = task.get("id")
        agent_type = task.get("agent_type", "builder")
        profile = AGENT_PROFILES.get(agent_type, AGENT_PROFILES["builder"])
        profile_guardrail = profile.get("guardrail", "")
        goal_text = task.get("goal", "")
        goal = (
            f"{goal_text.strip()}\n\n{AGENT_GUARDRAILS}\n\n"
            f"Agent profile ({agent_type}): {profile_guardrail}"
        )
        max_attempts = profile.get("max_attempts", MAX_ATTEMPTS)
        attempts = int(task.get("attempts", 0))

        if attempts >= max_attempts:
            updated_at = _timestamp()
            update_task_fields(
                task_id,
                worker_id,
                {
                    "status": "blocked",
                    "attempts": attempts,
                    "last_result": None,
                    "last_error": f"Max attempts reached ({attempts}/{max_attempts})",
                    "updated_at": updated_at,
                    "assigned_to": worker_id,
                },
            )
            self.logger.log(f"Task {task_id} blocked before run: max attempts reached.")
            return

        context_payload = {
            "task_id": task_id,
            "task_name": task.get("name"),
            "worker_id": worker_id,
            "business_id": task.get("business_id"),
        }
        set_agent_runtime_context(context_payload)
        self.logger.log(f"Worker {worker_id} running task {task_id}: {task.get('name')} [{agent_type}]")
        try:
            if agent_type == "editor":
                agent = EditorAgent(task=task, repo_root=os.fspath(self.repo_root))
                result = agent.run()
            else:
                agent = GodModeAgent(goal=goal, repo_root=os.fspath(self.repo_root))
                result = agent.run()
            attempts += 1
            updated_at = _timestamp()
            try:
                result_payload = json.dumps(result, default=str)
            except Exception:
                result_payload = str(result)
            update_task_fields(
                task_id,
                worker_id,
                {
                    "status": "done",
                    "attempts": attempts,
                    "last_result": result_payload,
                    "last_error": None,
                    "updated_at": updated_at,
                    "assigned_to": worker_id,
                },
            )
            task["type"] = task.get("type")
            task["metadata"] = task.get("metadata")
            rnd_build_mode.handle_task_completion(task)
            self.logger.log(f"Task {task_id} completed by {worker_id}.")
            try:
                self.history.record(
                    {
                        "timestamp": updated_at,
                        "task_id": task_id,
                        "agent_type": agent_type,
                        "status": "done",
                        "summary": str(result),
                        "worker_id": worker_id,
                        "mode": modes.get_current_mode(),
                    }
                )
            except Exception:
                # history.record is best-effort but guard in case of unexpected errors
                LOGGER.exception("Failed to record task completion to history for task %s", task_id)
        except Exception as exc:
            attempts += 1
            updated_at = _timestamp()
            error_msg = f"{exc.__class__.__name__}: {exc}"
            new_status = "blocked" if attempts >= max_attempts else "pending"
            assigned = None if new_status == "pending" else worker_id
            update_task_fields(
                task_id,
                worker_id,
                {
                    "status": new_status,
                    "attempts": attempts,
                    "last_result": None,
                    "last_error": error_msg,
                    "updated_at": updated_at,
                    "assigned_to": assigned,
                },
            )
            self.logger.log(
                f"Task {task_id} failed on worker {worker_id}: {error_msg} (status={new_status})"
            )
            try:
                self.history.record(
                    {
                        "timestamp": updated_at,
                        "task_id": task_id,
                        "agent_type": agent_type,
                        "status": new_status,
                        "error": error_msg,
                        "worker_id": worker_id,
                        "mode": modes.get_current_mode(),
                    }
                )
            except Exception:
                LOGGER.exception("Failed to record task failure to history for task %s", task_id)
            if new_status == "blocked":
                self.logger.log(f"Task {task_id} blocked after {attempts} attempts.")
                try:
                    note = f"Task {task_id} blocked after {attempts} attempts. Error: {error_msg}"
                    self.brain.memory_store(note, tags=["autopilot", "blocked_task"])
                except Exception:  # pragma: no cover - best effort
                    self.logger.log("Failed to store memory note for blocked task.")
        finally:
            clear_agent_runtime_context()


def main() -> None:
    parser = argparse.ArgumentParser(description="God Mode Autopilot")
    parser.add_argument(
        "--worker-id",
        type=str,
        default="worker_1",
        help="Logical worker identifier (e.g., worker_1, worker_2).",
    )
    parser.add_argument(
        "--idle-sleep-seconds",
        type=float,
        default=5.0,
        help="Seconds to sleep when no tasks are pending.",
    )
    args = parser.parse_args()

    if not _validate_runtime_env():
        sys.exit(1)

    autopilot = Autopilot(repo_root=REPO_ROOT)
    try:
        autopilot.run_forever(worker_id=args.worker_id, idle_sleep=args.idle_sleep_seconds)
    except KeyboardInterrupt:
        print("Autopilot interrupted by user.")
    except Exception as exc:
        LOGGER.exception("Autopilot terminated due to unexpected exception: %s", exc)
        print("Autopilot terminated due to an unexpected error. See logs for details.")


if __name__ == "__main__":
    main()
