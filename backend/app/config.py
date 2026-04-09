"""
Application configuration using pydantic-settings.
Values are read from environment variables / .env file.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Worker Safety Monitoring Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Database
    DB_URL: str = "sqlite:///./data/safety.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    REDIS_MAX_CONNECTIONS: int = 20

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Detection
    MODEL_PATH: str = "yolov8n.pt"
    SNAPSHOT_DIR: str = "snapshots"
    CONF_THRESHOLD: float = 0.4
    ALERT_COOLDOWN_SECONDS: float = 30.0

    # SMTP Email Alerts (optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_RECIPIENTS: str = ""  # comma-separated emails

    # OTP
    OTP_EXPIRY_MINUTES: int = 10

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def alert_recipient_list(self) -> list[str]:
        return [r.strip() for r in self.ALERT_RECIPIENTS.split(",") if r.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
