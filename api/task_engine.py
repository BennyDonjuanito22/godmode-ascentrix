import time, threading, queue, json, os
from fastapi import FastAPI
from typing import Dict
TASKS = queue.Queue()
RESULTS: Dict[int, Dict] = {}
HISTORY_FILE = "task_history.json"
if os.path.exists(HISTORY_FILE):
 try:
 with open(HISTORY_FILE, "r") as f:
 RESULTS.update(json.load(f))
 except:
 pass
def save_history():
 with open(HISTORY_FILE, "w") as f:
 json.dump(RESULTS, f)
def worker():
 while True:
 task = TASKS.get()
 tid = task["id"]
 title = task["title"]
 time.sleep(3)
 RESULTS[tid] = {
 "id": tid,
 "title": title,
 "status": "complete",
 "finished_at": time.time()
 }
 save_history()
 TASKS.task_done()
threading.Thread(target=worker, daemon=True).start()
app = FastAPI()
@app.post("/tasks")
def create_task(task: dict):
 TASKS.put(task)
 return {"queued": True}
@app.get("/tasks")
def list_tasks():
 return {"results": RESULTS}
@app.get("/health")
def health():
 return {"ok": True, "uptime": time.time()}
