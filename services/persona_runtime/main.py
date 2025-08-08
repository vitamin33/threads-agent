# services/persona_runtime/main.py
from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from services.common.metrics import (
    maybe_start_metrics_server,
    record_content_generation_latency,
    record_business_metric,
)

from .runtime import build_dag_from_persona

maybe_start_metrics_server()

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
        start_time = time.time()
        hook_start = None
        body_start = None

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
            # Track phase transitions
            if hook_start is None and "hook" in str(st):
                hook_start = time.time()
            if body_start is None and "body" in str(st):
                body_start = time.time()
                if hook_start:
                    record_content_generation_latency(
                        req.persona_id, "hook", body_start - hook_start
                    )

            if (msg := _extract_json(st)) is not None:
                # Record final metrics
                total_time = time.time() - start_time
                record_content_generation_latency(req.persona_id, "total", total_time)
                if body_start:
                    record_content_generation_latency(
                        req.persona_id, "body", time.time() - body_start
                    )

                # Track successful generation
                record_business_metric(
                    "posts_generated", persona_id=req.persona_id, status="success"
                )

                # no manual 'data: ' – EventSourceResponse does that
                yield msg

    return EventSourceResponse(streamer())


@api.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@api.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
