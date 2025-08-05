"""
Health Check Operator for Airflow (CRA-284)

Custom operator for performing comprehensive health checks across viral learning services.
Handles service availability, dependency checks, and system readiness validation.

Epic: E7 - Viral Learning Flywheel
"""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter, Retry

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.exceptions import AirflowException
from airflow.utils.context import Context


class HealthCheckOperator(BaseOperator):
    """
    Custom Airflow operator for comprehensive health checks across services.

    This operator provides:
    - Multi-service health monitoring
    - Dependency chain validation
    - Resource availability checks
    - Performance baseline validation
    - Readiness gate for workflows

    Args:
        service_urls: Dictionary mapping service names to their base URLs
        required_services: List of services that must be healthy (default: all)
        check_dependencies: Whether to check service dependencies (default: True)
        performance_thresholds: Response time thresholds per service (ms)
        max_retries: Maximum retries for failed health checks (default: 3)
        retry_delay: Delay between retries in seconds (default: 10)
        parallel_checks: Whether to run checks in parallel (default: True)
        fail_on_warning: Whether to fail task on warnings (default: False)
        timeout: Request timeout in seconds (default: 30)

    Example:
        ```python
        health_check = HealthCheckOperator(
            task_id='viral_learning_health_check',
            service_urls={
                'orchestrator': 'http://orchestrator:8080',
                'viral_scraper': 'http://viral-scraper:8080',
                'viral_engine': 'http://viral-engine:8080'
            },
            required_services=['orchestrator', 'viral_scraper'],
            performance_thresholds={
                'orchestrator': 500,
                'viral_scraper': 1000,
                'viral_engine': 2000
            },
            dag=dag
        )
        ```
    """

    template_fields = ["service_urls", "required_services", "performance_thresholds"]

    ui_color = "#f4d03f"
    ui_fgcolor = "#7d6608"

    @apply_defaults
    def __init__(
        self,
        service_urls: Dict[str, str],
        required_services: Optional[List[str]] = None,
        check_dependencies: bool = True,
        performance_thresholds: Optional[Dict[str, int]] = None,
        max_retries: int = 3,
        retry_delay: int = 10,
        parallel_checks: bool = True,
        fail_on_warning: bool = False,
        timeout: int = 30,
        verify_ssl: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.service_urls = {k: v.rstrip("/") for k, v in service_urls.items()}
        self.required_services = required_services or list(service_urls.keys())
        self.check_dependencies = check_dependencies
        self.performance_thresholds = performance_thresholds or {
            "orchestrator": 500,
            "viral_scraper": 1000,
            "viral_engine": 2000,
            "viral_pattern_engine": 2000,
            "persona_runtime": 1500,
        }
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.parallel_checks = parallel_checks
        self.fail_on_warning = fail_on_warning
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Validate required services
        for service in self.required_services:
            if service not in self.service_urls:
                raise ValueError(
                    f"Required service '{service}' not found in service_urls"
                )

        # Configure HTTP session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            status_forcelist=[500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=0.3,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def execute(self, context: Context) -> Dict[str, Any]:
        """
        Execute health checks across all configured services.

        Returns:
            Dict containing health check results and analysis
        """
        self.log.info(f"Starting health checks for {len(self.service_urls)} services")

        # Initialize results
        results = {
            "check_timestamp": datetime.now().isoformat(),
            "total_services": len(self.service_urls),
            "required_services": self.required_services,
            "services": {},
            "summary": {"healthy": 0, "unhealthy": 0, "degraded": 0, "warnings": []},
            "dependencies": {},
            "overall_status": "unknown",
        }

        # Perform health checks
        if self.parallel_checks:
            results["services"] = self._parallel_health_checks()
        else:
            results["services"] = self._sequential_health_checks()

        # Check dependencies if enabled
        if self.check_dependencies:
            results["dependencies"] = self._check_service_dependencies()

        # Analyze results
        self._analyze_results(results)

        # Determine overall status
        results["overall_status"] = self._determine_overall_status(results)

        # Log summary
        self._log_summary(results)

        # Determine if task should fail
        if results["overall_status"] == "unhealthy":
            raise AirflowException(
                f"Health check failed: {results['summary']['unhealthy']} unhealthy services"
            )

        if self.fail_on_warning and results["summary"]["warnings"]:
            raise AirflowException(
                f"Health check has warnings: {', '.join(results['summary']['warnings'])}"
            )

        return results

    def _parallel_health_checks(self) -> Dict[str, Any]:
        """Perform health checks in parallel using thread pool."""
        services_health = {}

        with ThreadPoolExecutor(
            max_workers=min(len(self.service_urls), 10)
        ) as executor:
            # Submit all health check tasks
            future_to_service = {
                executor.submit(self._check_service_health, name, url): name
                for name, url in self.service_urls.items()
            }

            # Collect results as they complete
            for future in as_completed(future_to_service):
                service_name = future_to_service[future]
                try:
                    services_health[service_name] = future.result()
                except Exception as e:
                    self.log.error(f"Health check failed for {service_name}: {e}")
                    services_health[service_name] = {
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }

        return services_health

    def _sequential_health_checks(self) -> Dict[str, Any]:
        """Perform health checks sequentially."""
        services_health = {}

        for service_name, service_url in self.service_urls.items():
            try:
                services_health[service_name] = self._check_service_health(
                    service_name, service_url
                )
            except Exception as e:
                self.log.error(f"Health check failed for {service_name}: {e}")
                services_health[service_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }

        return services_health

    def _check_service_health(
        self, service_name: str, service_url: str
    ) -> Dict[str, Any]:
        """Check health of a single service with retries."""
        self.log.info(f"Checking health of {service_name}")

        for attempt in range(self.max_retries):
            try:
                # Basic health check
                start_time = time.time()
                response = self.session.get(
                    f"{service_url}/health",
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )
                response_time_ms = (time.time() - start_time) * 1000

                # Parse health response
                health_data = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                    "response_time_ms": response_time_ms,
                    "timestamp": datetime.now().isoformat(),
                    "attempt": attempt + 1,
                }

                # Try to get detailed health info
                if response.status_code == 200:
                    try:
                        health_info = response.json()
                        health_data["details"] = health_info

                        # Check for degraded status
                        if health_info.get("status") == "degraded":
                            health_data["status"] = "degraded"
                            health_data["degradation_reason"] = health_info.get(
                                "reason", "Unknown"
                            )
                    except (KeyError, ValueError, TypeError):
                        pass

                # Check performance threshold
                threshold = self.performance_thresholds.get(service_name, 1000)
                if response_time_ms > threshold:
                    health_data["performance_warning"] = (
                        f"Response time {response_time_ms:.0f}ms exceeds threshold {threshold}ms"
                    )
                    if health_data["status"] == "healthy":
                        health_data["status"] = "degraded"

                # Additional checks for specific services
                if (
                    service_name == "orchestrator"
                    and health_data["status"] == "healthy"
                ):
                    health_data["additional_checks"] = (
                        self._check_orchestrator_specifics(service_url)
                    )
                elif (
                    service_name == "viral_scraper"
                    and health_data["status"] == "healthy"
                ):
                    health_data["additional_checks"] = (
                        self._check_viral_scraper_specifics(service_url)
                    )

                # If healthy or degraded, return immediately
                if health_data["status"] in ["healthy", "degraded"]:
                    return health_data

                # If unhealthy and not last attempt, retry
                if attempt < self.max_retries - 1:
                    self.log.warning(
                        f"{service_name} unhealthy, retrying in {self.retry_delay}s..."
                    )
                    time.sleep(self.retry_delay)
                    continue

                return health_data

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    self.log.warning(f"Failed to reach {service_name}, retrying: {e}")
                    time.sleep(self.retry_delay)
                    continue

                return {
                    "status": "unreachable",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "attempts": attempt + 1,
                }

        return {
            "status": "unhealthy",
            "error": "Max retries exceeded",
            "timestamp": datetime.now().isoformat(),
        }

    def _check_orchestrator_specifics(self, service_url: str) -> Dict[str, Any]:
        """Perform orchestrator-specific health checks."""
        specifics = {}

        try:
            # Check database connectivity
            response = self.session.get(
                f"{service_url}/health/database", timeout=10, verify=self.verify_ssl
            )
            specifics["database"] = (
                "connected" if response.status_code == 200 else "disconnected"
            )

            # Check message broker connectivity
            response = self.session.get(
                f"{service_url}/health/rabbitmq", timeout=10, verify=self.verify_ssl
            )
            specifics["rabbitmq"] = (
                "connected" if response.status_code == 200 else "disconnected"
            )

        except Exception as e:
            self.log.warning(f"Failed orchestrator-specific checks: {e}")

        return specifics

    def _check_viral_scraper_specifics(self, service_url: str) -> Dict[str, Any]:
        """Perform viral scraper-specific health checks."""
        specifics = {}

        try:
            # Check rate limiter status
            response = self.session.get(
                f"{service_url}/rate-limit/health", timeout=10, verify=self.verify_ssl
            )
            if response.status_code == 200:
                rate_limit_data = response.json()
                specifics["rate_limiter"] = {
                    "status": "operational",
                    "active_limits": rate_limit_data.get("active_limits", 0),
                }

        except Exception as e:
            self.log.warning(f"Failed viral scraper-specific checks: {e}")

        return specifics

    def _check_service_dependencies(self) -> Dict[str, Any]:
        """Check inter-service dependencies."""
        dependencies = {
            "orchestrator": ["postgres", "rabbitmq"],
            "viral_scraper": ["orchestrator"],
            "viral_engine": ["orchestrator", "viral_scraper"],
            "viral_pattern_engine": ["orchestrator", "viral_engine"],
            "persona_runtime": ["orchestrator", "viral_engine"],
        }

        dependency_status = {}

        for service, deps in dependencies.items():
            if service in self.service_urls:
                service_deps = []

                for dep in deps:
                    if dep in ["postgres", "rabbitmq"]:
                        # Check through orchestrator's health endpoints
                        if "orchestrator" in self.service_urls:
                            orch_health = self._get_service_health_status(
                                "orchestrator"
                            )
                            if (
                                orch_health
                                and orch_health.get("additional_checks", {}).get(dep)
                                == "connected"
                            ):
                                service_deps.append(
                                    {"dependency": dep, "status": "available"}
                                )
                            else:
                                service_deps.append(
                                    {"dependency": dep, "status": "unavailable"}
                                )
                    elif dep in self.service_urls:
                        # Check if dependent service is healthy
                        dep_health = self._get_service_health_status(dep)
                        if dep_health and dep_health.get("status") in [
                            "healthy",
                            "degraded",
                        ]:
                            service_deps.append(
                                {"dependency": dep, "status": "available"}
                            )
                        else:
                            service_deps.append(
                                {"dependency": dep, "status": "unavailable"}
                            )

                dependency_status[service] = {
                    "dependencies": service_deps,
                    "all_available": all(
                        d["status"] == "available" for d in service_deps
                    ),
                }

        return dependency_status

    def _get_service_health_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get cached health status for a service."""
        # This would be populated during the health check phase
        # For now, return None to indicate we need to implement caching
        return None

    def _analyze_results(self, results: Dict[str, Any]) -> None:
        """Analyze health check results and populate summary."""
        for service_name, health in results["services"].items():
            status = health.get("status", "unknown")

            if status == "healthy":
                results["summary"]["healthy"] += 1
            elif status == "degraded":
                results["summary"]["degraded"] += 1
                if "performance_warning" in health:
                    results["summary"]["warnings"].append(
                        f"{service_name}: {health['performance_warning']}"
                    )
                if "degradation_reason" in health:
                    results["summary"]["warnings"].append(
                        f"{service_name}: {health['degradation_reason']}"
                    )
            else:
                results["summary"]["unhealthy"] += 1

            # Check if this is a required service
            if service_name in self.required_services and status not in [
                "healthy",
                "degraded",
            ]:
                results["summary"]["warnings"].append(
                    f"Required service {service_name} is {status}"
                )

        # Check dependencies
        if results.get("dependencies"):
            for service, dep_info in results["dependencies"].items():
                if not dep_info["all_available"]:
                    unavailable = [
                        d["dependency"]
                        for d in dep_info["dependencies"]
                        if d["status"] != "available"
                    ]
                    results["summary"]["warnings"].append(
                        f"{service} missing dependencies: {', '.join(unavailable)}"
                    )

    def _determine_overall_status(self, results: Dict[str, Any]) -> str:
        """Determine overall system health status."""
        summary = results["summary"]

        # Check required services
        required_unhealthy = any(
            results["services"].get(service, {}).get("status")
            not in ["healthy", "degraded"]
            for service in self.required_services
        )

        if required_unhealthy or summary["unhealthy"] > 0:
            return "unhealthy"
        elif summary["degraded"] > 0 or summary["warnings"]:
            return "degraded"
        else:
            return "healthy"

    def _log_summary(self, results: Dict[str, Any]) -> None:
        """Log health check summary."""
        summary = results["summary"]
        overall = results["overall_status"]

        self.log.info(f"Health check complete: {overall.upper()}")
        self.log.info(
            f"  Healthy services: {summary['healthy']}/{results['total_services']}"
        )

        if summary["degraded"] > 0:
            self.log.warning(f"  Degraded services: {summary['degraded']}")

        if summary["unhealthy"] > 0:
            self.log.error(f"  Unhealthy services: {summary['unhealthy']}")

        if summary["warnings"]:
            self.log.warning("  Warnings:")
            for warning in summary["warnings"]:
                self.log.warning(f"    - {warning}")

        # Log individual service status
        self.log.info("Service Status:")
        for service, health in results["services"].items():
            status = health.get("status", "unknown")
            response_time = health.get("response_time_ms", 0)
            marker = (
                "✓" if status == "healthy" else "⚠" if status == "degraded" else "✗"
            )

            msg = f"  {marker} {service}: {status}"
            if response_time > 0:
                msg += f" ({response_time:.0f}ms)"

            if status == "healthy":
                self.log.info(msg)
            elif status == "degraded":
                self.log.warning(msg)
            else:
                self.log.error(msg)

    def on_kill(self) -> None:
        """Clean up resources when task is killed."""
        if hasattr(self, "session"):
            self.session.close()
        self.log.info("HealthCheckOperator killed, cleaned up resources")
