import json
from kafka import KafkaConsumer
from datetime import datetime
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
import threading
import os

# Audit Log Model
class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str = Field(index=True)
    task_id: int = Field(index=True)
    user_id: str
    action: str
    old_values: Optional[str] = Field(default=None)  # JSON string
    new_values: Optional[str] = Field(default=None)  # JSON string
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session


class AuditService:
    def __init__(self):
        kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.consumer = KafkaConsumer(
            'task-events',
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='audit-service'
        )

    def start_processing(self):
        """Start processing messages from Kafka"""
        print("Starting Audit Service...")
        for message in self.consumer:
            try:
                event_data = message.value
                event_type = event_data.get('event_type')
                
                if event_type in ['task.created', 'task.updated', 'task.completed', 'task.deleted']:
                    self.log_audit_event(event_data)
                    
            except Exception as e:
                print(f"Error processing audit event: {e}")

    def log_audit_event(self, event_data):
        """Log audit event to database"""
        with next(get_session()) as session:
            audit_log = AuditLog(
                event_type=event_data.get('event_type'),
                task_id=event_data.get('task_id'),
                user_id=event_data.get('user_id', 'unknown'),
                action=self.get_action_from_event_type(event_data.get('event_type')),
                old_values=event_data.get('old_values'),
                new_values=event_data.get('new_values'),
                timestamp=datetime.utcnow()
            )
            
            session.add(audit_log)
            session.commit()
            
            print(f"Audited event: {event_data.get('event_type')} for task {event_data.get('task_id')}")

    def get_action_from_event_type(self, event_type: str) -> str:
        """Convert event type to action description"""
        mapping = {
            'task.created': 'Task Created',
            'task.updated': 'Task Updated',
            'task.completed': 'Task Completed',
            'task.deleted': 'Task Deleted'
        }
        return mapping.get(event_type, event_type)


def main():
    service = AuditService()
    service.start_processing()


if __name__ == "__main__":
    main()