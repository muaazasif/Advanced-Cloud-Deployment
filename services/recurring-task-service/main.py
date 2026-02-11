import json
from kafka import KafkaConsumer
from datetime import datetime
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
from enum import Enum
import threading
import os
from dateutil.relativedelta import relativedelta

# Models (same as in chat-api for consistency)
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


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


class RecurringTaskProcessor:
    def __init__(self):
        kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.consumer = KafkaConsumer(
            'task-events',
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='recurring-task-service'
        )
        
        # Import Kafka producer for publishing new tasks
        from kafka_producer import kafka_producer
        self.kafka_producer = kafka_producer

    def start_processing(self):
        """Start processing messages from Kafka"""
        print("Starting Recurring Task Processor...")
        for message in self.consumer:
            try:
                event_data = message.value
                event_type = event_data.get('event_type')
                
                if event_type == 'task.completed':
                    self.handle_task_completed(event_data)
                    
            except Exception as e:
                print(f"Error processing message: {e}")

    def handle_task_completed(self, event_data):
        """Handle completed task events and create recurring tasks if needed"""
        task_data = event_data.get('task_data', {})
        task_id = event_data.get('task_id')
        
        # Check if this task has recurrence pattern
        if task_data.get('recurrence_pattern'):
            print(f"Processing recurring task for task ID: {task_id}")
            self.create_next_occurrence(task_data)

    def create_next_occurrence(self, completed_task_data):
        """Create the next occurrence of a recurring task"""
        with next(get_session()) as session:
            # Calculate next occurrence date based on recurrence pattern
            next_due_date = self.calculate_next_occurrence(
                completed_task_data.get('due_date'),
                completed_task_data.get('recurrence_pattern')
            )
            
            # Check if recurrence end date has been reached
            recurrence_end_date = completed_task_data.get('recurrence_end_date')
            if recurrence_end_date and next_due_date > datetime.fromisoformat(recurrence_end_date):
                print(f"Recurrence end date reached for task {completed_task_data.get('id')}")
                return  # Stop recurrence
            
            # Create a new task for the next occurrence
            new_task = Task(
                title=completed_task_data.get('title'),
                description=completed_task_data.get('description'),
                priority=completed_task_data.get('priority', 'medium'),
                due_date=next_due_date,
                tags=completed_task_data.get('tags'),
                recurrence_pattern=completed_task_data.get('recurrence_pattern'),
                recurrence_end_date=recurrence_end_date,
                parent_task_id=completed_task_data.get('id')  # Link to parent task
            )
            
            session.add(new_task)
            session.commit()
            
            print(f"Created next occurrence for task '{completed_task_data.get('title')}' due on {next_due_date}")
            
            # Publish event for the new task
            event_data = {
                'event_type': 'task.created',
                'task_id': new_task.id,
                'task_data': new_task.model_dump(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.kafka_producer.publish_event('task-events', event_data))
            loop.close()


def main():
    processor = RecurringTaskProcessor()
    processor.start_processing()


if __name__ == "__main__":
    main()