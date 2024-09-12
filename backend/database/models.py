from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, ForeignKey, Interval, Text, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

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
    __tablename__ = "day_plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    mode = Column(String)
    date = Column(Date, index=True)  # Keep the separate date field
    start_time = Column(Time, index=True)  # Change back to Time
    end_time = Column(Time, index=True)  # Change back to Time
    start_datetime = Column(DateTime, index=True)  # Add this for datetime operations
    end_datetime = Column(DateTime, index=True)  # Add this for datetime operations
    location = Column(String, nullable=True)
    status = Column(String, nullable=True)
    description = Column(String, nullable=True)
    attendees = Column(ARRAY(String), nullable=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id"))
    google_event_id = Column(String, nullable=True)

    daily_record = relationship("DailyRecord", back_populates="day_plans")
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
    time_created = Column(String)
    original_length = Column(String)
    time_remaining = Column(String)
    is_complete = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    subtasks = relationship("SubTask", back_populates="parent_task", cascade="all, delete-orphan")
    extensions = relationship("TaskExtension", back_populates="task", cascade="all, delete-orphan")
    task_order = relationship("TaskOrder", back_populates="task", uselist=False, cascade="all, delete-orphan")

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
    extension_length = Column(Interval)
    extension_time = Column(DateTime)

    task = relationship("Task", back_populates="extensions")

class TaskOrder(Base):
    __tablename__ = "task_orders"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), unique=True)
    order = Column(Integer, unique=True) 

    task = relationship("Task", back_populates="task_order")

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