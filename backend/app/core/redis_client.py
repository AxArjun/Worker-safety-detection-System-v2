import redis.asyncio as redis
import logging
from typing import Optional

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RedisClient:
    """Async Redis client wrapper."""
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    async def connect(self):
        """Establish async connection to Redis."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    settings.REDIS_URL,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                    max_connections=settings.REDIS_MAX_CONNECTIONS
                )
                # Ping to verify connection
                await self._client.ping()
                logger.info(f"Connected to Redis at {settings.REDIS_URL} ✓")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._client = None
                raise

    async def disconnect(self):
        """Close connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

# Singleton helper
redis_client = RedisClient()

async def get_redis():
    """Dependency for FastAPI or other services."""
    return redis_client.client
