import json
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_event(self, event_type: str, data: dict):
        payload = json.dumps({"event": event_type, "data": data})
        for conn in self.active_connections:
            try:
                await conn.send_text(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")

ws_manager = WebSocketManager()

