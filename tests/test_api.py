import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.database import get_session, engine
from api.models import Task, TaskCreate, TaskStatus, Priority
from sqlmodel import Session, SQLModel, create_engine
from unittest.mock import AsyncMock


@pytest.fixture(scope="function")
def test_client():
    """Create a test client for the API"""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def mock_db_session():
    """Create a mock database session for testing"""
    # Create an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=True)
    SQLModel.metadata.create_all(bind=engine)
    
    with Session(engine) as session:
        yield session


def test_health_check(test_client):
    """Test the health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "message": "Todo Chatbot API is running"}


def test_create_task(test_client, mock_db_session):
    """Test creating a new task"""
    # Mock the database session dependency
    app.dependency_overrides[get_session] = lambda: mock_db_session
    
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "medium"
    }
    
    response = test_client.post("/tasks/", json=task_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["priority"] == "medium"


def test_get_tasks(test_client, mock_db_session):
    """Test getting all tasks"""
    # Mock the database session dependency
    app.dependency_overrides[get_session] = lambda: mock_db_session
    
    # First create a task
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "medium"
    }
    
    create_response = test_client.post("/tasks/", json=task_data)
    assert create_response.status_code == 200
    
    # Then get all tasks
    response = test_client.get("/tasks/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Task"


def test_get_single_task(test_client, mock_db_session):
    """Test getting a single task by ID"""
    # Mock the database session dependency
    app.dependency_overrides[get_session] = lambda: mock_db_session
    
    # First create a task
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "medium"
    }
    
    create_response = test_client.post("/tasks/", json=task_data)
    assert create_response.status_code == 200
    created_task = create_response.json()
    task_id = created_task["id"]
    
    # Then get the specific task
    response = test_client.get(f"/tasks/{task_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Test Task"


def test_update_task(test_client, mock_db_session):
    """Test updating a task"""
    # Mock the database session dependency
    app.dependency_overrides[get_session] = lambda: mock_db_session
    
    # First create a task
    task_data = {
        "title": "Original Task",
        "description": "Original Description",
        "priority": "medium"
    }
    
    create_response = test_client.post("/tasks/", json=task_data)
    assert create_response.status_code == 200
    created_task = create_response.json()
    task_id = created_task["id"]
    
    # Then update the task
    update_data = {
        "title": "Updated Task",
        "status": "in_progress"
    }
    
    response = test_client.put(f"/tasks/{task_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Updated Task"
    assert data["status"] == "in_progress"


def test_delete_task(test_client, mock_db_session):
    """Test deleting a task"""
    # Mock the database session dependency
    app.dependency_overrides[get_session] = lambda: mock_db_session
    
    # First create a task
    task_data = {
        "title": "Test Task to Delete",
        "description": "Test Description",
        "priority": "medium"
    }
    
    create_response = test_client.post("/tasks/", json=task_data)
    assert create_response.status_code == 200
    created_task = create_response.json()
    task_id = created_task["id"]
    
    # Then delete the task
    response = test_client.delete(f"/tasks/{task_id}")
    
    assert response.status_code == 200
    
    # Verify the task is gone
    get_response = test_client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404


def test_complete_task(test_client, mock_db_session):
    """Test completing a task"""
    # Mock the database session dependency
    app.dependency_overrides[get_session] = lambda: mock_db_session
    
    # First create a task
    task_data = {
        "title": "Test Task to Complete",
        "description": "Test Description",
        "priority": "medium"
    }
    
    create_response = test_client.post("/tasks/", json=task_data)
    assert create_response.status_code == 200
    created_task = create_response.json()
    task_id = created_task["id"]
    
    # Then complete the task
    response = test_client.post(f"/tasks/{task_id}/complete")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["status"] == "completed"


def test_main_page_returns_html(test_client):
    """Test that the main page returns HTML content"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_app_page_returns_html(test_client):
    """Test that the app page returns HTML content"""
    response = test_client.get("/app")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]