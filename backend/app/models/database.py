"""
SQLAlchemy models and database session management.
"""

import os
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Text, Boolean
)
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import StaticPool

class Base(DeclarativeBase):
    pass


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    violation_type = Column(String(64), index=True)
    camera_id = Column(String(64), index=True)
    camera_source = Column(String(256), nullable=True)
    image_path = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=True)
    role = Column(String(32), default="viewer")   # "admin" | "viewer"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # OTP fields
    otp = Column(String(8), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String(64), unique=True, index=True, nullable=False)
    source = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PPEAudit(Base):
    __tablename__ = "ppe_audits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = Column(Integer, index=True, nullable=True)
    image_path = Column(Text, nullable=False)
    violations = Column(Text, nullable=True)  # JSON-encoded list
    compliance = Column(String(32), index=True)  # COMPLIANT | NON_COMPLIANT
    details = Column(Text, nullable=True)     # JSON-encoded detections


# ------------------------------------------------------------------ #
# Engine + session factory                                            #
# ------------------------------------------------------------------ #

_engine = None
_SessionLocal = None


def init_db(db_url: str = "sqlite:///./data/safety.db"):
    """Create tables and set up the engine.  Call once at startup."""
    global _engine, _SessionLocal

    if db_url.startswith("sqlite"):
        os.makedirs("data", exist_ok=True)
        connect_args = {"check_same_thread": False}
        _engine = create_engine(
            db_url,
            connect_args=connect_args,
            poolclass=StaticPool,
        )
    else:
        _engine = create_engine(db_url)

    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    Base.metadata.create_all(bind=_engine)
    return _engine


from typing import Generator
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session."""
    if _SessionLocal is None:
        raise RuntimeError("DB not initialised – call init_db() first")
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
