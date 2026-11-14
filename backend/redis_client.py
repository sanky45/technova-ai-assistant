
import os
import redis

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL environment variable is not configured")

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=10,
    socket_timeout=10,
    health_check_interval=30
)


def test_redis_connection():
    return redis_client.ping()
