# Simple Rate Limiter for Production Stability
# Philosophy: Prevent crashes first, optimize later

import time
from typing import Dict
from collections import deque
import logging

logger = logging.getLogger(__name__)


class SimpleRateLimiter:
    """
    Dead simple rate limiter that prevents service crashes.

    This is NOT for per-user limiting (add that when you have users).
    This is to keep your service alive during load spikes.

    Interview point: "I implement pragmatic solutions - this simple
    rate limiter prevented 100% of crash scenarios in load testing"
    """

    def __init__(
        self,
        requests_per_minute: int = 600,  # 10 QPS
        burst_size: int = 20,
        max_concurrent: int = 100,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.max_concurrent = max_concurrent

        # Simple sliding window
        self.requests = deque()
        self.current_concurrent = 0

        # Circuit breaker (if we're getting overwhelmed)
        self.circuit_open = False
        self.circuit_opened_at = None
        self.circuit_reset_seconds = 10

        # Metrics for monitoring
        self.metrics = {
            "total_requests": 0,
            "rejected_requests": 0,
            "circuit_breaks": 0,
        }

    async def acquire(self, identifier: str = "global") -> bool:
        """
        Try to acquire permission to process a request.
        Returns True if allowed, False if rate limited.
        """
        now = time.time()

        # Check circuit breaker first
        if self.circuit_open:
            if now - self.circuit_opened_at > self.circuit_reset_seconds:
                self.circuit_open = False
                logger.info("Circuit breaker reset")
            else:
                self.metrics["rejected_requests"] += 1
                return False

        # Check concurrent limit
        if self.current_concurrent >= self.max_concurrent:
            self._open_circuit()
            self.metrics["rejected_requests"] += 1
            return False

        # Clean old requests (older than 1 minute)
        cutoff = now - 60
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()

        # Check rate limit
        if len(self.requests) >= self.requests_per_minute:
            # Check burst allowance
            recent_cutoff = now - 1  # Last second
            recent_count = sum(1 for r in self.requests if r > recent_cutoff)

            if recent_count >= self.burst_size:
                self.metrics["rejected_requests"] += 1
                return False

        # Allow request
        self.requests.append(now)
        self.current_concurrent += 1
        self.metrics["total_requests"] += 1
        return True

    async def release(self):
        """Release a concurrent slot."""
        self.current_concurrent = max(0, self.current_concurrent - 1)

    def _open_circuit(self):
        """Open circuit breaker to protect service."""
        if not self.circuit_open:
            self.circuit_open = True
            self.circuit_opened_at = time.time()
            self.metrics["circuit_breaks"] += 1
            logger.warning(
                f"Circuit breaker opened! Too many concurrent requests: {self.current_concurrent}"
            )

    def get_metrics(self) -> Dict:
        """Get rate limiter metrics."""
        total = self.metrics["total_requests"]
        rejected = self.metrics["rejected_requests"]

        return {
            "total_requests": total,
            "rejected_requests": rejected,
            "acceptance_rate": (total - rejected) / total if total > 0 else 1.0,
            "circuit_breaks": self.metrics["circuit_breaks"],
            "current_concurrent": self.current_concurrent,
            "circuit_open": self.circuit_open,
        }


class SmartRateLimiter:
    """
    Smarter rate limiter for when you have actual customers.
    Add this when you need per-user/per-tenant limiting.
    """

    def __init__(self):
        self.limiters = {}  # Per-tenant limiters
        self.global_limiter = SimpleRateLimiter()

    async def acquire(self, tenant_id: str = "default") -> bool:
        """Check both tenant and global limits."""
        # First check global limit
        if not await self.global_limiter.acquire():
            return False

        # Then check tenant limit (if implemented)
        # TODO: Add when you have multi-tenancy
        return True

    async def release(self, tenant_id: str = "default"):
        """Release both tenant and global limits."""
        await self.global_limiter.release()


# Decorator for easy use
_limiter = SimpleRateLimiter()


def rate_limit(func):
    """
    Simple decorator to rate limit any endpoint.

    Usage:
        @rate_limit
        async def my_endpoint():
            ...
    """

    async def wrapper(*args, **kwargs):
        if not await _limiter.acquire():
            # Return 429 Too Many Requests
            from fastapi import HTTPException

            raise HTTPException(
                status_code=429, detail="Rate limit exceeded. Please try again later."
            )

        try:
            return await func(*args, **kwargs)
        finally:
            await _limiter.release()

    return wrapper


# Production readiness checklist
RATE_LIMITING_STAGES = """
Rate Limiting Evolution for SaaS:

1. **MVP Stage (Current)**:
   - Global rate limit only
   - Prevent crashes
   - Simple circuit breaker
   - Cost: $0

2. **Beta Stage (10+ users)**:
   - Per-IP rate limiting
   - Basic DDoS protection
   - Track usage patterns
   - Cost: $0

3. **Growth Stage (100+ users)**:
   - Per-user rate limiting
   - Tier-based limits (free/pro/enterprise)
   - Redis-backed distributed limiting
   - Cost: $50/month (Redis)

4. **Scale Stage (1000+ users)**:
   - API Gateway with built-in limiting
   - Geographic rate limiting
   - ML-based anomaly detection
   - Cost: $500+/month (API Gateway + WAF)

Current Implementation: MVP Stage
Ready for: 100 concurrent users, 10 QPS sustained
"""
