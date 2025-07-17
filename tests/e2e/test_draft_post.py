# /tests/e2e/test_draft_post.py
"""
End-to-end “happy path” for a single post …

(unchanged doc-string)
"""

from __future__ import annotations

import time
from typing import Generator

import httpx
import psycopg2
import pytest

PG_DSN = "postgresql://postgres:pass@localhost:5432/postgres"

# ------------------------------------------------------------------
# Local runs: if the e2e harness isn't registered, skip at collection
# ------------------------------------------------------------------
if "just_e2e_prepare" not in globals():  # pragma: no cover

    @pytest.fixture(scope="session")
    def just_e2e_prepare() -> Generator[None, None, None]:
        """Stub fixture so local unit runs skip this E2E test cleanly."""
        pytest.skip("e2e environment not available locally", allow_module_level=True)
        yield


@pytest.mark.e2e
def test_draft_post(just_e2e_prepare: None) -> None:
    # 1️⃣ enqueue a task via orchestrator
    with httpx.Client() as cli:
        cli.post(
            "http://localhost:8080/task",
            json={
                "persona_id": "ai-jesus",
                "task_type": "create_post",
                "trend_snippet": "solar panels are awesome",
            },
        ).raise_for_status()

        # 2️⃣ wait until fake-threads holds exactly 1 published item
        for _ in range(40):  # ~40 s budget
            time.sleep(1)
            published = cli.get("http://localhost:9009/published").json()
            if published and len(published) == 1:
                break
        else:  # pragma: no cover
            pytest.fail("publish never happened")

    # 3️⃣ verify Postgres has exactly one row
    with psycopg2.connect(PG_DSN) as pg, pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM posts")
        row = cur.fetchone()
        assert row is not None, "query returned no row"
        count: int = row[0]
        assert count == 1
