"""Utility helpers for capturing and inspecting funnel leads."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
LEADS_PATH = REPO_ROOT / "finance" / "leads.jsonl"
UTC = timezone.utc


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class LeadEntry:
    id: int
    email: str
    source: str
    status: str = "new"
    created_ts: str = field(default_factory=_now)
    last_contact_ts: Optional[str] = None
    converted_ts: Optional[str] = None
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "LeadEntry":
        return cls(
            id=int(payload.get("id", 0) or 0),
            email=str(payload.get("email", "")).lower(),
            source=payload.get("source", "landing"),
            status=payload.get("status", "new"),
            created_ts=payload.get("created_ts") or _now(),
            last_contact_ts=payload.get("last_contact_ts"),
            converted_ts=payload.get("converted_ts"),
            notes=payload.get("notes", ""),
            metadata=payload.get("metadata") or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _ensure_dir() -> None:
    LEADS_PATH.parent.mkdir(parents=True, exist_ok=True)


def iter_leads() -> Iterable[LeadEntry]:
    if not LEADS_PATH.exists():
        return []
    leads: List[LeadEntry] = []
    with LEADS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                leads.append(LeadEntry.from_dict(json.loads(line)))
            except json.JSONDecodeError:
                continue
    return leads


def list_leads() -> List[LeadEntry]:
    data = iter_leads()
    return list(data)


def _write_leads(leads: List[LeadEntry]) -> None:
    _ensure_dir()
    with LEADS_PATH.open("w", encoding="utf-8") as handle:
        for lead in leads:
            handle.write(json.dumps(lead.to_dict()) + "\n")


def _next_id(leads: List[LeadEntry]) -> int:
    if not leads:
        return 1
    return max(lead.id for lead in leads) + 1


def add_lead(email: str, source: str = "landing", metadata: Optional[Dict[str, Any]] = None) -> LeadEntry:
    leads = list_leads()
    lead = LeadEntry(
        id=_next_id(leads),
        email=email.strip().lower(),
        source=source or "landing",
        metadata=metadata or {},
    )
    _ensure_dir()
    with LEADS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(lead.to_dict()) + "\n")
    return lead


def update_lead(lead_id: int, **updates: Any) -> LeadEntry:
    leads = list_leads()
    target: Optional[LeadEntry] = None
    for lead in leads:
        if lead.id == lead_id:
            target = lead
            break
    if not target:
        raise ValueError(f"Lead id {lead_id} not found")

    for key, value in updates.items():
        if hasattr(target, key):
            setattr(target, key, value)
        else:
            target.metadata[key] = value
    _write_leads(leads)
    return target
