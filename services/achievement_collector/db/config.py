# Database Configuration

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Check if we should use SQLite
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"

# Check if we're in test mode
_in_test = (
    "pytest" in os.environ.get("_", "")
    or os.environ.get("PYTEST_CURRENT_TEST") is not None
    or "test" in os.environ.get("DATABASE_URL", "").lower()
)

if USE_SQLITE:
    # Use SQLite for local persistent storage
    # Check for existing test_achievements.db first
    local_db_path = Path("test_achievements.db")
    if local_db_path.exists():
        SQLITE_DB_PATH = local_db_path.absolute()
    else:
        ACHIEVEMENTS_DIR = Path.home() / ".threads-agent" / "achievements"
        ACHIEVEMENTS_DIR.mkdir(parents=True, exist_ok=True)
        SQLITE_DB_PATH = ACHIEVEMENTS_DIR / "achievements.db"
    DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"
    connect_args = {"check_same_thread": False}
    print(f"🗄️  Using SQLite database at: {SQLITE_DB_PATH}")
else:
    # Database URL from environment or default
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:pass@localhost:5432/achievement_collector",
    )
    connect_args = {}

# Create engine with better test handling
if _in_test:
    # In test mode, use SQLite in memory to avoid connection issues
    engine = create_engine(
        "sqlite:///:memory:",
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        connect_args={"check_same_thread": False},
    )
else:
    # Production mode - attempt to create normal engine
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_size=20,
            max_overflow=0,
            pool_pre_ping=True,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            connect_args=connect_args,
        )
    except Exception:
        # If connection fails, create a non-connecting engine for import safety
        engine = create_engine(
            "sqlite:///:memory:",
            echo=False,
            connect_args={"check_same_thread": False},
        )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
