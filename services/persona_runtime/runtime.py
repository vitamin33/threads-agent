# services/persona_runtime/runtime.py
# mypy: disable-error-code="import-not-found,attr-defined"
"""
LangGraph DAG factory – v2: real LLM + guard-rail + optional LoRA.

Extras for unit/CI
──────────────────
* If `OPENAI_API_KEY` is missing, empty, or literally ``"test"``,
  the code runs in **offline mode**: no network calls, deterministic stubs.
* `_llm` and `_moderate` short-circuit in offline mode.
"""

from __future__ import annotations

import os
import re
from types import SimpleNamespace
from typing import Any, NotRequired, TypedDict

# Viral hook engine HTTP client for enhanced hook generation
import httpx
import openai
from langgraph.graph import END, START, StateGraph

from services.common.metrics import (
    LLM_TOKENS_TOTAL,
    record_error,
    record_hourly_openai_cost,
    record_latency,
    record_openai_cost,
    update_content_quality,
)
from services.common.ai_metrics import ai_metrics
from services.common.ai_safety import ai_security

VIRAL_ENGINE_URL = os.getenv("VIRAL_ENGINE_URL")
VIRAL_ENGINE_AVAILABLE = bool(VIRAL_ENGINE_URL)

if VIRAL_ENGINE_AVAILABLE:
    print(f"[VIRAL] ViralHookEngine HTTP client available at {VIRAL_ENGINE_URL}")
else:
    print(
        "[VIRAL] ViralHookEngine not available - no VIRAL_ENGINE_URL environment variable"
    )

# ───────────────────────── optional PEFT support ──────────────────────────
PeftModel: Any  # forward declaration for static checkers
try:
    from peft import PeftModel as _PeftModel

    PeftModel = _PeftModel
    HAS_PEFT = True
except ImportError:  # CPU-only / CI path
    HAS_PEFT = False


def _maybe_load_lora() -> None:
    """Attach a LoRA adapter once at import-time (silently ignored on failure)."""
    path = os.getenv("LORA_PATH")
    if not path or not HAS_PEFT or not os.path.exists(path):
        return
    try:
        PeftModel.from_pretrained(os.getenv("HOOK_MODEL", "gpt-4o"), path)
        print("[LoRA] adapter loaded from", path)
    except Exception:
        # Harmless on CPU-only runners
        pass


_maybe_load_lora()

# ───────────────────────── constants / config ──────────────────────────
OFFLINE_MARKER = "test"
_RAW_KEY = os.getenv("OPENAI_API_KEY", "")
_MOCK_MODE = os.getenv("OPENAI_MOCK", "0") == "1"

# Treat "no key", empty key, or the literal string "test" as offline
_OFFLINE = _RAW_KEY in {"", OFFLINE_MARKER}

# Even in offline mode we must pass *some* non-empty key, otherwise the
# OpenAI Python SDK throws on import.  `"test"` is our sentinel.
openai_client = openai.AsyncOpenAI(api_key=OFFLINE_MARKER if _OFFLINE else _RAW_KEY)

HOOK_MODEL = os.getenv("HOOK_MODEL", "gpt-4o")
BODY_MODEL = os.getenv("BODY_MODEL", "gpt-3.5-turbo-0125")

GUARD_REGEX = re.compile(r"\b(suicide|bomb|kill)\b", re.I)

_PERSONA_DB = {
    "ai-jesus": SimpleNamespace(emoji="🙏", temperament="kind"),
    "ai-elon": SimpleNamespace(emoji="🚀", temperament="hype"),
}


# ───────────────────────────── state type ──────────────────────────────
class FlowState(TypedDict, total=False):
    text: str
    draft: NotRequired[dict[str, str]]  # {hook:str, body:str}


# ─────────────────────────── helper funcs ──────────────────────────────
async def _llm(model: str, prompt: str, content_type: str = "unknown") -> str:
    """One-shot OpenAI call with enhanced metrics (returns stub when offline)."""
    if _MOCK_MODE:
        return "MOCK"
    if _OFFLINE:
        return f"stub-{model}"

    print(">> calling openai", model)

    # Check prompt safety before making API call
    safety_check = ai_security.check_prompt_injection(prompt)
    if not safety_check["safe"] and safety_check["risk_level"] in ["high", "critical"]:
        record_error("persona_runtime", "prompt_injection_blocked", "security")
        print(f"🚨 Blocked potential prompt injection: {safety_check['risk_level']}")
        # Return safe fallback instead of making API call
        return "I can help you with that, but let me rephrase it in a safer way."

    # measure the call itself
    import time

    start_time = time.time()

    with record_latency("llm"):
        try:
            resp = await openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Extract response content
            content = (resp.choices[0].message.content or "").strip()

            # Enhanced metrics collection
            if resp.usage:
                total_tokens = resp.usage.total_tokens
                input_tokens = resp.usage.prompt_tokens
                output_tokens = resp.usage.completion_tokens

                # Count total tokens (existing metric)
                LLM_TOKENS_TOTAL.labels(model=model).inc(total_tokens)

                # Calculate and record cost
                cost_usd = _calculate_openai_cost(model, input_tokens, output_tokens)
                record_openai_cost(model, cost_usd)
                record_hourly_openai_cost(model, cost_usd)

                # Basic quality scoring based on response length and coherence
                quality_score = _calculate_content_quality(content, content_type)

                # Record to our AI metrics tracker
                ai_metrics.record_inference(
                    model_name=model,
                    tokens_used=total_tokens,
                    response_time_ms=response_time_ms,
                    confidence=quality_score,  # Use quality score as confidence proxy
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    error=False,
                )

                # Check for hallucination risks
                hallucination_check = ai_security.flag_potential_hallucination(content)
                if hallucination_check["potential_hallucination_risk"]:
                    print(
                        f"⚠️  Hallucination risk detected: {hallucination_check['risk_level']}"
                    )
                    # Adjust quality score based on hallucination risk
                    quality_score *= hallucination_check["confidence_adjustment"]
                    update_content_quality(
                        "persona_runtime", content_type, quality_score
                    )

                print(
                    f"<< got openai response: {total_tokens} tokens, ${cost_usd:.6f} cost, quality: {quality_score:.3f}, latency: {response_time_ms:.0f}ms"
                )

            return content

        except Exception as e:
            # Record error in AI metrics
            ai_metrics.record_inference(
                model_name=model,
                tokens_used=0,
                response_time_ms=(time.time() - start_time) * 1000,
                error=True,
            )
            record_error("persona_runtime", f"openai_{model}_error", "error")
            print(f"❌ OpenAI API error: {e}")
            raise


def _calculate_openai_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate OpenAI API cost in USD based on current pricing."""
    # Pricing as of 2024 (per 1000 tokens)
    pricing = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
        "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},  # Legacy pricing
    }

    model_pricing = pricing.get(model, {"input": 0.001, "output": 0.002})  # Fallback

    input_cost = (input_tokens / 1000) * model_pricing["input"]
    output_cost = (output_tokens / 1000) * model_pricing["output"]

    return input_cost + output_cost


def _calculate_content_quality(content: str, content_type: str) -> float:
    """Simple content quality scoring (0-1 scale)."""
    if not content or content == "MOCK":
        return 0.5  # Neutral for test mode

    score = 0.5  # Base score

    # Length scoring (appropriate length gets bonus)
    length = len(content)
    if content_type == "hook":
        # Hooks should be concise (50-200 chars ideal)
        if 50 <= length <= 200:
            score += 0.3
        elif length < 20 or length > 400:
            score -= 0.2
    elif content_type == "body":
        # Body should be substantial (200-800 chars ideal)
        if 200 <= length <= 800:
            score += 0.3
        elif length < 100 or length > 1200:
            score -= 0.2

    # Basic coherence scoring
    sentences = content.count(".") + content.count("!") + content.count("?")
    if sentences >= 1:
        score += 0.1

    # Engagement elements
    if any(char in content for char in ["?", "!", ":"]):
        score += 0.1

    return max(0.0, min(1.0, score))


async def _moderate(content: str) -> bool:
    """Return **True** if content passes moderation (always true offline)."""
    if _MOCK_MODE or _OFFLINE:
        return True

    if GUARD_REGEX.search(content):
        return False

    mod = await openai_client.moderations.create(
        model="omni-moderation-latest",
        input=content,
        timeout=30,
    )
    cats: dict[str, bool] = mod.results[0].categories.model_dump()  # pyright: ignore[reportGeneralTypeIssues]
    return not any(cats.values())


# ─────────────────────────── DAG factory ───────────────────────────────
def build_dag_from_persona(persona_id: str) -> Any | None:
    cfg = _PERSONA_DB.get(persona_id)
    if cfg is None:
        return None

    dag: StateGraph[Any] = StateGraph(FlowState)

    # 1️⃣ ingest – trim user input
    def ingest(state: FlowState) -> FlowState:
        return {"text": state.get("text", "").strip()}

    # 2️⃣ hook LLM (enhanced with viral patterns)
    async def hook_llm(state: FlowState) -> FlowState:
        base_content = state.get("text", "")
        hook = None

        # Try viral hook optimization first
        if VIRAL_ENGINE_AVAILABLE and VIRAL_ENGINE_URL:
            try:
                with record_latency("viral_hook_optimization"):
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{VIRAL_ENGINE_URL}/optimize-hook",
                            json={
                                "persona_id": persona_id,
                                "base_content": base_content,
                            },
                            timeout=5.0,
                        )
                        response.raise_for_status()
                        viral_result = response.json()

                    # Use viral hook if it meets quality threshold
                    if viral_result["expected_engagement_rate"] > 0.06:  # 6% threshold
                        hook = viral_result["optimized_hooks"][0]["content"]
                        print(
                            f"[VIRAL] Using viral hook: {viral_result['selected_pattern']} (ER: {viral_result['expected_engagement_rate']:.3f})"
                        )
                    else:
                        print(
                            f"[VIRAL] Viral hook below threshold ({viral_result['expected_engagement_rate']:.3f}), falling back to LLM"
                        )

            except Exception as e:
                print(f"[VIRAL] Hook optimization failed: {e}, falling back to LLM")
                record_error("persona_runtime", "viral_hook_error", "error")

        # Fall back to LLM if viral hook not available or below threshold
        if hook is None:
            hook = await _llm(HOOK_MODEL, base_content, "hook")
            print("[VIRAL] Using LLM-generated hook")

        # Record content quality metrics
        quality_score = _calculate_content_quality(hook, "hook")
        update_content_quality(persona_id, "hook", quality_score)

        return {"draft": {"hook": hook}}

    # 3️⃣ body LLM
    async def body_llm(state: FlowState) -> FlowState:
        prompt = f"{state.get('draft', {}).get('hook', '')}\n\nWrite a detailed post:"
        body = await _llm(BODY_MODEL, prompt, "body")

        # Record content quality metrics
        quality_score = _calculate_content_quality(body, "body")
        update_content_quality(persona_id, "body", quality_score)

        # Calculate combined quality score
        hook_quality = _calculate_content_quality(
            state.get("draft", {}).get("hook", ""), "hook"
        )
        combined_quality = (hook_quality + quality_score) / 2
        update_content_quality(persona_id, "combined", combined_quality)

        return {"draft": {"body": body}}

    # 4️⃣ guard-rail
    async def guardrail(state: FlowState) -> FlowState:
        draft = state.get("draft", {})
        bad = []

        # Check each part for moderation and content safety
        for part, txt in draft.items():
            # Original moderation check
            if not await _moderate(txt):
                bad.append(part)
                continue

            # Additional content safety check
            safety_check = ai_security.check_content_safety(txt)
            if not safety_check["safe"]:
                print(
                    f"🚨 Content safety violation in {part}: {safety_check['violations']}"
                )
                bad.append(part)

        if bad:
            raise RuntimeError(f"Guard-rail blocked parts: {bad}")
        return {}

    # 5️⃣ format final output
    def format_(state: FlowState) -> FlowState:
        draft = state.get("draft", {})
        hook_txt = f"{cfg.emoji} {draft.get('hook', '')} {cfg.emoji}"
        return {"draft": {"hook": hook_txt, "body": draft.get("body", "")}}

    # ─── wiring ───
    dag.add_node("ingest", ingest)
    dag.add_node("hook_llm", hook_llm)
    dag.add_node("body_llm", body_llm)
    dag.add_node("guardrail", guardrail)
    dag.add_node("format", format_)

    dag.add_edge(START, "ingest")
    dag.add_edge("ingest", "hook_llm")
    dag.add_edge("hook_llm", "body_llm")
    dag.add_edge("body_llm", "guardrail")
    dag.add_edge("guardrail", "format")
    dag.add_edge("format", END)

    return dag.compile()  # exposes .ainvoke / .astream
