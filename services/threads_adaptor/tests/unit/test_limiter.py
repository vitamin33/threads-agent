"""
Unit tests for token-bucket rate limiter.

Tests that the limiter correctly enforces rate limits and inserts pauses
when the rate is exceeded.
"""

import asyncio
import os
import time
from unittest.mock import AsyncMock, patch

import pytest

from services.threads_adaptor.limiter import (
    TokenBucketLimiter,
    get_rate_limiter,
    rate_limited_call,
)


class TestTokenBucketLimiter:
    """Test the TokenBucketLimiter class."""

    def test_init_default_rate(self) -> None:
        """Test limiter initialization with default rate."""
        limiter = TokenBucketLimiter()
        assert limiter.max_tokens == 20  # Default THREADS_RATE
        assert limiter.refill_rate == 20 / 60.0  # 20 tokens per minute = 1/3 per second
        assert limiter.tokens == 20

    def test_init_env_override(self) -> None:
        """Test limiter initialization with THREADS_RATE environment variable."""
        with patch.dict(os.environ, {"THREADS_RATE": "10"}):
            limiter = TokenBucketLimiter()
            assert limiter.max_tokens == 10
            assert limiter.refill_rate == 10 / 60.0

    def test_init_custom_params(self) -> None:
        """Test limiter initialization with custom parameters."""
        limiter = TokenBucketLimiter(max_tokens=5, refill_rate=0.1)
        assert limiter.max_tokens == 5
        assert limiter.refill_rate == 0.1
        assert limiter.tokens == 5

    def test_acquire_nowait_success(self) -> None:
        """Test acquiring token when tokens are available."""
        limiter = TokenBucketLimiter(max_tokens=5)
        assert limiter.acquire_nowait() is True
        assert limiter.tokens == 4.0

    def test_acquire_nowait_failure(self) -> None:
        """Test acquiring token when no tokens are available."""
        limiter = TokenBucketLimiter(max_tokens=1, refill_rate=0.0)

        # Consume the only token
        assert limiter.acquire_nowait() is True
        assert limiter.tokens == 0.0

        # Try to acquire another token immediately
        assert limiter.acquire_nowait() is False
        assert limiter.tokens == 0.0

    def test_token_refill(self) -> None:
        """Test that tokens are refilled over time."""
        limiter = TokenBucketLimiter(
            max_tokens=10, refill_rate=1.0
        )  # 1 token per second

        # Consume all tokens
        limiter.tokens = 0.0

        # Use fixed timestamps to avoid floating-point precision issues
        fixed_time = 1000.0
        limiter.last_refill = fixed_time

        # Simulate 2 seconds passing by setting last_refill to 2 seconds ago
        limiter.last_refill = fixed_time - 2.0

        # Mock time.time() to return the current fixed time
        with patch(
            "services.threads_adaptor.limiter.time.time", return_value=fixed_time
        ):
            limiter._refill_tokens()

        # Should have refilled 2 tokens
        assert limiter.tokens == 2.0

    def test_token_refill_max_cap(self) -> None:
        """Test that token refill respects max_tokens cap."""
        limiter = TokenBucketLimiter(max_tokens=5, refill_rate=10.0)  # Very fast refill

        # Simulate 10 seconds passing (would refill 100 tokens without cap)
        limiter.last_refill = time.time() - 10.0
        limiter._refill_tokens()

        # Should be capped at max_tokens
        assert limiter.tokens == 5.0


class TestRateLimitedCalls:
    """Test rate-limited function calls."""

    @pytest.mark.asyncio
    async def test_successful_call(self) -> None:
        """Test successful rate-limited call."""
        mock_func = AsyncMock(return_value="success")

        result = await rate_limited_call(mock_func, "arg1", keyword="arg2")

        assert result == "success"
        mock_func.assert_called_once_with("arg1", keyword="arg2")

    @pytest.mark.asyncio
    async def test_429_retry_mechanism(self) -> None:
        """Test that 429 errors trigger retry with exponential backoff."""

        class MockHTTPError(Exception):
            def __init__(self, status_code: int) -> None:
                self.status_code = status_code

        mock_func = AsyncMock()
        mock_func.side_effect = [
            MockHTTPError(429),  # First call: 429
            MockHTTPError(429),  # Second call: 429
            "success",  # Third call: success
        ]

        # Mock sleep to speed up test
        with patch("asyncio.sleep"):
            result = await rate_limited_call(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3


class TestHighVolumeRateLimiting:
    """Test rate limiting under high volume - the main requirement from CRA-213."""

    @pytest.mark.asyncio
    async def test_25_calls_inserts_pauses(self) -> None:
        """
        Test that firing 25 calls results in ≥5 pauses (as specified in ticket).

        This is the key test requirement: "Unit-test fires 25 calls→ sleep inserts ≥5 pauses"
        """
        # Set up a very restrictive rate limiter (5 tokens max, slow refill)
        # This ensures we'll hit the rate limit and need to pause
        limiter = TokenBucketLimiter(max_tokens=5, refill_rate=0.5)  # 0.5 tokens/sec

        pause_count = 0

        # Save the original sleep function before any mocking
        original_sleep = asyncio.sleep

        async def counting_sleep(duration: float) -> None:
            nonlocal pause_count
            pause_count += 1
            # Use a very short sleep for testing to speed up the test
            # Use the saved original sleep to avoid recursion
            await original_sleep(0.001)

        start_time = time.time()

        # Patch asyncio.sleep globally to count pauses and speed up test
        with patch("asyncio.sleep", side_effect=counting_sleep):
            # Fire 25 calls in rapid succession
            tasks = []
            for i in range(25):
                task = asyncio.create_task(limiter.acquire())
                tasks.append(task)

            # Wait for all acquisitions to complete
            await asyncio.gather(*tasks)

        end_time = time.time()

        # Verify we had ≥5 pauses as required by the ticket
        assert pause_count >= 5, f"Expected ≥5 pauses, got {pause_count}"

        # Verify test ran reasonably fast (with mocked sleep)
        assert (
            end_time - start_time < 1.0
        ), "Test took too long, sleep mocking may have failed"

    @pytest.mark.asyncio
    async def test_burst_then_steady_rate(self) -> None:
        """Test burst consumption followed by steady rate."""
        limiter = TokenBucketLimiter(
            max_tokens=3, refill_rate=1.0
        )  # 1 token per second

        # Burst: consume all 3 tokens immediately
        assert limiter.acquire_nowait() is True  # token 1
        assert limiter.acquire_nowait() is True  # token 2
        assert limiter.acquire_nowait() is True  # token 3
        assert limiter.acquire_nowait() is False  # no more tokens

        # Now test that acquire() waits for refill
        # This should wait ~1 second for next token
        with patch("asyncio.sleep") as mock_sleep:
            await limiter.acquire()

            # Verify sleep was called (indicating rate limiting kicked in)
            assert mock_sleep.called
            # Sleep duration should be approximately 1 second (1 token / 1 token per second)
            sleep_duration = mock_sleep.call_args[0][0]
            assert 0.8 <= sleep_duration <= 1.2


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

    def test_threads_rate_environment_variable(self) -> None:
        """Test that THREADS_RATE environment variable is respected."""
        test_cases = [("5", 5), ("50", 50), ("100", 100)]

        for env_value, expected_rate in test_cases:
            with patch.dict(os.environ, {"THREADS_RATE": env_value}):
                limiter = TokenBucketLimiter()
                assert limiter.max_tokens == expected_rate
                assert limiter.refill_rate == expected_rate / 60.0

    def test_global_rate_limiter_singleton(self) -> None:
        """Test that get_rate_limiter returns the same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        assert limiter1 is limiter2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_non_429_exception_passthrough(self) -> None:
        """Test that non-429 exceptions are passed through without retry."""
        mock_func = AsyncMock(side_effect=ValueError("not a rate limit error"))

        with pytest.raises(ValueError, match="not a rate limit error"):
            await rate_limited_call(mock_func)

        # Should only be called once (no retry)
        assert mock_func.call_count == 1

    def test_zero_refill_rate(self) -> None:
        """Test limiter with zero refill rate."""
        limiter = TokenBucketLimiter(max_tokens=1, refill_rate=0.0)

        # Consume the token
        assert limiter.acquire_nowait() is True

        # Simulate time passing - should not refill any tokens
        limiter.last_refill = time.time() - 1000.0
        limiter._refill_tokens()

        assert limiter.tokens == 0.0

    def test_negative_time_handling(self) -> None:
        """Test that negative elapsed time doesn't break the limiter."""
        limiter = TokenBucketLimiter(max_tokens=10, refill_rate=1.0)

        # Set last_refill to future time (simulates clock adjustment)
        limiter.last_refill = time.time() + 100.0
        limiter.tokens = 5.0

        # This should not crash or create negative tokens
        limiter._refill_tokens()

        # Tokens should remain at their current level (no negative refill)
        assert limiter.tokens >= 5.0
