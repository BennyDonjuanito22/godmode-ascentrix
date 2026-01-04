#!/usr/bin/env python3
"""CLI to generate a status dashboard from finance/leads.jsonl grouped by lead type (source)."""

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

LEADS_PATH = Path("finance/leads.jsonl")


def load_leads() -> List[Dict[str, Any]]:
    leads = []
    with LEADS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                lead = json.loads(line)
                leads.append(lead)
            except json.JSONDecodeError:
                print(f"Warning: Skipping invalid JSON line: {line}")
    return leads


def group_leads_by_type(leads: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped = defaultdict(list)
    for lead in leads:
        lead_type = lead.get("source", "unknown")
        grouped[lead_type].append(lead)
    return grouped


def format_markdown_table(grouped: Dict[str, List[Dict[str, Any]]]) -> str:
    lines = ["# Lead Status Dashboard\n"]
    for lead_type, leads in grouped.items():
        lines.append(f"## Lead Type: {lead_type} ({len(leads)} leads)\n")
        lines.append("| ID | Email | Status | Created | Last Contact | Converted | Notes |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for lead in leads:
            id_ = lead.get("id", "")
            email = lead.get("email", "")
            status = lead.get("status", "")
            created = lead.get("created_ts", "")
            last_contact = lead.get("last_contact_ts", "")
            converted = lead.get("converted_ts", "") or "-"
            notes = lead.get("notes", "").replace("\n", " ")
            lines.append(f"| {id_} | {email} | {status} | {created} | {last_contact} | {converted} | {notes} |")
        lines.append("")
    return "\n".join(lines)


def write_csv(grouped: Dict[str, List[Dict[str, Any]]], output_path: Path) -> None:
    with output_path.open("w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Lead Type", "ID", "Email", "Status", "Created", "Last Contact", "Converted", "Notes"])
        for lead_type, leads in grouped.items():
            for lead in leads:
                writer.writerow([
                    lead_type,
                    lead.get("id", ""),
                    lead.get("email", ""),
                    lead.get("status", ""),
                    lead.get("created_ts", ""),
                    lead.get("last_contact_ts", ""),
                    lead.get("converted_ts", "") or "",
                    lead.get("notes", ""),
                ])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate lead status dashboard grouped by lead type.")
    parser.add_argument(
        "--format",
        choices=["md", "csv"],
        default="md",
        help="Output format: md (Markdown) or csv (CSV file). Default is md.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path. If omitted, prints to stdout (for md) or requires output for csv.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    leads = load_leads()
    grouped = group_leads_by_type(leads)

    if args.format == "md":
        md = format_markdown_table(grouped)
        if args.output:
            args.output.write_text(md, encoding="utf-8")
            print(f"Markdown dashboard written to {args.output}")
        else:
            print(md)
    elif args.format == "csv":
        if not args.output:
            parser.error("--output is required for csv format")
        write_csv(grouped, args.output)
        print(f"CSV dashboard written to {args.output}")


if __name__ == "__main__":
    main()
