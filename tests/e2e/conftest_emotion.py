"""Database fixtures for emotion trajectory e2e tests."""

import os
import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///./test_emotion.db"

# Import database models
from services.orchestrator.db import Base


@pytest.fixture(scope="session")
def emotion_test_db():
    """Create test database for emotion trajectory tests."""
    engine = create_engine(
        "sqlite:///./test_emotion.db", connect_args={"check_same_thread": False}
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)

    # Remove test database file
    import os

    try:
        os.remove("test_emotion.db")
    except FileNotFoundError:
        pass


@pytest.fixture(scope="function")
def db_session(emotion_test_db):
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=emotion_test_db)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
