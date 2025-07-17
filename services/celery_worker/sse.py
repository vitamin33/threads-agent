# /services/celery_worker/sse.py
from __future__ import annotations

import json
from typing import Optional

import httpx


def run_persona(
    base_url: str,
    persona_id: str,
    text: str,
    *,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 90,
) -> dict[str, str]:
    """
    POSTs to /run and blocks until the first SSE chunk that contains
    both ``hook`` and ``body`` arrives. Returns {"hook":…, "body":…}.
    """
    url = f"{base_url.rstrip('/')}/run"
    hdrs = {"accept": "text/event-stream", **(headers or {})}
    with httpx.Client(timeout=timeout) as cli:
        with cli.stream(
            "POST",
            url,
            json={"persona_id": persona_id, "input": text},
            headers=hdrs,
        ) as r:
            r.raise_for_status()
            for line in r.iter_text():
                if not line.startswith("data:"):
                    continue
                data = json.loads(line[5:])
                draft = data.get("draft") or {}
                if {"hook", "body"} <= draft.keys():
                    return draft
    raise RuntimeError("persona-runtime finished without draft")
