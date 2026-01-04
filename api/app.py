"""FastAPI application that fronts the shared TaskManager."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr

from api.funnels import load_b1_funnel_config, render_b1_landing
from api.hud_api import hud_agents, hud_autopilot_status, hud_home, hud_logs, hud_settings, hud_streams
from api.leads import add_lead, list_leads
from api.ledger import LedgerEntry, append_entry, iter_entries, summarize
from api.vector_memory import build_index, search_index
from api.task_runtime import TaskManager

app = FastAPI()

SCRIPT_DIR = Path(__file__).resolve().parent
HISTORY_PATH = SCRIPT_DIR / "app_task_history.json"


def _process_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder worker logic until real jobs are wired up."""
    time.sleep(2)
    return {"status": "processed", "payload": task_data}


MANAGER = TaskManager(history_path=HISTORY_PATH, processor=_process_task, name="api-app-worker")


@app.on_event("startup")
def _startup() -> None:
    MANAGER.start()


@app.on_event("shutdown")
def _shutdown() -> None:
    MANAGER.shutdown()


@app.post("/task")
def enqueue_task(task: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    job_id = MANAGER.enqueue(task)
    return {"job_id": job_id, "status": "queued"}


@app.get("/result/{job_id}")
def get_result(job_id: int) -> Dict[str, Any]:
    record = MANAGER.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="job_id not found")
    return {
        "job_id": job_id,
        "status": record["status"],
        "result": record.get("result"),
        "error": record.get("error"),
    }


@app.get("/tasks")
def list_tasks() -> Dict[str, Any]:
    return {"results": MANAGER.snapshot()}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "uptime": MANAGER.uptime}


@app.get("/")
def root() -> Dict[str, Any]:
    return {"service": "godmode-api", "status": "running"}


@app.get("/funnels/b1")
def funnel_b1_config() -> Dict[str, Any]:
    """
    Return the current configuration for the B1 (Affiliate/Digital product) funnel.
    """
    config = load_b1_funnel_config()
    return {"funnel": config.to_dict()}


@app.get("/funnels/b1/landing", response_class=HTMLResponse)
def funnel_b1_landing() -> HTMLResponse:
    """
    Render a simple landing page that can be shared or embedded.
    """
    config = load_b1_funnel_config()
    html = render_b1_landing(config)
    return HTMLResponse(content=html)


class LeadCapturePayload(BaseModel):
    email: EmailStr
    source: str | None = "landing"
    tag: str | None = None


@app.post("/funnels/b1/lead")
def funnel_b1_capture(payload: LeadCapturePayload) -> Dict[str, Any]:
    metadata = {"tag": payload.tag} if payload.tag else None
    entry = add_lead(email=payload.email, source=payload.source or "landing", metadata=metadata)
    return {"ok": True, "lead": entry.to_dict()}


@app.get("/funnels/b1/lead")
def funnel_b1_leads(limit: int = 50) -> Dict[str, Any]:
    leads = list_leads()
    return {"leads": [lead.to_dict() for lead in leads[-limit:]]}


@app.get("/finance/ledger")
def ledger_list(limit: int = 50) -> Dict[str, Any]:
    entries = list(iter_entries(limit=limit))
    return {"entries": [entry.__dict__ for entry in entries]}


@app.post("/finance/ledger")
def ledger_append(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ["amount", "currency", "source", "funnel", "notes"]
    for key in required:
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {key}")
    entry = LedgerEntry(
        timestamp=time.time(),
        amount=float(payload["amount"]),
        currency=str(payload["currency"]),
        source=str(payload["source"]),
        funnel=str(payload["funnel"]),
        notes=str(payload["notes"]),
    )
    append_entry(entry)
    return {"ok": True}


@app.get("/finance/summary")
def ledger_summary() -> Dict[str, Any]:
    entries = iter_entries()
    data = summarize(entries)
    return data


@app.post("/memory/ingest")
def memory_ingest() -> Dict[str, Any]:
    stats = build_index()
    return {"ok": True, **stats}


@app.get("/memory/search")
def memory_search(query: str, limit: int = 5) -> Dict[str, Any]:
    results = search_index(query=query, limit=limit)
    return {"results": results}


@app.get("/hud/home")
def hud_home_endpoint() -> Dict[str, Any]:
    return hud_home()


@app.get("/hud/streams")
def hud_streams_endpoint() -> Dict[str, Any]:
    return hud_streams()


@app.get("/hud/agents")
def hud_agents_endpoint() -> Dict[str, Any]:
    return hud_agents()


@app.get("/hud/logs")
def hud_logs_endpoint() -> Dict[str, Any]:
    return hud_logs()


@app.get("/hud/settings")
def hud_settings_endpoint() -> Dict[str, Any]:
    return hud_settings()


@app.get("/hud/autopilot/status")
def hud_autopilot_status_endpoint() -> Dict[str, Any]:
    return hud_autopilot_status()
