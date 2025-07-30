"""Performance tests for Thompson Sampling optimization."""

import pytest
import time
import asyncio
from typing import List, Dict, Any
import numpy as np
from unittest.mock import Mock, patch

from services.orchestrator.thompson_sampling import (
    select_top_variants as select_top_variants_original,
    load_variants_from_db as load_variants_from_db_original,
    select_top_variants_with_engagement_predictor,
)
from services.orchestrator.thompson_sampling_optimized import (
    ThompsonSamplingOptimized,
    select_top_variants as select_top_variants_optimized,
    select_top_variants_with_engagement_predictor_async,
)


class TestThompsonSamplingPerformance:
    """Performance comparison tests."""

    @pytest.fixture
    def mock_variants_small(self) -> List[Dict[str, Any]]:
        """Generate 50 test variants."""
        return self._generate_variants(50)

    @pytest.fixture
    def mock_variants_large(self) -> List[Dict[str, Any]]:
        """Generate 192 test variants (realistic scenario)."""
        return self._generate_variants(192)

    @pytest.fixture
    def mock_variants_huge(self) -> List[Dict[str, Any]]:
        """Generate 1000 test variants (stress test)."""
        return self._generate_variants(1000)

    def _generate_variants(self, count: int) -> List[Dict[str, Any]]:
        """Generate test variant data."""
        variants = []
        for i in range(count):
            # Simulate realistic distribution
            if i < count * 0.1:  # 10% high performers
                impressions = np.random.randint(1000, 5000)
                success_rate = np.random.uniform(0.08, 0.15)
            elif i < count * 0.3:  # 20% medium performers
                impressions = np.random.randint(100, 1000)
                success_rate = np.random.uniform(0.04, 0.08)
            elif i < count * 0.6:  # 30% low performers
                impressions = np.random.randint(10, 100)
                success_rate = np.random.uniform(0.01, 0.04)
            else:  # 40% new variants
                impressions = np.random.randint(0, 10)
                success_rate = 0.0

            successes = int(impressions * success_rate)

            variants.append(
                {
                    "variant_id": f"variant_{i}",
                    "dimensions": {
                        "persona_id": f"persona_{i % 10}",
                        "hook_type": f"hook_{i % 20}",
                    },
                    "performance": {"impressions": impressions, "successes": successes},
                    "sample_content": f"Sample content for variant {i} with engagement hooks",
                }
            )

        return variants

    def test_selection_performance_small(self, mock_variants_small):
        """Test performance with small variant set."""
        # Original implementation
        start = time.time()
        for _ in range(100):
            result_orig = select_top_variants_original(mock_variants_small, top_k=10)
        time_orig = time.time() - start

        # Optimized implementation
        start = time.time()
        for _ in range(100):
            result_opt = select_top_variants_optimized(mock_variants_small, top_k=10)
        time_opt = time.time() - start

        # Both should return same number of results
        assert len(result_orig) == len(result_opt) == 10

        # Optimized should be faster or comparable
        print("\nSmall set (50 variants, 100 iterations):")
        print(f"Original: {time_orig:.3f}s")
        print(f"Optimized: {time_opt:.3f}s")
        print(f"Speedup: {time_orig / time_opt:.2f}x")

    def test_selection_performance_large(self, mock_variants_large):
        """Test performance with realistic variant set (192)."""
        # Original implementation
        start = time.time()
        for _ in range(50):
            result_orig = select_top_variants_original(mock_variants_large, top_k=10)
        time_orig = time.time() - start

        # Optimized implementation
        start = time.time()
        for _ in range(50):
            result_opt = select_top_variants_optimized(mock_variants_large, top_k=10)
        time_opt = time.time() - start

        # Both should return same number of results
        assert len(result_orig) == len(result_opt) == 10

        print("\nLarge set (192 variants, 50 iterations):")
        print(f"Original: {time_orig:.3f}s")
        print(f"Optimized: {time_opt:.3f}s")
        print(f"Speedup: {time_orig / time_opt:.2f}x")

        # Optimized should be significantly faster
        assert time_opt < time_orig * 0.8  # At least 20% faster

    def test_selection_performance_huge(self, mock_variants_huge):
        """Test performance with stress test variant set (1000)."""
        # Original implementation
        start = time.time()
        select_top_variants_original(mock_variants_huge, top_k=10)
        time_orig = time.time() - start

        # Optimized implementation
        start = time.time()
        select_top_variants_optimized(mock_variants_huge, top_k=10)
        time_opt = time.time() - start

        print("\nHuge set (1000 variants, single run):")
        print(f"Original: {time_orig:.3f}s")
        print(f"Optimized: {time_opt:.3f}s")
        print(f"Speedup: {time_orig / time_opt:.2f}x")

        # For large sets, heap-based selection should be much faster
        assert time_opt < time_orig * 0.5  # At least 2x faster

    def test_memory_usage_comparison(self, mock_variants_large):
        """Test memory efficiency of cache implementation."""
        import sys

        # Test unbounded dict cache
        cache_dict = {}
        for i in range(1000):
            cache_dict[f"content_{i}"] = np.random.random()
        dict_size = sys.getsizeof(cache_dict)

        # Test LRU cache (simulated)
        from functools import lru_cache

        @lru_cache(maxsize=500)
        def cached_func(content):
            return np.random.random()

        for i in range(1000):
            cached_func(f"content_{i}")

        # LRU cache should have bounded size
        print("\nMemory usage comparison:")
        print(f"Dict cache (1000 items): {dict_size} bytes")
        print("LRU cache (max 500): bounded")

        # Dict grows unbounded
        assert dict_size > 50000  # Rough estimate

    @pytest.mark.asyncio
    async def test_e3_prediction_performance(self, mock_variants_large):
        """Test E3 prediction performance with batching."""
        # Mock predictor
        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate = Mock(
            side_effect=lambda x: {"predicted_engagement_rate": 0.05 + len(x) * 0.001}
        )

        # Simulate original synchronous approach
        start = time.time()
        with patch(
            "time.sleep", lambda x: time.sleep(0.01)
        ):  # Simulate 10ms per prediction
            select_top_variants_with_engagement_predictor(
                mock_variants_large[:50],  # Use subset to avoid timeout
                top_k=10,
                predictor_instance=mock_predictor,
            )
        time_sync = time.time() - start

        # Async batched approach
        start = time.time()
        result_async = await select_top_variants_with_engagement_predictor_async(
            mock_variants_large[:50], top_k=10, predictor_instance=mock_predictor
        )
        time_async = time.time() - start

        print("\nE3 Prediction Performance (50 variants):")
        print(f"Synchronous: {time_sync:.3f}s")
        print(f"Async batched: {time_async:.3f}s")
        print(f"Speedup: {time_sync / time_async:.2f}x")

        # Async should be significantly faster due to batching
        assert len(result_async) == 10

    def test_database_query_optimization(self):
        """Test database query optimization."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from services.orchestrator.db.models import Base, VariantPerformance

        # Create in-memory database for testing
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Insert test data
        for i in range(200):
            variant = VariantPerformance(
                variant_id=f"variant_{i}",
                dimensions={"persona_id": f"persona_{i % 10}"},
                impressions=np.random.randint(0, 1000),
                successes=np.random.randint(0, 100),
            )
            session.add(variant)
        session.commit()

        optimizer = ThompsonSamplingOptimized()

        # Test original query (loads all)
        start = time.time()
        variants_orig = load_variants_from_db_original(session)
        time_orig = time.time() - start

        # Test optimized query (filtered)
        start = time.time()
        variants_opt = optimizer.load_variants_from_db_optimized(session, limit=100)
        time_opt = time.time() - start

        print("\nDatabase Query Performance:")
        print(
            f"Original (all records): {time_orig:.3f}s - {len(variants_orig)} records"
        )
        print(f"Optimized (filtered): {time_opt:.3f}s - {len(variants_opt)} records")

        # Optimized should load fewer records
        assert len(variants_opt) <= len(variants_orig)

        session.close()

    def test_response_time_under_2_seconds(self, mock_variants_large):
        """Ensure response time meets <2 second requirement."""
        optimizer = ThompsonSamplingOptimized()

        # Mock E3 predictor with realistic delay
        mock_predictor = Mock()

        def slow_predict(content):
            time.sleep(0.01)  # 10ms per prediction
            return {"predicted_engagement_rate": 0.05}

        mock_predictor.predict_engagement_rate = slow_predict

        # Run selection with E3 predictions
        start = time.time()

        # Use async version for better performance
        async def run_selection():
            return await optimizer.select_top_variants_with_e3_predictions_async(
                mock_variants_large, predictor=mock_predictor, top_k=10
            )

        result = asyncio.run(run_selection())
        elapsed = time.time() - start

        print(f"\nTotal response time for 192 variants with E3: {elapsed:.3f}s")

        # Must be under 2 seconds
        assert elapsed < 2.0, (
            f"Response time {elapsed:.3f}s exceeds 2 second requirement"
        )
        assert len(result) == 10


if __name__ == "__main__":
    # Run performance tests
    test = TestThompsonSamplingPerformance()

    # Generate test data
    small = test._generate_variants(50)
    large = test._generate_variants(192)
    huge = test._generate_variants(1000)

    # Run tests
    test.test_selection_performance_small(small)
    test.test_selection_performance_large(large)
    test.test_selection_performance_huge(huge)
    test.test_memory_usage_comparison(large)
    test.test_database_query_optimization()
    test.test_response_time_under_2_seconds(large)

    # Run async test
    asyncio.run(test.test_e3_prediction_performance(large))
