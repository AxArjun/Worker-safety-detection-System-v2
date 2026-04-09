import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages active WebSocket connections to provide real-time updates.
    Includes heartbeat and connection status tracking.
    """
    def __init__(self):
        # active_connections maps connection_id to WebSocket object
        self.active_connections: Dict[str, WebSocket] = {}
        # Simple set for broadcast convenience
        self._sockets: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self._sockets.add(websocket)
        logger.info(f"WebSocket client connected: {client_id}. Total: {len(self._sockets)}")

    def disconnect(self, client_id: str):
        """Handle a client disconnect."""
        websocket = self.active_connections.pop(client_id, None)
        if websocket:
            self._sockets.discard(websocket)
            logger.info(f"WebSocket client disconnected: {client_id}. Remaining: {len(self._sockets)}")

    async def broadcast(self, message: str):
        """Send a message to all connected clients."""
        if not self._sockets:
            return

        # Use gather to send messages concurrently and handle dropped connections
        tasks = []
        for connection in list(self._sockets):
            tasks.append(self._send_safe(connection, message))
        
        await asyncio.gather(*tasks)

    async def _send_safe(self, websocket: WebSocket, message: str):
        """Send message and handle individual connection failures."""
        try:
            await websocket.send_text(message)
        except Exception:
            # We don't remove here because disconnect() handles it, 
            # but we catch to prevent one failure from stopping the broadcast.
            pass

    async def heartbeat_loop(self, websocket: WebSocket, client_id: str):
        """Listen for pings/pongs to keep connection alive or detect death."""
        try:
            while True:
                # Wait for any message (acting as a keepalive)
                # In most browsers, JS side handles ping-pong automatically if used correctly,
                # but we'll monitor the socket for receive errors.
                data = await websocket.receive_text()
                # Optional: handle explicit 'ping' messages
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            self.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error in heartbeat loop for {client_id}: {e}")
            self.disconnect(client_id)

# Singleton manager
ws_manager = ConnectionManager()
