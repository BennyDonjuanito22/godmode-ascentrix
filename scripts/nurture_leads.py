#!/usr/bin/env python3
"""Simple CLI to nurture B1 leads and log conversions."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.funnels import load_b1_funnel_config  # noqa: E402
from api.leads import LeadEntry, list_leads, update_lead  # noqa: E402

LOG_DIR = ROOT / "logs" / "nurture_runs"
UTC = timezone.utc


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _write_log(entries: List[str]) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"nurture_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}.log"
    path.write_text("\n".join(entries), encoding="utf-8")
    return path


def send_followups(limit: int) -> None:
    leads = list_leads()
    targets = [lead for lead in leads if lead.status == "new"]
    if not targets:
        print("No new leads to contact.")
        return
    config = load_b1_funnel_config()
    messages: List[str] = []
    processed = 0
    for lead in targets:
        if processed >= limit:
            break
        processed += 1
        body = (
            f"Subject: Your AI Growth Toolkit link\n\n"
            f"Hey there,\n\n"
            f"I saw you requested the AI Growth Toolkit. Here's your direct checkout link:\n"
            f"{config.cta_url}\n\n"
            f"You'll get the launch checklist, prompt pack, and SOP templates immediately.\n"
            f"Reply to this email when you're live so we can feature your build.\n\n"
            f"- Ascentrix Autopilot"
        )
        messages.append(f"# Lead {lead.id}: {lead.email}\n{body}\n---")
        update_lead(
            lead.id,
            status="contacted",
            last_contact_ts=_timestamp(),
            notes="Initial nurture email sent.",
        )
    if not messages:
        print("Reached send limit without processing any leads.")
        return
    log_path = _write_log(messages)
    print(f"Prepared {len(messages)} follow-ups. Logged copy to {log_path}")


def mark_conversion(email: str, amount: float, currency: str, funnel: str, source: str, notes: Optional[str]) -> None:
    leads = list_leads()
    lead: Optional[LeadEntry] = next((item for item in leads if item.email == email.lower()), None)
    if not lead:
        raise SystemExit(f"Lead with email {email} not found.")
    record_script = ROOT / "scripts" / "record_revenue.py"
    cmd = [
        sys.executable,
        str(record_script),
        "--amount",
        str(amount),
        "--currency",
        currency,
        "--source",
        source,
        "--funnel",
        funnel,
        "--notes",
        notes or f"Lead {lead.email} converted via nurture script",
    ]
    subprocess.run(cmd, check=True, cwd=ROOT)
    update_lead(
        lead.id,
        status="converted",
        converted_ts=_timestamp(),
        notes=notes or lead.notes,
    )
    print(f"Recorded conversion for {lead.email} and logged revenue.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nurture B1 leads and record conversions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    send_parser = subparsers.add_parser("send", help="Generate nurture emails for new leads.")
    send_parser.add_argument("--limit", type=int, default=10, help="Maximum number of leads to process.")

    convert_parser = subparsers.add_parser("convert", help="Mark a lead as converted and record revenue.")
    convert_parser.add_argument("--email", required=True, help="Lead email address.")
    convert_parser.add_argument("--amount", type=float, required=True, help="Revenue amount to record.")
    convert_parser.add_argument("--currency", default="USD", help="Currency code (default: USD).")
    convert_parser.add_argument("--funnel", default="B1", help="Funnel identifier (default: B1).")
    convert_parser.add_argument("--source", default="gumroad", help="Source platform for the sale.")
    convert_parser.add_argument("--notes", help="Optional notes for the ledger + lead entry.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "send":
        send_followups(limit=args.limit)
    elif args.command == "convert":
        mark_conversion(
            email=args.email,
            amount=args.amount,
            currency=args.currency,
            funnel=args.funnel,
            source=args.source,
            notes=args.notes,
        )


if __name__ == "__main__":
    main()
