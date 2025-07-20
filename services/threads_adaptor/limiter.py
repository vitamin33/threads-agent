# services/threads_adaptor/limiter.py
"""
Token-bucket rate limiter for Threads API with exponential backoff.

Implements a simple in-memory leaky-bucket rate limiter that:
- Defaults to 20 requests per minute
- Falls back to sleep/backoff 0.5-32s on 429 responses
- Supports THREADS_RATE environment variable override
"""

import asyncio
import os
import time
from typing import Any, Callable, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded."""

    pass


class TokenBucketLimiter:
    """
    In-memory token bucket rate limiter.

    Uses leaky-bucket algorithm:
    - Tokens are added at a fixed rate (refill_rate)
    - Each request consumes one token
    - If no tokens available, request is delayed
    """

    def __init__(
        self, max_tokens: Optional[int] = None, refill_rate: Optional[float] = None
    ) -> None:
        # Get rate from environment variable or use default
        threads_rate = int(os.getenv("THREADS_RATE", "20"))

        self.max_tokens = max_tokens or threads_rate
        self.refill_rate = (
            refill_rate if refill_rate is not None else (threads_rate / 60.0)
        )  # tokens per second

        self.tokens = float(self.max_tokens)
        self.last_refill = time.time()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        # Handle negative elapsed time (clock adjustments, etc.)
        if elapsed < 0:
            elapsed = 0

        self.last_refill = now

        # Add tokens based on elapsed time, but only if refill_rate > 0
        if self.refill_rate > 0:
            self.tokens = min(
                self.max_tokens, self.tokens + (elapsed * self.refill_rate)
            )

    async def acquire(self) -> None:
        """
        Acquire a token from the bucket.

        If no tokens are available, sleeps until a token becomes available.
        """
        self._refill_tokens()

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return

        # If no tokens available, calculate sleep time and wait
        if self.refill_rate <= 0:
            raise RuntimeError("Cannot acquire token: refill rate is zero")

        # Calculate how long to sleep to get at least one token
        # We add a small buffer to account for timing precision
        tokens_needed = 1.0 - self.tokens
        sleep_time = tokens_needed / self.refill_rate

        await asyncio.sleep(sleep_time)

        # After sleeping, refill and consume the token
        self._refill_tokens()
        self.tokens = max(0.0, self.tokens - 1.0)

    def acquire_nowait(self) -> bool:
        """
        Try to acquire a token without waiting.

        Returns:
            True if token was acquired, False if no tokens available
        """
        self._refill_tokens()

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True

        return False


# Global rate limiter instance
_rate_limiter = TokenBucketLimiter()


def get_rate_limiter() -> TokenBucketLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1, min=0.5, max=32),
    stop=stop_after_attempt(5),
)
async def with_rate_limit_retry(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> Any:
    """
    Execute a function with rate limiting and exponential backoff on 429 errors.

    Args:
        func: The function to execute
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call

    Raises:
        RateLimitError: If 429 response is received (will trigger retry)
    """
    # Acquire token before making request
    await get_rate_limiter().acquire()

    try:
        result = await func(*args, **kwargs)
        return result
    except Exception as e:
        # Check if it's a 429 rate limit error
        if hasattr(e, "status_code") and getattr(e, "status_code") == 429:
            raise RateLimitError(f"Rate limit exceeded: {e}") from e
        # Re-raise other exceptions as-is
        raise


async def rate_limited_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    Convenience function to make rate-limited API calls.

    Usage:
        result = await rate_limited_call(api_client.post, url, data=data)
    """
    return await with_rate_limit_retry(func, *args, **kwargs)
