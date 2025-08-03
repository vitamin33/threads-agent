"""
Reply Depth Calculator - Measures conversation generation capability.

Calculates average depth of comment threads to measure discussion quality.
"""

from typing import Dict, Any, List
import httpx
import logging

logger = logging.getLogger(__name__)


class ReplyDepthCalculator:
    """
    Calculates average reply depth to measure how much discussion
    the content generates.

    Deeper threads indicate more engaging, discussion-worthy content.
    """

    async def calculate(
        self, post_id: str, engagement_data: Dict[str, Any], timeframe: str
    ) -> float:
        """
        Calculate average reply depth for a post.

        Args:
            post_id: Unique post identifier
            engagement_data: Dictionary containing engagement metrics
            timeframe: Time window for calculation

        Returns:
            Average conversation thread depth
        """
        # Get detailed comment thread data
        thread_data = await self.get_comment_threads(post_id)

        if not thread_data:
            return 0.0

        total_depth = 0
        thread_count = 0

        for thread in thread_data:
            depth = self.calculate_thread_depth(thread)
            total_depth += depth
            thread_count += 1

        # Calculate average depth
        return total_depth / max(thread_count, 1)

    async def get_comment_threads(self, post_id: str) -> List[Dict]:
        """
        Fetch comment thread structure from fake-threads API.

        Returns:
            List of comment thread dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"http://fake-threads:9009/threads/{post_id}"
                )

                if response.status_code == 200:
                    return response.json().get("threads", [])

                logger.warning(
                    f"Failed to get thread data for post {post_id}: {response.status_code}"
                )
                return []

        except Exception as e:
            logger.error(f"Error fetching thread data for post {post_id}: {e}")
            return []

    def calculate_thread_depth(self, thread: Dict) -> int:
        """
        Recursively calculate maximum depth of a comment thread.

        Args:
            thread: Comment thread dictionary with potential replies

        Returns:
            Maximum depth of the thread
        """
        if not thread.get("replies"):
            return 1

        max_depth = 1
        for reply in thread["replies"]:
            reply_depth = 1 + self.calculate_thread_depth(reply)
            max_depth = max(max_depth, reply_depth)

        return max_depth
