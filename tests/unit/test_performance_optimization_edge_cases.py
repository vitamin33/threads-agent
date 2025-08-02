"""Unit tests for edge cases and error handling in performance optimizations.

This module tests edge cases, error conditions, and resilience of the performance
optimizations in the auto-fine-tuning pipeline:
1. Connection pool exhaustion scenarios
2. Cache invalidation and corruption handling
3. Memory pressure and cleanup edge cases
4. Circuit breaker failure scenarios
5. Network timeout and retry logic
6. Resource limit enforcement
"""

import asyncio
import pytest
import time
import gc
import json
import redis
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from services.common.fine_tuning_pipeline import (
    DataCollector,
    ModelTrainer,
    ModelEvaluator,
    PipelineConfig,
    TrainingDataBatch
)
from services.common.kubernetes_fine_tuning_optimization import (
    KubernetesOptimizedPipeline,
    ConnectionPoolManager,
    CircuitBreaker,
    KubernetesResourceConfig
)


class TestConnectionPoolExhaustionScenarios:
    """Test connection pool exhaustion and recovery scenarios."""
    
    @pytest.fixture
    def connection_manager(self):
        """Create connection manager for testing."""
        return ConnectionPoolManager()
    
    async def test_database_pool_exhaustion_timeout(self, connection_manager):
        """Test handling when database connection pool is exhausted."""
        # Mock exhausted pool
        mock_pool = AsyncMock()
        mock_pool.acquire.side_effect = asyncio.TimeoutError("Pool exhausted after 30s")
        connection_manager.db_pool = mock_pool
        
        # Should raise timeout error when pool is exhausted
        with pytest.raises(asyncio.TimeoutError, match="Pool exhausted"):
            async with connection_manager.get_db_connection():
                pass
        
        # Verify stats don't show false active connections
        stats = connection_manager.get_pool_stats()
        assert stats["db_connections_active"] == 0
    
    async def test_redis_pool_exhaustion_graceful_degradation(self, connection_manager):
        """Test graceful degradation when Redis pool is exhausted."""
        # Mock Redis pool that fails
        mock_redis_pool = AsyncMock()
        connection_manager.redis_pool = mock_redis_pool
        
        with patch('aioredis.Redis') as mock_redis_class:
            mock_redis_client = AsyncMock()
            mock_redis_client.setex.side_effect = redis.ConnectionError("Pool exhausted")
            mock_redis_class.return_value = mock_redis_client
            
            # Should handle Redis exhaustion gracefully
            with pytest.raises(redis.ConnectionError):
                async with connection_manager.get_redis_connection() as redis_conn:
                    await redis_conn.setex("test", 300, "value")
    
    async def test_concurrent_connection_exhaustion_handling(self, connection_manager):
        """Test handling multiple concurrent requests when pool is exhausted."""
        # Setup mock pool with limited capacity
        mock_pool = AsyncMock()
        mock_connection = AsyncMock()
        
        connection_count = 0
        max_connections = 3
        
        async def mock_acquire():
            nonlocal connection_count
            if connection_count >= max_connections:
                raise asyncio.TimeoutError(f"Pool exhausted: {connection_count}/{max_connections}")
            connection_count += 1
            return mock_connection
        
        async def mock_release():
            nonlocal connection_count
            connection_count -= 1
        
        mock_pool.acquire.return_value.__aenter__ = mock_acquire
        mock_pool.acquire.return_value.__aexit__ = lambda *args: mock_release()
        connection_manager.db_pool = mock_pool
        
        # Launch more concurrent operations than pool capacity
        async def use_connection(delay: float):
            try:
                async with connection_manager.get_db_connection():
                    await asyncio.sleep(delay)
                return "success"
            except asyncio.TimeoutError:
                return "pool_exhausted"
        
        # Start 5 concurrent operations (more than 3 max connections)
        tasks = [
            asyncio.create_task(use_connection(0.1)),
            asyncio.create_task(use_connection(0.1)),
            asyncio.create_task(use_connection(0.1)),
            asyncio.create_task(use_connection(0.1)),
            asyncio.create_task(use_connection(0.1))
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some should succeed, some should fail with pool exhaustion
        success_count = sum(1 for r in results if r == "success")
        failure_count = sum(1 for r in results if r == "pool_exhausted")
        
        assert success_count <= max_connections
        assert failure_count > 0  # Some should fail due to exhaustion
        assert success_count + failure_count == 5
    
    async def test_pool_recovery_after_exhaustion(self, connection_manager):
        """Test pool recovery after temporary exhaustion."""
        mock_pool = AsyncMock()
        connection_manager.db_pool = mock_pool
        
        call_count = 0
        
        async def mock_acquire():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise asyncio.TimeoutError("Pool temporarily exhausted")
            return AsyncMock()  # Success on third attempt
        
        mock_pool.acquire.return_value.__aenter__ = mock_acquire
        mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # First two attempts should fail
        with pytest.raises(asyncio.TimeoutError):
            async with connection_manager.get_db_connection():
                pass
        
        with pytest.raises(asyncio.TimeoutError):
            async with connection_manager.get_db_connection():
                pass
        
        # Third attempt should succeed
        async with connection_manager.get_db_connection() as conn:
            assert conn is not None
        
        assert call_count == 3


class TestCacheInvalidationAndCorruption:
    """Test cache invalidation and corruption handling scenarios."""
    
    async def test_redis_cache_corruption_recovery(self):
        """Test recovery from corrupted Redis cache data."""
        evaluator = ModelEvaluator()
        
        # Mock corrupted cache scenarios
        corruption_scenarios = [
            "invalid-json",
            '{"incomplete": json',
            '{"wrong_format": "not_metrics"}',
            "",
            None
        ]
        
        valid_metrics = {
            "engagement_rate": 0.08,
            "cost_per_token": 0.0015,
            "response_time_ms": 1200,
            "quality_score": 0.80
        }
        
        for corrupted_data in corruption_scenarios:
            with patch('redis.ConnectionPool.from_url'), \
                 patch('redis.Redis') as mock_redis_class, \
                 patch.object(evaluator, '_calculate_metrics_from_db', return_value=valid_metrics):
                
                mock_redis = Mock()
                mock_redis.get.return_value = corrupted_data
                mock_redis_class.return_value = mock_redis
                
                # Should handle corruption gracefully and fallback to DB
                result = evaluator._collect_metrics("baseline", "test-corrupted")
                
                assert result == valid_metrics
                mock_redis.get.assert_called_once()
    
    async def test_cache_invalidation_race_conditions(self):
        """Test cache invalidation under race conditions."""
        k8s_pipeline = KubernetesOptimizedPipeline(KubernetesResourceConfig())
        
        test_metrics_v1 = {"version": 1, "value": 100}
        test_metrics_v2 = {"version": 2, "value": 200}
        
        mock_redis = AsyncMock()
        
        # Simulate race condition where cache is updated between get and set
        call_count = 0
        
        async def mock_get(key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps(test_metrics_v1)  # First read returns v1
            else:
                return json.dumps(test_metrics_v2)  # Later reads return v2
        
        mock_redis.get = mock_get
        
        with patch.object(k8s_pipeline.connection_manager, 'get_redis_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_redis
            
            # Concurrent cache operations
            async def cache_operation(suffix):
                await k8s_pipeline.cache_evaluation_metrics(f"model_{suffix}", "race_test", test_metrics_v2)
                return await k8s_pipeline.get_cached_metrics(f"model_{suffix}", "race_test")
            
            # Run concurrent operations
            tasks = [cache_operation(i) for i in range(3)]
            results = await asyncio.gather(*tasks)
            
            # All should handle race conditions gracefully
            for result in results:
                assert result is not None
                assert "version" in result
    
    async def test_cache_size_limit_enforcement(self):
        """Test cache behavior when size limits are exceeded."""
        k8s_pipeline = KubernetesOptimizedPipeline(KubernetesResourceConfig())
        
        # Mock Redis with memory limit
        mock_redis = AsyncMock()
        cache_size = 0
        max_cache_size = 1000  # bytes
        
        async def mock_setex(key, ttl, value):
            nonlocal cache_size
            new_size = cache_size + len(value.encode())
            if new_size > max_cache_size:
                raise redis.ResponseError("OOM command not allowed when used memory > 'maxmemory'")
            cache_size = new_size
            return True
        
        mock_redis.setex = mock_setex
        
        with patch.object(k8s_pipeline.connection_manager, 'get_redis_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_redis
            
            # Try to cache large amounts of data
            large_metrics = {"data": "x" * 500}  # 500+ bytes per entry
            
            # First cache operation should succeed
            await k8s_pipeline.cache_evaluation_metrics("model1", "test1", large_metrics)
            
            # Second cache operation should also succeed
            await k8s_pipeline.cache_evaluation_metrics("model2", "test2", large_metrics)
            
            # Third operation should fail due to memory limit
            with pytest.raises(redis.ResponseError, match="maxmemory"):
                await k8s_pipeline.cache_evaluation_metrics("model3", "test3", large_metrics)


class TestMemoryPressureAndCleanup:
    """Test memory pressure scenarios and cleanup edge cases."""
    
    async def test_memory_cleanup_under_pressure(self):
        """Test memory cleanup when system is under memory pressure."""
        import psutil
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create large training data to simulate memory pressure
        large_training_data = TrainingDataBatch(
            hook_examples=[
                {"messages": [{"role": "user", "content": f"Large content {i}" * 1000}]}
                for i in range(100)
            ],
            body_examples=[
                {"messages": [{"role": "user", "content": f"Large body {i}" * 1000}]}
                for i in range(100)
            ],
            metadata={"collected_at": datetime.now()}
        )
        
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Verify memory increased significantly
        assert memory_increase > 5, f"Expected significant memory increase, got {memory_increase:.2f}MB"
        
        # Simulate cleanup (as done in pipeline)
        large_training_data.hook_examples.clear()
        large_training_data.body_examples.clear()
        del large_training_data
        gc.collect()
        
        # Allow time for garbage collection
        await asyncio.sleep(0.1)
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_recovered = peak_memory - final_memory
        
        # Should recover some memory (Python GC may not recover everything immediately)
        recovery_percentage = (memory_recovered / memory_increase) * 100
        assert recovery_percentage > 10, f"Only recovered {recovery_percentage:.1f}% of memory"
    
    async def test_chunked_processing_memory_bounds(self):
        """Test that chunked processing maintains memory bounds."""
        import psutil
        
        # Test with various chunk sizes
        chunk_sizes = [100, 500, 1000, 2000]
        data_size = 5000
        
        for chunk_size in chunk_sizes:
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            peak_memory = initial_memory
            
            # Simulate chunked processing
            for i in range(0, data_size, chunk_size):
                chunk_end = min(i + chunk_size, data_size)
                chunk_data = [f"item_{j}" * 10 for j in range(i, chunk_end)]
                
                # Process chunk
                processed = [item.upper() for item in chunk_data]
                
                # Check memory
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                peak_memory = max(peak_memory, current_memory)
                
                # Cleanup chunk
                del chunk_data, processed
            
            memory_increase = peak_memory - initial_memory
            
            # Memory increase should be roughly proportional to chunk size
            # Larger chunks should use more memory, but with a reasonable upper bound
            max_expected_increase = (chunk_size / 100) * 2  # 2MB per 100 items
            assert memory_increase <= max_expected_increase, \
                f"Chunk size {chunk_size} used {memory_increase:.2f}MB, expected <= {max_expected_increase:.2f}MB"
    
    async def test_memory_leak_detection(self):
        """Test detection of potential memory leaks in repeated operations."""
        import psutil
        
        async def memory_intensive_operation():
            # Create and process data
            data = ["content" * 100 for _ in range(1000)]
            processed = [item.upper() for item in data]
            
            # Simulate some async work
            await asyncio.sleep(0.01)
            
            # Return small result (data should be collected)
            return len(processed)
        
        memory_measurements = []
        
        # Run operation multiple times
        for i in range(10):
            await memory_intensive_operation()
            
            # Force garbage collection
            gc.collect()
            await asyncio.sleep(0.01)
            
            # Measure memory
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_measurements.append(current_memory)
        
        # Check for memory leak pattern
        if len(memory_measurements) >= 5:
            # Compare first half with second half
            first_half = memory_measurements[:5]
            second_half = memory_measurements[5:]
            
            avg_first_half = sum(first_half) / len(first_half)
            avg_second_half = sum(second_half) / len(second_half)
            
            memory_growth = avg_second_half - avg_first_half
            
            # Should not have significant memory growth (allow some variance)
            assert memory_growth < 10, f"Potential memory leak detected: {memory_growth:.2f}MB growth"


class TestCircuitBreakerFailureScenarios:
    """Test circuit breaker behavior under various failure scenarios."""
    
    async def test_circuit_breaker_with_intermittent_failures(self):
        """Test circuit breaker with intermittent failure patterns."""
        cb = CircuitBreaker(failure_threshold=3, timeout=0.2)
        
        call_count = 0
        
        async def intermittent_function():
            nonlocal call_count
            call_count += 1
            # Fail every 3rd call
            if call_count % 3 == 0:
                raise Exception(f"Intermittent failure #{call_count}")
            return f"success #{call_count}"
        
        # Should handle intermittent failures without opening
        results = []
        for i in range(8):
            try:
                result = await cb.call(intermittent_function)
                results.append(result)
            except Exception as e:
                results.append(f"failed: {str(e)}")
        
        # Circuit should stay closed with intermittent failures
        assert cb.state == "CLOSED"
        
        # Should have some successes and some failures
        successes = [r for r in results if r.startswith("success")]
        failures = [r for r in results if r.startswith("failed")]
        
        assert len(successes) > 0
        assert len(failures) > 0
        assert len(successes) + len(failures) == 8
    
    async def test_circuit_breaker_rapid_failure_recovery(self):
        """Test circuit breaker with rapid failure and recovery cycles."""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)
        
        failure_mode = True
        
        async def toggling_function():
            nonlocal failure_mode
            if failure_mode:
                raise Exception("Service down")
            return "service recovered"
        
        # Trigger circuit breaker opening
        for _ in range(2):
            with pytest.raises(Exception, match="Service down"):
                await cb.call(toggling_function)
        
        assert cb.state == "OPEN"
        
        # Wait for timeout
        await asyncio.sleep(0.12)
        
        # Enable recovery
        failure_mode = False
        
        # Should transition through half-open to closed
        result = await cb.call(toggling_function)
        assert result == "service recovered"
        assert cb.state == "CLOSED"
        
        # Subsequent calls should work normally
        result = await cb.call(toggling_function)
        assert result == "service recovered"
        assert cb.state == "CLOSED"
    
    async def test_circuit_breaker_timeout_variations(self):
        """Test circuit breaker with different timeout scenarios."""
        # Test very short timeout
        cb_short = CircuitBreaker(failure_threshold=2, timeout=0.05)
        
        async def failing_function():
            raise Exception("Always fails")
        
        # Open circuit
        for _ in range(2):
            with pytest.raises(Exception, match="Always fails"):
                await cb_short.call(failing_function)
        
        assert cb_short.state == "OPEN"
        
        # Should still be open before timeout
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await cb_short.call(failing_function)
        
        # Wait for very short timeout
        await asyncio.sleep(0.06)
        
        # Should attempt call again (will fail and re-open)
        with pytest.raises(Exception, match="Always fails"):
            await cb_short.call(failing_function)
        
        assert cb_short.state == "OPEN"
    
    async def test_circuit_breaker_concurrent_failures(self):
        """Test circuit breaker with concurrent failure scenarios."""
        cb = CircuitBreaker(failure_threshold=3, timeout=0.5)
        
        async def concurrent_failing_function(delay: float):
            await asyncio.sleep(delay)
            raise Exception(f"Concurrent failure after {delay}s")
        
        # Launch concurrent failing operations
        tasks = [
            asyncio.create_task(cb.call(concurrent_failing_function, 0.01)),
            asyncio.create_task(cb.call(concurrent_failing_function, 0.02)),
            asyncio.create_task(cb.call(concurrent_failing_function, 0.03)),
            asyncio.create_task(cb.call(concurrent_failing_function, 0.04))
        ]
        
        # All should fail
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all failed
        assert all(isinstance(r, Exception) for r in results)
        
        # Circuit should be open after threshold failures
        assert cb.state == "OPEN"
        assert cb.failure_count >= 3


class TestNetworkTimeoutAndRetryLogic:
    """Test network timeout handling and retry logic."""
    
    async def test_openai_api_timeout_with_retry(self):
        """Test OpenAI API timeout handling with retry logic."""
        trainer = ModelTrainer(base_model="gpt-3.5-turbo-0125")
        
        training_data = TrainingDataBatch(
            hook_examples=[{"messages": [{"role": "user", "content": "test"}]}],
            body_examples=[{"messages": [{"role": "user", "content": "test"}]}],
            metadata={"collected_at": datetime.now()}
        )
        
        call_count = 0
        
        async def timeout_then_succeed(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                await asyncio.sleep(0.2)  # Timeout simulation
                raise asyncio.TimeoutError("Request timed out")
            return Mock(id="file-success")
        
        mock_client = AsyncMock()
        mock_client.files.create = timeout_then_succeed
        mock_client.fine_tuning.jobs.create = AsyncMock(return_value=Mock(id="job-success"))
        
        with patch('openai.AsyncOpenAI', return_value=mock_client):
            # Should succeed after retries
            result = await trainer.start_fine_tuning(training_data)
            
            assert result.training_job_id == "job-success"
            assert call_count == 3  # Failed twice, succeeded on third attempt
    
    async def test_database_connection_timeout_recovery(self):
        """Test database connection timeout and recovery."""
        k8s_pipeline = KubernetesOptimizedPipeline(KubernetesResourceConfig())
        
        call_count = 0
        
        async def timeout_then_recover(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                raise asyncio.TimeoutError("Database connection timeout")
            
            # Return successful result
            return [
                {
                    'id': 1,
                    'hook': 'Test hook',
                    'body': 'Test body',
                    'engagement_rate': 0.08,
                    'ts': datetime.now(),
                    'tokens_used': 100
                }
            ]
        
        mock_connection = AsyncMock()
        mock_connection.fetch = timeout_then_recover
        
        with patch.object(k8s_pipeline.connection_manager, 'get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            
            # First call should timeout
            with pytest.raises(asyncio.TimeoutError):
                await k8s_pipeline.collect_training_data_optimized(0.06, 7)
            
            # Second call should succeed
            result = await k8s_pipeline.collect_training_data_optimized(0.06, 7)
            
            assert len(result["hook_examples"]) == 1
            assert call_count == 2
    
    async def test_redis_connection_timeout_graceful_degradation(self):
        """Test Redis connection timeout with graceful degradation."""
        k8s_pipeline = KubernetesOptimizedPipeline(KubernetesResourceConfig())
        
        test_metrics = {"test": "data"}
        
        async def timeout_connection(*args, **kwargs):
            await asyncio.sleep(0.1)
            raise asyncio.TimeoutError("Redis connection timeout")
        
        with patch.object(k8s_pipeline.connection_manager, 'get_redis_connection') as mock_get_conn:
            mock_get_conn.side_effect = timeout_connection
            
            # Should handle timeout gracefully without raising
            await k8s_pipeline.cache_evaluation_metrics("model", "test", test_metrics)
            
            # Get should also handle timeout gracefully
            result = await k8s_pipeline.get_cached_metrics("model", "test")
            assert result is None  # Should return None instead of crashing


class TestResourceLimitEnforcement:
    """Test resource limit enforcement and handling."""
    
    async def test_memory_limit_enforcement(self):
        """Test enforcement of memory limits during processing."""
        import psutil
        
        # Simulate memory limit checking
        class MemoryLimitedProcessor:
            def __init__(self, memory_limit_mb: float):
                self.memory_limit_mb = memory_limit_mb
                self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            def check_memory_limit(self):
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                memory_usage = current_memory - self.initial_memory
                if memory_usage > self.memory_limit_mb:
                    raise MemoryError(f"Memory usage {memory_usage:.1f}MB exceeds limit {self.memory_limit_mb}MB")
            
            async def process_with_limit_check(self, data_size: int):
                processor = []
                
                try:
                    for i in range(data_size):
                        # Add data
                        processor.append(f"data_item_{i}" * 100)
                        
                        # Check memory every 100 items
                        if i % 100 == 0:
                            self.check_memory_limit()
                    
                    return len(processor)
                    
                except MemoryError:
                    # Cleanup on memory limit exceeded
                    processor.clear()
                    gc.collect()
                    raise
        
        # Test with reasonable limit
        processor = MemoryLimitedProcessor(memory_limit_mb=50)
        
        # Small dataset should succeed
        result = await processor.process_with_limit_check(100)
        assert result == 100
        
        # Large dataset should hit memory limit
        with pytest.raises(MemoryError, match="exceeds limit"):
            await processor.process_with_limit_check(5000)
    
    async def test_concurrent_operation_limit_enforcement(self):
        """Test enforcement of concurrent operation limits."""
        
        class ConcurrencyLimitedExecutor:
            def __init__(self, max_concurrent: int):
                self.max_concurrent = max_concurrent
                self.semaphore = asyncio.Semaphore(max_concurrent)
                self.active_count = 0
            
            async def execute_with_limit(self, operation_id: int, duration: float):
                async with self.semaphore:
                    self.active_count += 1
                    try:
                        # Verify limit is enforced
                        assert self.active_count <= self.max_concurrent, \
                            f"Active count {self.active_count} exceeds limit {self.max_concurrent}"
                        
                        await asyncio.sleep(duration)
                        return f"operation_{operation_id}_completed"
                    finally:
                        self.active_count -= 1
        
        # Test with limit of 3 concurrent operations
        executor = ConcurrencyLimitedExecutor(max_concurrent=3)
        
        # Launch 10 operations that should be limited to 3 concurrent
        tasks = [
            executor.execute_with_limit(i, 0.1)
            for i in range(10)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        # All operations should complete
        assert len(results) == 10
        assert all("completed" in result for result in results)
        
        # Duration should reflect concurrency limit
        # 10 operations with 3 concurrent should take roughly 10/3 * 0.1 = 0.33s
        expected_min_duration = 0.25  # Allow some variance
        assert duration >= expected_min_duration, \
            f"Duration {duration:.2f}s too short, expected >= {expected_min_duration}s"
    
    async def test_timeout_limit_enforcement(self):
        """Test enforcement of operation timeout limits."""
        
        async def operation_with_timeout(operation_duration: float, timeout_limit: float):
            """Execute operation with timeout enforcement."""
            try:
                return await asyncio.wait_for(
                    asyncio.sleep(operation_duration),
                    timeout=timeout_limit
                )
            except asyncio.TimeoutError:
                return "timeout_exceeded"
        
        # Test operation within timeout
        result = await operation_with_timeout(0.1, 0.2)
        assert result is None  # asyncio.sleep returns None
        
        # Test operation exceeding timeout
        result = await operation_with_timeout(0.3, 0.1)
        assert result == "timeout_exceeded"
        
        # Test multiple concurrent operations with timeouts
        tasks = [
            operation_with_timeout(0.05, 0.1),  # Should succeed
            operation_with_timeout(0.15, 0.1),  # Should timeout
            operation_with_timeout(0.08, 0.1),  # Should succeed
            operation_with_timeout(0.2, 0.1),   # Should timeout
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Check expected results
        assert results[0] is None  # Success
        assert results[1] == "timeout_exceeded"  # Timeout
        assert results[2] is None  # Success
        assert results[3] == "timeout_exceeded"  # Timeout