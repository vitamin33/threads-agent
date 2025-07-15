# services/persona_runtime/main.py
from __future__ import annotations

import json
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from .runtime import build_dag_from_persona

api = FastAPI(title="persona-runtime")
app = api


class RunRequest(BaseModel):
    persona_id: str = Field(..., examples=["ai-jesus"])
    input: str = Field(..., examples=["Write me a tweet about hope"])


@api.post("/run")
async def run(req: RunRequest) -> EventSourceResponse:
    dag = build_dag_from_persona(req.persona_id)
    if dag is None:
        raise HTTPException(
            status_code=404, detail=f"persona {req.persona_id!r} not found"
        )

    async def streamer() -> AsyncIterator[str]:
        """Relay LangGraph state updates as SSE lines."""

        def _extract_json(state: Any) -> str | None:
            """
            Return a JSON string once the **final** draft (hook + body) is present.

            Depending on how LangGraph merges node outputs the `draft`
            object can appear either:
            • at the root of the global state, *or*
            • inside the result of the `"format"` node.
            """
            if not isinstance(state, dict):
                return None

            # root-level check
            draft: Any = state.get("draft")
            if isinstance(draft, dict) and set(draft) == {"hook", "body"}:
                return json.dumps({"draft": draft})

            # nested under `"format"` node
            nested = state.get("format", {}).get("draft")
            if isinstance(nested, dict) and set(nested) == {"hook", "body"}:
                return json.dumps({"draft": nested})

            return None

        async for st in dag.astream({"text": req.input}):
            if (msg := _extract_json(st)) is not None:
                yield f"data:{msg}\n\n"

    return EventSourceResponse(streamer())


@api.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
