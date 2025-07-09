# services/persona_runtime/main.py
from __future__ import annotations

from typing import AsyncIterator

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
        raise HTTPException(404, f"persona {req.persona_id!r} not found")

    # `compile()` in runtime.py gives us a *CompiledStateGraph* that has `.astream`
    async def streamer() -> AsyncIterator[str]:
        async def _extract_text(s: object) -> str | None:  # helper
            if isinstance(s, dict):
                # prefer the formatted-node output first
                if (
                    "format" in s
                    and isinstance(s["format"], dict)
                    and "text" in s["format"]
                ):
                    return str(s["format"]["text"])
                # then the final global state
                if "text" in s:
                    return str(s["text"])
            return None

        async for state in dag.astream({"text": req.input}):
            if (msg := await _extract_text(state)) is not None:
                yield f"data:{msg}\n\n"

    return EventSourceResponse(streamer())


@api.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
