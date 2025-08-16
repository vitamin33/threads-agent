"""
A/B Testing Integration Layer for Content Generation Pipeline

This module integrates Thompson Sampling A/B testing with the persona runtime
workflow to optimize content generation based on real performance data.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy.orm import Session

from services.orchestrator.db import get_db_session
from services.orchestrator.variant_generator import (
    create_variant_generator,
)
from services.orchestrator import thompson_sampling
from services.common.metrics import record_latency

logger = logging.getLogger(__name__)


class ABTestingContentOptimizer:
    """
    Content optimization engine that uses A/B testing to improve content performance.

    Integrates with persona runtime to:
    1. Select optimal content variants using Thompson Sampling
    2. Track performance of generated content
    3. Continuously optimize content dimensions
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.variant_generator = create_variant_generator(db_session)
        self._cache = {}  # Simple in-memory cache for variant selections
        self._cache_ttl = 300  # 5 minutes TTL

    async def get_optimal_content_config(
        self,
        persona_id: str,
        content_type: str = "post",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get optimal content configuration using Thompson Sampling.

        Args:
            persona_id: ID of the persona generating content
            content_type: Type of content being generated
            context: Additional context for variant selection

        Returns:
            Dictionary containing optimal dimensions for content generation
        """
        try:
            with record_latency("ab_testing_variant_selection"):
                # Check cache first
                cache_key = f"{persona_id}_{content_type}"
                if cache_key in self._cache:
                    cached_result, timestamp = self._cache[cache_key]
                    if (asyncio.get_event_loop().time() - timestamp) < self._cache_ttl:
                        logger.debug(f"Using cached variant selection for {cache_key}")
                        return cached_result

                # Select optimal variants using Thompson Sampling
                variants = self.variant_generator.get_variants_for_persona(
                    persona_id=persona_id,
                    top_k=1,  # Get the single best variant for this generation
                    algorithm="thompson_sampling_exploration",
                )

                if not variants:
                    logger.warning(
                        f"No variants found for persona {persona_id}, using defaults"
                    )
                    return self._get_default_config()

                # Use the top variant
                selected_variant = variants[0]
                config = {
                    "variant_id": selected_variant["variant_id"],
                    "dimensions": selected_variant["dimensions"],
                    "performance": selected_variant["performance"],
                    "content_type": content_type,
                    "persona_id": persona_id,
                    "selection_timestamp": asyncio.get_event_loop().time(),
                }

                # Cache the result
                self._cache[cache_key] = (config, asyncio.get_event_loop().time())

                # Log business metrics
                logger.info("Business metric: optimal_config_generated=1")

                logger.info(
                    f"Selected variant {selected_variant['variant_id']} for persona {persona_id}"
                )
                return config

        except Exception as e:
            logger.error(f"Error getting optimal content config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default content configuration when A/B testing fails."""
        return {
            "variant_id": "default_variant",
            "dimensions": {
                "hook_style": "question",
                "tone": "engaging",
                "length": "medium",
            },
            "performance": {"impressions": 0, "successes": 0},
            "content_type": "post",
            "persona_id": "unknown",
            "selection_timestamp": asyncio.get_event_loop().time(),
        }

    async def track_content_impression(
        self,
        variant_id: str,
        persona_id: str,
        content_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Track that content was generated/shown (impression).

        Args:
            variant_id: ID of the variant used for content generation
            persona_id: ID of the persona that generated the content
            content_metadata: Additional metadata about the content

        Returns:
            True if tracking was successful
        """
        try:
            success = self.variant_generator.update_variant_performance(
                variant_id=variant_id,
                impression=True,
                success=False,
                metadata={
                    "persona_id": persona_id,
                    "action_type": "impression",
                    **(content_metadata or {}),
                },
            )

            if success:
                logger.debug(f"Tracked impression for variant {variant_id}")
                logger.info("Business metric: content_impressions=1")

            return success

        except Exception as e:
            logger.error(f"Error tracking content impression: {e}")
            return False

    async def track_content_engagement(
        self,
        variant_id: str,
        persona_id: str,
        engagement_type: str,
        engagement_value: float = 1.0,
        content_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Track content engagement (success metric).

        Args:
            variant_id: ID of the variant used for content generation
            persona_id: ID of the persona that generated the content
            engagement_type: Type of engagement (like, share, comment, etc.)
            engagement_value: Numeric value of engagement (for weighted scoring)
            content_metadata: Additional metadata about the content

        Returns:
            True if tracking was successful
        """
        try:
            # Determine if this counts as a "success" based on engagement type
            success_types = {"like", "share", "comment", "repost", "click", "view"}
            is_success = engagement_type.lower() in success_types

            # For high-value engagements, track as both impression and success
            success = self.variant_generator.update_variant_performance(
                variant_id=variant_id,
                impression=True,  # Engagement implies the content was seen
                success=is_success,
                metadata={
                    "persona_id": persona_id,
                    "action_type": "engagement",
                    "engagement_type": engagement_type,
                    "engagement_value": engagement_value,
                    **(content_metadata or {}),
                },
            )

            if success:
                logger.debug(
                    f"Tracked {engagement_type} engagement for variant {variant_id}"
                )
                logger.info("Business metric: content_engagements=1")
                logger.info(f"Business metric: engagement_{engagement_type}=1")

            return success

        except Exception as e:
            logger.error(f"Error tracking content engagement: {e}")
            return False

    async def get_performance_insights(
        self, persona_id: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get performance insights for content optimization.

        Args:
            persona_id: Optional filter by persona
            limit: Maximum number of variants to analyze

        Returns:
            Dictionary containing performance insights and recommendations
        """
        try:
            # Load variant performance data
            variants = thompson_sampling.load_variants_from_db(self.db_session)

            if not variants:
                return {"insights": "No performance data available yet"}

            # Sort by performance (success rate, then total impressions)
            sorted_variants = sorted(
                variants,
                key=lambda v: (
                    v["performance"]["successes"]
                    / max(v["performance"]["impressions"], 1),
                    v["performance"]["impressions"],
                ),
                reverse=True,
            )[:limit]

            # Analyze top performing dimensions
            dimension_performance = {}

            for variant in sorted_variants:
                perf = variant["performance"]
                if perf["impressions"] < 5:  # Skip variants with too little data
                    continue

                for dim_name, dim_value in variant["dimensions"].items():
                    if dim_name not in dimension_performance:
                        dimension_performance[dim_name] = {}

                    if dim_value not in dimension_performance[dim_name]:
                        dimension_performance[dim_name][dim_value] = {
                            "total_impressions": 0,
                            "total_successes": 0,
                            "variant_count": 0,
                        }

                    stats = dimension_performance[dim_name][dim_value]
                    stats["total_impressions"] += perf["impressions"]
                    stats["total_successes"] += perf["successes"]
                    stats["variant_count"] += 1

            # Calculate average success rates by dimension
            recommendations = {}
            for dim_name, dim_values in dimension_performance.items():
                best_value = None
                best_rate = 0

                for dim_value, stats in dim_values.items():
                    if stats["total_impressions"] >= 10:  # Minimum data threshold
                        rate = stats["total_successes"] / stats["total_impressions"]
                        if rate > best_rate:
                            best_rate = rate
                            best_value = dim_value

                if best_value:
                    recommendations[dim_name] = {
                        "recommended_value": best_value,
                        "success_rate": best_rate,
                        "total_impressions": dimension_performance[dim_name][
                            best_value
                        ]["total_impressions"],
                    }

            insights = {
                "top_performing_variants": [
                    {
                        "variant_id": v["variant_id"],
                        "dimensions": v["dimensions"],
                        "success_rate": v["performance"]["successes"]
                        / max(v["performance"]["impressions"], 1),
                        "total_impressions": v["performance"]["impressions"],
                    }
                    for v in sorted_variants[:5]
                ],
                "dimension_recommendations": recommendations,
                "total_variants_analyzed": len(variants),
                "variants_with_data": len(
                    [v for v in variants if v["performance"]["impressions"] > 0]
                ),
            }

            logger.info("Business metric: performance_insights_generated=1")

            return insights

        except Exception as e:
            logger.error(f"Error generating performance insights: {e}")
            return {"error": str(e)}


class ContentGenerationIntegration:
    """
    Integration layer between A/B testing and content generation.

    Provides middleware for persona runtime to use A/B testing
    for content optimization.
    """

    def __init__(self):
        self._optimizer_cache = {}

    @asynccontextmanager
    async def get_optimizer(self, db_session: Session):
        """Get A/B testing optimizer with proper resource management."""
        try:
            optimizer = ABTestingContentOptimizer(db_session)
            yield optimizer
        finally:
            # Cleanup if needed
            pass

    async def enhance_content_request(
        self, persona_id: str, original_request: Dict[str, Any], db_session: Session
    ) -> Tuple[Dict[str, Any], str]:
        """
        Enhance content generation request with A/B testing optimizations.

        Args:
            persona_id: ID of the persona generating content
            original_request: Original content generation request
            db_session: Database session

        Returns:
            Tuple of (enhanced_request, variant_id)
        """
        try:
            async with self.get_optimizer(db_session) as optimizer:
                # Get optimal content configuration
                config = await optimizer.get_optimal_content_config(
                    persona_id=persona_id,
                    content_type=original_request.get("content_type", "post"),
                    context=original_request.get("context"),
                )

                # Enhance the request with optimal dimensions
                enhanced_request = {
                    **original_request,
                    "ab_testing_config": config,
                    "dimensions": config["dimensions"],
                    "variant_id": config["variant_id"],
                }

                # Add dimension-specific instructions
                dimensions = config["dimensions"]

                # Enhance hook generation based on hook_style
                if "hook_style" in dimensions:
                    enhanced_request["hook_instructions"] = self._get_hook_instructions(
                        dimensions["hook_style"]
                    )

                # Enhance tone based on tone dimension
                if "tone" in dimensions:
                    enhanced_request["tone_instructions"] = self._get_tone_instructions(
                        dimensions["tone"]
                    )

                # Enhance length based on length dimension
                if "length" in dimensions:
                    enhanced_request["length_instructions"] = (
                        self._get_length_instructions(dimensions["length"])
                    )

                logger.info(
                    f"Enhanced content request for persona {persona_id} with variant {config['variant_id']}"
                )

                return enhanced_request, config["variant_id"]

        except Exception as e:
            logger.error(f"Error enhancing content request: {e}")
            return original_request, "error_fallback"

    def _get_hook_instructions(self, hook_style: str) -> str:
        """Get specific instructions for hook generation based on style."""
        instructions = {
            "question": "Start with an engaging question that makes the reader curious to learn more.",
            "statement": "Begin with a bold, clear statement that captures attention immediately.",
            "controversial": "Open with a thought-provoking statement that challenges conventional wisdom.",
            "story": "Start with a brief, relatable story or anecdote that draws the reader in.",
            "statistic": "Lead with a surprising or compelling statistic that highlights the topic's importance.",
            "personal": "Begin with a personal experience or insight that creates connection.",
            "urgent": "Create a sense of urgency or timeliness that compels immediate attention.",
            "curiosity_gap": "Hint at valuable information without revealing it, creating a knowledge gap.",
        }

        return instructions.get(
            hook_style, "Create an engaging opening that captures attention."
        )

    def _get_tone_instructions(self, tone: str) -> str:
        """Get specific instructions for tone based on dimension."""
        instructions = {
            "casual": "Use conversational, relaxed language as if talking to a friend.",
            "professional": "Maintain a business-appropriate, polished tone throughout.",
            "edgy": "Use bold, provocative language that pushes boundaries appropriately.",
            "humorous": "Include humor and wit while staying relevant to the topic.",
            "serious": "Adopt a thoughtful, earnest tone that conveys importance.",
            "engaging": "Use dynamic, energetic language that keeps readers interested.",
            "authoritative": "Write with confidence and expertise, establishing credibility.",
            "friendly": "Maintain a warm, approachable tone that builds rapport.",
        }

        return instructions.get(tone, "Maintain an appropriate tone for the content.")

    def _get_length_instructions(self, length: str) -> str:
        """Get specific instructions for content length."""
        instructions = {
            "short": "Keep content concise and impactful, under 50 words. Every word should count.",
            "medium": "Develop the topic with appropriate detail, aiming for 50-150 words.",
            "long": "Provide comprehensive coverage with examples and details, 150+ words.",
        }

        return instructions.get(length, "Write at an appropriate length for the topic.")


# Global integration instance
content_integration = ContentGenerationIntegration()


# Dependency injection for FastAPI
async def get_ab_testing_optimizer(
    db: Session = Depends(get_db_session),
) -> ABTestingContentOptimizer:
    """FastAPI dependency for A/B testing optimizer."""
    return ABTestingContentOptimizer(db)


# Utility functions for easy integration
async def track_impression(
    variant_id: str,
    persona_id: str,
    db_session: Session,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Utility function to track content impressions."""
    optimizer = ABTestingContentOptimizer(db_session)
    return await optimizer.track_content_impression(variant_id, persona_id, metadata)


async def track_engagement(
    variant_id: str,
    persona_id: str,
    engagement_type: str,
    db_session: Session,
    engagement_value: float = 1.0,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Utility function to track content engagement."""
    optimizer = ABTestingContentOptimizer(db_session)
    return await optimizer.track_content_engagement(
        variant_id, persona_id, engagement_type, engagement_value, metadata
    )
