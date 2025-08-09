"""Test fixtures for orchestrator service tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool



@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True for SQL debugging
    )

    # Import only the models we need to avoid PostgreSQL-specific types
    from services.orchestrator.db.models import (
        ContentItem,
        ContentSchedule,
        ContentAnalytics,
    )

    # Create only the tables we need for our tests
    ContentItem.__table__.create(engine, checkfirst=True)
    ContentSchedule.__table__.create(engine, checkfirst=True)
    ContentAnalytics.__table__.create(engine, checkfirst=True)

    yield engine

    # Clean up
    ContentItem.__table__.drop(engine, checkfirst=True)
    ContentSchedule.__table__.drop(engine, checkfirst=True)
    ContentAnalytics.__table__.drop(engine, checkfirst=True)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing."""
    SessionLocal = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def sample_content_data():
    """Sample content data for testing."""
    return {
        "blog_post": {
            "title": "Advanced AI Development Techniques",
            "content": "A comprehensive guide to modern AI development practices and techniques.",
            "content_type": "blog_post",
            "author_id": "ai_expert_001",
            "content_metadata": {
                "tags": ["AI", "Development", "Machine Learning"],
                "estimated_read_time": 8,
                "target_audience": "developers",
            },
        },
        "social_post": {
            "title": "Quick AI Tip",
            "content": "Here's a quick tip for improving your AI model performance!",
            "content_type": "social_post",
            "author_id": "ai_expert_001",
            "content_metadata": {
                "hashtags": ["#AI", "#MachineLearning", "#Tips"],
                "target_platforms": ["linkedin", "twitter"],
            },
        },
    }


@pytest.fixture(scope="function")
def sample_platform_configs():
    """Sample platform configurations for testing."""
    return {
        "linkedin": {
            "hashtags": ["#AI", "#TechLeadership", "#Innovation"],
            "mention_users": ["@techleader"],
            "include_call_to_action": True,
            "optimize_for_engagement": True,
        },
        "devto": {
            "tags": ["ai", "machinelearning", "python"],
            "series_name": "AI Development Series",
            "canonical_url": None,
            "cover_image": "https://example.com/cover.jpg",
        },
        "twitter": {
            "thread_mode": False,
            "hashtags": ["#AI", "#ML"],
            "mention_users": [],
            "include_media": False,
        },
        "medium": {
            "publication": "AI Developer Community",
            "tags": ["artificial-intelligence", "machine-learning", "programming"],
            "subtitle": "Insights from the AI development trenches",
        },
    }
