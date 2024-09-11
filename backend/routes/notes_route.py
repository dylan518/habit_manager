from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, date
from typing import List
from pydantic import BaseModel

from backend.database.database import get_db
from backend.database.models import Reminder, Goal


router = APIRouter()


class ReminderCreate(BaseModel):
    content: str


class GoalCreate(BaseModel):
    content: str


class ReminderResponse(BaseModel):
    id: int
    content: str
    last_updated: datetime

    class Config:
        orm_mode = True


class GoalResponse(BaseModel):
    id: int
    content: str
    date: date

    class Config:
        orm_mode = True


@router.post("/reminders", response_model=ReminderResponse)
def create_reminder(reminder: ReminderCreate, db: Session = Depends(get_db)):
    db_reminder = Reminder(content=reminder.content, last_updated=datetime.now())
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder


@router.post("/goals", response_model=GoalResponse)
def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    db_goal = Goal(content=goal.content, date=datetime.now())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal


@router.get("/latest", response_model=dict)
def get_latest_notes(db: Session = Depends(get_db)):
    latest_reminder = db.query(Reminder).order_by(desc(Reminder.last_updated)).first()
    latest_goal = db.query(Goal).order_by(desc(Goal.date)).first()
    return {
        "latest_reminder": (
            ReminderResponse.from_orm(latest_reminder) if latest_reminder else None
        ),
        "latest_goal": GoalResponse.from_orm(latest_goal) if latest_goal else None,
    }


@router.get("/reminders", response_model=List[ReminderResponse])
def get_Reminders(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    Reminders = (
        db.query(Reminder)
        .order_by(desc(Reminder.last_updated))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return Reminders


@router.get("/goals", response_model=List[GoalResponse])
def get_goals(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    goals = db.query(Goal).order_by(desc(Goal.date)).offset(skip).limit(limit).all()
    return goals
