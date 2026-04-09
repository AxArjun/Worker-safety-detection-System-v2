"""
Violations routes:
  GET    /api/violations        – paginated + filtered list
  GET    /api/violations/{id}   – single record
  DELETE /api/violations/{id}   – admin only
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from backend.app.models.database import Violation, get_db, User
    from backend.app.models.schemas import ViolationOut
    from backend.app.routers.auth import get_current_user, require_admin
except ImportError:
    from ..models.database import Violation, get_db, User
    from ..models.schemas import ViolationOut
    from ..routers.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/violations", tags=["violations"])


@router.get("", response_model=list[ViolationOut])
def list_violations(
    violation_type: Optional[str] = Query(None, alias="type"),
    camera_id: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Violation)
    if violation_type:
        q = q.filter(Violation.violation_type == violation_type)
    if camera_id:
        q = q.filter(Violation.camera_id == camera_id)
    if from_date:
        q = q.filter(Violation.timestamp >= from_date)
    if to_date:
        q = q.filter(Violation.timestamp <= to_date)
    return q.order_by(desc(Violation.timestamp)).offset(offset).limit(limit).all()


@router.get("/{violation_id}", response_model=ViolationOut)
def get_violation(
    violation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    v = db.query(Violation).filter(Violation.id == violation_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Violation not found")
    return v


@router.delete("/{violation_id}", status_code=204)
def delete_violation(
    violation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    v = db.query(Violation).filter(Violation.id == violation_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Violation not found")
    db.delete(v)
    db.commit()
