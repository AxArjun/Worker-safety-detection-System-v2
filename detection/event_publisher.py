import json
import logging
import time
import redis
from typing import Optional, Dict, Any

# We use sync Redis for the publisher because CameraStream runs in threads
class EventPublisher:
    """
    Publishes detection events and frame updates to Redis.
    Uses sync Redis client to work within CameraStream threads.
    """
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            logging.info(f"EventPublisher connected to Redis at {redis_url}")
        except Exception as e:
            logging.error(f"EventPublisher failed to connect to Redis: {e}")
            self.redis = None

    def publish_violation(self, camera_id: str, violation_event: Dict[str, Any]):
        """Publish a violation event to the raw violations channel."""
        if not self.redis:
            return

        try:
            payload = {
                "camera_id": camera_id,
                "timestamp": time.time(),
                "event": violation_event
            }
            self.redis.publish("violations.raw", json.dumps(payload))
            # logger.debug(f"Published violation for {camera_id} to violations.raw")
        except Exception as e:
            logging.error(f"Failed to publish violation: {e}")

    def update_frame_cache(self, camera_id: str, frame_bytes: bytes):
        """
        Update the latest frame in Redis cache.
        Stores as JPEG bytes with a short TTL.
        """
        if not self.redis:
            return

        try:
            key = f"frame_{camera_id}"
            # Use SET with EX (TTL) to ensure stale frames are cleared
            self.redis.set(key, frame_bytes, ex=5) 
        except Exception as e:
            logging.error(f"Failed to update frame cache for {camera_id}: {e}")

    def publish_metrics(self, camera_id: str, metrics: Dict[str, Any]):
        """Publish camera metrics (FPS, etc.)"""
        if not self.redis:
            return

        try:
            payload = {
                "camera_id": camera_id,
                "timestamp": time.time(),
                "metrics": metrics
            }
            self.redis.publish("stats.metrics", json.dumps(payload))
        except Exception as e:
            logging.error(f"Failed to publish metrics: {e}")
