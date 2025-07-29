"""Thompson Sampling for variant selection in A/B testing."""

from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session

from services.orchestrator.db.models import VariantPerformance


def select_top_variants(variants: List[Dict[str, Any]], top_k: int = 10) -> List[str]:
    """
    Select top k variants using Thompson Sampling.

    Args:
        variants: List of variant configurations with performance data
        top_k: Number of variants to select

    Returns:
        List of selected variant IDs
    """
    # Calculate Thompson scores for each variant
    scores = []

    for variant in variants:
        impressions = variant["performance"]["impressions"]
        successes = variant["performance"]["successes"]

        # Beta distribution parameters
        # Prior: alpha=1, beta=1 (uniform)
        alpha = successes + 1
        beta = impressions - successes + 1

        # Sample from Beta distribution
        score = np.random.beta(alpha, beta)
        scores.append((score, variant["variant_id"]))

    # Sort by score and select top k
    scores.sort(reverse=True)
    selected_ids = [variant_id for _, variant_id in scores[:top_k]]

    return selected_ids


def select_top_variants_with_exploration(
    variants: List[Dict[str, Any]],
    top_k: int = 10,
    min_impressions: int = 100,
    exploration_ratio: float = 0.3,
) -> List[str]:
    """
    Select top k variants with exploration/exploitation balance.

    Args:
        variants: List of variant configurations with performance data
        top_k: Number of variants to select
        min_impressions: Minimum impressions to consider a variant "experienced"
        exploration_ratio: Fraction of slots to use for exploration (0.0 to 1.0)

    Returns:
        List of selected variant IDs
    """
    # Separate experienced and new variants
    experienced = []
    new_variants = []

    for variant in variants:
        if variant["performance"]["impressions"] >= min_impressions:
            experienced.append(variant)
        else:
            new_variants.append(variant)

    # Calculate how many slots for each
    exploration_slots = int(top_k * exploration_ratio)
    exploitation_slots = top_k - exploration_slots

    selected_ids = []

    # Select from experienced variants using Thompson Sampling
    if experienced and exploitation_slots > 0:
        experienced_ids = select_top_variants(experienced, exploitation_slots)
        selected_ids.extend(experienced_ids)

    # Fill remaining slots with new variants (also using Thompson Sampling)
    remaining_slots = top_k - len(selected_ids)
    if new_variants and remaining_slots > 0:
        new_ids = select_top_variants(new_variants, remaining_slots)
        selected_ids.extend(new_ids)

    # If still not enough, fill from all variants
    if len(selected_ids) < top_k:
        all_ids = select_top_variants(variants, top_k)
        for variant_id in all_ids:
            if variant_id not in selected_ids:
                selected_ids.append(variant_id)
                if len(selected_ids) >= top_k:
                    break

    return selected_ids[:top_k]


def load_variants_from_db(session: Session) -> List[Dict[str, Any]]:
    """
    Load all variant performance data from database.

    Args:
        session: SQLAlchemy database session

    Returns:
        List of variant dictionaries in the expected format
    """
    variants = session.query(VariantPerformance).all()

    result = []
    for variant in variants:
        result.append(
            {
                "variant_id": variant.variant_id,
                "dimensions": variant.dimensions,
                "performance": {
                    "impressions": variant.impressions,
                    "successes": variant.successes,
                },
            }
        )

    return result


def select_top_variants_for_persona(
    session: Session,
    persona_id: str,
    top_k: int = 10,
    min_impressions: int = 100,
    exploration_ratio: float = 0.3,
) -> List[str]:
    """
    Select top variants for a specific persona from database.

    Args:
        session: SQLAlchemy database session
        persona_id: ID of the persona (for future persona-specific filtering)
        top_k: Number of variants to select
        min_impressions: Minimum impressions for experienced variants
        exploration_ratio: Fraction for exploration

    Returns:
        List of selected variant IDs
    """
    # Load variants from database
    variants = load_variants_from_db(session)

    # Use the exploration-aware selection
    return select_top_variants_with_exploration(
        variants,
        top_k=top_k,
        min_impressions=min_impressions,
        exploration_ratio=exploration_ratio,
    )


def update_variant_performance(
    session: Session, variant_id: str, impression: bool = True, success: bool = False
) -> None:
    """
    Update variant performance metrics.

    Args:
        session: SQLAlchemy database session
        variant_id: ID of the variant
        impression: Whether this was an impression
        success: Whether this was a success (engagement)
    """
    from datetime import datetime, timezone

    variant = session.query(VariantPerformance).filter_by(variant_id=variant_id).first()

    if variant:
        if impression:
            variant.impressions += 1
        if success:
            variant.successes += 1
        variant.last_used = datetime.now(timezone.utc)
        session.commit()


# Cache for E3 predictions to avoid repeated calls
_e3_cache = {}


def _get_e3_prediction(predictor, content: str, use_cache: bool = True) -> float:
    """Get E3 prediction with optional caching."""
    if use_cache and content in _e3_cache:
        return _e3_cache[content]

    try:
        result = predictor.predict_engagement_rate(content)
        prediction = result["predicted_engagement_rate"]
        if use_cache:
            _e3_cache[content] = prediction
        return prediction
    except Exception:
        # Return None to indicate failure, will use uniform prior
        return None


def select_top_variants_with_e3_predictions(
    variants: List[Dict[str, Any]],
    predictor: Any,
    top_k: int = 10,
    use_cache: bool = True,
) -> List[str]:
    """
    Select top k variants using Thompson Sampling with E3 predictions as priors.

    Args:
        variants: List of variant configurations with performance data
        predictor: E3 engagement predictor instance
        top_k: Number of variants to select
        use_cache: Whether to cache E3 predictions

    Returns:
        List of selected variant IDs
    """
    # Calculate Thompson scores for each variant
    scores = []

    for variant in variants:
        impressions = variant["performance"]["impressions"]
        successes = variant["performance"]["successes"]

        # Get E3 prediction for informed prior
        sample_content = variant.get("sample_content", "")
        e3_prediction = _get_e3_prediction(predictor, sample_content, use_cache)

        if e3_prediction is not None:
            # Blend E3 prediction with observed data
            # Weight E3 prediction less as we get more observed data
            virtual_impressions = 10  # Pseudo-count for E3 prediction

            if impressions == 0:
                # No observed data - use only E3 prediction
                alpha = e3_prediction * virtual_impressions + 1
                beta = (1 - e3_prediction) * virtual_impressions + 1
            else:
                # Blend E3 with observed data
                # E3 influence decreases as impressions increase
                e3_weight = virtual_impressions / (virtual_impressions + impressions)
                observed_weight = impressions / (virtual_impressions + impressions)

                # Blended success rate
                observed_rate = successes / impressions if impressions > 0 else 0
                blended_rate = (
                    e3_weight * e3_prediction + observed_weight * observed_rate
                )

                # Convert to Beta parameters
                total_pseudo_impressions = impressions + virtual_impressions
                alpha = blended_rate * total_pseudo_impressions + 1
                beta = (1 - blended_rate) * total_pseudo_impressions + 1
        else:
            # E3 failed - use observed data or uniform prior
            alpha = successes + 1
            beta = impressions - successes + 1

        # Sample from Beta distribution
        score = np.random.beta(alpha, beta)
        scores.append((score, variant["variant_id"]))

    # Sort by score and select top k
    scores.sort(reverse=True)
    selected_ids = [variant_id for _, variant_id in scores[:top_k]]

    return selected_ids


def select_top_variants_with_engagement_predictor(
    variants: List[Dict[str, Any]],
    top_k: int = 10,
    use_cache: bool = True,
    predictor_instance: Optional[Any] = None,
) -> List[str]:
    """
    Select top k variants using Thompson Sampling with E3 Engagement Predictor.

    This is a convenience function that automatically imports and uses the
    EngagementPredictor from viral_engine service.

    Args:
        variants: List of variant configurations with performance data
        top_k: Number of variants to select
        use_cache: Whether to cache E3 predictions
        predictor_instance: Optional predictor instance (for testing)

    Returns:
        List of selected variant IDs
    """
    # Use provided predictor or try to import
    if predictor_instance is None:
        # Import here to avoid circular dependencies
        try:
            from services.viral_engine.engagement_predictor import EngagementPredictor

            predictor_instance = EngagementPredictor()
        except ImportError:
            # Fall back to regular Thompson Sampling if E3 not available
            print(
                "Warning: EngagementPredictor not available, using standard Thompson Sampling"
            )
            return select_top_variants(variants, top_k)

    # Use E3-enhanced Thompson Sampling
    return select_top_variants_with_e3_predictions(
        variants, predictor=predictor_instance, top_k=top_k, use_cache=use_cache
    )
