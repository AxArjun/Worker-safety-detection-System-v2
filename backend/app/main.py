"""
FastAPI application entry point.
"""

import time
import asyncio
import sys
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root is on path so `detection` package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

try:
    from backend.app.config import get_settings
    from backend.app.models.database import init_db, User, get_db, Camera
    from backend.app.routers import auth, detect, violations, stats, cameras, websockets, ppe
    from backend.app.routes.auth import hash_password
    from backend.app.services.alert_service import get_recent_alerts, alert_service
    from backend.app.core.redis_client import redis_client
    from backend.app.workers.event_consumer import violation_consumer
except ImportError:
    # Handle environment where 'backend.app' is not on path
    from .config import get_settings
    from .models.database import init_db, User, get_db, Camera
    from .routers import auth, detect, violations, stats, cameras, websockets, ppe
    from .routes.auth import hash_password
    from .services.alert_service import get_recent_alerts, alert_service
    from .core.redis_client import redis_client
    from .workers.event_consumer import violation_consumer

from detection.camera_manager import CameraManager
from detection.engine import SafetyDetector
from detection.event_publisher import EventPublisher
from detection.ppe_detector import PPEDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown logic."""
    logger.info("🚀 Starting AI Worker Safety Platform…")

    # Initialize database
    init_db(settings.DB_URL)
    logger.info("Database initialized ✓")

    # Initialize detector
    app.state.detector = SafetyDetector(
        model_path=settings.MODEL_PATH,
        snapshot_dir=settings.SNAPSHOT_DIR,
        conf_threshold=settings.CONF_THRESHOLD
    )
    # Initialize PPE detector
    app.state.ppe_detector = PPEDetector(
        model_path=os.path.join("backend", "models", "ppe.pt")
    )
    logger.info("PPEDetector initialized ✓")

    # Initialize publisher
    app.state.publisher = EventPublisher(redis_url=settings.REDIS_URL)

    # Initialize camera manager
    app.state.camera_manager = CameraManager(
        detector=app.state.detector,
        publisher=app.state.publisher
    )
    
    # Load cameras from DB and seed default
    _seed_cameras(app.state.camera_manager)
    
    # Seed default admin user if DB is empty
    _seed_admin()

    # Redis + Workers
    try:
        await redis_client.connect()
        app.state.worker_task = asyncio.create_task(violation_consumer())
        app.state.alert_task = asyncio.create_task(alert_service.start_alert_processor())
        logger.info("Redis connected and background worker/alert processor started ✓")
    except Exception as e:
        logger.error(f"Failed to start Redis/Worker/AlertProcessor: {e}")

    logger.info("🚀 System ready on Port 8001")
    yield

    # Shutdown
    if hasattr(app.state, "worker_task"):
        app.state.worker_task.cancel()
    if hasattr(app.state, "alert_task"):
        app.state.alert_task.cancel()
    
    await redis_client.disconnect()
    app.state.camera_manager.stop_all()
    logger.info("🛑 System shutdown complete")


def _seed_cameras(manager: CameraManager):
    """Load cameras from DB or add default webcam if empty."""
    from sqlalchemy.orm import Session
    from backend.app.models.database import _SessionLocal
    
    if _SessionLocal is None:
        return

    db: Session = _SessionLocal()
    try:
        db_cameras = db.query(Camera).all()
        if not db_cameras:
            logger.info("No cameras found in DB, seeding default 'webcam'...")
            default_cam = Camera(camera_id="webcam", source="0", is_active=True)
            db.add(default_cam)
            db.commit()
            db_cameras = [default_cam]
        
        for cam in db_cameras:
            if cam.is_active:
                logger.info(f"Restoring camera {cam.camera_id} from DB...")
                manager.add_camera(cam.camera_id, cam.source)
    except Exception as e:
        logger.error(f"Failed to seed cameras: {e}")
    finally:
        db.close()


def _seed_admin():
    """Create a default admin user on first run."""
    try:
        from backend.app.models.database import get_db
    except ImportError:
        from .models.database import get_db
    
    # We use next() because it's a generator dependency
    db = next(get_db())
    try:
        if not db.query(User).filter(User.role == "admin").first():
            admin = User(
                email="admin@safeguard.local",
                hashed_password=hash_password("admin1234"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin created: admin@safeguard.local / admin1234")
    finally:
        db.close()


# ------------------------------------------------------------------
# Build app
# ------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Worker Safety Monitoring Platform API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve violation snapshot images
snapshots_dir = os.path.abspath(settings.SNAPSHOT_DIR)
os.makedirs(snapshots_dir, exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=snapshots_dir), name="snapshots")

# Register routers
app.include_router(auth.router)
app.include_router(detect.router)
app.include_router(violations.router)
app.include_router(stats.router)
app.include_router(cameras.router)
app.include_router(websockets.router)
app.include_router(ppe.router)


@app.get("/api/cameras/{camera_id}/stream")
async def stream_camera(camera_id: str, request: Request):
    """
    MJPEG streaming endpoint.
    """
    manager: CameraManager = request.app.state.camera_manager
    stream = manager.get_stream(camera_id)
    
    if not stream:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found")

    def generate():
        logger.info(f"Starting MJPEG stream for {camera_id}")
        while True:
            frame_bytes = stream.get_latest_frame()
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # No frame yet, wait a bit
                time.sleep(0.01)

    return StreamingResponse(
        generate(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/api/alerts/recent")
def recent_alerts(_=None):
    return get_recent_alerts(limit=20)
