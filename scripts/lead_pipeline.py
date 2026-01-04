#!/usr/bin/env python3
"""
Summaries finance/leads.jsonl into grouped dashboards (Markdown + CSV).

Usage:
  python scripts/lead_pipeline.py --output markdown
  python scripts/lead_pipeline.py --output csv

Lead type heuristics:
  - metadata.tag starting with "partner" => partner
  - source contains "affiliate" => affiliate
  - default => landing
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
LEADS_PATH = REPO_ROOT / "finance" / "leads.jsonl"
OUTPUT_DIR = REPO_ROOT / "reports"


def load_leads() -> List[Dict[str, str]]:
    if not LEADS_PATH.exists():
        return []
    leads: List[Dict[str, str]] = []
    with LEADS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                leads.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return leads


def classify(lead: Dict[str, str]) -> str:
    metadata = lead.get("metadata") or {}
    tag = metadata.get("tag") or ""
    source = (lead.get("source") or "").lower()
    if isinstance(tag, str) and tag.startswith("partner"):
        return "partner"
    if "affiliate" in source:
        return "affiliate"
    if "partner" in source:
        return "partner"
    return "landing"


def build_summary(leads: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for lead in leads:
        grouped[classify(lead)].append(lead)
    return grouped


def render_markdown(grouped: Dict[str, List[Dict[str, str]]]) -> str:
    lines = ["# Lead & Partner Pipeline", ""]
    total = sum(len(v) for v in grouped.values())
    lines.append(f"Total leads: **{total}**\n")
    for lead_type, entries in grouped.items():
        lines.append(f"## {lead_type.title()} Leads ({len(entries)})\n")
        lines.append("| ID | Email | Source | Status | Last Contact | Notes |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for entry in entries:
            lines.append(
                f"| {entry.get('id','–')} | {entry.get('email','')} | {entry.get('source','')} "
                f"| {entry.get('status','')} | {entry.get('last_contact_ts','–')} | {entry.get('notes','')} |"
            )
        lines.append("")
    return "\n".join(lines)


def write_csv(leads: List[Dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "email",
        "source",
        "status",
        "created_ts",
        "last_contact_ts",
        "converted_ts",
        "notes",
        "lead_type",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for lead in leads:
            writer.writerow(
                {
                    "id": lead.get("id"),
                    "email": lead.get("email"),
                    "source": lead.get("source"),
                    "status": lead.get("status"),
                    "created_ts": lead.get("created_ts"),
                    "last_contact_ts": lead.get("last_contact_ts"),
                    "converted_ts": lead.get("converted_ts"),
                    "notes": lead.get("notes"),
                    "lead_type": classify(lead),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize leads.jsonl into dashboards.")
    parser.add_argument("--output", choices=["markdown", "csv", "both"], default="markdown")
    args = parser.parse_args()

    leads = load_leads()
    grouped = build_summary(leads)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.output in ("markdown", "both"):
        md = render_markdown(grouped)
        (OUTPUT_DIR / "lead_pipeline.md").write_text(md, encoding="utf-8")
        print(f"Wrote {OUTPUT_DIR / 'lead_pipeline.md'}")
    if args.output in ("csv", "both"):
        write_csv(leads, OUTPUT_DIR / "lead_pipeline.csv")
        print(f"Wrote {OUTPUT_DIR / 'lead_pipeline.csv'}")


if __name__ == "__main__":
    main()
