import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, timedelta

from backend.main import app  # adjust this import based on your project structure
from backend.database.models import Base, ToDo, Goal

from backend.database.database import get_db

# Setup test database
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


def test_create_todo(test_db):
    response = client.post("/notes/todos", json={"content": "Test ToDo"})
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test ToDo"
    assert "id" in data
    assert "last_updated" in data


def test_create_goal(test_db):
    response = client.post(
        "/notes/goals", json={"content": "Test Goal", "date": str(date.today())}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test Goal"
    assert data["date"] == str(date.today())
    assert "id" in data


def test_get_latest_notes(test_db):
    # Create some test data
    client.post("/notes/todos", json={"content": "Old ToDo"})
    client.post(
        "/notes/goals",
        json={"content": "Old Goal", "date": str(date.today() - timedelta(days=1))},
    )
    client.post("/notes/todos", json={"content": "New ToDo"})
    client.post("/notes/goals", json={"content": "New Goal", "date": str(date.today())})

    response = client.get("/notes/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["latest_todo"]["content"] == "New ToDo"
    assert data["latest_goal"]["content"] == "New Goal"


def test_get_todos(test_db):
    # Create some test data
    for i in range(15):
        client.post("/notes/todos", json={"content": f"ToDo {i}"})

    response = client.get("/notes/todos?skip=5&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["content"] == "ToDo 9"  # Assuming reverse chronological order


def test_get_goals(test_db):
    # Create some test data
    for i in range(15):
        client.post(
            "/notes/goals",
            json={
                "content": f"Goal {i}",
                "date": str(date.today() - timedelta(days=i)),
            },
        )

    response = client.get("/notes/goals?skip=5&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["content"] == "Goal 5"  # Assuming reverse chronological order


if __name__ == "__main__":
    # Run the current test file directly
    pytest.main([__file__])
