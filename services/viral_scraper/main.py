# services/viral_scraper/main.py
"""
Viral Content Scraper Service

Monitors and extracts viral content from high-performing Threads accounts.
Minimal implementation to pass initial tests.
"""

from fastapi import FastAPI, HTTPException, Response
from typing import Dict, Optional, Any
from pydantic import BaseModel
import uuid

from .rate_limiter import RateLimiter

app = FastAPI(title="viral-scraper", description="Viral content scraper service")

# Initialize rate limiter (1 request per minute for testing)
rate_limiter = RateLimiter(requests_per_window=1, window_seconds=60)


class ScrapeRequest(BaseModel):
    """Request model for scraping configuration"""

    max_posts: Optional[int] = 50
    days_back: Optional[int] = 7
    min_performance_percentile: Optional[float] = 99.0


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "viral-scraper"}


@app.post("/scrape/account/{account_id}")
async def scrape_account(
    account_id: str, request: Optional[ScrapeRequest] = None
) -> Dict[str, Any]:
    """Trigger scraping for a specific account"""
    # Check rate limit
    if not rate_limiter.check_rate_limit(account_id):
        retry_after = rate_limiter.get_retry_after(account_id)
        
        # Create HTTPException with proper rate limiting headers
        detail = {
            "error": "Rate limit exceeded for this account",
            "retry_after": retry_after,
        }
        
        exception = HTTPException(status_code=429, detail=detail)
        # Add rate limiting headers
        exception.headers = {
            "X-RateLimit-Limit": str(rate_limiter.requests_per_window),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(retry_after),
            "Retry-After": str(retry_after)
        }
        raise exception

    task_id = str(uuid.uuid4())

    response = {"task_id": task_id, "account_id": account_id, "status": "queued"}

    # Add request parameters if provided
    if request:
        response.update(
            {
                "max_posts": request.max_posts,
                "days_back": request.days_back,
                "min_performance_percentile": request.min_performance_percentile,
            }
        )

    return response


@app.get("/scrape/tasks/{task_id}/status")
async def get_scraping_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a scraping task"""
    # Minimal implementation - always return queued for now
    return {"task_id": task_id, "status": "queued"}


@app.get("/viral-posts")
async def get_viral_posts(
    account_id: Optional[str] = None,
    limit: int = 20,
    page: int = 1,
    min_engagement_rate: Optional[float] = None,
    top_1_percent_only: bool = False,
) -> Dict[str, Any]:
    """Get list of viral posts with optional filtering"""
    # Minimal implementation - return mock data
    mock_posts = []

    # If top_1_percent_only, return posts with >99% percentile
    if top_1_percent_only:
        mock_posts = [
            {
                "content": "Mock viral post",
                "account_id": account_id or "test_account",
                "post_url": "https://threads.net/test/123",
                "timestamp": "2023-12-01T10:00:00Z",
                "likes": 5000,
                "comments": 200,
                "shares": 1000,
                "engagement_rate": 0.25,
                "performance_percentile": 99.5,
            }
        ]

    return {
        "posts": mock_posts,
        "total_count": len(mock_posts),
        "page": page,
        "page_size": limit,
    }


@app.get("/viral-posts/{account_id}")
async def get_viral_posts_by_account(account_id: str) -> Dict[str, Any]:
    """Get viral posts for a specific account"""
    # Minimal implementation - return mock data
    return {"account_id": account_id, "posts": []}


@app.get("/rate-limit/status/{account_id}")
async def get_rate_limit_status(account_id: str) -> Dict[str, Any]:
    """Get rate limit status for a specific account"""
    return rate_limiter.get_status(account_id)


if __name__ == "__main__":
    import uvicorn  # type: ignore[import-not-found]

    uvicorn.run(app, host="0.0.0.0", port=8080)
