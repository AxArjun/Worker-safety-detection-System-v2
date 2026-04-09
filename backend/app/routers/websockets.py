import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.ws_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websockets"])

@router.websocket("/ws/alerts")
async def alerts_websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time safety alerts.
    Clients connect and receive JSON payloads of recent violations.
    """
    client_id = str(uuid.uuid4())
    await ws_manager.connect(websocket, client_id)
    
    try:
        # Start heartbeat/listening loop for the connection
        await ws_manager.heartbeat_loop(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket session error for {client_id}: {e}")
    finally:
        ws_manager.disconnect(client_id)
