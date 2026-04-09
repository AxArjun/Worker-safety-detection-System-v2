import asyncio
import json
import logging
from typing import Optional, Dict, Any

from ..core.redis_client import redis_client
from ..core.ws_manager import ws_manager
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class AlertService:
    """
    Service responsible for processing raw violation events,
    classifying them by severity, and broadcasting via WebSockets.
    """
    
    def classify_severity(self, violation_type: str) -> str:
        """Classify violation type into HIGH, MEDIUM, LOW severity."""
        v_type = violation_type.upper()
        if "HELMET" in v_type or "SAFETY" in v_type:
            return "HIGH"
        if "VEST" in v_type:
            return "MEDIUM"
        return "LOW"

    async def start_alert_processor(self):
        """
        Background task to consume 'violations.raw', process them,
        and broadcast to all connected WebSocket clients.
        """
        logger.info("Starting alert processor service...")
        
        try:
            pubsub = redis_client.client.pubsub()
            await pubsub.subscribe("violations.raw")
            
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                
                try:
                    data = json.loads(message["data"])
                    await self.process_and_broadcast(data)
                except Exception as e:
                    logger.error(f"Error in alert processor: {e}")
                    
        except Exception as e:
            logger.error(f"Alert processor encountered an error: {e}")

    async def process_and_broadcast(self, data: dict):
        """Classify event and broadcast via WebSocket."""
        camera_id = data.get("camera_id")
        event = data.get("event", {})
        violation_type = event.get("violation_type", "UNKNOWN")
        
        severity = self.classify_severity(violation_type)
        
        # Enrich event with severity and metadata for UI
        alert_payload = {
            "type": "SAFETY_ALERT",
            "severity": severity,
            "camera_id": camera_id,
            "violation_type": violation_type,
            "timestamp": data.get("timestamp"),
            "confidence": event.get("confidence"),
            "snapshot_path": event.get("snapshot_path"),
            "message": f"{severity} Severity: {violation_type} detected on {camera_id}"
        }
        
        # Broadcast to all WebSocket clients
        await ws_manager.broadcast(json.dumps(alert_payload))
        
        # Also publish to 'alerts.processed' for other microservices (if any)
        await redis_client.client.publish("alerts.processed", json.dumps(alert_payload))

# Singleton instance
alert_service = AlertService()

# Legacy helper for breadcrumbs/REST compatibility
def get_recent_alerts(limit: int = 50) -> list[dict]:
    # This could be powered by Redis or DB. 
    # For now, we'll keep it simple or return empty as the new system is live.
    return []
