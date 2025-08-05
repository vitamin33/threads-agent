"""
Metrics Collector Operator for Airflow (CRA-284)

Custom operator for collecting and aggregating metrics from all viral learning services.
Handles performance monitoring, KPI calculation, and business metrics tracking.

Epic: E7 - Viral Learning Flywheel
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict

import requests
from requests.adapters import HTTPAdapter, Retry

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.utils.context import Context


class MetricsCollectorOperator(BaseOperator):
    """
    Custom Airflow operator for comprehensive metrics collection across services.

    This operator provides:
    - Multi-service metrics aggregation
    - KPI calculation and tracking
    - Business metrics computation
    - Performance trend analysis
    - Alerting threshold checks

    Args:
        service_urls: Dictionary mapping service names to their base URLs
        metrics_types: List of metric types to collect (default: all)
        aggregation_window_hours: Hours of data to aggregate (default: 24)
        include_prometheus_metrics: Whether to fetch Prometheus metrics (default: True)
        kpi_thresholds: Dictionary of KPI thresholds for alerting
        timeout: Request timeout in seconds (default: 300)

    Example:
        ```python
        collect_metrics = MetricsCollectorOperator(
            task_id='collect_viral_learning_metrics',
            service_urls={
                'orchestrator': 'http://orchestrator:8080',
                'viral_scraper': 'http://viral-scraper:8080',
                'viral_engine': 'http://viral-engine:8080'
            },
            metrics_types=['engagement', 'cost', 'performance'],
            kpi_thresholds={
                'engagement_rate': 0.06,
                'cost_per_follow': 0.01
            },
            dag=dag
        )
        ```
    """

    template_fields = [
        "service_urls",
        "metrics_types",
        "aggregation_window_hours",
        "kpi_thresholds",
    ]

    ui_color = "#a9dfbf"
    ui_fgcolor = "#145a32"

    @apply_defaults
    def __init__(
        self,
        service_urls: Dict[str, str],
        metrics_types: Optional[List[str]] = None,
        aggregation_window_hours: int = 24,
        include_prometheus_metrics: bool = True,
        kpi_thresholds: Optional[Dict[str, float]] = None,
        timeout: int = 300,
        verify_ssl: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.service_urls = {k: v.rstrip("/") for k, v in service_urls.items()}
        self.metrics_types = metrics_types or ["all"]
        self.aggregation_window_hours = aggregation_window_hours
        self.include_prometheus_metrics = include_prometheus_metrics
        self.kpi_thresholds = kpi_thresholds or {
            "engagement_rate": 0.06,
            "cost_per_follow": 0.01,
            "viral_coefficient": 1.2,
            "response_time_ms": 1000,
            "error_rate": 0.01,
        }
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Configure HTTP session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def execute(self, context: Context) -> Dict[str, Any]:
        """
        Execute metrics collection across all configured services.

        Returns:
            Dict containing aggregated metrics and analysis
        """
        self.log.info(
            f"Starting metrics collection from {len(self.service_urls)} services"
        )

        # Initialize results structure
        results = {
            "collection_timestamp": datetime.now().isoformat(),
            "aggregation_window_hours": self.aggregation_window_hours,
            "services": {},
            "aggregated_metrics": {},
            "kpis": {},
            "alerts": [],
            "trends": {},
            "summary": {},
        }

        # Collect metrics from each service
        for service_name, service_url in self.service_urls.items():
            try:
                service_metrics = self._collect_service_metrics(
                    service_name, service_url
                )
                results["services"][service_name] = service_metrics
            except Exception as e:
                self.log.error(f"Failed to collect metrics from {service_name}: {e}")
                results["services"][service_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

        # Aggregate metrics across services
        results["aggregated_metrics"] = self._aggregate_metrics(results["services"])

        # Calculate KPIs
        results["kpis"] = self._calculate_kpis(results["aggregated_metrics"])

        # Check thresholds and generate alerts
        results["alerts"] = self._check_thresholds(results["kpis"])

        # Analyze trends
        results["trends"] = self._analyze_trends(results["aggregated_metrics"])

        # Generate summary
        results["summary"] = self._generate_summary(results)

        self.log.info(
            f"Metrics collection completed: {len(results['kpis'])} KPIs calculated"
        )

        # Log alerts if any
        if results["alerts"]:
            self.log.warning(
                f"Alerts generated: {len(results['alerts'])} threshold violations"
            )
            for alert in results["alerts"]:
                self.log.warning(
                    f"  - {alert['metric']}: {alert['value']:.4f} ({alert['severity']})"
                )

        return results

    def _collect_service_metrics(
        self, service_name: str, service_url: str
    ) -> Dict[str, Any]:
        """Collect metrics from a single service."""
        self.log.info(f"Collecting metrics from {service_name}")

        service_data = {
            "service_name": service_name,
            "service_url": service_url,
            "status": "unknown",
            "metrics": {},
            "health": {},
            "timestamp": datetime.now().isoformat(),
        }

        # Health check
        try:
            health_response = self.session.get(
                f"{service_url}/health", timeout=10, verify=self.verify_ssl
            )
            service_data["health"] = {
                "status": "healthy"
                if health_response.status_code == 200
                else "unhealthy",
                "response_time_ms": health_response.elapsed.total_seconds() * 1000,
                "status_code": health_response.status_code,
            }
        except Exception as e:
            service_data["health"] = {"status": "unreachable", "error": str(e)}

        # Collect metrics based on service type
        if service_name == "orchestrator":
            service_data["metrics"] = self._collect_orchestrator_metrics(service_url)
        elif service_name == "viral_scraper":
            service_data["metrics"] = self._collect_viral_scraper_metrics(service_url)
        elif service_name == "viral_engine":
            service_data["metrics"] = self._collect_viral_engine_metrics(service_url)
        elif service_name == "viral_pattern_engine":
            service_data["metrics"] = self._collect_viral_pattern_engine_metrics(
                service_url
            )
        elif service_name == "persona_runtime":
            service_data["metrics"] = self._collect_persona_runtime_metrics(service_url)
        else:
            # Generic metrics collection
            service_data["metrics"] = self._collect_generic_metrics(service_url)

        service_data["status"] = "success" if service_data["metrics"] else "partial"

        return service_data

    def _collect_orchestrator_metrics(self, service_url: str) -> Dict[str, Any]:
        """Collect metrics specific to orchestrator service."""
        metrics = {}

        try:
            # Main metrics endpoint
            response = self.session.get(
                f"{service_url}/metrics", timeout=30, verify=self.verify_ssl
            )
            if response.status_code == 200:
                metrics["core"] = response.json()

            # Thompson sampling metrics
            response = self.session.get(
                f"{service_url}/thompson-sampling/metrics",
                params={"hours": self.aggregation_window_hours},
                timeout=30,
                verify=self.verify_ssl,
            )
            if response.status_code == 200:
                metrics["thompson_sampling"] = response.json()

            # Task metrics
            response = self.session.get(
                f"{service_url}/tasks/metrics",
                params={"hours": self.aggregation_window_hours},
                timeout=30,
                verify=self.verify_ssl,
            )
            if response.status_code == 200:
                metrics["tasks"] = response.json()

        except Exception as e:
            self.log.warning(f"Failed to collect orchestrator metrics: {e}")

        return metrics

    def _collect_viral_scraper_metrics(self, service_url: str) -> Dict[str, Any]:
        """Collect metrics specific to viral scraper service."""
        metrics = {}

        try:
            # Scraping metrics
            response = self.session.get(
                f"{service_url}/metrics", timeout=30, verify=self.verify_ssl
            )
            if response.status_code == 200:
                metrics["scraping"] = response.json()

            # Rate limit metrics
            response = self.session.get(
                f"{service_url}/rate-limit/metrics", timeout=30, verify=self.verify_ssl
            )
            if response.status_code == 200:
                metrics["rate_limits"] = response.json()

        except Exception as e:
            self.log.warning(f"Failed to collect viral scraper metrics: {e}")

        return metrics

    def _collect_viral_engine_metrics(self, service_url: str) -> Dict[str, Any]:
        """Collect metrics specific to viral engine service."""
        metrics = {}

        try:
            # Pattern extraction metrics
            response = self.session.get(
                f"{service_url}/metrics/patterns",
                params={"hours": self.aggregation_window_hours},
                timeout=30,
                verify=self.verify_ssl,
            )
            if response.status_code == 200:
                metrics["patterns"] = response.json()

            # Engagement prediction metrics
            response = self.session.get(
                f"{service_url}/metrics/predictions",
                params={"hours": self.aggregation_window_hours},
                timeout=30,
                verify=self.verify_ssl,
            )
            if response.status_code == 200:
                metrics["predictions"] = response.json()

            # Viral coefficient metrics
            response = self.session.get(
                f"{service_url}/metrics/viral-coefficient",
                timeout=30,
                verify=self.verify_ssl,
            )
            if response.status_code == 200:
                metrics["viral_coefficient"] = response.json()

        except Exception as e:
            self.log.warning(f"Failed to collect viral engine metrics: {e}")

        return metrics

    def _collect_viral_pattern_engine_metrics(self, service_url: str) -> Dict[str, Any]:
        """Collect metrics specific to viral pattern engine service."""
        metrics = {}

        try:
            response = self.session.get(
                f"{service_url}/metrics", timeout=30, verify=self.verify_ssl
            )
            if response.status_code == 200:
                metrics["pattern_analysis"] = response.json()

        except Exception as e:
            self.log.warning(f"Failed to collect viral pattern engine metrics: {e}")

        return metrics

    def _collect_persona_runtime_metrics(self, service_url: str) -> Dict[str, Any]:
        """Collect metrics specific to persona runtime service."""
        metrics = {}

        try:
            response = self.session.get(
                f"{service_url}/metrics", timeout=30, verify=self.verify_ssl
            )
            if response.status_code == 200:
                metrics["content_generation"] = response.json()

        except Exception as e:
            self.log.warning(f"Failed to collect persona runtime metrics: {e}")

        return metrics

    def _collect_generic_metrics(self, service_url: str) -> Dict[str, Any]:
        """Collect generic metrics from any service."""
        metrics = {}

        try:
            response = self.session.get(
                f"{service_url}/metrics", timeout=30, verify=self.verify_ssl
            )
            if response.status_code == 200:
                metrics["generic"] = response.json()

        except Exception as e:
            self.log.warning(f"Failed to collect generic metrics: {e}")

        return metrics

    def _aggregate_metrics(self, services_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate metrics across all services."""
        aggregated = defaultdict(lambda: defaultdict(float))
        counts = defaultdict(int)

        # Aggregate numeric metrics
        for service_name, service_data in services_data.items():
            if service_data.get("status") in ["success", "partial"]:
                metrics = service_data.get("metrics", {})

                # Flatten nested metrics
                flattened = self._flatten_dict(metrics)

                for metric_name, metric_value in flattened.items():
                    if isinstance(metric_value, (int, float)):
                        aggregated["sum"][metric_name] += metric_value
                        counts[metric_name] += 1

                        # Track min/max
                        if metric_name not in aggregated["min"]:
                            aggregated["min"][metric_name] = metric_value
                            aggregated["max"][metric_name] = metric_value
                        else:
                            aggregated["min"][metric_name] = min(
                                aggregated["min"][metric_name], metric_value
                            )
                            aggregated["max"][metric_name] = max(
                                aggregated["max"][metric_name], metric_value
                            )

        # Calculate averages
        for metric_name, total in aggregated["sum"].items():
            if counts[metric_name] > 0:
                aggregated["avg"][metric_name] = total / counts[metric_name]

        # Convert defaultdicts to regular dicts
        return {k: dict(v) for k, v in aggregated.items()}

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested dictionary structure."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _calculate_kpis(self, aggregated_metrics: Dict[str, Any]) -> Dict[str, float]:
        """Calculate key performance indicators from aggregated metrics."""
        kpis = {}
        avg_metrics = aggregated_metrics.get("avg", {})

        # Business KPIs
        kpis["engagement_rate"] = avg_metrics.get("core.engagement_rate", 0.0)
        kpis["cost_per_follow"] = avg_metrics.get("core.cost_per_follow", 0.0)
        kpis["viral_coefficient"] = avg_metrics.get(
            "viral_coefficient.coefficient", 0.0
        )
        kpis["revenue_projection_monthly"] = avg_metrics.get(
            "core.revenue_projection_monthly", 0.0
        )

        # Performance KPIs
        kpis["avg_response_time_ms"] = avg_metrics.get("health.response_time_ms", 0.0)
        kpis["pattern_extraction_rate"] = avg_metrics.get(
            "patterns.extraction_rate", 0.0
        )
        kpis["prediction_accuracy"] = avg_metrics.get("predictions.accuracy", 0.0)
        kpis["thompson_sampling_convergence"] = avg_metrics.get(
            "thompson_sampling.convergence_rate", 0.0
        )

        # Operational KPIs
        kpis["task_success_rate"] = avg_metrics.get("tasks.success_rate", 0.0)
        kpis["scraping_success_rate"] = avg_metrics.get("scraping.success_rate", 0.0)
        kpis["rate_limit_violations"] = aggregated_metrics.get("sum", {}).get(
            "rate_limits.violations", 0.0
        )

        # Efficiency KPIs
        kpis["content_generation_speed"] = avg_metrics.get(
            "content_generation.speed_posts_per_hour", 0.0
        )
        kpis["pattern_utilization_rate"] = avg_metrics.get(
            "patterns.utilization_rate", 0.0
        )

        return kpis

    def _check_thresholds(self, kpis: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check KPIs against configured thresholds and generate alerts."""
        alerts = []

        for metric_name, threshold in self.kpi_thresholds.items():
            if metric_name in kpis:
                current_value = kpis[metric_name]

                # Determine if threshold is violated
                if metric_name in [
                    "engagement_rate",
                    "viral_coefficient",
                    "task_success_rate",
                ]:
                    # Higher is better
                    if current_value < threshold:
                        severity = (
                            "critical" if current_value < threshold * 0.5 else "warning"
                        )
                        alerts.append(
                            {
                                "metric": metric_name,
                                "value": current_value,
                                "threshold": threshold,
                                "severity": severity,
                                "type": "below_threshold",
                                "message": f"{metric_name} is {current_value:.4f}, below threshold of {threshold:.4f}",
                            }
                        )
                elif metric_name in [
                    "cost_per_follow",
                    "error_rate",
                    "response_time_ms",
                ]:
                    # Lower is better
                    if current_value > threshold:
                        severity = (
                            "critical" if current_value > threshold * 2 else "warning"
                        )
                        alerts.append(
                            {
                                "metric": metric_name,
                                "value": current_value,
                                "threshold": threshold,
                                "severity": severity,
                                "type": "above_threshold",
                                "message": f"{metric_name} is {current_value:.4f}, above threshold of {threshold:.4f}",
                            }
                        )

        return alerts

    def _analyze_trends(self, aggregated_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metric trends and patterns."""
        trends = {"improving": [], "declining": [], "stable": [], "volatile": []}

        # Simple trend analysis based on min/max/avg
        for metric_name in aggregated_metrics.get("avg", {}).keys():
            avg_val = aggregated_metrics["avg"].get(metric_name, 0)
            min_val = aggregated_metrics["min"].get(metric_name, 0)
            max_val = aggregated_metrics["max"].get(metric_name, 0)

            if avg_val > 0:
                variance_ratio = (max_val - min_val) / avg_val

                if variance_ratio > 0.5:
                    trends["volatile"].append(
                        {
                            "metric": metric_name,
                            "variance_ratio": variance_ratio,
                            "range": [min_val, max_val],
                        }
                    )
                else:
                    trends["stable"].append(
                        {
                            "metric": metric_name,
                            "variance_ratio": variance_ratio,
                            "average": avg_val,
                        }
                    )

        return trends

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of metrics collection."""
        return {
            "total_services": len(results["services"]),
            "healthy_services": sum(
                1
                for s in results["services"].values()
                if s.get("health", {}).get("status") == "healthy"
            ),
            "total_kpis": len(results["kpis"]),
            "critical_alerts": sum(
                1 for a in results["alerts"] if a["severity"] == "critical"
            ),
            "warning_alerts": sum(
                1 for a in results["alerts"] if a["severity"] == "warning"
            ),
            "overall_health": self._calculate_overall_health(results),
            "key_insights": self._generate_insights(results),
        }

    def _calculate_overall_health(self, results: Dict[str, Any]) -> str:
        """Calculate overall system health score."""
        health_score = 100.0

        # Deduct for unhealthy services
        unhealthy_services = sum(
            1
            for s in results["services"].values()
            if s.get("health", {}).get("status") != "healthy"
        )
        health_score -= unhealthy_services * 10

        # Deduct for alerts
        health_score -= len(results["alerts"]) * 5

        # Deduct for poor KPIs
        kpis = results["kpis"]
        if kpis.get("engagement_rate", 0) < 0.04:  # Below 4%
            health_score -= 20
        if kpis.get("cost_per_follow", 1.0) > 0.02:  # Above $0.02
            health_score -= 15

        if health_score >= 90:
            return "excellent"
        elif health_score >= 70:
            return "good"
        elif health_score >= 50:
            return "fair"
        else:
            return "poor"

    def _generate_insights(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from metrics."""
        insights = []
        kpis = results["kpis"]

        # Engagement insights
        if kpis.get("engagement_rate", 0) < 0.06:
            insights.append(
                f"Engagement rate ({kpis['engagement_rate']:.2%}) below target - consider increasing content variety"
            )
        elif kpis.get("engagement_rate", 0) > 0.08:
            insights.append(
                f"Excellent engagement rate ({kpis['engagement_rate']:.2%}) - scale successful patterns"
            )

        # Cost insights
        if kpis.get("cost_per_follow", 1.0) > 0.01:
            insights.append(
                f"Cost per follow (${kpis['cost_per_follow']:.3f}) exceeds target - optimize targeting"
            )

        # Viral coefficient insights
        if kpis.get("viral_coefficient", 0) < 1.0:
            insights.append(
                "Viral coefficient below 1.0 - content not achieving viral growth"
            )
        elif kpis.get("viral_coefficient", 0) > 1.5:
            insights.append("Strong viral coefficient - maintain current strategy")

        # Performance insights
        if kpis.get("avg_response_time_ms", 0) > 1000:
            insights.append(
                "High response times detected - investigate performance bottlenecks"
            )

        # Operational insights
        if kpis.get("task_success_rate", 1.0) < 0.95:
            insights.append(
                "Task failures detected - review error logs and retry mechanisms"
            )

        if not insights:
            insights.append("All metrics within normal ranges - system performing well")

        return insights

    def on_kill(self) -> None:
        """Clean up resources when task is killed."""
        if hasattr(self, "session"):
            self.session.close()
        self.log.info("MetricsCollectorOperator killed, cleaned up resources")
