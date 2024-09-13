from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, ForeignKey, Interval, Text, ARRAY, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import json
from datetime import datetime, timedelta

Base = declarative_base()

class DailyRecord(Base):
    __tablename__ = "daily_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    current_page = Column(Integer, default=0)

    day_plans = relationship("DayPlan", back_populates="daily_record")
    journals = relationship("Journal", back_populates="daily_record")

class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    exact_time = Column(DateTime, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id"))

    daily_record = relationship("DailyRecord", back_populates="journals")
    sections = relationship("JournalSection", back_populates="journal")


class DayPlan(Base):
    __tablename__ = 'day_plans'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    mode = Column(String)
    date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    start_datetime = Column(DateTime, nullable=True)
    end_datetime = Column(DateTime, nullable=True)
    location = Column(String)
    status = Column(String, nullable=True)
    description = Column(String)
    _attendees = Column(String)  # Store as JSON string
    daily_record_id = Column(Integer, ForeignKey('daily_records.id'))
    google_event_id = Column(String, nullable=True)

    daily_record = relationship("DailyRecord", back_populates="day_plans")

    @property
    def attendees(self):
        return json.loads(self._attendees) if self._attendees else []

    @attendees.setter
    def attendees(self, value):
        self._attendees = json.dumps(value) if value else '[]'
class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    last_updated = Column(DateTime)

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    date = Column(Date)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    time_created = Column(DateTime, default=datetime.utcnow)
    original_length_seconds = Column(Float)  # Store as seconds
    time_remaining_seconds = Column(Float)  # Store as seconds
    is_complete = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    subtasks = relationship(
        "SubTask",
        back_populates="parent_task",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    extensions = relationship(
        "TaskExtension",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    task_order = relationship(
        "TaskOrder",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def original_length(self):
        return (
            timedelta(seconds=self.original_length_seconds)
            if self.original_length_seconds is not None
            else None
        )

    @original_length.setter
    def original_length(self, value):
        if isinstance(value, timedelta):
            self.original_length_seconds = value.total_seconds()
        else:
            self.original_length_seconds = value

    @property
    def time_remaining(self):
        return (
            timedelta(seconds=self.time_remaining_seconds)
            if self.time_remaining_seconds is not None
            else None
        )

    @time_remaining.setter
    def time_remaining(self, value):
        if isinstance(value, timedelta):
            self.time_remaining_seconds = value.total_seconds()
        else:
            self.time_remaining_seconds = value

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "time_created": self.time_created.isoformat()
            if self.time_created
            else None,
            "original_length": timedelta_to_string(self.original_length)
            if self.original_length
            else None,
            "time_remaining": timedelta_to_string(self.time_remaining)
            if self.time_remaining
            else None,
            "is_complete": self.is_complete,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }



class SubTask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    completed = Column(Boolean, default=False)
    task_id = Column(Integer, ForeignKey("tasks.id"))

    parent_task = relationship("Task", back_populates="subtasks")


class TaskExtension(Base):
    __tablename__ = "task_extensions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    extension_length_seconds = Column(Float)  # Store as seconds
    extension_time = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="extensions")

    @property
    def extension_length(self):
        return (
            timedelta(seconds=self.extension_length_seconds)
            if self.extension_length_seconds is not None
            else None
        )

    @extension_length.setter
    def extension_length(self, value):
        if isinstance(value, timedelta):
            self.extension_length_seconds = value.total_seconds()
        else:
            self.extension_length_seconds = value


class TaskOrder(Base):
    __tablename__ = "task_order"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    order = Column(Integer, nullable=False)

    task = relationship("Task", back_populates="task_order")


# Helper functions (ensure these are accessible where needed)
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

class DailyProgress(Base):
    __tablename__ = "daily_progress"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True)
    current_page = Column(Integer, default=0)



class JournalSection(Base):
    __tablename__ = "journal_sections"

    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journals.id"))
    header = Column(String(255))
    content = Column(Text)
    order = Column(Integer)

    journal = relationship("Journal", back_populates="sections")