"""
Test file for PerformanceRegressionDetector - statistical analysis for detecting performance drops.

This follows strict TDD practices for CRA-297 CI/CD Pipeline implementation.
The PerformanceRegressionDetector should provide statistical analysis capabilities
to detect significant performance regressions in prompt templates during CI/CD deployment.

Author: TDD Implementation for CRA-297
"""

import pytest
import numpy as np
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

# These imports should now succeed after implementation
from services.common.performance_regression_detector import (
    PerformanceRegressionDetector,
    RegressionResult,
    StatisticalTest,
    PerformanceData,
    RegressionError,
    MetricType,
    SignificanceLevel,
)


@dataclass
class MockPerformanceData:
    """Mock performance data for testing."""

    timestamp: datetime
    metric_name: str
    value: float
    metadata: Dict[str, Any]


class TestPerformanceRegressionDetectorBasics:
    """Test basic PerformanceRegressionDetector functionality."""

    @pytest.fixture
    def sample_historical_data(self):
        """Sample historical performance data."""
        np.random.seed(123)  # Set seed for reproducible test data
        base_time = datetime.now() - timedelta(days=30)
        return [
            PerformanceData(
                timestamp=base_time + timedelta(days=i),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.02),  # 85% ± 2% accuracy
                metadata={"model_version": f"1.{i}.0", "test_set": "validation"},
            )
            for i in range(30)
        ]

    @pytest.fixture
    def sample_current_data(self):
        """Sample current performance data."""
        np.random.seed(456)  # Different seed for current data
        return [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.82 + np.random.normal(0, 0.01),  # 82% accuracy (regression!)
                metadata={"model_version": "2.0.0", "test_set": "validation"},
            )
            for _ in range(10)
        ]

    def test_performance_regression_detector_initialization(self):
        """Test PerformanceRegressionDetector can be initialized with default parameters."""
        # This will fail - we haven't implemented PerformanceRegressionDetector yet
        detector = PerformanceRegressionDetector()

        assert detector.significance_level == SignificanceLevel.ALPHA_05
        assert detector.statistical_tests == [
            StatisticalTest.T_TEST,
            StatisticalTest.MANN_WHITNEY,
        ]
        assert detector.minimum_samples == 10

    def test_performance_regression_detector_with_custom_config(self):
        """Test initialization with custom configuration."""
        detector = PerformanceRegressionDetector(
            significance_level=SignificanceLevel.ALPHA_01,
            statistical_tests=[StatisticalTest.T_TEST],
            minimum_samples=5,
            baseline_window_days=14,
        )

        assert detector.significance_level == SignificanceLevel.ALPHA_01
        assert detector.statistical_tests == [StatisticalTest.T_TEST]
        assert detector.minimum_samples == 5
        assert detector.baseline_window_days == 14

    def test_detect_regression_with_significant_drop(
        self, sample_historical_data, sample_current_data
    ):
        """Test detecting significant performance regression."""
        detector = PerformanceRegressionDetector()

        result = detector.detect_regression(
            historical_data=sample_historical_data,
            current_data=sample_current_data,
            metric_name="accuracy",
        )

        assert isinstance(result, RegressionResult)
        assert result.metric_name == "accuracy"
        assert result.is_regression is True
        assert result.confidence_level >= 0.95
        assert result.effect_size < 0  # Negative effect size indicates performance drop
        assert result.p_value < 0.05

    def test_detect_regression_with_no_significant_change(self):
        """Test no regression detected when performance is stable."""
        # Set random seed for deterministic test
        np.random.seed(42)

        # Create stable performance data
        base_time = datetime.now() - timedelta(days=30)
        stable_historical = [
            PerformanceData(
                timestamp=base_time + timedelta(days=i),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.005),  # Very stable 85%
                metadata={"model_version": f"1.{i}.0"},
            )
            for i in range(30)
        ]

        stable_current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.005),  # Same stable 85%
                metadata={"model_version": "2.0.0"},
            )
            for _ in range(10)
        ]

        detector = PerformanceRegressionDetector()
        result = detector.detect_regression(
            historical_data=stable_historical,
            current_data=stable_current,
            metric_name="accuracy",
        )

        assert result.is_regression is False
        assert result.p_value > 0.05
        assert (
            abs(result.effect_size) < 0.15
        )  # Small effect size (allowing for some randomness)


class TestPerformanceRegressionDetectorStatisticalTests:
    """Test different statistical test implementations."""

    @pytest.fixture
    def regression_detector(self):
        """Create detector with all statistical tests."""
        return PerformanceRegressionDetector(
            statistical_tests=[
                StatisticalTest.T_TEST,
                StatisticalTest.MANN_WHITNEY,
                StatisticalTest.WELCH_T_TEST,
                StatisticalTest.KOLMOGOROV_SMIRNOV,
            ]
        )

    @pytest.fixture
    def clear_regression_data(self):
        """Create data with clear regression pattern."""
        historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="latency",
                value=100 + np.random.normal(0, 5),  # 100ms ± 5ms
                metadata={"test": "historical"},
            )
            for i in range(1, 31)
        ]

        current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="latency",
                value=150 + np.random.normal(0, 5),  # 150ms ± 5ms (50% increase!)
                metadata={"test": "current"},
            )
            for _ in range(15)
        ]

        return historical, current

    def test_t_test_detects_regression(
        self, regression_detector, clear_regression_data
    ):
        """Test T-test correctly detects regression."""
        historical, current = clear_regression_data

        result = regression_detector.detect_regression(
            historical_data=historical,
            current_data=current,
            metric_name="latency",
            metric_type=MetricType.LOWER_IS_BETTER,
        )

        assert result.is_regression is True
        assert "t_test" in result.test_results
        assert result.test_results["t_test"]["p_value"] < 0.01

    def test_mann_whitney_detects_regression(
        self, regression_detector, clear_regression_data
    ):
        """Test Mann-Whitney U test correctly detects regression."""
        historical, current = clear_regression_data

        result = regression_detector.detect_regression(
            historical_data=historical,
            current_data=current,
            metric_name="latency",
            metric_type=MetricType.LOWER_IS_BETTER,
        )

        assert result.is_regression is True
        assert "mann_whitney" in result.test_results
        assert result.test_results["mann_whitney"]["p_value"] < 0.01

    def test_welch_t_test_handles_unequal_variances(self, regression_detector):
        """Test Welch's T-test handles data with unequal variances."""
        # Historical data with low variance
        historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.9 + np.random.normal(0, 0.01),
                metadata={},
            )
            for i in range(1, 21)
        ]

        # Current data with high variance and lower mean
        current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.05),
                metadata={},
            )
            for _ in range(10)
        ]

        result = regression_detector.detect_regression(
            historical_data=historical, current_data=current, metric_name="accuracy"
        )

        assert "welch_t_test" in result.test_results
        assert result.test_results["welch_t_test"]["p_value"] is not None

    def test_multiple_tests_consensus(self, regression_detector, clear_regression_data):
        """Test that multiple statistical tests reach consensus on clear regression."""
        historical, current = clear_regression_data

        result = regression_detector.detect_regression(
            historical_data=historical,
            current_data=current,
            metric_name="latency",
            metric_type=MetricType.LOWER_IS_BETTER,
        )

        # All tests should agree on regression
        significant_tests = [
            test
            for test, details in result.test_results.items()
            if details["p_value"] < 0.05
        ]

        assert len(significant_tests) >= 2  # At least 2 tests agree
        assert result.consensus_score > 0.5  # Majority consensus


class TestPerformanceRegressionDetectorMetricTypes:
    """Test handling of different metric types (higher/lower is better)."""

    def test_accuracy_metric_regression_detection(self):
        """Test regression detection for accuracy metric (higher is better)."""
        detector = PerformanceRegressionDetector()

        # High historical accuracy
        historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.92 + np.random.normal(0, 0.01),
                metadata={},
            )
            for i in range(1, 21)
        ]

        # Lower current accuracy
        current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.88 + np.random.normal(0, 0.01),
                metadata={},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical,
            current_data=current,
            metric_name="accuracy",
            metric_type=MetricType.HIGHER_IS_BETTER,
        )

        assert result.is_regression is True
        assert result.effect_size < 0  # Negative because performance dropped

    def test_latency_metric_regression_detection(self):
        """Test regression detection for latency metric (lower is better)."""
        detector = PerformanceRegressionDetector()

        # Low historical latency
        historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="latency",
                value=50 + np.random.normal(0, 5),
                metadata={},
            )
            for i in range(1, 21)
        ]

        # Higher current latency
        current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="latency",
                value=80 + np.random.normal(0, 5),
                metadata={},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical,
            current_data=current,
            metric_name="latency",
            metric_type=MetricType.LOWER_IS_BETTER,
        )

        assert result.is_regression is True
        assert (
            result.effect_size > 0
        )  # Positive because latency increased (current > historical)

    def test_neutral_metric_detection(self):
        """Test detection for neutral metrics (directional change matters)."""
        detector = PerformanceRegressionDetector()

        historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="memory_usage",
                value=1000 + np.random.normal(0, 50),
                metadata={},
            )
            for i in range(1, 21)
        ]

        current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="memory_usage",
                value=1200 + np.random.normal(0, 50),
                metadata={},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical,
            current_data=current,
            metric_name="memory_usage",
            metric_type=MetricType.NEUTRAL,
        )

        # For neutral metrics, we detect significant change but don't judge if it's "bad"
        assert result.is_significant_change is True
        assert result.effect_size != 0


class TestPerformanceRegressionDetectorValidation:
    """Test input validation and error handling."""

    def test_insufficient_historical_data_raises_error(self):
        """Test that insufficient historical data raises appropriate error."""
        detector = PerformanceRegressionDetector(minimum_samples=10)

        insufficient_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.85,
                metadata={},
            )
            for i in range(5)  # Only 5 samples, need 10
        ]

        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.85,
                metadata={},
            )
            for _ in range(10)
        ]

        with pytest.raises(RegressionError, match="Insufficient historical data"):
            detector.detect_regression(
                historical_data=insufficient_data,
                current_data=current_data,
                metric_name="accuracy",
            )

    def test_insufficient_current_data_raises_error(self):
        """Test that insufficient current data raises appropriate error."""
        detector = PerformanceRegressionDetector(minimum_samples=10)

        historical_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.85,
                metadata={},
            )
            for i in range(20)
        ]

        insufficient_current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.85,
                metadata={},
            )
            for _ in range(5)  # Only 5 samples, need 10
        ]

        with pytest.raises(RegressionError, match="Insufficient current data"):
            detector.detect_regression(
                historical_data=historical_data,
                current_data=insufficient_current,
                metric_name="accuracy",
            )

    def test_mismatched_metric_names_raises_error(self):
        """Test that mismatched metric names raise appropriate error."""
        detector = PerformanceRegressionDetector()

        historical_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.85,
                metadata={},
            )
            for i in range(15)
        ]

        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="latency",  # Different metric name!
                value=100,
                metadata={},
            )
            for _ in range(10)
        ]

        with pytest.raises(RegressionError, match="Metric name mismatch"):
            detector.detect_regression(
                historical_data=historical_data,
                current_data=current_data,
                metric_name="accuracy",
            )

    def test_empty_data_raises_error(self):
        """Test that empty data raises appropriate error."""
        detector = PerformanceRegressionDetector()

        with pytest.raises(RegressionError, match="Historical data cannot be empty"):
            detector.detect_regression(
                historical_data=[], current_data=[], metric_name="accuracy"
            )


class TestPerformanceRegressionDetectorAdvancedFeatures:
    """Test advanced features and configurations."""

    def test_baseline_window_filtering(self):
        """Test that baseline window correctly filters historical data."""
        detector = PerformanceRegressionDetector(baseline_window_days=7)

        # Create data spanning 30 days
        old_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=20),
                metric_name="accuracy",
                value=0.80,  # Old, lower performance
                metadata={},
            )
            for _ in range(10)
        ]

        recent_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=3),
                metric_name="accuracy",
                value=0.90,  # Recent, higher performance
                metadata={},
            )
            for _ in range(15)
        ]

        all_historical = old_data + recent_data

        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.88,  # Slight drop from recent baseline
                metadata={},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=all_historical,
            current_data=current_data,
            metric_name="accuracy",
        )

        # Should only compare against recent 7-day window (0.90 baseline)
        # So 0.88 vs 0.90 might show regression
        assert result.baseline_mean > 0.85  # Should use recent higher baseline

    def test_outlier_detection_and_filtering(self):
        """Test outlier detection and filtering from data."""
        detector = PerformanceRegressionDetector(filter_outliers=True)

        # Create data with obvious outliers
        # normal_data = [0.85] * 20  # Not used
        outlier_data = [0.85] * 18 + [0.3, 1.5]  # Two obvious outliers

        historical_with_outliers = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=outlier_data[i],
                metadata={},
            )
            for i in range(20)
        ]

        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.83,  # Slight drop
                metadata={},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical_with_outliers,
            current_data=current_data,
            metric_name="accuracy",
        )

        # Should have filtered outliers, so baseline should be close to 0.85
        assert 0.84 < result.baseline_mean < 0.86
        assert result.outliers_filtered > 0

    def test_confidence_intervals_calculation(self):
        """Test confidence interval calculations."""
        detector = PerformanceRegressionDetector()

        historical_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.02),
                metadata={},
            )
            for i in range(1, 21)
        ]

        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.80 + np.random.normal(0, 0.02),
                metadata={},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical_data,
            current_data=current_data,
            metric_name="accuracy",
        )

        assert result.baseline_confidence_interval is not None
        assert result.current_confidence_interval is not None
        assert len(result.baseline_confidence_interval) == 2  # [lower, upper]
        assert len(result.current_confidence_interval) == 2
        assert (
            result.baseline_confidence_interval[0]
            < result.baseline_confidence_interval[1]
        )

    def test_effect_size_calculation(self):
        """Test effect size (Cohen's d) calculation."""
        detector = PerformanceRegressionDetector()

        # Create data with known effect size
        historical_mean = 0.90
        current_mean = 0.85
        std_dev = 0.02

        historical_data = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=historical_mean + np.random.normal(0, std_dev),
                metadata={},
            )
            for i in range(1, 21)
        ]

        current_data = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=current_mean + np.random.normal(0, std_dev),
                metadata={},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical_data,
            current_data=current_data,
            metric_name="accuracy",
        )

        # Effect size should be approximately (0.85 - 0.90) / 0.02 = -2.5 (large effect)
        assert result.effect_size < -1.0  # Large negative effect size
        assert result.effect_size_magnitude == "large"


class TestPerformanceRegressionDetectorReporting:
    """Test reporting and summary capabilities."""

    @pytest.fixture
    def detector_with_regression(self):
        """Create detector and run regression test."""
        detector = PerformanceRegressionDetector()

        historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.90 + np.random.normal(0, 0.01),
                metadata={"version": f"1.{i}"},
            )
            for i in range(1, 21)
        ]

        current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.01),
                metadata={"version": "2.0"},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical, current_data=current, metric_name="accuracy"
        )

        return detector, result

    def test_generate_detailed_report(self, detector_with_regression):
        """Test generating detailed regression analysis report."""
        detector, result = detector_with_regression

        report = detector.generate_detailed_report(result)

        assert isinstance(report, dict)
        assert "summary" in report
        assert "statistical_analysis" in report
        assert "recommendations" in report
        assert report["summary"]["metric_name"] == "accuracy"
        assert report["summary"]["is_regression"] is True
        assert "confidence_level" in report["summary"]

    def test_generate_alert_summary(self, detector_with_regression):
        """Test generating alert summary for CI/CD systems."""
        detector, result = detector_with_regression

        alert = detector.generate_alert_summary(result)

        assert isinstance(alert, dict)
        assert alert["severity"] in ["low", "medium", "high", "critical"]
        assert "title" in alert
        assert "description" in alert
        assert "recommended_action" in alert
        assert alert["metric_name"] == "accuracy"

    def test_export_results_to_json(self, detector_with_regression):
        """Test exporting results to JSON format."""
        detector, result = detector_with_regression

        json_report = detector.export_results_to_json(result)

        assert isinstance(json_report, str)

        # Parse JSON to verify structure
        import json

        parsed = json.loads(json_report)
        assert "regression_result" in parsed
        assert "analysis_timestamp" in parsed
        assert parsed["regression_result"]["metric_name"] == "accuracy"


class TestPerformanceDataDataclass:
    """Test PerformanceData dataclass functionality."""

    def test_performance_data_creation(self):
        """Test PerformanceData creation with all fields."""
        timestamp = datetime.now()
        data = PerformanceData(
            timestamp=timestamp,
            metric_name="accuracy",
            value=0.85,
            metadata={"model": "v1.0", "dataset": "test"},
        )

        assert data.timestamp == timestamp
        assert data.metric_name == "accuracy"
        assert data.value == 0.85
        assert data.metadata["model"] == "v1.0"

    def test_performance_data_with_optional_metadata(self):
        """Test PerformanceData with empty metadata."""
        data = PerformanceData(
            timestamp=datetime.now(), metric_name="latency", value=120.5, metadata={}
        )

        assert data.metadata == {}
        assert data.value == 120.5


class TestRegressionResultDataclass:
    """Test RegressionResult dataclass functionality."""

    def test_regression_result_creation(self):
        """Test RegressionResult creation with all fields."""
        result = RegressionResult(
            metric_name="accuracy",
            is_regression=True,
            is_significant_change=True,
            p_value=0.001,
            effect_size=-1.5,
            effect_size_magnitude="large",
            confidence_level=0.99,
            baseline_mean=0.90,
            current_mean=0.85,
            baseline_std=0.02,
            current_std=0.015,
            test_results={"t_test": {"p_value": 0.001, "statistic": -8.5}},
            consensus_score=1.0,
            baseline_confidence_interval=[0.86, 0.94],
            current_confidence_interval=[0.82, 0.88],
            outliers_filtered=2,
        )

        assert result.metric_name == "accuracy"
        assert result.is_regression is True
        assert result.effect_size == -1.5
        assert result.consensus_score == 1.0


# Edge cases and performance tests
class TestPerformanceRegressionDetectorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_identical_distributions_no_regression(self):
        """Test identical distributions show no regression."""
        detector = PerformanceRegressionDetector()

        # Identical normal distributions
        np.random.seed(42)  # For reproducible results
        values = np.random.normal(0.85, 0.02, 30)

        historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=values[i],
                metadata={},
            )
            for i in range(20)
        ]

        current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=values[i + 20],
                metadata={},
            )
            for i in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical, current_data=current, metric_name="accuracy"
        )

        assert result.is_regression is False
        assert result.p_value > 0.05
        assert abs(result.effect_size) < 0.2  # Very small effect size

    def test_extreme_variance_handling(self):
        """Test handling of data with extreme variance."""
        detector = PerformanceRegressionDetector()

        # Historical data with extreme variance
        historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.85 + np.random.normal(0, 0.2),  # Very high variance
                metadata={},
            )
            for i in range(1, 21)
        ]

        # Current data with normal variance but different mean
        current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.75 + np.random.normal(0, 0.01),  # Low variance, lower mean
                metadata={},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical, current_data=current, metric_name="accuracy"
        )

        # Should handle extreme variance gracefully
        assert result is not None
        assert isinstance(result.p_value, float)
        assert 0 <= result.p_value <= 1

    def test_single_value_datasets(self):
        """Test handling of datasets with identical values."""
        detector = PerformanceRegressionDetector()

        # All historical values identical
        historical = [
            PerformanceData(
                timestamp=datetime.now() - timedelta(days=i),
                metric_name="accuracy",
                value=0.85,  # Identical values
                metadata={},
            )
            for i in range(1, 21)
        ]

        # All current values identical but different
        current = [
            PerformanceData(
                timestamp=datetime.now(),
                metric_name="accuracy",
                value=0.80,  # Different but identical values
                metadata={},
            )
            for _ in range(10)
        ]

        result = detector.detect_regression(
            historical_data=historical, current_data=current, metric_name="accuracy"
        )

        assert result.is_regression is True  # Clear difference should be detected
        assert result.baseline_std == 0.0  # Zero standard deviation
        assert result.current_std == 0.0


# Mark integration tests
@pytest.mark.e2e
class TestPerformanceRegressionDetectorIntegration:
    """Integration tests with real data and MLflow integration."""

    def test_integration_with_mlflow_metrics(self):
        """Test integration with MLflow metrics tracking."""
        # This would require actual MLflow server
        pytest.skip("Requires MLflow server - implement when e2e environment ready")

    def test_integration_with_prompt_test_runner(self):
        """Test integration with PromptTestRunner for full CI/CD pipeline."""
        # This would test the full pipeline integration
        pytest.skip("Requires full pipeline - implement when all components ready")
