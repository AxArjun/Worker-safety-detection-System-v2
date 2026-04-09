"""
Stats routes:
  GET /api/stats          – aggregated platform metrics
  GET /api/stats/cameras  – per-camera breakdown
"""

from datetime import datetime, date, time, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import Request

try:
    from backend.app.models.database import Violation, get_db, User
    from backend.app.models.schemas import StatsResponse, CameraStats
    from backend.app.routers.auth import get_current_user
except ImportError:
    from ..models.database import Violation, get_db, User
    from ..models.schemas import StatsResponse, CameraStats
    from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
def get_stats(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    mgr = request.app.state.camera_manager
    total = db.query(func.count(Violation.id)).scalar() or 0

    today_start = datetime.combine(date.today(), time.min).replace(tzinfo=timezone.utc)
    today = db.query(func.count(Violation.id)).filter(
        Violation.timestamp >= today_start
    ).scalar() or 0

    # Active cameras = actual running streams
    active_cams = len(mgr.active_camera_ids())

    # Violations by type
    by_type_rows = db.query(
        Violation.violation_type, func.count(Violation.id)
    ).group_by(Violation.violation_type).all()
    by_type = {row[0]: row[1] for row in by_type_rows}

    # Violations by hour (last 24h)
    by_hour = []
    for h in range(24):
        hour_start = datetime.combine(date.today(), time.min).replace(hour=h, tzinfo=timezone.utc)
        hour_end = hour_start.replace(hour=h + 1) if h < 23 else datetime.combine(
            date.today(), time.max
        ).replace(tzinfo=timezone.utc)
        count = db.query(func.count(Violation.id)).filter(
            Violation.timestamp >= hour_start,
            Violation.timestamp < hour_end,
        ).scalar() or 0
        by_hour.append({"hour": h, "count": count})

    # Per-camera stats
    cam_rows = db.query(
        Violation.camera_id,
        func.count(Violation.id),
        func.max(Violation.timestamp),
    ).group_by(Violation.camera_id).all()
    cam_stats = [
        CameraStats(camera_id=r[0], total_violations=r[1], last_violation=r[2])
        for r in cam_rows
    ]

    return StatsResponse(
        total_violations=total,
        today_violations=today,
        cameras_active=active_cams,
        violations_by_type=by_type,
        violations_by_hour=by_hour,
        camera_stats=cam_stats,
    )


@router.get("/cameras", response_model=list[CameraStats])
def get_camera_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = db.query(
        Violation.camera_id,
        func.count(Violation.id),
        func.max(Violation.timestamp),
    ).group_by(Violation.camera_id).all()
    return [CameraStats(camera_id=r[0], total_violations=r[1], last_violation=r[2]) for r in rows]
