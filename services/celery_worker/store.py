# /services/celery_worker/store.py
from __future__ import annotations

import os
from typing import Any, Dict, List

import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import (  # ← import models here
    Distance,
    PointStruct,
    VectorParams,
)

# ─────────────────────────────── env / globals ───────────────────────────────
_POSTGRES_DSN = os.getenv(
    "POSTGRES_DSN", "postgresql://postgres:pass@postgres:5432/postgres"
)
_QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
_COLLECTION = "posts_ai-jesus"  # same as orchestrator.vector

_PG: psycopg2.extensions.connection | None = None
_QD: QdrantClient | None = None


# ───────────────────────────── helpers ───────────────────────────────────────
def _pg() -> psycopg2.extensions.connection:
    """Lazy singleton Postgres connection (autocommit on)."""
    global _PG
    if _PG is None:
        _PG = psycopg2.connect(_POSTGRES_DSN)
        _PG.autocommit = True
    return _PG


def _qd() -> QdrantClient:
    """Lazy singleton Qdrant client; bootstrap collection if missing."""
    global _QD
    if _QD is None:
        _QD = QdrantClient(url=_QDRANT_URL, prefer_grpc=False, timeout=5)
        if not _QD.collection_exists(_COLLECTION):
            _QD.create_collection(
                collection_name=_COLLECTION,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE),
            )
    return _QD


# ───────────────────────────── public API  ───────────────────────────────────
def save_post(row: Dict[str, Any]) -> int:
    """
    Insert a post row and return its primary-key ID.

    Raises RuntimeError if the INSERT somehow returns no row
    (satisfies the Pylance Optional warning).
    """
    with _pg().cursor() as cur:
        cur.execute(
            """
            INSERT INTO posts (persona_id, hook, body, tokens_used)
            VALUES (%s, %s, %s, %s) RETURNING id;
            """,
            (row["persona_id"], row["hook"], row["body"], row.get("tokens_used", 0)),
        )
        rec = cur.fetchone()
        if rec is None:  # <- fixes “Object of type 'None' is not subscriptable”
            raise RuntimeError("Post-insert fetch returned no row")
        return int(rec[0])


def upsert_vector(pid: str, vid: int, vector: List[float]) -> None:
    """
    Upsert a placeholder vector for the post.

    The direct `PointStruct` import fixes the “models is not a known attribute”
    message in strict type-checkers / Pylance.
    """
    _qd().upsert(
        collection_name=_COLLECTION,
        points=[PointStruct(id=vid, vector=vector, payload={"persona": pid})],
    )


__all__ = [
    "save_post",
    "upsert_vector",
]
