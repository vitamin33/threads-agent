# /services/common/openai_wrapper.py
from __future__ import annotations

import json
import os
import time
from functools import wraps
from typing import Awaitable, Callable, ParamSpec, Protocol, TypeVar, cast

import openai
import redis
import tenacity
from openai.types import CompletionUsage  # only the tiny usage model – always available

P = ParamSpec("P")
T = TypeVar("T")


# ---------------------------------------------------------------------------
#  Type helpers – we don't *care* if the real object is ChatCompletion,
#  FunctionCall, ImageGeneration… we only need .model and .usage.
# ---------------------------------------------------------------------------
class _OpenAIRespLike(Protocol):
    model: str
    usage: CompletionUsage | None  # runtime can legitimately be None


# ---------------------------------------------------------------------------
#  Lazy singletons
# ---------------------------------------------------------------------------
_ai: openai.AsyncOpenAI | None = None
_rd: redis.Redis | None = None


def ai() -> openai.AsyncOpenAI:
    """Process-wide AsyncOpenAI client (lazy singleton)."""
    global _ai
    if _ai is None:
        _ai = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=30,
        )
    return _ai


def _redis() -> redis.Redis:
    """Redis connection for cost rows."""
    global _rd
    if _rd is None:
        _rd = cast(
            redis.Redis,
            redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0")),  # type: ignore[no-untyped-call]
        )
    return _rd


# ---------------------------------------------------------------------------
#  Retry policy (HTTP 429 or overload)
# ---------------------------------------------------------------------------
_retry = tenacity.retry(
    retry=tenacity.retry_if_exception_type(openai.RateLimitError),
    wait=tenacity.wait_exponential(multiplier=0.5, max=32),
    stop=tenacity.stop_after_attempt(6),
    reraise=True,
)


# ---------------------------------------------------------------------------
#  Very-rough USD estimator (update numbers quarterly)
# ---------------------------------------------------------------------------
def _usd(model: str, pt: int, ct: int) -> float:
    prm, cmp = {
        "gpt-4o-mini": (0.0005, 0.0015),
        "gpt-3.5-turbo-0125": (0.0005, 0.0015),
        "gpt-4o": (0.005, 0.015),
    }.get(model, (0.001, 0.002))
    return round((pt * prm + ct * cmp) / 1000, 6)


# ---------------------------------------------------------------------------
#  Decorator
# ---------------------------------------------------------------------------
def track_cost(
    *,
    persona: str,
    task: str,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Wrap an async function that returns an OpenAI response (or look-alike).
    On success → push cost / latency row into Redis list ``llm_costs``.
    """

    def _decor(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(fn)
        async def _wrap(*a: P.args, **kw: P.kwargs) -> T:
            start = time.perf_counter()

            raw_resp = await _retry(fn)(*a, **kw)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

            # Mypy-friendly view of what we need
            resp = cast(_OpenAIRespLike, raw_resp)
            usage = resp.usage or CompletionUsage(
                prompt_tokens=0, completion_tokens=0, total_tokens=0
            )

            row = {
                "ts": int(time.time()),
                "persona": persona,
                "task": task,
                "model": resp.model,
                "prompt_tks": usage.prompt_tokens,
                "completion_tks": usage.completion_tokens,
                "usd": _usd(resp.model, usage.prompt_tokens, usage.completion_tokens),
                "latency_ms": elapsed_ms,
            }
            _redis().rpush("llm_costs", json.dumps(row))

            return raw_resp  # unchanged return type

        return _wrap

    return _decor
