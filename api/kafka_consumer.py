import json
from kafka import KafkaConsumer
from typing import Callable
import threading
import os
from datetime import datetime
from .models import Task, TaskStatus
from .database import get_session
from sqlmodel import Session, select
from .kafka_producer import kafka_producer

class KafkaEventConsumer:
    def __init__(self):
        kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.consumer = KafkaConsumer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='todo-group'
        )
        
        # Register event handlers
        self.event_handlers = {
            'task.created': self.handle_task_created,
            'task.updated': self.handle_task_updated,
            'task.completed': self.handle_task_completed,
            'task.deleted': self.handle_task_deleted,
            'reminder.triggered': self.handle_reminder_triggered
        }
    
    def start_consuming(self):
        """Start consuming messages from Kafka"""
        self.consumer.subscribe(['task-events', 'reminders', 'task-updates'])
        
        print("Starting Kafka consumer...")
        for message in self.consumer:
            try:
                event_data = message.value
                event_type = event_data.get('event_type')
                
                if event_type in self.event_handlers:
                    handler = self.event_handlers[event_type]
                    handler(event_data)
                else:
                    print(f"No handler for event type: {event_type}")
                    
            except Exception as e:
                print(f"Error processing message: {e}")
    
    def handle_task_created(self, event_data):
        print(f"Handling task created: {event_data}")
        # Additional business logic can be added here
    
    def handle_task_updated(self, event_data):
        print(f"Handling task updated: {event_data}")
        # Additional business logic can be added here
    
    def handle_task_completed(self, event_data):
        print(f"Handling task completed: {event_data}")
        # Check if this is a recurring task and create the next occurrence
        task_id = event_data.get('task_id')
        if task_id:
            self.process_recurring_task_completion(task_id)
    
    def handle_task_deleted(self, event_data):
        print(f"Handling task deleted: {event_data}")
        # Additional business logic can be added here
    
    def handle_reminder_triggered(self, event_data):
        print(f"Handling reminder triggered: {event_data}")
        # Send notification to user
        # This would typically call a notification service
    
    def process_recurring_task_completion(self, task_id: int):
        """Process a completed recurring task and create the next occurrence"""
        with next(get_session()) as session:
            # Get the completed task
            completed_task = session.get(Task, task_id)
            
            if completed_task and completed_task.recurrence_pattern:
                # Calculate next occurrence date based on recurrence pattern
                next_due_date = self.calculate_next_occurrence(
                    completed_task.due_date, 
                    completed_task.recurrence_pattern
                )
                
                # Check if recurrence end date has been reached
                if (completed_task.recurrence_end_date and 
                    next_due_date > completed_task.recurrence_end_date):
                    return  # Stop recurrence
                
                # Create a new task for the next occurrence
                new_task = Task(
                    title=completed_task.title,
                    description=completed_task.description,
                    priority=completed_task.priority,
                    due_date=next_due_date,
                    tags=completed_task.tags,
                    recurrence_pattern=completed_task.recurrence_pattern,
                    recurrence_end_date=completed_task.recurrence_end_date,
                    parent_task_id=completed_task.id  # Link to parent task
                )
                
                session.add(new_task)
                session.commit()
                
                # Publish event for the new task
                event_data = {
                    'event_type': 'task.created',
                    'task_id': new_task.id,
                    'task_data': new_task.dict(),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                # Publish to Kafka
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(kafka_producer.publish_event('task-events', event_data))
                loop.close()
    
    def calculate_next_occurrence(self, current_date: datetime, pattern: str) -> datetime:
        """Calculate the next occurrence date based on the recurrence pattern"""
        from dateutil.relativedelta import relativedelta
        
        if pattern == 'daily':
            return current_date + relativedelta(days=1)
        elif pattern == 'weekly':
            return current_date + relativedelta(weeks=1)
        elif pattern == 'monthly':
            return current_date + relativedelta(months=1)
        elif pattern == 'yearly':
            return current_date + relativedelta(years=1)
        else:
            return current_date + relativedelta(days=1)  # Default to daily


# Consumer thread
def start_kafka_consumer():
    consumer = KafkaEventConsumer()
    consumer.start_consuming()


# Start consumer in a separate thread
consumer_thread = threading.Thread(target=start_kafka_consumer, daemon=True)
consumer_thread.start()