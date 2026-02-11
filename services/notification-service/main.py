import json
from kafka import KafkaConsumer
from datetime import datetime
import threading
import os
import asyncio
import httpx

class NotificationService:
    def __init__(self):
        kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.consumer = KafkaConsumer(
            'reminders',
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='notification-service'
        )

    def start_processing(self):
        """Start processing reminder messages from Kafka"""
        print("Starting Notification Service...")
        for message in self.consumer:
            try:
                event_data = message.value
                event_type = event_data.get('event_type')
                
                if event_type == 'reminder.triggered':
                    self.handle_reminder(event_data)
                    
            except Exception as e:
                print(f"Error processing notification: {e}")

    async def send_notification(self, task_id: int, title: str, user_id: str):
        """Send notification to user"""
        # In a real implementation, this would send actual notifications
        # via email, push notification, or SMS
        print(f"Sending notification for task {task_id}: '{title}' to user {user_id}")
        
        # Simulate sending notification
        # This could be email, push notification, or in-app notification
        notification_methods = [
            self.send_email_notification,
            self.send_push_notification,
            self.send_in_app_notification
        ]
        
        for method in notification_methods:
            try:
                await method(task_id, title, user_id)
            except Exception as e:
                print(f"Failed to send notification via {method.__name__}: {e}")

    async def send_email_notification(self, task_id: int, title: str, user_id: str):
        """Send email notification"""
        # In a real implementation, this would connect to an email service
        print(f"Email notification sent for task {task_id} to user {user_id}")

    async def send_push_notification(self, task_id: int, title: str, user_id: str):
        """Send push notification"""
        # In a real implementation, this would connect to a push notification service
        print(f"Push notification sent for task {task_id} to user {user_id}")

    async def send_in_app_notification(self, task_id: int, title: str, user_id: str):
        """Send in-app notification"""
        # In a real implementation, this would store notification in database
        # for WebSocket service to broadcast
        print(f"In-app notification stored for task {task_id} to user {user_id}")

    def handle_reminder(self, event_data):
        """Handle reminder event and send notification"""
        task_id = event_data.get('task_id')
        title = event_data.get('title')
        user_id = event_data.get('user_id')
        
        print(f"Handling reminder for task {task_id}: {title}")
        
        # Send notification asynchronously
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.send_notification(task_id, title, user_id))
        loop.close()


def main():
    service = NotificationService()
    service.start_processing()


if __name__ == "__main__":
    main()