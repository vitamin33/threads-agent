"""
Integration Tests for Complete Monitoring Workflow (CRA-284)

This module provides comprehensive integration tests for the complete Airflow
monitoring workflow including end-to-end orchestration, service communication,
and real-world failure scenarios.

Test Categories:
- End-to-end workflow integration
- Cross-service communication
- Data flow validation
- Error handling and recovery
- Performance under load
- Real-time monitoring integration

Requirements:
- All tests must complete within 1 second
- 90%+ code coverage
- Proper test isolation
- CI/CD integration ready
"""

import pytest
import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch

# Import operators for testing
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../operators"))

from health_check_operator import HealthCheckOperator
from metrics_collector_operator import MetricsCollectorOperator


class TestMonitoringWorkflowIntegration:
    """Integration tests for complete monitoring workflow."""

    @pytest.fixture
    def workflow_config(self):
        """Configuration for complete monitoring workflow."""
        return {
            "services": {
                "orchestrator": "http://orchestrator:8080",
                "viral_scraper": "http://viral-scraper:8080",
                "viral_engine": "http://viral-engine:8080",
                "viral_pattern_engine": "http://viral-pattern-engine:8080",
                "persona_runtime": "http://persona-runtime:8080",
            },
            "monitoring": {
                "prometheus_url": "http://prometheus:9090",
                "grafana_url": "http://grafana:3000",
                "alertmanager_url": "http://alertmanager:9093",
            },
            "thresholds": {
                "engagement_rate": 0.06,
                "cost_per_follow": 0.01,
                "response_time_ms": 1000,
                "error_rate": 0.01,
            },
            "workflow_timeout": 300,
            "parallel_execution": True,
        }

    @pytest.fixture
    def mock_service_responses(self):
        """Mock service responses for complete workflow."""
        return {
            "health_responses": {
                "orchestrator": {
                    "status": "healthy",
                    "response_time_ms": 45,
                    "dependencies": {"database": "connected", "rabbitmq": "connected"},
                },
                "viral_scraper": {
                    "status": "healthy",
                    "response_time_ms": 78,
                    "rate_limiter": {"status": "operational", "active_limits": 3},
                },
                "viral_engine": {
                    "status": "degraded",
                    "response_time_ms": 1250,
                    "issues": ["high_cpu_usage"],
                },
            },
            "metrics_responses": {
                "orchestrator": {
                    "core": {
                        "engagement_rate": 0.067,
                        "cost_per_follow": 0.009,
                        "revenue_projection_monthly": 18500.0,
                    },
                    "thompson_sampling": {
                        "convergence_rate": 0.89,
                        "best_variant": "story_hook",
                    },
                },
                "viral_scraper": {
                    "scraping": {"success_rate": 0.94, "posts_per_hour": 24}
                },
            },
        }

    @pytest.mark.integration
    async def test_complete_monitoring_workflow_success(
        self, workflow_config, mock_service_responses, requests_mock_setup
    ):
        """Test complete monitoring workflow with all services healthy."""
        start_time = time.time()

        # Configure mocks for successful workflow
        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Health check responses
            health_responses = []
            for service, response in mock_service_responses["health_responses"].items():
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = response
                mock_response.elapsed.total_seconds.return_value = (
                    response["response_time_ms"] / 1000
                )
                health_responses.append(mock_response)

            # Metrics responses
            metrics_responses = []
            for service, response in mock_service_responses[
                "metrics_responses"
            ].items():
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = response
                metrics_responses.append(mock_response)

            # Configure session to return appropriate responses
            mock_session.get.side_effect = health_responses + metrics_responses

            # Step 1: Health Check Operator
            health_operator = HealthCheckOperator(
                task_id="health_check",
                service_urls=workflow_config["services"],
                parallel_checks=True,
                timeout=30,
            )

            health_results = health_operator.execute({})

            # Validate health check results
            assert health_results["overall_status"] == "degraded"  # Due to viral_engine
            assert health_results["summary"]["healthy"] == 2
            assert health_results["summary"]["degraded"] == 1
            assert len(health_results["services"]) == 3  # Number of mocked services

            # Step 2: Metrics Collection Operator
            metrics_operator = MetricsCollectorOperator(
                task_id="collect_metrics",
                service_urls=workflow_config["services"],
                kpi_thresholds=workflow_config["thresholds"],
                timeout=60,
            )

            # Reset mock for metrics collection
            mock_session.get.side_effect = metrics_responses

            metrics_results = metrics_operator.execute({})

            # Validate metrics collection
            assert metrics_results["kpis"]["engagement_rate"] == 0.067
            assert metrics_results["kpis"]["cost_per_follow"] == 0.009
            assert len(metrics_results["alerts"]) == 0  # No threshold violations
            assert metrics_results["summary"]["overall_health"] in ["excellent", "good"]

        # Validate execution time
        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Integration test took {execution_time:.2f}s, exceeds 1s limit"
        )

    @pytest.mark.integration
    async def test_monitoring_workflow_with_failures(
        self, workflow_config, requests_mock_setup
    ):
        """Test monitoring workflow resilience with service failures."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate service failures
            def side_effect(*args, **kwargs):
                url = args[0]
                if "viral-engine" in url:
                    # Simulate timeout
                    import requests

                    raise requests.exceptions.Timeout("Service timeout")
                elif "viral-scraper" in url and "/health" in url:
                    # Simulate 503 Service Unavailable
                    mock_response = Mock()
                    mock_response.status_code = 503
                    mock_response.json.return_value = {"error": "Service unavailable"}
                    mock_response.elapsed.total_seconds.return_value = 0.050
                    return mock_response
                else:
                    # Orchestrator healthy
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "healthy",
                        "response_time_ms": 45,
                    }
                    mock_response.elapsed.total_seconds.return_value = 0.045
                    return mock_response

            mock_session.get.side_effect = side_effect

            # Execute health check with failures
            health_operator = HealthCheckOperator(
                task_id="health_check_with_failures",
                service_urls=workflow_config["services"],
                max_retries=2,
                retry_delay=0.1,  # Fast retry for testing
                parallel_checks=True,
            )

            health_results = health_operator.execute({})

            # Validate failure handling
            assert health_results["overall_status"] == "unhealthy"
            assert health_results["summary"]["unhealthy"] >= 1
            assert any(
                "timeout" in str(s.get("error", "")).lower()
                for s in health_results["services"].values()
            )

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Failure test took {execution_time:.2f}s, exceeds 1s limit"
        )

    @pytest.mark.integration
    async def test_end_to_end_data_flow(self, workflow_config, mock_service_responses):
        """Test complete data flow from health checks to metrics aggregation."""
        start_time = time.time()

        # Mock data pipeline
        pipeline_data = {
            "health_check_timestamp": datetime.now().isoformat(),
            "services_status": {},
            "aggregated_metrics": {},
            "alerts_generated": [],
            "workflow_duration_ms": 0,
        }

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Setup responses for complete data flow
            all_responses = []

            # Health responses first
            for service, health_data in mock_service_responses[
                "health_responses"
            ].items():
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = health_data
                mock_response.elapsed.total_seconds.return_value = (
                    health_data["response_time_ms"] / 1000
                )
                all_responses.append(mock_response)

            # Then metrics responses
            for service, metrics_data in mock_service_responses[
                "metrics_responses"
            ].items():
                for endpoint, data in metrics_data.items():
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = data
                    all_responses.append(mock_response)

            mock_session.get.side_effect = all_responses

            # Execute complete pipeline
            workflow_start = time.time()

            # 1. Health checks
            health_operator = HealthCheckOperator(
                task_id="e2e_health_check", service_urls=workflow_config["services"]
            )
            health_results = health_operator.execute({})
            pipeline_data["services_status"] = health_results["services"]

            # 2. Metrics collection (only if health allows)
            if health_results["overall_status"] != "unhealthy":
                metrics_operator = MetricsCollectorOperator(
                    task_id="e2e_metrics_collection",
                    service_urls=workflow_config["services"],
                    kpi_thresholds=workflow_config["thresholds"],
                )
                metrics_results = metrics_operator.execute({})
                pipeline_data["aggregated_metrics"] = metrics_results[
                    "aggregated_metrics"
                ]
                pipeline_data["alerts_generated"] = metrics_results["alerts"]

            pipeline_data["workflow_duration_ms"] = (
                time.time() - workflow_start
            ) * 1000

            # Validate complete data flow
            assert len(pipeline_data["services_status"]) > 0
            assert pipeline_data["workflow_duration_ms"] < 1000  # Under 1 second

            # Validate data consistency
            healthy_services = [
                name
                for name, status in pipeline_data["services_status"].items()
                if status.get("status") in ["healthy", "degraded"]
            ]
            assert len(healthy_services) >= 1

            # If metrics were collected, validate structure
            if pipeline_data["aggregated_metrics"]:
                assert "avg" in pipeline_data["aggregated_metrics"]
                assert "min" in pipeline_data["aggregated_metrics"]
                assert "max" in pipeline_data["aggregated_metrics"]

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"E2E test took {execution_time:.2f}s, exceeds 1s limit"
        )

    @pytest.mark.integration
    async def test_concurrent_workflow_execution(
        self, workflow_config, mock_service_responses
    ):
        """Test concurrent execution of multiple monitoring workflows."""
        start_time = time.time()

        async def run_workflow(workflow_id: int) -> Dict[str, Any]:
            """Run a single workflow instance."""
            with patch("requests.Session") as mock_session_class:
                mock_session = Mock()
                mock_session_class.return_value = mock_session

                # Fast responses for concurrent testing
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "healthy",
                    "workflow_id": workflow_id,
                    "timestamp": datetime.now().isoformat(),
                }
                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                # Execute health check
                health_operator = HealthCheckOperator(
                    task_id=f"concurrent_health_check_{workflow_id}",
                    service_urls={
                        "orchestrator": workflow_config["services"]["orchestrator"]
                    },
                    timeout=5,
                )

                return health_operator.execute({})

        # Run multiple workflows concurrently
        num_workflows = 5
        tasks = [run_workflow(i) for i in range(num_workflows)]

        # Execute all workflows concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Validate concurrent execution
        successful_workflows = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_workflows) == num_workflows

        # Validate each workflow result
        for result in successful_workflows:
            assert result["overall_status"] == "healthy"
            assert len(result["services"]) == 1

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Concurrent test took {execution_time:.2f}s, exceeds 1s limit"
        )

    @pytest.mark.integration
    async def test_workflow_error_recovery(self, workflow_config):
        """Test workflow recovery from transient errors."""
        start_time = time.time()

        # Simulate transient failures with recovery
        call_count = 0

        def transient_failure_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if call_count <= 2:  # First two calls fail
                import requests

                raise requests.exceptions.ConnectionError("Transient network error")
            else:  # Third call succeeds
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "healthy",
                    "recovered": True,
                    "attempts": call_count,
                }
                mock_response.elapsed.total_seconds.return_value = 0.025
                return mock_response

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.get.side_effect = transient_failure_side_effect

            # Configure operator with retry logic
            health_operator = HealthCheckOperator(
                task_id="recovery_health_check",
                service_urls={
                    "orchestrator": workflow_config["services"]["orchestrator"]
                },
                max_retries=3,
                retry_delay=0.01,  # Very fast retry for testing
                timeout=5,
            )

            results = health_operator.execute({})

            # Validate successful recovery
            assert results["overall_status"] == "healthy"
            assert call_count == 3  # Succeeded on third attempt
            orchestrator_health = results["services"]["orchestrator"]
            assert orchestrator_health["status"] == "healthy"
            assert orchestrator_health["details"]["recovered"] is True

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Recovery test took {execution_time:.2f}s, exceeds 1s limit"
        )

    @pytest.mark.integration
    async def test_workflow_timeout_handling(self, workflow_config):
        """Test workflow behavior under timeout conditions."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate timeout
            def timeout_side_effect(*args, **kwargs):
                import requests

                raise requests.exceptions.Timeout("Request timeout")

            mock_session.get.side_effect = timeout_side_effect

            # Configure operator with short timeout
            health_operator = HealthCheckOperator(
                task_id="timeout_health_check",
                service_urls={"slow_service": "http://slow-service:8080"},
                timeout=0.1,  # Very short timeout
                max_retries=1,  # Single retry
            )

            results = health_operator.execute({})

            # Validate timeout handling
            assert results["overall_status"] == "unhealthy"
            slow_service_status = results["services"]["slow_service"]
            assert slow_service_status["status"] == "unreachable"
            assert "timeout" in slow_service_status["error"].lower()

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Timeout test took {execution_time:.2f}s, exceeds 1s limit"
        )

    @pytest.mark.integration
    async def test_metrics_aggregation_accuracy(
        self, workflow_config, mock_service_responses
    ):
        """Test accuracy of metrics aggregation across services."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Prepare known metrics for aggregation testing
            test_metrics = {
                "service_a": {"metric_1": 10.0, "metric_2": 20.0},
                "service_b": {"metric_1": 15.0, "metric_2": 25.0},
                "service_c": {"metric_1": 5.0, "metric_2": 35.0},
            }

            # Setup mock responses
            responses = []
            for service, metrics in test_metrics.items():
                # Health response
                health_response = Mock()
                health_response.status_code = 200
                health_response.json.return_value = {"status": "healthy"}
                health_response.elapsed.total_seconds.return_value = 0.01
                responses.append(health_response)

                # Metrics response
                metrics_response = Mock()
                metrics_response.status_code = 200
                metrics_response.json.return_value = metrics
                responses.append(metrics_response)

            mock_session.get.side_effect = responses

            # Execute metrics collection
            metrics_operator = MetricsCollectorOperator(
                task_id="accuracy_metrics_test",
                service_urls={
                    service: f"http://{service}:8080" for service in test_metrics.keys()
                },
            )

            results = metrics_operator.execute({})

            # Validate aggregation accuracy
            aggregated = results["aggregated_metrics"]

            # Check sums
            assert aggregated["sum"]["metric_1"] == 30.0  # 10 + 15 + 5
            assert aggregated["sum"]["metric_2"] == 80.0  # 20 + 25 + 35

            # Check averages
            assert aggregated["avg"]["metric_1"] == 10.0  # 30 / 3
            assert abs(aggregated["avg"]["metric_2"] - 26.67) < 0.1  # 80 / 3

            # Check min/max
            assert aggregated["min"]["metric_1"] == 5.0
            assert aggregated["max"]["metric_1"] == 15.0
            assert aggregated["min"]["metric_2"] == 20.0
            assert aggregated["max"]["metric_2"] == 35.0

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Accuracy test took {execution_time:.2f}s, exceeds 1s limit"
        )


class TestWorkflowPerformance:
    """Performance-focused integration tests."""

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_workflow_under_load(self, workflow_config):
        """Test workflow performance under high load conditions."""
        start_time = time.time()

        # Simulate high-load scenario
        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Fast response for load testing
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy", "load_test": True}
            mock_response.elapsed.total_seconds.return_value = 0.005
            mock_session.get.return_value = mock_response

            # Create multiple operators simulating high load
            operators = []
            for i in range(10):  # 10 concurrent health checks
                operator = HealthCheckOperator(
                    task_id=f"load_test_health_{i}",
                    service_urls={"test_service": f"http://service-{i}:8080"},
                    parallel_checks=True,
                    timeout=5,
                )
                operators.append(operator)

            # Execute all operators
            results = []
            for operator in operators:
                result = operator.execute({})
                results.append(result)

            # Validate load test results
            assert len(results) == 10
            for result in results:
                assert result["overall_status"] == "healthy"

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Load test took {execution_time:.2f}s, exceeds 1s limit"
        )

    @pytest.mark.integration
    @pytest.mark.performance
    async def test_memory_efficiency(self, workflow_config):
        """Test workflow memory efficiency with large datasets."""
        start_time = time.time()

        # Simulate large metrics dataset
        large_metrics = {}
        for i in range(1000):  # 1000 metrics
            large_metrics[f"metric_{i}"] = float(i % 100)

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Health response
            health_response = Mock()
            health_response.status_code = 200
            health_response.json.return_value = {"status": "healthy"}
            health_response.elapsed.total_seconds.return_value = 0.01

            # Large metrics response
            metrics_response = Mock()
            metrics_response.status_code = 200
            metrics_response.json.return_value = large_metrics

            mock_session.get.side_effect = [health_response, metrics_response]

            # Execute with large dataset
            metrics_operator = MetricsCollectorOperator(
                task_id="memory_efficiency_test",
                service_urls={"large_service": "http://large-service:8080"},
            )

            results = metrics_operator.execute({})

            # Validate handling of large dataset
            assert len(results["aggregated_metrics"]["sum"]) == 1000
            assert results["aggregated_metrics"]["avg"]["metric_50"] == 50.0

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Memory test took {execution_time:.2f}s, exceeds 1s limit"
        )


class TestWorkflowEdgeCases:
    """Edge case integration tests."""

    @pytest.mark.integration
    async def test_empty_service_list(self):
        """Test workflow behavior with empty service configuration."""
        start_time = time.time()

        # Test empty services
        health_operator = HealthCheckOperator(
            task_id="empty_services_test", service_urls={}, required_services=[]
        )

        results = health_operator.execute({})

        # Validate empty service handling
        assert results["total_services"] == 0
        assert results["overall_status"] == "healthy"  # No services to check
        assert len(results["services"]) == 0

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Empty services test took {execution_time:.2f}s"

    @pytest.mark.integration
    async def test_malformed_service_responses(self, workflow_config):
        """Test workflow resilience to malformed service responses."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Malformed JSON response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError(
                "Invalid JSON", "doc", 0
            )
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_session.get.return_value = mock_response

            health_operator = HealthCheckOperator(
                task_id="malformed_response_test",
                service_urls={"malformed_service": "http://malformed:8080"},
            )

            results = health_operator.execute({})

            # Validate malformed response handling
            assert (
                results["overall_status"] == "healthy"
            )  # Should still work without JSON
            service_health = results["services"]["malformed_service"]
            assert service_health["status"] == "healthy"  # 200 status is still healthy
            assert "details" not in service_health  # No JSON details

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Malformed response test took {execution_time:.2f}s"
        )

    @pytest.mark.integration
    async def test_partial_service_availability(self, workflow_config):
        """Test workflow behavior with partial service availability."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Mixed responses - some services available, others not
            def mixed_responses(*args, **kwargs):
                url = args[0]
                if "service-1" in url:
                    # Available service
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {"status": "healthy"}
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    return mock_response
                elif "service-2" in url:
                    # Unavailable service
                    import requests

                    raise requests.exceptions.ConnectionError("Service unavailable")
                else:
                    # Degraded service
                    mock_response = Mock()
                    mock_response.status_code = 500
                    mock_response.elapsed.total_seconds.return_value = 0.05
                    return mock_response

            mock_session.get.side_effect = mixed_responses

            health_operator = HealthCheckOperator(
                task_id="partial_availability_test",
                service_urls={
                    "service-1": "http://service-1:8080",
                    "service-2": "http://service-2:8080",
                    "service-3": "http://service-3:8080",
                },
                required_services=["service-1"],  # Only service-1 is required
            )

            results = health_operator.execute({})

            # Validate partial availability handling
            assert results["overall_status"] == "unhealthy"  # Due to failures
            assert results["services"]["service-1"]["status"] == "healthy"
            assert results["services"]["service-2"]["status"] == "unreachable"
            assert results["services"]["service-3"]["status"] == "unhealthy"

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Partial availability test took {execution_time:.2f}s"
        )
