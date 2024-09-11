from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from backend.database.database import get_db
from backend.database.models import Task
from datetime import timedelta

router = APIRouter()


class TaskTimeUpdate(BaseModel):
    time_remaining: timedelta


class TaskTimeResponse(BaseModel):
    id: int
    title: str
    time_remaining: timedelta
    is_complete: bool
    original_length: timedelta
    total_time: timedelta

    class Config:
        orm_mode = True
        json_encoders = {timedelta: lambda v: int(v.total_seconds())}


@router.put("/tasks/{task_id}/decrement-time", response_model=TaskTimeResponse)
def decrement_task_time(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.is_complete:
        raise HTTPException(status_code=400, detail="Task is already completed")

    # Decrement by 1 second
    task.time_remaining = max(
        timedelta(seconds=0), task.time_remaining - timedelta(seconds=1)
    )

    if task.time_remaining == timedelta(seconds=0):
        task.is_complete = True

    # Calculate total time including extensions
    extension_time = sum((ext.duration for ext in task.extensions), timedelta())
    total_time = task.original_length + extension_time

    db.commit()
    db.refresh(task)

    # Create a dictionary with task attributes and add the calculated total_time
    response_data = {
        "id": task.id,
        "title": task.title,
        "time_remaining": task.time_remaining,
        "is_complete": task.is_complete,
        "original_length": task.original_length,
        "total_time": total_time,
    }

    return TaskTimeResponse(**response_data)


@router.get("/tasks/{task_id}/total-time", response_model=Dict[str, int])
def get_total_time(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"total_time": task.original_length}


@router.get("/tasks/{task_id}/time-remaining", response_model=Dict[str, int])
def get_time_remaining(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"time_remaining": task.time_remaining}
