import time, threading, queue, json, os
from fastapi import FastAPI
from typing import Dict

app = FastAPI()

TASKS = queue.Queue()
RESULTS: Dict[int, dict] = {}

def worker():
    while True:
        task = TASKS.get()
        tid = task["id"]
        title = task["title"]
        time.sleep(2)  # simulate work
        RESULTS[tid] = {"id": tid, "title": title, "status": "complete"}
        TASKS.task_done()

threading.Thread(target=worker, daemon=True).start()

@app.post("/tasks")
def create_task(task: dict):
    TASKS.put(task)
    return {"queued": True}

@app.get("/tasks")
def list_tasks():
    return {"results": RESULTS}
