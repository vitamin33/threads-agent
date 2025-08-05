# /services/fake_threads/main.py
from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime
import uuid

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="fake-threads")


class Post(BaseModel):
    topic: str
    content: str


class CommentCreate(BaseModel):
    text: str
    author: str


class Comment(BaseModel):
    id: str
    post_id: str
    text: str
    author: str
    timestamp: str


# ──────────────────────────────────────────────────────────────
# simple in-memory "DB" so the e2e test has something to assert
# ──────────────────────────────────────────────────────────────
_published: list[Post] = []
_comments: Dict[str, List[Comment]] = {}  # post_id -> list of comments


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


@app.get("/posts/{post_id}/comments")
def get_comments(post_id: str) -> List[Comment]:
    """Get all comments for a specific post."""
    return _comments.get(post_id, [])


@app.post("/posts/{post_id}/comments", status_code=201)
def create_comment(post_id: str, comment: CommentCreate) -> Comment:
    """Create a new comment for a specific post."""
    new_comment = Comment(
        id=f"comment_{uuid.uuid4().hex[:8]}",
        post_id=post_id,
        text=comment.text,
        author=comment.author,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
    
    if post_id not in _comments:
        _comments[post_id] = []
    
    _comments[post_id].append(new_comment)
    return new_comment
