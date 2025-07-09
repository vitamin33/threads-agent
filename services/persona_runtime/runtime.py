# services/persona_runtime/runtime.py
# mypy: disable-error-code="import-not-found,attr-defined"

"""
LangGraph DAG factory – demo edition
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, TypedDict

# LangGraph ≤ 0.5.1 ships no stubs – ignore missing-import
from langgraph.graph import END, START, StateGraph


class FlowState(TypedDict):
    text: str


def build_dag_from_persona(persona_id: str) -> Any:
    # ── tiny “DB” ────────────────────────────────────────────────
    db = {
        "ai-jesus": SimpleNamespace(emoji="🙏", temperament="kind"),
        "ai-elon": SimpleNamespace(emoji="🚀", temperament="hype"),
    }
    cfg = db.get(persona_id)
    if cfg is None:
        return None

    # ── build graph ─────────────────────────────────────────────
    dag: StateGraph[Any] = StateGraph(FlowState)

    # ---------- nodes ----------
    def ingest(state: FlowState) -> FlowState:
        return {"text": state["text"].strip()}

    def enrich(state: FlowState) -> FlowState:
        return {"text": f"{cfg.emoji} {state['text']} {cfg.emoji}"}

    def format_(state: FlowState) -> FlowState:
        return {"text": state["text"].upper()}

    dag.add_node("ingest", ingest)
    dag.add_node("enrich", enrich)
    dag.add_node("format", format_)

    # ---------- edges ----------
    dag.add_edge(START, "ingest")  # ⬅️  entry-point required
    dag.add_edge("ingest", "enrich")
    dag.add_edge("enrich", "format")
    dag.add_edge("format", END)

    return dag.compile()  # exposes .arun / .astream
