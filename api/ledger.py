"""JSONL-backed ledger utilities for minimal financial logging."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "finance" / "ledger.jsonl"


@dataclass
class LedgerEntry:
    timestamp: float
    amount: float
    currency: str
    source: str
    funnel: str
    notes: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "LedgerEntry":
        return cls(
            timestamp=float(data["timestamp"]),
            amount=float(data["amount"]),
            currency=data.get("currency", "USD"),
            source=data.get("source", "unknown"),
            funnel=data.get("funnel", "unknown"),
            notes=data.get("notes", ""),
        )


def append_entry(entry: LedgerEntry) -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(entry.to_json() + "\n")


def iter_entries(limit: Optional[int] = None) -> Iterable[LedgerEntry]:
    if not LEDGER_PATH.exists():
        return []
    entries: List[LedgerEntry] = []
    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                entries.append(LedgerEntry.from_dict(data))
            except (KeyError, ValueError):
                continue
    return entries[-limit:] if limit else entries


def summarize(entries: Iterable[LedgerEntry]) -> Dict[str, Dict[str, float]]:
    per_day: Dict[str, Dict[str, float]] = {}
    per_funnel: Dict[str, float] = {}
    for entry in entries:
        day = time.strftime("%Y-%m-%d", time.gmtime(entry.timestamp))
        per_day.setdefault(day, {"amount": 0.0})
        per_day[day]["amount"] += entry.amount
        per_funnel[entry.funnel] = per_funnel.get(entry.funnel, 0.0) + entry.amount
    return {"per_day": per_day, "per_funnel": per_funnel}
