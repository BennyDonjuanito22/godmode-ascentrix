from fastapi import FastAPI, Body
import threading, queue, time

app = FastAPI()
task_queue = queue.Queue()
results = {}
job_id_counter = 0
queue_lock = threading.Lock()

def process_task(task_data):
    time.sleep(2)
    return {"data": task_data, "status": "processed"}

def save_history(entry=None):
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("history.log", "a") as f:
            f.write(f"[{timestamp}] {entry}\n")
    except Exception as e:
        print(f"Error saving history: {e}")

def worker():
    while True:
        task = task_queue.get()
        if task is None:
            break
        job_id, data = task
        try:
            result = process_task(data)
            results[job_id] = result
            save_history({"job_id": job_id, "result": result})
        except Exception as e:
            results[job_id] = {"error": str(e)}
        finally:
            task_queue.task_done()

worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()

@app.post("/task")
def enqueue_task(task: dict = Body(...)):
    global job_id_counter
    with queue_lock:
        job_id_counter += 1
        job_id = job_id_counter
    results[job_id] = None
    task_queue.put((job_id, task))
    return {"job_id": job_id, "status": "queued"}

@app.get("/result/{job_id}")
def get_result(job_id: int):
    if job_id not in results:
        return {"status": "invalid job id"}
    if results[job_id] is None:
        return {"status": "pending", "result": None}
    return {"status": "complete", "result": results[job_id]}

@app.get("/")
def read_root():
    return {"status": "running"}

@app.on_event("shutdown")
def on_shutdown():
    task_queue.put(None)
    worker_thread.join(timeout=5)
