import redis

from config import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB
)


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)


def test_redis_connection():

    return redis_client.ping()