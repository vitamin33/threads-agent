"""
Rate limiting configuration for parallel agents.
Each agent gets its own quota to prevent conflicts.
"""

import os
from typing import Dict
from functools import wraps
import time
import threading

# Rate limits per agent (tokens per minute)
AGENT_RATE_LIMITS: Dict[str, Dict[str, int]] = {
    "a1": {
        "tokens_per_minute": 10000,
        "requests_per_minute": 100,
        "priority": 1,  # Core pipeline gets priority
    },
    "a2": {
        "tokens_per_minute": 20000,  # AI/ML heavy work
        "requests_per_minute": 200,
        "priority": 2,
    },
    "a3": {
        "tokens_per_minute": 5000,  # Analytics
        "requests_per_minute": 50,
        "priority": 3,
    },
    "a4": {
        "tokens_per_minute": 5000,  # Platform
        "requests_per_minute": 50,
        "priority": 3,
    },
}


class AgentRateLimiter:
    """Simple rate limiter for agent-based development."""

    def __init__(self):
        self.agent_id = os.getenv("AGENT_ID", "a1")
        self.limits = AGENT_RATE_LIMITS.get(self.agent_id, AGENT_RATE_LIMITS["a1"])
        self.token_bucket = self.limits["tokens_per_minute"]
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume_tokens(self, tokens: int) -> bool:
        """Consume tokens from the bucket."""
        with self.lock:
            # Refill bucket
            now = time.time()
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * (self.limits["tokens_per_minute"] / 60)
            self.token_bucket = min(
                self.limits["tokens_per_minute"], self.token_bucket + tokens_to_add
            )
            self.last_refill = now

            # Check if we can consume
            if self.token_bucket >= tokens:
                self.token_bucket -= tokens
                return True
            return False

    def wait_if_needed(self, tokens: int) -> None:
        """Wait until tokens are available."""
        while not self.consume_tokens(tokens):
            time.sleep(0.1)


def get_agent_rate_limit() -> Dict[str, int]:
    """Get rate limits for current agent."""
    agent_id = os.getenv("AGENT_ID", "a1")
    return AGENT_RATE_LIMITS.get(agent_id, AGENT_RATE_LIMITS["a1"])


def get_agent_priority() -> int:
    """Get priority for current agent (lower = higher priority)."""
    agent_id = os.getenv("AGENT_ID", "a1")
    return AGENT_RATE_LIMITS.get(agent_id, {}).get("priority", 99)


# Global rate limiter instance
rate_limiter = AgentRateLimiter()


def rate_limited(tokens: int = 100):
    """Decorator to rate limit function calls."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            rate_limiter.wait_if_needed(tokens)
            return func(*args, **kwargs)

        return wrapper

    return decorator
