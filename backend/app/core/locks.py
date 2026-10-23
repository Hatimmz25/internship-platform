import contextlib
import logging
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize a synchronous Redis client for lock management
redis_client = redis.Redis.from_url(
    getattr(settings, "REDIS_URL", "redis://redis:6379/0"),
    decode_responses=True
)

@contextlib.contextmanager
def redis_lock(lock_name: str, timeout: int = 1800):
    """
    Acquires a non-blocking distributed lock using Redis SETNX.
    Yields True if acquired, False otherwise.
    Auto-expires after `timeout` seconds to prevent deadlocks.
    """
    lock_key = f"lock:{lock_name}"
    acquired = redis_client.set(lock_key, "locked", nx=True, ex=timeout)
    
    try:
        yield acquired
    finally:
        if acquired:
            try:
                redis_client.delete(lock_key)
            except redis.RedisError as e:
                logger.error(f"Failed to release lock {lock_key}: {e}")