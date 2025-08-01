"""Thompson Sampling with Pattern Fatigue Detection Integration."""

from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta
import numpy as np

from services.orchestrator.thompson_sampling_optimized import ThompsonSamplingOptimized
from services.pattern_analyzer.service import PatternAnalyzerService
from services.pattern_analyzer.pattern_extractor import PatternExtractor
from services.pattern_analyzer.models import PatternUsage
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import os

# Create session factory
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/threads_agent"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)


class ThompsonSamplingWithFatigue(ThompsonSamplingOptimized):
    """Extended Thompson Sampling that integrates pattern fatigue detection."""

    def __init__(self):
        super().__init__()
        self.pattern_service = PatternAnalyzerService()
        self.pattern_extractor = PatternExtractor()
        self.fatigue_weight = 0.3  # Weight for fatigue score in final selection

    def select_top_variants_with_fatigue_detection(
        self,
        variants: List[Dict[str, Any]],
        persona_id: str,
        top_k: int = 10,
        target_er: float = 0.08,
        use_cache: bool = True,
    ) -> List[str]:
        """
        Select top variants considering both Thompson Sampling scores and pattern fatigue.

        Args:
            variants: List of variant dictionaries
            persona_id: Persona ID for fatigue tracking
            top_k: Number of top variants to select
            target_er: Target engagement rate
            use_cache: Whether to use caching

        Returns:
            List of selected variant IDs
        """
        logger.info(
            f"Selecting {top_k} variants for persona {persona_id} with fatigue detection"
        )

        # First, get Thompson Sampling scores for all variants
        thompson_scores = self._calculate_thompson_scores(variants)

        # Check pattern fatigue for each variant
        fresh_variants = []
        for idx, variant in enumerate(variants):
            variant_id = variant.get("variant_id", f"variant_{idx}")
            content = variant.get("content", variant.get("sample_content", ""))

            if not content:
                logger.warning(f"No content found for variant {variant_id}")
                continue

            # Extract patterns from variant content
            pattern = self.pattern_extractor.extract_pattern(content)
            patterns = [pattern] if pattern else []
            variant["patterns"] = patterns

            # Calculate fatigue score for this variant
            fatigue_score = self._calculate_variant_fatigue_score(persona_id, patterns)

            # Combine Thompson score with fatigue score
            thompson_score = thompson_scores.get(variant_id, 0.5)
            combined_score = (
                1 - self.fatigue_weight
            ) * thompson_score + self.fatigue_weight * fatigue_score

            fresh_variants.append(
                {
                    "variant": variant,
                    "variant_id": variant_id,
                    "thompson_score": thompson_score,
                    "fatigue_score": fatigue_score,
                    "combined_score": combined_score,
                    "patterns": patterns,
                }
            )

        # Sort by combined score (descending)
        fresh_variants.sort(key=lambda x: x["combined_score"], reverse=True)

        # Select top k variants
        selected = fresh_variants[:top_k]

        # Record pattern usage for selected variants
        self._record_pattern_usage(selected, persona_id)

        # Return variant IDs
        selected_ids = [item["variant_id"] for item in selected]

        if selected:
            avg_fatigue_score = sum(item["fatigue_score"] for item in selected) / len(
                selected
            )
            logger.info(
                f"Selected {len(selected_ids)} variants with average fatigue score: {avg_fatigue_score:.3f}"
            )
        else:
            logger.info("No variants selected")

        return selected_ids

    def _calculate_thompson_scores(
        self, variants: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate Thompson Sampling scores for all variants."""
        scores = {}

        for idx, variant in enumerate(variants):
            variant_id = variant.get("variant_id", f"variant_{idx}")
            impressions = variant.get("performance", {}).get("impressions", 0)
            successes = variant.get("performance", {}).get("successes", 0)

            # Calculate Thompson score
            alpha = successes + 1
            beta = impressions - successes + 1
            score = np.random.beta(alpha, beta)

            scores[variant_id] = score

        return scores

    def _calculate_variant_fatigue_score(
        self, persona_id: str, patterns: List[str]
    ) -> float:
        """
        Calculate fatigue score for a variant based on its patterns.
        Higher score = fresher content.
        """
        if not patterns:
            return 1.0  # No patterns = maximum freshness

        # Batch query all patterns at once to avoid N+1
        with SessionLocal() as db:
            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)

            # Single query for all patterns
            pattern_counts = (
                db.query(
                    PatternUsage.pattern_id,
                    func.count(PatternUsage.id).label("usage_count"),
                )
                .filter(
                    PatternUsage.persona_id == persona_id,
                    PatternUsage.pattern_id.in_(patterns),
                    PatternUsage.used_at > seven_days_ago,
                )
                .group_by(PatternUsage.pattern_id)
                .all()
            )

            # Convert to dict for O(1) lookups
            usage_map = {pattern: count for pattern, count in pattern_counts}

            # Calculate scores without additional queries
            fatigue_scores = []
            for pattern in patterns:
                recent_uses = usage_map.get(pattern, 0)
                if recent_uses >= 3:
                    score = 0.0
                elif recent_uses == 2:
                    score = 0.25
                elif recent_uses == 1:
                    score = 0.5
                else:
                    score = 1.0
                fatigue_scores.append(score)

            return sum(fatigue_scores) / len(fatigue_scores) if fatigue_scores else 1.0

    def _record_pattern_usage(
        self, selected_variants: List[Dict[str, Any]], persona_id: str
    ) -> None:
        """Record pattern usage for selected variants with bulk insert."""
        db = None
        try:
            db = SessionLocal()

            # Prepare bulk insert data
            pattern_usages = []
            timestamp = datetime.now()

            for item in selected_variants:
                variant_id = item["variant_id"]
                patterns = item.get("patterns", [])

                for pattern in patterns:
                    pattern_usages.append(
                        {
                            "persona_id": persona_id,
                            "pattern_id": pattern,
                            "post_id": variant_id,
                            "used_at": timestamp,
                        }
                    )

            # Bulk insert all pattern usages at once
            if pattern_usages:
                db.bulk_insert_mappings(PatternUsage, pattern_usages)
                db.commit()
                logger.info(f"Recorded {len(pattern_usages)} pattern usages in bulk")

        except Exception as e:
            logger.error(f"Error recording pattern usage: {e}")
            if db:
                db.rollback()
            # Don't fail the selection if recording fails
        finally:
            if db:
                db.close()

    def generate_variants_with_freshness(
        self,
        base_content: str,
        persona_id: str,
        count: int = 10,
        target_er: float = 0.08,
    ) -> List[Dict[str, Any]]:
        """
        Generate fresh variants avoiding fatigued patterns.

        This is a placeholder for integration with the actual variant generation system.
        """
        # Get recently used patterns to avoid
        recent_patterns = self.pattern_service.get_recent_patterns(persona_id, days=7)

        # Filter out patterns used 3+ times
        fatigued_patterns = [
            pattern for pattern, usage in recent_patterns.items() if usage >= 3
        ]

        logger.info(
            f"Avoiding {len(fatigued_patterns)} fatigued patterns for persona {persona_id}"
        )

        # TODO: Integrate with actual variant generation system
        # For now, return a placeholder
        return [
            {
                "variant_id": f"fresh_variant_{i}",
                "content": f"Fresh content variant {i}",
                "patterns": [],
                "performance": {"impressions": 0, "successes": 0},
            }
            for i in range(count)
        ]


# Convenience function for easy integration
def select_variants_with_fatigue_detection(
    variants: List[Dict[str, Any]], persona_id: str, top_k: int = 10, **kwargs
) -> List[str]:
    """
    Convenience function to select variants with fatigue detection.

    Args:
        variants: List of variant dictionaries
        persona_id: Persona ID for fatigue tracking
        top_k: Number of variants to select
        **kwargs: Additional arguments passed to the selector

    Returns:
        List of selected variant IDs
    """
    selector = ThompsonSamplingWithFatigue()
    return selector.select_top_variants_with_fatigue_detection(
        variants, persona_id, top_k, **kwargs
    )
