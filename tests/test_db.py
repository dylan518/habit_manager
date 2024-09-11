import pytest
from sqlalchemy.orm import Session
from backend.database.database import engine, SessionLocal
from backend.database.models import Base, Habit, DailyHabit, DailyRecord
from datetime import date


# Set up the database for testing
@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_and_read_habit(db: Session):
    # Create a new habit
    new_habit = Habit(name="Test Habit", associated_app="Test App")
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)

    # Read the habit
    habit = db.query(Habit).filter(Habit.name == "Test Habit").first()
    assert habit is not None
    assert habit.name == "Test Habit"
    assert habit.associated_app == "Test App"


def test_update_habit(db: Session):
    # Create a habit
    habit = Habit(name="Update Test Habit")
    db.add(habit)
    db.commit()

    # Update the habit
    habit.name = "Updated Habit"
    db.commit()
    db.refresh(habit)

    # Verify the update
    updated_habit = db.query(Habit).filter(Habit.id == habit.id).first()
    assert updated_habit.name == "Updated Habit"


def test_delete_habit(db: Session):
    # Create a habit
    habit = Habit(name="Delete Test Habit")
    db.add(habit)
    db.commit()

    # Delete the habit
    db.delete(habit)
    db.commit()

    # Verify the deletion
    deleted_habit = db.query(Habit).filter(Habit.id == habit.id).first()
    assert deleted_habit is None


from datetime import date


def test_create_daily_habit(db: Session):
    # Create a habit
    habit = Habit(name="Daily Habit Test")
    db.add(habit)
    db.commit()

    # Create a daily record for today
    daily_record = DailyRecord(date=date.today())
    db.add(daily_record)
    db.commit()

    # Create a daily habit
    daily_habit = DailyHabit(
        habit_id=habit.id, daily_record_id=daily_record.id, completed=True
    )
    db.add(daily_habit)
    db.commit()

    # Verify the daily habit
    retrieved_daily_habit = (
        db.query(DailyHabit).filter(DailyHabit.habit_id == habit.id).first()
    )
    assert retrieved_daily_habit is not None
    assert retrieved_daily_habit.completed == True
    assert retrieved_daily_habit.habit_id == habit.id
    assert retrieved_daily_habit.daily_record_id == daily_record.id


if __name__ == "__main__":
    pytest.main([__file__])
