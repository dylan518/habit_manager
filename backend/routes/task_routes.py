from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, validator
from backend.database.database import get_db
from backend.database.models import Task, SubTask, TaskExtension, TaskOrder
import logging
from datetime import datetime
from tzlocal import get_localzone
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError



router = APIRouter()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)


def string_to_timedelta(time_str: str) -> timedelta:
    """Convert a string in format 'HH:MM:SS' to timedelta."""
    hours, minutes, seconds = map(int, time_str.split(":"))
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def timedelta_to_string(td: timedelta) -> str:
    """Convert a timedelta to string in format 'HH:MM:SS'."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class SubTaskCreate(BaseModel):
    description: str


class TaskExtensionCreate(BaseModel):
    extension_length: str  # in format "HH:MM:SS"

    @validator("extension_length")
    def validate_extension_length(cls, v):
        try:
            string_to_timedelta(v)
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM:SS")
        return v


class TaskCreate(BaseModel):
    title: str
    description: str
    original_length: str  # in format "HH:MM:SS"
    subtasks: Optional[List[SubTaskCreate]] = []

    @validator("original_length")
    def validate_original_length(cls, v):
        try:
            string_to_timedelta(v)
        except ValueError:
            raise ValueError("Invalid time format. Use HH:MM:SS")
        return v


class SubTaskResponse(BaseModel):
    id: int
    description: str
    completed: bool


class TaskExtensionResponse(BaseModel):
    id: int
    extension_length: str
    extension_time: str  # ISO format datetime string


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    time_created: str  # ISO format datetime string
    original_length: str
    time_remaining: str
    is_complete: bool
    completed_at: Optional[str]  # ISO format datetime string
    subtasks: List[SubTaskResponse]
    extensions: List[TaskExtensionResponse]

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        # Convert datetime fields to ISO format strings
        d = {}
        for field in cls.__fields__:
            value = getattr(obj, field)
            if isinstance(value, datetime):
                d[field] = value.isoformat()
            elif isinstance(value, timedelta):
                d[field] = timedelta_to_string(value)
            else:
                d[field] = value
        return cls(**d)


class TaskOrderUpdate(BaseModel):
    task_ids: List[int]


@router.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    original_length = string_to_timedelta(task.original_length)
    local_tz = get_localzone()
    db_task = Task(
        title=task.title,
        description=task.description,
        original_length=original_length,
        time_remaining=original_length,
        time_created=datetime.now(local_tz),
    )
    db.add(db_task)
    db.flush()  # This assigns an ID to db_task

    for subtask in task.subtasks:
        db_subtask = SubTask(description=subtask.description, parent_task=db_task)
        db.add(db_subtask)

    # Add the new task to the end of the order
    max_order = db.query(func.coalesce(func.max(TaskOrder.order), 0)).scalar()
    db_task_order = TaskOrder(task_id=db_task.id, order=max_order + 1)
    db.add(db_task_order)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # If there's a conflict, query for the highest order again and use that
        max_order = db.query(func.coalesce(func.max(TaskOrder.order), 0)).scalar()
        db_task_order.order = max_order + 1
        db.add(db_task_order)
        db.commit()

    db.refresh(db_task)
    return db_task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Remove the task from the order
    db_task_order = db.query(TaskOrder).filter(TaskOrder.task_id == task_id).first()
    if db_task_order:
        db.delete(db_task_order)
        # Reorder the remaining tasks
        db.query(TaskOrder).filter(TaskOrder.order > db_task_order.order).update(
            {"order": TaskOrder.order - 1}
        )

    db.delete(db_task)
    db.commit()
    return {"detail": "Task deleted successfully"}


@router.put("/tasks/reorder", status_code=200)
def reorder_tasks(task_order: TaskOrderUpdate, db: Session = Depends(get_db)):
    for index, task_id in enumerate(task_order.task_ids, start=1):
        db_task_order = db.query(TaskOrder).filter(TaskOrder.task_id == task_id).first()
        if db_task_order:
            db_task_order.order = index
        else:
            db.add(TaskOrder(task_id=task_id, order=index))
    db.commit()
    return {"detail": "Tasks reordered successfully"}


@router.get("/tasks/incomplete", response_model=List[TaskResponse])
def get_incomplete_tasks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    tasks = (
        db.query(Task)
        .join(TaskOrder)
        .filter(Task.is_complete == False)
        .order_by(TaskOrder.order)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return tasks


@router.put("/tasks/{task_id}/update-time", response_model=TaskResponse)
def update_task_time(task_id: int, time_elapsed: str, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    elapsed = string_to_timedelta(time_elapsed)
    db_task.time_remaining -= elapsed
    if db_task.time_remaining <= timedelta(0):
        db_task.is_complete = True
        db_task.completed_at = datetime.now(get_localzone())
        db_task.time_remaining = timedelta(0)

    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/tasks/incomplete", response_model=List[TaskResponse])
def get_incomplete_tasks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    tasks = (
        db.query(Task)
        .filter(Task.is_complete == False)
        .order_by(desc(Task.time_created))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/extend", response_model=TaskResponse)
def extend_task(
    task_id: int, extension: TaskExtensionCreate, db: Session = Depends(get_db)
):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    extension_length = string_to_timedelta(extension.extension_length)
    db_extension = TaskExtension(
        task_id=db_task.id,
        extension_length=extension_length,
        extension_time=datetime.utcnow(),
    )
    db.add(db_extension)
    db_task.time_remaining += extension_length

    db.commit()
    db.refresh(db_task)
    return db_task
