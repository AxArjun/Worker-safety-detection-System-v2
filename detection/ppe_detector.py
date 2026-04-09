import cv2
import numpy as np
import logging
import os
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class PPEDetector:
    """
    Enterprise PPE Detector using multi-class YOLOv8.
    Classes: person, helmet, vest.
    Implements regional spatial matching for high-precision compliance.
    """
    def __init__(self, model_path: str = "backend/models/ppe.pt", fallback_model: str = "yolov8n.pt"):
        self.model_path = model_path
        self.model = None
        self.is_ppe_aware = False
        
        # Load the specialized PPE model
        if os.path.exists(model_path):
            try:
                self.model = YOLO(model_path)
                classes = self.model.names
                # We expect person, helmet, vest
                self.is_ppe_aware = any(c.lower() in ["helmet", "vest", "hard-hat", "safety-vest"] for c in classes.values())
                logger.info(f"Loaded Multi-Class PPE model: {model_path} (Classes: {list(classes.values())})")
            except Exception as e:
                logger.error(f"Failed to load multi-class PPE model from {model_path}: {e}")

        # Fallback to standard model if specialized one is missing
        if not self.model:
            logger.warning(f"No specialized PPE model found at {model_path}. Using {fallback_model} (Graceful mode).")
            try:
                self.model = YOLO(fallback_model)
                self.is_ppe_aware = False
            except Exception as e:
                logger.error(f"Critical: Failed to load fallback detector: {e}")
                raise

    def detect(self, image: np.ndarray, conf: float = 0.25) -> list:
        """
        Run inference and classify worker compliance using regional spatial matching.
        Returns a list of workers with detailed PPE status and classification.
        """
        results = self.model(image, conf=conf, verbose=False)
        workers = []
        
        person_detections = []
        helmet_detections = []
        vest_detections = []
        
        # 1. Group Detections by Class
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                name = self.model.names[cls_id].lower()
                bbox = box.xyxy[0].tolist()
                score = float(box.conf[0])
                
                # Confidence thresholds (requested: 0.5 for helmet/vest)
                if "person" in name:
                    person_detections.append({"bbox": bbox, "score": score})
                elif any(x in name for x in ["helmet", "hard-hat", "head"]) and score >= 0.5:
                    helmet_detections.append({"bbox": bbox, "score": score})
                elif any(x in name for x in ["vest", "reflective", "safety-vest"]) and score >= 0.5:
                    vest_detections.append({"bbox": bbox, "score": score})

        # 2. Regional Spatial Matching
        for i, person in enumerate(person_detections):
            px1, py1, px2, py2 = person["bbox"]
            p_w = px2 - px1
            p_h = py2 - py1
            
            # Regional logic (Head = top 30%, Torso = 30-80%)
            y_head_max = py1 + (p_h * 0.3)
            y_torso_min = py1 + (p_h * 0.3)
            y_torso_max = py1 + (p_h * 0.8)
            
            helmet_match = None
            vest_match = None
            
            # Find best helmet in head region
            for h in helmet_detections:
                hx1, hy1, hx2, hy2 = h["bbox"]
                h_cx = (hx1 + hx2) / 2
                h_cy = (hy1 + hy2) / 2
                # Spatial check: center must be in person's horizontal bounds and head region
                if px1 <= h_cx <= px2 and py1 <= h_cy <= y_head_max:
                    helmet_match = h
                    break
            
            # Find best vest in torso region
            for v in vest_detections:
                vx1, vy1, vx2, vy2 = v["bbox"]
                v_cx = (vx1 + vx2) / 2
                v_cy = (vy1 + vy2) / 2
                if px1 <= v_cx <= px2 and y_torso_min <= v_cy <= y_torso_max:
                    vest_match = v
                    break

            # 3. Status Classification
            has_helmet = helmet_match is not None
            has_vest = vest_match is not None
            
            if has_helmet and has_vest:
                status = "FULLY_COMPLIANT"
            elif has_helmet and not has_vest:
                status = "NO_VEST"
            elif not has_helmet and has_vest:
                status = "NO_HELMET"
            else:
                status = "NON_COMPLIANT"
            
            # 4. Confidence Calculation
            # Combined confidence is the minimum of detected ppe items, or person conf if none
            if has_helmet and has_vest:
                final_conf = min(helmet_match["score"], vest_match["score"])
            elif has_helmet:
                final_conf = helmet_match["score"]
            elif has_vest:
                final_conf = vest_match["score"]
            else:
                final_conf = person["score"]

            workers.append({
                "person_id": i + 1,
                "bbox": person["bbox"],
                "confidence": round(final_conf, 2),
                "helmet": has_helmet,
                "vest": has_vest,
                "status": status
            })
            
        return workers

    def annotate(self, image: np.ndarray, workers: list) -> np.ndarray:
        """Annotate image using enterprise-grade color coding."""
        annotated = image.copy()
        
        # Color mapping (BGR)
        palette = {
            "FULLY_COMPLIANT": (0, 255, 0),    # Green
            "NO_VEST": (0, 255, 255),          # Yellow
            "NO_HELMET": (0, 255, 255),        # Yellow
            "NON_COMPLIANT": (0, 0, 255)       # Red
        }
        
        for w in workers:
            x1, y1, x2, y2 = map(int, w["bbox"])
            status = w["status"]
            color = palette.get(status, (255, 255, 255))
            
            # 1. Main bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 1)
            
            # 2. Worker ID & Confidence
            label = f"WORKER #{w['person_id']} [{int(w['confidence']*100)}%]"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 10), (x1 + tw + 10, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 5, y1 - 6), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
            
            # 3. State Badge
            state_label = status.replace("_", " ")
            cv2.putText(annotated, state_label, (x1 + 5, y1 + 15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1, cv2.LINE_AA)

        return annotated
