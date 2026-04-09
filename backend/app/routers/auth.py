"""
Authentication routes:
  POST /api/auth/register
  POST /api/auth/login
  POST /api/auth/otp/send
  POST /api/auth/otp/verify
  GET  /api/auth/me
"""

import random
import string
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from passlib.context import CryptContext

from ..models.database import User, get_db
from ..models.schemas import (
    UserCreate, LoginRequest, OtpSendRequest, OtpVerifyRequest,
    TokenResponse, UserOut
)
from ..config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()
pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_jwt(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


# ------------------------------------------------------------------ #
# Dependency: current user from JWT                                    #
# ------------------------------------------------------------------ #

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise cred_exc
    except JWTError:
        raise cred_exc

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise cred_exc
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ------------------------------------------------------------------ #
# Routes                                                               #
# ------------------------------------------------------------------ #

@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_jwt({"sub": user.email, "role": user.role})
    return TokenResponse(access_token=token, role=user.role, email=user.email)


@router.post("/otp/send")
def send_otp(body: OtpSendRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        # Don't leak whether email exists
        return {"message": "If that email is registered, an OTP has been sent."}
    otp = generate_otp()
    user.otp = hash_password(otp)  # store hashed OTP
    user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    db.commit()
    # In production: send via email. For dev, return in response.
    return {"message": "OTP generated", "otp_debug": otp}  # Remove otp_debug in prod!


@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(body: OtpVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.otp:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
    if datetime.now(timezone.utc) > user.otp_expiry:
        raise HTTPException(status_code=401, detail="OTP expired")
    if not verify_password(body.otp, user.otp):
        raise HTTPException(status_code=401, detail="Invalid OTP")
    # Clear OTP after use
    user.otp = None
    user.otp_expiry = None
    db.commit()
    token = create_jwt({"sub": user.email, "role": user.role})
    return TokenResponse(access_token=token, role=user.role, email=user.email)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
