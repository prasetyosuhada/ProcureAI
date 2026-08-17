import logging
import redis.asyncio as aioredis
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from app.core.config import settings

logger = logging.getLogger(__name__)

async def get_redis_client():
    """Get an async Redis client instance."""
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def check_redis_connection() -> bool:
    """Check if Redis server is reachable."""
    try:
        client = await get_redis_client()
        pong = await client.ping()
        await client.aclose()
        logger.info(f"Redis ping response: {pong}")
        return pong is True or pong == "PONG"
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False

def get_redis_checkpointer():
    """Initialize and return an AsyncRedisSaver context manager for LangGraph state checkpointing."""
    return AsyncRedisSaver.from_conn_string(settings.REDIS_URL)
