"""Simple background task engine for the God Mode stack."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException

from api.task_runtime import TaskManager

app = FastAPI()

HISTORY_PATH = Path(__file__).resolve().parent / "task_history.json"


def _process_payload(task: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate a unit of work until real orchestration is wired up."""
    time.sleep(3)
    title = task.get("title") or f"task-{task.get('id', 'unknown')}"
    return {
        "id": task.get("id"),
        "title": title,
        "status": "complete",
        "payload": task,
    }


MANAGER = TaskManager(history_path=HISTORY_PATH, processor=_process_payload, name="task-engine-worker")


@app.on_event("startup")
def _startup() -> None:
    MANAGER.start()


@app.on_event("shutdown")
def _shutdown() -> None:
    MANAGER.shutdown()


@app.post("/tasks")
def create_task(task: Dict[str, Any]) -> Dict[str, Any]:
    if "id" not in task:
        raise HTTPException(status_code=400, detail="task payload must include an 'id' field")
    job_id = int(task["id"])
    MANAGER.enqueue(task, job_id=job_id)
    return {"queued": True, "job_id": job_id}


@app.get("/tasks")
def list_tasks() -> Dict[str, Any]:
    return {"results": MANAGER.snapshot()}


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "uptime": MANAGER.uptime}
