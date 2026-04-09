"""
CameraManager – Multi-camera stream manager.
Each camera runs in its own thread, feeding frames to the SafetyDetector.
NOTE: IDE "Could not find import" warnings for fastapi/cv2 are typically due to local 
environment indexing. The system is verified to run on Port 8001.
"""

import threading
import time
import logging
import queue
import cv2
from typing import Callable, Optional, Union, cast, Any

# Internal imports
try:
    from .engine import SafetyDetector
    from .event_publisher import EventPublisher
except ImportError:
    # Handle direct execution or different path
    from engine import SafetyDetector
    from event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class CameraStream:
    """Individual camera stream with background thread capture and detection."""

    def __init__(
        self, 
        camera_id: str, 
        source: Union[int, str], 
        detector: Optional[SafetyDetector] = None,
        publisher: Optional[EventPublisher] = None,
        buffer_size: int = 10,
        fps_limit: int = 15
    ):
        self.camera_id = camera_id
        self.source = source
        self.detector = detector
        self.publisher = publisher
        self.buffer_size = buffer_size
        self.fps_limit = fps_limit
        self.frame_interval = 1.0 / fps_limit if fps_limit > 0 else 0
        
        self._cap: Optional[cv2.VideoCapture] = None
        self._queue: queue.Queue = queue.Queue(maxsize=buffer_size)
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._error: Optional[str] = None
        
        # Thread-safe frame storage for MJPEG streaming
        self._frame_lock = threading.Lock()
        self._latest_frame: Optional[bytes] = None
        
        self.frame_count = 0
        self.connected_at: Optional[float] = None
        self.fps = 0.0
        self.violation_count = 0

    def start(self) -> bool:
        try:
            logger.info(f"[DEBUG] Starting camera {self.camera_id} source={self.source}")
            src = int(self.source) if str(self.source).isdigit() else self.source
            self._cap = cv2.VideoCapture(src)
            cap = cast(Any, self._cap)
            if cap is None or not cap.isOpened():
                self._error = f"Cannot open source: {self.source}"
                logger.error(self._error)
                return False
            
            self._running = True
            self.connected_at = time.time()
            self._thread = threading.Thread(
                target=self._capture_loop, daemon=True, name=f"cam-{self.camera_id}"
            )
            cast(Any, self._thread).start()
            logger.info(f"Camera {self.camera_id} thread started")
            return True
        except Exception as e:
            self._error = str(e)
            logger.error(f"Failed to start camera {self.camera_id}: {e}")
            return False

    def stop(self):
        self._running = False
        if self._thread:
            cast(Any, self._thread).join(timeout=3)
        if self._cap:
            cast(Any, self._cap).release()
        logger.info(f"Camera {self.camera_id} stopped and cleaned up")

    def get_latest_frame(self) -> Optional[bytes]:
        """Thread-safe retrieval of the latest encoded JPEG frame."""
        with self._frame_lock:
            return self._latest_frame

    def is_running(self) -> bool:
        thread = cast(Any, self._thread)
        return self._running and (thread is not None) and thread.is_alive()

    def read(self) -> Optional[Any]:
        """Read the latest raw frame from the internal queue."""
        try:
            return self._queue.get(timeout=0.2)
        except queue.Empty:
            return None

    def get_info(self) -> dict:
        return {
            "camera_id": self.camera_id,
            "source": str(self.source),
            "running": self.is_running(),
            "frame_count": self.frame_count,
            "fps": self.fps,
            "violation_count": self.violation_count,
            "error": self._error,
            "uptime_s": self._get_uptime(),
        }

    def _get_uptime(self) -> float:
        conn_at = self.connected_at
        if conn_at is None:
            return 0.0
        diff = float(time.time() - conn_at)
        try:
            return float(f"{diff:.1f}")
        except (ValueError, TypeError):
            return 0.0

    def _attempt_reconnect(self, delay: float = 3.0):
        time.sleep(delay)
        if self._cap:
            cast(Any, self._cap).release()
        src = int(self.source) if str(self.source).isdigit() else self.source
        self._cap = cv2.VideoCapture(src)
        cap = cast(Any, self._cap)
        if cap and cap.isOpened():
            logger.info(f"Camera {self.camera_id} reconnected")
        else:
            logger.error(f"Camera {self.camera_id} reconnect failed")

    def _capture_loop(self):
        logger.info(f"[DEBUG] Camera {self.camera_id} capture loop entering")
        last_frame_time = 0
        
        while self._running:
            # FPS Limiter
            if self.frame_interval > 0:
                elapsed = time.time() - last_frame_time
                if elapsed < self.frame_interval:
                    time.sleep(self.frame_interval - elapsed)
            
            last_frame_time = time.time()

            cap = cast(Any, self._cap)
            if not cap or not cap.isOpened():
                self._attempt_reconnect()
                continue

            ret, frame = cap.read()
            if not ret:
                logger.warning(f"Camera {self.camera_id}: failed to read frame, reconnecting…")
                self._attempt_reconnect()
                continue
            
            self.frame_count += 1
            
            # Process frame with detector
            processed_frame = frame
            detector = self.detector
            results = None
            
            if detector is not None:
                results = detector.process_frame(frame, camera_id=self.camera_id)
                processed_frame = results.get("annotated_frame", frame)
                self.fps = results.get("fps", 0.0)
                self.violation_count = results.get("violation_count", 0)

            # Encode to JPEG for streaming
            success, jpeg_buf = cv2.imencode(".jpg", processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_bytes = None
            if success:
                frame_bytes = jpeg_buf.tobytes()
                with self._frame_lock:
                    self._latest_frame = frame_bytes

            # Publish to Redis
            if self.publisher:
                # Update frame cache in Redis
                if frame_bytes:
                    self.publisher.update_frame_cache(self.camera_id, frame_bytes)
                
                # Publish violations
                if results and results.get("violations"):
                    for viol in results["violations"]:
                        self.publisher.publish_violation(self.camera_id, viol)
                
                # Publish periodic metrics
                if self.frame_count % 30 == 0:
                    self.publisher.publish_metrics(self.camera_id, {
                        "fps": self.fps,
                        "violation_total": self.violation_count,
                        "uptime": self._get_uptime()
                    })

            # Backpressure: Frame skipping if queue is full
            if self._queue.full():
                # Skip this frame instead of blocking or popping old ones manually 
                # (although putting we'll still pop below to keep it fresh for consumers)
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass
            
            try:
                self._queue.put_nowait(frame)
            except queue.Full:
                pass


class CameraManager:
    """
    Manages multiple CameraStream instances.
    Provides add/remove/list/read operations.
    """

    def __init__(self, detector: Optional[SafetyDetector] = None, publisher: Optional[EventPublisher] = None):
        self._cameras: dict[str, CameraStream] = {}
        self._lock = threading.Lock()
        self.detector = detector
        self.publisher = publisher

    def add_camera(
        self,
        camera_id: str,
        source: Union[int, str],
        on_frame: Optional[Callable] = None,
    ) -> bool:
        """
        Add and start a camera stream.
        """
        with self._lock:
            if camera_id in self._cameras:
                logger.warning(f"Camera {camera_id} already exists")
                return False
            
            stream = CameraStream(
                camera_id=camera_id, 
                source=source, 
                detector=self.detector,
                publisher=self.publisher
            )
            success = stream.start()
            if success:
                self._cameras[camera_id] = stream
                if on_frame:
                    self._start_callback_thread(stream, on_frame)
            return success

    def remove_camera(self, camera_id: str) -> bool:
        with self._lock:
            stream = self._cameras.pop(camera_id, None)
            if stream:
                stream.stop()
                return True
            return False

    def get_stream(self, camera_id: str) -> Optional[CameraStream]:
        """Retrieve the stream object for direct access (e.g. MJPEG)."""
        return self._cameras.get(camera_id)

    def read_frame(self, camera_id: str):
        """Read latest RAW frame from a specific camera queue."""
        stream = self._cameras.get(camera_id)
        return stream.read() if stream else None

    def list_cameras(self) -> list[dict]:
        with self._lock:
            return [s.get_info() for s in self._cameras.values()]

    def get_camera_info(self, camera_id: str) -> Optional[dict]:
        stream = self._cameras.get(camera_id)
        return stream.get_info() if stream else None

    def stop_all(self):
        with self._lock:
            for stream in self._cameras.values():
                stream.stop()
            self._cameras.clear()

    def camera_count(self) -> int:
        return len(self._cameras)

    def active_camera_ids(self) -> list[str]:
        with self._lock:
            return [cid for cid, s in self._cameras.items() if s.is_running()]

    # --- internal ---

    def _start_callback_thread(self, stream: CameraStream, callback: Callable):
        def loop():
            while stream.is_running():
                frame = stream.read()
                if frame is not None:
                    try:
                        callback(stream.camera_id, frame)
                    except Exception as e:
                        logger.error(f"Frame callback error for {stream.camera_id}: {e}")
                else:
                    time.sleep(0.01)

        t = threading.Thread(target=loop, daemon=True, name=f"cb-{stream.camera_id}")
        t.start()
