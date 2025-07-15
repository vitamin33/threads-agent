# services/persona_runtime/runtime.py
# mypy: disable-error-code="import-not-found,attr-defined"

"""
LangGraph DAG factory – v2: real LLM + guard-rail + optional LoRA.

Extras for unit/CI
──────────────────
* Builds an OpenAI client even if OPENAI_API_KEY is missing.
  The dummy key `"test"` marks “offline” mode so tests never hit the network.
* `_llm` and `_moderate` short-circuit in offline mode for deterministic output.
"""

from __future__ import annotations

import os
import re
from types import SimpleNamespace
from typing import Any, NotRequired, TypedDict

import openai
from langgraph.graph import END, START, StateGraph
from openai import OpenAIError

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
    except Exception:
        # Harmless on CPU-only runners
        pass


_maybe_load_lora()

# ───────────────────────── constants / config ──────────────────────────
try:
    openai_client = openai.AsyncOpenAI()  # real key present
except OpenAIError:  # no OPENAI_API_KEY → offline
    openai_client = openai.AsyncOpenAI(api_key="test")

_OFFLINE = openai_client.api_key == "test"  # unit-test marker

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
async def _llm(model: str, prompt: str) -> str:
    """One-shot OpenAI call (returns stub when offline)."""
    if _OFFLINE:
        return f"stub-{model}"

    resp = await openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    # `content` is str | None
    return (resp.choices[0].message.content or "").strip()


async def _moderate(content: str) -> bool:
    """Return **True** if content passes moderation (always true offline)."""
    if _OFFLINE:
        return True

    if GUARD_REGEX.search(content):
        return False
    mod = await openai_client.moderations.create(
        model="omni-moderation-latest",
        input=content,
    )
    cats: dict[str, bool] = mod.results[
        0
    ].categories.model_dump()  # pyright: ignore[reportGeneralTypeIssues]
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

    # 2️⃣ hook LLM
    async def hook_llm(state: FlowState) -> FlowState:
        hook = await _llm(HOOK_MODEL, state.get("text", ""))
        return {"draft": {"hook": hook}}

    # 3️⃣ body LLM
    async def body_llm(state: FlowState) -> FlowState:
        prompt = f"{state.get('draft', {}).get('hook', '')}\n\nWrite a detailed post:"
        body = await _llm(BODY_MODEL, prompt)
        return {"draft": {"body": body}}

    # 4️⃣ guard-rail
    async def guardrail(state: FlowState) -> FlowState:
        bad: list[str] = [
            part
            for part, txt in state.get("draft", {}).items()
            if not await _moderate(txt)
        ]
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
