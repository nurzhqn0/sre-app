from __future__ import annotations

import logging
from typing import Optional
import redis

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_redis_client(redis_url: str) -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis_client


def check_redis(redis_url: str) -> bool:
    try:
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        return bool(client.ping())
    except Exception as exc:
        logger.warning("Redis check failed: %s", exc)
        return False
