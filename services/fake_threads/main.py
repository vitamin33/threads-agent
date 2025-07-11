# /services/fake_threads/main.py
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="fake-threads")


class Post(BaseModel):
    topic: str
    content: str


# ──────────────────────────────────────────────────────────────
# simple in-memory “DB” so the e2e test has something to assert
# ──────────────────────────────────────────────────────────────
_published: list[Post] = []


@app.get("/ping")
def ping() -> dict[str, bool]:
    """Liveness probe used by the Helm chart and tests."""
    return {"pong": True}


@app.get("/health")
def health() -> dict[str, str]:
    """K8s readiness probe (mirrors other services)."""
    return {"status": "ok"}


@app.post("/publish")
def publish(post: Post) -> dict[str, Any]:
    """
    Store the draft in memory and echo it back.
    The orchestrator calls this in dev/E2E runs.
    """
    _published.append(post)
    return {"status": "published", **post.model_dump()}


@app.get("/published")
def list_published() -> list[Post]:
    """Return all drafts so the e2e test can poll for them."""
    return _published
