import time
import psutil
import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

# Import metrics from main
from ..main import REQUEST_COUNT, REQUEST_LATENCY, MEMORY_USAGE

logger = structlog.get_logger()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track performance metrics"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Track memory usage before request
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss

        # Process request
        response = await call_next(request)

        # Calculate metrics
        duration = time.time() - start_time
        memory_after = process.memory_info().rss
        memory_used = memory_after - memory_before

        # Extract endpoint from path
        endpoint = request.url.path
        method = request.method
        status_code = str(response.status_code)

        # Record metrics
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()

        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

        if memory_used > 0:
            MEMORY_USAGE.labels(operation="request_processing").observe(memory_used)

        # Add performance headers
        response.headers["X-Process-Time"] = str(duration)
        response.headers["X-Memory-Delta"] = str(memory_used)

        # Log slow requests
        if duration > 5.0:  # Log requests taking more than 5 seconds
            logger.warning(
                "Slow request detected",
                endpoint=endpoint,
                method=method,
                duration=duration,
                memory_used=memory_used,
            )

        return response


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware to handle health checks efficiently"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Handle health check requests without full middleware stack
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Process other requests normally
        return await call_next(request)


def add_monitoring_headers(response: Response, operation: str, duration: float):
    """Add monitoring headers to responses"""
    response.headers["X-Operation"] = operation
    response.headers["X-Duration"] = str(duration)
    response.headers["X-Service"] = "tech-doc-generator"
