import pytest
from unittest.mock import AsyncMock, patch

from app.db.redis import check_redis_connection, get_redis_client


@pytest.fixture
def redis_client_mock():
    """Stateful async Redis double for deterministic unit tests."""
    values = {}
    client = AsyncMock()
    client.ping.return_value = True

    async def set_value(key, value, ex=None):
        values[key] = value

    async def get_value(key):
        return values.get(key)

    client.set.side_effect = set_value
    client.get.side_effect = get_value

    with patch("app.db.redis.aioredis.from_url", return_value=client):
        yield client


@pytest.mark.asyncio
async def test_redis_ping(redis_client_mock):
    """Verify the Redis connection helper handles a successful async ping."""
    is_connected = await check_redis_connection()
    assert is_connected is True, "Failed to ping Redis instance"
    redis_client_mock.ping.assert_awaited_once()
    redis_client_mock.aclose.assert_awaited_once()

@pytest.mark.asyncio
async def test_redis_set_get(redis_client_mock):
    """Verify callers can use the async Redis client contract."""
    client = await get_redis_client()
    test_key = "test:procureai:ping"
    test_val = "hello_redis"
    
    await client.set(test_key, test_val, ex=10)
    result = await client.get(test_key)
    await client.aclose()
    
    assert result == test_val, f"Expected {test_val}, got {result}"
