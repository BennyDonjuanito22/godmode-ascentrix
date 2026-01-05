"""HUD data providers backed by repo state with operational guardrails."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from api import accounting, llm_metrics, password_vault
from godmode.accounts import registry as account_registry
from godmode.business import landing_pages
from godmode.funnels import config as funnel_config
from godmode.offers import registry as offer_registry
from api.funnels import load_b1_funnel_config
from api.leads import list_leads
from api.ledger import iter_entries, summarize
from api.task_store import load_tasks_unlocked
from api.vector_memory import search_index
from godmode.blitz import income_tracker
from godmode.config import modes, get_settings
from godmode.rnd import ideas as rnd_ideas

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TASKS_PATH = SCRIPT_DIR / "tasks" / "roadmap.jsonl"
PROMO_LOG_PATH = REPO_ROOT / "docs" / "b1_promo_log.md"
NOTES_PATH = REPO_ROOT / "memory" / "notes.jsonl"
AUTOPILOT_HISTORY_PATH = REPO_ROOT / "memory" / "autopilot_history.jsonl"
AGENT_RUNS_DIR = REPO_ROOT / "logs" / "agent_runs"
AUTOPILOT_RUNS_DIR = REPO_ROOT / "logs" / "autopilot_runs"
REPORTS_DIR = REPO_ROOT / "reports"
PORTFOLIO_PATH = REPO_ROOT / "data" / "portfolio_states.json"
BUSINESS_CHAT_DIR = REPO_ROOT / "data" / "business_chats"


def _parse_iso_timestamp(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _autopilot_history() -> List[Dict[str, Any]]:
    return _read_jsonl(AUTOPILOT_HISTORY_PATH)


def _autopilot_metrics(window_hours: int = 24) -> Dict[str, Any]:
    rows = _autopilot_history()
    if not rows:
        return {"window_hours": window_hours, "total": 0, "success_rate": 0.0, "last_run": None, "online": False}
    cutoff = datetime.now(timezone.utc).timestamp() - (window_hours * 3600)
    filtered = [row for row in rows if _parse_iso_timestamp(row.get("timestamp")) >= cutoff]
    total = len(filtered)
    if total == 0:
        return {"window_hours": window_hours, "total": 0, "success_rate": 0.0, "last_run": None, "online": False}
    done = sum(1 for row in filtered if row.get("status") == "done")
    success_rate = round((done / total) * 100, 1)
    last_run = filtered[-1].get("timestamp")
    last_ts = _parse_iso_timestamp(last_run)
    online = (datetime.now(timezone.utc).timestamp() - last_ts) < 15 * 60 if last_ts else False
    return {"window_hours": window_hours, "total": total, "success_rate": success_rate, "last_run": last_run, "online": online}


def _historical_durations() -> Dict[str, float]:
    """Compute average task durations from autopilot history."""
    rows = _autopilot_history()
    start_times: Dict[str, float] = {}
    durations_by_name: Dict[str, List[float]] = {}
    durations_by_agent: Dict[str, List[float]] = {}
    for row in rows:
        task_id = row.get("task_id")
        task_key = str(task_id) if task_id is not None else None
        status = (row.get("status") or "").lower()
        ts = _parse_iso_timestamp(row.get("timestamp"))
        name = str(row.get("task_name") or row.get("name") or "")
        agent = str(row.get("agent_type") or "")
        if status in {"in_progress", "running"} and task_key:
            start_times[task_key] = ts
        if status in {"done", "failed", "blocked"} and task_key:
            start = start_times.get(task_key)
            if start and ts > start:
                duration = ts - start
                if name:
                    durations_by_name.setdefault(name, []).append(duration)
                if agent:
                    durations_by_agent.setdefault(agent, []).append(duration)
    def _median(values: List[float]) -> float:
        if not values:
            return 0.0
        values = sorted(values)
        mid = len(values) // 2
        if len(values) % 2 == 1:
            return values[mid]
        return (values[mid - 1] + values[mid]) / 2

    medians: Dict[str, float] = {}
    for name, durations in durations_by_name.items():
        medians[f"name:{name}"] = _median(durations)
    for agent, durations in durations_by_agent.items():
        medians[f"agent:{agent}"] = _median(durations)
    return medians


def _autopilot_trend(days: int = 7) -> List[Dict[str, Any]]:
    rows = _autopilot_history()
    if not rows:
        return []
    buckets: Dict[str, Dict[str, int]] = {}
    for row in rows:
        ts = _parse_iso_timestamp(row.get("timestamp"))
        if not ts:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        buckets.setdefault(day, {"total": 0, "done": 0})
        buckets[day]["total"] += 1
        if row.get("status") == "done":
            buckets[day]["done"] += 1
    days_list = sorted(buckets.keys())[-days:]
    output = []
    for day in days_list:
        total = buckets[day]["total"]
        done = buckets[day]["done"]
        success_rate = round((done / total) * 100, 1) if total else 0.0
        output.append({"day": day, "total": total, "done": done, "success_rate": success_rate})
    return output


def _load_portfolio_states() -> Dict[str, Any]:
    if not PORTFOLIO_PATH.exists():
        return {"generated_at": None, "states": {}}
    try:
        return json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Failed to load portfolio states: {exc}")
        return {"generated_at": None, "states": {}}


def _business_chat_path(business_id: str) -> Path:
    BUSINESS_CHAT_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = business_id.replace("/", "_")
    return BUSINESS_CHAT_DIR / f"{safe_id}.jsonl"


def _load_business_chat(business_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    path = _business_chat_path(business_id)
    if not path.exists():
        return []
    rows = _read_jsonl(path)
    return rows[-limit:]


def _append_business_chat(business_id: str, role: str, text: str) -> Dict[str, Any]:
    path = _business_chat_path(business_id)
    entry = {
        "role": role,
        "text": text,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    return entry


def _urgency_score(text: str) -> int:
    text = text.lower()
    score = 0
    revenue_terms = ["revenue", "sale", "checkout", "payment", "offer", "cta", "funnel", "pricing", "promo", "ads", "marketing", "conversion"]
    data_terms = ["ledger", "sync", "sales", "audience", "tracking", "email", "retarget"]
    infra_terms = ["infra", "backup", "health", "monitoring", "scale", "vector", "qdrant", "security"]
    docs_terms = ["doc", "documentation", "spec", "overview", "plan", "notes", "practice"]
    for term in revenue_terms:
        if term in text:
            score += 12
    for term in data_terms:
        if term in text:
            score += 6
    for term in infra_terms:
        if term in text:
            score += 2
    for term in docs_terms:
        if term in text:
            score -= 4
    return max(score, 0)

logger = logging.getLogger(__name__)


def _read_jsonl(path: Path, limit: int | None = None) -> List[Dict[str, Any]]:
    try:
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return []
        rows: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in {path} line: {line} error: {e}")
                    continue
        return rows[-limit:] if limit else rows
    except Exception as e:
        logger.error(f"Failed to read JSONL file {path}: {e}")
        return []


def _ago(ts: str | None) -> str:
    if not ts:
        return "—"
    try:
        timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        logger.warning(f"Invalid timestamp format: {ts}")
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
    try:
        if not TASKS_PATH.exists():
            logger.warning(f"Tasks file not found: {TASKS_PATH}")
            return stats
        with TASKS_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    status = data.get("status", "pending")
                    stats[status] = stats.get(status, 0) + 1
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in tasks file line: {line} error: {e}")
                    continue
        stats["total"] = sum(stats.values())
        return stats
    except Exception as e:
        logger.error(f"Failed to load tasks from {TASKS_PATH}: {e}")
        return stats


def _load_autopilot_status() -> Dict[str, Any]:
    try:
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
    except Exception as e:
        logger.error(f"Failed to load autopilot status: {e}")
        return {"status": "error", "task": None}


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
    try:
        leads = list_leads()
        stats = {"landing": 0, "affiliate": 0, "partner": 0, "total": len(leads)}
        for lead in leads:
            lead_type = _classify_lead(lead.source, (lead.metadata or {}).get("tag"))
            stats[lead_type] = stats.get(lead_type, 0) + 1
        return stats
    except Exception as e:
        logger.error(f"Failed to load lead stats: {e}")
        return {"landing": 0, "affiliate": 0, "partner": 0, "total": 0}


def _parse_promo_log() -> List[Dict[str, str]]:
    try:
        if not PROMO_LOG_PATH.exists():
            logger.warning(f"Promo log file not found: {PROMO_LOG_PATH}")
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
    except Exception as e:
        logger.error(f"Failed to parse promo log: {e}")
        return []


def _promo_summary(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    try:
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
    except Exception as e:
        logger.error(f"Failed to summarize promo data: {e}")
        return {"published": 0, "scheduled": 0, "latest": None, "next": None}


def _recent_autopilot_history(limit: int = 5) -> List[Dict[str, Any]]:
    try:
        history = _read_jsonl(AUTOPILOT_HISTORY_PATH, limit=limit)
        history.reverse()
        return history
    except Exception as e:
        logger.error(f"Failed to load recent autopilot history: {e}")
        return []


def _recent_notes(limit: int = 5) -> List[Dict[str, Any]]:
    try:
        notes = _read_jsonl(NOTES_PATH, limit=limit)
        formatted: List[Dict[str, Any]] = []
        for note in reversed(notes):
            text = note.get("text")
            if isinstance(text, dict):
                title = text.get("title") or ""
                content = text.get("content") or ""
                text = f"{title}\n{content}".strip()
            formatted.append(
                {
                    "ts": note.get("timestamp", ""),
                    "tags": note.get("tags") or [],
                    "text": text or "",
                }
            )
        return formatted
    except Exception as e:
        logger.error(f"Failed to load recent notes: {e}")
        return []


def _recent_logs(directory: Path, limit: int = 5) -> List[str]:
    try:
        if not directory.exists():
            logger.warning(f"Logs directory not found: {directory}")
            return []
        files = sorted(directory.glob("*.log"))
        return [f.name for f in files[-limit:]]
    except Exception as e:
        logger.error(f"Failed to load recent logs from {directory}: {e}")
        return []


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


from api.accounting import business_snapshot_enhanced

# Modify _business_snapshots to use business_snapshot_enhanced with error handling

def _business_snapshots() -> List[Dict[str, Any]]:
    try:
        records = accounting.list_businesses()
        snapshots = []
        for record in records:
            snapshot = accounting.business_snapshot_enhanced(record)
            business_id = snapshot.get("id") or record.id
            email_accounts = account_registry.get_accounts_for_business(business_id, account_type="email")
            primary_email = email_accounts[0].to_dict() if email_accounts else None
            pages = [page.to_dict() for page in landing_pages.list_pages_for_business(business_id)]
            funnels = []
            for funnel in funnel_config.list_funnels_for_business(business_id):
                entry = funnel.to_dict()
                offer = offer_registry.get_offer(funnel.offer_id)
                if offer:
                    entry["offer_name"] = offer.name
                    entry["offer_platform"] = offer.platform
                funnels.append(entry)
            snapshot["email_account"] = primary_email
            snapshot["landing_pages"] = pages
            snapshot["funnels"] = funnels
            snapshots.append(snapshot)
        if not snapshots:
            config = load_b1_funnel_config()
            snapshots.append(
                {
                    "id": "b1",
                    "name": "B1 Toolkit",
                    "slug": "b1_toolkit",
                    "status": "live" if "pay.godmode" in (config.cta_url or "") else "queued",
                    "kind": "digital",
                    "cta_url": config.cta_url,
                    "instant_payout": "pay.godmode" in (config.cta_url or ""),
                    "revenue": 0,
                    "last_sale": None,
                    "recent_buyers": 0,
                    "tags": ["b1"],
                    "mock_data": False,
                }
            )
        return snapshots
    except Exception as e:
        logger.error(f"Failed to load business snapshots: {e}")
        return []


def _group_businesses(businesses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    idea_map: Dict[str, str] = {}
    try:
        for idea in rnd_ideas.list_ideas():
            business_id = str((idea.metadata or {}).get("business_id") or "")
            if business_id:
                idea_map[business_id] = idea.category
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for business in businesses:
            biz_id = str(business.get("id"))
            category = idea_map.get(biz_id) or (business.get("tags") or ["general"])[0] or "general"
            groups.setdefault(category, []).append(business)
        for category, rows in groups.items():
            rows.sort(key=lambda item: item.get("name", ""))
        return groups
    except Exception as e:
        logger.error(f"Failed to group businesses: {e}")
        return {}


def hud_home() -> Dict[str, Any]:
    try:
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
        config = load_b1_funnel_config()
        alerts = _alerts(config.cta_url, lead_stats, promo_snapshot)
        business_cards = _business_snapshots()
        business_groups = _group_businesses(business_cards)
        blitz_status = income_tracker.get_blitz_income_summary() if modes.is_blitz_mode() else None
        vault_entries = [entry.to_dict() for entry in password_vault.list_entries()[:5]]
        autopilot_metrics = _autopilot_metrics()
        portfolio = _load_portfolio_states()
        return {
            "mode": modes.get_current_mode(),
            "revenue": {
                "today": round(today_amount, 2),
                "d7": round(_sum_window(per_day, 7), 2),
                "d30": round(_sum_window(per_day, 30), 2),
                "delta": 0,
            },
            "streams": business_cards,
            "business_groups": business_groups,
            "autopilot": _load_autopilot_status(),
            "tasks": _load_tasks(),
            "agents": _build_agent_cards(),
            "alerts": alerts,
            "leads": lead_stats,
            "promotions": promo_snapshot,
            "vault": vault_entries,
            "blitz": blitz_status,
            "autopilot_metrics": autopilot_metrics,
            "portfolio": portfolio,
        }
    except Exception as e:
        logger.error(f"Failed to build hud_home data: {e}")
        return {}


def hud_llm_usage() -> Dict[str, Any]:
    """
    Aggregate recent LLM usage so the HUD can display backend/model stats.
    """
    try:
        return llm_metrics.summarize(window_minutes=24 * 60)
    except Exception as e:  # pragma: no cover - defensive
        logger.error(f"Failed to build LLM analytics: {e}")
        return {"totals": {"count": 0, "errors": 0, "avg_latency_ms": 0}, "by_backend": [], "by_model": [], "latest_ts": None}


def hud_streams() -> Dict[str, Any]:
    try:
        businesses = _business_snapshots()
        promo_rows = _parse_promo_log()
        scheduled = [row for row in promo_rows if row["status"] != "published"][:5]
        lead_stats = _lead_stats()
        if not businesses:
            logger.warning("No businesses found for hud_streams")
            return {"list": [], "detail": {}, "queue": []}
        detail_business = businesses[0]
        primary_url = detail_business.get("cta_url")
        landing_urls = [
            f"/landing/{page.get('slug')}"
            for page in detail_business.get("landing_pages", [])
            if page.get("slug")
        ]
        urls = [url for url in [primary_url] + landing_urls if url]
        detail = {
            "name": detail_business["name"],
            "offer": detail_business.get("cta_url") or "See business config",
            "icp": ", ".join(detail_business.get("tags") or []) or "Pending ICP",
            "urls": urls,
            "notes": [
                f"Leads captured: {lead_stats['total']}",
                f"Queue: {len(scheduled)} scheduled promos",
            ],
            "metrics": {
                "conversion": f"{detail_business.get('recent_buyers', 0)} buyers",
                "ctr": "Pending traffic instrumentation",
                "cadence": f"{len(promo_rows)} logged promos",
            },
            "email": detail_business.get("email_account"),
            "landing_pages": detail_business.get("landing_pages", []),
            "funnels": detail_business.get("funnels", []),
            "business_id": detail_business.get("id"),
            "slug": detail_business.get("slug"),
        }
        queue = [
            {"id": idx + 1, "name": row["hook"], "status": row["status"], "timestamp": row["timestamp"]}
            for idx, row in enumerate(scheduled)
        ]
        return {"list": businesses, "detail": detail, "queue": queue}
    except Exception as e:
        logger.error(f"Failed to build hud_streams data: {e}")
        return {"list": [], "detail": {}, "queue": []}


def hud_agents() -> Dict[str, Any]:
    try:
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
    except Exception as e:
        logger.error(f"Failed to build hud_agents data: {e}")
        return {"status": [], "detail": {}}


def hud_logs() -> Dict[str, Any]:
    try:
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
    except Exception as e:
        logger.error(f"Failed to build hud_logs data: {e}")
        return {"agent": [], "autopilot": [], "memory": [], "history": []}


def hud_settings() -> Dict[str, Any]:
    try:
        config = load_b1_funnel_config()
        settings = get_settings()
        openai_status = "ok" if settings.integrations.openai_api_key else "missing"
        cta_status = "ok" if config.cta_url else "pending"
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
                {"name": "Primary CTA", "status": cta_status},
                {"name": "Qdrant", "status": "ok"},
            ],
            "streams": [
                {"name": "B1 Toolkit", "state": "live"},
                {"name": "B2 Micro-store", "state": "building"},
                {"name": "B3 Content Engine", "state": "active"},
            ],
            "maintenance": maintenance,
        }
    except Exception as e:
        logger.error(f"Failed to build hud_settings data: {e}")
        return {}


def hud_autopilot_status() -> Dict[str, Any]:
    return _load_autopilot_status()

# Enhancements to _business_snapshots to mark mock data, zero balances, and align CTAs with instant-pay links

def _business_snapshots() -> List[Dict[str, Any]]:
    try:
        records = accounting.list_businesses()
        snapshots = []
        for record in records:
            snapshot = accounting.business_snapshot_enhanced(record)
            business_id = snapshot.get("id") or record.id
            email_accounts = account_registry.get_accounts_for_business(business_id, account_type="email")
            primary_email = email_accounts[0].to_dict() if email_accounts else None
            pages = [page.to_dict() for page in landing_pages.list_pages_for_business(business_id)]
            funnels = []
            for funnel in funnel_config.list_funnels_for_business(business_id):
                entry = funnel.to_dict()
                offer = offer_registry.get_offer(funnel.offer_id)
                if offer:
                    entry["offer_name"] = offer.name
                    entry["offer_platform"] = offer.platform
                funnels.append(entry)
            # Ensure zero balances when keys missing
            revenue = snapshot.get("revenue") or 0
            last_sale = snapshot.get("last_sale")
            recent_buyers = snapshot.get("recent_buyers") or 0
            # Mark mock data if no real revenue or no email accounts
            mock_data = False
            if revenue == 0 and not email_accounts:
                mock_data = True
            # Align CTA with instant-pay links
            cta_url = snapshot.get("cta_url") or ""
            instant_payout = "pay.godmode" in cta_url
            # Update snapshot with these fields
            snapshot.update({
                "email_account": primary_email,
                "landing_pages": pages,
                "funnels": funnels,
                "revenue": revenue,
                "last_sale": last_sale,
                "recent_buyers": recent_buyers,
                "mock_data": mock_data,
                "instant_payout": instant_payout,
            })
            snapshots.append(snapshot)
        # If no businesses, add default B1 Toolkit with mock_data flag
        if not snapshots:
            config = load_b1_funnel_config()
            snapshots.append(
                {
                    "id": "b1",
                    "name": "B1 Toolkit",
                    "slug": "b1_toolkit",
                    "status": "live" if "pay.godmode" in (config.cta_url or "") else "queued",
                    "kind": "digital",
                    "cta_url": config.cta_url,
                    "instant_payout": "pay.godmode" in (config.cta_url or ""),
                    "revenue": 0,
                    "last_sale": None,
                    "recent_buyers": 0,
                    "tags": ["b1"],
                    "mock_data": True,
                }
            )
        return snapshots
    except Exception as e:
        logger.error(f"Failed to load business snapshots: {e}")
        return []


def hud_memory_search(query: str, limit: int = 5) -> dict:
    """Perform a vector search on memory notes and return top results."""
    try:
        if not query:
            return {"query": query, "results": []}
        results = search_index(query, limit=limit)
        # Format results for HUD consumption
        formatted = []
        for res in results:
            formatted.append({
                "id": res.get("id"),
                "score": res.get("score"),
                "text": res.get("text"),
                "metadata": res.get("metadata", {}),
            })
        return {"query": query, "results": formatted}
    except Exception as e:
        logger.error(f"Failed to perform memory vector search: {e}")
        return {"query": query, "results": [], "error": str(e)}


def _latest_channel_summary() -> Dict[str, Any]:
    """Load the most recent channel summary report if present."""
    try:
        if not REPORTS_DIR.exists():
            return {}
        summaries = sorted(REPORTS_DIR.glob("channel_summary_*.json"))
        if not summaries:
            return {}
        latest = summaries[-1]
        with latest.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Failed to load channel summary: {exc}")
        return {}


def hud_channel_summary() -> Dict[str, Any]:
    summary = _latest_channel_summary()
    return {"summary": summary, "generated_at": summary.get("generated_at")} if summary else {"summary": {}, "generated_at": None}


def hud_master_checklist() -> Dict[str, Any]:
    data_path = REPO_ROOT / "data" / "master_checklist.json"
    try:
        if not data_path.exists():
            return {"generated_at": None, "core_items": [], "blueprints": []}
        return json.loads(data_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Failed to load master checklist: {exc}")
        return {"generated_at": None, "core_items": [], "blueprints": []}

def _work_queue_rows(tasks: List[Dict[str, Any]], limit: int = 12) -> List[Dict[str, Any]]:
    duration_cache = _historical_durations()

    def progress_for(status: str) -> int:
        status = (status or "").lower()
        if status == "done":
            return 100
        if status in {"in_progress", "running"}:
            return 55
        if status == "waiting_on_human":
            return 20
        if status == "blocked":
            return 5
        return 0

    def eta_for(task: Dict[str, Any]) -> str:
        status = (task.get("status") or "").lower()
        if status == "done":
            return "0m"
        if status == "waiting_on_human":
            return "pending human"
        if status == "blocked":
            return "blocked"
        name_key = f"name:{task.get('name') or ''}"
        agent_key = f"agent:{task.get('agent_type') or ''}"
        avg = duration_cache.get(name_key) or duration_cache.get(agent_key) or 3600
        updated_at = _parse_iso_timestamp(task.get("updated_at"))
        elapsed = max(0, datetime.now(timezone.utc).timestamp() - updated_at) if updated_at else 0
        remaining = max(300, avg - elapsed) if avg else 3600
        return f"~{int(remaining // 60)}m"

    def urgency_for(task: Dict[str, Any]) -> int:
        text = f"{task.get('name','')} {task.get('goal','')}"
        return _urgency_score(text)

    def score(task: Dict[str, Any]) -> tuple:
        status = (task.get("status") or "").lower()
        priority = {"in_progress": 0, "running": 0, "pending": 1, "waiting_on_human": 2, "blocked": 3, "done": 4}
        updated = task.get("updated_at") or ""
        urgency = urgency_for(task)
        return (priority.get(status, 5), -urgency, updated)

    ordered = sorted(tasks, key=score)
    rows = []
    for task in ordered[:limit]:
        status = task.get("status") or "pending"
        rows.append(
            {
                "id": task.get("id"),
                "name": task.get("name") or task.get("goal") or "Untitled task",
                "status": status,
                "progress": progress_for(status),
                "eta": eta_for(task),
                "urgency": urgency_for(task),
                "blocked_by": task.get("blocked_by_request_id"),
                "agent_type": task.get("agent_type"),
            }
        )
    return rows


def hud_work_queue(limit: int = 12) -> Dict[str, Any]:
    """Return a live work queue with rough progress/ETA estimates."""
    tasks = load_tasks_unlocked()
    if not tasks:
        return {"tasks": []}
    return {"tasks": _work_queue_rows(tasks, limit=limit)}


def hud_business_queue(business_id: str, limit: int = 12) -> Dict[str, Any]:
    """Return a per-business work queue filtered by business_id."""
    tasks = [task for task in load_tasks_unlocked() if str(task.get("business_id") or "") == str(business_id)]
    if not tasks:
        return {"business_id": business_id, "tasks": []}
    return {"business_id": business_id, "tasks": _work_queue_rows(tasks, limit=limit)}


def hud_portfolio_states() -> Dict[str, Any]:
    return _load_portfolio_states()


def hud_business_chat(business_id: str, limit: int = 200) -> Dict[str, Any]:
    messages = _load_business_chat(business_id, limit=limit)
    return {"business_id": business_id, "messages": messages}


def hud_append_business_chat(business_id: str, role: str, text: str) -> Dict[str, Any]:
    if not role or not text:
        return {"business_id": business_id, "message": None}
    entry = _append_business_chat(business_id, role=role, text=text)
    return {"business_id": business_id, "message": entry}


def hud_autopilot_metrics() -> Dict[str, Any]:
    return _autopilot_metrics()


def hud_autopilot_trend(days: int = 7) -> Dict[str, Any]:
    return {"days": days, "trend": _autopilot_trend(days=days)}
