"""Concurrent access and thread safety tests for Thompson Sampling."""

import pytest
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import time
import numpy as np
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from services.orchestrator.db import Base
from services.orchestrator.db.models import VariantPerformance
from services.orchestrator.thompson_sampling import (
    select_top_variants,
    update_variant_performance,
    select_top_variants_with_e3_predictions,
    _e3_cache,
)
from services.orchestrator.thompson_sampling_optimized import (
    ThompsonSamplingOptimized,
    select_top_variants_with_engagement_predictor_async,
)


class TestThompsonSamplingConcurrent:
    """Test concurrent access scenarios for Thompson Sampling."""

    @pytest.fixture
    def db_engine(self):
        """Create a test database engine with connection pooling."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},  # Allow multi-threaded access
            pool_size=10,
            max_overflow=20,
        )
        Base.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def session_factory(self, db_engine):
        """Create a thread-safe session factory."""
        return scoped_session(sessionmaker(bind=db_engine))

    @pytest.fixture
    def test_variants(self) -> List[Dict[str, Any]]:
        """Generate test variants for concurrent access."""
        return [
            {
                "variant_id": f"v_{i}",
                "dimensions": {"hook_style": f"style_{i % 5}"},
                "performance": {
                    "impressions": np.random.randint(0, 1000),
                    "successes": np.random.randint(0, 100),
                },
                "sample_content": f"Content for variant {i}",
            }
            for i in range(100)
        ]

    def test_concurrent_variant_selection(self, test_variants):
        """Test concurrent selection doesn't cause race conditions."""
        results = []
        errors = []

        def select_variants():
            try:
                selected = select_top_variants(test_variants, top_k=10)
                results.append(selected)
            except Exception as e:
                errors.append(e)

        # Run concurrent selections
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=select_variants)
            thread.start()
            threads.append(thread)

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Assert
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 20
        # All results should have 10 variants
        assert all(len(r) == 10 for r in results)

    def test_concurrent_database_updates(self, session_factory):
        """Test concurrent database updates don't cause conflicts."""
        # Create initial variants
        session = session_factory()
        for i in range(10):
            variant = VariantPerformance(
                variant_id=f"concurrent_v_{i}",
                dimensions={"hook_style": "question"},
                impressions=0,
                successes=0,
            )
            session.add(variant)
        session.commit()
        session.close()

        errors = []

        def update_variant(variant_id: str, thread_id: int):
            session = session_factory()
            try:
                # Simulate multiple updates
                for _ in range(10):
                    update_variant_performance(
                        session,
                        variant_id,
                        impression=True,
                        success=(thread_id % 2 == 0),  # Even threads report success
                    )
                    time.sleep(0.001)  # Small delay to increase contention
            except Exception as e:
                errors.append((variant_id, thread_id, str(e)))
            finally:
                session.close()

        # Run concurrent updates
        threads = []
        for i in range(5):
            for j in range(10):
                thread = threading.Thread(
                    target=update_variant, args=(f"concurrent_v_{j}", i)
                )
                thread.start()
                threads.append(thread)

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Check final state
        session = session_factory()
        variants = session.query(VariantPerformance).all()
        for variant in variants:
            # Each variant should have 50 impressions (5 threads × 10 updates)
            assert variant.impressions == 50
            # Even threads (0, 2, 4) report success: 3 threads × 10 = 30
            assert variant.successes == 30
        session.close()

    def test_e3_cache_thread_safety(self):
        """Test E3 cache is thread-safe under concurrent access."""
        mock_predictor = Mock()
        call_count = 0
        call_lock = threading.Lock()

        def predict_side_effect(content):
            nonlocal call_count
            with call_lock:
                call_count += 1
            time.sleep(0.01)  # Simulate API delay
            return {"predicted_engagement_rate": 0.05 + len(content) * 0.001}

        mock_predictor.predict_engagement_rate.side_effect = predict_side_effect

        # Clear cache
        _e3_cache.clear()

        # Create variants with same content (to test cache)
        variants = [
            {
                "variant_id": f"cache_test_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": "shared content for caching",  # Same content
            }
            for i in range(50)
        ]

        results = []

        def select_with_e3():
            selected = select_top_variants_with_e3_predictions(
                variants[:10],  # Use subset
                predictor=mock_predictor,
                top_k=5,
                use_cache=True,
            )
            results.append(selected)

        # Run concurrent selections
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=select_with_e3)
            thread.start()
            threads.append(thread)

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Assert
        assert len(results) == 10
        # Cache should prevent multiple calls for same content
        assert call_count < 10, (
            f"Expected fewer than 10 calls due to caching, got {call_count}"
        )

    @pytest.mark.asyncio
    async def test_async_e3_predictions_concurrent(self):
        """Test async E3 predictions handle concurrent requests properly."""
        ThompsonSamplingOptimized()
        mock_predictor = Mock()

        call_times = []
        call_lock = asyncio.Lock()

        async def async_predict(content):
            async with call_lock:
                call_times.append(time.time())
            await asyncio.sleep(0.05)  # Simulate API delay
            return {"predicted_engagement_rate": 0.05}

        mock_predictor.predict_engagement_rate = Mock(
            side_effect=lambda x: async_predict(x)
        )

        # Create many variants
        variants = [
            {
                "variant_id": f"async_v_{i}",
                "dimensions": {"hook_style": f"style_{i % 5}"},
                "performance": {"impressions": 0, "successes": 0},
                "sample_content": f"Content {i}",
            }
            for i in range(50)
        ]

        # Run multiple async selections concurrently
        tasks = []
        for i in range(5):
            task = select_top_variants_with_engagement_predictor_async(
                variants[i * 10 : (i + 1) * 10],  # Different subsets
                top_k=5,
                predictor_instance=mock_predictor,
            )
            tasks.append(task)

        # Wait for all tasks
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Assert
        assert len(results) == 5
        assert all(len(r) == 5 for r in results)

        # Should complete faster than sequential (5 × 50ms = 250ms)
        assert end_time - start_time < 0.2, (
            "Async execution should be faster than sequential"
        )

    def test_race_condition_in_exploration_selection(self):
        """Test for race conditions in exploration/exploitation split."""
        # Create variants that will cause contention
        experienced_variants = [
            {
                "variant_id": f"exp_{i}",
                "dimensions": {"hook_style": "question"},
                "performance": {"impressions": 200, "successes": 100},
            }
            for i in range(10)
        ]

        new_variants = [
            {
                "variant_id": f"new_{i}",
                "dimensions": {"hook_style": "statement"},
                "performance": {"impressions": 5, "successes": 1},
            }
            for i in range(10)
        ]

        all_variants = experienced_variants + new_variants

        results = []

        def select_with_exploration():
            from services.orchestrator.thompson_sampling import (
                select_top_variants_with_exploration,
            )

            selected = select_top_variants_with_exploration(
                all_variants, top_k=10, min_impressions=100, exploration_ratio=0.5
            )
            results.append(selected)

        # Run many times concurrently
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(select_with_exploration) for _ in range(100)]
            for future in futures:
                future.result()

        # Verify all selections are valid
        assert len(results) == 100
        for result in results:
            assert len(result) == 10
            # Check no duplicates
            assert len(set(result)) == 10

    def test_memory_consistency_under_load(self, test_variants):
        """Test memory consistency when cache is under heavy load."""
        optimizer = ThompsonSamplingOptimized(cache_size=50)  # Small cache

        # Generate many unique contents to stress cache
        variants_with_unique_content = []
        for i in range(200):
            variant = test_variants[i % len(test_variants)].copy()
            variant["variant_id"] = f"memory_test_{i}"
            variant["sample_content"] = f"Unique content {i} " * 10  # Larger content
            variants_with_unique_content.append(variant)

        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate.return_value = {
            "predicted_engagement_rate": 0.05
        }

        results = []
        memory_errors = []

        def stress_cache():
            try:
                # Each thread processes many variants
                for i in range(10):
                    subset = variants_with_unique_content[i * 20 : (i + 1) * 20]
                    selected = optimizer.select_top_variants(subset, top_k=5)
                    results.append(selected)
            except MemoryError as e:
                memory_errors.append(e)

        # Run concurrent stress test
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=stress_cache)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        # Assert no memory errors
        assert len(memory_errors) == 0
        assert len(results) > 0

    def test_database_connection_pool_exhaustion(self, db_engine):
        """Test behavior when database connection pool is exhausted."""
        # Create session with very small pool
        small_pool_engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            pool_size=2,
            max_overflow=0,
            pool_timeout=1,  # 1 second timeout
        )
        Base.metadata.create_all(small_pool_engine)
        SessionFactory = scoped_session(sessionmaker(bind=small_pool_engine))

        # Create test data
        session = SessionFactory()
        for i in range(10):
            variant = VariantPerformance(
                variant_id=f"pool_test_{i}",
                dimensions={"hook_style": "question"},
                impressions=100,
                successes=50,
            )
            session.add(variant)
        session.commit()
        session.close()

        timeouts = []
        successes = []

        def long_running_query(thread_id):
            session = SessionFactory()
            try:
                # Hold connection for a while
                session.query(VariantPerformance).all()
                time.sleep(0.5)  # Simulate slow operation
                successes.append(thread_id)
            except Exception as e:
                if "timeout" in str(e).lower():
                    timeouts.append(thread_id)
            finally:
                session.close()

        # Start many threads to exhaust pool
        threads = []
        for i in range(10):
            thread = threading.Thread(target=long_running_query, args=(i,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        # Some threads should timeout due to pool exhaustion
        assert len(timeouts) > 0, "Expected some timeouts due to pool exhaustion"
        assert len(successes) >= 2, "At least pool_size threads should succeed"

    def test_concurrent_optimized_vs_original(self, test_variants):
        """Test that optimized version produces similar results under concurrent load."""
        from services.orchestrator.thompson_sampling_optimized import (
            select_top_variants as select_optimized,
        )

        # Set seed for reproducibility
        np.random.seed(42)

        original_results = []
        optimized_results = []

        def run_original():
            for _ in range(10):
                result = select_top_variants(test_variants[:50], top_k=10)
                original_results.append(set(result))

        def run_optimized():
            for _ in range(10):
                result = select_optimized(test_variants[:50], top_k=10)
                optimized_results.append(set(result))

        # Run both concurrently
        t1 = threading.Thread(target=run_original)
        t2 = threading.Thread(target=run_optimized)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Both should produce valid results
        assert len(original_results) == 10
        assert len(optimized_results) == 10

        # Results should be similar (not identical due to randomness)
        # But should have significant overlap
        for orig, opt in zip(original_results, optimized_results):
            overlap = len(orig.intersection(opt))
            assert overlap >= 5, "Results should have significant overlap"
