"""
Performance Impact Testing for M1 Telemetry System
Measures overhead of telemetry decorators vs undecorated functions
"""

import time
import statistics
import sys
from pathlib import Path

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import telemetry_decorator


def measure_function_overhead():
    """Measure telemetry decorator overhead"""
    print("🔄 Measuring telemetry overhead...")

    # Undecorated function
    def plain_function(x, y):
        return x * y + x + y

    # Decorated function
    @telemetry_decorator(agent_name="perf_test")
    def decorated_function(x, y):
        return x * y + x + y

    # Warm up both functions
    for _ in range(100):
        plain_function(42, 17)
        decorated_function(42, 17)

    # Measure plain function performance
    plain_times = []
    for _ in range(1000):
        start = time.perf_counter()
        result = plain_function(42, 17)
        end = time.perf_counter()
        plain_times.append(end - start)

    # Measure decorated function performance
    decorated_times = []
    for _ in range(1000):
        start = time.perf_counter()
        decorated_function(42, 17)  # Don't store unused result
        end = time.perf_counter()
        decorated_times.append(end - start)

    # Calculate statistics
    plain_mean = statistics.mean(plain_times) * 1_000_000  # Convert to microseconds
    plain_stdev = statistics.stdev(plain_times) * 1_000_000

    decorated_mean = statistics.mean(decorated_times) * 1_000_000
    decorated_stdev = statistics.stdev(decorated_times) * 1_000_000

    overhead = decorated_mean - plain_mean
    overhead_percent = (overhead / plain_mean) * 100 if plain_mean > 0 else 0

    print("📊 Performance Results:")
    print(f"  Plain function:     {plain_mean:.2f}μs ± {plain_stdev:.2f}μs")
    print(f"  Decorated function: {decorated_mean:.2f}μs ± {decorated_stdev:.2f}μs")
    print(f"  Overhead:           {overhead:.2f}μs ({overhead_percent:.1f}%)")

    # Overhead should be reasonable (< 1000μs = 1ms)
    assert overhead < 1000, f"Excessive overhead: {overhead:.2f}μs"

    return {
        "plain_mean_us": plain_mean,
        "decorated_mean_us": decorated_mean,
        "overhead_us": overhead,
        "overhead_percent": overhead_percent,
    }


def measure_database_write_performance():
    """Measure database write performance"""
    print("🔄 Measuring database write performance...")

    @telemetry_decorator(agent_name="db_perf_test")
    def db_test_function(i):
        return f"iteration_{i}"

    # Measure time for batch of database writes
    batch_sizes = [1, 10, 100, 500]
    results = {}

    for batch_size in batch_sizes:
        start_time = time.time()

        for i in range(batch_size):
            db_test_function(i)

        total_time = time.time() - start_time
        time_per_call = (total_time / batch_size) * 1000  # Convert to ms

        results[batch_size] = {
            "total_time_s": total_time,
            "time_per_call_ms": time_per_call,
            "calls_per_second": batch_size / total_time if total_time > 0 else 0,
        }

        print(
            f"  Batch size {batch_size:3d}: {time_per_call:.3f}ms/call, {results[batch_size]['calls_per_second']:.1f} calls/s"
        )

    return results


def measure_metrics_calculation_performance():
    """Measure metrics calculation performance with different data sizes"""
    print("🔄 Measuring metrics calculation performance...")

    from ops.telemetry import get_daily_metrics

    # Test metrics calculation time
    times = []
    for _ in range(10):
        start = time.time()
        get_daily_metrics(1)  # 1 day - don't store unused result
        end = time.time()
        times.append(end - start)

    mean_time = statistics.mean(times) * 1000  # Convert to ms

    print(f"  Metrics calculation: {mean_time:.3f}ms average")

    # Should be fast (< 100ms for reasonable data sizes)
    assert mean_time < 100, f"Metrics calculation too slow: {mean_time:.3f}ms"

    return mean_time


def run_performance_tests():
    """Run all performance tests"""
    print("🚀 Starting M1 Telemetry Performance Tests")
    print("=" * 60)

    results = {}

    try:
        print("\n1. Function Call Overhead")
        results["overhead"] = measure_function_overhead()

        print("\n2. Database Write Performance")
        results["database"] = measure_database_write_performance()

        print("\n3. Metrics Calculation Performance")
        results["metrics"] = measure_metrics_calculation_performance()

        print(f"\n{'=' * 60}")
        print("📊 Performance Summary:")
        print(
            f"  Function overhead:    {results['overhead']['overhead_us']:.2f}μs ({results['overhead']['overhead_percent']:.1f}%)"
        )
        print(
            f"  DB writes (per call): {results['database'][100]['time_per_call_ms']:.3f}ms"
        )
        print(f"  Metrics calculation:  {results['metrics']:.3f}ms")

        # Overall assessment
        total_overhead_us = results["overhead"]["overhead_us"]
        if total_overhead_us < 100:
            performance_rating = "Excellent"
        elif total_overhead_us < 500:
            performance_rating = "Good"
        elif total_overhead_us < 1000:
            performance_rating = "Acceptable"
        else:
            performance_rating = "Poor"

        print(f"  Overall rating:       {performance_rating}")
        print(f"{'=' * 60}")

        return True

    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)
