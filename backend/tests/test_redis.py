import pytest
import asyncio
from app.db.redis import check_redis_connection, get_redis_client

@pytest.mark.asyncio
async def test_redis_ping():
    """Verify that Redis instance is reachable."""
    is_connected = await check_redis_connection()
    assert is_connected is True, "Failed to ping Redis instance"

@pytest.mark.asyncio
async def test_redis_set_get():
    """Verify basic key-value operations on Redis."""
    client = await get_redis_client()
    test_key = "test:procureai:ping"
    test_val = "hello_redis"
    
    await client.set(test_key, test_val, ex=10)
    result = await client.get(test_key)
    await client.aclose()
    
    assert result == test_val, f"Expected {test_val}, got {result}"

if __name__ == "__main__":
    asyncio.run(test_redis_ping())
    asyncio.run(test_redis_set_get())
    print("Redis verification tests passed successfully!")
