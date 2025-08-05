"""
Thompson Sampling Operator for Airflow (CRA-284)

Custom operator for optimizing Thompson sampling parameters in the orchestrator service.
Handles parameter updates, performance monitoring, and A/B test optimization.

Epic: E7 - Viral Learning Flywheel
"""

import numpy as np
from typing import Any, Dict, List
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter, Retry

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.exceptions import AirflowException
from airflow.utils.context import Context


class ThompsonSamplingOperator(BaseOperator):
    """
    Custom Airflow operator for Thompson sampling parameter optimization.

    This operator provides:
    - Thompson sampling parameter updates based on performance data
    - A/B test variant optimization
    - Exploration vs exploitation balancing
    - Performance-based learning rate adjustment

    Args:
        orchestrator_url: Base URL for the orchestrator service
        operation: Operation to perform ('update_parameters', 'optimize_variants', 'analyze_performance')
        learning_rate: Base learning rate for parameter updates (default: 0.1)
        exploration_factor: Exploration vs exploitation balance (default: 0.2)
        performance_window_hours: Hours of data to consider for optimization (default: 24)
        min_sample_size: Minimum samples required for reliable optimization (default: 50)
        target_engagement_rate: Target engagement rate for optimization (default: 0.06)
        target_cost_per_follow: Target cost per follow for optimization (default: 0.01)
        timeout: Request timeout in seconds (default: 300)

    Example:
        ```python
        optimize_thompson_sampling = ThompsonSamplingOperator(
            task_id='optimize_thompson_sampling',
            orchestrator_url='http://orchestrator:8080',
            operation='update_parameters',
            learning_rate=0.15,
            exploration_factor=0.25,
            dag=dag
        )
        ```
    """

    template_fields = [
        "operation",
        "learning_rate",
        "exploration_factor",
        "performance_window_hours",
        "target_engagement_rate",
        "target_cost_per_follow",
        "orchestrator_url",
    ]

    ui_color = "#d5dbdb"
    ui_fgcolor = "#2c3e50"

    @apply_defaults
    def __init__(
        self,
        orchestrator_url: str,
        operation: str = "update_parameters",
        learning_rate: float = 0.1,
        exploration_factor: float = 0.2,
        performance_window_hours: int = 24,
        min_sample_size: int = 50,
        target_engagement_rate: float = 0.06,
        target_cost_per_follow: float = 0.01,
        timeout: int = 300,
        verify_ssl: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.orchestrator_url = orchestrator_url.rstrip("/")
        self.operation = operation
        self.learning_rate = learning_rate
        self.exploration_factor = exploration_factor
        self.performance_window_hours = performance_window_hours
        self.min_sample_size = min_sample_size
        self.target_engagement_rate = target_engagement_rate
        self.target_cost_per_follow = target_cost_per_follow
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Validate operation
        valid_operations = [
            "update_parameters",
            "optimize_variants",
            "analyze_performance",
            "reset_parameters",
            "export_statistics",
        ]
        if self.operation not in valid_operations:
            raise ValueError(
                f"Invalid operation: {operation}. Must be one of {valid_operations}"
            )

        # Validate parameters
        if not 0.0 <= self.learning_rate <= 1.0:
            raise ValueError("Learning rate must be between 0.0 and 1.0")
        if not 0.0 <= self.exploration_factor <= 1.0:
            raise ValueError("Exploration factor must be between 0.0 and 1.0")

        # Configure HTTP session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST", "PUT"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def execute(self, context: Context) -> Dict[str, Any]:
        """
        Execute Thompson sampling optimization operation.

        Returns:
            Dict containing optimization results and metrics
        """
        self.log.info(f"Starting Thompson sampling operation: {self.operation}")

        # Perform health check
        if not self._health_check():
            raise AirflowException("Orchestrator service is not healthy")

        # Execute operation based on type
        if self.operation == "update_parameters":
            return self._update_parameters(context)
        elif self.operation == "optimize_variants":
            return self._optimize_variants(context)
        elif self.operation == "analyze_performance":
            return self._analyze_performance(context)
        elif self.operation == "reset_parameters":
            return self._reset_parameters(context)
        elif self.operation == "export_statistics":
            return self._export_statistics(context)
        else:
            raise AirflowException(f"Unknown operation: {self.operation}")

    def _health_check(self) -> bool:
        """Perform health check on orchestrator service."""
        try:
            response = self.session.get(
                f"{self.orchestrator_url}/health", timeout=10, verify=self.verify_ssl
            )
            return response.status_code == 200
        except Exception as e:
            self.log.error(f"Health check failed: {e}")
            return False

    def _update_parameters(self, context: Context) -> Dict[str, Any]:
        """Update Thompson sampling parameters based on recent performance."""
        self.log.info("Updating Thompson sampling parameters")

        # Get current performance metrics
        performance_data = self._get_performance_data()
        current_params = self._get_current_parameters()

        # Calculate new parameters based on performance
        new_params = self._calculate_optimized_parameters(
            performance_data, current_params
        )

        # Update parameters in orchestrator
        update_payload = {
            "parameters": new_params,
            "learning_rate": self.learning_rate,
            "exploration_factor": self.exploration_factor,
            "update_reason": "automated_optimization",
            "performance_window_hours": self.performance_window_hours,
        }

        try:
            response = self.session.post(
                f"{self.orchestrator_url}/thompson-sampling/update",
                json=update_payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()

            self.log.info("Thompson sampling parameters updated successfully")
            self.log.info(f"Parameters changed: {len(new_params)} variants updated")

            return {
                "operation": "update_parameters",
                "status": "success",
                "parameters_updated": len(new_params),
                "old_parameters": current_params,
                "new_parameters": new_params,
                "performance_improvement_expected": result.get(
                    "expected_improvement", 0.0
                ),
                "learning_rate_used": self.learning_rate,
                "exploration_factor_used": self.exploration_factor,
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Parameter update failed: {e}")

    def _optimize_variants(self, context: Context) -> Dict[str, Any]:
        """Optimize variant selection and allocation based on Thompson sampling."""
        self.log.info("Optimizing content variant allocation")

        # Get variant performance data
        try:
            response = self.session.get(
                f"{self.orchestrator_url}/thompson-sampling/variants",
                params={"hours": self.performance_window_hours},
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            variants_data = response.json()

            # Analyze variant performance and calculate optimal allocation
            optimization_results = self._calculate_optimal_allocation(variants_data)

            # Update variant weights
            update_payload = {
                "variant_weights": optimization_results["optimal_weights"],
                "allocation_strategy": optimization_results["strategy"],
                "expected_improvement": optimization_results["expected_improvement"],
            }

            response = self.session.post(
                f"{self.orchestrator_url}/thompson-sampling/variants/optimize",
                json=update_payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            _ = response.json()

            self.log.info("Variant optimization completed")
            self.log.info(f"Strategy: {optimization_results['strategy']}")
            self.log.info(
                f"Expected improvement: {optimization_results['expected_improvement']:.2%}"
            )

            return {
                "operation": "optimize_variants",
                "status": "success",
                "variants_analyzed": len(variants_data.get("variants", [])),
                "allocation_strategy": optimization_results["strategy"],
                "optimal_weights": optimization_results["optimal_weights"],
                "expected_improvement": optimization_results["expected_improvement"],
                "performance_analysis": optimization_results["analysis"],
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Variant optimization failed: {e}")

    def _analyze_performance(self, context: Context) -> Dict[str, Any]:
        """Analyze Thompson sampling performance and effectiveness."""
        self.log.info("Analyzing Thompson sampling performance")

        try:
            # Get comprehensive performance analytics
            response = self.session.get(
                f"{self.orchestrator_url}/thompson-sampling/analytics",
                params={
                    "hours": self.performance_window_hours,
                    "include_convergence": True,
                    "include_regret": True,
                    "include_exploration_exploitation": True,
                },
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            analytics_data = response.json()

            # Calculate key performance indicators
            kpis = self._calculate_thompson_sampling_kpis(analytics_data)

            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(
                analytics_data, kpis
            )

            self.log.info("Thompson sampling analysis completed")
            self.log.info(f"Convergence rate: {kpis['convergence_rate']:.2%}")
            self.log.info(f"Regret rate: {kpis['regret_rate']:.4f}")
            self.log.info(f"Exploration ratio: {kpis['exploration_ratio']:.2%}")

            return {
                "operation": "analyze_performance",
                "status": "success",
                "kpis": kpis,
                "convergence_analysis": analytics_data.get("convergence", {}),
                "regret_analysis": analytics_data.get("regret", {}),
                "exploration_exploitation_balance": analytics_data.get(
                    "exploration_exploitation", {}
                ),
                "recommendations": recommendations,
                "performance_trends": analytics_data.get("trends", {}),
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Performance analysis failed: {e}")

    def _reset_parameters(self, context: Context) -> Dict[str, Any]:
        """Reset Thompson sampling parameters to default values."""
        self.log.info("Resetting Thompson sampling parameters to defaults")

        default_params = {
            "learning_rate": 0.1,
            "exploration_factor": 0.2,
            "prior_alpha": 1.0,
            "prior_beta": 1.0,
            "decay_factor": 0.99,
            "min_samples": 10,
        }

        try:
            response = self.session.post(
                f"{self.orchestrator_url}/thompson-sampling/reset",
                json={"parameters": default_params, "reason": "manual_reset"},
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()

            self.log.info("Thompson sampling parameters reset successfully")

            return {
                "operation": "reset_parameters",
                "status": "success",
                "reset_parameters": default_params,
                "previous_parameters": result.get("previous_parameters", {}),
                "variants_reset": result.get("variants_reset", 0),
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Parameter reset failed: {e}")

    def _export_statistics(self, context: Context) -> Dict[str, Any]:
        """Export Thompson sampling statistics for analysis."""
        self.log.info("Exporting Thompson sampling statistics")

        try:
            response = self.session.get(
                f"{self.orchestrator_url}/thompson-sampling/export",
                params={
                    "hours": self.performance_window_hours,
                    "format": "detailed",
                    "include_raw_data": True,
                },
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            statistics = response.json()

            # Calculate summary metrics
            summary = {
                "total_decisions": statistics.get("total_decisions", 0),
                "total_variants": len(statistics.get("variants", [])),
                "best_performing_variant": statistics.get("best_variant", {}),
                "overall_performance": statistics.get("overall_performance", {}),
                "export_timestamp": datetime.now().isoformat(),
            }

            self.log.info(
                f"Statistics exported: {summary['total_decisions']} decisions analyzed"
            )

            return {
                "operation": "export_statistics",
                "status": "success",
                "summary": summary,
                "detailed_statistics": statistics,
                "export_size_mb": len(str(statistics)) / (1024 * 1024),
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Statistics export failed: {e}")

    def _get_performance_data(self) -> Dict[str, Any]:
        """Get recent performance data for optimization."""
        try:
            response = self.session.get(
                f"{self.orchestrator_url}/metrics/performance",
                params={"hours": self.performance_window_hours},
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.log.warning(f"Failed to get performance data: {e}")
            return {}

    def _get_current_parameters(self) -> Dict[str, Any]:
        """Get current Thompson sampling parameters."""
        try:
            response = self.session.get(
                f"{self.orchestrator_url}/thompson-sampling/parameters",
                timeout=30,
                verify=self.verify_ssl,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.log.warning(f"Failed to get current parameters: {e}")
            return {}

    def _calculate_optimized_parameters(
        self, performance_data: Dict[str, Any], current_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate optimized parameters based on performance data."""
        # Get key performance metrics
        current_engagement = performance_data.get("engagement_rate", 0.0)
        current_cost = performance_data.get("cost_per_follow", 0.01)
        sample_size = performance_data.get("total_samples", 0)

        # Skip optimization if insufficient data
        if sample_size < self.min_sample_size:
            self.log.warning(
                f"Insufficient sample size ({sample_size} < {self.min_sample_size}), keeping current parameters"
            )
            return current_params

        # Calculate performance ratios
        engagement_ratio = current_engagement / self.target_engagement_rate
        cost_ratio = self.target_cost_per_follow / max(current_cost, 0.001)

        # Adjust learning rate based on performance
        performance_score = (engagement_ratio + cost_ratio) / 2
        adjusted_learning_rate = self.learning_rate

        if performance_score < 0.8:  # Poor performance
            adjusted_learning_rate = min(
                self.learning_rate * 1.5, 0.3
            )  # Increase learning
        elif performance_score > 1.2:  # Good performance
            adjusted_learning_rate = max(
                self.learning_rate * 0.8, 0.05
            )  # Reduce learning

        # Adjust exploration factor
        adjusted_exploration = self.exploration_factor
        if current_engagement < self.target_engagement_rate * 0.8:
            adjusted_exploration = min(
                self.exploration_factor * 1.3, 0.4
            )  # More exploration
        elif current_engagement > self.target_engagement_rate * 1.1:
            adjusted_exploration = max(
                self.exploration_factor * 0.7, 0.1
            )  # Less exploration

        # Create optimized parameters
        optimized_params = {
            "learning_rate": adjusted_learning_rate,
            "exploration_factor": adjusted_exploration,
            "prior_alpha": current_params.get("prior_alpha", 1.0),
            "prior_beta": current_params.get("prior_beta", 1.0),
            "decay_factor": 0.99 if performance_score > 1.0 else 0.95,
            "min_samples": max(10, int(sample_size * 0.1)),
        }

        return optimized_params

    def _calculate_optimal_allocation(
        self, variants_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate optimal variant allocation using Thompson sampling principles."""
        variants = variants_data.get("variants", [])

        if not variants:
            return {
                "optimal_weights": {},
                "strategy": "equal_allocation",
                "expected_improvement": 0.0,
                "analysis": {},
            }

        # Calculate Thompson sampling weights for each variant
        optimal_weights = {}
        total_weight = 0

        for variant in variants:
            # Use Beta distribution parameters (alpha, beta) for Thompson sampling
            alpha = variant.get("successes", 1) + 1
            beta = variant.get("failures", 1) + 1

            # Sample from Beta distribution to get weight
            weight = np.random.beta(alpha, beta)
            optimal_weights[variant["id"]] = weight
            total_weight += weight

        # Normalize weights
        for variant_id in optimal_weights:
            optimal_weights[variant_id] /= total_weight

        # Determine allocation strategy
        max_weight = max(optimal_weights.values())
        if max_weight > 0.7:
            strategy = "exploit_best"
        elif max_weight < 0.4:
            strategy = "explore_equally"
        else:
            strategy = "balanced_exploration"

        # Calculate expected improvement (simplified)
        current_performance = variants_data.get("overall_performance", 0.0)
        best_variant_performance = max(
            [v.get("performance", 0.0) for v in variants], default=0.0
        )
        expected_improvement = (
            best_variant_performance - current_performance
        ) * max_weight

        return {
            "optimal_weights": optimal_weights,
            "strategy": strategy,
            "expected_improvement": expected_improvement,
            "analysis": {
                "total_variants": len(variants),
                "best_variant_weight": max_weight,
                "weight_distribution": optimal_weights,
            },
        }

    def _calculate_thompson_sampling_kpis(
        self, analytics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate key performance indicators for Thompson sampling."""
        convergence_data = analytics_data.get("convergence", {})
        regret_data = analytics_data.get("regret", {})
        exploration_data = analytics_data.get("exploration_exploitation", {})

        return {
            "convergence_rate": convergence_data.get("rate", 0.0),
            "regret_rate": regret_data.get("cumulative_regret", 0.0)
            / max(regret_data.get("total_rounds", 1), 1),
            "exploration_ratio": exploration_data.get("exploration_ratio", 0.0),
            "exploitation_ratio": exploration_data.get("exploitation_ratio", 0.0),
            "best_arm_selection_rate": analytics_data.get(
                "best_arm_selection_rate", 0.0
            ),
            "parameter_stability": analytics_data.get("parameter_stability", 0.0),
        }

    def _generate_optimization_recommendations(
        self, analytics_data: Dict[str, Any], kpis: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []

        # Convergence recommendations
        if kpis["convergence_rate"] < 0.8:
            recommendations.append(
                "Increase learning rate to improve convergence speed"
            )

        # Regret recommendations
        if kpis["regret_rate"] > 0.1:
            recommendations.append("Reduce exploration factor to minimize regret")

        # Exploration-exploitation balance
        if kpis["exploration_ratio"] > 0.7:
            recommendations.append("Reduce exploration factor - too much exploration")
        elif kpis["exploration_ratio"] < 0.2:
            recommendations.append(
                "Increase exploration factor - insufficient exploration"
            )

        # Best arm selection
        if kpis["best_arm_selection_rate"] < 0.6:
            recommendations.append("Improve variant quality or increase sample sizes")

        # Parameter stability
        if kpis["parameter_stability"] < 0.5:
            recommendations.append(
                "Consider increasing decay factor for more stable parameters"
            )

        if not recommendations:
            recommendations.append(
                "Thompson sampling is performing well, no immediate changes needed"
            )

        return recommendations

    def on_kill(self) -> None:
        """Clean up resources when task is killed."""
        if hasattr(self, "session"):
            self.session.close()
        self.log.info("ThompsonSamplingOperator killed, cleaned up resources")
