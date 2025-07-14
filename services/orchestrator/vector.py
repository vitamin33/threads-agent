# services/orchestrator/vector.py
from __future__ import annotations

import os
from typing import List

import qdrant_client
from qdrant_client.models import (
    CollectionDescription,
    CollectionStatus,
    Distance,
    VectorParams,
)

_POSTS = "posts_ai-jesus"  # single collection we care about
_client: qdrant_client.QdrantClient | None = None


# ──────────────────────────────────────────────────────────
# client helpers
# ──────────────────────────────────────────────────────────
def _new_client() -> qdrant_client.QdrantClient:
    """Return a *fresh* Qdrant client.

    * ``QDRANT_URL=:memory:`` → in-process (pure-Python) store — ideal for unit-tests.
    * any other value        → treat as HTTP endpoint.
    """
    url = os.getenv("QDRANT_URL", "http://qdrant:6333")
    if url == ":memory:":
        return qdrant_client.QdrantClient(":memory:")
    return qdrant_client.QdrantClient(url=url, prefer_grpc=False)


def get_client() -> qdrant_client.QdrantClient:
    """Process-wide singleton accessor."""
    global _client
    if _client is None:
        _client = _new_client()
    return _client


# ──────────────────────────────────────────────────────────
# bootstrap util
# ──────────────────────────────────────────────────────────
def _names(cols: List[CollectionDescription]) -> list[str]:  # mypy helper
    return [c.name for c in cols]


def ensure_posts_collection(dim: int = 128) -> None:
    """Create the ``posts_ai-jesus`` collection if it does not exist."""
    client = get_client()

    if _POSTS in _names(client.get_collections().collections):
        # runtime attr exists; missing only in type stubs
        status = client.collection_info(_POSTS).status  # type: ignore[attr-defined]
        if status != CollectionStatus.GREEN:
            raise RuntimeError(f"Collection {_POSTS!r} not ready: {status}")
        return

    client.create_collection(
        collection_name=_POSTS,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
