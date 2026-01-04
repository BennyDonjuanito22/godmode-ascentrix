"""HUD data providers backed by repo state."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from api.funnels import load_b1_funnel_config
from api.leads import list_leads
from api.ledger import iter_entries, summarize
from api.vector_memory import search_index

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TASKS_PATH = SCRIPT_DIR / "tasks" / "roadmap.jsonl"
PROMO_LOG_PATH = REPO_ROOT / "docs" / "b1_promo_log.md"
NOTES_PATH = REPO_ROOT / "memory" / "notes.jsonl"
AUTOPILOT_HISTORY_PATH = REPO_ROOT / "memory" / "autopilot_history.jsonl"
AGENT_RUNS_DIR = REPO_ROOT / "logs" / "agent_runs"
AUTOPILOT_RUNS_DIR = REPO_ROOT / "logs" / "autopilot_runs"


def _read_jsonl(path: Path, limit: int | None = None) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:] if limit else rows


def _ago(ts: str | None) -> str:
    if not ts:
        return "—"
    try:
        timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return ts
    delta = datetime.now(timezone.utc) - timestamp
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def _load_tasks() -> Dict[str, int]:
    stats = {"pending": 0, "running": 0, "done": 0, "blocked": 0}
    if not TASKS_PATH.exists():
        return stats
    with TASKS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            status = data.get("status", "pending")
            stats[status] = stats.get(status, 0) + 1
    stats["total"] = sum(stats.values())
    return stats


def _load_autopilot_status() -> Dict[str, Any]:
    history = _read_jsonl(AUTOPILOT_HISTORY_PATH, limit=1)
    if not history:
        return {"status": "idle", "task": None}
    entry = history[-1]
    task_name = f"Task {entry.get('task_id')}"
    return {
        "status": entry.get("status", "idle"),
        "task": {"id": entry.get("task_id"), "name": task_name},
        "agent_type": entry.get("agent_type"),
        "timestamp": entry.get("timestamp"),
    }


def _classify_lead(source: str, tag: str | None) -> str:
    tag = tag or ""
    if isinstance(tag, str) and tag.startswith("partner"):
        return "partner"
    source = (source or "").lower()
    if "affiliate" in source:
        return "affiliate"
    if "partner" in source:
        return "partner"
    return "landing"


def _lead_stats() -> Dict[str, int]:
    leads = list_leads()
    stats = {"landing": 0, "affiliate": 0, "partner": 0, "total": len(leads)}
    for lead in leads:
        lead_type = _classify_lead(lead.source, (lead.metadata or {}).get("tag"))
        stats[lead_type] = stats.get(lead_type, 0) + 1
    return stats


def _parse_promo_log() -> List[Dict[str, str]]:
    if not PROMO_LOG_PATH.exists():
        return []
    rows: List[Dict[str, str]] = []
    with PROMO_LOG_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line.startswith("|"):
                continue
            if "---" in line:
                continue
            cells = [col.strip() for col in line.strip("|").split("|")]
            if not cells or cells[0].lower().startswith("timestamp"):
                continue
            status = "scheduled"
            url = cells[2]
            if url and not url.startswith("("):
                status = "published"
            rows.append(
                {
                    "timestamp": cells[0],
                    "channel": cells[1],
                    "url": url,
                    "hook": cells[3],
                    "cta": cells[4],
                    "views": cells[5],
                    "ctr": cells[6],
                    "notes": cells[7],
                    "status": status,
                }
            )
    return rows


def _promo_summary(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    published = [row for row in rows if row["status"] == "published"]
    scheduled = [row for row in rows if row["status"] != "published"]
    latest = published[-1] if published else None
    next_item = scheduled[0] if scheduled else None
    return {
        "published": len(published),
        "scheduled": len(scheduled),
        "latest": latest,
        "next": next_item,
    }


def _recent_autopilot_history(limit: int = 5) -> List[Dict[str, Any]]:
    history = _read_jsonl(AUTOPILOT_HISTORY_PATH, limit=limit)
    history.reverse()
    return history


def _recent_notes(limit: int = 5) -> List[Dict[str, Any]]:
    notes = _read_jsonl(NOTES_PATH, limit=limit)
    formatted: List[Dict[str, Any]] = []
    for note in reversed(notes):
        text = note.get("text")
        if isinstance(text, dict):
            title = text.get("title") or ""
            content = text.get("content") or ""
            text = f"{title}\\n{content}".strip()
        formatted.append(
            {
                "ts": note.get("timestamp", ""),
                "tags": note.get("tags") or [],
                "text": text or "",
            }
        )
    return formatted


def _recent_logs(directory: Path, limit: int = 5) -> List[str]:
    if not directory.exists():
        return []
    files = sorted(directory.glob("*.log"))
    return [f.name for f in files[-limit:]]


def _sum_window(per_day: Dict[str, Dict[str, float]], days: int) -> float:
    total = 0.0
    today = datetime.now(timezone.utc).date()
    for offset in range(days):
        day = (today - timedelta(days=offset)).isoformat()
        total += per_day.get(day, {}).get("amount", 0.0)
    return total


def _build_agent_cards() -> List[Dict[str, Any]]:
    history = _recent_autopilot_history(limit=8)
    if not history:
        return [{"type": "builder", "goal": "Waiting for next task", "status": "idle", "duration": "—"}]
    cards = []
    for entry in history[:4]:
        cards.append(
            {
                "type": entry.get("agent_type", "agent"),
                "goal": f"Task {entry.get('task_id')}",
                "status": entry.get("status", "idle"),
                "duration": _ago(entry.get("timestamp")),
            }
        )
    return cards


def _alerts(config_cta: str, leads: Dict[str, int], promo: Dict[str, Any]) -> List[Dict[str, str]]:
    alerts: List[Dict[str, str]] = []
    if "test" in config_cta or "example" in config_cta:
        alerts.append(
            {"severity": "warn", "title": "CTA placeholder", "desc": "Swap the CTA URL with the production checkout link."}
        )
    if leads["total"] == 0:
        alerts.append(
            {"severity": "warn", "title": "Lead pipeline empty", "desc": "Capture at least one lead to verify automations."}
        )
    if promo["published"] == 0:
        alerts.append(
            {"severity": "error", "title": "No promo assets live", "desc": "Publish the queued TikTok/LinkedIn/email posts and update docs/b1_promo_log.md."}
        )
    return alerts


def hud_home() -> Dict[str, Any]:
    config = load_b1_funnel_config()
    revenue_summary = summarize(iter_entries())
    per_day = revenue_summary.get("per_day", {})
    today = time.strftime("%Y-%m-%d", time.gmtime())
    today_amount = per_day.get(today, {}).get("amount", 0.0)
    lead_stats = _lead_stats()
    promo_rows = _parse_promo_log()
    promo = _promo_summary(promo_rows)
    promo_snapshot = {
        "published": promo["published"],
        "scheduled": promo["scheduled"],
        "latest_url": (promo["latest"] or {}).get("url"),
        "next_hook": (promo["next"] or {}).get("hook"),
        "next_time": (promo["next"] or {}).get("timestamp"),
    }
    alerts = _alerts(config.cta_url, lead_stats, promo_snapshot)
    per_funnel = revenue_summary.get("per_funnel", {})
    streams = [
        {
            "name": "B1 Toolkit",
            "status": "live" if "gumroad" in config.cta_url else "queued",
            "trend": f"{promo_snapshot['scheduled']} promo(s) queued",
            "type": "digital",
            "revenue": round(per_funnel.get("B1", 0.0), 2),
        }
    ]
    return {
        "revenue": {
            "today": round(today_amount, 2),
            "d7": round(_sum_window(per_day, 7), 2),
            "d30": round(_sum_window(per_day, 30), 2),
            "delta": 0,
        },
        "streams": streams,
        "autopilot": _load_autopilot_status(),
        "tasks": _load_tasks(),
        "agents": _build_agent_cards(),
        "alerts": alerts,
        "leads": lead_stats,
        "promotions": promo_snapshot,
    }


def hud_streams() -> Dict[str, Any]:
    config = load_b1_funnel_config()
    revenue_summary = summarize(iter_entries())
    per_funnel = revenue_summary.get("per_funnel", {})
    promo_rows = _parse_promo_log()
    promo = _promo_summary(promo_rows)
    scheduled = [row for row in promo_rows if row["status"] != "published"][:5]
    lead_stats = _lead_stats()
    list_rows = [
        {
            "name": "B1 Toolkit",
            "type": "digital",
            "status": "live" if "gumroad" in config.cta_url else "queued",
            "owner": "builder",
            "revenue": round(per_funnel.get("B1", 0.0), 2),
            "traffic": ["TikTok", "Shorts", "LinkedIn", "Email"],
            "nextTask": (scheduled[0]["hook"] if scheduled else "Publish next promo"),
        },
        {
            "name": "B2 Holiday Micro-store",
            "type": "ecom",
            "status": "building",
            "owner": "builder",
            "revenue": 0,
            "traffic": ["Pinterest", "Email"],
            "nextTask": "Upload SKU mockups",
        },
        {
            "name": "B3 Content Engine",
            "type": "content",
            "status": "active",
            "owner": "researcher",
            "revenue": 0,
            "traffic": ["YouTube Shorts", "Threads"],
            "nextTask": "Schedule next hook batch",
        },
    ]
    detail = {
        "name": "B1 Toolkit",
        "offer": config.hero_subtitle,
        "icp": "Solopreneurs, creator agencies, automation freelancers",
        "urls": [
            "http://127.0.0.1:5051/funnels/b1/landing",
            config.cta_url,
        ],
        "notes": [
            f"Leads captured: {lead_stats['total']}",
            f"Promo calendar: {promo['scheduled']} queued",
        ],
        "metrics": {
            "conversion": f"{lead_stats['total']} captured",
            "ctr": "Pending real traffic",
            "cadence": f"{promo['published']} published / {promo['scheduled']} queued",
        },
    }
    queue = [
        {
            "id": idx + 1,
            "name": row["hook"],
            "status": row["status"],
            "timestamp": row["timestamp"],
        }
        for idx, row in enumerate(scheduled)
    ]
    return {"list": list_rows, "detail": detail, "queue": queue}


def hud_agents() -> Dict[str, Any]:
    history = _recent_autopilot_history(limit=5)
    latest_by_type: Dict[str, Dict[str, Any]] = {}
    for entry in history:
        agent_type = entry.get("agent_type")
        if agent_type and agent_type not in latest_by_type:
            latest_by_type[agent_type] = entry
    statuses = []
    for agent_type in ["builder", "fixer", "researcher", "promoter", "autopilot"]:
        entry = latest_by_type.get(agent_type)
        statuses.append(
            {
                "type": agent_type,
                "state": entry.get("status", "idle") if entry else "idle",
                "goal": f"Task {entry.get('task_id')}" if entry else "",
                "success": 100 if entry and entry.get("status") == "done" else 0,
                "lastRun": _ago(entry.get("timestamp")) if entry else "—",
            }
        )
    detail_history = [
        {
            "goal": f"Task {entry.get('task_id')} ({entry.get('agent_type')})",
            "status": entry.get("status", ""),
            "duration": _ago(entry.get("timestamp")),
        }
        for entry in history[:3]
    ]
    detail_notes = [entry.get("summary", "") for entry in history[:3] if entry.get("summary")]
    detail = {
        "type": detail_history[0]["goal"] if detail_history else "N/A",
        "history": detail_history,
        "notes": detail_notes or ["No recent notes logged."],
        "logSample": "See logs/autopilot_runs/ for detailed transcripts.",
    }
    return {"status": statuses, "detail": detail}


def hud_logs() -> Dict[str, Any]:
    return {
        "agent": _recent_logs(AGENT_RUNS_DIR),
        "autopilot": _recent_logs(AUTOPILOT_RUNS_DIR),
        "memory": _recent_notes(),
        "history": [
            {
                "id": entry.get("task_id"),
                "status": entry.get("status", ""),
                "summary": entry.get("summary") or f"{entry.get('agent_type')} run",
            }
            for entry in _recent_autopilot_history(limit=5)
        ],
    }


def hud_settings() -> Dict[str, Any]:
    config = load_b1_funnel_config()
    openai_status = "ok" if os.environ.get("OPENAI_API_KEY") or (Path.home() / ".config/godmode/openai_key").exists() else "missing"
    gumroad_status = "ok" if "gumroad.com" in config.cta_url else "pending"
    cron_path = REPO_ROOT / "config" / "cron" / "godmode.cron"
    maintenance = [
        {"name": "Cron jobs", "status": "ready" if cron_path.exists() else "missing", "detail": str(cron_path)},
        {"name": "Lead dashboard", "status": "automated", "detail": "scripts/lead_pipeline.py --output both"},
        {"name": "Nurture CLI", "status": "ready", "detail": "scripts/nurture_leads.py send --limit 25"},
    ]
    return {
        "goals": {"daily": 500, "weekly": 2500, "monthly": 12000, "focus": "B1 launch"},
        "integrations": [
            {"name": "OpenAI", "status": openai_status},
            {"name": "Gumroad CTA", "status": gumroad_status},
            {"name": "Qdrant", "status": "ok"},
        ],
        "streams": [
            {"name": "B1 Toolkit", "state": "live"},
            {"name": "B2 Micro-store", "state": "building"},
            {"name": "B3 Content Engine", "state": "active"},
        ],
        "maintenance": maintenance,
    }


def hud_autopilot_status() -> Dict[str, Any]:
    return _load_autopilot_status()
