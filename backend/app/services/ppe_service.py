import cv2
import numpy as np
import base64
import logging
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from detection.ppe_detector import PPEDetector
from ..models.database import PPEAudit
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class PPEService:
    """
    Enterprise PPE Service.
    Handles business logic for multi-class PPE compliance verification and audit logging.
    Strictly follows 'Assume Unsafe' logic.
    """
    
    def __init__(self, ppe_detector: PPEDetector):
        self.ppe_detector = ppe_detector

    def analyze_and_audit(self, image_bytes: bytes, db: Session, user_id: int = None) -> Dict[str, Any]:
        """
        Processes an image, runs multi-class PPE detection, calculates summary, 
        saves audit logs, and returns structured result.
        """
        # 1. Image Decoding
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Invalid image data provided for analysis")

        # 2. PPE Detection (Multi-class with Regional Logic)
        workers = self.ppe_detector.detect(image, conf=settings.CONF_THRESHOLD)
        
        # 3. Compliance Summary Calculation
        total_p = len(workers)
        compliant_c = sum(1 for w in workers if w["status"] == "FULLY_COMPLIANT")
        partial_c = sum(1 for w in workers if w["status"] in ["NO_VEST", "NO_HELMET"])
        non_compliant_c = sum(1 for w in workers if w["status"] == "NON_COMPLIANT")
        
        summary = {
            "total_persons": total_p,
            "compliant": compliant_c,
            "partial": partial_c,
            "non_compliant": non_compliant_c
        }

        # Global Compliance Flag
        global_compliance = "COMPLIANT" if (total_p > 0 and compliant_c == total_p) else "NON_COMPLIANT"
        
        # 4. Violation Aggregation (for backward compatibility)
        violations = []
        for w in workers:
            if w["status"] != "FULLY_COMPLIANT":
                violations.append(f"Worker #{w['person_id']}: {w['status']}")
        
        if not workers:
            violations.append("SYSTEM: No workers detected in field of view")

        # 5. Professional Annotation
        annotated_image = self.ppe_detector.annotate(image, workers)
        _, buf = cv2.imencode(".jpg", annotated_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        img_b64 = base64.b64encode(buf).decode("utf-8")

        # 6. Enterprise Audit Trail
        audit_filename = f"audit_ppe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        audit_path = os.path.join(settings.SNAPSHOT_DIR, audit_filename)
        
        try:
            cv2.imwrite(audit_path, annotated_image)
            
            # Persist session to database (Step 3: Audit Persistence)
            audit_entry = PPEAudit(
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                image_path=audit_filename,
                violations=json.dumps(violations),
                compliance=global_compliance,
                details=json.dumps(workers) # Stores ID, helmet, vest, status, confidence
            )
            db.add(audit_entry)
            db.commit()
            logger.info(f"PPE Multi-Class Audit persisted: {audit_filename} | Summary: {summary}")
        except Exception as e:
            logger.error(f"Failed to persist multi-class PPE audit: {e}")
            db.rollback()

        return {
            "detections": workers,
            "violations": violations,
            "compliance": global_compliance,
            "summary": summary,
            "image_base64": img_b64,
            "timestamp": datetime.now(timezone.utc)
        }
