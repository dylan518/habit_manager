import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, Text
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database.models import Base, DayPlan
from backend.database.database import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def patched_dayplan():
    with patch("backend.database.models.DayPlan") as mock_dayplan:
        mock_dayplan.attendees = Column(Text, nullable=True)
        yield mock_dayplan


@pytest.mark.usefixtures("patched_dayplan")
class TestTimeRoutes:
    def test_decrement_task_time(self, test_db):
        # Create a task
        response = client.post(
            "/tasks/",
            json={
                "title": "Test Task",
                "original_length": 3600,
                "time_remaining": 3600,
            },
        )
        assert response.status_code == 200
        task_id = response.json()["id"]

        # Decrement time
        response = client.put(f"/tasks/{task_id}/decrement-time")
        assert response.status_code == 200
        data = response.json()
        assert data["time_remaining"] == 3599
        assert data["is_complete"] == False

    def test_get_total_time(self, test_db):
        # Create a task
        response = client.post(
            "/tasks/",
            json={
                "title": "Test Task",
                "original_length": 7200,
                "time_remaining": 7200,
            },
        )
        assert response.status_code == 200
        task_id = response.json()["id"]

        # Get total time
        response = client.get(f"/tasks/{task_id}/total-time")
        assert response.status_code == 200
        data = response.json()
        assert data["total_time"] == 7200

    def test_get_time_remaining(self, test_db):
        # Create a task
        response = client.post(
            "/tasks/",
            json={
                "title": "Test Task",
                "original_length": 5400,
                "time_remaining": 5400,
            },
        )
        assert response.status_code == 200
        task_id = response.json()["id"]

        # Get time remaining
        response = client.get(f"/tasks/{task_id}/time-remaining")
        assert response.status_code == 200
        data = response.json()
        assert data["time_remaining"] == 5400


# Add more test cases as needed

if __name__ == "__main__":
    pytest.main([__file__])
