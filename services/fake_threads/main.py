# /services/fake_threads/main.py
from __future__ import annotations

import random
from typing import Any, Dict, List
from datetime import datetime
import uuid
import logging

from fastapi import FastAPI, Response
from pydantic import BaseModel
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Import metrics
from services.common.metrics import (
    record_engagement_rate,
    record_business_metric,
    update_revenue_projection,
    record_cost_per_follow,
    maybe_start_metrics_server,
)

# Reduce health check log spam
logging.getLogger("uvicorn.access").addFilter(
    lambda record: "/health" not in record.getMessage()
)

app = FastAPI(title="fake-threads")
maybe_start_metrics_server(port=8090)


class Post(BaseModel):
    topic: str
    content: str
    engagement_rate: float = 0.0
    followers_gained: int = 0
    cost_per_follow: float = 0.0


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
_comments: Dict[str, List[Comment]] = {}


def simulate_engagement(content: str) -> float:
    """Simulate realistic engagement based on content quality indicators."""
    engagement = 0.04  # Base 4%

    # Boost for viral indicators
    viral_words = [
        "shocking",
        "secret",
        "revealed",
        "mistake",
        "truth",
        "nobody talks about",
    ]
    for word in viral_words:
        if word.lower() in content.lower():
            engagement += 0.008

    # Boost for questions
    if "?" in content:
        engagement += 0.005

    # Boost for numbers/stats
    if any(char.isdigit() for char in content):
        engagement += 0.003

    # Length penalty for very long posts
    if len(content) > 200:
        engagement -= 0.005

    # Random variation ±15%
    engagement *= random.uniform(0.85, 1.15)

    return round(min(max(engagement, 0.02), 0.12), 4)  # Cap between 2% and 12%


def calculate_cost_per_follow(engagement_rate: float) -> float:
    """Calculate cost per follower based on engagement."""
    # Higher engagement = lower cost per follow
    base_cost = 0.015
    efficiency_factor = max(0.5, (0.06 / engagement_rate))  # Target 6% engagement
    return round(base_cost * efficiency_factor, 3)


def detect_persona(content: str) -> str:
    """Detect persona type from content patterns."""
    tech_keywords = ["ai", "productivity", "automation", "system", "workflow", "tools"]
    business_keywords = [
        "growth",
        "revenue",
        "customers",
        "marketing",
        "sales",
        "business",
    ]

    tech_score = sum(1 for word in tech_keywords if word.lower() in content.lower())
    business_score = sum(
        1 for word in business_keywords if word.lower() in content.lower()
    )

    return "techie" if tech_score > business_score else "entrepreneur"


@app.get("/ping")
def ping() -> dict[str, bool]:
    """Liveness probe used by the Helm chart and tests."""
    return {"pong": True}


@app.get("/health")
def health() -> dict[str, str]:
    """K8s readiness probe (mirrors other services)."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/publish")
def publish(post: Post) -> dict[str, Any]:
    """
    Store the draft in memory and echo it back with simulated engagement.
    The orchestrator calls this in dev/E2E runs.
    """
    # Simulate realistic engagement based on content
    engagement_rate = simulate_engagement(post.content)
    followers_gained = int(engagement_rate * random.randint(800, 1200))
    cost_per_follow = calculate_cost_per_follow(engagement_rate)

    # Update post with metrics
    post.engagement_rate = engagement_rate
    post.followers_gained = followers_gained
    post.cost_per_follow = cost_per_follow

    # Determine persona from content patterns
    persona_id = detect_persona(post.content)

    # Record metrics
    record_engagement_rate(persona_id, engagement_rate)
    record_cost_per_follow(persona_id, cost_per_follow)
    record_business_metric("posts_generated", persona_id=persona_id, status="success")

    # Update revenue projection
    monthly_revenue = followers_gained * 0.15  # $0.15 per follower per month
    update_revenue_projection("posts", monthly_revenue)

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
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    if post_id not in _comments:
        _comments[post_id] = []

    _comments[post_id].append(new_comment)
    return new_comment
