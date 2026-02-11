from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RecurrencePattern(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: Optional[str] = None
    priority: Priority = Field(default=Priority.MEDIUM)
    status: TaskStatus = Field(default=TaskStatus.TODO)
    due_date: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    tags: Optional[str] = Field(default=None)  # Comma-separated tags
    recurrence_pattern: Optional[RecurrencePattern] = Field(default=None)
    recurrence_end_date: Optional[datetime] = Field(default=None)
    parent_task_id: Optional[int] = Field(default=None, foreign_key="task.id")  # For recurring tasks
    reminder_sent: bool = Field(default=False)


class TaskCreate(SQLModel):
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    tags: Optional[str] = None
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[datetime] = None


class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None
    tags: Optional[str] = None
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[datetime] = None


class TaskFilter(SQLModel):
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    tag: Optional[str] = None
    due_after: Optional[datetime] = None
    due_before: Optional[datetime] = None
    search: Optional[str] = None
    sort_by: Optional[str] = "created_at"  # created_at, due_date, priority
    sort_order: Optional[str] = "asc"  # asc, desc