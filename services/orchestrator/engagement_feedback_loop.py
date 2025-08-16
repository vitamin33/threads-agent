"""
Engagement Feedback Loop for A/B Testing Optimization

This module implements a feedback loop that connects real content engagement
metrics back to the A/B testing system for continuous optimization.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_

from services.orchestrator.db import get_db_session
from services.orchestrator.db.models import Post, VariantPerformance
from services.orchestrator.variant_generator import VariantGenerator
from services.common.metrics import record_latency

logger = logging.getLogger(__name__)


class EngagementType(Enum):
    """Types of content engagement."""

    IMPRESSION = "impression"
    LIKE = "like"
    SHARE = "share"
    COMMENT = "comment"
    CLICK = "click"
    REPOST = "repost"
    SAVE = "save"
    VIEW = "view"


@dataclass
class EngagementEvent:
    """Represents a content engagement event."""

    variant_id: str
    persona_id: str
    post_id: Optional[str]
    engagement_type: EngagementType
    engagement_value: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class EngagementFeedbackLoop:
    """
    Feedback loop system that processes engagement events and updates
    A/B testing variant performance for continuous optimization.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.variant_generator = VariantGenerator(db_session)
        self._event_queue = asyncio.Queue()
        self._batch_size = 50
        self._batch_timeout = 30  # seconds
        self._processing_task = None

        # Engagement scoring weights
        self.engagement_weights = {
            EngagementType.IMPRESSION: 0.1,
            EngagementType.VIEW: 0.2,
            EngagementType.LIKE: 1.0,
            EngagementType.SHARE: 3.0,
            EngagementType.COMMENT: 2.5,
            EngagementType.REPOST: 4.0,
            EngagementType.CLICK: 1.5,
            EngagementType.SAVE: 2.0,
        }

    async def start_processing(self):
        """Start the background processing loop."""
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._processing_loop())
            logger.info("Started engagement feedback loop processing")

    async def stop_processing(self):
        """Stop the background processing loop."""
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped engagement feedback loop processing")

    async def record_engagement(self, event: EngagementEvent) -> bool:
        """
        Record an engagement event for processing.

        Args:
            event: The engagement event to record

        Returns:
            True if event was queued successfully
        """
        try:
            await self._event_queue.put(event)
            logger.debug(
                f"Queued {event.engagement_type.value} event for variant {event.variant_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error queuing engagement event: {e}")
            return False

    async def record_engagement_simple(
        self,
        variant_id: str,
        persona_id: str,
        engagement_type: Union[str, EngagementType],
        engagement_value: float = 1.0,
        post_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Simplified interface for recording engagement events.

        Args:
            variant_id: ID of the content variant
            persona_id: ID of the persona that generated the content
            engagement_type: Type of engagement (string or enum)
            engagement_value: Numeric value of the engagement
            post_id: Optional post ID
            metadata: Optional additional metadata

        Returns:
            True if event was recorded successfully
        """
        try:
            # Convert string to enum if needed
            if isinstance(engagement_type, str):
                engagement_type = EngagementType(engagement_type.lower())

            event = EngagementEvent(
                variant_id=variant_id,
                persona_id=persona_id,
                post_id=post_id,
                engagement_type=engagement_type,
                engagement_value=engagement_value,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata,
            )

            return await self.record_engagement(event)

        except Exception as e:
            logger.error(f"Error recording engagement event: {e}")
            return False

    async def _processing_loop(self):
        """Main processing loop for engagement events."""
        while True:
            try:
                # Collect events for batch processing
                events = []
                timeout_start = asyncio.get_event_loop().time()

                while (
                    len(events) < self._batch_size
                    and (asyncio.get_event_loop().time() - timeout_start)
                    < self._batch_timeout
                ):
                    try:
                        # Wait for events with timeout
                        remaining_timeout = self._batch_timeout - (
                            asyncio.get_event_loop().time() - timeout_start
                        )
                        if remaining_timeout <= 0:
                            break

                        event = await asyncio.wait_for(
                            self._event_queue.get(), timeout=remaining_timeout
                        )
                        events.append(event)

                    except asyncio.TimeoutError:
                        break

                # Process the batch if we have events
                if events:
                    await self._process_event_batch(events)

                # Small delay to prevent tight looping
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.info("Engagement processing loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in engagement processing loop: {e}")
                await asyncio.sleep(1)  # Wait before retrying

    async def _process_event_batch(self, events: List[EngagementEvent]):
        """Process a batch of engagement events."""
        try:
            with record_latency("engagement_batch_processing"):
                # Group events by variant
                variant_updates = {}

                for event in events:
                    if event.variant_id not in variant_updates:
                        variant_updates[event.variant_id] = {
                            "impressions": 0,
                            "engagement_score": 0.0,
                            "engagement_count": 0,
                            "events": [],
                        }

                    update = variant_updates[event.variant_id]
                    update["events"].append(event)

                    # Calculate weighted engagement score
                    weight = self.engagement_weights.get(event.engagement_type, 1.0)
                    engagement_score = weight * event.engagement_value

                    # Update metrics
                    if event.engagement_type == EngagementType.IMPRESSION:
                        update["impressions"] += 1
                    else:
                        update["engagement_count"] += 1
                        update["engagement_score"] += engagement_score

                # Apply updates to database
                for variant_id, update_data in variant_updates.items():
                    await self._update_variant_performance(variant_id, update_data)

                logger.info(
                    f"Processed batch of {len(events)} engagement events for {len(variant_updates)} variants"
                )
                logger.info(
                    f"Business metric: engagement_events_processed={len(events)}"
                )

        except Exception as e:
            logger.error(f"Error processing event batch: {e}")

    async def _update_variant_performance(
        self, variant_id: str, update_data: Dict[str, Any]
    ):
        """Update variant performance based on engagement data."""
        try:
            # Find the variant
            variant = (
                self.db_session.query(VariantPerformance)
                .filter_by(variant_id=variant_id)
                .first()
            )

            if not variant:
                logger.warning(f"Variant {variant_id} not found for performance update")
                return

            # Calculate if this batch represents a "success"
            # Success is defined as having significant engagement beyond just impressions
            engagement_score = update_data["engagement_score"]
            engagement_count = update_data["engagement_count"]

            # Threshold for considering engagement as "success"
            success_threshold = 2.0  # Minimum weighted engagement score
            has_success = engagement_score >= success_threshold

            # Update variant metrics
            variant.impressions += max(update_data["impressions"], engagement_count)

            if has_success:
                # Convert engagement score to discrete successes
                # Higher engagement scores count as multiple successes
                success_count = max(1, int(engagement_score / 2.0))
                variant.successes += success_count

            # Update timestamp
            variant.last_used = datetime.now(timezone.utc)

            # Commit changes
            self.db_session.commit()

            logger.debug(
                f"Updated variant {variant_id}: +{update_data['impressions']} impressions, engagement_score={engagement_score:.2f}"
            )

            # Log metrics
            logger.info("Business metric: variant_performance_updates=1")
            if has_success:
                logger.info("Business metric: variant_engagement_successes=1")

        except Exception as e:
            logger.error(f"Error updating variant performance for {variant_id}: {e}")
            self.db_session.rollback()

    async def sync_post_engagements(self, hours_back: int = 24) -> int:
        """
        Sync engagement data from posts to variant performance.

        This method looks at recent posts and their engagement metrics,
        then updates the corresponding variant performance data.

        Args:
            hours_back: How many hours back to sync data

        Returns:
            Number of posts processed
        """
        try:
            with record_latency("post_engagement_sync"):
                # Find recent posts with engagement data
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

                posts = (
                    self.db_session.query(Post)
                    .filter(
                        and_(
                            Post.ts >= cutoff_time,
                            Post.engagement_rate.isnot(None),
                            Post.engagement_rate > 0,
                        )
                    )
                    .all()
                )

                synced_count = 0

                for post in posts:
                    # Try to extract variant information from post metadata
                    variant_id = await self._extract_variant_from_post(post)

                    if variant_id:
                        # Convert engagement rate to engagement events
                        engagement_value = (
                            post.engagement_rate * 10
                        )  # Scale up the engagement

                        await self.record_engagement_simple(
                            variant_id=variant_id,
                            persona_id=post.persona_id,
                            engagement_type=EngagementType.LIKE,  # Assume likes for simplicity
                            engagement_value=engagement_value,
                            post_id=str(post.id),
                            metadata={
                                "source": "post_sync",
                                "post_tokens": post.tokens_used,
                                "engagement_rate": post.engagement_rate,
                            },
                        )

                        synced_count += 1

                logger.info(f"Synced engagement data from {synced_count} posts")
                logger.info(f"Business metric: posts_synced={synced_count}")

                return synced_count

        except Exception as e:
            logger.error(f"Error syncing post engagements: {e}")
            return 0

    async def _extract_variant_from_post(self, post: Post) -> Optional[str]:
        """
        Extract variant ID from post data.

        This is a heuristic method that tries to determine which variant
        was used to generate a specific post.
        """
        try:
            # For now, we'll use a simple heuristic based on post characteristics
            # In a real implementation, this would be stored with the post

            hook = post.hook.lower() if post.hook else ""
            body = post.body.lower() if post.body else ""

            # Analyze hook style
            if "?" in hook:
                hook_style = "question"
            elif any(word in hook for word in ["breaking", "urgent", "now"]):
                hook_style = "urgent"
            elif any(word in hook for word in ["story", "once", "remember"]):
                hook_style = "story"
            else:
                hook_style = "statement"

            # Analyze tone
            if any(
                word in (hook + " " + body) for word in ["awesome", "amazing", "love"]
            ):
                tone = "engaging"
            elif any(
                word in (hook + " " + body) for word in ["professional", "business"]
            ):
                tone = "professional"
            else:
                tone = "casual"

            # Analyze length
            total_length = len(hook) + len(body)
            if total_length < 100:
                length = "short"
            elif total_length > 300:
                length = "long"
            else:
                length = "medium"

            # Try to find a matching variant
            variant = (
                self.db_session.query(VariantPerformance)
                .filter(
                    VariantPerformance.dimensions.contains(
                        {"hook_style": hook_style, "tone": tone, "length": length}
                    )
                )
                .first()
            )

            if variant:
                return variant.variant_id

            # Fallback: find any variant with similar characteristics
            variants = (
                self.db_session.query(VariantPerformance)
                .filter(VariantPerformance.dimensions.has_key("hook_style"))
                .all()
            )

            for variant in variants:
                dims = variant.dimensions
                score = 0
                if dims.get("hook_style") == hook_style:
                    score += 1
                if dims.get("tone") == tone:
                    score += 1
                if dims.get("length") == length:
                    score += 1

                if score >= 2:  # At least 2 dimensions match
                    return variant.variant_id

            return None

        except Exception as e:
            logger.error(f"Error extracting variant from post: {e}")
            return None

    async def get_engagement_analytics(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get engagement analytics for the feedback loop.

        Args:
            days_back: Number of days of data to analyze

        Returns:
            Dictionary containing engagement analytics
        """
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_back)

            # Get variant performance data
            variants = (
                self.db_session.query(VariantPerformance)
                .filter(VariantPerformance.last_used >= cutoff_time)
                .all()
            )

            # Calculate analytics
            total_variants = len(variants)
            active_variants = len([v for v in variants if v.impressions > 0])
            total_impressions = sum(v.impressions for v in variants)
            total_successes = sum(v.successes for v in variants)

            # Calculate success rate distribution
            success_rates = [v.success_rate for v in variants if v.impressions > 0]
            avg_success_rate = (
                sum(success_rates) / len(success_rates) if success_rates else 0
            )

            # Find top performing dimensions
            dimension_performance = {}
            for variant in variants:
                if variant.impressions < 5:  # Skip variants with little data
                    continue

                for dim_name, dim_value in variant.dimensions.items():
                    if dim_name not in dimension_performance:
                        dimension_performance[dim_name] = {}

                    if dim_value not in dimension_performance[dim_name]:
                        dimension_performance[dim_name][dim_value] = {
                            "total_impressions": 0,
                            "total_successes": 0,
                            "variants": 0,
                        }

                    stats = dimension_performance[dim_name][dim_value]
                    stats["total_impressions"] += variant.impressions
                    stats["total_successes"] += variant.successes
                    stats["variants"] += 1

            # Calculate success rates by dimension
            for dim_name in dimension_performance:
                for dim_value in dimension_performance[dim_name]:
                    stats = dimension_performance[dim_name][dim_value]
                    if stats["total_impressions"] > 0:
                        stats["success_rate"] = (
                            stats["total_successes"] / stats["total_impressions"]
                        )
                    else:
                        stats["success_rate"] = 0.0

            analytics = {
                "period_days": days_back,
                "total_variants": total_variants,
                "active_variants": active_variants,
                "total_impressions": total_impressions,
                "total_successes": total_successes,
                "overall_success_rate": total_successes / total_impressions
                if total_impressions > 0
                else 0,
                "average_success_rate": avg_success_rate,
                "dimension_performance": dimension_performance,
                "top_variants": sorted(
                    [
                        {
                            "variant_id": v.variant_id,
                            "dimensions": v.dimensions,
                            "success_rate": v.success_rate,
                            "impressions": v.impressions,
                        }
                        for v in variants
                        if v.impressions >= 10
                    ],
                    key=lambda x: x["success_rate"],
                    reverse=True,
                )[:10],
            }

            return analytics

        except Exception as e:
            logger.error(f"Error generating engagement analytics: {e}")
            return {"error": str(e)}


# Global feedback loop instance
_feedback_loop = None


async def get_feedback_loop(db_session: Session) -> EngagementFeedbackLoop:
    """Get or create the global feedback loop instance."""
    global _feedback_loop

    if _feedback_loop is None:
        _feedback_loop = EngagementFeedbackLoop(db_session)
        await _feedback_loop.start_processing()

    return _feedback_loop


# Utility functions for easy integration
async def record_content_impression(
    variant_id: str,
    persona_id: str,
    post_id: Optional[str] = None,
    db_session: Session = None,
) -> bool:
    """Utility function to record content impressions."""
    if db_session is None:
        db_session = next(get_db_session())

    feedback_loop = await get_feedback_loop(db_session)
    return await feedback_loop.record_engagement_simple(
        variant_id=variant_id,
        persona_id=persona_id,
        engagement_type=EngagementType.IMPRESSION,
        post_id=post_id,
    )


async def record_content_engagement(
    variant_id: str,
    persona_id: str,
    engagement_type: str,
    engagement_value: float = 1.0,
    post_id: Optional[str] = None,
    db_session: Session = None,
) -> bool:
    """Utility function to record content engagement."""
    if db_session is None:
        db_session = next(get_db_session())

    feedback_loop = await get_feedback_loop(db_session)
    return await feedback_loop.record_engagement_simple(
        variant_id=variant_id,
        persona_id=persona_id,
        engagement_type=engagement_type,
        engagement_value=engagement_value,
        post_id=post_id,
    )
