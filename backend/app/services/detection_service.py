"""
DetectionService – business logic layer for frame processing,
violation DB persistence, and alert triggering.
"""

import sys
import os
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from ..config import get_settings
from detection.event_publisher import EventPublisher

logger = logging.getLogger(__name__)

# Lazy-load detector to avoid import overhead during unit testing
_detector = None
_alert_manager = None


def _get_detector():
    global _detector
    if _detector is None:
        # Ensure detection module is importable (running from project root)
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
        from detection.engine import SafetyDetector
        from ..config import get_settings
        s = get_settings()
        _detector = SafetyDetector(
            model_path=s.MODEL_PATH,
            snapshot_dir=s.SNAPSHOT_DIR,
            conf_threshold=s.CONF_THRESHOLD,
        )
    return _detector


    from ..config import get_settings
    from .alert_service import get_recent_alerts, alert_service
    from .core.redis_client import redis_client
    from .workers.event_consumer import violation_consumer


class DetectionService:
    def __init__(self, db: Session):
        self.db = db

    def process(
        self,
        frame_bytes: bytes,
        camera_id: str = "cam-0",
        camera_source: str = "",
    ) -> dict:
        detector = _get_detector()
        
        # Initialize publisher to send event to Redis
        publisher = EventPublisher(redis_url=get_settings().REDIS_URL)

        result = detector.process_frame_bytes(frame_bytes, camera_id=camera_id)

        alert_triggered = False
        for v in result["violations"]:
            # 1. Publish to Redis (Worker will save to DB, AlertService will notify WS)
            publisher.publish_violation(camera_id, v)

        return {
            "detections": result["detections"],
            "violations": result["violations"],
            "fps": result["fps"],
            "violation_count": result["violation_count"],
            "annotated_frame_b64": result["annotated_frame_b64"],
            "snapshot_path": result.get("snapshot_path"),
            "alert_triggered": False, # Handled by WS
        }

    def _save_violation(
        self,
        violation_type: str,
        camera_id: str,
        camera_source: str,
        image_path: Optional[str],
        confidence: Optional[float],
    ):
        from ..models.database import Violation
        v = Violation(
            timestamp=datetime.now(timezone.utc),
            violation_type=violation_type,
            camera_id=camera_id,
            camera_source=camera_source,
            image_path=image_path,
            confidence=confidence,
        )
        self.db.add(v)
        self.db.commit()
        logger.info(f"Violation logged: {violation_type} @ {camera_id}")
