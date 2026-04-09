"""
Detection route:
  POST /api/detect  – process uploaded frame, return results + log violations
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..models.database import get_db, User
from ..models.schemas import DetectionResult
from ..routers.auth import get_current_user
from ..services.detection_service import DetectionService

router = APIRouter(prefix="/api", tags=["detection"])


@router.post("/detect", response_model=DetectionResult)
async def detect_frame(
    frame: UploadFile = File(..., description="JPEG/PNG image frame"),
    camera_id: str = Form("cam-0"),
    camera_source: str = Form(""),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Accept a single image frame, run YOLO safety detection,
    log violations to DB, and return annotated results.
    """
    raw_bytes = await frame.read()
    svc = DetectionService(db=db)
    result = svc.process(
        frame_bytes=raw_bytes,
        camera_id=camera_id,
        camera_source=camera_source or str(camera_id),
    )
    return result
