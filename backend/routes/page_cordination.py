from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import DailyProgress, DayPlan, Task, TaskOrder
from datetime import date, datetime, time
from pydantic import BaseModel
from typing import Optional, List
import logging
from tzlocal import get_localzone

router = APIRouter()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)


class CurrentActivityResponse(BaseModel):
    activity_type: str  # 'event', 'habit_page', 'queue', or 'schedule'
    page_number: Optional[int] = None
    event_info: Optional[dict] = None


class SetPageRequest(BaseModel):
    page_number: int


class DayPlanResponse(BaseModel):
    id: int
    title: str
    mode: str
    date: date
    start_time: time
    end_time: time
    location: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    attendees: Optional[List[str]] = None


@router.get("/current-activity", response_model=CurrentActivityResponse)
def get_current_activity(db: Session = Depends(get_db)):
    local_tz = get_localzone()
    now = datetime.now(local_tz)
    current_date = now.date()
    current_time = now.time()
    logger.info(f"Current time: {current_time}")

    current_day_plan = (
        db.query(DayPlan)
        .filter(
            DayPlan.date == current_date,
            DayPlan.start_time <= current_time,
            DayPlan.end_time > current_time,
        )
        .first()
    )

    if current_day_plan and current_day_plan.mode != "work":
        logger.debug(f"Current event exists: {current_day_plan.title}")
        # This is an event block
        process_event(db, current_day_plan, now)
        return create_event_response(current_day_plan)

    # Check for current habit page
    daily_progress = get_or_create_daily_progress(db, current_date)
    logger.info(f"current page {daily_progress.current_page}")
    if daily_progress.current_page < 3:  # Assuming 3 habit pages before queue
        logger.info(f"bring to page {daily_progress.current_page}")
        return CurrentActivityResponse(
            activity_type="habit_page", page_number=daily_progress.current_page
        )

    if current_day_plan and current_day_plan.mode == "work":
        # This is a work block
        tasks_in_queue = (
            db.query(Task).join(TaskOrder).filter(Task.is_complete == False).first()
        )
        if tasks_in_queue:
            logger.info("Work block with tasks in queue, opening event timer")
            return create_event_response(current_day_plan)

    logger.info(
        "No current event, habit pages, or work block with tasks, defaulting to queue"
    )
    return CurrentActivityResponse(activity_type="queue")


def create_event_response(day_plan):
    return CurrentActivityResponse(
        activity_type="event",
        event_info=DayPlanResponse(
            id=day_plan.id,
            title=day_plan.title,
            mode=day_plan.mode,
            date=day_plan.date,
            start_time=day_plan.start_time,
            end_time=day_plan.end_time,
            location=day_plan.location,
            status=day_plan.status,
            description=day_plan.description,
            attendees=day_plan.attendees,
        ).dict(),
    )


@router.put("/current-activity/set-page", response_model=CurrentActivityResponse)
def set_current_page(request: SetPageRequest, db: Session = Depends(get_db)):
    today = date.today()
    daily_progress = get_or_create_daily_progress(db, today)
    daily_progress.current_page = request.page_number
    db.commit()
    db.refresh(daily_progress)

    return CurrentActivityResponse(
        activity_type="habit_page", page_number=daily_progress.current_page
    )


def process_event(db: Session, day_plan: DayPlan, now: datetime):
    existing_task = db.query(Task).filter(Task.title == day_plan.title).first()
    if not existing_task:
        new_task = Task(
            title=day_plan.title,
            description=day_plan.description or "",
            original_length=(day_plan.end_time - day_plan.start_time).seconds,
            time_remaining=(day_plan.end_time - now.time()).seconds,
            time_created=now,
        )
        db.add(new_task)
        db.flush()

        max_order = db.query(TaskOrder).count()
        db_task_order = TaskOrder(task_id=new_task.id, order=max_order + 1)
        db.add(db_task_order)
        db.commit()


def get_or_create_daily_progress(db: Session, current_date: date) -> DailyProgress:
    daily_progress = (
        db.query(DailyProgress).filter(DailyProgress.date == current_date).first()
    )
    if not daily_progress:
        daily_progress = DailyProgress(date=current_date, current_page=0)
        db.add(daily_progress)
        db.commit()
        db.refresh(daily_progress)
    return daily_progress
