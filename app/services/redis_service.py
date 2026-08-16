import os

import redis
from dotenv import load_dotenv


load_dotenv()


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)


redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
)


def ping_redis() -> bool:
    return bool(redis_client.ping())


def set_value(
    key: str,
    value: str,
    expire_seconds: int | None = None,
) -> bool:
    return bool(
        redis_client.set(
            key,
            value,
            ex=expire_seconds,
        )
    )


def get_value(key: str) -> str | None:
    return redis_client.get(key)


def delete_value(key: str) -> int:
    return redis_client.delete(key)
