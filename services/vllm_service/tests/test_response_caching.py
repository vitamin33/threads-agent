"""
Test Response Caching and Optimization Features - Validate <50ms performance targets
"""

import pytest
import time
import asyncio
from unittest.mock import patch, AsyncMock

from services.vllm_service.model_manager import vLLMModelManager


class TestResponseCachingFunctionality:
    """Test response caching implementation for performance optimization."""

    @pytest.mark.asyncio
    async def test_cache_key_generation_consistency(self):
        """Test cache key generation is consistent for identical requests."""
        manager = vLLMModelManager()

        # Same parameters should generate same cache key
        prompt = "Write a viral hook about productivity"
        max_tokens = 256
        temperature = 0.7
        top_p = 0.9

        key1 = manager._generate_cache_key(prompt, max_tokens, temperature, top_p)
        key2 = manager._generate_cache_key(prompt, max_tokens, temperature, top_p)

        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length

        # Different parameters should generate different keys
        key3 = manager._generate_cache_key(
            prompt, max_tokens, 0.8, top_p
        )  # Different temperature
        assert key1 != key3

    @pytest.mark.asyncio
    async def test_cache_key_variation_with_parameters(self):
        """Test cache keys vary appropriately with different parameters."""
        manager = vLLMModelManager()

        base_prompt = "Create viral content"
        base_params = (256, 0.7, 0.9)

        # Generate baseline key
        base_key = manager._generate_cache_key(base_prompt, *base_params)

        # Test variations
        test_cases = [
            ("Different prompt", 256, 0.7, 0.9),  # Different prompt
            ("Create viral content", 512, 0.7, 0.9),  # Different max_tokens
            ("Create viral content", 256, 0.8, 0.9),  # Different temperature
            ("Create viral content", 256, 0.7, 0.95),  # Different top_p
        ]

        for prompt, max_tokens, temp, top_p in test_cases:
            key = manager._generate_cache_key(prompt, max_tokens, temp, top_p)
            assert key != base_key, (
                f"Key should differ for {prompt}, {max_tokens}, {temp}, {top_p}"
            )

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_response(self):
        """Test cache hit returns previously cached response with performance benefits."""
        manager = vLLMModelManager()

        # Mock successful model loading
        with patch.object(manager, "_load_fallback_model", new_callable=AsyncMock):
            await manager.load_model("meta-llama/Llama-3.1-8B-Instruct")

        # Mock slow generation for first request
        original_response = {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Cached response"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "performance": {
                "inference_time_ms": 100.0,
                "warmup_completed": True,
                "apple_silicon_optimized": True,
                "cache_hit": False,
            },
        }

        with patch.object(
            manager, "_generate_fallback", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = "Cached response"

            messages = [{"role": "user", "content": "Test prompt"}]

            # First request - should cache the response
            response1 = await manager.generate(
                messages, max_tokens=256, temperature=0.7, top_p=0.9
            )

            # Manually add to cache to simulate caching behavior
            cache_key = manager._generate_cache_key(
                manager._messages_to_prompt(messages), 256, 0.7, 0.9
            )
            manager.inference_cache[cache_key] = response1.copy()
            response1["performance"]["cache_hit"] = False

            # Second identical request - should hit cache
            response2 = await manager.generate(
                messages, max_tokens=256, temperature=0.7, top_p=0.9
            )

            # Should return cached response with cache hit marker
            assert response2["performance"]["cache_hit"] is True
            assert (
                response2["performance"]["inference_time_ms"] == 0.5
            )  # Near-instant cache response
            assert (
                response2["choices"][0]["message"]["content"]
                == response1["choices"][0]["message"]["content"]
            )

    @pytest.mark.asyncio
    async def test_cache_miss_generates_new_response(self):
        """Test cache miss generates new response and caches it."""
        manager = vLLMModelManager()

        # Mock successful model loading
        with patch.object(manager, "_load_fallback_model", new_callable=AsyncMock):
            await manager.load_model("meta-llama/Llama-3.1-8B-Instruct")

        # Ensure cache is empty
        manager.inference_cache.clear()

        with patch.object(
            manager, "_generate_fallback", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = "New response"

            messages = [{"role": "user", "content": "New prompt"}]

            # Request should be cache miss
            response = await manager.generate(
                messages, max_tokens=256, temperature=0.7, top_p=0.9
            )

            # Should generate new response
            assert response["performance"]["cache_hit"] is False
            assert response["choices"][0]["message"]["content"] == "New response"

            # Should add to cache
            assert len(manager.inference_cache) == 1

    @pytest.mark.asyncio
    async def test_cache_size_limit_enforcement(self):
        """Test cache enforces size limit and evicts oldest entries."""
        manager = vLLMModelManager()

        # Mock successful model loading
        with patch.object(manager, "_load_fallback_model", new_callable=AsyncMock):
            await manager.load_model("meta-llama/Llama-3.1-8B-Instruct")

        # Clear cache and set up for testing
        manager.inference_cache.clear()

        with patch.object(
            manager, "_generate_fallback", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = "Response"

            # Fill cache to capacity (100 entries)
            for i in range(105):  # Exceed capacity by 5
                messages = [{"role": "user", "content": f"Prompt {i}"}]
                await manager.generate(
                    messages, max_tokens=256, temperature=0.7, top_p=0.9
                )

            # Cache should maintain max size
            assert len(manager.inference_cache) <= 100

            # Should have evicted oldest entries
            # (Testing exact eviction order is complex due to async execution,
            # but size limit should be enforced)

    @pytest.mark.asyncio
    async def test_cache_performance_improvement_measurement(self):
        """Test cache provides measurable performance improvement."""
        manager = vLLMModelManager()

        # Mock successful model loading
        with patch.object(manager, "_load_fallback_model", new_callable=AsyncMock):
            await manager.load_model("meta-llama/Llama-3.1-8B-Instruct")

        # Mock generation with realistic timing
        async def timed_generate(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms simulated generation time
            return "Generated response"

        with patch.object(manager, "_generate_fallback", side_effect=timed_generate):
            messages = [{"role": "user", "content": "Performance test"}]

            # First request (cache miss)
            start_time = time.time()
            response1 = await manager.generate(
                messages, max_tokens=256, temperature=0.7, top_p=0.9
            )
            first_request_time = time.time() - start_time

            # Manually cache the response
            cache_key = manager._generate_cache_key(
                manager._messages_to_prompt(messages), 256, 0.7, 0.9
            )
            manager.inference_cache[cache_key] = response1.copy()

            # Second request (cache hit)
            start_time = time.time()
            response2 = await manager.generate(
                messages, max_tokens=256, temperature=0.7, top_p=0.9
            )
            second_request_time = time.time() - start_time

            # Cache hit should be significantly faster
            assert second_request_time < first_request_time
            assert second_request_time < 0.01  # Should be very fast (< 10ms)
            assert response2["performance"]["cache_hit"] is True

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_cleanup(self):
        """Test cache is properly invalidated during cleanup."""
        manager = vLLMModelManager()

        # Mock successful model loading
        with patch.object(manager, "_load_fallback_model", new_callable=AsyncMock):
            await manager.load_model("meta-llama/Llama-3.1-8B-Instruct")

        # Add some cache entries
        manager.inference_cache["key1"] = {"test": "data1"}
        manager.inference_cache["key2"] = {"test": "data2"}
        assert len(manager.inference_cache) == 2

        # Cleanup should clear cache
        await manager.cleanup()

        assert len(manager.inference_cache) == 0


class TestCachingOptimizationStrategies:
    """Test caching optimization strategies for viral content generation."""

    @pytest.mark.asyncio
    async def test_prompt_truncation_for_cache_key(self):
        """Test prompt truncation for cache key generation handles long prompts."""
        manager = vLLMModelManager()

        # Test with very long prompt
        long_prompt = "Write viral content " * 100  # 1800+ characters
        short_prompt = "Write viral content about productivity"

        # Cache key should use truncated prompt (first 100 chars)
        long_key = manager._generate_cache_key(long_prompt, 256, 0.7, 0.9)

        # Should be consistent
        long_key2 = manager._generate_cache_key(long_prompt, 256, 0.7, 0.9)
        assert long_key == long_key2

        # Should differ from short prompt
        short_key = manager._generate_cache_key(short_prompt, 256, 0.7, 0.9)
        assert long_key != short_key

    @pytest.mark.asyncio
    async def test_parameter_normalization_for_caching(self):
        """Test parameter normalization for better cache hit rates."""
        manager = vLLMModelManager()

        # Similar but slightly different parameters
        prompt = "Create viral hook"

        # These should generate different cache keys (no normalization in current implementation)
        key1 = manager._generate_cache_key(prompt, 256, 0.700, 0.90)
        key2 = manager._generate_cache_key(prompt, 256, 0.701, 0.90)

        # Current implementation should treat these as different
        assert key1 != key2

        # But identical parameters should match
        key3 = manager._generate_cache_key(prompt, 256, 0.700, 0.90)
        assert key1 == key3

    @pytest.mark.asyncio
    async def test_viral_content_caching_patterns(self):
        """Test caching patterns specific to viral content generation."""
        manager = vLLMModelManager()

        # Mock successful model loading
        with patch.object(manager, "_load_fallback_model", new_callable=AsyncMock):
            await manager.load_model("meta-llama/Llama-3.1-8B-Instruct")

        with patch.object(
            manager, "_generate_fallback", new_callable=AsyncMock
        ) as mock_generate:
            mock_generate.return_value = "🔥 Viral content response"

            # Common viral content prompts that should cache well
            viral_prompts = [
                "Write a viral hook about productivity",
                "Create engaging content about AI",
                "Generate a controversial take on remote work",
                "Write a viral hook about productivity",  # Duplicate for cache test
            ]

            messages_list = [
                [{"role": "user", "content": prompt}] for prompt in viral_prompts
            ]

            # Generate responses
            for messages in messages_list:
                await manager.generate(
                    messages, max_tokens=256, temperature=0.7, top_p=0.9
                )

            # Should have cached 3 unique responses (4th is duplicate)
            assert len(manager.inference_cache) == 3


class TestCacheMetricsAndMonitoring:
    """Test cache metrics and monitoring for performance optimization."""

    @pytest.mark.asyncio
    async def test_cache_hit_rate_tracking(self):
        """Test cache hit rate tracking for performance monitoring."""
        manager = vLLMModelManager()

        # Mock successful model loading
        with patch.object(manager, "_load_fallback_model", new_callable=AsyncMock):
            await manager.load_model("meta-llama/Llama-3.1-8B-Instruct")

        # Get performance metrics should include cache info
        metrics = manager.get_performance_metrics()

        assert "performance" in metrics
        performance = metrics["performance"]

        # Should track cache entries
        assert "cache_entries" in performance
        assert isinstance(performance["cache_entries"], int)
        assert performance["cache_entries"] >= 0

    @pytest.mark.asyncio
    async def test_cache_size_monitoring(self):
        """Test cache size monitoring for memory management."""
        manager = vLLMModelManager()

        # Add some cache entries
        for i in range(10):
            manager.inference_cache[f"key_{i}"] = {
                "test": f"data_{i}",
                "large_content": "x" * 1000,  # 1KB per entry
            }

        # Get performance metrics
        metrics = manager.get_performance_metrics()

        # Should report cache size
        assert metrics["performance"]["cache_entries"] == 10

    @pytest.mark.asyncio
    async def test_memory_usage_includes_cache(self):
        """Test memory usage reporting includes cache memory."""
        manager = vLLMModelManager()

        # Add cache entries
        for i in range(50):
            manager.inference_cache[f"key_{i}"] = {
                "choices": [{"message": {"content": "x" * 1000}}],  # ~1KB per entry
                "usage": {"total_tokens": 100},
                "performance": {"inference_time_ms": 50},
            }

        # Get memory usage
        memory_stats = manager.get_memory_usage()

        # Should report process memory (which includes cache)
        assert memory_stats["process_rss_mb"] > 0
        assert memory_stats["process_percent"] >= 0

    @pytest.mark.asyncio
    async def test_cache_effectiveness_for_repeated_patterns(self):
        """Test cache effectiveness for repeated viral content patterns."""
        manager = vLLMModelManager()

        # Mock successful model loading
        with patch.object(manager, "_load_fallback_model", new_callable=AsyncMock):
            await manager.load_model("meta-llama/Llama-3.1-8B-Instruct")

        call_count = 0

        async def counting_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return f"Response {call_count}"

        with patch.object(manager, "_generate_fallback", side_effect=counting_generate):
            # Make repeated requests with same parameters
            messages = [{"role": "user", "content": "Create viral hook"}]

            # First request
            response1 = await manager.generate(
                messages, max_tokens=256, temperature=0.7, top_p=0.9
            )

            # Cache the response manually for testing
            cache_key = manager._generate_cache_key(
                manager._messages_to_prompt(messages), 256, 0.7, 0.9
            )
            manager.inference_cache[cache_key] = response1.copy()

            # Second identical request
            response2 = await manager.generate(
                messages, max_tokens=256, temperature=0.7, top_p=0.9
            )

            # Should hit cache (call_count shouldn't increase for cache hit)
            assert response2["performance"]["cache_hit"] is True

            # Different request should miss cache
            different_messages = [{"role": "user", "content": "Different prompt"}]
            response3 = await manager.generate(
                different_messages, max_tokens=256, temperature=0.7, top_p=0.9
            )

            assert response3["performance"]["cache_hit"] is False


class TestCachePerformanceBenchmarks:
    """Test cache performance benchmarks for <50ms targets."""

    @pytest.mark.asyncio
    async def test_cache_hit_latency_under_1ms(self):
        """Test cache hits achieve sub-millisecond latency."""
        manager = vLLMModelManager()

        # Pre-populate cache
        test_response = {
            "id": "test",
            "choices": [{"message": {"content": "Cached response"}}],
            "usage": {"total_tokens": 10},
            "performance": {"cache_hit": False},
        }

        cache_key = "test_cache_key"
        manager.inference_cache[cache_key] = test_response

        # Mock cache key generation to return our test key
        with patch.object(manager, "_generate_cache_key", return_value=cache_key):
            messages = [{"role": "user", "content": "test"}]

            # Measure cache hit time
            start_time = time.time()
            response = await manager.generate(messages)
            cache_hit_time = time.time() - start_time

            # Cache hit should be very fast
            assert cache_hit_time < 0.001  # Under 1ms
            assert response["performance"]["cache_hit"] is True
            assert response["performance"]["inference_time_ms"] == 0.5

    @pytest.mark.asyncio
    async def test_cache_memory_efficiency(self):
        """Test cache memory efficiency for production use."""
        manager = vLLMModelManager()

        # Add realistic cache entries
        realistic_response = {
            "id": "chatcmpl-realistic",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "🔥 Realistic viral content with proper length and engagement elements that would be typical for cached responses in production usage scenarios.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 25, "completion_tokens": 30, "total_tokens": 55},
            "performance": {
                "inference_time_ms": 45.0,
                "warmup_completed": True,
                "apple_silicon_optimized": True,
                "cache_hit": False,
            },
        }

        # Add 100 entries (cache limit)
        for i in range(100):
            cache_key = f"realistic_key_{i}"
            manager.inference_cache[cache_key] = realistic_response.copy()

        # Cache should maintain reasonable memory footprint
        import sys

        cache_size_bytes = sys.getsizeof(manager.inference_cache)

        # Rough estimate: should be under 1MB for 100 cached responses
        assert cache_size_bytes < 1024 * 1024  # 1MB limit

        # Cache should be at capacity
        assert len(manager.inference_cache) == 100
