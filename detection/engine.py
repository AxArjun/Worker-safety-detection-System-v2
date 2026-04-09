"""
SafetyDetector – Core YOLO inference + violation detection engine.
Wraps YOLOv8 and adds FPS tracking, violation flagging, and snapshot saving.
"""

import time
import os
import uuid
import base64
import logging
from dataclasses import dataclass, field
import cv2
import numpy as np
import itertools
from ultralytics import YOLO
from typing import Any, cast, List, Dict, Optional

logger = logging.getLogger(__name__)

# Violation categories (expandable when a PPE-specific model is loaded)
VIOLATION_TYPES = {
    "NO_HELMET": "No Helmet / Head Protection",
    "NO_VEST": "No Safety Vest",
    "UNSAFE_ZONE": "Person in Unsafe Zone",
    "NO_PPE": "Missing PPE",
}

# COCO class IDs for general safety heuristics using yolov8n.pt
PERSON_CLASS_ID = 0


@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple  # (x1, y1, x2, y2)


@dataclass
class ViolationEvent:
    violation_type: str
    confidence: float
    camera_id: str
    snapshot_path: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class FPSTracker:
    """Rolling FPS counter."""

    def __init__(self, window: int = 30):
        self.window = window
        self.timestamps: list[float] = []

    def tick(self) -> float:
        now = time.time()
        self.timestamps.append(now)
        if len(self.timestamps) > self.window:
            self.timestamps.pop(0)
        if len(self.timestamps) < 2:
            return 0.0
        elapsed = self.timestamps[-1] - self.timestamps[0]
        return (len(self.timestamps) - 1) / elapsed if elapsed > 0 else 0.0


class SafetyDetector:
    """
    Production-grade safety detector.

    Args:
        model_path: Path to YOLOv8 .pt model file.
        snapshot_dir: Directory to save violation screenshots.
        conf_threshold: Minimum confidence for detections.
        save_snapshots: Whether to write PNG snapshots to disk.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        snapshot_dir: str = "snapshots",
        conf_threshold: float = 0.4,
        save_snapshots: bool = True,
        device: str = "cpu",
    ):
        self.model_path = model_path
        self.snapshot_dir = os.path.abspath(snapshot_dir)
        self.conf_threshold = conf_threshold
        self.save_snapshots = save_snapshots
        self.device = device
        self._fps_trackers: dict[str, FPSTracker] = {}
        self._violation_counter: dict[str, int] = {}

        os.makedirs(self.snapshot_dir, exist_ok=True)

        logger.info(f"Loading YOLO model from {model_path} on {device}…")
        self.model = YOLO(model_path)
        logger.info("Model loaded ✓")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_frame(
        self, frame: np.ndarray, camera_id: str = "cam-0"
    ) -> dict:
        """
        Run detection on a single frame.

        Returns:
            {
                "detections": [...],
                "violations": [...],
                "annotated_frame": np.ndarray,
                "annotated_frame_b64": str,
                "fps": float,
                "violation_count": int,
            }
        """
        if camera_id not in self._fps_trackers:
            self._fps_trackers[camera_id] = FPSTracker()
        fps = self._fps_trackers[camera_id].tick()

        # Run YOLO inference
        results: Any = self.model(frame, conf=self.conf_threshold, verbose=False)

        detections: list[Detection] = []
        violations: list[ViolationEvent] = []
        annotated = frame.copy()

        for r in results:
            res = cast(Any, r)
            for box in res.boxes:
                cls_id = int(box.cls[0].item())
                cls_name = str(self.model.names[cls_id])
                conf = float(box.conf[0].item())
                # Use .tolist() or explicit casting to ensure type checker knows it's a sequence
                coords = box.xyxy[0].tolist()
                x1, y1, x2, y2 = map(int, coords)

                det = Detection(
                    class_id=cls_id,
                    class_name=cls_name,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                )
                detections.append(det)

                # ---- Violation heuristics ----
                # Until a PPE-specific model is supplied, flag every detected
                # person as a "NO_HELMET" violation (placeholder logic).
                if cls_id == PERSON_CLASS_ID:
                    v = ViolationEvent(
                        violation_type="NO_HELMET",
                        confidence=conf,
                        camera_id=camera_id,
                    )
                    violations.append(v)
                    self._violation_counter[camera_id] = (
                        self._violation_counter.get(camera_id, 0) + 1
                    )

                # Annotate frame
                self._draw_detection(annotated, det, is_violation=(cls_id == PERSON_CLASS_ID))

        # Overlay HUD
        self._draw_hud(annotated, fps, len(violations), camera_id)

        # Save snapshot if violations found
        snapshot_path = None
        if violations and self.save_snapshots:
            snapshot_path = self._save_snapshot(annotated, camera_id)
            for v in violations:
                v.snapshot_path = snapshot_path

        # Encode to base64 for API transport
        _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
        b64 = base64.b64encode(buf).decode("utf-8")

        fps_val: float = float(fps)
        # Using format to avoid round() overload confusion in strict environments
        try:
            fps_rounded = float(f"{fps_val:.1f}")
        except (ValueError, TypeError):
            fps_rounded = 0.0

        return {
            "detections": [self._det_to_dict(d) for d in detections],
            "violations": [self._viol_to_dict(v) for v in violations],
            "annotated_frame": annotated,
            "annotated_frame_b64": b64,
            "fps": fps_rounded,
            "violation_count": self._violation_counter.get(camera_id, 0),
            "snapshot_path": snapshot_path,
        }

    def process_frame_bytes(self, frame_bytes: bytes, camera_id: str = "cam-0") -> dict:
        """Accept raw JPEG/PNG bytes (from API upload)."""
        arr = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Could not decode image bytes")
        return self.process_frame(frame, camera_id)

    def get_violation_count(self, camera_id: str = "cam-0") -> int:
        return self._violation_counter.get(camera_id, 0)

    def reset_counters(self, camera_id: Optional[str] = None):
        if camera_id:
            self._violation_counter.pop(camera_id, None)
        else:
            self._violation_counter.clear()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _draw_detection(self, frame: np.ndarray, det: Detection, is_violation: bool):
        x1, y1, x2, y2 = det.bbox
        color = (0, 0, 255) if is_violation else (0, 255, 0)
        label = f"{det.class_name} {det.confidence:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        if is_violation:
            # Red alert bar below the box
            cv2.rectangle(frame, (x1, y2 + 2), (x2, y2 + 28), (0, 0, 200), -1)
            cv2.putText(frame, "⚠ NO HELMET", (x1 + 4, y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def _draw_hud(self, frame: np.ndarray, fps: float, violations: int, camera_id: str):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 36), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

        cv2.putText(frame, f"FPS: {fps:.1f}", (8, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        cv2.putText(frame, f"Violations: {violations}", (120, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 100, 255), 2)
        cv2.putText(frame, f"CAM: {camera_id}", (w - 160, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        if violations > 0:
            cv2.putText(frame, "⚠ ALERT!", (w // 2 - 60, 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    def _save_snapshot(self, frame: np.ndarray, camera_id: str) -> str:
        ts = int(time.time())
        u_hex = str(uuid.uuid4().hex)
        # Using islice to avoid 'Cannot index into str' error in strict environments
        uid = "".join(list(itertools.islice(u_hex, 6)))
        filename = f"violation_{camera_id}_{ts}_{uid}.jpg"
        path = os.path.join(self.snapshot_dir, filename)
        cv2.imwrite(path, frame)
        logger.info(f"Snapshot saved: {path}")
        return path

    @staticmethod
    def _det_to_dict(d: Detection) -> dict:
        conf_val: float = float(d.confidence)
        # Using format to avoid round() overload confusion
        try:
            conf_rounded = float(f"{conf_val:.3f}")
        except (ValueError, TypeError):
            conf_rounded = 0.0

        return {
            "class_id": d.class_id,
            "class_name": d.class_name,
            "confidence": conf_rounded,
            "bbox": list(d.bbox),
        }

    @staticmethod
    def _viol_to_dict(v: ViolationEvent) -> dict:
        conf_val: float = float(v.confidence)
        # Using format to avoid round() overload confusion
        try:
            conf_rounded = float(f"{conf_val:.3f}")
        except (ValueError, TypeError):
            conf_rounded = 0.0

        return {
            "violation_type": v.violation_type,
            "confidence": conf_rounded,
            "camera_id": v.camera_id,
            "snapshot_path": v.snapshot_path,
            "timestamp": v.timestamp,
        }


# ------------------------------------------------------------------
# Standalone test (python detection/engine.py)
# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    source = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    detector = SafetyDetector(model_path="yolov8n.pt", save_snapshots=True)
    cap = cv2.VideoCapture(source)
    print("Press ESC to quit")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        result = detector.process_frame(frame, camera_id="cam-0")
        cv2.imshow("Safety Monitor", result["annotated_frame"])
        if cv2.waitKey(1) == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
