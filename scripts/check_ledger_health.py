#!/usr/bin/env python3
"""Quick validator that checks finance/ledger.jsonl for parse errors and summarizes totals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

LEDGER_PATH = Path(__file__).resolve().parents[1] / "finance" / "ledger.jsonl"


def load_entries(path: Path) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    if not path.exists():
        return totals
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON on line {line_no}: {exc}") from exc
            funnel = data.get("funnel", "unknown")
            amount = float(data.get("amount", 0.0))
            totals[funnel] = totals.get(funnel, 0.0) + amount
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Check ledger integrity and summarize totals.")
    parser.add_argument("--path", type=Path, default=LEDGER_PATH, help="Path to ledger.jsonl")
    args = parser.parse_args()

    totals = load_entries(args.path)
    if not totals:
        print("Ledger empty or missing.")
        return

    grand_total = sum(totals.values())
    print(f"Ledger OK. Grand total: {grand_total:.2f}")
    for funnel, amount in sorted(totals.items()):
        print(f"  {funnel}: {amount:.2f}")


if __name__ == "__main__":
    main()
