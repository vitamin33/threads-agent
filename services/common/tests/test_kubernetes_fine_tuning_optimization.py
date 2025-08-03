"""Unit tests for Kubernetes-specific fine-tuning optimizations.

This module provides focused unit tests for the Kubernetes optimization components:
1. Connection pool management
2. Circuit breaker patterns
3. Resource configuration
4. Health checks and monitoring
5. Performance metrics collection
"""

import asyncio
import pytest
import time
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from services.common.kubernetes_fine_tuning_optimization import (
    KubernetesOptimizedPipeline,
    ConnectionPoolManager,
    CircuitBreaker,
    KubernetesResourceConfig,
    get_kubernetes_deployment_yaml,
)


class TestKubernetesResourceConfig:
    """Test Kubernetes resource configuration."""

    def test_default_resource_configuration(self):
        """Test default resource configuration values."""
        config = KubernetesResourceConfig()

        assert config.memory_request == "512Mi"
        assert config.memory_limit == "2Gi"
        assert config.cpu_request == "500m"
        assert config.cpu_limit == "2000m"
        assert config.max_replicas == 5
        assert config.min_replicas == 1
        assert config.target_cpu_utilization == 70
        assert config.target_memory_utilization == 80

    def test_custom_resource_configuration(self):
        """Test custom resource configuration."""
        config = KubernetesResourceConfig(
            memory_request="1Gi",
            memory_limit="4Gi",
            cpu_request="1000m",
            cpu_limit="4000m",
            max_replicas=10,
            min_replicas=2,
            target_cpu_utilization=60,
            target_memory_utilization=70,
        )

        assert config.memory_request == "1Gi"
        assert config.memory_limit == "4Gi"
        assert config.cpu_request == "1000m"
        assert config.cpu_limit == "4000m"
        assert config.max_replicas == 10
        assert config.min_replicas == 2
        assert config.target_cpu_utilization == 60
        assert config.target_memory_utilization == 70


class TestConnectionPoolManager:
    """Test connection pool management for database and Redis."""

    @pytest.fixture
    def connection_manager(self):
        """Create a connection pool manager for testing."""
        return ConnectionPoolManager()

    async def test_connection_pool_initialization(self, connection_manager):
        """Test connection pool initialization with optimized settings."""
        # When asyncpg/aioredis are not available, it should use mock pools
        await connection_manager.initialize_pools()

        # Verify mock pools were created
        assert hasattr(connection_manager.db_pool, "__aenter__")  # AsyncMock
        assert hasattr(connection_manager.redis_pool, "__aenter__")  # AsyncMock

        # Verify pool stats are initialized
        stats = connection_manager.get_pool_stats()
        assert stats["db_connections_active"] == 0
        assert stats["db_connections_idle"] == 0
        assert stats["redis_connections_active"] == 0
        assert stats["redis_connections_idle"] == 0

    async def test_database_connection_context_manager(self, connection_manager):
        """Test database connection context manager."""
        # Initialize pools to get mock pools
        await connection_manager.initialize_pools()

        # Test context manager usage with mock pool
        async with connection_manager.get_db_connection() as conn:
            # With mock pool, it yields the pool itself
            assert conn is connection_manager.db_pool
            assert connection_manager._pool_stats["db_connections_active"] == 1

        # Verify cleanup
        assert connection_manager._pool_stats["db_connections_active"] == 0
        assert connection_manager._pool_stats["db_connections_idle"] == 1

    async def test_redis_connection_context_manager(self, connection_manager):
        """Test Redis connection context manager."""
        # Initialize pools to get mock pools
        await connection_manager.initialize_pools()

        # Test context manager usage with mock pool
        async with connection_manager.get_redis_connection() as redis_conn:
            # With mock pool, it yields the pool itself
            assert redis_conn is connection_manager.redis_pool
            assert connection_manager._pool_stats["redis_connections_active"] == 1

        # Verify cleanup
        assert connection_manager._pool_stats["redis_connections_active"] == 0
        assert connection_manager._pool_stats["redis_connections_idle"] == 1

    def test_pool_statistics_tracking(self, connection_manager):
        """Test connection pool statistics tracking."""
        # Initial state
        stats = connection_manager.get_pool_stats()
        assert stats["db_connections_active"] == 0
        assert stats["db_connections_idle"] == 0
        assert stats["redis_connections_active"] == 0
        assert stats["redis_connections_idle"] == 0

        # Manually update stats to test tracking
        connection_manager._pool_stats["db_connections_active"] = 5
        connection_manager._pool_stats["redis_connections_active"] = 3

        updated_stats = connection_manager.get_pool_stats()
        assert updated_stats["db_connections_active"] == 5
        assert updated_stats["redis_connections_active"] == 3

        # Verify stats are copied (not referenced)
        assert updated_stats is not connection_manager._pool_stats


class TestCircuitBreaker:
    """Test circuit breaker pattern implementation."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization with default and custom parameters."""
        # Default parameters
        cb = CircuitBreaker()
        assert cb.failure_threshold == 5
        assert cb.timeout == 60.0
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.state == "CLOSED"

        # Custom parameters
        cb_custom = CircuitBreaker(failure_threshold=3, timeout=30.0)
        assert cb_custom.failure_threshold == 3
        assert cb_custom.timeout == 30.0
        assert cb_custom.state == "CLOSED"

    async def test_circuit_breaker_success_flow(self):
        """Test circuit breaker with successful function calls."""
        cb = CircuitBreaker(failure_threshold=3, timeout=10.0)

        async def successful_function(value):
            return f"success: {value}"

        # Multiple successful calls should work
        for i in range(5):
            result = await cb.call(successful_function, i)
            assert result == f"success: {i}"
            assert cb.state == "CLOSED"
            assert cb.failure_count == 0

    async def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opening after failure threshold."""
        cb = CircuitBreaker(failure_threshold=3, timeout=1.0)

        async def failing_function():
            raise ValueError("Service error")

        # Test failures leading to open state
        for i in range(3):
            with pytest.raises(ValueError, match="Service error"):
                await cb.call(failing_function)

            assert cb.failure_count == i + 1
            if i < 2:
                assert cb.state == "CLOSED"
            else:
                assert cb.state == "OPEN"

        # Verify circuit breaker rejects calls when open
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb.call(failing_function)

    async def test_circuit_breaker_half_open_transition(self):
        """Test circuit breaker half-open state and recovery."""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)

        async def failing_function():
            raise RuntimeError("Service down")

        async def successful_function():
            return "recovered"

        # Trigger circuit breaker opening
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(failing_function)

        assert cb.state == "OPEN"

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Next successful call should transition to half-open then closed
        result = await cb.call(successful_function)
        assert result == "recovered"
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    async def test_circuit_breaker_half_open_failure(self):
        """Test circuit breaker re-opening from half-open state on failure."""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)

        async def failing_function():
            raise ConnectionError("Still failing")

        # Open circuit breaker
        for _ in range(2):
            with pytest.raises(ConnectionError):
                await cb.call(failing_function)

        assert cb.state == "OPEN"

        # Wait for timeout to enable half-open
        await asyncio.sleep(0.15)

        # Failure in half-open should re-open circuit
        with pytest.raises(ConnectionError):
            await cb.call(failing_function)

        assert cb.state == "OPEN"
        assert cb.failure_count == 3  # Incremented from half-open failure

    async def test_circuit_breaker_with_async_timeout(self):
        """Test circuit breaker with async function that times out."""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)

        async def slow_function():
            await asyncio.sleep(0.5)  # Simulate slow operation
            return "slow result"

        async def timeout_wrapper():
            return await asyncio.wait_for(slow_function(), timeout=0.1)

        # Test that timeouts are treated as failures
        for _ in range(2):
            with pytest.raises(asyncio.TimeoutError):
                await cb.call(timeout_wrapper)

        assert cb.state == "OPEN"
        assert cb.failure_count == 2


class TestKubernetesOptimizedPipeline:
    """Test the complete Kubernetes-optimized pipeline."""

    @pytest.fixture
    def k8s_config(self):
        """Kubernetes resource configuration for testing."""
        return KubernetesResourceConfig(
            memory_request="256Mi",
            memory_limit="1Gi",
            cpu_request="250m",
            cpu_limit="1000m",
        )

    @pytest.fixture
    def k8s_pipeline(self, k8s_config):
        """Kubernetes-optimized pipeline for testing."""
        return KubernetesOptimizedPipeline(k8s_config)

    async def test_pipeline_initialization(self, k8s_pipeline, k8s_config):
        """Test pipeline initialization with all components."""
        assert k8s_pipeline.resource_config == k8s_config
        assert isinstance(k8s_pipeline.connection_manager, ConnectionPoolManager)
        assert isinstance(k8s_pipeline.openai_circuit_breaker, CircuitBreaker)
        assert isinstance(k8s_pipeline.mlflow_circuit_breaker, CircuitBreaker)

        # Test circuit breaker configurations
        assert k8s_pipeline.openai_circuit_breaker.failure_threshold == 3
        assert k8s_pipeline.openai_circuit_breaker.timeout == 120
        assert k8s_pipeline.mlflow_circuit_breaker.failure_threshold == 5
        assert k8s_pipeline.mlflow_circuit_breaker.timeout == 60

    async def test_optimized_training_data_collection(self, k8s_pipeline):
        """Test optimized training data collection with chunked processing."""
        mock_connection = AsyncMock()

        # Mock database query result
        mock_rows = []
        for i in range(2500):  # Test chunking with 2500 rows
            mock_rows.append(
                {
                    "id": i,
                    "persona_id": "test-persona",
                    "hook": f"Hook content {i}",
                    "body": f"Body content {i}",
                    "engagement_rate": 0.06 + (i % 10) * 0.01,
                    "ts": datetime.now() - timedelta(hours=i % 24),
                    "tokens_used": 100 + (i % 50),
                }
            )

        mock_connection.fetch.return_value = mock_rows

        with patch.object(
            k8s_pipeline.connection_manager, "get_db_connection"
        ) as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection

            result = await k8s_pipeline.collect_training_data_optimized(
                engagement_threshold=0.06, days_back=7
            )

        # Verify data collection
        assert len(result["hook_examples"]) == 2500
        assert len(result["body_examples"]) == 2500

        # Verify chunking metadata
        assert result["metadata"]["total_records"] == 2500
        assert result["metadata"]["chunk_size"] == 1000

        # Verify data format
        hook_example = result["hook_examples"][0]
        assert "messages" in hook_example
        assert len(hook_example["messages"]) == 2
        assert hook_example["messages"][0]["role"] == "user"
        assert hook_example["messages"][1]["role"] == "assistant"
        assert hook_example["engagement_rate"] >= 0.06

    async def test_fine_tuning_with_circuit_breaker_protection(self, k8s_pipeline):
        """Test fine-tuning operation with circuit breaker protection."""
        training_data = {
            "hook_examples": [{"messages": [{"role": "user", "content": "test"}]}],
            "body_examples": [{"messages": [{"role": "user", "content": "test"}]}],
        }

        # Mock successful OpenAI operations
        mock_client = AsyncMock()
        mock_file_upload = Mock()
        mock_file_upload.id = "file-test-123"
        mock_job = Mock()
        mock_job.id = "ftjob-test-123"

        mock_client.files.create.return_value = mock_file_upload
        mock_client.fine_tuning.jobs.create.return_value = mock_job

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            result = await k8s_pipeline.start_fine_tuning_with_circuit_breaker(
                training_data
            )

        # Verify successful operation
        assert result["job_id"] == "ftjob-test-123"
        assert result["status"] == "training"
        assert result["training_examples"] == 2

        # Verify circuit breaker remains closed
        assert k8s_pipeline.openai_circuit_breaker.state == "CLOSED"
        assert k8s_pipeline.openai_circuit_breaker.failure_count == 0

    async def test_redis_caching_operations(self, k8s_pipeline):
        """Test Redis caching operations with connection pooling."""
        test_metrics = {
            "engagement_rate": 0.08,
            "cost_efficiency": 0.15,
            "quality_score": 0.85,
        }

        mock_redis_client = AsyncMock()

        with patch.object(
            k8s_pipeline.connection_manager, "get_redis_connection"
        ) as mock_get_redis:
            mock_get_redis.return_value.__aenter__.return_value = mock_redis_client

            # Test caching metrics
            await k8s_pipeline.cache_evaluation_metrics(
                "candidate", "test-ab-123", test_metrics
            )

            # Verify Redis setex call
            mock_redis_client.setex.assert_called_once()
            cache_key, ttl, cached_data = mock_redis_client.setex.call_args[0]
            assert cache_key == "model_metrics:test-ab-123:candidate"
            assert ttl == 300  # 5 minutes
            assert json.loads(cached_data) == test_metrics

            # Test retrieving cached metrics
            mock_redis_client.get.return_value = json.dumps(test_metrics)

            result = await k8s_pipeline.get_cached_metrics("candidate", "test-ab-123")

            assert result == test_metrics
            mock_redis_client.get.assert_called_once_with(
                "model_metrics:test-ab-123:candidate"
            )

    async def test_redis_caching_error_handling(self, k8s_pipeline):
        """Test Redis caching error handling and graceful degradation."""
        with patch.object(
            k8s_pipeline.connection_manager, "get_redis_connection"
        ) as mock_get_redis:
            # Simulate Redis connection failure
            mock_get_redis.side_effect = Exception("Redis connection failed")

            # Should not raise exception, just return None
            result = await k8s_pipeline.get_cached_metrics("candidate", "test-ab-456")

            assert result is None

    async def test_health_check_comprehensive(self, k8s_pipeline):
        """Test comprehensive health check functionality."""
        # Mock healthy database connection
        mock_db_conn = AsyncMock()
        mock_db_conn.fetchval.return_value = 1

        # Mock healthy Redis connection
        mock_redis_conn = AsyncMock()
        mock_redis_conn.ping.return_value = True

        with (
            patch.object(
                k8s_pipeline.connection_manager, "get_db_connection"
            ) as mock_get_db,
            patch.object(
                k8s_pipeline.connection_manager, "get_redis_connection"
            ) as mock_get_redis,
        ):
            mock_get_db.return_value.__aenter__.return_value = mock_db_conn
            mock_get_redis.return_value.__aenter__.return_value = mock_redis_conn

            # Set some pool stats
            k8s_pipeline.connection_manager._pool_stats = {
                "db_connections_active": 3,
                "db_connections_idle": 7,
                "redis_connections_active": 2,
                "redis_connections_idle": 18,
            }

            health_status = await k8s_pipeline.health_check()

        # Verify overall health
        assert health_status["status"] == "healthy"
        assert "timestamp" in health_status

        # Verify component health
        components = health_status["components"]
        assert components["database"] == "healthy"
        assert components["redis"] == "healthy"
        assert components["openai_circuit_breaker"] == "CLOSED"
        assert components["mlflow_circuit_breaker"] == "CLOSED"

        # Verify connection pool stats
        pool_stats = health_status["connection_pools"]
        assert pool_stats["db_connections_active"] == 3
        assert pool_stats["db_connections_idle"] == 7
        assert pool_stats["redis_connections_active"] == 2
        assert pool_stats["redis_connections_idle"] == 18

    async def test_prometheus_metrics_generation(self, k8s_pipeline):
        """Test Prometheus metrics generation."""
        # Set up test state
        k8s_pipeline.connection_manager._pool_stats = {
            "db_connections_active": 4,
            "db_connections_idle": 6,
            "redis_connections_active": 3,
            "redis_connections_idle": 17,
        }

        # Simulate some circuit breaker failures
        k8s_pipeline.openai_circuit_breaker.failure_count = 2
        k8s_pipeline.mlflow_circuit_breaker.failure_count = 0

        metrics_output = await k8s_pipeline.get_prometheus_metrics()

        # Verify connection pool metrics
        assert "fine_tuning_db_connections_active 4" in metrics_output
        assert "fine_tuning_db_connections_idle 6" in metrics_output
        assert "fine_tuning_redis_connections_active 3" in metrics_output
        assert "fine_tuning_redis_connections_idle 17" in metrics_output

        # Verify circuit breaker metrics
        assert (
            'fine_tuning_openai_circuit_breaker_state{state="CLOSED"} 1'
            in metrics_output
        )
        assert "fine_tuning_openai_failures_total 2" in metrics_output
        assert (
            'fine_tuning_mlflow_circuit_breaker_state{state="CLOSED"} 1'
            in metrics_output
        )
        assert "fine_tuning_mlflow_failures_total 0" in metrics_output

        # Verify proper Prometheus format
        assert metrics_output.endswith("\n")
        lines = metrics_output.strip().split("\n")
        assert len(lines) >= 6  # Should have multiple metrics


class TestKubernetesDeploymentGeneration:
    """Test Kubernetes deployment YAML generation."""

    def test_deployment_yaml_generation(self):
        """Test generation of optimized Kubernetes deployment YAML."""
        config = KubernetesResourceConfig(
            memory_request="512Mi",
            memory_limit="2Gi",
            cpu_request="500m",
            cpu_limit="2000m",
            max_replicas=5,
            min_replicas=1,
            target_cpu_utilization=70,
            target_memory_utilization=80,
        )

        yaml_output = get_kubernetes_deployment_yaml(config)

        # Verify deployment configuration
        assert "apiVersion: apps/v1" in yaml_output
        assert "kind: Deployment" in yaml_output
        assert "name: fine-tuning-pipeline" in yaml_output

        # Verify resource limits
        assert 'memory: "512Mi"' in yaml_output
        assert 'memory: "2Gi"' in yaml_output
        assert 'cpu: "500m"' in yaml_output
        assert 'cpu: "2000m"' in yaml_output

        # Verify service configuration
        assert "kind: Service" in yaml_output
        assert "name: fine-tuning-pipeline-service" in yaml_output
        assert "port: 8080" in yaml_output
        assert "port: 9090" in yaml_output

        # Verify HPA configuration
        assert "kind: HorizontalPodAutoscaler" in yaml_output
        assert "minReplicas: 1" in yaml_output
        assert "maxReplicas: 5" in yaml_output
        assert "averageUtilization: 70" in yaml_output
        assert "averageUtilization: 80" in yaml_output

        # Verify health check configuration
        assert "livenessProbe:" in yaml_output
        assert "readinessProbe:" in yaml_output
        assert "path: /health" in yaml_output
        assert "path: /ready" in yaml_output

        # Verify environment variables
        assert "DATABASE_URL" in yaml_output
        assert "REDIS_URL" in yaml_output
        assert "OPENAI_API_KEY" in yaml_output
        assert "MLFLOW_TRACKING_URI" in yaml_output

    def test_deployment_yaml_with_custom_config(self):
        """Test deployment YAML generation with custom configuration."""
        config = KubernetesResourceConfig(
            memory_request="1Gi",
            memory_limit="4Gi",
            cpu_request="1000m",
            cpu_limit="4000m",
            max_replicas=10,
            min_replicas=3,
            target_cpu_utilization=60,
            target_memory_utilization=75,
        )

        yaml_output = get_kubernetes_deployment_yaml(config)

        # Verify custom resource limits
        assert 'memory: "1Gi"' in yaml_output
        assert 'memory: "4Gi"' in yaml_output
        assert 'cpu: "1000m"' in yaml_output
        assert 'cpu: "4000m"' in yaml_output

        # Verify custom HPA settings
        assert "minReplicas: 3" in yaml_output
        assert "maxReplicas: 10" in yaml_output
        assert "averageUtilization: 60" in yaml_output
        assert "averageUtilization: 75" in yaml_output


class TestPerformanceMonitoring:
    """Test performance monitoring and optimization tracking."""

    async def test_connection_pool_performance_tracking(self):
        """Test connection pool performance metrics tracking."""
        connection_manager = ConnectionPoolManager()

        # Initialize pools to get proper mocks
        await connection_manager.initialize_pools()

        # Simulate multiple concurrent connections
        tasks = []

        async def use_db_connection(delay):
            async with connection_manager.get_db_connection():
                await asyncio.sleep(delay)

        async def use_redis_connection(delay):
            async with connection_manager.get_redis_connection():
                await asyncio.sleep(delay)

        # Create concurrent tasks
        for i in range(5):
            tasks.append(asyncio.create_task(use_db_connection(0.1)))
        for i in range(3):
            tasks.append(asyncio.create_task(use_redis_connection(0.1)))

        # Run concurrently and measure performance
        start_time = time.time()
        await asyncio.gather(*tasks)
        duration = time.time() - start_time

        # Verify concurrent execution (should be ~0.1s, not 0.8s)
        assert duration < 0.3, (
            f"Concurrent execution took {duration:.2f}s, expected < 0.3s"
        )

        # Verify all connections were properly cleaned up
        final_stats = connection_manager.get_pool_stats()
        assert final_stats["db_connections_active"] == 0
        assert final_stats["redis_connections_active"] == 0
        assert final_stats["db_connections_idle"] == 5
        assert final_stats["redis_connections_idle"] == 3

    async def test_circuit_breaker_performance_impact(self):
        """Test circuit breaker performance impact on successful operations."""
        cb = CircuitBreaker(failure_threshold=5, timeout=60.0)

        async def fast_operation(value):
            return value * 2

        # Measure performance without circuit breaker
        start_time = time.time()
        for i in range(100):
            await fast_operation(i)
        baseline_duration = time.time() - start_time

        # Measure performance with circuit breaker
        start_time = time.time()
        for i in range(100):
            await cb.call(fast_operation, i)
        cb_duration = time.time() - start_time

        # Circuit breaker should add reasonable overhead (< 200% increase)
        overhead_percentage = (
            (cb_duration - baseline_duration) / baseline_duration
        ) * 100
        assert overhead_percentage < 200, (
            f"Circuit breaker added {overhead_percentage:.1f}% overhead"
        )

        # Verify circuit breaker remained closed
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    async def test_memory_efficiency_under_load(self):
        """Test memory efficiency under high load conditions."""
        k8s_pipeline = KubernetesOptimizedPipeline(KubernetesResourceConfig())

        # Simulate processing large amounts of data
        # Simulate processing large amounts of data without storing it
        # (variable removed to fix linting)

        # Mock successful caching operations
        mock_redis_client = AsyncMock()

        with patch.object(
            k8s_pipeline.connection_manager, "get_redis_connection"
        ) as mock_get_redis:
            mock_get_redis.return_value.__aenter__.return_value = mock_redis_client

            # Process multiple caching operations
            start_memory = self._get_memory_usage()

            tasks = []
            for i in range(10):
                task = asyncio.create_task(
                    k8s_pipeline.cache_evaluation_metrics(
                        f"model_{i}", f"test_{i}", {"metric": f"value_{i}"}
                    )
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

            end_memory = self._get_memory_usage()
            memory_increase = end_memory - start_memory

        # Verify memory efficiency (should not increase by more than 50MB)
        assert memory_increase < 50, (
            f"Memory increased by {memory_increase:.2f}MB under load"
        )

    def _get_memory_usage(self):
        """Get current memory usage in MB."""
        import psutil

        return psutil.Process().memory_info().rss / 1024 / 1024
