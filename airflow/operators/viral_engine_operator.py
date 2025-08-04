"""
Viral Engine Operator for Airflow (CRA-284)

Custom operator for interacting with the Viral Engine Service.
Handles pattern extraction, viral analysis, and optimization workflows.

Epic: E7 - Viral Learning Flywheel
"""

import time
from typing import Any, Dict, Optional
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter, Retry

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.exceptions import AirflowException
from airflow.utils.context import Context


class ViralEngineOperator(BaseOperator):
    """
    Custom Airflow operator for viral engine pattern extraction and analysis.

    This operator provides:
    - Viral pattern extraction from scraped content
    - Engagement prediction and scoring
    - Viral coefficient calculation
    - Performance optimization recommendations

    Args:
        viral_engine_url: Base URL for the viral engine service
        operation: Operation to perform ('extract_patterns', 'predict_engagement', 'calculate_viral_coefficient')
        batch_size: Number of posts to process per batch (default: 25)
        max_parallel_tasks: Maximum parallel processing tasks (default: 5)
        source_filter: Filter for content source (default: None)
        min_engagement_threshold: Minimum engagement rate for processing (default: 0.01)
        timeout: Request timeout in seconds (default: 600)

    Example:
        ```python
        extract_patterns = ViralEngineOperator(
            task_id='extract_viral_patterns',
            viral_engine_url='http://viral-engine:8080',
            operation='extract_patterns',
            batch_size=50,
            max_parallel_tasks=10,
            dag=dag
        )
        ```
    """

    template_fields = [
        "operation",
        "batch_size",
        "max_parallel_tasks",
        "source_filter",
        "min_engagement_threshold",
        "viral_engine_url",
    ]

    ui_color = "#f9e79f"
    ui_fgcolor = "#7d6608"

    @apply_defaults
    def __init__(
        self,
        viral_engine_url: str,
        operation: str = "extract_patterns",
        batch_size: int = 25,
        max_parallel_tasks: int = 5,
        source_filter: Optional[str] = None,
        min_engagement_threshold: float = 0.01,
        timeout: int = 600,
        verify_ssl: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.viral_engine_url = viral_engine_url.rstrip("/")
        self.operation = operation
        self.batch_size = batch_size
        self.max_parallel_tasks = max_parallel_tasks
        self.source_filter = source_filter
        self.min_engagement_threshold = min_engagement_threshold
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Validate operation
        valid_operations = [
            "extract_patterns",
            "predict_engagement",
            "calculate_viral_coefficient",
            "optimize_parameters",
            "analyze_performance",
        ]
        if self.operation not in valid_operations:
            raise ValueError(
                f"Invalid operation: {operation}. Must be one of {valid_operations}"
            )

        # Configure HTTP session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=2,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def execute(self, context: Context) -> Dict[str, Any]:
        """
        Execute viral engine operation.

        Returns:
            Dict containing operation results and metrics
        """
        self.log.info(f"Starting viral engine operation: {self.operation}")

        # Perform health check
        if not self._health_check():
            raise AirflowException("Viral Engine service is not healthy")

        # Execute operation based on type
        if self.operation == "extract_patterns":
            return self._extract_patterns(context)
        elif self.operation == "predict_engagement":
            return self._predict_engagement(context)
        elif self.operation == "calculate_viral_coefficient":
            return self._calculate_viral_coefficient(context)
        elif self.operation == "optimize_parameters":
            return self._optimize_parameters(context)
        elif self.operation == "analyze_performance":
            return self._analyze_performance(context)
        else:
            raise AirflowException(f"Unknown operation: {self.operation}")

    def _health_check(self) -> bool:
        """Perform health check on viral engine service."""
        try:
            response = self.session.get(
                f"{self.viral_engine_url}/health", timeout=10, verify=self.verify_ssl
            )
            return response.status_code == 200
        except Exception as e:
            self.log.error(f"Health check failed: {e}")
            return False

    def _extract_patterns(self, context: Context) -> Dict[str, Any]:
        """Extract viral patterns from scraped content."""
        self.log.info("Extracting viral patterns from scraped content")

        payload = {
            "batch_size": self.batch_size,
            "max_parallel_tasks": self.max_parallel_tasks,
            "source_filter": self.source_filter,
            "min_engagement_threshold": self.min_engagement_threshold,
            "extract_features": True,
            "analyze_sentiment": True,
            "identify_hooks": True,
        }

        try:
            response = self.session.post(
                f"{self.viral_engine_url}/patterns/extract",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()
            self.log.info(
                f"Pattern extraction completed: {result.get('patterns_extracted', 0)} patterns found"
            )

            # Wait for processing completion if async
            if result.get("status") == "processing":
                task_id = result.get("task_id")
                result = self._wait_for_task_completion(task_id, "pattern_extraction")

            return {
                "operation": "extract_patterns",
                "status": "success",
                "patterns_extracted": result.get("patterns_extracted", 0),
                "top_patterns": result.get("top_patterns", []),
                "engagement_insights": result.get("engagement_insights", {}),
                "processing_time_ms": result.get("processing_time_ms", 0),
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Pattern extraction failed: {e}")

    def _predict_engagement(self, context: Context) -> Dict[str, Any]:
        """Predict engagement rates for content using viral patterns."""
        self.log.info("Predicting engagement rates using viral engine")

        # Get recent posts that need engagement prediction
        payload = {
            "batch_size": self.batch_size,
            "use_viral_patterns": True,
            "include_confidence_score": True,
            "min_engagement_threshold": self.min_engagement_threshold,
        }

        try:
            response = self.session.post(
                f"{self.viral_engine_url}/predict/engagement",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()

            # Calculate prediction metrics
            predictions = result.get("predictions", [])
            avg_predicted_engagement = (
                sum(p.get("predicted_engagement", 0) for p in predictions)
                / len(predictions)
                if predictions
                else 0
            )
            high_potential_posts = [
                p for p in predictions if p.get("predicted_engagement", 0) > 0.06
            ]

            self.log.info(
                f"Engagement prediction completed: {len(predictions)} posts analyzed"
            )
            self.log.info(
                f"Average predicted engagement: {avg_predicted_engagement:.2%}"
            )
            self.log.info(f"High potential posts (>6%): {len(high_potential_posts)}")

            return {
                "operation": "predict_engagement",
                "status": "success",
                "total_predictions": len(predictions),
                "average_predicted_engagement": avg_predicted_engagement,
                "high_potential_posts": len(high_potential_posts),
                "predictions": predictions[:10],  # Return top 10 for visibility
                "processing_time_ms": result.get("processing_time_ms", 0),
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Engagement prediction failed: {e}")

    def _calculate_viral_coefficient(self, context: Context) -> Dict[str, Any]:
        """Calculate viral coefficient for recent content."""
        self.log.info("Calculating viral coefficient for content performance")

        payload = {
            "analysis_period_hours": 168,  # 7 days
            "include_breakdown": True,
            "segment_by_persona": True,
            "min_sample_size": 10,
        }

        try:
            response = self.session.post(
                f"{self.viral_engine_url}/analyze/viral-coefficient",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()

            viral_coefficient = result.get("viral_coefficient", 0.0)
            target_coefficient = 1.2  # Target for viral growth

            self.log.info(f"Viral coefficient calculated: {viral_coefficient:.3f}")
            self.log.info(f"Target coefficient: {target_coefficient:.3f}")

            # Determine if performance is meeting viral growth targets
            performance_status = (
                "excellent"
                if viral_coefficient >= target_coefficient
                else "needs_improvement"
            )

            return {
                "operation": "calculate_viral_coefficient",
                "status": "success",
                "viral_coefficient": viral_coefficient,
                "target_coefficient": target_coefficient,
                "performance_status": performance_status,
                "coefficient_breakdown": result.get("breakdown", {}),
                "persona_analysis": result.get("persona_analysis", {}),
                "recommendations": result.get("recommendations", []),
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Viral coefficient calculation failed: {e}")

    def _optimize_parameters(self, context: Context) -> Dict[str, Any]:
        """Optimize viral engine parameters based on recent performance."""
        self.log.info("Optimizing viral engine parameters")

        # Get recent performance metrics
        try:
            metrics_response = self.session.get(
                f"{self.viral_engine_url}/metrics/recent",
                timeout=30,
                verify=self.verify_ssl,
            )
            metrics_response.raise_for_status()
            current_metrics = metrics_response.json()

            # Calculate optimization parameters
            current_engagement = current_metrics.get("average_engagement_rate", 0.0)
            target_engagement = 0.06  # 6% target

            optimization_payload = {
                "current_performance": current_metrics,
                "target_engagement_rate": target_engagement,
                "optimization_strategy": "aggressive"
                if current_engagement < target_engagement * 0.8
                else "conservative",
                "adjust_pattern_weights": True,
                "update_scoring_algorithm": True,
            }

            response = self.session.post(
                f"{self.viral_engine_url}/optimize/parameters",
                json=optimization_payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()

            self.log.info("Parameter optimization completed")
            self.log.info(f"Optimization strategy: {result.get('strategy', 'unknown')}")

            return {
                "operation": "optimize_parameters",
                "status": "success",
                "current_engagement": current_engagement,
                "target_engagement": target_engagement,
                "optimization_strategy": result.get("strategy"),
                "parameters_updated": result.get("parameters_updated", []),
                "expected_improvement": result.get("expected_improvement", 0.0),
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Parameter optimization failed: {e}")

    def _analyze_performance(self, context: Context) -> Dict[str, Any]:
        """Analyze current viral content performance and trends."""
        self.log.info("Analyzing viral content performance")

        payload = {
            "analysis_period_days": 7,
            "include_trends": True,
            "segment_by_time": True,
            "include_predictions": True,
            "calculate_roi": True,
        }

        try:
            response = self.session.post(
                f"{self.viral_engine_url}/analyze/performance",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()

            # Extract key performance indicators
            kpis = result.get("kpis", {})
            engagement_rate = kpis.get("engagement_rate", 0.0)
            cost_per_follow = kpis.get("cost_per_follow", 0.0)
            viral_coefficient = kpis.get("viral_coefficient", 0.0)

            # Determine overall performance status
            performance_score = self._calculate_performance_score(
                engagement_rate, cost_per_follow, viral_coefficient
            )

            self.log.info("Performance analysis completed")
            self.log.info(f"Engagement rate: {engagement_rate:.2%}")
            self.log.info(f"Cost per follow: ${cost_per_follow:.3f}")
            self.log.info(f"Viral coefficient: {viral_coefficient:.3f}")
            self.log.info(f"Performance score: {performance_score:.1f}/100")

            return {
                "operation": "analyze_performance",
                "status": "success",
                "kpis": kpis,
                "performance_score": performance_score,
                "trends": result.get("trends", {}),
                "predictions": result.get("predictions", {}),
                "roi_analysis": result.get("roi_analysis", {}),
                "recommendations": result.get("recommendations", []),
                "completion_time": datetime.now().isoformat(),
            }

        except requests.exceptions.RequestException as e:
            raise AirflowException(f"Performance analysis failed: {e}")

    def _calculate_performance_score(
        self, engagement_rate: float, cost_per_follow: float, viral_coefficient: float
    ) -> float:
        """Calculate overall performance score based on KPIs."""
        # Target values
        target_engagement = 0.06
        target_cost = 0.01
        target_viral_coeff = 1.2

        # Calculate individual scores (0-100)
        engagement_score = min(100, (engagement_rate / target_engagement) * 100)
        cost_score = min(100, (target_cost / max(cost_per_follow, 0.001)) * 100)
        viral_score = min(100, (viral_coefficient / target_viral_coeff) * 100)

        # Weighted average (engagement is most important)
        performance_score = (
            (engagement_score * 0.5) + (cost_score * 0.3) + (viral_score * 0.2)
        )

        return min(100, max(0, performance_score))

    def _wait_for_task_completion(
        self, task_id: str, operation_type: str
    ) -> Dict[str, Any]:
        """Wait for async task completion."""
        max_wait_time = self.timeout
        check_interval = 10
        start_time = time.time()

        self.log.info(f"Waiting for {operation_type} task completion: {task_id}")

        while time.time() - start_time < max_wait_time:
            try:
                response = self.session.get(
                    f"{self.viral_engine_url}/task/status/{task_id}",
                    timeout=30,
                    verify=self.verify_ssl,
                )

                if response.status_code == 200:
                    task_status = response.json()

                    if task_status.get("status") == "completed":
                        return task_status.get("result", {})
                    elif task_status.get("status") == "failed":
                        raise AirflowException(
                            f"Task {task_id} failed: {task_status.get('error', 'Unknown error')}"
                        )

                time.sleep(check_interval)

            except Exception as e:
                self.log.warning(f"Failed to check task status: {e}")
                time.sleep(check_interval)

        raise AirflowException(f"Task {task_id} timeout after {max_wait_time} seconds")

    def on_kill(self) -> None:
        """Clean up resources when task is killed."""
        if hasattr(self, "session"):
            self.session.close()
        self.log.info("ViralEngineOperator killed, cleaned up resources")
