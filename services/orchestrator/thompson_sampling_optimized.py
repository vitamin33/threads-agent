"""Optimized Thompson Sampling for variant selection in A/B testing."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import or_
from functools import lru_cache
import hashlib
import heapq
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from prometheus_client import Histogram, Counter, Gauge

from services.orchestrator.db.models import VariantPerformance

# Prometheus metrics
thompson_selection_duration = Histogram(
    "thompson_sampling_selection_duration_seconds",
    "Time spent selecting variants",
    ["method", "variant_count"],
)

thompson_cache_hits = Counter(
    "thompson_sampling_cache_hits_total", "E3 cache hit count"
)

thompson_cache_misses = Counter(
    "thompson_sampling_cache_misses_total", "E3 cache miss count"
)

thompson_variant_count = Gauge(
    "thompson_sampling_active_variants", "Number of active variants being considered"
)

e3_prediction_duration = Histogram(
    "thompson_sampling_e3_prediction_seconds", "Time spent on E3 predictions"
)

# Configuration
MAX_CACHE_SIZE = 500
BATCH_SIZE = 10
PREDICTION_TIMEOUT = 0.5  # 500ms per prediction
ACTIVE_VARIANT_DAYS = 30


class ThompsonSamplingOptimized:
    """Optimized Thompson Sampling implementation with caching and batching."""

    def __init__(self, cache_size: int = MAX_CACHE_SIZE):
        self.cache_size = cache_size
        self._executor = ThreadPoolExecutor(max_workers=4)

    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def _get_e3_prediction_cached(
        self, content_hash: str, predictor_id: int
    ) -> Optional[float]:
        """LRU cache for E3 predictions."""
        # This will be populated by the actual prediction
        pass

    def _compute_e3_prediction(self, predictor: Any, content: str) -> Optional[float]:
        """Compute E3 prediction with timeout."""
        try:
            with e3_prediction_duration.time():
                result = predictor.predict_engagement_rate(content)
                return result["predicted_engagement_rate"]
        except Exception:
            return None

    def _get_e3_prediction(
        self, predictor: Any, content: str, use_cache: bool = True
    ) -> Optional[float]:
        """Get E3 prediction with bounded caching."""
        if not use_cache:
            return self._compute_e3_prediction(predictor, content)

        # Create hash of content for cache key
        content_hash = hashlib.md5(content.encode()).hexdigest()
        predictor_id = id(predictor)

        # Try to get from cache
        try:
            # Check if value exists in cache
            cached = self._get_e3_prediction_cached(content_hash, predictor_id)
            thompson_cache_hits.inc()
            return cached
        except KeyError:
            thompson_cache_misses.inc()

            # Compute prediction
            prediction = self._compute_e3_prediction(predictor, content)

            if prediction is not None:
                # Store in cache
                self._get_e3_prediction_cached.__wrapped__(
                    self, content_hash, predictor_id
                ).__wrapped__ = prediction

            return prediction

    @thompson_selection_duration.labels(method="basic", variant_count="unknown").time()
    def select_top_variants(
        self, variants: List[Dict[str, Any]], top_k: int = 10
    ) -> List[str]:
        """Optimized variant selection using heap for O(n log k) complexity."""
        thompson_variant_count.set(len(variants))

        # Use min heap to keep top k elements
        heap = []

        for variant in variants:
            impressions = variant["performance"]["impressions"]
            successes = variant["performance"]["successes"]

            # Beta distribution parameters
            alpha = successes + 1
            beta = impressions - successes + 1

            # Sample from Beta distribution
            score = np.random.beta(alpha, beta)

            # Maintain heap of top k scores
            if len(heap) < top_k:
                heapq.heappush(heap, (score, variant["variant_id"]))
            elif score > heap[0][0]:
                heapq.heapreplace(heap, (score, variant["variant_id"]))

        # Extract results in descending order
        results = []
        while heap:
            score, variant_id = heapq.heappop(heap)
            results.append(variant_id)

        return results[::-1]  # Reverse to get descending order

    def load_variants_from_db_optimized(
        self,
        session: Session,
        persona_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Load variant performance data with efficient querying."""
        # Only fetch necessary columns
        query = session.query(
            VariantPerformance.variant_id,
            VariantPerformance.dimensions,
            VariantPerformance.impressions,
            VariantPerformance.successes,
        )

        # Add filtering for active variants
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=ACTIVE_VARIANT_DAYS)
        query = query.filter(
            or_(
                VariantPerformance.impressions > 0,
                VariantPerformance.created_at > cutoff_date,
            )
        )

        # Filter by persona if provided
        if persona_id:
            # Assuming dimensions contains persona_id
            query = query.filter(
                VariantPerformance.dimensions["persona_id"].astext == persona_id
            )

        # Order by impressions desc for better cache locality
        query = query.order_by(VariantPerformance.impressions.desc())

        if limit:
            query = query.limit(limit)

        # Use yield_per for memory efficiency
        result = []
        for row in query.yield_per(100):
            result.append(
                {
                    "variant_id": row.variant_id,
                    "dimensions": row.dimensions,
                    "performance": {
                        "impressions": row.impressions,
                        "successes": row.successes,
                    },
                }
            )

        return result

    async def select_top_variants_with_e3_predictions_async(
        self,
        variants: List[Dict[str, Any]],
        predictor: Any,
        top_k: int = 10,
        use_cache: bool = True,
    ) -> List[str]:
        """Async variant selection with batched E3 predictions."""
        thompson_variant_count.set(len(variants))

        with thompson_selection_duration.labels(
            method="e3_async", variant_count=len(variants)
        ).time():
            scores = []

            # Process variants in batches
            for i in range(0, len(variants), BATCH_SIZE):
                batch = variants[i : i + BATCH_SIZE]

                # Prepare batch predictions
                futures = []
                for variant in batch:
                    sample_content = variant.get("sample_content", "")
                    if sample_content:
                        future = self._executor.submit(
                            self._get_e3_prediction,
                            predictor,
                            sample_content,
                            use_cache,
                        )
                        futures.append((variant, future))
                    else:
                        futures.append((variant, None))

                # Process batch results
                for variant, future in futures:
                    impressions = variant["performance"]["impressions"]
                    successes = variant["performance"]["successes"]

                    e3_prediction = None
                    if future:
                        try:
                            e3_prediction = future.result(timeout=PREDICTION_TIMEOUT)
                        except:
                            e3_prediction = None

                    # Calculate Thompson score with E3 prior
                    if e3_prediction is not None:
                        # Blend E3 prediction with observed data
                        virtual_impressions = 10

                        if impressions == 0:
                            alpha = e3_prediction * virtual_impressions + 1
                            beta = (1 - e3_prediction) * virtual_impressions + 1
                        else:
                            # Blend with decreasing E3 influence
                            e3_weight = virtual_impressions / (
                                virtual_impressions + impressions
                            )
                            observed_weight = impressions / (
                                virtual_impressions + impressions
                            )

                            observed_rate = (
                                successes / impressions if impressions > 0 else 0
                            )
                            blended_rate = (
                                e3_weight * e3_prediction
                                + observed_weight * observed_rate
                            )

                            total_pseudo_impressions = impressions + virtual_impressions
                            alpha = blended_rate * total_pseudo_impressions + 1
                            beta = (1 - blended_rate) * total_pseudo_impressions + 1
                    else:
                        # Fallback to uniform prior
                        alpha = successes + 1
                        beta = impressions - successes + 1

                    score = np.random.beta(alpha, beta)
                    scores.append((score, variant["variant_id"]))

            # Use heap for efficient top-k selection
            return self._extract_top_k(scores, top_k)

    def _extract_top_k(self, scores: List[Tuple[float, str]], top_k: int) -> List[str]:
        """Extract top k variants using heap."""
        # For small k, heap is more efficient
        if top_k < len(scores) / 10:
            heap = scores[:top_k]
            heapq.heapify(heap)

            for score, variant_id in scores[top_k:]:
                if score > heap[0][0]:
                    heapq.heapreplace(heap, (score, variant_id))

            # Extract in descending order
            results = []
            while heap:
                _, variant_id = heapq.heappop(heap)
                results.append(variant_id)
            return results[::-1]
        else:
            # For large k, sorting is simpler
            scores.sort(reverse=True)
            return [variant_id for _, variant_id in scores[:top_k]]

    def update_variant_performance_batch(
        self, session: Session, updates: List[Dict[str, Any]]
    ) -> None:
        """Batch update variant performance metrics."""
        # Group updates by variant_id
        variant_updates = {}
        for update in updates:
            variant_id = update["variant_id"]
            if variant_id not in variant_updates:
                variant_updates[variant_id] = {"impressions": 0, "successes": 0}

            if update.get("impression", False):
                variant_updates[variant_id]["impressions"] += 1
            if update.get("success", False):
                variant_updates[variant_id]["successes"] += 1

        # Bulk update using SQL
        from sqlalchemy import case

        # Build case statements for bulk update
        impression_cases = []
        success_cases = []
        variant_ids = list(variant_updates.keys())

        for variant_id, updates in variant_updates.items():
            impression_cases.append(
                (
                    VariantPerformance.variant_id == variant_id,
                    VariantPerformance.impressions + updates["impressions"],
                )
            )
            success_cases.append(
                (
                    VariantPerformance.variant_id == variant_id,
                    VariantPerformance.successes + updates["successes"],
                )
            )

        # Execute bulk update
        if variant_ids:
            session.query(VariantPerformance).filter(
                VariantPerformance.variant_id.in_(variant_ids)
            ).update(
                {
                    VariantPerformance.impressions: case(
                        impression_cases, else_=VariantPerformance.impressions
                    ),
                    VariantPerformance.successes: case(
                        success_cases, else_=VariantPerformance.successes
                    ),
                    VariantPerformance.last_used: datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )

            session.commit()

    def __del__(self):
        """Cleanup executor on deletion."""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)


# Convenience functions for backward compatibility
_default_optimizer = None


def get_default_optimizer() -> ThompsonSamplingOptimized:
    """Get or create default optimizer instance."""
    global _default_optimizer
    if _default_optimizer is None:
        _default_optimizer = ThompsonSamplingOptimized()
    return _default_optimizer


def select_top_variants(variants: List[Dict[str, Any]], top_k: int = 10) -> List[str]:
    """Backward compatible function."""
    return get_default_optimizer().select_top_variants(variants, top_k)


def load_variants_from_db(session: Session) -> List[Dict[str, Any]]:
    """Backward compatible function."""
    return get_default_optimizer().load_variants_from_db_optimized(session)


def select_top_variants_for_persona(
    session: Session,
    persona_id: str,
    top_k: int = 10,
    min_impressions: int = 100,
    exploration_ratio: float = 0.3,
) -> List[str]:
    """Optimized variant selection for persona."""
    optimizer = get_default_optimizer()

    # Load variants with optimization
    variants = optimizer.load_variants_from_db_optimized(
        session,
        persona_id=persona_id,
        limit=1000,  # Reasonable limit for processing
    )

    # Separate by experience level
    experienced = []
    new_variants = []

    for variant in variants:
        if variant["performance"]["impressions"] >= min_impressions:
            experienced.append(variant)
        else:
            new_variants.append(variant)

    # Calculate slots
    exploration_slots = int(top_k * exploration_ratio)
    exploitation_slots = top_k - exploration_slots

    selected_ids = []

    # Select from experienced variants
    if experienced and exploitation_slots > 0:
        experienced_ids = optimizer.select_top_variants(experienced, exploitation_slots)
        selected_ids.extend(experienced_ids)

    # Fill with new variants
    remaining_slots = top_k - len(selected_ids)
    if new_variants and remaining_slots > 0:
        new_ids = optimizer.select_top_variants(new_variants, remaining_slots)
        selected_ids.extend(new_ids)

    # Fill any remaining slots
    if len(selected_ids) < top_k:
        all_ids = optimizer.select_top_variants(variants, top_k)
        for variant_id in all_ids:
            if variant_id not in selected_ids:
                selected_ids.append(variant_id)
                if len(selected_ids) >= top_k:
                    break

    return selected_ids[:top_k]


async def select_top_variants_with_engagement_predictor_async(
    variants: List[Dict[str, Any]],
    top_k: int = 10,
    use_cache: bool = True,
    predictor_instance: Optional[Any] = None,
) -> List[str]:
    """Async version with E3 predictions."""
    if predictor_instance is None:
        try:
            from services.viral_engine.engagement_predictor import EngagementPredictor

            predictor_instance = EngagementPredictor()
        except ImportError:
            # Fallback to regular selection
            return select_top_variants(variants, top_k)

    optimizer = get_default_optimizer()
    return await optimizer.select_top_variants_with_e3_predictions_async(
        variants, predictor=predictor_instance, top_k=top_k, use_cache=use_cache
    )
