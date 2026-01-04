"""Specialised worker API for higher-level agent orchestration."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

from api.task_runtime import TaskManager

app = FastAPI()

SCRIPT_DIR = Path(__file__).resolve().parent
HISTORY_PATH = SCRIPT_DIR / "agent_engine_history.json"


def _simulate_agent_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Placeholder processor until real orchestration glue is wired up."""
    time.sleep(2)
    title = payload.get("title") or f"task-{payload.get('id', 'unknown')}"
    return {
        "id": payload.get("id"),
        "title": title,
        "status": "complete",
        "details": payload.get("details", {}),
    }


MANAGER = TaskManager(history_path=HISTORY_PATH, processor=_simulate_agent_task, name="agent-engine-worker")


@app.on_event("startup")
def _startup() -> None:
    MANAGER.start()


@app.on_event("shutdown")
def _shutdown() -> None:
    MANAGER.shutdown()


@app.post("/tasks")
def create_task(task: Dict[str, Any]) -> Dict[str, Any]:
    if "id" not in task:
        raise HTTPException(status_code=400, detail="task payload must include 'id'")
    job_id = int(task["id"])
    MANAGER.enqueue(task, job_id=job_id)
    return {"queued": True, "job_id": job_id}


@app.get("/tasks")
def list_tasks() -> Dict[str, Any]:
    return {"results": MANAGER.snapshot()}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "uptime": MANAGER.uptime}
