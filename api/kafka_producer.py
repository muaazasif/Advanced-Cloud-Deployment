import json
from typing import Dict, Any
from kafka import KafkaProducer
import os
from dapr.ext.fastapi import DaprApp
from fastapi import FastAPI
import asyncio

class KafkaEventProducer:
    def __init__(self):
        # Check if we're using Dapr or direct Kafka
        self.use_dapr = os.getenv("USE_DAPR", "false").lower() == "true"
        
        if not self.use_dapr:
            kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
            self.producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
    
    async def publish_event(self, topic: str, event_data: Dict[str, Any]):
        """Publish an event to Kafka topic"""
        if self.use_dapr:
            # Using Dapr pub/sub
            import httpx
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        f"http://localhost:3500/v1.0/publish/pubsub/{topic}",
                        json=event_data
                    )
                    return response.status_code == 200
                except Exception as e:
                    print(f"Error publishing to Dapr pub/sub: {e}")
                    return False
        else:
            # Using direct Kafka
            try:
                future = self.producer.send(topic, value=event_data)
                result = future.get(timeout=10)
                return True
            except Exception as e:
                print(f"Error publishing to Kafka: {e}")
                return False
    
    def close(self):
        if hasattr(self, 'producer'):
            self.producer.close()


# Global instance
kafka_producer = KafkaEventProducer()
