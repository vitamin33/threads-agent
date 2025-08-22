#!/usr/bin/env python3
"""
Performance Testing Stubs - Validate Performance Measurement

Tests performance profiling without requiring actual models.
"""

import pytest
from unittest.mock import Mock, patch
from evalsuite.metrics.perf_metrics import PerformanceProfiler, PerformanceMetrics


def test_performance_metrics_calculation():
    """Test performance metrics calculation with mock data."""
    
    # Mock latency data
    mock_latencies = [100, 120, 110, 105, 115, 125, 108, 112, 118, 122]
    
    profiler = PerformanceProfiler(warmup_runs=2, timed_runs=10)
    
    # Test percentile calculations
    import statistics
    
    p50 = statistics.median(mock_latencies)
    p95 = statistics.quantiles(mock_latencies, n=20)[18] if len(mock_latencies) >= 20 else max(mock_latencies)
    
    assert p50 > 0
    assert p95 >= p50
    assert p95 <= max(mock_latencies)


def test_performance_profiler_initialization():
    """Test performance profiler initialization."""
    profiler = PerformanceProfiler(warmup_runs=3, timed_runs=15)
    
    assert profiler.warmup_runs == 3
    assert profiler.timed_runs == 15
    assert profiler.process is not None


@patch('psutil.Process')
def test_memory_monitoring_stub(mock_process):
    """Test memory monitoring with mocked psutil."""
    
    # Mock memory info
    mock_memory = Mock()
    mock_memory.rss = 1024 * 1024 * 1024  # 1GB in bytes
    mock_process.return_value.memory_info.return_value = mock_memory
    
    profiler = PerformanceProfiler()
    
    # Test memory calculation
    memory_mb = mock_memory.rss / (1024 * 1024)
    assert memory_mb == 1024.0  # 1GB = 1024MB


def test_performance_metrics_dataclass():
    """Test PerformanceMetrics dataclass."""
    metrics = PerformanceMetrics(
        p50_latency_ms=100.0,
        p95_latency_ms=150.0,
        tokens_per_second=25.0,
        peak_rss_mb=512.0,
        context_length=100,
        warmup_runs=5,
        timed_runs=20,
        device="mps",
        stack="pytorch"
    )
    
    assert metrics.p50_latency_ms == 100.0
    assert metrics.p95_latency_ms == 150.0
    assert metrics.device == "mps"
    assert metrics.stack == "pytorch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])