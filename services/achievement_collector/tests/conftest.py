# Pytest configuration for achievement collector tests

import os
import sys
from pathlib import Path

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Set test environment variables before importing any modules
os.environ["DATABASE_URL"] = "sqlite:///./test_achievements.db"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"
os.environ["PORTFOLIO_OUTPUT_DIR"] = "/tmp/test_portfolios"

# Clean up any Kubernetes environment variables that might interfere
for key in list(os.environ.keys()):
    if key.endswith("_PORT") and os.environ[key].startswith("tcp://"):
        del os.environ[key]

from services.achievement_collector.db.models import Base  # noqa: E402


@pytest.fixture(scope="session")
def test_db():
    """Create test database for session."""
    engine = create_engine(
        "sqlite:///./test_achievements.db", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a new database session for each test."""
    connection = test_db.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
