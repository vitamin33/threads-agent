"""
Advanced test suite for PerformanceRegressionDetector - comprehensive edge cases and statistical scenarios.

This suite focuses on:
- Statistical edge cases and boundary conditions
- Advanced statistical scenarios and distributions
- Performance requirements and scalability
- Failure injection and error resilience
- Real-world data patterns and anomalies
- Memory and computational efficiency

Author: Test Generation Specialist for CRA-297
"""

import pytest
import numpy as np
import time
import gc
import psutil
from scipy import stats
from unittest.mock import Mock, patch
from typing import List, Dict, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.common.performance_regression_detector import (
    PerformanceRegressionDetector,
    PerformanceData,
    RegressionResult,
    RegressionError,
    MetricType,
    SignificanceLevel,
    StatisticalTest
)


class TestPerformanceRegressionDetectorStatisticalEdgeCases:
    """Test statistical edge cases and boundary conditions."""

    def test_extreme_variance_differences(self):
        """Test handling of extreme variance differences between datasets."""
        detector = PerformanceRegressionDetector()
        
        # High variance historical data
        high_variance_historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.5 + np.random.normal(0, 0.3),  # Very high variance
                metadata={}
            )
            for i in range(1, 31)
        ]
        
        # Low variance current data
        low_variance_current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.8 + np.random.normal(0, 0.001),  # Very low variance
                metadata={}
            )
            for _ in range(15)
        ]
        
        result = detector.detect_regression(
            historical_data=high_variance_historical,
            current_data=low_variance_current,
            metric_name="accuracy"
        )
        
        # Should handle extreme variance differences gracefully
        assert result is not None
        assert isinstance(result.p_value, float)
        assert 0 <= result.p_value <= 1
        assert result.effect_size is not None

    def test_non_normal_distributions(self):
        """Test handling of non-normal data distributions."""
        detector = PerformanceRegressionDetector(
            statistical_tests=[
                StatisticalTest.MANN_WHITNEY,  # Non-parametric test
                StatisticalTest.KOLMOGOROV_SMIRNOV
            ]
        )
        
        # Generate bimodal distribution (clearly non-normal)
        np.random.seed(42)
        bimodal_values = np.concatenate([
            np.random.normal(0.3, 0.05, 15),  # First mode
            np.random.normal(0.7, 0.05, 15)   # Second mode
        ])
        
        historical_bimodal = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=float(val),
                metadata={}
            )
            for i, val in enumerate(bimodal_values)
        ]
        
        # Uniform distribution current data
        uniform_values = np.random.uniform(0.45, 0.55, 20)
        current_uniform = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=float(val),
                metadata={}
            )
            for val in uniform_values
        ]
        
        result = detector.detect_regression(
            historical_data=historical_bimodal,
            current_data=current_uniform,
            metric_name="accuracy"
        )
        
        # Non-parametric tests should handle non-normal data
        assert result is not None
        assert "mann_whitney" in result.test_results
        assert "kolmogorov_smirnov" in result.test_results

    def test_extreme_outliers_impact(self):
        """Test impact of extreme outliers on regression detection."""
        detector_with_outliers = PerformanceRegressionDetector(filter_outliers=False)
        detector_without_outliers = PerformanceRegressionDetector(filter_outliers=True)
        
        # Create data with extreme outliers
        normal_values = [0.85] * 20
        outlier_values = [0.85] * 18 + [0.1, 1.9]  # Extreme outliers
        
        historical_normal = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=val,
                metadata={}
            )
            for i, val in enumerate(normal_values)
        ]
        
        historical_outliers = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=val,
                metadata={}
            )
            for i, val in enumerate(outlier_values)
        ]
        
        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.83,  # Slight change
                metadata={}
            )
            for _ in range(15)
        ]
        
        # Compare results with and without outliers
        result_with_outliers = detector_with_outliers.detect_regression(
            historical_data=historical_outliers,
            current_data=current_data,
            metric_name="accuracy"
        )
        
        result_without_outliers = detector_without_outliers.detect_regression(
            historical_data=historical_outliers,
            current_data=current_data,
            metric_name="accuracy"
        )
        
        # Outlier filtering should affect results
        assert result_without_outliers.outliers_filtered > 0
        assert result_with_outliers.outliers_filtered == 0
        
        # Statistical significance may differ
        # (can't guarantee direction, but should be different)
        assert result_with_outliers.p_value != result_without_outliers.p_value

    def test_temporal_patterns_and_trends(self):
        """Test detection in presence of temporal trends."""
        detector = PerformanceRegressionDetector()
        
        # Create trending historical data (improving over time)
        trending_historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=30-i),
                metric_name="accuracy",
                value=0.70 + (i * 0.01) + np.random.normal(0, 0.02),  # Upward trend
                metadata={}
            )
            for i in range(30)
        ]
        
        # Current data continues the trend
        current_trending = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=1.0 + np.random.normal(0, 0.02),  # Continues upward
                metadata={}
            )
            for _ in range(15)
        ]
        
        result = detector.detect_regression(
            historical_data=trending_historical,
            current_data=current_trending,
            metric_name="accuracy"
        )
        
        # Should not detect regression if trend continues positively
        assert result.is_regression is False
        assert result.effect_size > 0  # Positive effect (improvement)

    def test_seasonal_patterns_handling(self):
        """Test handling of seasonal or cyclical patterns in data."""
        detector = PerformanceRegressionDetector(baseline_window_days=14)
        
        # Create cyclical pattern (e.g., weekly performance cycles)
        cyclical_data = []
        for day in range(60):  # 60 days of data
            # Weekly cycle: higher performance on weekdays, lower on weekends
            day_of_week = day % 7
            base_performance = 0.85 if day_of_week < 5 else 0.75  # Weekday vs weekend
            
            cyclical_data.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(days=60-day),
                    metric_name="accuracy",
                    value=base_performance + np.random.normal(0, 0.05),
                    metadata={"day_of_week": day_of_week}
                )
            )
        
        # Current data follows the same pattern
        current_day_of_week = 2  # Wednesday (good performance day)
        current_cyclical = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.05),
                metadata={"day_of_week": current_day_of_week}
            )
            for _ in range(10)
        ]
        
        result = detector.detect_regression(
            historical_data=cyclical_data,
            current_data=current_cyclical,
            metric_name="accuracy"
        )
        
        # Should not detect regression for normal cyclical pattern
        assert result.is_regression is False

    def test_multiple_changepoints_in_data(self):
        """Test handling of data with multiple changepoints."""
        detector = PerformanceRegressionDetector()
        
        # Create data with multiple performance regime changes
        changepoint_data = []
        
        # Regime 1: Days 1-10 (good performance)
        for i in range(10):
            changepoint_data.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(days=30-i),
                    metric_name="accuracy",
                    value=0.90 + np.random.normal(0, 0.02),
                    metadata={"regime": 1}
                )
            )
        
        # Regime 2: Days 11-20 (poor performance)
        for i in range(10, 20):
            changepoint_data.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(days=30-i),
                    metric_name="accuracy",
                    value=0.70 + np.random.normal(0, 0.02),
                    metadata={"regime": 2}
                )
            )
        
        # Regime 3: Days 21-30 (recovered performance)
        for i in range(20, 30):
            changepoint_data.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(days=30-i),
                    metric_name="accuracy",
                    value=0.88 + np.random.normal(0, 0.02),
                    metadata={"regime": 3}
                )
            )
        
        # Current data similar to recent regime
        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.87 + np.random.normal(0, 0.02),
                metadata={}
            )
            for _ in range(15)
        ]
        
        result = detector.detect_regression(
            historical_data=changepoint_data,
            current_data=current_data,
            metric_name="accuracy"
        )
        
        # Should use recent baseline for comparison
        assert abs(result.baseline_mean - 0.88) < 0.05  # Should be close to regime 3


class TestPerformanceRegressionDetectorScalabilityAndPerformance:
    """Test scalability and performance characteristics."""

    def test_large_dataset_processing_efficiency(self):
        """Test processing efficiency with large datasets."""
        detector = PerformanceRegressionDetector()
        
        # Generate large datasets
        large_historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=i),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.02),
                metadata={}
            )
            for i in range(10000)  # 10k data points
        ]
        
        large_current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.83 + np.random.normal(0, 0.02),
                metadata={}
            )
            for _ in range(1000)  # 1k data points
        ]
        
        # Measure processing time
        start_time = time.time()
        result = detector.detect_regression(
            historical_data=large_historical,
            current_data=large_current,
            metric_name="accuracy"
        )
        processing_time = time.time() - start_time
        
        # Performance requirements
        assert result is not None
        assert processing_time < 10.0  # Should process large datasets quickly
        assert result.is_regression is True  # Should detect the regression

    def test_memory_efficiency_with_large_datasets(self):
        """Test memory efficiency when processing large datasets."""
        detector = PerformanceRegressionDetector()
        process = psutil.Process()
        
        # Record initial memory
        initial_memory = process.memory_info().rss
        
        # Process multiple large datasets
        for dataset_size in [1000, 5000, 10000]:
            historical_data = [
                PerformanceData(
                    timestamp=datetime.now() - timedelta(hours=i),
                    metric_name="accuracy",
                    value=0.85 + np.random.normal(0, 0.02),
                    metadata={}
                )
                for i in range(dataset_size)
            ]
            
            current_data = [
                PerformanceData(
                    timestamp=datetime.now(),
                    metric_name="accuracy",
                    value=0.83 + np.random.normal(0, 0.02),
                    metadata={}
                )
                for _ in range(dataset_size // 10)
            ]
            
            result = detector.detect_regression(
                historical_data=historical_data,
                current_data=current_data,
                metric_name="accuracy"
            )
            
            assert result is not None
            
            # Force cleanup
            del historical_data, current_data, result
            gc.collect()
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase excessively
        assert memory_increase < 200 * 1024 * 1024  # Less than 200MB increase

    def test_concurrent_regression_detection(self):
        """Test concurrent execution of regression detection."""
        detector = PerformanceRegressionDetector()
        
        def run_regression_detection(thread_id: int) -> RegressionResult:
            np.random.seed(thread_id)  # Different seed per thread
            
            historical_data = [
                PerformanceData(
                    timestamp=datetime.now() - timedelta(hours=i),
                    metric_name="accuracy",
                    value=0.85 + np.random.normal(0, 0.02),
                    metadata={"thread_id": thread_id}
                )
                for i in range(100)
            ]
            
            current_data = [
                PerformanceData(
                    timestamp=datetime.now(),
                    metric_name="accuracy",
                    value=0.83 + np.random.normal(0, 0.02),
                    metadata={"thread_id": thread_id}
                )
                for _ in range(50)
            ]
            
            return detector.detect_regression(
                historical_data=historical_data,
                current_data=current_data,
                metric_name="accuracy"
            )
        
        # Run concurrent regression detections
        num_threads = 10
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(run_regression_detection, i)
                for i in range(num_threads)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        # Verify all completed successfully
        assert len(results) == num_threads
        assert all(isinstance(result, RegressionResult) for result in results)
        assert all(result.is_regression is True for result in results)  # Should detect regression

    def test_statistical_test_performance_comparison(self):
        """Test and compare performance of different statistical tests."""
        test_configurations = [
            [StatisticalTest.T_TEST],
            [StatisticalTest.MANN_WHITNEY],
            [StatisticalTest.WELCH_T_TEST],
            [StatisticalTest.KOLMOGOROV_SMIRNOV],
            [StatisticalTest.T_TEST, StatisticalTest.MANN_WHITNEY],  # Multiple tests
        ]
        
        # Generate test data once
        historical_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=i),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.02),
                metadata={}
            )
            for i in range(1000)
        ]
        
        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.83 + np.random.normal(0, 0.02),
                metadata={}
            )
            for _ in range(500)
        ]
        
        performance_results = {}
        
        for tests in test_configurations:
            detector = PerformanceRegressionDetector(statistical_tests=tests)
            
            # Measure execution time
            start_time = time.time()
            result = detector.detect_regression(
                historical_data=historical_data,
                current_data=current_data,
                metric_name="accuracy"
            )
            execution_time = time.time() - start_time
            
            test_names = "_".join([test.value for test in tests])
            performance_results[test_names] = {
                "execution_time": execution_time,
                "result": result
            }
        
        # Verify all tests complete within reasonable time
        for test_name, perf_data in performance_results.items():
            assert perf_data["execution_time"] < 5.0, f"{test_name} took too long: {perf_data['execution_time']}s"
            assert perf_data["result"] is not None


class TestPerformanceRegressionDetectorFailureInjection:
    """Test failure injection and error resilience."""

    def test_corrupted_data_handling(self):
        """Test handling of corrupted or malformed data."""
        detector = PerformanceRegressionDetector()
        
        # Create data with various corruption patterns
        corrupted_historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=1),
                metric_name="accuracy",
                value=float('inf'),  # Infinite value
                metadata={}
            ),
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=2),
                metric_name="accuracy",
                value=float('-inf'),  # Negative infinite value
                metadata={}
            ),
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=3),
                metric_name="accuracy",
                value=float('nan'),  # NaN value
                metadata={}
            ),
        ]
        
        # Fill with some normal data
        for i in range(4, 25):
            corrupted_historical.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(hours=i),
                    metric_name="accuracy",
                    value=0.85 + np.random.normal(0, 0.02),
                    metadata={}
                )
            )
        
        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.83 + np.random.normal(0, 0.02),
                metadata={}
            )
            for _ in range(15)
        ]
        
        # Should handle corrupted data gracefully
        result = detector.detect_regression(
            historical_data=corrupted_historical,
            current_data=current_data,
            metric_name="accuracy"
        )
        
        assert result is not None
        # NaN/inf values should be filtered out or handled
        assert not np.isnan(result.baseline_mean)
        assert not np.isinf(result.baseline_mean)

    def test_statistical_test_failures(self):
        """Test handling of statistical test failures."""
        # Mock detector with failing statistical tests
        detector = PerformanceRegressionDetector()
        
        # Create problematic data that might cause statistical test failures
        problematic_historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=i),
                metric_name="accuracy",
                value=0.85,  # All identical values (zero variance)
                metadata={}
            )
            for i in range(20)
        ]
        
        problematic_current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.85,  # All identical values (zero variance)
                metadata={}
            )
            for _ in range(15)
        ]
        
        # Should handle zero variance gracefully
        result = detector.detect_regression(
            historical_data=problematic_historical,
            current_data=problematic_current,
            metric_name="accuracy"
        )
        
        assert result is not None
        assert result.baseline_std == 0.0
        assert result.current_std == 0.0
        assert not result.is_regression  # No difference between identical distributions

    def test_memory_pressure_handling(self):
        """Test behavior under memory pressure conditions."""
        detector = PerformanceRegressionDetector()
        
        # Try to create memory pressure
        large_arrays = []
        try:
            # Allocate large arrays to create memory pressure
            for _ in range(10):
                large_arrays.append(np.random.random(10000000))  # 10M floats each
            
            # Now try regression detection under memory pressure
            historical_data = [
                PerformanceData(
                    timestamp=datetime.now() - timedelta(hours=i),
                    metric_name="accuracy",
                    value=0.85 + np.random.normal(0, 0.02),
                    metadata={}
                )
                for i in range(100)
            ]
            
            current_data = [
                PerformanceData(
                    timestamp=datetime.now(),
                    metric_name="accuracy",
                    value=0.83 + np.random.normal(0, 0.02),
                    metadata={}
                )
                for _ in range(50)
            ]
            
            result = detector.detect_regression(
                historical_data=historical_data,
                current_data=current_data,
                metric_name="accuracy"
            )
            
            assert result is not None
            
        except MemoryError:
            # If we actually run out of memory, that's expected in this test
            pytest.skip("Not enough memory to create pressure for testing")
        finally:
            # Clean up large arrays
            del large_arrays
            gc.collect()

    def test_infinite_loop_protection(self):
        """Test protection against infinite loops in statistical computations."""
        detector = PerformanceRegressionDetector()
        
        # Create data that might cause numerical issues
        problematic_values = [1e-100] * 10 + [1e100] * 10  # Extreme values
        
        historical_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=i),
                metric_name="accuracy",
                value=val,
                metadata={}
            )
            for i, val in enumerate(problematic_values)
        ]
        
        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=1e50,  # Another extreme value
                metadata={}
            )
            for _ in range(15)
        ]
        
        # Set timeout to detect if computation hangs
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Regression detection took too long")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
        
        try:
            result = detector.detect_regression(
                historical_data=historical_data,
                current_data=current_data,
                metric_name="accuracy"
            )
            assert result is not None
        except TimeoutError:
            pytest.fail("Regression detection timed out - possible infinite loop")
        finally:
            signal.alarm(0)  # Cancel alarm


class TestPerformanceRegressionDetectorRealWorldScenarios:
    """Test real-world scenarios and use cases."""

    def test_microservice_performance_monitoring(self):
        """Test scenario: monitoring microservice performance metrics."""
        detector = PerformanceRegressionDetector(
            significance_level=SignificanceLevel.ALPHA_05,
            minimum_samples=5,  # Lower threshold for microservices
            baseline_window_days=7  # Shorter window for fast-moving services
        )
        
        # Simulate microservice latency data (realistic patterns)
        business_hours_multiplier = lambda hour: 1.5 if 9 <= hour <= 17 else 1.0
        
        historical_latencies = []
        for day in range(14):  # 2 weeks of data
            for hour in range(24):
                base_latency = 50.0 * business_hours_multiplier(hour)
                actual_latency = base_latency + np.random.exponential(10)  # Exponential tail
                
                historical_latencies.append(
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(days=14-day, hours=24-hour),
                        metric_name="response_latency_ms",
                        value=actual_latency,
                        metadata={
                            "service": "user-service",
                            "hour": hour,
                            "is_business_hours": 9 <= hour <= 17
                        }
                    )
                )
        
        # Current data shows performance regression during business hours
        current_latencies = []
        for hour in range(9, 18):  # Business hours only
            degraded_latency = 120.0 + np.random.exponential(20)  # Much higher latency
            current_latencies.append(
                PerformanceData(
                    timestamp=datetime.now(),
                    metric_name="response_latency_ms",
                    value=degraded_latency,
                    metadata={
                        "service": "user-service",
                        "hour": hour,
                        "is_business_hours": True
                    }
                )
            )
        
        result = detector.detect_regression(
            historical_data=historical_latencies,
            current_data=current_latencies,
            metric_name="response_latency_ms",
            metric_type=MetricType.LOWER_IS_BETTER
        )
        
        # Should detect regression in latency
        assert result.is_regression is True
        assert result.effect_size > 0  # Positive effect for latency increase
        assert result.p_value < 0.05

    def test_ml_model_accuracy_monitoring(self):
        """Test scenario: monitoring ML model accuracy degradation."""
        detector = PerformanceRegressionDetector(
            significance_level=SignificanceLevel.ALPHA_01,  # Stricter threshold for ML
            statistical_tests=[
                StatisticalTest.T_TEST,
                StatisticalTest.MANN_WHITNEY,  # Non-parametric backup
                StatisticalTest.KOLMOGOROV_SMIRNOV  # Distribution change detection
            ]
        )
        
        # Simulate model accuracy over time with data drift
        historical_accuracies = []
        
        # Early period: stable high accuracy
        for week in range(4):
            for day in range(7):
                accuracy = 0.94 + np.random.normal(0, 0.01)  # 94% ± 1%
                historical_accuracies.append(
                    PerformanceData(
                        timestamp=datetime.now() - timedelta(weeks=4-week, days=7-day),
                        metric_name="model_accuracy",
                        value=max(0, min(1, accuracy)),  # Clamp to [0,1]
                        metadata={
                            "model_version": "v1.0",
                            "dataset": "production",
                            "week": week
                        }
                    )
                )
        
        # Current period: accuracy degradation due to data drift
        current_accuracies = []
        for day in range(7):  # Last week
            # Gradual degradation
            degraded_accuracy = 0.88 - (day * 0.005) + np.random.normal(0, 0.015)
            current_accuracies.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(days=7-day),
                    metric_name="model_accuracy",
                    value=max(0, min(1, degraded_accuracy)),
                    metadata={
                        "model_version": "v1.0",
                        "dataset": "production",
                        "drift_detected": True
                    }
                )
            )
        
        result = detector.detect_regression(
            historical_data=historical_accuracies,
            current_data=current_accuracies,
            metric_name="model_accuracy",
            metric_type=MetricType.HIGHER_IS_BETTER
        )
        
        # Should detect significant accuracy regression
        assert result.is_regression is True
        assert result.effect_size < 0  # Negative effect for accuracy decrease
        assert result.p_value < 0.01  # Highly significant
        assert result.consensus_score > 0.6  # Multiple tests should agree

    def test_batch_processing_throughput_monitoring(self):
        """Test scenario: monitoring batch processing throughput."""
        detector = PerformanceRegressionDetector(
            filter_outliers=True,  # Remove processing anomalies
            outlier_threshold=2.5
        )
        
        # Simulate batch processing throughput (jobs per hour)
        historical_throughput = []
        
        # Normal operation with some variation
        for hour in range(24 * 7):  # 1 week of hourly data
            # Night hours typically have higher throughput (less competition)
            hour_of_day = hour % 24
            base_throughput = 1000 if 22 <= hour_of_day or hour_of_day <= 6 else 800
            
            # Add some outliers for maintenance windows
            if np.random.random() < 0.05:  # 5% chance of maintenance
                actual_throughput = base_throughput * 0.3  # Reduced throughput
            else:
                actual_throughput = base_throughput + np.random.normal(0, 50)
            
            historical_throughput.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(hours=24*7-hour),
                    metric_name="jobs_per_hour",
                    value=max(0, actual_throughput),
                    metadata={
                        "hour_of_day": hour_of_day,
                        "shift": "night" if 22 <= hour_of_day or hour_of_day <= 6 else "day"
                    }
                )
            )
        
        # Current data shows consistent throughput degradation
        current_throughput = []
        for hour in range(24):  # Last 24 hours
            hour_of_day = hour
            base_throughput = 1000 if 22 <= hour_of_day or hour_of_day <= 6 else 800
            
            # Consistent degradation (possible infrastructure issue)
            degraded_throughput = base_throughput * 0.7 + np.random.normal(0, 30)
            
            current_throughput.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(hours=24-hour),
                    metric_name="jobs_per_hour",
                    value=max(0, degraded_throughput),
                    metadata={
                        "hour_of_day": hour_of_day,
                        "shift": "night" if 22 <= hour_of_day or hour_of_day <= 6 else "day"
                    }
                )
            )
        
        result = detector.detect_regression(
            historical_data=historical_throughput,
            current_data=current_throughput,
            metric_name="jobs_per_hour",
            metric_type=MetricType.HIGHER_IS_BETTER
        )
        
        # Should detect throughput regression
        assert result.is_regression is True
        assert result.effect_size < 0  # Negative effect for throughput decrease
        assert result.outliers_filtered > 0  # Should filter maintenance outliers

    def test_database_query_performance_monitoring(self):
        """Test scenario: monitoring database query performance."""
        detector = PerformanceRegressionDetector(
            statistical_tests=[StatisticalTest.MANN_WHITNEY],  # Good for latency data
            baseline_window_days=3  # Short window for DB monitoring
        )
        
        # Simulate database query latencies (log-normal distribution is typical)
        historical_query_times = []
        
        for hour in range(72):  # 3 days of hourly data
            # Base query time varies by time of day (more load during business hours)
            hour_of_day = hour % 24
            load_factor = 2.0 if 9 <= hour_of_day <= 17 else 1.0
            
            # Log-normal distribution for query times
            base_time = 10.0 * load_factor  # Base time in ms
            query_time = np.random.lognormal(np.log(base_time), 0.5)
            
            historical_query_times.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(hours=72-hour),
                    metric_name="avg_query_time_ms",
                    value=query_time,
                    metadata={
                        "hour": hour_of_day,
                        "load_factor": load_factor,
                        "query_type": "SELECT"
                    }
                )
            )
        
        # Current data shows query performance degradation (e.g., missing index)
        current_query_times = []
        for minute in range(60):  # Last hour of minute-by-minute data
            # Significantly slower queries
            degraded_time = np.random.lognormal(np.log(50.0), 0.3)  # Much slower
            
            current_query_times.append(
                PerformanceData(
                    timestamp=datetime.now() - timedelta(minutes=60-minute),
                    metric_name="avg_query_time_ms",
                    value=degraded_time,
                    metadata={
                        "minute": minute,
                        "query_type": "SELECT",
                        "possible_issue": "missing_index"
                    }
                )
            )
        
        result = detector.detect_regression(
            historical_data=historical_query_times,
            current_data=current_query_times,
            metric_name="avg_query_time_ms",
            metric_type=MetricType.LOWER_IS_BETTER
        )
        
        # Should detect query performance regression
        assert result.is_regression is True
        assert result.effect_size > 0  # Positive effect for latency increase
        assert result.p_value < 0.05


@pytest.mark.performance
class TestPerformanceRegressionDetectorPerformanceRequirements:
    """Test specific performance requirements and SLAs."""

    def test_real_time_detection_latency(self):
        """Test real-time detection latency requirements."""
        detector = PerformanceRegressionDetector()
        
        # Simulate real-time monitoring scenario
        historical_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(hours=i),
                metric_name="response_time",
                value=100 + np.random.normal(0, 10),
                metadata={}
            )
            for i in range(100)  # Recent 100 hours
        ]
        
        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="response_time",
                value=150 + np.random.normal(0, 10),  # Clear regression
                metadata={}
            )
            for _ in range(10)  # Last 10 measurements
        ]
        
        # Measure detection latency
        latencies = []
        for _ in range(20):  # Multiple runs for average
            start_time = time.time()
            result = detector.detect_regression(
                historical_data=historical_data,
                current_data=current_data,
                metric_name="response_time",
                metric_type=MetricType.LOWER_IS_BETTER
            )
            detection_latency = time.time() - start_time
            latencies.append(detection_latency)
            
            assert result.is_regression is True
        
        # Real-time requirements
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        assert avg_latency < 1.0   # Average under 1 second
        assert max_latency < 2.0   # Maximum under 2 seconds

    def test_high_frequency_monitoring_performance(self):
        """Test performance under high-frequency monitoring scenarios."""
        detector = PerformanceRegressionDetector(minimum_samples=5)
        
        # Generate streaming data
        def generate_data_point(timestamp, is_degraded=False):
            base_value = 0.85 if not is_degraded else 0.75
            return PerformanceData(
                timestamp=timestamp,
                metric_name="accuracy",
                value=base_value + np.random.normal(0, 0.02),
                metadata={}
            )
        
        # Initial historical data
        historical_data = [
            generate_data_point(datetime.now() - timedelta(minutes=i))
            for i in range(60, 0, -1)  # Last 60 minutes
        ]
        
        # Simulate high-frequency monitoring (every 10 seconds)
        total_detections = 0
        total_time = 0
        
        for second in range(0, 300, 10):  # 5 minutes of monitoring, every 10 seconds
            current_timestamp = datetime.now() + timedelta(seconds=second)
            
            # Add new data point
            new_point = generate_data_point(current_timestamp, is_degraded=(second > 120))
            current_data = [new_point]
            
            # Perform regression detection
            start_time = time.time()
            result = detector.detect_regression(
                historical_data=historical_data[-30:],  # Use recent 30 minutes
                current_data=current_data,
                metric_name="accuracy"
            )
            detection_time = time.time() - start_time
            
            total_detections += 1
            total_time += detection_time
            
            # Update historical data (sliding window)
            historical_data.append(new_point)
            if len(historical_data) > 100:
                historical_data.pop(0)
        
        # High-frequency monitoring requirements
        avg_detection_time = total_time / total_detections
        assert avg_detection_time < 0.1  # Under 100ms per detection
        assert total_detections == 30     # Should complete all detections


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])