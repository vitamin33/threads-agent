import asyncio
import time
from typing import Any, Callable, Dict
from enum import Enum
import structlog
from functools import wraps

logger = structlog.get_logger()


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern for external API calls"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable) -> Callable:
        """Decorator to apply circuit breaker to function"""

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(
                        "Circuit breaker moving to HALF_OPEN", func=func.__name__
                    )
                else:
                    raise Exception(f"Circuit breaker OPEN for {func.__name__}")

            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time
            and time.time() - self.last_failure_time >= self.timeout
        )

    def _on_success(self):
        """Reset failure count on successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Increment failure count and update state"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker OPEN",
                failures=self.failure_count,
                threshold=self.failure_threshold,
            )


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def with_retry(config: RetryConfig = None, retryable_exceptions: tuple = (Exception,)):
    """Decorator for exponential backoff retry with jitter"""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts - 1:
                        logger.error(
                            "All retry attempts failed",
                            func=func.__name__,
                            attempts=config.max_attempts,
                            error=str(e),
                        )
                        raise e

                    delay = min(
                        config.base_delay * (config.exponential_base**attempt),
                        config.max_delay,
                    )

                    if config.jitter:
                        import random

                        delay *= 0.5 + random.random() * 0.5  # Add 0-50% jitter

                    logger.warning(
                        "Retrying after failure",
                        func=func.__name__,
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                    )

                    await asyncio.sleep(delay)

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


class RateLimiter:
    """Token bucket rate limiter for API calls"""

    def __init__(self, max_tokens: int, refill_rate: float):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = max_tokens
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from the bucket"""
        async with self._lock:
            now = time.time()

            # Refill tokens based on time elapsed
            time_elapsed = now - self.last_refill
            self.tokens = min(
                self.max_tokens, self.tokens + (time_elapsed * self.refill_rate)
            )
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    async def wait_for_tokens(self, tokens: int = 1):
        """Wait until tokens are available"""
        while not await self.acquire(tokens):
            await asyncio.sleep(0.1)


# Global circuit breakers for different services
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get or create circuit breaker for service"""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker(
            failure_threshold=5, timeout=60
        )
    return _circuit_breakers[service_name]


# Rate limiters for different APIs
_rate_limiters: Dict[str, RateLimiter] = {
    "openai": RateLimiter(max_tokens=10, refill_rate=1.0),  # 10 requests, 1 per second
    "devto": RateLimiter(max_tokens=5, refill_rate=0.1),  # 5 requests, 1 per 10 seconds
    "linkedin": RateLimiter(
        max_tokens=3, refill_rate=0.05
    ),  # 3 requests, 1 per 20 seconds
}


def get_rate_limiter(service_name: str) -> RateLimiter:
    """Get rate limiter for service"""
    return _rate_limiters.get(service_name, RateLimiter(10, 1.0))


async def resilient_api_call(func: Callable, service_name: str, *args, **kwargs) -> Any:
    """Make resilient API call with circuit breaker, retry, and rate limiting"""

    # Apply rate limiting
    rate_limiter = get_rate_limiter(service_name)
    await rate_limiter.wait_for_tokens()

    # Apply circuit breaker and retry
    circuit_breaker = get_circuit_breaker(service_name)
    retry_config = RetryConfig(max_attempts=3, base_delay=1.0)

    @circuit_breaker.call
    @with_retry(retry_config)
    async def protected_call():
        return await func(*args, **kwargs)

    return await protected_call()
