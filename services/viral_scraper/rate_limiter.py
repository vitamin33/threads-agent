# services/viral_scraper/rate_limiter.py
"""
Simple rate limiter for viral content scraper.

Minimal implementation to pass initial tests.
"""

from typing import Dict, Any
from datetime import datetime, timedelta


class RateLimiter:
    """Simple in-memory rate limiter per account"""

    def __init__(self, requests_per_window: int = 1, window_seconds: int = 60):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.requests: Dict[str, datetime] = {}

    def check_rate_limit(self, account_id: str) -> bool:
        """Check if request is within rate limit. Returns True if allowed."""
        now = datetime.now()

        if account_id not in self.requests:
            self.requests[account_id] = now
            return True

        last_request = self.requests[account_id]
        time_diff = now - last_request

        if time_diff.total_seconds() >= self.window_seconds:
            self.requests[account_id] = now
            return True

        return False

    def get_retry_after(self, account_id: str) -> int:
        """Get seconds to wait before next request is allowed"""
        if account_id not in self.requests:
            return 0

        now = datetime.now()
        last_request = self.requests[account_id]
        elapsed = (now - last_request).total_seconds()
        remaining = max(0, self.window_seconds - elapsed)
        return int(remaining)

    def get_status(self, account_id: str) -> Dict[str, Any]:
        """Get rate limit status for account"""
        now = datetime.now()

        if account_id not in self.requests:
            return {
                "account_id": account_id,
                "requests_remaining": self.requests_per_window,
                "reset_time": (
                    now + timedelta(seconds=self.window_seconds)
                ).isoformat(),
            }

        last_request = self.requests[account_id]
        time_diff = now - last_request

        if time_diff.total_seconds() >= self.window_seconds:
            remaining = self.requests_per_window
        else:
            remaining = 0

        reset_time = last_request + timedelta(seconds=self.window_seconds)

        return {
            "account_id": account_id,
            "requests_remaining": remaining,
            "reset_time": reset_time.isoformat(),
        }
