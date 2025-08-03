"""Redis cache connection utilities for viral metrics service."""

import os
import redis


def get_redis_connection():
    """Get Redis connection for viral metrics caching."""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    return redis.from_url(redis_url, decode_responses=True)
