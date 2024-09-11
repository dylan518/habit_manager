from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import DayPlan, DailyRecord
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, time, datetime
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from zoneinfo import ZoneInfo
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

CLIENT_SECRETS_FILE = "credentials.env"


def get_calendar_service():
    try:
        with open("token.json", "r") as token_file:
            creds_data = json.load(token_file)
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        return build("calendar", "v3", credentials=creds)
    except FileNotFoundError:
        raise HTTPException(status_code=401, detail="Authentication required")


class DayPlanBase(BaseModel):
    title: str
    mode: str
    date: date
    start_time: time
    end_time: time
    location: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    attendees: Optional[List[str]] = None


class DayPlanCreate(BaseModel):
    title: str
    mode: str
    start_time: time
    end_time: time
    location: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    attendees: Optional[List[str]] = Field(default_factory=list)

    class Config:
        extra = "forbid"  # This will raise an error if extra fields are provided


class DayPlanUpdate(BaseModel):
    title: Optional[str] = None
    mode: Optional[str] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    attendees: Optional[List[str]] = None


class DayPlanResponse(DayPlanBase):
    id: int
    daily_record_id: int
    mode: str  # Make this required

    class Config:
        orm_mode = True


def sync_with_google_calendar(
    db: Session, day_plan: DayPlan, service, operation="create"
):
    time_zone = "America/Los_Angeles"  # Replace with your desired time zone
    event = {
        "summary": day_plan.title,
        "location": day_plan.location,
        "description": day_plan.description,
        "start": {
            "dateTime": datetime.combine(day_plan.date, day_plan.start_time)
            .replace(tzinfo=ZoneInfo(time_zone))
            .isoformat(),
            "timeZone": time_zone,
        },
        "end": {
            "dateTime": datetime.combine(day_plan.date, day_plan.end_time)
            .replace(tzinfo=ZoneInfo(time_zone))
            .isoformat(),
            "timeZone": time_zone,
        },
        "attendees": [{"email": attendee} for attendee in (day_plan.attendees or [])],
        "extendedProperties": {"private": {"mode": day_plan.mode}},
    }

    try:
        if operation == "create":
            created_event = (
                service.events().insert(calendarId="primary", body=event).execute()
            )
            day_plan.google_event_id = created_event["id"]
            db.commit()
            logger.info(
                f"Created Google Calendar event with ID: {created_event['id']} and mode: {day_plan.mode}"
            )
        elif operation == "update":
            if not day_plan.google_event_id:
                logger.error(
                    f"Attempted to update event without google_event_id: {day_plan.id}"
                )
                raise ValueError("Cannot update event: missing google_event_id")
            service.events().update(
                calendarId="primary",
                eventId=day_plan.google_event_id,
                body=event,
            ).execute()
            logger.info(
                f"Updated Google Calendar event with ID: {day_plan.google_event_id} and mode: {day_plan.mode}"
            )
        elif operation == "delete":
            if not day_plan.google_event_id:
                logger.error(
                    f"Attempted to delete event without google_event_id: {day_plan.id}"
                )
                raise ValueError("Cannot delete event: missing google_event_id")
            service.events().delete(
                calendarId="primary", eventId=day_plan.google_event_id
            ).execute()
            logger.info(
                f"Deleted Google Calendar event with ID: {day_plan.google_event_id}"
            )
    except HttpError as error:
        logger.error(f"An error occurred with Google Calendar API: {error}")
        raise HTTPException(
            status_code=500, detail=f"Google Calendar API error: {str(error)}"
        )


@router.post("/dayplans", response_model=DayPlanResponse)
def add_day_plan(day_plan: DayPlanCreate, db: Session = Depends(get_db)):
    try:
        today = date.today()
        daily_record = db.query(DailyRecord).filter(DailyRecord.date == today).first()
        if not daily_record:
            daily_record = DailyRecord(date=today)
            db.add(daily_record)
            db.commit()

        new_day_plan = DayPlan(
            title=day_plan.title,
            mode=day_plan.mode,
            description=day_plan.description,
            date=today,
            start_time=day_plan.start_time,
            end_time=day_plan.end_time,
            location=day_plan.location,
            attendees=day_plan.attendees,
            status=day_plan.status,
            daily_record_id=daily_record.id,
        )
        db.add(new_day_plan)
        db.commit()
        db.refresh(new_day_plan)

        logger.info(f"Adding day plan with mode: {day_plan.mode}")

        # Sync with Google Calendar
        service = get_calendar_service()
        sync_with_google_calendar(db, new_day_plan, service, "create")

        return new_day_plan
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in add_day_plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/dayplans/{day_plan_id}", response_model=DayPlanResponse)
def update_day_plan(
    day_plan_id: int, day_plan_update: DayPlanUpdate, db: Session = Depends(get_db)
):
    try:
        db_day_plan = db.query(DayPlan).filter(DayPlan.id == day_plan_id).first()
        if db_day_plan is None:
            raise HTTPException(status_code=404, detail="Day plan not found")

        update_data = day_plan_update.dict(exclude_unset=True)
        if "attendees" in update_data:
            update_data["attendees"] = update_data["attendees"] or []
        for key, value in update_data.items():
            setattr(db_day_plan, key, value)

        db.commit()
        db.refresh(db_day_plan)

        logger.info(
            f"Updating day plan {day_plan_id} with mode: {update_data.get('mode', 'unchanged')}"
        )

        # Sync with Google Calendar
        service = get_calendar_service()
        sync_with_google_calendar(db, db_day_plan, service, "update")

        return db_day_plan
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in update_day_plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/dayplans", response_model=List[DayPlanResponse])
def get_day_plans(db: Session = Depends(get_db)):
    try:
        today = date.today()
        logger.info(f"Fetching day plans for today: {today}")

        # Ensure we have a DailyRecord for today
        daily_record = db.query(DailyRecord).filter(DailyRecord.date == today).first()
        if not daily_record:
            daily_record = DailyRecord(date=today)
            db.add(daily_record)
            db.commit()
            db.refresh(daily_record)

        day_plans = (
            db.query(DayPlan)
            .filter(func.date(DayPlan.date) == today)
            .order_by(DayPlan.start_time)
            .all()
        )

        # Sync with Google Calendar
        service = get_calendar_service()
        start_of_day = datetime.combine(today, time.min).isoformat() + "Z"
        end_of_day = datetime.combine(today, time.max).isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        # Update local database with new events from Google Calendar
        for event in events:
            existing_plan = next(
                (plan for plan in day_plans if plan.google_event_id == event["id"]),
                None,
            )
            if not existing_plan:
                # Retrieve the mode from extended properties
                mode = (
                    event.get("extendedProperties", {})
                    .get("private", {})
                    .get("mode", "event")
                )
                new_plan = DayPlan(
                    title=event["summary"],
                    description=event.get("description", ""),
                    date=today,
                    start_time=datetime.fromisoformat(
                        event["start"]["dateTime"]
                    ).time(),
                    end_time=datetime.fromisoformat(event["end"]["dateTime"]).time(),
                    location=event.get("location", ""),
                    attendees=[
                        attendee["email"] for attendee in event.get("attendees", [])
                    ],
                    google_event_id=event["id"],
                    daily_record_id=daily_record.id,
                    mode=mode,  # Set the mode here
                )
                db.add(new_plan)
                day_plans.append(new_plan)

        db.commit()
        logger.info(f"Found {len(day_plans)} day plans for today")

        return day_plans
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_day_plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_day_plans: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.delete("/dayplans/{day_plan_id}", response_model=dict)
def delete_day_plan(day_plan_id: int, db: Session = Depends(get_db)):
    try:
        db_day_plan = db.query(DayPlan).filter(DayPlan.id == day_plan_id).first()
        if db_day_plan is None:
            raise HTTPException(status_code=404, detail="Day plan not found")

        # Sync with Google Calendar only if google_event_id exists
        if db_day_plan.google_event_id:
            try:
                service = get_calendar_service()
                sync_with_google_calendar(db, db_day_plan, service, "delete")
            except ValueError as e:
                logger.warning(f"Failed to delete Google Calendar event: {str(e)}")
        else:
            logger.info(
                f"Day plan {day_plan_id} has no associated Google Calendar event. Skipping Google Calendar sync."
            )

        db.delete(db_day_plan)
        db.commit()
        return {"message": "Day plan deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in delete_day_plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in delete_day_plan: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


class IsWorkingResponse(BaseModel):
    is_working: bool
    current_plan: Optional[DayPlanResponse] = None


@router.get("/current-event", response_model=Optional[DayPlanResponse])
def get_current_event(db: Session = Depends(get_db)):
    try:
        now = datetime.now()
        today = now.date()
        current_time = now.time()

        current_event = (
            db.query(DayPlan)
            .filter(
                func.date(DayPlan.date) == today,
                DayPlan.start_time <= current_time,
                DayPlan.end_time > current_time,
            )
            .first()
        )

        return current_event
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_current_event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_current_event: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )
