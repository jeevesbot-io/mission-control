import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[websocket] = set()
        logger.info("WebSocket connected, total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.pop(websocket, None)
        logger.info("WebSocket disconnected, total: %d", len(self.active_connections))

    def subscribe(self, websocket: WebSocket, topic: str) -> None:
        if websocket in self.active_connections:
            self.active_connections[websocket].add(topic)

    def unsubscribe(self, websocket: WebSocket, topic: str) -> None:
        if websocket in self.active_connections:
            self.active_connections[websocket].discard(topic)

    async def broadcast(self, topic: str, data: dict) -> None:
        message = json.dumps({"topic": topic, "data": data})
        for ws, topics in list(self.active_connections.items()):
            if topic in topics or not topics:
                try:
                    await ws.send_text(message)
                except Exception:
                    self.disconnect(ws)


manager = ConnectionManager()
