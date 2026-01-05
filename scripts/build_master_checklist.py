#!/usr/bin/env python3
"""Build the master checklist + blueprint inventory and export MD/JSON artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_MD = ROOT / "docs" / "system_blueprint_checklist.md"
OUTPUT_JSON = ROOT / "data" / "master_checklist.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _color_for(percent: int) -> str:
    if percent <= 0:
        return "red"
    if percent >= 100:
        return "green"
    return "orange"


def build_core_items() -> List[Dict[str, Any]]:
    return [
        {
            "id": "offers_config",
            "title": "Offers config source of truth",
            "status": 100,
            "notes": "config/offers.json + docs/offers_config.md + sync scripts",
            "purpose": "Single source of truth for every sellable offer; drives product sync and sales ingestion.",
            "paths": ["config/offers.json", "docs/offers_config.md"],
        },
        {
            "id": "platform_sync",
            "title": "Gumroad/Digistore sync + sales ingest",
            "status": 100,
            "notes": "Clients + sync + fetch scripts; ledger tagging with business_id/offer_id",
            "purpose": "Turns offers into live products and logs revenue back into the ledger.",
            "paths": [
                "godmode/integrations/gumroad_client.py",
                "godmode/integrations/digistore_client.py",
                "scripts/sync_offers_to_platforms.py",
                "scripts/fetch_sales_and_log.py",
            ],
        },
        {
            "id": "ledger_api",
            "title": "Ledger API + health checks",
            "status": 100,
            "notes": "finance/ledger.jsonl + /finance endpoints + check_ledger_health",
            "purpose": "Canonical revenue record and validation to protect integrity and HUD metrics.",
            "paths": ["api/ledger.py", "api/app.py", "scripts/check_ledger_health.py"],
        },
        {
            "id": "consent_tracking",
            "title": "Consent + first-party tracking",
            "status": 70,
            "notes": "HUD + B1 lander consent; extend to all business landers via scaffold",
            "purpose": "Collects legal first-party data to improve targeting and conversion decisions.",
            "paths": ["hud/index.html", "api/funnels.py", "api/app.py"],
        },
        {
            "id": "audience_rollups",
            "title": "Channel summaries + audience export",
            "status": 100,
            "notes": "Daily summary + hashed audience export",
            "purpose": "Gives cross-channel performance and consented retargeting audiences.",
            "paths": ["scripts/generate_channel_summary.py", "scripts/export_audiences.py"],
        },
        {
            "id": "email_infra",
            "title": "SMTP email system + templates",
            "status": 60,
            "notes": "SMTP sender + follow-up scripts + base templates; per-business edits pending",
            "purpose": "Automated activation and recovery emails to lift conversions and retention.",
            "paths": [
                "scripts/email_sender.py",
                "scripts/send_followups.py",
                "content/templates/email/activation_quickstart.md",
                "content/templates/email/recovery_abandoned_cart.md",
            ],
        },
        {
            "id": "business_scaffold",
            "title": "Business scaffold + marketing plan skeletons",
            "status": 80,
            "notes": "Scaffold creates offers/checklist/promo log/marketing plan + templates",
            "purpose": "Standardizes new business launches with consistent assets and checklists.",
            "paths": ["scripts/scaffold_business.py", "businesses/"],
        },
        {
            "id": "hud_master_checklist",
            "title": "Master checklist on HUD home (live)",
            "status": 70,
            "notes": "Checklist data + HUD widget wired; live refresh requires rerunning build script",
            "purpose": "Single operational checklist for Jarvis and the operator.",
            "paths": ["data/master_checklist.json", "api/hud_api.py", "hud/index.html"],
        },
        {
            "id": "live_work_queue",
            "title": "Live work queue with % + ETA",
            "status": 100,
            "notes": "HUD widget + /hud/work_queue endpoint live; ETA uses historical median durations",
            "purpose": "Real-time view of active tasks and execution pressure for autopilot.",
            "paths": ["api/hud_api.py", "api/app.py", "hud/index.html"],
        },
        {
            "id": "business_ranking_queue",
            "title": "Business ranking queue (scored ideas)",
            "status": 60,
            "notes": "Ranking helpers + config + JSONL store exist; HUD/portfolio view pending",
            "purpose": "Ranks candidate businesses by scoring config for prioritization.",
            "paths": ["api/business_research.py", "research/business_ideas.jsonl", "research/business_scoring_config.json"],
        },
        {
            "id": "portfolio_states",
            "title": "Portfolio states (LAUNCH/BUILD/RANK) single source",
            "status": 60,
            "notes": "Data file + HUD card wired; automation and validation pending",
            "purpose": "Operator-visible state of portfolio by launch phase.",
            "paths": ["data/portfolio_states.json", "design_docs/businesses_plan.md"],
        },
        {
            "id": "business_chat",
            "title": "Per-business persistent chat thread",
            "status": 60,
            "notes": "HUD + API persistence wired; auth/UX refinements pending",
            "purpose": "Keeps a shared business thread across subpages.",
            "paths": ["api/hud_api.py", "api/app.py", "hud/index.html"],
        },
        {
            "id": "business_live_stream",
            "title": "Per-business live agent stream + queue",
            "status": 60,
            "notes": "Per-business queue endpoint + HUD wiring live; task tagging gaps pending",
            "purpose": "Live visibility into ETA/%/status for each business.",
            "paths": ["api/hud_api.py", "api/app.py", "hud/index.html"],
        },
        {
            "id": "godmode_landing",
            "title": "God Mode landing page (security + infrastructure)",
            "status": 20,
            "notes": "HUD placeholder layout added; data wiring pending",
            "purpose": "Operator view for security and infrastructure oversight.",
            "paths": ["hud/index.html"],
        },
        {
            "id": "design_dev_studio",
            "title": "Design/Dev Studio module (media + prototypes)",
            "status": 20,
            "notes": "HUD placeholder layout added; media/prototype tooling pending",
            "purpose": "Edit media, generate demos, and reuse tools across businesses.",
            "paths": ["hud/index.html"],
        },
        {
            "id": "infra_registry",
            "title": "Org/infra registry (LLC/EIN/security/infra inventory)",
            "status": 10,
            "notes": "Location/format needs defining; recommended to store in secure vault",
            "purpose": "Keeps critical business and infrastructure data organized for operations.",
            "paths": [],
        },
        {
            "id": "customer_profiles",
            "title": "Cross-business customer profiles",
            "status": 70,
            "notes": "Rebuild script + API summary endpoints; feeds shared customer intelligence",
            "purpose": "Unified customer metadata across all businesses for targeting and upsell.",
            "paths": ["api/accounting.py", "scripts/rebuild_customer_profiles.py", "api/app.py"],
        },
        {
            "id": "autopilot_proof",
            "title": "Autopilot proof metrics (success rate)",
            "status": 80,
            "notes": "HUD card + /hud/autopilot/metrics and /hud/autopilot/trend endpoints",
            "purpose": "Provides evidence that autopilot runs are succeeding over time.",
            "paths": ["api/hud_api.py", "api/app.py", "hud/index.html"],
        },
        {
            "id": "autopilot_watchdog",
            "title": "Autopilot watchdog (auto-restart)",
            "status": 70,
            "notes": "scripts/autopilot_watchdog.sh keeps autopilot running; needs to be launched by operator/launchd",
            "purpose": "Ensures autopilot stays online and restarts when it crashes.",
            "paths": ["scripts/autopilot_watchdog.sh", "scripts/start_autopilot.sh"],
        },
        {
            "id": "stuck_task_reset",
            "title": "Stuck task reset (auto-unblock)",
            "status": 80,
            "notes": "Resets in-progress tasks stuck >20m back to pending with a note",
            "purpose": "Prevents autopilot from getting stuck on long-running tasks.",
            "paths": ["api/autopilot.py"],
        },
    ]


def blueprint_status_map() -> Dict[str, int]:
    return {
        "design_docs/dashboard_spec.md": 70,
        "design_docs/businesses_plan.md": 60,
        "design_docs/godmode_overview.md": 80,
        "design_docs/hud_api.md": 70,
        "design_docs/implementation_blueprint.md": 50,
        "design_docs/infra_scaling_spec.md": 20,
        "design_docs/security_plan.md": 20,
        "design_docs/notifications_sse.md": 20,
        "design_docs/vector_memory_upgrade.md": 40,
        "docs/finance_logging.md": 80,
        "docs/offers_config.md": 100,
        "docs/email_setup.md": 80,
        "businesses/b1_affiliate_toolkit/README.md": 40,
        "businesses/b2_ecom_holiday/README.md": 20,
        "businesses/b3_content_engine/README.md": 20,
        "businesses/b4_ai_service/README.md": 30,
        "businesses/templates/README.md": 40,
    }


def gather_blueprints() -> List[Dict[str, Any]]:
    roots = ["design_docs", "docs", "businesses", "blueprints"]
    inventory = []
    status_map = blueprint_status_map()
    for folder in roots:
        base = ROOT / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = path.as_posix()
            headings: List[str] = []
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.startswith("#"):
                        headings.append(line.strip())
            except Exception:
                pass
            status = status_map.get(rel, 0)
            inventory.append(
                {
                    "path": rel,
                    "headings": headings[:60],
                    "status": status,
                    "color": _color_for(status),
                }
            )
    return inventory


def write_outputs(core_items: List[Dict[str, Any]], blueprints: List[Dict[str, Any]]) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": _now(),
        "core_items": core_items,
        "blueprints": blueprints,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# System Blueprint + Progress Checklist")
    lines.append("")
    lines.append(f"Generated: {_now()}")
    lines.append("")
    lines.append("Legend: 🔴0% (not started) • 🟠/🟡 in-progress • 🟢100% (complete)")
    lines.append("")
    lines.append("## Master Checklist (audited)")
    lines.append("")
    for item in core_items:
        pct = item["status"]
        color = _color_for(pct)
        icon = "🟢" if pct >= 100 else ("🔴" if pct == 0 else "🟠")
        lines.append(f"- {icon} {pct}% ({color}) — {item['title']}")
        if item.get("notes"):
            lines.append(f"  - {item['notes']}")
        if item.get("purpose"):
            lines.append(f"  - Purpose: {item['purpose']}")
        if item.get("paths"):
            for path in item["paths"]:
                lines.append(f"  - {path}")
    lines.append("")
    lines.append("## Blueprint Inventory (cross-referenced)")
    lines.append("")
    for bp in blueprints:
        pct = bp["status"]
        icon = "🟢" if pct >= 100 else ("🔴" if pct == 0 else "🟠")
        lines.append(f"### {bp['path']} — {icon} {pct}%")
        if bp["headings"]:
            for h in bp["headings"]:
                lines.append(f"- {h}")
        else:
            lines.append("- (no headings parsed)")
        lines.append("")
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    core_items = build_core_items()
    blueprints = gather_blueprints()
    write_outputs(core_items, blueprints)
    print(f"Wrote {OUTPUT_MD} and {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
