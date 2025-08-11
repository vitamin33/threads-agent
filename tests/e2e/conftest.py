"""Shared fixtures for e2e tests."""

from __future__ import annotations

import subprocess
import time
from typing import Iterator
import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, Text
from sqlalchemy.orm import sessionmaker

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
    pf_postgres = _port_forward("postgres-0", POSTGRES_PORT, 5432)

    # Give port forwards time to establish
    time.sleep(2)

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


# Database fixtures for emotion tests
@pytest.fixture(scope="session")
def emotion_test_db():
    """Create test database for emotion trajectory tests."""
    # Use in-memory SQLite for tests (avoids PostgreSQL dependency issues)
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    # Import database models after setting environment
    from sqlalchemy import String, Integer, DateTime, Boolean, Float

    # Create SQLite-compatible emotion models
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )

    # Create a minimal subset of tables needed for emotion tests
    # We'll only create the core emotion tables, not all orchestrator tables
    from sqlalchemy import MetaData, Table, Column

    metadata = MetaData()

    # EmotionTrajectory table
    Table(
        "emotion_trajectories",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("post_id", String(50), nullable=False),
        Column("persona_id", String(50), nullable=False),
        Column("content_hash", String(64), nullable=False),
        Column("segment_count", Integer, nullable=False),
        Column("total_duration_words", Integer, nullable=False),
        Column("analysis_model", String(50), nullable=False),
        Column("confidence_score", Float, nullable=False),
        Column("trajectory_type", String(20), nullable=False),
        Column("emotional_variance", Float, nullable=False),
        Column("peak_count", Integer, nullable=False),
        Column("valley_count", Integer, nullable=False),
        Column("transition_count", Integer, nullable=False),
        Column("joy_avg", Float, nullable=False),
        Column("anger_avg", Float, nullable=False),
        Column("fear_avg", Float, nullable=False),
        Column("sadness_avg", Float, nullable=False),
        Column("surprise_avg", Float, nullable=False),
        Column("disgust_avg", Float, nullable=False),
        Column("trust_avg", Float, nullable=False),
        Column("anticipation_avg", Float, nullable=False),
        Column("sentiment_compound", Float, nullable=True),
        Column("sentiment_positive", Float, nullable=True),
        Column("sentiment_neutral", Float, nullable=True),
        Column("sentiment_negative", Float, nullable=True),
        Column("processing_time_ms", Integer, nullable=False),
        Column("created_at", DateTime, nullable=True),
        Column("updated_at", DateTime, nullable=True),
    )

    # EmotionSegment table
    Table(
        "emotion_segments",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("trajectory_id", Integer, nullable=False),
        Column("segment_index", Integer, nullable=False),
        Column("content_text", Text, nullable=False),
        Column("word_count", Integer, nullable=False),
        Column("sentence_count", Integer, nullable=False),
        Column("joy_score", Float, nullable=False),
        Column("anger_score", Float, nullable=False),
        Column("fear_score", Float, nullable=False),
        Column("sadness_score", Float, nullable=False),
        Column("surprise_score", Float, nullable=False),
        Column("disgust_score", Float, nullable=False),
        Column("trust_score", Float, nullable=False),
        Column("anticipation_score", Float, nullable=False),
        Column("sentiment_compound", Float, nullable=True),
        Column("sentiment_positive", Float, nullable=True),
        Column("sentiment_neutral", Float, nullable=True),
        Column("sentiment_negative", Float, nullable=True),
        Column("dominant_emotion", String(20), nullable=False),
        Column("confidence_score", Float, nullable=False),
        Column("is_peak", Boolean, nullable=False),
        Column("is_valley", Boolean, nullable=False),
        Column("created_at", DateTime, nullable=True),
    )

    # EmotionTransition table
    Table(
        "emotion_transitions",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("trajectory_id", Integer, nullable=False),
        Column("from_segment_index", Integer, nullable=False),
        Column("to_segment_index", Integer, nullable=False),
        Column("from_emotion", String(20), nullable=False),
        Column("to_emotion", String(20), nullable=False),
        Column("transition_type", String(30), nullable=False),
        Column("intensity_change", Float, nullable=False),
        Column("transition_speed", Float, nullable=False),
        Column("strength_score", Float, nullable=False),
        Column("created_at", DateTime, nullable=True),
    )

    # EmotionPerformance table
    Table(
        "emotion_performance",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("trajectory_id", Integer, nullable=False),
        Column("post_id", String(100), nullable=False),
        Column("persona_id", String(50), nullable=False),
        Column("engagement_rate", Float, nullable=False),
        Column("likes_count", Integer, nullable=False),
        Column("shares_count", Integer, nullable=False),
        Column("comments_count", Integer, nullable=False),
        Column("reach", Integer, nullable=False),
        Column("impressions", Integer, nullable=False),
        Column("emotion_effectiveness", Float, nullable=False),
        Column("predicted_engagement", Float, nullable=False),
        Column("actual_vs_predicted", Float, nullable=False),
        Column("measured_at", DateTime, nullable=False),
        Column("created_at", DateTime, nullable=True),
    )

    # EmotionTemplate table (simplified for SQLite)
    Table(
        "emotion_templates",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("template_name", String(100), nullable=False),
        Column("template_type", String(30), nullable=False),
        Column("pattern_description", Text, nullable=False),
        Column("segment_count", Integer, nullable=False),
        Column("optimal_duration_words", Integer, nullable=False),
        Column("trajectory_pattern", String(20), nullable=False),
        Column("primary_emotions", Text, nullable=False),  # Store as JSON string
        Column("emotion_sequence", Text, nullable=False),
        Column("transition_patterns", Text, nullable=False),
        Column("usage_count", Integer, nullable=False),
        Column("average_engagement", Float, nullable=False),
        Column("effectiveness_score", Float, nullable=False),
        Column("engagement_correlation", Float, nullable=False),
        Column("version", Integer, nullable=False),
        Column("is_active", Boolean, nullable=False),
        Column("created_at", DateTime, nullable=True),
        Column("updated_at", DateTime, nullable=True),
    )

    metadata.create_all(engine)

    yield engine


@pytest.fixture(scope="function")
def db_session(emotion_test_db):
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=emotion_test_db)
    session = SessionLocal()

    # Clean up any existing data before each test
    from sqlalchemy import MetaData

    metadata = MetaData()
    metadata.reflect(bind=emotion_test_db)
    for table in reversed(metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
