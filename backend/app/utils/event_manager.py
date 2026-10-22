import asyncio
from typing import Set, Dict, Any
from fastapi import WebSocket
from app.utils.logger import logger

class ScanEventManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        dead = set()
        for conn in list(self.active_connections):
            try:
                await conn.send_json(message)
            except Exception:
                dead.add(conn)
        for d in dead:
            self.active_connections.discard(d)

    def broadcast_sync(self, message: Dict[str, Any]):
        """Safe thread-safe broadcast callable from worker threads."""
        try:
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
            else:
                asyncio.run(self.broadcast(message))
        except Exception as e:
            logger.debug(f"Event broadcast skipped: {e}")

event_manager = ScanEventManager()
