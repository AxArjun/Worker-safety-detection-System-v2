import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from ..core.redis_client import redis_client
from ..models import database

logger = logging.getLogger(__name__)

async def violation_consumer():
    """
    Async worker that subscribes to 'violations.raw' in Redis
    and persists them to the database.
    """
    logger.info("Starting violation consumer worker...")
    
    # Ensure Redis is connected (should be handled by lifespan, but safe check)
    try:
        pubsub = redis_client.client.pubsub()
        await pubsub.subscribe("violations.raw")
        
        logger.info("Subscribed to 'violations.raw'. Waiting for events...")
        
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
                
            try:
                data = json.loads(message["data"])
                await process_violation_event(data)
            except Exception as e:
                logger.error(f"Error processing violation event: {e}")
                
    except Exception as e:
        logger.error(f"Violation consumer encountered a fatal error: {e}")
    finally:
        logger.info("Violation consumer shutting down.")

async def process_violation_event(data: dict):
    """Parse and save violation to DB."""
    camera_id = data.get("camera_id")
    event = data.get("event", {})
    
    violation_type = event.get("violation_type")
    confidence = event.get("confidence")
    snapshot_path = event.get("snapshot_path")
    
    if not violation_type or not camera_id:
        logger.warning(f"Malformed violation event received: {data}")
        return

    # Database persistence
    if database._SessionLocal is None:
        logger.error("Database not initialized. Cannot save violation.")
        return

    # Run DB operation in a thread to keep consumer non-blocking if needed,
    # but here we use a short session.
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _save_to_db, violation_type, camera_id, confidence, snapshot_path)

def _save_to_db(violation_type, camera_id, confidence, snapshot_path):
    db: Session = database._SessionLocal()
    try:
        v = database.Violation(
            timestamp=datetime.now(timezone.utc),
            violation_type=violation_type,
            camera_id=camera_id,
            confidence=confidence,
            image_path=snapshot_path,
            notes="Processed via EventConsumer"
        )
        db.add(v)
        db.commit()
        logger.info(f"Violation logged to DB from Redis: {violation_type} @ {camera_id}")
    except Exception as e:
        logger.error(f"Failed to save violation to DB: {e}")
        db.rollback()
    finally:
        db.close()
