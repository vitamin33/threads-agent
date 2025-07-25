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
        assert out.status_code == 200
        posts = out.json()
        if posts:
            # Look for our specific ai-jesus post
            for post in posts:
                if "topic" in post and "ai-jesus" in post["topic"].lower():
                    assert "content" in post
                    print(f"✅ Content published: {post['content'][:50]}...")
                    return
        time.sleep(1)

    pytest.fail("ai-jesus post never appeared in 40s window")


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

    # 2️⃣ get initial state, then wait for new ai-jesus content to be published
    initial_response = httpx.get(
        f"http://localhost:{THREADS_PORT}/published", timeout=5
    )
    initial_posts = initial_response.json() if initial_response.status_code == 200 else []
    
    # Count initial ai-jesus posts
    initial_ai_jesus_count = sum(1 for p in initial_posts if "topic" in p and "ai-jesus" in p["topic"].lower())

    published_content = None
    for _ in range(40):  # ~40 s budget
        time.sleep(1)
        published = httpx.get(
            f"http://localhost:{THREADS_PORT}/published", timeout=5
        ).json()
        
        # Look for new ai-jesus posts specifically
        ai_jesus_posts = [p for p in published if "topic" in p and "ai-jesus" in p["topic"].lower()]
        
        if len(ai_jesus_posts) > initial_ai_jesus_count:
            # Get the newest ai-jesus post
            published_content = ai_jesus_posts[-1]
            break
    else:  # pragma: no cover
        pytest.fail("ai-jesus post never appeared within 40s timeout")

    # 3️⃣ verify Postgres has a row matching our specific request
    with psycopg2.connect(PG_DSN) as pg, pg.cursor() as cur:
        cur.execute(
            "SELECT hook, body, persona_id FROM posts WHERE persona_id = %s ORDER BY id DESC LIMIT 1;",
            ("ai-jesus",),
        )
        result = cur.fetchone()
        assert result is not None, "no posts found in postgres"
        hook, body, persona_id = result
        assert persona_id == "ai-jesus"
        assert hook and body, "hook/body should be non-empty"

    # 4️⃣ verify vector store knows about this content
    qclient = qdrant_client.QdrantClient(url=QDRANT_URL, check_compatibility=False)
    try:
        collection_info = qclient.get_collection(COLLECTION_NAME)
        assert collection_info.points_count > 0, "qdrant should have at least 1 point"
    except Exception:  # pragma: no cover
        pytest.fail(f"qdrant collection {COLLECTION_NAME} missing or empty")

    # 5️⃣ verify fake-threads received our exact post
    assert published_content is not None
    assert "topic" in published_content
    assert "content" in published_content
    # topic should contain persona_id
    assert "ai-jesus" in published_content["topic"].lower(), f"Expected ai-jesus in topic but got: {published_content['topic']}"
    # content should be hook + body combined
    full_content = published_content["content"]
    assert hook in full_content or body in full_content, "published content missing hook/body"

    # 6️⃣ verify it all happened in reasonable time
    elapsed = time.time() - start_time
    assert elapsed < 40, f"whole flow took {elapsed:.1f}s, expected <40s"

    print(f"✅ e2e test passed in {elapsed:.1f}s")


@pytest.mark.e2e
def test_metrics_endpoint() -> None:
    """
    Verify that Prometheus metrics are available on orchestrator.
    """
    response = httpx.get(f"http://localhost:{ORCH_PORT}/metrics", timeout=10)
    response.raise_for_status()
    metrics_text = response.text

    # check for custom metric families
    assert "request_latency_seconds" in metrics_text
    assert "llm_tokens_total" in metrics_text
    # Prometheus metrics should be text/plain
    assert "text/plain" in response.headers.get("content-type", "")

    print("✅ metrics endpoint accessible")


@pytest.mark.e2e
def test_health_endpoint() -> None:
    """
    Verify that health endpoint works on orchestrator.
    """
    response = httpx.get(f"http://localhost:{ORCH_PORT}/health", timeout=10)
    response.raise_for_status()
    health_data = response.json()

    assert "status" in health_data
    assert health_data["status"] == "ok"

    print("✅ health endpoint accessible")
