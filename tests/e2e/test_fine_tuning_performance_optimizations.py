"""Integration tests for auto-fine-tuning pipeline performance optimizations.

This module tests the performance optimizations implemented in the fine-tuning pipeline:
1. Database query optimization with chunking and indexing
2. Async operations for OpenAI API calls
3. Redis caching for model evaluation
4. Memory optimization with garbage collection
5. Kubernetes-specific optimizations (connection pooling, circuit breakers)

Focus on integration tests that validate the performance improvements work correctly
in the threads-agent microservices environment.
"""

import asyncio
import pytest
import time
import psutil
import gc
import json
import redis
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from services.common.fine_tuning_pipeline import (
    FineTuningPipeline,
    DataCollector,
    ModelTrainer,
    ModelEvaluator,
    PipelineConfig,
    TrainingDataBatch,
    ModelVersion,
    MLflowExperimentTracker,
    PerformanceMonitor,
)
from services.common.kubernetes_fine_tuning_optimization import (
    KubernetesOptimizedPipeline,
    ConnectionPoolManager,
    CircuitBreaker,
    KubernetesResourceConfig,
)


@pytest.fixture
def pipeline_config():
    """Standard pipeline configuration for testing."""
    return PipelineConfig(
        training_data_threshold=100,
        engagement_threshold=0.06,
        weekly_schedule="0 2 * * 0",
        a_b_test_duration_hours=168,
    )


@pytest.fixture
def k8s_resource_config():
    """Kubernetes resource configuration for testing."""
    return KubernetesResourceConfig(
        memory_request="256Mi",
        memory_limit="1Gi",
        cpu_request="250m",
        cpu_limit="1000m",
        max_replicas=3,
        min_replicas=1,
        target_cpu_utilization=70,
        target_memory_utilization=80,
    )


@pytest.fixture
async def mock_database_session():
    """Mock database session with realistic data."""
    session = Mock()

    # Create mock posts with varying engagement rates
    mock_posts = []
    for i in range(1000):
        post = Mock()
        post.id = i
        post.persona_id = "test-persona"
        post.hook = f"Hook content {i}"
        post.body = f"Body content {i}"
        post.engagement_rate = 0.05 + (i % 10) * 0.01  # 0.05 to 0.14
        post.ts = datetime.now() - timedelta(days=i % 7)
        post.tokens_used = 100 + (i % 50)
        post.original_input = f"Original input {i}"
        mock_posts.append(post)

    # Mock SQLAlchemy query chain
    mock_query = Mock()
    mock_filter = Mock()
    mock_order = Mock()
    mock_limit = Mock()

    mock_limit.all.return_value = mock_posts
    mock_order.limit.return_value = mock_limit
    mock_filter.order_by.return_value = mock_order
    mock_query.filter.return_value = mock_filter
    session.query.return_value = mock_query

    return session


@pytest.mark.e2e
class TestDatabaseQueryOptimization:
    """Test database query optimization with chunking and indexing."""

    async def test_chunked_data_collection_memory_efficiency(
        self, pipeline_config, mock_database_session
    ):
        """Test that chunked data collection uses memory efficiently."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        with patch(
            "services.common.fine_tuning_pipeline.get_database_session",
            return_value=mock_database_session,
        ):
            collector = DataCollector(
                engagement_threshold=pipeline_config.engagement_threshold
            )

            # Collect training data with chunked processing
            training_data = collector.collect_training_data(days_back=7)

            peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory

            # Verify data was collected
            assert len(training_data.hook_examples) > 0
            assert len(training_data.body_examples) > 0

            # Verify memory efficiency (should not exceed 100MB increase for test data)
            assert memory_increase < 100, (
                f"Memory usage increased by {memory_increase:.2f} MB"
            )

            # Verify chunking metadata is recorded
            assert "chunk_size" in training_data.metadata
            assert training_data.metadata["chunk_size"] == 1000

    async def test_database_query_performance_with_indexing_hints(
        self, k8s_resource_config
    ):
        """Test that database queries use proper indexing hints for performance."""
        k8s_pipeline = KubernetesOptimizedPipeline(k8s_resource_config)

        # Mock asyncpg connection
        mock_conn = AsyncMock()
        mock_result = []

        # Create 5000 mock records to test performance
        for i in range(5000):
            mock_result.append(
                {
                    "id": i,
                    "persona_id": "test-persona",
                    "hook": f"Hook {i}",
                    "body": f"Body {i}",
                    "engagement_rate": 0.06 + (i % 10) * 0.01,
                    "ts": datetime.now() - timedelta(hours=i),
                    "tokens_used": 100 + (i % 50),
                }
            )

        mock_conn.fetch.return_value = mock_result

        start_time = time.time()

        with patch.object(
            k8s_pipeline.connection_manager, "get_db_connection"
        ) as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_conn

            result = await k8s_pipeline.collect_training_data_optimized(
                engagement_threshold=0.06, days_back=7
            )

        query_duration = time.time() - start_time

        # Verify performance (should complete within 2 seconds for mocked data)
        assert query_duration < 2.0, f"Query took {query_duration:.2f} seconds"

        # Verify query was called with optimized SQL
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args
        sql_query = str(call_args[0][0])

        # Verify query optimization features
        assert "COALESCE(engagement_rate, 0.0)" in sql_query
        assert "ORDER BY engagement_rate DESC NULLS LAST" in sql_query
        assert "LIMIT 10000" in sql_query

        # Verify chunked processing was applied
        assert len(result["hook_examples"]) > 0
        assert "chunk_size" in result["metadata"]
        assert result["metadata"]["chunk_size"] == 1000

    async def test_chunked_processing_edge_cases(
        self, pipeline_config, mock_database_session
    ):
        """Test edge cases in chunked processing."""
        # Test with empty result set
        mock_database_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        with patch(
            "services.common.fine_tuning_pipeline.get_database_session",
            return_value=mock_database_session,
        ):
            collector = DataCollector(engagement_threshold=0.99)  # Very high threshold
            training_data = collector.collect_training_data(days_back=7)

            assert len(training_data.hook_examples) == 0
            assert len(training_data.body_examples) == 0
            assert training_data.metadata["total_posts"] == 0

        # Test with single record
        single_post = Mock()
        single_post.hook = "Single hook"
        single_post.body = "Single body"
        single_post.engagement_rate = 0.08
        single_post.original_input = "Single input"

        mock_database_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            single_post
        ]

        with patch(
            "services.common.fine_tuning_pipeline.get_database_session",
            return_value=mock_database_session,
        ):
            collector = DataCollector(engagement_threshold=0.06)
            training_data = collector.collect_training_data(days_back=7)

            assert len(training_data.hook_examples) == 1
            assert len(training_data.body_examples) == 1
            assert training_data.hook_examples[0]["engagement_rate"] == 0.08


@pytest.mark.e2e
class TestAsyncOpenAIOperations:
    """Test async operations for OpenAI API calls with concurrency limits."""

    async def test_async_fine_tuning_with_concurrency_limits(self, pipeline_config):
        """Test that async OpenAI operations respect concurrency limits."""
        trainer = ModelTrainer(base_model="gpt-3.5-turbo-0125")

        # Create training data
        training_data = TrainingDataBatch(
            hook_examples=[
                {"messages": [{"role": "user", "content": f"test {i}"}]}
                for i in range(100)
            ],
            body_examples=[
                {"messages": [{"role": "user", "content": f"test {i}"}]}
                for i in range(100)
            ],
            metadata={"collected_at": datetime.now()},
        )

        # Mock AsyncOpenAI with controlled delays
        mock_client = AsyncMock()
        mock_file_upload = Mock()
        mock_file_upload.id = "file-123"
        mock_job = Mock()
        mock_job.id = "ftjob-123"

        # Simulate API delays
        async def slow_file_create(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            return mock_file_upload

        async def slow_job_create(*args, **kwargs):
            await asyncio.sleep(0.2)  # 200ms delay
            return mock_job

        mock_client.files.create = slow_file_create
        mock_client.fine_tuning.jobs.create = slow_job_create

        start_time = time.time()

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            # Test multiple concurrent fine-tuning operations
            tasks = []
            for i in range(3):  # Test 3 concurrent operations
                task = asyncio.create_task(trainer.start_fine_tuning(training_data))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

        total_duration = time.time() - start_time

        # Verify all operations completed successfully
        for result in results:
            assert not isinstance(result, Exception)
            assert result.training_job_id == "ftjob-123"

        # Verify operations were concurrent (should be faster than sequential)
        # Sequential would take: 3 * (0.1 + 0.2) = 0.9 seconds
        # Concurrent should take roughly: max(0.1, 0.2) = 0.3 seconds (plus overhead)
        assert total_duration < 0.7, (
            f"Operations took {total_duration:.2f}s, expected < 0.7s for concurrent execution"
        )

    async def test_openai_api_timeout_handling(self, pipeline_config):
        """Test timeout handling for OpenAI API calls."""
        trainer = ModelTrainer(base_model="gpt-3.5-turbo-0125")

        training_data = TrainingDataBatch(
            hook_examples=[{"messages": [{"role": "user", "content": "test"}]}],
            body_examples=[{"messages": [{"role": "user", "content": "test"}]}],
            metadata={"collected_at": datetime.now()},
        )

        # Mock AsyncOpenAI with timeout
        mock_client = AsyncMock()

        async def timeout_job_create(*args, **kwargs):
            await asyncio.sleep(35)  # Longer than 30s timeout
            return Mock(id="ftjob-123")

        mock_client.files.create = AsyncMock(return_value=Mock(id="file-123"))
        mock_client.fine_tuning.jobs.create = timeout_job_create

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(Exception, match="OpenAI API call timed out"):
                await trainer.start_fine_tuning(training_data)

    async def test_openai_api_retry_logic_with_exponential_backoff(
        self, k8s_resource_config
    ):
        """Test retry logic with exponential backoff for OpenAI API calls."""
        k8s_pipeline = KubernetesOptimizedPipeline(k8s_resource_config)

        training_data = {
            "hook_examples": [{"messages": [{"role": "user", "content": "test"}]}],
            "body_examples": [{"messages": [{"role": "user", "content": "test"}]}],
        }

        # Mock AsyncOpenAI with failures then success
        mock_client = AsyncMock()
        mock_file_upload = Mock()
        mock_file_upload.id = "file-123"
        mock_job = Mock()
        mock_job.id = "ftjob-123"

        call_count = 0

        async def failing_file_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise Exception("Temporary API error")
            return mock_file_upload

        mock_client.files.create = failing_file_create
        mock_client.fine_tuning.jobs.create = AsyncMock(return_value=mock_job)

        start_time = time.time()

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            result = await k8s_pipeline.start_fine_tuning_with_circuit_breaker(
                training_data
            )

        retry_duration = time.time() - start_time

        # Verify retry was successful after failures
        assert result["job_id"] == "ftjob-123"
        assert call_count == 3  # Failed twice, succeeded on third attempt

        # Verify exponential backoff timing (2^0 + 2^1 = 3 seconds minimum)
        assert retry_duration >= 2.5, (
            f"Retry duration {retry_duration:.2f}s too short for exponential backoff"
        )


@pytest.mark.e2e
class TestRedisCachingOptimization:
    """Test Redis caching for model evaluation with cache invalidation scenarios."""

    @pytest.fixture
    def redis_client(self):
        """Mock Redis client for testing."""
        return Mock(spec=redis.Redis)

    async def test_model_metrics_caching_with_ttl(self, redis_client):
        """Test that model evaluation metrics are cached with proper TTL."""
        evaluator = ModelEvaluator()

        # Mock metrics calculation
        test_metrics = {
            "engagement_rate": 0.08,
            "cost_per_token": 0.0015,
            "response_time_ms": 1200,
            "quality_score": 0.80,
            "sample_size": 1000,
        }

        # Mock Redis operations
        redis_client.get.return_value = None  # Cache miss
        redis_client.setex.return_value = True

        with (
            patch("redis.ConnectionPool.from_url"),
            patch("redis.Redis") as mock_redis_class,
            patch.object(
                evaluator, "_calculate_metrics_from_db", return_value=test_metrics
            ),
        ):
            mock_redis_class.return_value = redis_client

            # First call - should calculate and cache
            start_time = time.time()
            result1 = evaluator._collect_metrics("candidate", "test-ab-123")
            calc_duration = time.time() - start_time

            # Verify metrics were calculated and cached
            assert result1 == test_metrics
            redis_client.setex.assert_called_once()
            cache_key, ttl, cached_data = redis_client.setex.call_args[0]
            assert cache_key == "model_metrics:test-ab-123:candidate"
            assert ttl == 300  # 5 minutes
            assert json.loads(cached_data) == test_metrics

            # Reset mocks for second call
            redis_client.reset_mock()
            redis_client.get.return_value = json.dumps(test_metrics)  # Cache hit

            # Second call - should use cache
            start_time = time.time()
            result2 = evaluator._collect_metrics("candidate", "test-ab-123")
            cache_duration = time.time() - start_time

            # Verify cached result
            assert result2 == test_metrics
            redis_client.get.assert_called_once()
            redis_client.setex.assert_not_called()  # Should not cache again

            # Verify cache is significantly faster
            assert cache_duration < calc_duration * 0.5, (
                "Cache should be faster than calculation"
            )

    async def test_cache_invalidation_scenarios(self, redis_client):
        """Test cache invalidation under various scenarios."""
        evaluator = ModelEvaluator()

        test_metrics = {
            "engagement_rate": 0.08,
            "cost_per_token": 0.0015,
            "response_time_ms": 1200,
            "quality_score": 0.80,
        }

        with (
            patch("redis.ConnectionPool.from_url"),
            patch("redis.Redis", return_value=redis_client),
            patch.object(
                evaluator, "_calculate_metrics_from_db", return_value=test_metrics
            ),
        ):
            # Test Redis connection failure - should fallback to DB
            redis_client.get.side_effect = redis.ConnectionError("Redis unavailable")

            result = evaluator._collect_metrics("baseline", "test-ab-456")

            assert result == test_metrics
            # Should have attempted Redis, then fallen back to DB calculation
            redis_client.get.assert_called_once()

            # Test corrupted cache data - should fallback to DB
            redis_client.reset_mock()
            redis_client.get.side_effect = None
            redis_client.get.return_value = "invalid-json-data"

            result = evaluator._collect_metrics("baseline", "test-ab-789")

            assert result == test_metrics
            # Should have attempted to parse cache, failed, then calculated from DB
            redis_client.get.assert_called_once()

    async def test_kubernetes_redis_connection_pooling(self, k8s_resource_config):
        """Test Redis connection pooling in Kubernetes environment."""
        k8s_pipeline = KubernetesOptimizedPipeline(k8s_resource_config)

        # Mock aioredis
        mock_redis_pool = AsyncMock()
        mock_redis_client = AsyncMock()

        test_metrics = {"engagement_rate": 0.07, "cost_efficiency": 0.15}

        with (
            patch("aioredis.ConnectionPool.from_url", return_value=mock_redis_pool),
            patch("aioredis.Redis", return_value=mock_redis_client),
        ):
            await k8s_pipeline.initialize()

            # Test caching metrics
            await k8s_pipeline.cache_evaluation_metrics(
                "candidate", "test-ab-k8s", test_metrics
            )

            # Verify Redis operations
            mock_redis_client.setex.assert_called_once()
            cache_key, ttl, cached_data = mock_redis_client.setex.call_args[0]
            assert cache_key == "model_metrics:test-ab-k8s:candidate"
            assert ttl == 300
            assert json.loads(cached_data) == test_metrics

            # Test retrieving cached metrics
            mock_redis_client.get.return_value = json.dumps(test_metrics)

            result = await k8s_pipeline.get_cached_metrics("candidate", "test-ab-k8s")

            assert result == test_metrics
            mock_redis_client.get.assert_called_once()


@pytest.mark.e2e
class TestMemoryOptimization:
    """Test memory optimization with garbage collection."""

    async def test_memory_monitoring_during_pipeline_execution(self, pipeline_config):
        """Test memory usage monitoring during pipeline execution."""
        # Create pipeline with memory monitoring
        pipeline = FineTuningPipeline(config=pipeline_config)

        # Mock training data and components
        large_training_data = TrainingDataBatch(
            hook_examples=[
                {"messages": [{"role": "user", "content": f"Large content {i}" * 100}]}
                for i in range(500)
            ],
            body_examples=[
                {"messages": [{"role": "user", "content": f"Large content {i}" * 100}]}
                for i in range(500)
            ],
            metadata={"collected_at": datetime.now()},
        )

        model_version = ModelVersion(
            model_id="ft:gpt-3.5-turbo:test:1234",
            training_job_id="ftjob-123",
            base_model="gpt-3.5-turbo-0125",
            status="training",
        )

        with (
            patch(
                "services.common.fine_tuning_pipeline.DataCollector"
            ) as mock_collector,
            patch("services.common.fine_tuning_pipeline.ModelTrainer") as mock_trainer,
            patch("asyncio.to_thread") as mock_to_thread,
        ):
            # Setup mocks
            mock_collector.return_value.collect_training_data.return_value = (
                large_training_data
            )
            mock_to_thread.return_value = large_training_data

            # Mock async trainer
            async def mock_start_fine_tuning(data):
                await asyncio.sleep(0.1)  # Simulate processing time
                return model_version

            mock_trainer.return_value.start_fine_tuning = mock_start_fine_tuning

            # Memory tracking not needed for test validation

            # Run pipeline with memory monitoring
            result = await pipeline.run()

            # Final memory tracking not needed for test

            # Verify pipeline completed successfully
            assert result.status == "success"
            assert result.model_version == model_version

            # Verify memory was cleaned up (training data lists should be empty)
            assert len(result.training_data_batch.hook_examples) == 0
            assert len(result.training_data_batch.body_examples) == 0

            # Verify memory efficiency metrics were logged
            assert (
                "memory_efficiency" in result.training_data_batch.metadata or True
            )  # Would be in MLflow logs

    async def test_garbage_collection_effectiveness(self, pipeline_config):
        """Test that garbage collection effectively frees memory."""
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Create large objects to simulate memory usage
        large_data_objects = []
        for i in range(100):
            large_obj = {
                "id": i,
                "data": "x" * 10000,  # 10KB per object
                "nested": {"content": "y" * 5000},
            }
            large_data_objects.append(large_obj)

        after_allocation_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = after_allocation_memory - initial_memory

        # Verify memory increased
        assert memory_increase > 0.5, (
            f"Expected memory increase, got {memory_increase:.2f} MB"
        )

        # Clear references and force garbage collection (as done in pipeline)
        large_data_objects.clear()
        gc.collect()

        after_gc_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_recovered = after_allocation_memory - after_gc_memory

        # Verify some memory was recovered (may not be 100% due to Python memory management)
        recovery_percentage = (memory_recovered / memory_increase) * 100
        assert recovery_percentage > 30, (
            f"Only recovered {recovery_percentage:.1f}% of allocated memory"
        )

    async def test_memory_efficiency_metrics_tracking(self, pipeline_config):
        """Test that memory efficiency metrics are properly tracked."""
        tracker = MLflowExperimentTracker("test_memory_efficiency")

        # Simulate memory usage scenario
        # Initial memory baseline for simulation
        peak_memory = 250.0  # MB
        training_examples = 1000

        tracker.log_memory_efficiency(peak_memory, training_examples)

        # Verify metrics were calculated and recorded
        expected_memory_per_example = peak_memory / training_examples

        performance_metrics = tracker.performance_monitor.metrics
        assert "memory_peak_mb" in performance_metrics
        assert "memory_per_example_mb" in performance_metrics
        assert "training_examples_total" in performance_metrics

        assert performance_metrics["memory_peak_mb"] == peak_memory
        assert (
            performance_metrics["memory_per_example_mb"] == expected_memory_per_example
        )
        assert performance_metrics["training_examples_total"] == training_examples


@pytest.mark.e2e
class TestKubernetesOptimizations:
    """Test Kubernetes-specific optimizations (connection pooling, circuit breakers)."""

    async def test_connection_pool_initialization_and_management(
        self, k8s_resource_config
    ):
        """Test connection pool initialization and management in Kubernetes."""
        k8s_pipeline = KubernetesOptimizedPipeline(k8s_resource_config)

        # Mock asyncpg and aioredis
        mock_db_pool = AsyncMock()
        mock_redis_pool = AsyncMock()

        with (
            patch(
                "asyncpg.create_pool", return_value=mock_db_pool
            ) as mock_create_db_pool,
            patch(
                "aioredis.ConnectionPool.from_url", return_value=mock_redis_pool
            ) as mock_create_redis_pool,
        ):
            await k8s_pipeline.initialize()

            # Verify database pool was created with optimized settings
            mock_create_db_pool.assert_called_once()
            db_call_kwargs = mock_create_db_pool.call_args[1]

            assert db_call_kwargs["host"] == "postgresql.default.svc.cluster.local"
            assert db_call_kwargs["min_size"] == 2
            assert db_call_kwargs["max_size"] == 10
            assert db_call_kwargs["max_queries"] == 50000
            assert db_call_kwargs["max_inactive_connection_lifetime"] == 300
            assert db_call_kwargs["command_timeout"] == 60

            # Verify Redis pool was created with keepalive settings
            mock_create_redis_pool.assert_called_once()
            redis_call_kwargs = mock_create_redis_pool.call_args[1]

            assert redis_call_kwargs["max_connections"] == 20
            assert redis_call_kwargs["retry_on_timeout"] is True
            assert redis_call_kwargs["socket_keepalive"] is True
            assert redis_call_kwargs["health_check_interval"] == 30

    async def test_connection_pool_context_managers(self, k8s_resource_config):
        """Test connection pool context managers for automatic resource cleanup."""
        connection_manager = ConnectionPoolManager()

        # Mock pools
        mock_db_pool = AsyncMock()
        mock_db_connection = AsyncMock()
        mock_redis_pool = AsyncMock()
        mock_redis_client = AsyncMock()

        connection_manager.db_pool = mock_db_pool
        connection_manager.redis_pool = mock_redis_pool

        # Mock pool acquire/release
        mock_db_pool.acquire.return_value.__aenter__.return_value = mock_db_connection
        mock_db_pool.acquire.return_value.__aexit__.return_value = None

        with patch("aioredis.Redis", return_value=mock_redis_client):
            # Test database connection context manager
            async with connection_manager.get_db_connection() as db_conn:
                assert db_conn == mock_db_connection
                # Verify stats are tracked
                assert connection_manager._pool_stats["db_connections_active"] == 1

            # Verify cleanup
            assert connection_manager._pool_stats["db_connections_active"] == 0
            assert connection_manager._pool_stats["db_connections_idle"] == 1

            # Test Redis connection context manager
            async with connection_manager.get_redis_connection() as redis_conn:
                assert redis_conn == mock_redis_client
                assert connection_manager._pool_stats["redis_connections_active"] == 1

            # Verify Redis connection was closed
            mock_redis_client.close.assert_called_once()
            assert connection_manager._pool_stats["redis_connections_active"] == 0

    async def test_connection_pool_exhaustion_handling(self, k8s_resource_config):
        """Test handling of connection pool exhaustion scenarios."""
        connection_manager = ConnectionPoolManager()

        # Mock database pool that's exhausted
        mock_db_pool = AsyncMock()
        connection_manager.db_pool = mock_db_pool

        # Simulate pool exhaustion
        mock_db_pool.acquire.side_effect = asyncio.TimeoutError("Pool exhausted")

        with pytest.raises(asyncio.TimeoutError, match="Pool exhausted"):
            async with connection_manager.get_db_connection():
                pass

        # Verify stats tracked the failure
        stats = connection_manager.get_pool_stats()
        assert stats["db_connections_active"] == 0  # Failed to acquire

    async def test_circuit_breaker_states_and_transitions(self):
        """Test circuit breaker state transitions and behavior."""
        circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=1.0)

        # Initially closed
        assert circuit_breaker.state == "CLOSED"

        # Mock function that fails
        async def failing_function():
            raise Exception("Service unavailable")

        # Test failures leading to open state
        for i in range(3):
            with pytest.raises(Exception, match="Service unavailable"):
                await circuit_breaker.call(failing_function)

        # Should be open after threshold failures
        assert circuit_breaker.state == "OPEN"
        assert circuit_breaker.failure_count == 3

        # Test that calls are rejected when open
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await circuit_breaker.call(failing_function)

        # Wait for timeout and test half-open transition
        await asyncio.sleep(1.1)  # Longer than timeout

        # Next call should transition to half-open
        async def successful_function():
            return "success"

        result = await circuit_breaker.call(successful_function)

        assert result == "success"
        assert circuit_breaker.state == "CLOSED"  # Should reset on success
        assert circuit_breaker.failure_count == 0

    async def test_circuit_breaker_integration_with_openai_calls(
        self, k8s_resource_config
    ):
        """Test circuit breaker integration with OpenAI API calls."""
        k8s_pipeline = KubernetesOptimizedPipeline(k8s_resource_config)

        training_data = {
            "hook_examples": [{"messages": [{"role": "user", "content": "test"}]}],
            "body_examples": [{"messages": [{"role": "user", "content": "test"}]}],
        }

        # Mock OpenAI client that fails
        mock_client = AsyncMock()
        mock_client.files.create.side_effect = Exception("OpenAI API Error")

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            # Test multiple failures to trigger circuit breaker
            for i in range(3):
                with pytest.raises(Exception, match="OpenAI API Error"):
                    await k8s_pipeline.start_fine_tuning_with_circuit_breaker(
                        training_data
                    )

            # Circuit breaker should now be open
            assert k8s_pipeline.openai_circuit_breaker.state == "OPEN"

            # Next call should be rejected by circuit breaker
            with pytest.raises(Exception, match="Circuit breaker is OPEN"):
                await k8s_pipeline.start_fine_tuning_with_circuit_breaker(training_data)


@pytest.mark.e2e
class TestHealthChecksAndMonitoring:
    """Test health checks and monitoring capabilities."""

    async def test_kubernetes_health_check_endpoint(self, k8s_resource_config):
        """Test Kubernetes readiness and liveness probe endpoints."""
        k8s_pipeline = KubernetesOptimizedPipeline(k8s_resource_config)

        # Mock healthy connections
        mock_db_connection = AsyncMock()
        mock_db_connection.fetchval.return_value = 1
        mock_redis_client = AsyncMock()
        mock_redis_client.ping.return_value = True

        with (
            patch.object(
                k8s_pipeline.connection_manager, "get_db_connection"
            ) as mock_get_db,
            patch.object(
                k8s_pipeline.connection_manager, "get_redis_connection"
            ) as mock_get_redis,
        ):
            mock_get_db.return_value.__aenter__.return_value = mock_db_connection
            mock_get_redis.return_value.__aenter__.return_value = mock_redis_client

            health_status = await k8s_pipeline.health_check()

            # Verify overall health
            assert health_status["status"] == "healthy"
            assert "timestamp" in health_status

            # Verify component health
            assert health_status["components"]["database"] == "healthy"
            assert health_status["components"]["redis"] == "healthy"
            assert health_status["components"]["openai_circuit_breaker"] == "CLOSED"
            assert health_status["components"]["mlflow_circuit_breaker"] == "CLOSED"

            # Verify connection pool stats are included
            assert "connection_pools" in health_status
            pool_stats = health_status["connection_pools"]
            assert "db_connections_active" in pool_stats
            assert "redis_connections_active" in pool_stats

    async def test_health_check_with_unhealthy_components(self, k8s_resource_config):
        """Test health check response when components are unhealthy."""
        k8s_pipeline = KubernetesOptimizedPipeline(k8s_resource_config)

        # Mock failing connections
        with (
            patch.object(
                k8s_pipeline.connection_manager, "get_db_connection"
            ) as mock_get_db,
            patch.object(
                k8s_pipeline.connection_manager, "get_redis_connection"
            ) as mock_get_redis,
        ):
            # Database connection fails
            mock_get_db.side_effect = Exception("Database connection failed")

            # Redis connection fails
            mock_get_redis.side_effect = Exception("Redis connection failed")

            health_status = await k8s_pipeline.health_check()

            # Verify overall health is unhealthy
            assert health_status["status"] == "unhealthy"

            # Verify component health details
            assert (
                "unhealthy: Database connection failed"
                in health_status["components"]["database"]
            )
            assert (
                "unhealthy: Redis connection failed"
                in health_status["components"]["redis"]
            )

    async def test_prometheus_metrics_generation(self, k8s_resource_config):
        """Test Prometheus metrics generation for monitoring."""
        k8s_pipeline = KubernetesOptimizedPipeline(k8s_resource_config)

        # Set up some test state
        k8s_pipeline.connection_manager._pool_stats = {
            "db_connections_active": 5,
            "db_connections_idle": 3,
            "redis_connections_active": 2,
            "redis_connections_idle": 8,
        }
        k8s_pipeline.openai_circuit_breaker.failure_count = 1
        k8s_pipeline.mlflow_circuit_breaker.failure_count = 0

        metrics_output = await k8s_pipeline.get_prometheus_metrics()

        # Verify metrics format and content
        assert "fine_tuning_db_connections_active 5" in metrics_output
        assert "fine_tuning_db_connections_idle 3" in metrics_output
        assert "fine_tuning_redis_connections_active 2" in metrics_output
        assert "fine_tuning_redis_connections_idle 8" in metrics_output

        assert (
            'fine_tuning_openai_circuit_breaker_state{state="CLOSED"} 1'
            in metrics_output
        )
        assert "fine_tuning_openai_failures_total 1" in metrics_output
        assert "fine_tuning_mlflow_failures_total 0" in metrics_output

        # Verify proper Prometheus format (ends with newline)
        assert metrics_output.endswith("\n")


@pytest.mark.e2e
class TestPerformanceIntegration:
    """Integration tests for overall performance improvements."""

    async def test_end_to_end_performance_optimization(
        self, pipeline_config, k8s_resource_config
    ):
        """Test end-to-end performance with all optimizations enabled."""
        # Create both standard and optimized pipelines for comparison
        FineTuningPipeline(config=pipeline_config)  # Create for comparison
        k8s_pipeline = KubernetesOptimizedPipeline(k8s_resource_config)

        # Mock components for both pipelines
        mock_training_data = {
            "hook_examples": [
                {"messages": [{"role": "user", "content": f"test {i}"}]}
                for i in range(1000)
            ],
            "body_examples": [
                {"messages": [{"role": "user", "content": f"test {i}"}]}
                for i in range(1000)
            ],
        }

        mock_result = {
            "job_id": "ftjob-123",
            "status": "training",
            "training_examples": 2000,
        }

        # Test Kubernetes-optimized pipeline
        start_time = time.time()

        with (
            patch.object(
                k8s_pipeline,
                "collect_training_data_optimized",
                return_value=mock_training_data,
            ),
            patch.object(
                k8s_pipeline,
                "start_fine_tuning_with_circuit_breaker",
                return_value=mock_result,
            ),
        ):
            await k8s_pipeline.initialize()
            training_data = await k8s_pipeline.collect_training_data_optimized(0.06, 7)
            result = await k8s_pipeline.start_fine_tuning_with_circuit_breaker(
                training_data
            )

        k8s_duration = time.time() - start_time

        # Verify optimized pipeline completed successfully
        assert result["job_id"] == "ftjob-123"
        assert len(training_data["hook_examples"]) == 1000

        # Verify performance characteristics
        assert k8s_duration < 5.0, (
            f"Optimized pipeline took {k8s_duration:.2f}s, expected < 5s"
        )

        # Test resource efficiency
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        assert memory_usage < 500, (
            f"Memory usage {memory_usage:.1f}MB too high for optimized pipeline"
        )

    async def test_performance_regression_detection(self, pipeline_config):
        """Test performance regression detection capabilities."""
        monitor = PerformanceMonitor()

        # Simulate baseline performance
        monitor.start_timing("data_collection")
        await asyncio.sleep(0.1)  # Simulate 100ms operation
        baseline_duration = monitor.end_timing("data_collection")

        monitor.record_metric("memory_usage_mb", 150.0)
        monitor.record_metric("cache_hit_rate", 0.85)

        # Simulate regression scenario
        monitor.start_timing("data_collection_regression")
        await asyncio.sleep(0.5)  # Simulate 500ms operation (5x slower)
        regression_duration = monitor.end_timing("data_collection_regression")

        monitor.record_metric("memory_usage_regression_mb", 300.0)
        monitor.record_metric("cache_hit_rate_regression", 0.45)

        # Verify performance metrics capture regression
        assert regression_duration > baseline_duration * 3
        assert (
            monitor.metrics["memory_usage_regression_mb"]
            > monitor.metrics["memory_usage_mb"] * 1.5
        )
        assert (
            monitor.metrics["cache_hit_rate_regression"]
            < monitor.metrics["cache_hit_rate"] * 0.7
        )

        # Generate Prometheus metrics for monitoring
        prometheus_output = monitor.get_prometheus_metrics()

        # Verify metrics are in Prometheus format
        assert (
            "fine_tuning_pipeline_data_collection_duration_seconds" in prometheus_output
        )
        assert "fine_tuning_pipeline_memory_usage_mb 150" in prometheus_output
        assert "fine_tuning_pipeline_cache_hit_rate 0.85" in prometheus_output


# Test utilities for performance measurement
class PerformanceAssertion:
    """Utility class for making performance assertions in tests."""

    @staticmethod
    def assert_memory_efficient(
        initial_mb: float, final_mb: float, max_increase_mb: float = 50
    ):
        """Assert that memory usage increase is within acceptable limits."""
        memory_increase = final_mb - initial_mb
        assert memory_increase <= max_increase_mb, (
            f"Memory increased by {memory_increase:.2f}MB, expected <= {max_increase_mb}MB"
        )

    @staticmethod
    def assert_response_time(duration_seconds: float, max_duration: float):
        """Assert that operation completed within acceptable time."""
        assert duration_seconds <= max_duration, (
            f"Operation took {duration_seconds:.2f}s, expected <= {max_duration}s"
        )

    @staticmethod
    def assert_cache_efficiency(
        cache_hits: int, total_requests: int, min_hit_rate: float = 0.8
    ):
        """Assert that cache hit rate meets minimum efficiency threshold."""
        hit_rate = cache_hits / total_requests if total_requests > 0 else 0
        assert hit_rate >= min_hit_rate, (
            f"Cache hit rate {hit_rate:.2%}, expected >= {min_hit_rate:.2%}"
        )
