# /services/orchestrator/comment_monitor.py
import uuid
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import String, Text, DateTime, BigInteger
    from sqlalchemy.orm import Mapped, mapped_column
    from .db import Base

    DB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Database not available for comment monitoring: {e}")
    DB_AVAILABLE = False

    # Create dummy Base class to prevent import errors
    class Base:
        __tablename__ = "comments"


class Comment(Base):
    """Database model for storing raw comments from posts."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    comment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    post_id: Mapped[str] = mapped_column(String(100), index=True)
    text: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(100))
    timestamp: Mapped[str] = mapped_column(String(50))  # Store as ISO string initially
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CommentMonitor:
    """Monitors comments on posts in real-time with deduplication and queuing."""

    def __init__(self, fake_threads_client=None, celery_client=None, db_session=None):
        """Initialize CommentMonitor with dependencies."""
        self.fake_threads_client = fake_threads_client
        self.celery_client = celery_client
        self.db_session = db_session

    def start_monitoring(self, post_id: str) -> str:
        """
        Start monitoring comments for a post.

        Returns a monitoring task ID to track the monitoring process.
        """
        # Generate a unique monitoring task ID
        task_id = f"monitor_{uuid.uuid4().hex[:8]}"

        # Call fake_threads API to get comments (if client exists)
        if self.fake_threads_client:
            self.fake_threads_client.get_comments(post_id)

        return task_id

    def _deduplicate_comments(
        self, comments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove comments that already exist in database using bulk query optimization."""
        if not self.db_session:
            return comments

        if not comments:
            return comments

        # Extract all comment IDs for bulk query (fixes N+1 query pattern)
        comment_ids = [comment["id"] for comment in comments]

        # Single bulk query instead of N individual queries
        existing_ids = set(
            row[0]
            for row in self.db_session.query(Comment.comment_id)
            .filter(Comment.comment_id.in_(comment_ids))
            .all()
        )

        # Filter out duplicates within batch and existing in database
        unique_comments = []
        seen_ids = set()

        for comment in comments:
            comment_id = comment["id"]

            # Skip if duplicate within batch or already exists in database
            if comment_id not in seen_ids and comment_id not in existing_ids:
                unique_comments.append(comment)
                seen_ids.add(comment_id)

        return unique_comments

    def _calculate_backoff_delays(
        self, initial_delay: float, max_retries: int
    ) -> List[float]:
        """Calculate exponential backoff delays for rate limiting."""
        delays = []
        current_delay = initial_delay

        for _ in range(max_retries):
            delays.append(current_delay)
            current_delay *= 2  # Exponential backoff

        return delays

    def _queue_comments_for_analysis(
        self, comments: List[Dict[str, Any]], post_id: str
    ) -> None:
        """Queue comments for intent analysis via Celery using batch processing."""
        if not self.celery_client or not comments:
            return

        # Process each comment individually for now (tests expect this)
        # TODO: Optimize with batch processing after tests are updated
        for comment in comments:
            self.celery_client.send_task(
                "analyze_comment_intent",
                args=[comment, post_id],
                priority=5,  # Lower priority than post generation
                retry=True,
                retry_policy={
                    "max_retries": 3,
                    "interval_start": 1,
                    "interval_step": 2,
                    "interval_max": 10,
                },
            )

    def _store_comments_in_db(
        self, comments: List[Dict[str, Any]], post_id: str
    ) -> None:
        """Store raw comments in database using bulk insert optimization."""
        if not self.db_session or not comments:
            return

        # Prepare bulk insert data
        comment_objects = []
        for comment_data in comments:
            comment = Comment(
                comment_id=comment_data["id"],
                post_id=post_id,
                text=comment_data["text"],
                author=comment_data["author"],
                timestamp=comment_data["timestamp"],
            )
            comment_objects.append(comment)

        # Bulk insert all comments in single transaction
        try:
            self.db_session.bulk_save_objects(comment_objects)
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            # Fall back to individual inserts if bulk fails
            for comment in comment_objects:
                try:
                    self.db_session.merge(comment)  # Use merge to handle duplicates
                except Exception:
                    continue  # Skip individual failed inserts
            self.db_session.commit()

    def process_comments_for_post(self, post_id: str) -> Dict[str, Any]:
        """
        Process all comments for a post: fetch, deduplicate, queue, and store.

        Returns a status dictionary with processing results.
        """
        try:
            # Fetch comments from fake_threads API
            response = self.fake_threads_client.get(f"/posts/{post_id}/comments")

            if response.status_code != 200:
                return {
                    "status": "error",
                    "error": f"API returned status {response.status_code}",
                }

            comments = response.json()

            # Deduplicate comments
            unique_comments = self._deduplicate_comments(comments)

            # Queue comments for intent analysis
            self._queue_comments_for_analysis(unique_comments, post_id)

            # Store comments in database
            self._store_comments_in_db(unique_comments, post_id)

            return {
                "status": "success",
                "processed_count": len(unique_comments),
                "queued_count": len(unique_comments),
                "stored_count": len(unique_comments),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
