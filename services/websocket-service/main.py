import json
from kafka import KafkaConsumer
from datetime import datetime
import asyncio
import websockets
from typing import List
import threading
import os

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[websockets.WebSocketServerProtocol] = []

    async def connect(self, websocket: websockets.WebSocketServerProtocol):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"New client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: websockets.WebSocketServerProtocol):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_message(self, message: dict):
        if self.active_connections:
            await asyncio.gather(
                *[conn.send(json.dumps(message)) for conn in self.active_connections],
                return_exceptions=True
            )
            print(f"Broadcasted message to {len(self.active_connections)} clients")


# Global WebSocket manager
websocket_manager = WebSocketManager()


class WebSocketService:
    def __init__(self):
        kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.consumer = KafkaConsumer(
            'task-updates',
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            group_id='websocket-service'
        )

    def start_kafka_listener(self):
        """Start listening to Kafka messages in a separate thread"""
        print("Starting WebSocket Kafka listener...")
        for message in self.consumer:
            try:
                event_data = message.value
                # Broadcast the event to all connected clients
                asyncio.run(websocket_manager.broadcast_message(event_data))
            except Exception as e:
                print(f"Error broadcasting message: {e}")


async def websocket_endpoint(websocket: websockets.WebSocketServerProtocol):
    await websocket_manager.connect(websocket)
    try:
        # Keep the connection alive
        while True:
            # This will raise an exception when the connection is closed
            await websocket.recv()
    except websockets.exceptions.ConnectionClosed:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


async def start_websocket_server():
    server = await websockets.serve(websocket_endpoint, "0.0.0.0", 8765)
    print("WebSocket server started on ws://0.0.0.0:8765")
    await server.wait_closed()


def main():
    # Start Kafka listener in a separate thread
    kafka_thread = threading.Thread(target=WebSocketService().start_kafka_listener, daemon=True)
    kafka_thread.start()
    
    # Start WebSocket server
    asyncio.run(start_websocket_server())


if __name__ == "__main__":
    main()