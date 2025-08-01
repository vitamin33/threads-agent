"""Redis caching layer for performance data."""

import json
import os
from typing import Dict, List, Optional, Any
import redis


class PerformanceCache:
    """Redis-backed performance data cache."""

    def __init__(self, ttl: int = 30):
        """Initialize cache with TTL in seconds."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl

    def get_performance(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get cached performance data."""
        key = f"perf:{post_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set_performance(self, post_id: str, data: Dict[str, Any]) -> None:
        """Cache performance data."""
        key = f"perf:{post_id}"
        self.redis.setex(key, self.ttl, json.dumps(data))

    def bulk_get_performance(
        self, post_ids: List[str]
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """Bulk get with pipeline for efficiency."""
        if not post_ids:
            return {}

        pipe = self.redis.pipeline()
        for post_id in post_ids:
            pipe.get(f"perf:{post_id}")

        results = pipe.execute()
        return {
            post_id: json.loads(data) if data else None
            for post_id, data in zip(post_ids, results)
        }

    def bulk_set_performance(self, performances: Dict[str, Dict[str, Any]]) -> None:
        """Bulk set with pipeline."""
        if not performances:
            return

        pipe = self.redis.pipeline()
        for post_id, data in performances.items():
            key = f"perf:{post_id}"
            pipe.setex(key, self.ttl, json.dumps(data))
        pipe.execute()

    def invalidate(self, post_id: str) -> None:
        """Invalidate cached performance data."""
        self.redis.delete(f"perf:{post_id}")

    def invalidate_many(self, post_ids: List[str]) -> None:
        """Invalidate multiple cached entries."""
        if post_ids:
            keys = [f"perf:{post_id}" for post_id in post_ids]
            self.redis.delete(*keys)
