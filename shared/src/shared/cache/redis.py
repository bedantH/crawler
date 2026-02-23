from redis.asyncio import Redis
from shared.utils import logger

_redis: Redis | None = None


async def init_redis(host: str = "localhost", port: int = 6379, db: int = 0) -> None:
    """Initialize the module-level Redis connection. Call once at service startup."""
    global _redis
    if _redis is not None:
        return

    _redis = Redis(host=host, port=port, db=db, decode_responses=True)
    await _redis.ping()
    logger.info("Redis connection established (%s:%d/%d)", host, port, db)


def get_redis() -> Redis:
    """Return the shared async Redis client. Raises if init_redis() hasn't been called."""
    if _redis is None:
        raise RuntimeError(
            "Redis not initialized. Call `await init_redis()` during service startup."
        )
    return _redis


async def close_redis() -> None:
    """Gracefully close the Redis connection."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
        logger.info("Redis connection closed")
