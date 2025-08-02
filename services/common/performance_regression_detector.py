"""
PerformanceRegressionDetector - Statistical analysis for detecting performance drops.

Part of CRA-297 CI/CD Pipeline implementation. Provides statistical analysis capabilities
to detect significant performance regressions in prompt templates during CI/CD deployment.

This implementation follows strict TDD practices and integrates with the existing
MLflow Model Registry and PromptModel infrastructure.

Author: TDD Implementation for CRA-297
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from scipy import stats
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


class RegressionError(Exception):
    """Raised when PerformanceRegressionDetector encounters an error."""
    pass


class MetricType(Enum):
    """Types of metrics for regression analysis."""
    HIGHER_IS_BETTER = "higher_is_better"  # e.g., accuracy, precision
    LOWER_IS_BETTER = "lower_is_better"    # e.g., latency, error_rate
    NEUTRAL = "neutral"                    # e.g., memory usage (detect change)


class SignificanceLevel(Enum):
    """Statistical significance levels."""
    ALPHA_01 = 0.01  # 99% confidence
    ALPHA_05 = 0.05  # 95% confidence
    ALPHA_10 = 0.10  # 90% confidence


class StatisticalTest(Enum):
    """Available statistical tests."""
    T_TEST = "t_test"                        # Student's t-test
    WELCH_T_TEST = "welch_t_test"           # Welch's t-test (unequal variances)
    MANN_WHITNEY = "mann_whitney"            # Mann-Whitney U test (non-parametric)
    KOLMOGOROV_SMIRNOV = "kolmogorov_smirnov"  # Kolmogorov-Smirnov test


@dataclass
class PerformanceData:
    """
    Represents a single performance measurement.
    
    Attributes:
        timestamp: When the measurement was taken
        metric_name: Name of the performance metric
        value: Measured value
        metadata: Additional metadata about the measurement
    """
    timestamp: datetime
    metric_name: str
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegressionResult:
    """
    Results of performance regression analysis.
    
    Attributes:
        metric_name: Name of the analyzed metric
        is_regression: Whether a significant regression was detected
        is_significant_change: Whether any significant change was detected
        p_value: Combined p-value from statistical tests
        effect_size: Cohen's d or similar effect size measure
        effect_size_magnitude: Textual description of effect size
        confidence_level: Confidence level of the analysis
        baseline_mean: Mean of the baseline (historical) data
        current_mean: Mean of the current data
        baseline_std: Standard deviation of baseline data
        current_std: Standard deviation of current data
        test_results: Detailed results from each statistical test
        consensus_score: Agreement score between different tests (0-1)
        baseline_confidence_interval: Confidence interval for baseline mean
        current_confidence_interval: Confidence interval for current mean
        outliers_filtered: Number of outliers filtered from analysis
    """
    metric_name: str
    is_regression: bool
    is_significant_change: bool
    p_value: float
    effect_size: float
    effect_size_magnitude: str
    confidence_level: float
    baseline_mean: float
    current_mean: float
    baseline_std: float
    current_std: float
    test_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    consensus_score: float = 0.0
    baseline_confidence_interval: Optional[List[float]] = None
    current_confidence_interval: Optional[List[float]] = None
    outliers_filtered: int = 0


class PerformanceRegressionDetector:
    """
    Statistical analysis framework for detecting performance regressions.
    
    Provides comprehensive statistical testing capabilities including:
    - Multiple statistical tests (parametric and non-parametric)
    - Effect size analysis
    - Confidence interval calculations
    - Outlier detection and filtering
    - Multi-metric support
    
    Integrates with existing CI/CD pipeline for automated regression detection.
    """
    
    def __init__(
        self,
        significance_level: SignificanceLevel = SignificanceLevel.ALPHA_05,
        statistical_tests: List[StatisticalTest] = None,
        minimum_samples: int = 10,
        baseline_window_days: int = 30,
        filter_outliers: bool = False,
        outlier_threshold: float = 2.0
    ):
        """
        Initialize PerformanceRegressionDetector.
        
        Args:
            significance_level: Statistical significance level to use
            statistical_tests: List of statistical tests to run
            minimum_samples: Minimum number of samples required for analysis
            baseline_window_days: Number of days to look back for baseline data
            filter_outliers: Whether to filter outliers from data
            outlier_threshold: Z-score threshold for outlier detection
        """
        self.significance_level = significance_level
        self.statistical_tests = statistical_tests or [
            StatisticalTest.T_TEST,
            StatisticalTest.MANN_WHITNEY
        ]
        self.minimum_samples = minimum_samples
        self.baseline_window_days = baseline_window_days
        self.filter_outliers = filter_outliers
        self.outlier_threshold = outlier_threshold
    
    def detect_regression(
        self,
        historical_data: List[PerformanceData],
        current_data: List[PerformanceData],
        metric_name: str,
        metric_type: MetricType = MetricType.HIGHER_IS_BETTER
    ) -> RegressionResult:
        """
        Detect performance regression by comparing current data against historical baseline.
        
        Args:
            historical_data: Historical performance measurements
            current_data: Current performance measurements
            metric_name: Name of the metric to analyze
            metric_type: Type of metric (higher/lower is better)
            
        Returns:
            RegressionResult with detailed analysis
            
        Raises:
            RegressionError: If data is insufficient or invalid
        """
        # Validate inputs
        self._validate_inputs(historical_data, current_data, metric_name)
        
        # Filter data by baseline window
        filtered_historical = self._filter_by_baseline_window(historical_data)
        
        # Extract values for analysis
        historical_values = [d.value for d in filtered_historical]
        current_values = [d.value for d in current_data]
        
        # Filter outliers if enabled
        outliers_filtered = 0
        if self.filter_outliers:
            historical_values, h_outliers = self._filter_outliers(historical_values)
            current_values, c_outliers = self._filter_outliers(current_values)
            outliers_filtered = h_outliers + c_outliers
        
        # Calculate basic statistics
        baseline_mean = np.mean(historical_values)
        current_mean = np.mean(current_values)
        baseline_std = np.std(historical_values, ddof=1) if len(historical_values) > 1 else 0.0
        current_std = np.std(current_values, ddof=1) if len(current_values) > 1 else 0.0
        
        # Run statistical tests
        test_results = self._run_statistical_tests(historical_values, current_values)
        
        # Calculate effect size
        effect_size = self._calculate_effect_size(
            historical_values, current_values, metric_type
        )
        effect_size_magnitude = self._interpret_effect_size(abs(effect_size))
        
        # Calculate confidence intervals
        baseline_ci = self._calculate_confidence_interval(historical_values)
        current_ci = self._calculate_confidence_interval(current_values)
        
        # Determine overall result
        p_values = [result["p_value"] for result in test_results.values()]
        combined_p_value = self._combine_p_values(p_values)
        
        # Special case: if both groups have zero variance but different means, it's significant
        if baseline_std == 0.0 and current_std == 0.0 and baseline_mean != current_mean:
            is_significant_change = True
            combined_p_value = 0.0  # Effectively zero p-value
        else:
            is_significant_change = combined_p_value < self.significance_level.value
        is_regression = self._determine_regression(
            is_significant_change, effect_size, metric_type
        )
        
        # Calculate consensus score
        consensus_score = self._calculate_consensus_score(test_results)
        
        return RegressionResult(
            metric_name=metric_name,
            is_regression=bool(is_regression),
            is_significant_change=bool(is_significant_change),
            p_value=combined_p_value,
            effect_size=effect_size,
            effect_size_magnitude=effect_size_magnitude,
            confidence_level=1.0 - self.significance_level.value,
            baseline_mean=baseline_mean,
            current_mean=current_mean,
            baseline_std=baseline_std,
            current_std=current_std,
            test_results=test_results,
            consensus_score=consensus_score,
            baseline_confidence_interval=baseline_ci,
            current_confidence_interval=current_ci,
            outliers_filtered=outliers_filtered
        )
    
    def _validate_inputs(
        self,
        historical_data: List[PerformanceData],
        current_data: List[PerformanceData],
        metric_name: str
    ) -> None:
        """Validate input data for regression analysis."""
        if not historical_data:
            raise RegressionError("Historical data cannot be empty")
        
        if not current_data:
            raise RegressionError("Current data cannot be empty")
        
        if len(historical_data) < self.minimum_samples:
            raise RegressionError(
                f"Insufficient historical data: {len(historical_data)} < {self.minimum_samples}"
            )
        
        if len(current_data) < self.minimum_samples:
            raise RegressionError(
                f"Insufficient current data: {len(current_data)} < {self.minimum_samples}"
            )
        
        # Check metric name consistency
        for data in historical_data + current_data:
            if data.metric_name != metric_name:
                raise RegressionError(
                    f"Metric name mismatch: expected '{metric_name}', got '{data.metric_name}'"
                )
    
    def _filter_by_baseline_window(
        self, historical_data: List[PerformanceData]
    ) -> List[PerformanceData]:
        """Filter historical data by baseline window."""
        cutoff_date = datetime.now() - timedelta(days=self.baseline_window_days)
        return [d for d in historical_data if d.timestamp >= cutoff_date]
    
    def _filter_outliers(self, values: List[float]) -> Tuple[List[float], int]:
        """Filter outliers using Z-score method."""
        if len(values) < 3:
            return values, 0
        
        z_scores = np.abs(stats.zscore(values))
        filtered_values = [v for v, z in zip(values, z_scores) if z < self.outlier_threshold]
        outliers_count = len(values) - len(filtered_values)
        
        return filtered_values, outliers_count
    
    def _run_statistical_tests(
        self, historical_values: List[float], current_values: List[float]
    ) -> Dict[str, Dict[str, Any]]:
        """Run configured statistical tests."""
        results = {}
        
        # Check for zero variance cases
        hist_std = np.std(historical_values, ddof=1) if len(historical_values) > 1 else 0.0
        curr_std = np.std(current_values, ddof=1) if len(current_values) > 1 else 0.0
        
        for test in self.statistical_tests:
            try:
                if test == StatisticalTest.T_TEST:
                    statistic, p_value = stats.ttest_ind(historical_values, current_values)
                    results["t_test"] = {"statistic": statistic, "p_value": p_value}
                    
                elif test == StatisticalTest.WELCH_T_TEST:
                    statistic, p_value = stats.ttest_ind(
                        historical_values, current_values, equal_var=False
                    )
                    results["welch_t_test"] = {"statistic": statistic, "p_value": p_value}
                    
                elif test == StatisticalTest.MANN_WHITNEY:
                    statistic, p_value = stats.mannwhitneyu(
                        historical_values, current_values, alternative='two-sided'
                    )
                    results["mann_whitney"] = {"statistic": statistic, "p_value": p_value}
                    
                elif test == StatisticalTest.KOLMOGOROV_SMIRNOV:
                    statistic, p_value = stats.ks_2samp(historical_values, current_values)
                    results["kolmogorov_smirnov"] = {"statistic": statistic, "p_value": p_value}
                    
            except (ValueError, RuntimeWarning, Exception) as e:
                # Handle cases where statistical tests fail (e.g., zero variance)
                hist_mean = np.mean(historical_values)
                curr_mean = np.mean(current_values)
                
                if hist_std == 0.0 and curr_std == 0.0:
                    # Both groups have zero variance
                    if hist_mean == curr_mean:
                        p_value = 1.0  # No difference
                    else:
                        p_value = 0.0  # Clear difference
                else:
                    p_value = 1.0  # Conservative: assume no significance if test fails
                
                test_name = test.value
                results[test_name] = {"statistic": np.nan, "p_value": p_value}
        
        return results
    
    def _calculate_effect_size(
        self,
        historical_values: List[float],
        current_values: List[float],
        metric_type: MetricType
    ) -> float:
        """Calculate Cohen's d effect size."""
        mean1 = np.mean(historical_values)
        mean2 = np.mean(current_values)
        
        # Pooled standard deviation
        n1, n2 = len(historical_values), len(current_values)
        s1, s2 = np.std(historical_values, ddof=1), np.std(current_values, ddof=1)
        
        if s1 == 0 and s2 == 0:
            # Both have zero variance
            if mean1 == mean2:
                return 0.0
            else:
                # Use a large effect size to indicate clear difference when variance is zero
                return 10.0 if mean2 > mean1 else -10.0
        
        pooled_std = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return 0.0
        
        effect_size = (mean2 - mean1) / pooled_std
        
        # For effect size, we don't adjust the sign here - we'll handle it in regression determination
        # Effect size represents (current - historical) / pooled_std
        
        return effect_size
    
    def _interpret_effect_size(self, abs_effect_size: float) -> str:
        """Interpret effect size magnitude."""
        if abs_effect_size < 0.2:
            return "negligible"
        elif abs_effect_size < 0.5:
            return "small"
        elif abs_effect_size < 0.8:
            return "medium"
        else:
            return "large"
    
    def _calculate_confidence_interval(
        self, values: List[float], confidence: float = 0.95
    ) -> List[float]:
        """Calculate confidence interval for mean."""
        if len(values) < 2:
            return [values[0], values[0]] if values else [0.0, 0.0]
        
        mean = np.mean(values)
        std_err = stats.sem(values)
        
        # Use t-distribution for small samples
        df = len(values) - 1
        t_value = stats.t.ppf((1 + confidence) / 2, df)
        
        margin_of_error = t_value * std_err
        
        return [mean - margin_of_error, mean + margin_of_error]
    
    def _combine_p_values(self, p_values: List[float]) -> float:
        """Combine p-values using Fisher's method."""
        if not p_values:
            return 1.0
        
        # Filter out any NaN or invalid p-values
        valid_p_values = [p for p in p_values if not np.isnan(p) and 0 <= p <= 1]
        
        if not valid_p_values:
            return 1.0
        
        # Fisher's combined probability test
        try:
            _, combined_p = stats.combine_pvalues(valid_p_values, method='fisher')
            return combined_p
        except:
            # Fallback to minimum p-value
            return min(valid_p_values)
    
    def _determine_regression(
        self, is_significant: bool, effect_size: float, metric_type: MetricType
    ) -> bool:
        """Determine if there is a performance regression."""
        if not is_significant:
            return False
        
        if metric_type == MetricType.NEUTRAL:
            return False  # For neutral metrics, we only detect change, not regression
        
        # Effect size = (current - historical) / pooled_std
        # For higher_is_better: negative effect size is regression (current < historical)
        # For lower_is_better: positive effect size is regression (current > historical) 
        if metric_type == MetricType.HIGHER_IS_BETTER:
            return effect_size < 0
        else:  # LOWER_IS_BETTER
            return effect_size > 0
    
    def _calculate_consensus_score(self, test_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate consensus score between different statistical tests."""
        if not test_results:
            return 0.0
        
        significant_tests = sum(
            1 for result in test_results.values()
            if result.get("p_value", 1.0) < self.significance_level.value
        )
        
        return significant_tests / len(test_results)
    
    def generate_detailed_report(self, result: RegressionResult) -> Dict[str, Any]:
        """Generate detailed regression analysis report."""
        return {
            "summary": {
                "metric_name": result.metric_name,
                "is_regression": result.is_regression,
                "is_significant_change": result.is_significant_change,
                "confidence_level": result.confidence_level,
                "effect_size": result.effect_size,
                "effect_size_magnitude": result.effect_size_magnitude
            },
            "statistical_analysis": {
                "p_value": result.p_value,
                "consensus_score": result.consensus_score,
                "test_results": result.test_results,
                "baseline_stats": {
                    "mean": result.baseline_mean,
                    "std": result.baseline_std,
                    "confidence_interval": result.baseline_confidence_interval
                },
                "current_stats": {
                    "mean": result.current_mean,
                    "std": result.current_std,
                    "confidence_interval": result.current_confidence_interval
                }
            },
            "data_quality": {
                "outliers_filtered": result.outliers_filtered
            },
            "recommendations": self._generate_recommendations(result)
        }
    
    def generate_alert_summary(self, result: RegressionResult) -> Dict[str, Any]:
        """Generate alert summary for CI/CD systems."""
        severity = self._determine_alert_severity(result)
        
        return {
            "severity": severity,
            "metric_name": result.metric_name,
            "title": f"Performance Regression Detected: {result.metric_name}",
            "description": (
                f"Significant regression detected in {result.metric_name} "
                f"(p-value: {result.p_value:.4f}, effect size: {result.effect_size:.2f})"
            ),
            "recommended_action": self._get_recommended_action(severity),
            "confidence_level": result.confidence_level,
            "effect_size_magnitude": result.effect_size_magnitude
        }
    
    def export_results_to_json(self, result: RegressionResult) -> str:
        """Export regression results to JSON format."""
        report_data = {
            "analysis_timestamp": datetime.now().isoformat(),
            "regression_result": {
                "metric_name": result.metric_name,
                "is_regression": result.is_regression,
                "is_significant_change": result.is_significant_change,
                "p_value": result.p_value,
                "effect_size": result.effect_size,
                "effect_size_magnitude": result.effect_size_magnitude,
                "confidence_level": result.confidence_level,
                "baseline_mean": result.baseline_mean,
                "current_mean": result.current_mean,
                "baseline_std": result.baseline_std,
                "current_std": result.current_std,
                "consensus_score": result.consensus_score,
                "test_results": result.test_results,
                "baseline_confidence_interval": result.baseline_confidence_interval,
                "current_confidence_interval": result.current_confidence_interval,
                "outliers_filtered": result.outliers_filtered
            }
        }
        
        return json.dumps(report_data, indent=2, default=str)
    
    def _generate_recommendations(self, result: RegressionResult) -> List[str]:
        """Generate recommendations based on regression analysis."""
        recommendations = []
        
        if result.is_regression:
            recommendations.append("Performance regression detected - investigate recent changes")
            
            if result.effect_size_magnitude == "large":
                recommendations.append("Large effect size - prioritize immediate investigation")
            
            if result.consensus_score < 0.5:
                recommendations.append("Low consensus between tests - verify with additional metrics")
        
        if result.outliers_filtered > 0:
            recommendations.append(f"Filtered {result.outliers_filtered} outliers - verify data quality")
        
        return recommendations
    
    def _determine_alert_severity(self, result: RegressionResult) -> str:
        """Determine alert severity based on regression analysis."""
        if not result.is_regression:
            return "low"
        
        if result.effect_size_magnitude == "large" and result.p_value < 0.01:
            return "critical"
        elif result.effect_size_magnitude in ["large", "medium"] and result.p_value < 0.05:
            return "high"
        else:
            return "medium"
    
    def _get_recommended_action(self, severity: str) -> str:
        """Get recommended action based on severity."""
        actions = {
            "low": "Monitor closely in next deployment",
            "medium": "Review changes and run additional tests",
            "high": "Block deployment and investigate immediately",
            "critical": "Halt deployment and rollback if necessary"
        }
        return actions.get(severity, "Review and investigate")