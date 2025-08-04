"""
Chaos Tests for Failure Scenarios (CRA-284)

This module provides comprehensive chaos testing to validate system resilience
under various failure conditions and edge cases.

Test Categories:
- Network failures and partitions
- Service degradation and failures
- Resource exhaustion scenarios
- Timeout and latency issues
- Cascading failure scenarios
- Recovery and self-healing tests

Requirements:
- All tests must complete within 1 second
- System must gracefully handle failures
- No data corruption during failures
- Proper error reporting and recovery
"""

import pytest
import time
import random
from typing import List
from unittest.mock import Mock, patch

# Import operators for testing
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../operators"))

from health_check_operator import HealthCheckOperator


class ChaosSimulator:
    """Utility class for simulating various failure scenarios."""

    def __init__(self):
        self.active_failures = {}
        self.failure_history = []

    def simulate_network_partition(self, services: List[str], duration_ms: int = 100):
        """Simulate network partition between services."""

        def network_failure(*args, **kwargs):
            import requests

            raise requests.exceptions.ConnectionError(
                "Network partition: Connection refused"
            )

        return network_failure

    def simulate_service_overload(self, max_response_time_ms: int = 5000):
        """Simulate service overload with slow responses."""

        def overloaded_response(*args, **kwargs):
            # Simulate random response times under overload
            delay = random.uniform(0.1, max_response_time_ms / 1000.0)
            time.sleep(min(delay, 0.2))  # Cap at 200ms for test speed

            mock_response = Mock()
            mock_response.status_code = 503 if delay > 1.0 else 200
            mock_response.json.return_value = {
                "status": "degraded" if delay > 0.5 else "healthy",
                "response_time_ms": delay * 1000,
                "load": "high",
            }
            mock_response.elapsed.total_seconds.return_value = delay
            return mock_response

        return overloaded_response

    def simulate_intermittent_failures(self, failure_rate: float = 0.3):
        """Simulate intermittent service failures."""

        def intermittent_response(*args, **kwargs):
            if random.random() < failure_rate:
                import requests

                raise requests.exceptions.Timeout("Intermittent timeout")
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "healthy",
                    "intermittent": True,
                }
                mock_response.elapsed.total_seconds.return_value = 0.01
                return mock_response

        return intermittent_response

    def simulate_memory_pressure(self):
        """Simulate memory pressure conditions."""

        def memory_pressure_response(*args, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "degraded",
                "memory_usage_percent": 95,
                "gc_pressure": True,
                "warnings": ["high_memory_usage"],
            }
            mock_response.elapsed.total_seconds.return_value = 0.05  # Slower due to GC
            return mock_response

        return memory_pressure_response

    def simulate_cascading_failure(self, services: List[str]):
        """Simulate cascading failure across services."""
        failure_sequence = []

        def cascading_response(*args, **kwargs):
            url = args[0] if args else ""
            service_name = None

            # Identify which service is being called
            for service in services:
                if service in url:
                    service_name = service
                    break

            if not service_name:
                service_name = "unknown"

            # Track failure sequence
            failure_sequence.append(service_name)

            # First service fails immediately
            if service_name == services[0]:
                import requests

                raise requests.exceptions.ConnectionError("Primary service down")

            # Subsequent services fail due to dependency
            if len(failure_sequence) > 1:
                mock_response = Mock()
                mock_response.status_code = 503
                mock_response.json.return_value = {
                    "status": "unhealthy",
                    "error": f"Dependency {services[0]} unavailable",
                    "cascading_failure": True,
                }
                mock_response.elapsed.total_seconds.return_value = 0.01
                return mock_response

            # Shouldn't reach here in normal cascading scenario
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy"}
            mock_response.elapsed.total_seconds.return_value = 0.01
            return mock_response

        return cascading_response


class TestNetworkFailures:
    """Test network failure scenarios."""

    @pytest.mark.chaos
    async def test_complete_network_partition(self):
        """Test complete network partition scenario."""
        start_time = time.time()

        chaos = ChaosSimulator()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate complete network partition
            mock_session.get.side_effect = chaos.simulate_network_partition(
                ["service1", "service2"]
            )

            health_operator = HealthCheckOperator(
                task_id="network_partition_test",
                service_urls={
                    "service1": "http://service1:8080",
                    "service2": "http://service2:8080",
                },
                max_retries=2,
                retry_delay=0.01,  # Fast retry for testing
            )

            results = health_operator.execute({})

            # Should handle network partition gracefully
            assert results["overall_status"] == "unhealthy"
            assert all(
                service["status"] == "unreachable"
                for service in results["services"].values()
            )

            # Should record appropriate errors
            for service_name, service_health in results["services"].items():
                assert "connection" in service_health.get("error", "").lower()

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Network partition test took {execution_time:.2f}s"
        )

    @pytest.mark.chaos
    async def test_partial_network_failure(self):
        """Test partial network failure affecting some services."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate partial network failure
            def partial_failure(*args, **kwargs):
                url = args[0] if args else ""
                if "service1" in url:
                    # Service1 is unreachable
                    import requests

                    raise requests.exceptions.ConnectionError("Network unreachable")
                else:
                    # Service2 is reachable
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "healthy",
                        "partial_failure_test": True,
                    }
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    return mock_response

            mock_session.get.side_effect = partial_failure

            health_operator = HealthCheckOperator(
                task_id="partial_network_failure_test",
                service_urls={
                    "service1": "http://service1:8080",
                    "service2": "http://service2:8080",
                },
                required_services=["service2"],  # Only service2 is required
            )

            results = health_operator.execute({})

            # Should handle partial failure appropriately
            assert results["overall_status"] == "unhealthy"  # service1 failed
            assert results["services"]["service1"]["status"] == "unreachable"
            assert results["services"]["service2"]["status"] == "healthy"

            # Should identify which services are affected
            assert len(results["summary"]["warnings"]) > 0

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Partial network failure test took {execution_time:.2f}s"
        )

    @pytest.mark.chaos
    async def test_intermittent_network_issues(self):
        """Test intermittent network connectivity issues."""
        start_time = time.time()

        chaos = ChaosSimulator()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate intermittent failures (30% failure rate)
            mock_session.get.side_effect = chaos.simulate_intermittent_failures(0.3)

            health_operator = HealthCheckOperator(
                task_id="intermittent_network_test",
                service_urls={"unstable_service": "http://unstable-service:8080"},
                max_retries=3,
                retry_delay=0.001,  # Very fast retry
            )

            results = health_operator.execute({})

            # Should eventually succeed or handle gracefully
            service_health = results["services"]["unstable_service"]
            assert service_health["status"] in ["healthy", "unreachable"]

            # If successful, should show retry attempts
            if service_health["status"] == "healthy":
                assert service_health.get("attempt", 1) >= 1

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Intermittent network test took {execution_time:.2f}s"
        )


class TestServiceDegradation:
    """Test service degradation scenarios."""

    @pytest.mark.chaos
    async def test_service_overload_scenario(self):
        """Test service behavior under heavy load."""
        start_time = time.time()

        chaos = ChaosSimulator()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate overloaded service
            mock_session.get.side_effect = chaos.simulate_service_overload(
                3000
            )  # Up to 3s response

            health_operator = HealthCheckOperator(
                task_id="service_overload_test",
                service_urls={"overloaded_service": "http://overloaded-service:8080"},
                timeout=1,  # 1 second timeout
                performance_thresholds={"overloaded_service": 500},  # 500ms threshold
            )

            results = health_operator.execute({})

            # Should detect degraded performance
            service_health = results["services"]["overloaded_service"]
            assert service_health["status"] in ["degraded", "unhealthy", "unreachable"]

            # Should identify performance issues
            if "performance_warning" in service_health:
                assert "threshold" in service_health["performance_warning"]

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Service overload test took {execution_time:.2f}s"

    @pytest.mark.chaos
    async def test_gradual_service_degradation(self):
        """Test gradual service performance degradation."""
        start_time = time.time()

        degradation_levels = [0.01, 0.05, 0.1, 0.2]  # Increasing response times

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            results_over_time = []

            for delay in degradation_levels:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "degraded" if delay > 0.1 else "healthy",
                    "response_time_ms": delay * 1000,
                    "degradation_level": delay,
                }
                mock_response.elapsed.total_seconds.return_value = delay
                mock_session.get.return_value = mock_response

                health_operator = HealthCheckOperator(
                    task_id=f"gradual_degradation_test_{delay}",
                    service_urls={"degrading_service": "http://degrading-service:8080"},
                    performance_thresholds={
                        "degrading_service": 100
                    },  # 100ms threshold
                )

                result = health_operator.execute({})
                results_over_time.append(result)

            # Should detect degradation pattern
            statuses = [
                r["services"]["degrading_service"]["status"] for r in results_over_time
            ]

            # Should show progression from healthy to degraded
            assert statuses[0] == "healthy"  # 10ms response
            assert statuses[-1] == "degraded"  # 200ms response

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Gradual degradation test took {execution_time:.2f}s"
        )

    @pytest.mark.chaos
    async def test_memory_pressure_degradation(self):
        """Test service degradation under memory pressure."""
        start_time = time.time()

        chaos = ChaosSimulator()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate memory pressure
            mock_session.get.side_effect = chaos.simulate_memory_pressure()

            health_operator = HealthCheckOperator(
                task_id="memory_pressure_test",
                service_urls={
                    "memory_constrained_service": "http://memory-service:8080"
                },
            )

            results = health_operator.execute({})

            # Should detect memory-related degradation
            service_health = results["services"]["memory_constrained_service"]
            assert service_health["status"] == "degraded"

            # Should capture memory-related details
            details = service_health.get("details", {})
            if details:
                assert details.get("memory_usage_percent", 0) > 90
                assert details.get("gc_pressure") is True

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Memory pressure test took {execution_time:.2f}s"


class TestCascadingFailures:
    """Test cascading failure scenarios."""

    @pytest.mark.chaos
    async def test_dependency_chain_failure(self):
        """Test failure propagation through dependency chain."""
        start_time = time.time()

        chaos = ChaosSimulator()
        services = ["primary_service", "secondary_service", "tertiary_service"]

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate cascading failure
            mock_session.get.side_effect = chaos.simulate_cascading_failure(services)

            health_operator = HealthCheckOperator(
                task_id="cascading_failure_test",
                service_urls={
                    service: f"http://{service}:8080" for service in services
                },
                check_dependencies=True,
            )

            results = health_operator.execute({})

            # Should detect cascading failure
            assert results["overall_status"] == "unhealthy"

            # Primary service should be unreachable
            assert results["services"]["primary_service"]["status"] == "unreachable"

            # Dependent services should show dependency failures
            for service in services[1:]:
                service_health = results["services"][service]
                assert service_health["status"] == "unhealthy"
                if "details" in service_health:
                    details = service_health["details"]
                    assert details.get("cascading_failure") is True

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Cascading failure test took {execution_time:.2f}s"
        )

    @pytest.mark.chaos
    async def test_database_failure_impact(self):
        """Test impact of database failure on dependent services."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate database connectivity issues
            def db_failure_response(*args, **kwargs):
                url = args[0] if args else ""

                if "/health/database" in url:
                    # Database health check fails
                    mock_response = Mock()
                    mock_response.status_code = 503
                    mock_response.json.return_value = {
                        "error": "Database connection failed"
                    }
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    return mock_response
                elif "/health" in url:
                    # Main health check shows degraded due to DB
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "degraded",
                        "database": "disconnected",
                        "reason": "Database connectivity issues",
                    }
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    return mock_response
                else:
                    # Other endpoints fail due to DB dependency
                    mock_response = Mock()
                    mock_response.status_code = 503
                    mock_response.json.return_value = {
                        "error": "Service unavailable due to database issues"
                    }
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    return mock_response

            mock_session.get.side_effect = db_failure_response

            health_operator = HealthCheckOperator(
                task_id="database_failure_test",
                service_urls={"db_dependent_service": "http://db-service:8080"},
            )

            results = health_operator.execute({})

            # Should detect database-related degradation
            service_health = results["services"]["db_dependent_service"]
            assert service_health["status"] == "degraded"

            # Should identify database as the issue
            details = service_health.get("details", {})
            if details:
                assert "database" in str(details).lower()

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Database failure test took {execution_time:.2f}s"

    @pytest.mark.chaos
    async def test_circuit_breaker_behavior(self):
        """Test circuit breaker pattern during failures."""
        start_time = time.time()

        failure_count = 0

        def circuit_breaker_response(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1

            if failure_count <= 3:
                # First 3 calls fail (triggers circuit breaker)
                import requests

                raise requests.exceptions.Timeout("Service timeout")
            elif failure_count <= 6:
                # Circuit breaker open - fast failure
                mock_response = Mock()
                mock_response.status_code = 503
                mock_response.json.return_value = {
                    "error": "Circuit breaker open",
                    "state": "open",
                }
                mock_response.elapsed.total_seconds.return_value = 0.001  # Very fast
                return mock_response
            else:
                # Circuit breaker recovery
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "healthy",
                    "circuit_breaker": "closed",
                }
                mock_response.elapsed.total_seconds.return_value = 0.01
                return mock_response

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.get.side_effect = circuit_breaker_response

            # Test multiple attempts to trigger circuit breaker
            for attempt in range(7):
                health_operator = HealthCheckOperator(
                    task_id=f"circuit_breaker_test_{attempt}",
                    service_urls={"circuit_breaker_service": "http://cb-service:8080"},
                    max_retries=1,
                    retry_delay=0.001,
                )

                results = health_operator.execute({})
                service_health = results["services"]["circuit_breaker_service"]

                if attempt < 3:
                    # Initial failures
                    assert service_health["status"] == "unreachable"
                elif attempt < 6:
                    # Circuit breaker open
                    assert service_health["status"] == "unhealthy"
                    if "details" in service_health:
                        assert "circuit" in str(service_health["details"]).lower()
                else:
                    # Recovery
                    assert service_health["status"] == "healthy"

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Circuit breaker test took {execution_time:.2f}s"


class TestResourceExhaustion:
    """Test resource exhaustion scenarios."""

    @pytest.mark.chaos
    async def test_connection_pool_exhaustion(self):
        """Test behavior when connection pool is exhausted."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate connection pool exhaustion
            def connection_exhaustion(*args, **kwargs):
                import requests

                raise requests.exceptions.ConnectionError(
                    "HTTPSConnectionPool: Max retries exceeded"
                )

            mock_session.get.side_effect = connection_exhaustion

            health_operator = HealthCheckOperator(
                task_id="connection_pool_exhaustion_test",
                service_urls={
                    f"service_{i}": f"http://service-{i}:8080" for i in range(5)
                },
                parallel_checks=True,
                max_retries=2,
            )

            results = health_operator.execute({})

            # Should handle connection pool exhaustion gracefully
            assert results["overall_status"] == "unhealthy"

            # All services should be unreachable
            for service_health in results["services"].values():
                assert service_health["status"] == "unreachable"
                assert "connection" in service_health.get("error", "").lower()

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Connection pool exhaustion test took {execution_time:.2f}s"
        )

    @pytest.mark.chaos
    async def test_thread_pool_saturation(self):
        """Test behavior when thread pool is saturated."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate slow responses to saturate thread pool
            def slow_response(*args, **kwargs):
                time.sleep(0.05)  # 50ms delay
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": "healthy", "slow": True}
                mock_response.elapsed.total_seconds.return_value = 0.05
                return mock_response

            mock_session.get.side_effect = slow_response

            # Create many services to saturate thread pool
            many_services = {
                f"service_{i}": f"http://service-{i}:8080" for i in range(20)
            }

            health_operator = HealthCheckOperator(
                task_id="thread_pool_saturation_test",
                service_urls=many_services,
                parallel_checks=True,
                timeout=0.2,  # 200ms timeout
            )

            results = health_operator.execute({})

            # Should handle thread pool saturation
            # Some services might timeout, others should succeed
            successful_services = sum(
                1
                for service in results["services"].values()
                if service["status"] == "healthy"
            )

            # At least some services should succeed despite saturation
            assert successful_services > 0
            assert results["overall_status"] in ["healthy", "degraded", "unhealthy"]

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Thread pool saturation test took {execution_time:.2f}s"
        )

    @pytest.mark.chaos
    async def test_memory_exhaustion_protection(self):
        """Test protection against memory exhaustion attacks."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate response that could cause memory issues
            large_response_data = {
                "status": "healthy",
                "large_data": ["x" * 1000] * 100,  # 100KB of data
                "memory_test": True,
            }

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = large_response_data
            mock_response.elapsed.total_seconds.return_value = 0.01
            mock_session.get.return_value = mock_response

            health_operator = HealthCheckOperator(
                task_id="memory_exhaustion_test",
                service_urls={"memory_intensive_service": "http://memory-service:8080"},
            )

            results = health_operator.execute({})

            # Should handle large responses without crashing
            assert (
                results["services"]["memory_intensive_service"]["status"] == "healthy"
            )

            # Should not leak excessive memory
            # (This would be better tested with actual memory monitoring)
            assert "details" in results["services"]["memory_intensive_service"]

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Memory exhaustion test took {execution_time:.2f}s"
        )


class TestRecoveryScenarios:
    """Test recovery and self-healing scenarios."""

    @pytest.mark.chaos
    async def test_automatic_recovery_after_failure(self):
        """Test automatic recovery after transient failures."""
        start_time = time.time()

        attempt_count = 0

        def recovery_response(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count <= 2:
                # First 2 attempts fail
                import requests

                raise requests.exceptions.ConnectionError("Transient failure")
            else:
                # Recovery on 3rd attempt
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "healthy",
                    "recovered": True,
                    "recovery_attempt": attempt_count,
                }
                mock_response.elapsed.total_seconds.return_value = 0.01
                return mock_response

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_session.get.side_effect = recovery_response

            health_operator = HealthCheckOperator(
                task_id="automatic_recovery_test",
                service_urls={"recovering_service": "http://recovering-service:8080"},
                max_retries=3,
                retry_delay=0.001,  # Fast retry for testing
            )

            results = health_operator.execute({})

            # Should successfully recover
            service_health = results["services"]["recovering_service"]
            assert service_health["status"] == "healthy"
            assert service_health["attempt"] == 3

            # Should indicate recovery
            details = service_health.get("details", {})
            if details:
                assert details.get("recovered") is True

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Automatic recovery test took {execution_time:.2f}s"
        )

    @pytest.mark.chaos
    async def test_gradual_recovery_monitoring(self):
        """Test monitoring of gradual service recovery."""
        start_time = time.time()

        recovery_stages = [
            {"status": "unhealthy", "recovery_percent": 0},
            {"status": "degraded", "recovery_percent": 30},
            {"status": "degraded", "recovery_percent": 70},
            {"status": "healthy", "recovery_percent": 100},
        ]

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            recovery_results = []

            for stage in recovery_stages:
                mock_response = Mock()
                mock_response.status_code = (
                    200 if stage["status"] != "unhealthy" else 503
                )
                mock_response.json.return_value = {
                    "status": stage["status"],
                    "recovery_percent": stage["recovery_percent"],
                    "recovery_stage": True,
                }
                mock_response.elapsed.total_seconds.return_value = 0.01
                mock_session.get.return_value = mock_response

                health_operator = HealthCheckOperator(
                    task_id=f"gradual_recovery_test_{stage['recovery_percent']}",
                    service_urls={
                        "recovering_service": "http://recovering-service:8080"
                    },
                )

                result = health_operator.execute({})
                recovery_results.append(result)

            # Should show recovery progression
            statuses = [
                r["services"]["recovering_service"]["status"] for r in recovery_results
            ]

            assert statuses[0] == "unhealthy"  # Initial failure
            assert statuses[1] == "degraded"  # Partial recovery
            assert statuses[2] == "degraded"  # Still recovering
            assert statuses[3] == "healthy"  # Full recovery

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Gradual recovery test took {execution_time:.2f}s"

    @pytest.mark.chaos
    async def test_partial_recovery_handling(self):
        """Test handling of partial service recovery."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate partial recovery (some endpoints work, others don't)
            def partial_recovery(*args, **kwargs):
                url = args[0] if args else ""

                if "/health" in url and "/health/database" not in url:
                    # Main health endpoint works
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "degraded",
                        "partial_recovery": True,
                        "working_endpoints": ["/health", "/metrics"],
                        "failed_endpoints": ["/health/database"],
                    }
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    return mock_response
                else:
                    # Other endpoints still failing
                    mock_response = Mock()
                    mock_response.status_code = 503
                    mock_response.json.return_value = {
                        "error": "Service partially unavailable"
                    }
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    return mock_response

            mock_session.get.side_effect = partial_recovery

            health_operator = HealthCheckOperator(
                task_id="partial_recovery_test",
                service_urls={
                    "partially_recovered_service": "http://partial-recovery:8080"
                },
            )

            results = health_operator.execute({})

            # Should detect partial recovery
            service_health = results["services"]["partially_recovered_service"]
            assert service_health["status"] == "degraded"

            # Should indicate partial functionality
            details = service_health.get("details", {})
            if details:
                assert details.get("partial_recovery") is True

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Partial recovery test took {execution_time:.2f}s"


class TestComplexChaosScenarios:
    """Test complex multi-failure chaos scenarios."""

    @pytest.mark.chaos
    async def test_multi_service_chaos_scenario(self):
        """Test complex scenario with multiple simultaneous failures."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Complex failure simulation
            def complex_chaos(*args, **kwargs):
                url = args[0] if args else ""

                if "service1" in url:
                    # Service1: Network timeout
                    import requests

                    raise requests.exceptions.Timeout("Network timeout")
                elif "service2" in url:
                    # Service2: Overloaded (slow response)
                    time.sleep(0.1)  # 100ms delay
                    mock_response = Mock()
                    mock_response.status_code = 503
                    mock_response.json.return_value = {
                        "status": "degraded",
                        "error": "Service overloaded",
                    }
                    mock_response.elapsed.total_seconds.return_value = 0.1
                    return mock_response
                elif "service3" in url:
                    # Service3: Authentication failure
                    mock_response = Mock()
                    mock_response.status_code = 401
                    mock_response.json.return_value = {"error": "Authentication failed"}
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    return mock_response
                else:
                    # Service4: Working normally
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "healthy",
                        "chaos_survivor": True,
                    }
                    mock_response.elapsed.total_seconds.return_value = 0.01
                    return mock_response

            mock_session.get.side_effect = complex_chaos

            health_operator = HealthCheckOperator(
                task_id="multi_service_chaos_test",
                service_urls={
                    "service1": "http://service1:8080",
                    "service2": "http://service2:8080",
                    "service3": "http://service3:8080",
                    "service4": "http://service4:8080",
                },
                parallel_checks=True,
                timeout=0.2,  # 200ms timeout
                max_retries=1,
            )

            results = health_operator.execute({})

            # Should handle multiple failure types
            assert results["overall_status"] == "unhealthy"

            # Verify different failure types are detected
            services = results["services"]
            assert services["service1"]["status"] == "unreachable"  # Timeout
            assert services["service2"]["status"] == "unhealthy"  # 503 error
            assert services["service3"]["status"] == "unhealthy"  # 401 error
            assert services["service4"]["status"] == "healthy"  # Working

            # Should have multiple warnings
            assert len(results["summary"]["warnings"]) >= 3

        execution_time = time.time() - start_time
        assert execution_time < 1.0, (
            f"Multi-service chaos test took {execution_time:.2f}s"
        )

    @pytest.mark.chaos
    async def test_stress_test_scenario(self):
        """Test system behavior under extreme stress conditions."""
        start_time = time.time()

        with patch("requests.Session") as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Simulate stress conditions
            stress_level = 0

            def stress_response(*args, **kwargs):
                nonlocal stress_level
                stress_level += 1

                # Increasing stress with each request
                delay = min(stress_level * 0.001, 0.05)  # Max 50ms delay
                time.sleep(delay)

                if stress_level > 50:
                    # High stress - some services fail
                    if random.random() < 0.3:  # 30% failure rate
                        mock_response = Mock()
                        mock_response.status_code = 503
                        mock_response.json.return_value = {
                            "status": "unhealthy",
                            "error": "System under stress",
                            "stress_level": stress_level,
                        }
                        mock_response.elapsed.total_seconds.return_value = delay
                        return mock_response

                # Normal response under stress
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "degraded" if stress_level > 20 else "healthy",
                    "stress_level": stress_level,
                    "performance_impact": delay * 1000,
                }
                mock_response.elapsed.total_seconds.return_value = delay
                return mock_response

            mock_session.get.side_effect = stress_response

            # Create high load scenario
            many_services = {
                f"stress_service_{i}": f"http://stress-{i}:8080" for i in range(100)
            }

            health_operator = HealthCheckOperator(
                task_id="stress_test_scenario",
                service_urls=many_services,
                parallel_checks=True,
                timeout=0.1,  # Short timeout under stress
                performance_thresholds={
                    service: 20 for service in many_services.keys()
                },  # 20ms threshold
            )

            results = health_operator.execute({})

            # Should handle stress gracefully
            assert results["overall_status"] in ["healthy", "degraded", "unhealthy"]

            # Should complete despite stress
            assert len(results["services"]) == 100

            # Should detect performance degradation
            degraded_services = sum(
                1
                for service in results["services"].values()
                if service["status"] == "degraded"
            )

            # Under stress, some services should be degraded
            assert degraded_services > 0

        execution_time = time.time() - start_time
        assert execution_time < 1.0, f"Stress test took {execution_time:.2f}s"
