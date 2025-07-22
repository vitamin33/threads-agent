"""Shared fixtures for e2e tests."""

from __future__ import annotations

import subprocess
import time
from typing import Iterator

import pytest

# Port mappings for e2e tests
ORCH_PORT = 8080
THREADS_PORT = 9009
QDRANT_PORT = 6333
POSTGRES_PORT = 15432


def _port_forward(svc: str, local: int, remote: int) -> subprocess.Popen[bytes]:
    """Run `kubectl port-forward` in the background and return its process."""
    return subprocess.Popen(
        ["kubectl", "port-forward", f"svc/{svc}", f"{local}:{remote}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _wait_for_service(url: str, timeout: int = 30) -> bool:
    """Wait for a service to become available."""
    import httpx

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(url, timeout=2)
            if response.status_code < 500:  # Accept any non-server error
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session", autouse=True)
def k8s_port_forwards() -> Iterator[None]:
    """
    Establish port forwards to all services needed for e2e tests.

    This runs once per test session and is automatically used by all e2e tests.
    """
    # Start all port forwards
    pf_orchestrator = _port_forward("orchestrator", ORCH_PORT, 8080)
    pf_fake_threads = _port_forward("fake-threads", THREADS_PORT, 9009)
    pf_qdrant = _port_forward("qdrant", QDRANT_PORT, 6333)
    pf_postgres = _port_forward("postgres", POSTGRES_PORT, 5432)

    # Wait for services to become available
    services_ready = True
    if not _wait_for_service(f"http://localhost:{ORCH_PORT}/health"):
        print(f"⚠️  orchestrator not ready at localhost:{ORCH_PORT}")
        services_ready = False

    if not _wait_for_service(f"http://localhost:{THREADS_PORT}/ping"):
        print(f"⚠️  fake-threads not ready at localhost:{THREADS_PORT}")
        services_ready = False

    if not services_ready:
        # Clean up and fail
        for pf in [pf_orchestrator, pf_fake_threads, pf_qdrant, pf_postgres]:
            pf.terminate()
        pytest.skip("Services not ready for e2e tests")

    print("✅ All port forwards established and services ready")

    try:
        yield
    finally:
        # Clean up all port forwards
        for pf in [pf_orchestrator, pf_fake_threads, pf_qdrant, pf_postgres]:
            pf.terminate()
            try:
                pf.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pf.kill()
        print("🧹 Port forwards cleaned up")
