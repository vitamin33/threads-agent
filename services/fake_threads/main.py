# /services/fake_threads/main.py
from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="fake-threads")


class Post(BaseModel):
    topic: str
    content: str


@app.get("/ping")
def ping() -> Dict[str, bool]:
    """Liveness probe used by the Helm chart and tests."""
    return {"pong": True}


@app.get("/health")
def health() -> Dict[str, str]:
    """K8s readiness probe (mirrors other services)."""
    return {"status": "ok"}


@app.post("/publish")
def publish(post: Post) -> Dict[str, Any]:
    """Echo the post back so tests can assert on it later."""
    return {"status": "published", **post.model_dump()}
