"""Mock ThreadsClient for performance monitoring when threads_adaptor is not available."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class ThreadsClientSync:
    """Mock Threads client that simulates engagement metrics."""

    def __init__(self):
        logger.warning(
            "Using mock ThreadsClientSync - threads_adaptor service not available"
        )
        self._mock_data = {}

    def get_post_metrics(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get mock metrics for a post."""
        # Return cached mock data or generate new
        if post_id not in self._mock_data:
            self._mock_data[post_id] = {
                "post_id": post_id,
                "views": random.randint(100, 10000),
                "likes": random.randint(10, 500),
                "comments": random.randint(1, 50),
                "shares": random.randint(0, 20),
                "engagement_rate": round(random.uniform(0.01, 0.15), 3),
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Simulate some growth over time
        data = self._mock_data[post_id]
        data["views"] += random.randint(0, 100)
        data["likes"] += random.randint(0, 10)

        return data

    def get_engagement_rate(self, post_id: str) -> float:
        """Get engagement rate for a post."""
        metrics = self.get_post_metrics(post_id)
        if metrics:
            return metrics.get("engagement_rate", 0.0)
        return 0.0
