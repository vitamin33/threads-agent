# /services/common/metrics.py
"""Common Prometheus metrics helpers (CRA-212)."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator, Literal

from prometheus_client import Counter, Summary, start_http_server

# ───── metric registry ──────────────────────────────────────────────────
REQUEST_LATENCY = Summary(
    "request_latency_seconds",
    "End-to-end request (phase) latency",
    ["phase"],  # e.g. parse, llm, persist
)

LLM_TOKENS_TOTAL = Counter(
    "llm_tokens_total",
    "Total LLM tokens - labelled by model",
    ["model"],
)


# ───── utilities ────────────────────────────────────────────────────────
@contextmanager
def record_latency(
    phase: Literal["parse", "llm", "persist"],
) -> Generator[None, None, None]:
    """Context manager → records time spent inside the **with** block."""
    start = time.perf_counter()
    try:
        yield
    finally:
        REQUEST_LATENCY.labels(phase=phase).observe(time.perf_counter() - start)


def maybe_start_metrics_server(port: int = 9090) -> None:
    """
    Idempotently start the Prometheus exposition HTTP server.

    • Keeps a module-level flag so we don’t start multiple times
    • Call this once from service startup (orchestrator, worker, …)
    """
    if getattr(maybe_start_metrics_server, "_started", False):
        return
    start_http_server(port)  # non-blocking
    setattr(maybe_start_metrics_server, "_started", True)
