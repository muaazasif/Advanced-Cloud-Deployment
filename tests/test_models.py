import pytest
from api.models import Task, TaskCreate, TaskUpdate, TaskFilter, TaskStatus, Priority
from datetime import datetime
from pydantic import ValidationError


def test_task_model_creation():
    """Test creating a Task model instance"""
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": Priority.MEDIUM,
        "status": TaskStatus.TODO
    }
    
    task = Task(**task_data)
    
    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert task.priority == Priority.MEDIUM
    assert task.status == TaskStatus.TODO


def test_task_create_model():
    """Test creating a TaskCreate model instance"""
    task_create_data = {
        "title": "New Task",
        "description": "New Description",
        "priority": "high"
    }
    
    task_create = TaskCreate(**task_create_data)
    
    assert task_create.title == "New Task"
    assert task_create.description == "New Description"
    assert task_create.priority == Priority.HIGH


def test_task_update_model():
    """Test creating a TaskUpdate model instance"""
    task_update_data = {
        "title": "Updated Task",
        "priority": "low",
        "status": "in_progress"
    }
    
    task_update = TaskUpdate(**task_update_data)
    
    assert task_update.title == "Updated Task"
    assert task_update.priority == Priority.LOW
    assert task_update.status == TaskStatus.IN_PROGRESS


def test_task_filter_model():
    """Test creating a TaskFilter model instance"""
    filter_data = {
        "status": "completed",
        "priority": "high",
        "search": "important",
        "sort_by": "due_date",
        "sort_order": "desc"
    }
    
    task_filter = TaskFilter(**filter_data)
    
    assert task_filter.status == TaskStatus.COMPLETED
    assert task_filter.priority == Priority.HIGH
    assert task_filter.search == "important"
    assert task_filter.sort_by == "due_date"
    assert task_filter.sort_order == "desc"


def test_task_required_fields():
    """Test that required fields are enforced"""
    with pytest.raises(ValidationError):
        TaskCreate(priority="medium", status="todo")  # Missing required 'title'


def test_task_optional_fields():
    """Test that optional fields can be omitted"""
    task_create = TaskCreate(title="Test Task", priority="medium")
    
    assert task_create.title == "Test Task"
    assert task_create.priority == Priority.MEDIUM
    assert task_create.description is None  # Optional field should be None


def test_task_status_enum_values():
    """Test that TaskStatus enum has the expected values"""
    assert TaskStatus.TODO.value == "todo"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.COMPLETED.value == "completed"


def test_priority_enum_values():
    """Test that Priority enum has the expected values"""
    assert Priority.LOW.value == "low"
    assert Priority.MEDIUM.value == "medium"
    assert Priority.HIGH.value == "high"


def test_task_default_values():
    """Test default values for Task model"""
    task = Task(
        title="Test Task",
        priority=Priority.MEDIUM,
        status=TaskStatus.TODO
    )
    
    # Check that timestamps are set appropriately
    assert task.created_at is not None
    assert task.updated_at is not None
    assert task.reminder_sent is False