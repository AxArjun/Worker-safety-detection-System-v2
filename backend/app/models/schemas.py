"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ------------------------------------------------------------------ #
# Auth                                                                 #
# ------------------------------------------------------------------ #

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = Field(default="viewer", pattern="^(admin|viewer)$")


class LoginRequest(BaseModel):
    email: str
    password: str


class OtpSendRequest(BaseModel):
    email: EmailStr


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
# Violations                                                           #
# ------------------------------------------------------------------ #

class ViolationOut(BaseModel):
    id: int
    timestamp: datetime
    violation_type: str
    camera_id: str
    camera_source: Optional[str]
    image_path: Optional[str]
    confidence: Optional[float]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ViolationCreate(BaseModel):
    violation_type: str
    camera_id: str
    camera_source: Optional[str] = None
    image_path: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None


# ------------------------------------------------------------------ #
# Detection                                                            #
# ------------------------------------------------------------------ #

class DetectionRequest(BaseModel):
    camera_id: str = "cam-0"
    camera_source: Optional[str] = None


class DetectionResult(BaseModel):
    detections: list[dict]
    violations: list[dict]
    fps: float
    violation_count: int
    annotated_frame_b64: Optional[str] = None
    snapshot_path: Optional[str] = None
    alert_triggered: bool = False


# ------------------------------------------------------------------ #
# Stats                                                                #
# ------------------------------------------------------------------ #

class CameraStats(BaseModel):
    camera_id: str
    total_violations: int
    last_violation: Optional[datetime]


class StatsResponse(BaseModel):
    total_violations: int
    today_violations: int
    cameras_active: int
    violations_by_type: dict[str, int]
    violations_by_hour: list[dict]
    camera_stats: list[CameraStats]


# ------------------------------------------------------------------ #
# Camera                                                               #
# ------------------------------------------------------------------ #

class CameraAddRequest(BaseModel):
    camera_id: str
    source: str  # "0", "rtsp://...", "http://..."


class CameraInfo(BaseModel):
    camera_id: str
    source: str
    running: bool
    frame_count: int
    error: Optional[str]
    uptime_s: float


# ------------------------------------------------------------------ #
# PPE Module                                                         #
# ------------------------------------------------------------------ #

class PPEDetection(BaseModel):
    person_id: int
    helmet: bool
    vest: bool
    confidence: float
    status: str  # FULLY_COMPLIANT, NO_VEST, NO_HELMET, NON_COMPLIANT


class PPESummary(BaseModel):
    total_persons: int
    compliant: int
    partial: int
    non_compliant: int


class PPEResponse(BaseModel):
    detections: list[PPEDetection]
    violations: list[str]
    compliance: str  # COMPLIANT | NON_COMPLIANT
    summary: PPESummary
    image_base64: str
    timestamp: datetime = Field(default_factory=datetime.now)
