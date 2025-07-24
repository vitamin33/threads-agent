# tests/e2e/test_post_flow.py
from __future__ import annotations

import time

import httpx
import pytest

from .conftest import ORCH_PORT, POSTGRES_PORT, QDRANT_PORT, THREADS_PORT

pytestmark = pytest.mark.e2e


# Port forwards are now handled by conftest.py k8s_port_forwards fixture


def test_post_task_end_to_end() -> None:
    """Full flow: POST /task → Celery → fake-threads /published."""
    payload = {"persona_id": "ai-jesus", "task_type": "create_post"}

    # 1️⃣  enqueue task
    resp = httpx.post(f"http://localhost:{ORCH_PORT}/task", json=payload, timeout=5)
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"

    # 2️⃣  poll fake-threads until the draft appears (≤ 40 s)
    deadline = time.time() + 40
    while time.time() < deadline:
        out = httpx.get(f"http://localhost:{THREADS_PORT}/published", timeout=5)
        if out.status_code == 200 and out.json():
            # got at least one draft ✅
            assert out.json()[0]["topic"].startswith("ai-jesus")
            break
        time.sleep(1)
    else:
        pytest.fail("Timed-out waiting for fake-threads to store draft")


def test_draft_post_happy_path() -> None:
    """
    End-to-end test for draft post generation happy path.

    Verifies:
    - POST /task triggers content generation
    - Postgres row with hook/body content
    - Vector store has the embedded content
    - Fake-threads receives published content
    - Latency metrics are recorded

    Should complete in <40s.
    """
    import psycopg2
    import qdrant_client

    PG_DSN = f"postgresql://postgres:pass@localhost:{POSTGRES_PORT}/postgres"
    QDRANT_URL = f"http://localhost:{QDRANT_PORT}"
    COLLECTION_NAME = "posts_ai-jesus"

    start_time = time.time()

    # 1️⃣ enqueue a task via orchestrator
    response = httpx.post(
        f"http://localhost:{ORCH_PORT}/task",
        json={
            "persona_id": "ai-jesus",
            "task_type": "create_post",
            "trend_snippet": "solar panels are awesome",
        },
        timeout=10,
    )
    response.raise_for_status()

    # 2️⃣ get initial count, then wait for new content to be published
    initial_response = httpx.get(
        f"http://localhost:{THREADS_PORT}/published", timeout=5
    )
    initial_count = (
        len(initial_response.json()) if initial_response.status_code == 200 else 0
    )

    published_content = None
    for _ in range(40):  # ~40 s budget
        time.sleep(1)
        published = httpx.get(
            f"http://localhost:{THREADS_PORT}/published", timeout=5
        ).json()
        if published and len(published) > initial_count:
            # New content was published - get the latest one
            published_content = published[-1]  # Most recent post
            break
    else:  # pragma: no cover
        pytest.fail("publish never happened within 40s timeout")

    # 3️⃣ verify Postgres has the most recent row with hook/body content
    with psycopg2.connect(PG_DSN) as pg, pg.cursor() as cur:
        cur.execute(
            "SELECT persona_id, hook, body, tokens_used, ts FROM posts ORDER BY ts DESC LIMIT 1"
        )
        row = cur.fetchone()
        assert row is not None, "no post found in database"

        persona_id, hook, body, tokens_used, ts = row

        # Verify content exists and is not empty
        assert persona_id == "ai-jesus", f"wrong persona_id: {persona_id}"
        assert hook and len(hook.strip()) > 0, "hook is empty"
        assert body and len(body.strip()) > 0, "body is empty"
        assert tokens_used == 0, (
            f"tokens_used should be 0 in test mode, got {tokens_used}"
        )
        assert ts is not None, "timestamp not set"

        # Verify hook/body content makes sense
        assert isinstance(hook, str), "hook should be string"
        assert isinstance(body, str), "body should be string"

    # 4️⃣ verify vector store has the embedded content
    qdrant = qdrant_client.QdrantClient(
        url=QDRANT_URL,
        prefer_grpc=False,
        timeout=5,
        check_compatibility=False,  # Ignore version mismatch warnings
    )

    # Check collection exists and has vectors
    count_result = qdrant.count(collection_name=COLLECTION_NAME)
    assert count_result.count >= 1, (
        f"expected at least 1 vector, got {count_result.count}"
    )

    # 5️⃣ verify published content matches database content
    assert published_content is not None, "published content is None"

    # The published content should contain the hook and body
    published_text = published_content.get("content", "")
    assert hook in published_text or body in published_text, (
        "published content doesn't match database hook/body"
    )

    # 6️⃣ verify latency metrics were logged
    metrics_response = httpx.get(f"http://localhost:{ORCH_PORT}/metrics", timeout=10)
    metrics_response.raise_for_status()
    metrics_text = metrics_response.text

    # Verify required metric types exist
    assert "# TYPE request_latency_seconds" in metrics_text, (
        "request_latency_seconds metric not found"
    )
    assert "# TYPE llm_tokens_total" in metrics_text, (
        "llm_tokens_total metric not found"
    )

    # Verify business metrics were recorded during content generation
    # Check that posts were generated (should be > 0 after successful generation)
    assert "posts_generated_total" in metrics_text, (
        "posts_generated_total metric not found"
    )

    # Check that content generation latency was recorded
    assert "content_generation_latency_seconds" in metrics_text, (
        "content_generation_latency_seconds metric not found"
    )

    # 7️⃣ verify test completed within time budget
    elapsed = time.time() - start_time
    assert elapsed < 40.0, f"test took {elapsed:.1f}s, should be <40s"
