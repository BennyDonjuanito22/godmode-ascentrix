"""Shared task-management utilities for the API services.

This module provides a ``TaskManager`` that encapsulates the common pattern of
queueing units of work, processing them on a background thread, and persisting
results to disk.  The previous code scattered this logic across multiple files,
which made it difficult to reason about worker state and hampered restart
reliability.  Centralising the implementation here keeps the FastAPI apps lean
and gives us a single place to enforce logging, history persistence, and
graceful shutdown behaviour.
"""

from __future__ import annotations

import itertools
import json
import queue
import threading
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional

TaskPayload = Dict[str, Any]
TaskResult = Dict[str, Any]
ProcessorFn = Callable[[TaskPayload], TaskResult]


@dataclass
class TaskRecord:
    job_id: int
    payload: TaskPayload
    status: str = "queued"
    result: Optional[TaskResult] = None
    error: Optional[str] = None
    enqueued_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskRecord":
        return cls(
            job_id=int(data["job_id"]),
            payload=data.get("payload", {}),
            status=data.get("status", "unknown"),
            result=data.get("result"),
            error=data.get("error"),
            enqueued_at=float(data.get("enqueued_at", time.time())),
            finished_at=data.get("finished_at"),
        )


class TaskManager:
    """Owns the worker queue and provides thread-safe helpers."""

    def __init__(self, history_path: Path, processor: ProcessorFn, name: str = "task-manager"):
        self.history_path = history_path
        self.processor = processor
        self._queue: "queue.Queue[Optional[int]]" = queue.Queue()
        self._records: Dict[int, TaskRecord] = {}
        self._lock = threading.RLock()
        self._counter = itertools.count(1)
        self._worker = threading.Thread(target=self._worker_loop, name=name, daemon=True)
        self._shutdown_event = threading.Event()
        self._started = False
        self._start_time: Optional[float] = None
        self._load_history()

    # ------------------------------------------------------------------#
    # Lifecycle
    # ------------------------------------------------------------------#

    def start(self) -> None:
        if self._started:
            return
        self._start_time = time.time()
        self._worker.start()
        self._started = True

    def shutdown(self, timeout: float = 5.0) -> None:
        if not self._started:
            return
        self._shutdown_event.set()
        self._queue.put(None)
        self._worker.join(timeout=timeout)
        self._started = False

    # ------------------------------------------------------------------#
    # Queue operations
    # ------------------------------------------------------------------#

    def enqueue(self, payload: TaskPayload, job_id: Optional[int] = None) -> int:
        with self._lock:
            if job_id is None:
                job_id = next(self._counter)
            elif job_id in self._records:
                raise ValueError(f"Job id {job_id} already exists")
            record = TaskRecord(job_id=job_id, payload=payload, enqueued_at=time.time())
            self._records[job_id] = record
        self._queue.put(job_id)
        self._persist_history()
        return job_id

    def get(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            record = self._records.get(job_id)
            return record.to_dict() if record else None

    def snapshot(self) -> Dict[int, Dict[str, Any]]:
        with self._lock:
            return {job_id: record.to_dict() for job_id, record in self._records.items()}

    @property
    def uptime(self) -> float:
        if not self._start_time:
            return 0.0
        return time.time() - self._start_time

    # ------------------------------------------------------------------#
    # Worker internals
    # ------------------------------------------------------------------#

    def _worker_loop(self) -> None:
        while not self._shutdown_event.is_set():
            job_id = self._queue.get()
            if job_id is None:
                self._queue.task_done()
                break
            with self._lock:
                record = self._records.get(job_id)
            if not record:
                continue
            try:
                output = self.processor(record.payload)
                record.result = output
                record.status = "complete"
                record.error = None
            except Exception as exc:  # pragma: no cover - defensive logging
                record.result = {}
                record.status = "error"
                record.error = f"{exc.__class__.__name__}: {exc}"
            finally:
                record.finished_at = time.time()
                self._persist_history()
                self._queue.task_done()

    def _load_history(self) -> None:
        if not self.history_path.exists():
            return
        try:
            data = json.loads(self.history_path.read_text(encoding="utf-8"))
        except Exception:
            self.history_path.rename(self.history_path.with_suffix(".corrupt"))
            return
        for raw_record in data.values():
            record = TaskRecord.from_dict(raw_record)
            self._records[record.job_id] = record
        if self._records:
            max_existing = max(self._records)
            self._counter = itertools.count(max_existing + 1)

    def _persist_history(self) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            snapshot = {job_id: record.to_dict() for job_id, record in self._records.items()}
        tmp_path = self.history_path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        tmp_path.replace(self.history_path)
