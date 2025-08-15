"""
Automatic Variant Generation System for A/B Testing

This module automatically generates content variants based on persona dimensions
and integrates with the Thompson Sampling A/B testing framework.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from itertools import product
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from services.orchestrator.db.models import VariantPerformance
from services.orchestrator import thompson_sampling

logger = logging.getLogger(__name__)


class VariantGenerator:
    """
    Automatic variant generation for A/B testing content optimization.

    Generates variants based on dimensional combinations and integrates
    with Thompson Sampling for intelligent content optimization.
    """

    # Default dimension configurations for content generation
    DEFAULT_DIMENSIONS = {
        "hook_style": [
            "question",
            "statement",
            "controversial",
            "story",
            "statistic",
            "personal",
            "urgent",
            "curiosity_gap",
        ],
        "tone": [
            "casual",
            "professional",
            "edgy",
            "humorous",
            "serious",
            "engaging",
            "authoritative",
            "friendly",
        ],
        "length": [
            "short",  # <50 words
            "medium",  # 50-150 words
            "long",  # 150+ words
        ],
        "emotion": [
            "excitement",
            "curiosity",
            "urgency",
            "empathy",
            "confidence",
            "surprise",
        ],
        "format": ["thread", "single_post", "quote_tweet", "poll", "story"],
    }

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def generate_variant_id(self, dimensions: Dict[str, str]) -> str:
        """Generate unique variant ID from dimensions."""
        # Sort dimensions for consistent ID generation
        sorted_dims = sorted(dimensions.items())
        dim_string = "_".join(f"{k}_{v}" for k, v in sorted_dims)

        # Create hash for uniqueness while keeping readable prefix
        dim_hash = hashlib.md5(dim_string.encode()).hexdigest()[:8]

        # Create readable variant ID
        primary_dims = ["hook_style", "tone", "length"]
        readable_parts = []

        for dim in primary_dims:
            if dim in dimensions:
                readable_parts.append(dimensions[dim])

        readable_id = "_".join(readable_parts)
        return f"variant_{readable_id}_{dim_hash}"

    def generate_all_variants(
        self,
        custom_dimensions: Optional[Dict[str, List[str]]] = None,
        max_variants: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Generate all possible variant combinations from dimensions.

        Args:
            custom_dimensions: Override default dimensions
            max_variants: Maximum number of variants to generate

        Returns:
            List of variant configurations
        """
        dimensions = custom_dimensions or self.DEFAULT_DIMENSIONS

        # Generate all combinations
        dimension_names = list(dimensions.keys())
        dimension_values = [dimensions[name] for name in dimension_names]

        variants = []
        for combination in product(*dimension_values):
            if len(variants) >= max_variants:
                logger.warning(f"Reached max variants limit: {max_variants}")
                break

            # Create dimension dict
            variant_dims = dict(zip(dimension_names, combination))

            # Generate variant ID
            variant_id = self.generate_variant_id(variant_dims)

            variant = {
                "variant_id": variant_id,
                "dimensions": variant_dims,
                "performance": {"impressions": 0, "successes": 0},
            }

            variants.append(variant)

        logger.info(f"Generated {len(variants)} variant combinations")
        return variants

    def seed_database_variants(
        self,
        variants: Optional[List[Dict[str, Any]]] = None,
        include_bootstrap_data: bool = True,
    ) -> List[VariantPerformance]:
        """
        Seed the database with initial variants.

        Args:
            variants: Custom variants to seed, or None for auto-generation
            include_bootstrap_data: Whether to include some initial performance data

        Returns:
            List of created VariantPerformance objects
        """
        if variants is None:
            # Generate core variants for essential combinations
            core_dimensions = {
                "hook_style": ["question", "statement", "story", "controversial"],
                "tone": ["casual", "professional", "engaging", "edgy"],
                "length": ["short", "medium", "long"],
            }
            variants = self.generate_all_variants(core_dimensions, max_variants=50)

        created_variants = []

        for variant_config in variants:
            try:
                # Check if variant already exists
                existing = (
                    self.db_session.query(VariantPerformance)
                    .filter_by(variant_id=variant_config["variant_id"])
                    .first()
                )

                if existing:
                    logger.debug(
                        f"Variant {variant_config['variant_id']} already exists"
                    )
                    created_variants.append(existing)
                    continue

                # Create initial performance data
                impressions = 0
                successes = 0

                if include_bootstrap_data:
                    # Add some realistic bootstrap data for Thompson Sampling
                    impressions = self._generate_bootstrap_impressions(
                        variant_config["dimensions"]
                    )
                    successes = self._generate_bootstrap_successes(
                        impressions, variant_config["dimensions"]
                    )

                # Create new variant
                variant_obj = VariantPerformance(
                    variant_id=variant_config["variant_id"],
                    dimensions=variant_config["dimensions"],
                    impressions=impressions,
                    successes=successes,
                    last_used=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                )

                self.db_session.add(variant_obj)
                created_variants.append(variant_obj)

                logger.debug(f"Created variant: {variant_config['variant_id']}")

            except IntegrityError as e:
                logger.warning(
                    f"Integrity error creating variant {variant_config['variant_id']}: {e}"
                )
                self.db_session.rollback()
                continue

        try:
            self.db_session.commit()
            logger.info(
                f"Successfully seeded {len(created_variants)} variants to database"
            )

            # Log business metric
            logger.info(f"Business metric: variants_seeded={len(created_variants)}")

        except Exception as e:
            logger.error(f"Error committing variants to database: {e}")
            self.db_session.rollback()
            raise

        return created_variants

    def _generate_bootstrap_impressions(self, dimensions: Dict[str, str]) -> int:
        """Generate realistic bootstrap impression data based on dimensions."""
        # Simulate different performance levels based on combinations
        base_impressions = 50

        # Hook style impact
        hook_multipliers = {
            "question": 1.2,
            "controversial": 1.5,
            "story": 1.1,
            "statement": 1.0,
            "statistic": 0.9,
            "personal": 1.3,
            "urgent": 1.4,
            "curiosity_gap": 1.6,
        }

        # Tone impact
        tone_multipliers = {
            "engaging": 1.3,
            "casual": 1.1,
            "edgy": 1.4,
            "professional": 0.9,
            "humorous": 1.2,
            "serious": 0.8,
            "authoritative": 0.9,
            "friendly": 1.1,
        }

        # Length impact
        length_multipliers = {"short": 1.2, "medium": 1.0, "long": 0.8}

        multiplier = 1.0
        multiplier *= hook_multipliers.get(dimensions.get("hook_style", ""), 1.0)
        multiplier *= tone_multipliers.get(dimensions.get("tone", ""), 1.0)
        multiplier *= length_multipliers.get(dimensions.get("length", ""), 1.0)

        # Add some randomness (deterministic based on variant ID hash)
        variant_hash = hash(str(sorted(dimensions.items()))) % 100
        randomness = 0.8 + (variant_hash / 100) * 0.4  # 0.8 to 1.2

        return int(base_impressions * multiplier * randomness)

    def _generate_bootstrap_successes(
        self, impressions: int, dimensions: Dict[str, str]
    ) -> int:
        """Generate realistic bootstrap success data based on dimensions and impressions."""
        if impressions == 0:
            return 0

        # Base success rate around 8%
        base_rate = 0.08

        # Dimension impact on success rate
        hook_rates = {
            "question": 0.12,
            "controversial": 0.15,
            "curiosity_gap": 0.18,
            "story": 0.11,
            "personal": 0.13,
            "urgent": 0.14,
            "statement": 0.08,
            "statistic": 0.07,
        }

        tone_rates = {
            "engaging": 0.14,
            "edgy": 0.16,
            "casual": 0.10,
            "humorous": 0.12,
            "friendly": 0.09,
            "professional": 0.07,
            "serious": 0.06,
            "authoritative": 0.08,
        }

        # Calculate expected success rate
        success_rate = base_rate
        success_rate = max(
            success_rate, hook_rates.get(dimensions.get("hook_style", ""), base_rate)
        )
        success_rate = max(
            success_rate, tone_rates.get(dimensions.get("tone", ""), base_rate)
        )

        # Add variant-specific randomness
        variant_hash = hash(str(sorted(dimensions.items()))) % 100
        randomness = 0.7 + (variant_hash / 100) * 0.6  # 0.7 to 1.3

        final_rate = success_rate * randomness
        final_rate = min(final_rate, 0.25)  # Cap at 25% success rate

        return int(impressions * final_rate)

    def get_variants_for_persona(
        self,
        persona_id: str,
        top_k: int = 10,
        algorithm: str = "thompson_sampling_exploration",
    ) -> List[Dict[str, Any]]:
        """
        Get optimal variants for a specific persona using Thompson Sampling.

        Args:
            persona_id: ID of the persona requesting variants
            top_k: Number of variants to return
            algorithm: Selection algorithm to use

        Returns:
            List of selected variants with performance data
        """
        try:
            # Load all variants from database
            variants = thompson_sampling.load_variants_from_db(self.db_session)

            if not variants:
                logger.warning("No variants found in database - generating initial set")
                self.seed_database_variants()
                variants = thompson_sampling.load_variants_from_db(self.db_session)

            # Select top variants using Thompson Sampling
            if algorithm == "thompson_sampling":
                selected_ids = thompson_sampling.select_top_variants(variants, top_k)
            elif algorithm == "thompson_sampling_exploration":
                selected_ids = thompson_sampling.select_top_variants_with_exploration(
                    variants, top_k=top_k, min_impressions=50, exploration_ratio=0.3
                )
            elif algorithm == "thompson_sampling_e3":
                selected_ids = (
                    thompson_sampling.select_top_variants_with_engagement_predictor(
                        variants, top_k=top_k
                    )
                )
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")

            # Get full variant data for selected IDs
            selected_variants = []
            for variant_id in selected_ids:
                variant = next(
                    (v for v in variants if v["variant_id"] == variant_id), None
                )
                if variant:
                    selected_variants.append(variant)

            logger.info(
                f"Selected {len(selected_variants)} variants for persona {persona_id}"
            )

            # Log business metric
            logger.info(f"Business metric: variants_selected={len(selected_variants)}")

            return selected_variants

        except Exception as e:
            logger.error(f"Error selecting variants for persona {persona_id}: {e}")
            raise

    def update_variant_performance(
        self,
        variant_id: str,
        impression: bool = True,
        success: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update variant performance based on content engagement.

        Args:
            variant_id: ID of the variant to update
            impression: Whether this counts as an impression
            success: Whether this was a successful engagement
            metadata: Additional tracking metadata

        Returns:
            True if update was successful
        """
        try:
            variant = (
                self.db_session.query(VariantPerformance)
                .filter_by(variant_id=variant_id)
                .first()
            )

            if not variant:
                logger.error(f"Variant {variant_id} not found for performance update")
                return False

            # Update performance metrics
            if impression:
                variant.impressions += 1

            if success:
                # Success implies impression if not already counted
                if not impression:
                    variant.impressions += 1
                variant.successes += 1

            # Update last used timestamp
            variant.last_used = datetime.now(timezone.utc)

            self.db_session.commit()

            logger.debug(
                f"Updated variant {variant_id}: impressions={variant.impressions}, successes={variant.successes}"
            )

            # Log business metrics
            if success:
                logger.info("Business metric: variant_success=1")
            if impression:
                logger.info("Business metric: variant_impression=1")

            return True

        except Exception as e:
            logger.error(f"Error updating variant performance for {variant_id}: {e}")
            self.db_session.rollback()
            return False

    def get_variant_statistics(self, variant_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a specific variant."""
        try:
            variant = (
                self.db_session.query(VariantPerformance)
                .filter_by(variant_id=variant_id)
                .first()
            )

            if not variant:
                return None

            # Calculate confidence intervals using scipy
            try:
                import scipy.stats as stats

                if variant.impressions > 0:
                    # Beta distribution confidence interval
                    alpha = variant.successes + 1
                    beta = variant.impressions - variant.successes + 1

                    lower = stats.beta.ppf(0.025, alpha, beta)
                    upper = stats.beta.ppf(0.975, alpha, beta)

                    confidence_interval = {
                        "lower_bound": float(lower),
                        "upper_bound": float(upper),
                        "confidence_level": 0.95,
                    }
                else:
                    confidence_interval = {
                        "lower_bound": 0.0,
                        "upper_bound": 0.0,
                        "confidence_level": 0.95,
                    }
            except ImportError:
                # Fallback if scipy not available
                confidence_interval = {
                    "lower_bound": 0.0,
                    "upper_bound": 1.0,
                    "confidence_level": 0.95,
                }

            # Thompson Sampling parameters
            alpha = variant.successes + 1
            beta = variant.impressions - variant.successes + 1
            expected_value = alpha / (alpha + beta)
            variance = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))

            return {
                "variant_id": variant.variant_id,
                "dimensions": variant.dimensions,
                "performance": {
                    "impressions": variant.impressions,
                    "successes": variant.successes,
                    "success_rate": variant.success_rate,
                },
                "confidence_intervals": confidence_interval,
                "thompson_sampling_stats": {
                    "alpha": float(alpha),
                    "beta": float(beta),
                    "expected_value": float(expected_value),
                    "variance": float(variance),
                },
                "last_used": variant.last_used,
                "created_at": variant.created_at,
            }

        except Exception as e:
            logger.error(f"Error getting statistics for variant {variant_id}: {e}")
            return None


def create_variant_generator(db_session: Session) -> VariantGenerator:
    """Factory function to create VariantGenerator instance."""
    return VariantGenerator(db_session)


def initialize_default_variants(db_session: Session) -> bool:
    """
    Initialize the database with a default set of high-performing variants.

    This function should be called during system startup to ensure
    variants are available for Thompson Sampling.
    """
    try:
        generator = VariantGenerator(db_session)

        # Check if we already have variants
        existing_count = db_session.query(VariantPerformance).count()

        if existing_count > 0:
            logger.info(
                f"Database already has {existing_count} variants - skipping initialization"
            )
            return True

        # Generate and seed variants
        variants = generator.seed_database_variants(include_bootstrap_data=True)

        logger.info(f"Successfully initialized {len(variants)} default variants")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize default variants: {e}")
        return False
