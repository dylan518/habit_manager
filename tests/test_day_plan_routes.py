import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date, time
from unittest.mock import patch

from backend.database.database import get_db
from backend.database.models import Base
from backend.app import app

# Use in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_google_calendar():
    with patch("backend.routers.day_plans.get_calendar_service") as mock:
        yield mock


def test_add_day_plan(client, mock_google_calendar):
    mock_google_calendar.return_value.events.return_value.insert.return_value.execute.return_value = {
        "id": "test_google_id"
    }

    response = client.post(
        "/api/dayplans",
        json={
            "title": "Test Day Plan",
            "mode": "work",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "description": "Test description",
            "location": "Test location",
            "attendees": ["test@example.com"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Day Plan"
    assert data["mode"] == "work"
    assert "id" in data
    assert data["google_event_id"] == "test_google_id"


def test_get_day_plans(client, mock_google_calendar):
    # Add a day plan
    client.post(
        "/api/dayplans",
        json={
            "title": "Test Day Plan",
            "mode": "work",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    )

    # Mock Google Calendar response
    mock_google_calendar.return_value.events.return_value.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "google_event_id",
                "summary": "Google Calendar Event",
                "start": {"dateTime": f"{date.today()}T10:00:00"},
                "end": {"dateTime": f"{date.today()}T11:00:00"},
            }
        ]
    }

    response = client.get("/api/dayplans")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # At least the one we added and the one from Google Calendar
    assert any(plan["title"] == "Test Day Plan" for plan in data)
    assert any(plan["title"] == "Google Calendar Event" for plan in data)


def test_update_day_plan(client, mock_google_calendar):
    # Add a day plan
    add_response = client.post(
        "/api/dayplans",
        json={
            "title": "Test Day Plan",
            "mode": "work",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    )
    day_plan_id = add_response.json()["id"]

    # Update the day plan
    update_response = client.put(
        f"/api/dayplans/{day_plan_id}",
        json={
            "title": "Updated Day Plan",
            "mode": "personal",
            "start_time": "10:00:00",
            "end_time": "18:00:00",
        },
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["title"] == "Updated Day Plan"
    assert updated_data["mode"] == "personal"
    assert updated_data["start_time"] == "10:00:00"
    assert updated_data["end_time"] == "18:00:00"


def test_delete_day_plan(client, mock_google_calendar):
    # Add a day plan
    add_response = client.post(
        "/api/dayplans",
        json={
            "title": "Day Plan to Delete",
            "mode": "work",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    )
    day_plan_id = add_response.json()["id"]

    # Delete the day plan
    delete_response = client.delete(f"/api/dayplans/{day_plan_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Day plan deleted successfully"

    # Verify that the day plan has been deleted
    get_response = client.get("/api/dayplans")
    assert get_response.status_code == 200
    day_plans = get_response.json()
    assert not any(plan["id"] == day_plan_id for plan in day_plans)


def test_get_current_event(client, mock_google_calendar):
    # Add two day plans
    client.post(
        "/api/dayplans",
        json={
            "title": "Past Event",
            "mode": "work",
            "start_time": "08:00:00",
            "end_time": "09:00:00",
        },
    )
    client.post(
        "/api/dayplans",
        json={
            "title": "Current Event",
            "mode": "work",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    )

    # Mock the current time to be 10:00:00
    with patch("backend.routers.day_plans.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime.combine(date.today(), time(10, 0))

        response = client.get("/api/current-event")
        assert response.status_code == 200
        current_event = response.json()
        assert current_event["title"] == "Current Event"


if __name__ == "__main__":
    pytest.main([__file__])
