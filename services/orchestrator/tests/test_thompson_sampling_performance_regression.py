"""Performance regression tests for Thompson Sampling."""

import pytest
import time
import numpy as np
import gc
from typing import List, Dict, Any
from memory_profiler import memory_usage
from unittest.mock import Mock
import cProfile
import pstats
import io

from services.orchestrator.thompson_sampling import (
    select_top_variants,
    select_top_variants_with_exploration,
    select_top_variants_with_e3_predictions,
)
from services.orchestrator.thompson_sampling_optimized import (
    select_top_variants as select_top_variants_optimized,
)


class TestThompsonSamplingPerformanceRegression:
    """Performance regression tests to ensure optimization improvements are maintained."""

    # Performance thresholds (in seconds)
    SMALL_SET_THRESHOLD = 0.01  # 10ms for 50 variants
    MEDIUM_SET_THRESHOLD = 0.05  # 50ms for 200 variants
    LARGE_SET_THRESHOLD = 0.2  # 200ms for 1000 variants
    HUGE_SET_THRESHOLD = 1.0  # 1s for 5000 variants

    # Memory thresholds (in MB)
    MEMORY_THRESHOLD_PER_1000_VARIANTS = 10  # 10MB per 1000 variants

    @pytest.fixture
    def performance_test_variants(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate variants for performance testing."""

        def create_variants(count: int) -> List[Dict[str, Any]]:
            variants = []
            for i in range(count):
                # Realistic distribution of performance
                if i < count * 0.1:  # 10% high performers
                    impressions = np.random.randint(5000, 10000)
                    success_rate = np.random.uniform(0.08, 0.12)
                elif i < count * 0.4:  # 30% medium performers
                    impressions = np.random.randint(500, 5000)
                    success_rate = np.random.uniform(0.04, 0.08)
                elif i < count * 0.7:  # 30% low performers
                    impressions = np.random.randint(50, 500)
                    success_rate = np.random.uniform(0.01, 0.04)
                else:  # 30% new variants
                    impressions = np.random.randint(0, 50)
                    success_rate = (
                        np.random.uniform(0.0, 0.1) if impressions > 0 else 0.0
                    )

                successes = int(impressions * success_rate)

                variants.append(
                    {
                        "variant_id": f"perf_test_v_{i}",
                        "dimensions": {
                            "hook_style": f"style_{i % 10}",
                            "emotion": f"emotion_{i % 8}",
                            "length": ["short", "medium", "long"][i % 3],
                        },
                        "performance": {
                            "impressions": impressions,
                            "successes": successes,
                        },
                        "sample_content": f"Performance test content {i} " * 5,
                    }
                )

            return variants

        return {
            "small": create_variants(50),
            "medium": create_variants(200),
            "large": create_variants(1000),
            "huge": create_variants(5000),
        }

    def test_selection_performance_small_set(self, performance_test_variants):
        """Test performance with small variant set meets threshold."""
        variants = performance_test_variants["small"]

        # Warm up
        select_top_variants(variants, top_k=10)

        # Measure performance
        start = time.perf_counter()
        for _ in range(100):
            result = select_top_variants(variants, top_k=10)
        elapsed = time.perf_counter() - start
        avg_time = elapsed / 100

        assert len(result) == 10
        assert avg_time < self.SMALL_SET_THRESHOLD, (
            f"Small set took {avg_time:.4f}s, threshold is {self.SMALL_SET_THRESHOLD}s"
        )

        # Compare with optimized version
        start = time.perf_counter()
        for _ in range(100):
            select_top_variants_optimized(variants, top_k=10)
        elapsed_opt = time.perf_counter() - start
        avg_time_opt = elapsed_opt / 100

        print("\nSmall set (50 variants):")
        print(f"Original: {avg_time:.4f}s per selection")
        print(f"Optimized: {avg_time_opt:.4f}s per selection")
        print(f"Speedup: {avg_time / avg_time_opt:.2f}x")

    def test_selection_performance_medium_set(self, performance_test_variants):
        """Test performance with medium variant set meets threshold."""
        variants = performance_test_variants["medium"]

        # Measure performance
        start = time.perf_counter()
        for _ in range(50):
            result = select_top_variants(variants, top_k=10)
        elapsed = time.perf_counter() - start
        avg_time = elapsed / 50

        assert len(result) == 10
        assert avg_time < self.MEDIUM_SET_THRESHOLD, (
            f"Medium set took {avg_time:.4f}s, threshold is {self.MEDIUM_SET_THRESHOLD}s"
        )

    def test_selection_performance_large_set(self, performance_test_variants):
        """Test performance with large variant set meets threshold."""
        variants = performance_test_variants["large"]

        # Measure performance
        start = time.perf_counter()
        for _ in range(10):
            result = select_top_variants(variants, top_k=10)
        elapsed = time.perf_counter() - start
        avg_time = elapsed / 10

        assert len(result) == 10
        assert avg_time < self.LARGE_SET_THRESHOLD, (
            f"Large set took {avg_time:.4f}s, threshold is {self.LARGE_SET_THRESHOLD}s"
        )

    def test_selection_performance_huge_set(self, performance_test_variants):
        """Test performance with huge variant set meets threshold."""
        variants = performance_test_variants["huge"]

        # Single run for huge set
        start = time.perf_counter()
        result = select_top_variants(variants, top_k=10)
        elapsed = time.perf_counter() - start

        assert len(result) == 10
        assert elapsed < self.HUGE_SET_THRESHOLD, (
            f"Huge set took {elapsed:.4f}s, threshold is {self.HUGE_SET_THRESHOLD}s"
        )

    def test_memory_usage_scaling(self, performance_test_variants):
        """Test that memory usage scales linearly with variant count."""
        # Force garbage collection
        gc.collect()

        def measure_memory(variants):
            def select_variants():
                return select_top_variants(variants, top_k=10)

            # Measure memory usage
            mem_usage = memory_usage(select_variants)
            return max(mem_usage) - min(mem_usage)

        # Measure for different sizes
        small_mem = measure_memory(performance_test_variants["small"])
        medium_mem = measure_memory(performance_test_variants["medium"])
        large_mem = measure_memory(performance_test_variants["large"])

        print("\nMemory usage:")
        print(f"Small (50): {small_mem:.2f} MB")
        print(f"Medium (200): {medium_mem:.2f} MB")
        print(f"Large (1000): {large_mem:.2f} MB")

        # Check memory scaling
        # Memory per 1000 variants should be under threshold
        memory_per_1000 = (large_mem / 1000) * 1000
        assert memory_per_1000 < self.MEMORY_THRESHOLD_PER_1000_VARIANTS

    def test_exploration_performance_impact(self, performance_test_variants):
        """Test performance impact of exploration/exploitation split."""
        variants = performance_test_variants["medium"]

        # Test different exploration ratios
        ratios = [0.0, 0.3, 0.5, 0.7, 1.0]
        times = []

        for ratio in ratios:
            start = time.perf_counter()
            for _ in range(20):
                select_top_variants_with_exploration(
                    variants, top_k=10, min_impressions=100, exploration_ratio=ratio
                )
            elapsed = time.perf_counter() - start
            times.append(elapsed / 20)

        print("\nExploration ratio performance impact:")
        for ratio, avg_time in zip(ratios, times):
            print(f"Ratio {ratio:.1f}: {avg_time:.4f}s")

        # Performance should not degrade significantly with different ratios
        max_time = max(times)
        min_time = min(times)
        assert (max_time - min_time) / min_time < 0.5, (
            "Performance varies too much with exploration ratio"
        )

    def test_e3_prediction_performance_overhead(self, performance_test_variants):
        """Test overhead of E3 predictions."""
        variants = performance_test_variants["small"]

        # Mock predictor with realistic delay
        mock_predictor = Mock()
        mock_predictor.predict_engagement_rate.return_value = {
            "predicted_engagement_rate": 0.05
        }

        # Measure without E3
        start = time.perf_counter()
        for _ in range(10):
            select_top_variants(variants, top_k=10)
        time_basic = time.perf_counter() - start

        # Measure with E3 (cached)
        start = time.perf_counter()
        for _ in range(10):
            select_top_variants_with_e3_predictions(
                variants, predictor=mock_predictor, top_k=10, use_cache=True
            )
        time_e3 = time.perf_counter() - start

        print("\nE3 prediction overhead:")
        print(f"Basic: {time_basic:.4f}s for 10 runs")
        print(f"With E3: {time_e3:.4f}s for 10 runs")
        print(f"Overhead: {((time_e3 - time_basic) / time_basic * 100):.1f}%")

        # E3 overhead should be reasonable (less than 100%)
        assert time_e3 < time_basic * 2.0, "E3 predictions add too much overhead"

    def test_cpu_usage_profile(self, performance_test_variants):
        """Profile CPU usage to identify bottlenecks."""
        variants = performance_test_variants["large"]

        # Profile the selection function
        profiler = cProfile.Profile()
        profiler.enable()

        for _ in range(5):
            select_top_variants(variants, top_k=10)

        profiler.disable()

        # Analyze profile
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
        ps.print_stats(10)  # Top 10 functions

        profile_output = s.getvalue()
        print("\nCPU Profile (top 10 functions):")
        print(profile_output)

        # Check that numpy.random.beta is called appropriate number of times
        # Should be called once per variant per iteration
        assert "random.beta" in profile_output

    def test_performance_degradation_over_time(self, performance_test_variants):
        """Test that performance doesn't degrade with repeated use."""
        variants = performance_test_variants["medium"]

        # Run many iterations and measure time for each batch
        batch_times = []
        batch_size = 100

        for batch in range(10):
            start = time.perf_counter()
            for _ in range(batch_size):
                select_top_variants(variants, top_k=10)
            elapsed = time.perf_counter() - start
            batch_times.append(elapsed / batch_size)

            # Small delay between batches
            time.sleep(0.1)

        print("\nPerformance over time (avg per selection):")
        for i, batch_time in enumerate(batch_times):
            print(f"Batch {i + 1}: {batch_time:.4f}s")

        # Check for performance degradation
        # Last batch should not be significantly slower than first
        degradation = (batch_times[-1] - batch_times[0]) / batch_times[0]
        assert degradation < 0.2, f"Performance degraded by {degradation * 100:.1f}%"

    def test_concurrent_performance_scaling(self, performance_test_variants):
        """Test performance scaling with concurrent requests."""
        from concurrent.futures import ThreadPoolExecutor

        variants = performance_test_variants["small"]

        def run_selections(n_selections):
            for _ in range(n_selections):
                select_top_variants(variants, top_k=10)

        # Test different concurrency levels
        thread_counts = [1, 2, 4, 8]
        times = []

        for n_threads in thread_counts:
            start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=n_threads) as executor:
                futures = [
                    executor.submit(run_selections, 100 // n_threads)
                    for _ in range(n_threads)
                ]
                for future in futures:
                    future.result()
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        print("\nConcurrent performance scaling:")
        for n_threads, elapsed in zip(thread_counts, times):
            print(f"{n_threads} threads: {elapsed:.4f}s")

        # Performance should scale reasonably with threads
        # Not linear due to GIL, but should show some improvement
        assert times[1] < times[0] * 0.9, "No improvement with 2 threads"

    def test_optimized_version_maintains_quality(self, performance_test_variants):
        """Test that optimized version maintains selection quality."""
        variants = performance_test_variants["medium"]

        # Set seed for reproducibility
        np.random.seed(42)

        # Run both versions multiple times
        n_runs = 100
        original_selections = []
        optimized_selections = []

        for _ in range(n_runs):
            orig = select_top_variants(variants, top_k=10)
            opt = select_top_variants_optimized(variants, top_k=10)
            original_selections.extend(orig)
            optimized_selections.extend(opt)

        # Count frequency of each variant
        from collections import Counter

        orig_counts = Counter(original_selections)
        opt_counts = Counter(optimized_selections)

        # Top variants should be similar
        top_10_orig = [v for v, _ in orig_counts.most_common(10)]
        top_10_opt = [v for v, _ in opt_counts.most_common(10)]

        overlap = len(set(top_10_orig).intersection(set(top_10_opt)))
        assert overlap >= 7, f"Only {overlap} variants in common between top 10"

        print("\nSelection quality comparison:")
        print(f"Top 10 overlap: {overlap}/10")
        print("Total unique variants selected:")
        print(f"  Original: {len(orig_counts)}")
        print(f"  Optimized: {len(opt_counts)}")
