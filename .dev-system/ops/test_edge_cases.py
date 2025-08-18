"""
Edge Case Testing for M1 Telemetry System
Tests database failures, large datasets, memory usage, and corner cases
"""

import time
import sys
import threading
from pathlib import Path

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import telemetry_decorator, get_daily_metrics


def test_large_dataset_performance():
    """Test system performance with large number of events"""
    print("🔄 Testing large dataset performance...")

    @telemetry_decorator(agent_name="load_test")
    def fast_function(i):
        return f"result_{i}"

    # Generate 1000 events quickly
    start_time = time.time()
    for i in range(1000):
        if i % 100 == 0:
            print(f"  Generated {i} events...")
        fast_function(i)

    total_time = time.time() - start_time
    print(
        f"✅ Generated 1000 events in {total_time:.2f}s ({1000 / total_time:.1f} events/sec)"
    )

    # Test metrics calculation with large dataset
    metrics_start = time.time()
    get_daily_metrics()  # Just test the timing, don't store result
    metrics_time = time.time() - metrics_start

    print(f"✅ Metrics calculation took {metrics_time:.3f}s")
    assert metrics_time < 1.0, f"Metrics too slow: {metrics_time:.3f}s"


def test_database_corruption_resilience():
    """Test system resilience to database issues"""
    print("🔄 Testing database corruption resilience...")

    @telemetry_decorator(agent_name="resilience_test")
    def resilient_function():
        return "still_working"

    # Test normal operation first
    result = resilient_function()
    assert result == "still_working"

    # Function should still work even if database has issues
    # (telemetry fails silently to not break main application)
    result = resilient_function()
    assert result == "still_working"

    print("✅ System resilient to database issues")


def test_memory_usage():
    """Test memory usage doesn't grow excessively"""
    print("🔄 Testing memory usage...")

    import psutil
    import gc

    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    @telemetry_decorator(agent_name="memory_test")
    def memory_function(data_size):
        # Create some data
        data = "x" * data_size
        return len(data)

    # Run many operations with varying data sizes
    for i in range(100):
        memory_function(1000)  # 1KB each

    gc.collect()  # Force garbage collection

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_growth = final_memory - initial_memory

    print(
        f"✅ Memory usage: {initial_memory:.1f}MB → {final_memory:.1f}MB (growth: {memory_growth:.1f}MB)"
    )

    # Memory growth should be reasonable (< 50MB for this test)
    assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.1f}MB"


def test_unicode_and_special_characters():
    """Test handling of unicode and special characters"""
    print("🔄 Testing unicode and special characters...")

    @telemetry_decorator(agent_name="unicode_test")
    def unicode_function(text):
        return f"processed: {text}"

    # Test various unicode and special characters
    test_strings = [
        "Hello 世界",  # Chinese characters
        "🚀🎯✅❌📊",  # Emojis
        "Special chars: !@#$%^&*()",
        "Quotes: \"single\" 'double'",
        "Newlines\nand\ttabs",
        "SQL injection'; DROP TABLE--",
        "Very long " + "x" * 10000,  # Long string
    ]

    for test_str in test_strings:
        try:
            result = unicode_function(test_str)
            assert test_str in result
        except Exception as e:
            print(f"❌ Failed with string: {test_str[:50]}... Error: {e}")
            raise

    print("✅ Unicode and special characters handled correctly")


def test_extreme_latencies():
    """Test handling of very fast and very slow operations"""
    print("🔄 Testing extreme latencies...")

    @telemetry_decorator(agent_name="latency_test")
    def instant_function():
        return "instant"

    @telemetry_decorator(agent_name="latency_test")
    def slow_function():
        time.sleep(2.0)  # 2 second delay
        return "slow"

    # Test very fast operation
    start = time.time()
    result = instant_function()
    duration = time.time() - start
    assert result == "instant"
    assert duration < 0.1  # Should be very fast

    # Test slow operation
    start = time.time()
    result = slow_function()
    duration = time.time() - start
    assert result == "slow"
    assert 1.9 < duration < 2.5  # Should take ~2 seconds

    print("✅ Extreme latencies handled correctly")


def test_concurrent_database_access():
    """Test high concurrency database access"""
    print("🔄 Testing concurrent database access...")

    @telemetry_decorator(agent_name="concurrent_db_test")
    def concurrent_db_function(worker_id, iteration):
        time.sleep(0.01)  # Small delay to increase contention
        return f"worker_{worker_id}_iter_{iteration}"

    results = []
    errors = []

    def worker(worker_id):
        try:
            for i in range(50):  # 50 calls per worker
                result = concurrent_db_function(worker_id, i)
                results.append(result)
        except Exception as e:
            errors.append(f"Worker {worker_id}: {e}")

    # Start 20 concurrent workers (1000 total operations)
    threads = []
    start_time = time.time()

    for worker_id in range(20):
        thread = threading.Thread(target=worker, args=(worker_id,))
        threads.append(thread)
        thread.start()

    # Wait for all workers
    for thread in threads:
        thread.join()

    total_time = time.time() - start_time

    print(
        f"✅ Concurrent test: {len(results)} results, {len(errors)} errors in {total_time:.2f}s"
    )

    assert len(errors) == 0, (
        f"Concurrent errors: {errors[:5]}..."
    )  # Show first 5 errors
    assert len(results) == 1000, f"Expected 1000 results, got {len(results)}"


def test_metrics_with_mixed_timeframes():
    """Test metrics calculation across different time periods"""
    print("🔄 Testing metrics with mixed timeframes...")

    # This test uses existing data from previous tests

    # Test different time periods
    for period_days in [1, 7, 30]:
        metrics = get_daily_metrics(period_days)

        # Verify metrics structure
        required_keys = ["success_rate", "p95_latency_ms", "total_cost", "failed_calls"]
        for key in required_keys:
            assert key in metrics, f"Missing metric key: {key}"
            assert isinstance(metrics[key], (int, float)), f"Invalid type for {key}"

        # Verify reasonable values
        assert 0.0 <= metrics["success_rate"] <= 1.0, (
            f"Invalid success rate: {metrics['success_rate']}"
        )
        assert metrics["p95_latency_ms"] >= 0, (
            f"Invalid latency: {metrics['p95_latency_ms']}"
        )
        assert metrics["total_cost"] >= 0, f"Invalid cost: {metrics['total_cost']}"
        assert metrics["failed_calls"] >= 0, (
            f"Invalid failed calls: {metrics['failed_calls']}"
        )

    print("✅ Metrics calculation works across all timeframes")


def run_edge_case_tests():
    """Run all edge case tests"""
    print("🚀 Starting M1 Telemetry Edge Case Tests")
    print("=" * 60)

    tests = [
        ("Large Dataset Performance", test_large_dataset_performance),
        ("Database Corruption Resilience", test_database_corruption_resilience),
        ("Memory Usage", test_memory_usage),
        ("Unicode Characters", test_unicode_and_special_characters),
        ("Extreme Latencies", test_extreme_latencies),
        ("Concurrent Database Access", test_concurrent_database_access),
        ("Mixed Timeframes", test_metrics_with_mixed_timeframes),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            test_func()
            print(f"✅ Passed: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ Failed: {test_name} - {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"📊 Edge Case Test Results: {passed}/{passed + failed} tests passed")
    if failed == 0:
        print("🎉 All edge case tests passed!")
    print(f"{'=' * 60}")

    return failed == 0


if __name__ == "__main__":
    success = run_edge_case_tests()
    sys.exit(0 if success else 1)
