"""
Camera management routes:
  GET    /api/cameras          – list all registered cameras
  POST   /api/cameras          – add new camera
  DELETE /api/cameras/{id}     – remove camera
  GET    /api/cameras/{id}     – get camera info
"""

from fastapi import APIRouter, Depends, HTTPException
from ..models.schemas import CameraAddRequest, CameraInfo
from ..models.database import User, Camera, get_db
from ..routers.auth import get_current_user, require_admin
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/cameras", tags=["cameras"])

# Camera manager is a singleton stored in app state; accessed via request.app.state
from fastapi import Request


@router.get("", response_model=list[CameraInfo])
def list_cameras(
    request: Request,
    _: User = Depends(get_current_user),
):
    mgr = request.app.state.camera_manager
    return mgr.list_cameras()


@router.get("/{camera_id}", response_model=CameraInfo)
def get_camera(
    camera_id: str,
    request: Request,
    _: User = Depends(get_current_user),
):
    mgr = request.app.state.camera_manager
    info = mgr.get_camera_info(camera_id)
    if not info:
        raise HTTPException(status_code=404, detail="Camera not found")
    return info


@router.post("", response_model=CameraInfo, status_code=201)
def add_camera(
    body: CameraAddRequest,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    mgr = request.app.state.camera_manager
    success = mgr.add_camera(body.camera_id, body.source)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start camera or ID already exists")
    
    # Persist to DB
    try:
        new_cam = Camera(camera_id=body.camera_id, source=str(body.source), is_active=True)
        db.add(new_cam)
        db.commit()
    except Exception as e:
        # It might already exist in DB if manually added or partially failed
        db.rollback()
    
    info = mgr.get_camera_info(body.camera_id)
    return info


@router.delete("/{camera_id}", status_code=204)
def remove_camera(
    camera_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    mgr = request.app.state.camera_manager
    removed = mgr.remove_camera(camera_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    # Remove from DB
    db.query(Camera).filter(Camera.camera_id == camera_id).delete()
    db.commit()
