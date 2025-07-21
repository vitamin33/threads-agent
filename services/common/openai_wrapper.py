# /services/common/openai_wrapper.py
from __future__ import annotations

import functools
import json
import os
import time
from functools import wraps
from types import SimpleNamespace
from typing import Awaitable, Callable, ParamSpec, Protocol, Tuple, TypeVar, cast

import openai
import redis
import tenacity
from openai.types import CompletionUsage  # tiny model always present

from services.common.metrics import LLM_TOKENS_TOTAL, record_latency  # NEW

P = ParamSpec("P")
T = TypeVar("T")


# ---------------------------------------------------------------------------
#  Type helpers – we don't *care* if the real object is ChatCompletion,
#  FunctionCall, ImageGeneration… we only need .model and .usage.
# ---------------------------------------------------------------------------
class _OpenAIRespLike(Protocol):
    model: str
    usage: CompletionUsage | None  # runtime may legitimately be None


# ---------------------------------------------------------------------------
#  Lazy singletons
# ---------------------------------------------------------------------------
_ai: openai.OpenAI | None = None  # sync client for convenience
_ai_async: openai.AsyncOpenAI | None = None
_rd: redis.Redis | None = None
_OFFLINE = os.getenv("OPENAI_API_KEY", "") in {"", "test"}  # NEW
_MOCK_MODE = os.getenv("OPENAI_MOCK", "0") == "1"  # NEW - Fast CI mocking


# ---------------------------------------------------------------------------
#  Mock response for fast CI (OPENAI_MOCK=1)
# ---------------------------------------------------------------------------
class _MockResp:
    def __init__(self, model: str):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content="MOCK"))]
        self.usage = CompletionUsage(
            prompt_tokens=10, completion_tokens=10, total_tokens=20
        )
        self.model = model


class _MockChatComp:
    @staticmethod
    def create(model: str, messages: object) -> "_MockResp":  # noqa: ANN401
        return _MockResp(model)


class _MockChat:
    completions = _MockChatComp()


class _MockOpenAI:
    chat = _MockChat()


_MOCK_CLIENT: openai.OpenAI = cast(openai.OpenAI, _MockOpenAI())

# ---------------------------------------------------------------------------
#  Very small stub client (sync) for offline mode
# ---------------------------------------------------------------------------
if _OFFLINE:

    class _StubResp:
        def __init__(self, model: str):
            self.choices = [
                SimpleNamespace(message=SimpleNamespace(content=f"stub-{model}"))
            ]
            self.usage = CompletionUsage(
                prompt_tokens=0, completion_tokens=0, total_tokens=0
            )
            self.model = model  # for consistency

    class _StubChatComp:
        @staticmethod
        def create(model: str, messages: object) -> "_StubResp":  # noqa: ANN401
            return _StubResp(model)

    class _StubChat:
        completions = _StubChatComp()

    class _StubOpenAI:
        chat = _StubChat()

    _STUB_CLIENT: openai.OpenAI = cast(openai.OpenAI, _StubOpenAI())


def _sync_ai() -> openai.OpenAI:
    global _ai
    if _ai is None:
        if _MOCK_MODE:
            _ai = _MOCK_CLIENT
            return _ai
        if _OFFLINE:
            _ai = _STUB_CLIENT
            return _ai
        _ai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30)
    return _ai


def ai() -> openai.AsyncOpenAI:
    """Process-wide async client (kept for existing async callers)."""
    global _ai_async
    if _ai_async is None:
        _ai_async = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=30,
        )
    return _ai_async


def _redis() -> redis.Redis:
    global _rd
    if _rd is None:
        _rd = cast(
            redis.Redis,
            redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0")),  # type: ignore[no-untyped-call]
        )
    return _rd


# ---------------------------------------------------------------------------
#  Retry policy (HTTP 429 / overload)
# ---------------------------------------------------------------------------
_retry = tenacity.retry(
    retry=tenacity.retry_if_exception_type(openai.RateLimitError),
    wait=tenacity.wait_exponential(multiplier=0.5, max=32),
    stop=tenacity.stop_after_attempt(6),
    reraise=True,
)


# ---------------------------------------------------------------------------
#  Very rough USD estimator (update quarterly)
# ---------------------------------------------------------------------------
def _usd(model: str, pt: int, ct: int) -> float:
    if _MOCK_MODE:
        return 0.0  # Mock mode costs nothing
    prm, cmp = {
        "gpt-4o-mini": (0.0005, 0.0015),
        "gpt-3.5-turbo-0125": (0.0005, 0.0015),
        "gpt-4o": (0.005, 0.015),
    }.get(model, (0.001, 0.002))
    return round((pt * prm + ct * cmp) / 1000, 6)


# ---------------------------------------------------------------------------
#  Sync **cached** wrapper for simple chat-completions
# ---------------------------------------------------------------------------
@functools.lru_cache(maxsize=512)
def _chat_call_uncached(model: str, prompt: str) -> Tuple[str, int]:
    """
    Low-level chat request with 512-entry LRU cache.

    Returns:
        tuple of (text, total_tokens)
    """
    # measure the OpenAI round-trip – labels it as “llm” latency
    with record_latency("llm"):
        resp = _retry(_sync_ai().chat.completions.create)(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

    usage = resp.usage or CompletionUsage(
        prompt_tokens=0, completion_tokens=0, total_tokens=0
    )
    text = (resp.choices[0].message.content or "").strip()
    return text, usage.total_tokens


def chat(model: str, prompt: str) -> str:
    """
    High-level helper used by synchronous callers.

    * hits the LRU cache
    * records token usage in Prometheus
    """
    text, tokens = _chat_call_uncached(model, prompt)
    LLM_TOKENS_TOTAL.labels(model=model).inc(tokens)
    return text


# ---------------------------------------------------------------------------
#  Decorator (unchanged) – tracks cost for **async** calls
# ---------------------------------------------------------------------------
def track_cost(
    *,
    persona: str,
    task: str,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Wrap an **async** function that returns an OpenAI response (or look-alike).
    On success → push cost / latency row into Redis list ``llm_costs``.
    """

    def _decor(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(fn)
        async def _wrap(*a: P.args, **kw: P.kwargs) -> T:
            start = time.perf_counter()

            raw_resp = await _retry(fn)(*a, **kw)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

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

            # push metrics for async callers, too
            LLM_TOKENS_TOTAL.labels(model=resp.model).inc(usage.total_tokens)
            return raw_resp

        return _wrap

    return _decor
