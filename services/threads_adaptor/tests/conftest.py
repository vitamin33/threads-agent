# Pytest configuration for threads_adaptor tests

import os
import sys
from pathlib import Path

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Set test environment variables before importing any modules
os.environ["DATABASE_URL"] = "sqlite:///./test_threads.db"
os.environ["THREADS_APP_ID"] = "test_app_id"
os.environ["THREADS_APP_SECRET"] = "test_secret"
os.environ["THREADS_ACCESS_TOKEN"] = "test_token"
os.environ["THREADS_USER_ID"] = "test_user_id"

# Clean up Kubernetes environment variables
for key in list(os.environ.keys()):
    if key.endswith("_PORT") and os.environ[key].startswith("tcp://"):
        del os.environ[key]

# Import after setting environment variables
from services.threads_adaptor.main import Base  # noqa: E402


@pytest.fixture(scope="session")
def test_db():
    """Create test database for session."""
    engine = create_engine(
        "sqlite:///./test_threads.db", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_db):
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db)
    session = SessionLocal()
    yield session
    session.close()
