import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Project, Task, TimeEntry

app = FastAPI(title="Construction Time Tracking API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class IdModel(BaseModel):
    id: str


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


@app.get("/")
def read_root():
    return {"message": "Construction Time Tracking API"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Projects
@app.post("/api/projects", response_model=IdModel)
def create_project(project: Project):
    inserted_id = create_document("project", project)
    return {"id": inserted_id}


@app.get("/api/projects")
def list_projects(limit: Optional[int] = 50):
    docs = get_documents("project", {}, limit)
    # string-ify ids
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# Tasks
@app.post("/api/tasks", response_model=IdModel)
def create_task(task: Task):
    # verify project exists
    proj = db["project"].find_one({"_id": to_object_id(task.project_id)})
    if not proj:
        raise HTTPException(404, detail="Project not found")
    inserted_id = create_document("task", task)
    return {"id": inserted_id}


@app.get("/api/tasks")
def list_tasks(project_id: Optional[str] = None, limit: Optional[int] = 100):
    filt = {}
    if project_id:
        filt["project_id"] = project_id
    docs = get_documents("task", filt, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# Time Entries
class StartTimerRequest(BaseModel):
    task_id: str
    user_id: Optional[str] = None
    note: Optional[str] = None


@app.post("/api/time/start", response_model=IdModel)
def start_timer(payload: StartTimerRequest):
    # verify task exists
    t = db["task"].find_one({"_id": to_object_id(payload.task_id)})
    if not t:
        raise HTTPException(404, detail="Task not found")

    entry = TimeEntry(
        task_id=payload.task_id,
        user_id=payload.user_id,
        start_time=datetime.now(timezone.utc),
        end_time=None,
        duration_sec=None,
        note=payload.note,
    )
    inserted_id = create_document("timeentry", entry)
    return {"id": inserted_id}


class StopTimerRequest(BaseModel):
    entry_id: str


@app.post("/api/time/stop")
def stop_timer(payload: StopTimerRequest):
    entry = db["timeentry"].find_one({"_id": to_object_id(payload.entry_id)})
    if not entry:
        raise HTTPException(404, detail="Time entry not found")
    if entry.get("end_time") is not None:
        raise HTTPException(400, detail="Timer already stopped")

    end_time = datetime.now(timezone.utc)
    duration = int((end_time - entry["start_time"]).total_seconds())
    db["timeentry"].update_one(
        {"_id": entry["_id"]},
        {"$set": {"end_time": end_time, "updated_at": end_time, "duration_sec": duration}},
    )
    updated = db["timeentry"].find_one({"_id": entry["_id"]})
    updated["id"] = str(updated.pop("_id"))
    return updated


@app.get("/api/time/entries")
def list_time_entries(task_id: Optional[str] = None, project_id: Optional[str] = None, limit: Optional[int] = 200):
    filt = {}
    if task_id:
        filt["task_id"] = task_id
    if project_id:
        # find tasks for project
        task_ids = [str(t["_id"]) for t in db["task"].find({"project_id": project_id}, {"_id": 1})]
        filt["task_id"] = {"$in": task_ids}
    docs = get_documents("timeentry", filt, limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs


# Simple reporting: total tracked seconds per task
@app.get("/api/reports/task/{task_id}")
def report_task(task_id: str):
    entries = db["timeentry"].find({"task_id": task_id})
    total = 0
    for e in entries:
        if e.get("duration_sec") is not None:
            total += int(e["duration_sec"])
    return {"task_id": task_id, "total_seconds": total}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
