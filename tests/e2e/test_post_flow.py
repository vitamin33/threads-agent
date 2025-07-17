# tests/e2e/test_post_flow.py
from __future__ import annotations

import subprocess
import time
from typing import Iterator

import httpx
import pytest

pytestmark = pytest.mark.e2e

ORCH_PORT = 8080
THREADS_PORT = 9009


def _port_forward(svc: str, local: int, remote: int) -> subprocess.Popen[bytes]:
    """Run `kubectl port-forward` in the background and return its process."""
    return subprocess.Popen(
        ["kubectl", "port-forward", f"svc/{svc}", f"{local}:{remote}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@pytest.fixture(autouse=True)
def port_forwards() -> Iterator[None]:
    """Establish local forwards to the orchestrator and fake-threads services."""
    pf1 = _port_forward("orchestrator", ORCH_PORT, 8080)
    pf2 = _port_forward("fake-threads", THREADS_PORT, 9009)
    time.sleep(2)  # give k8s a moment
    try:
        yield
    finally:
        pf1.terminate()
        pf2.terminate()


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
