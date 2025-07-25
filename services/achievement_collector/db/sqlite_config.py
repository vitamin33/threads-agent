# SQLite configuration for local achievement storage
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create achievements directory in your home folder
ACHIEVEMENTS_DIR = Path.home() / ".threads-agent" / "achievements"
ACHIEVEMENTS_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database file
SQLITE_DB_PATH = ACHIEVEMENTS_DIR / "achievements.db"
SQLITE_URL = f"sqlite:///{SQLITE_DB_PATH}"

# Create engine with SQLite
sqlite_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},  # Needed for FastAPI
    echo=False,
)

# Session maker
SqliteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)


def get_sqlite_db():
    """Get SQLite database session"""
    db = SqliteSessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_sqlite_db():
    """Initialize SQLite database with tables"""
    from services.achievement_collector.db.models import Base

    Base.metadata.create_all(bind=sqlite_engine)
    print(f"✅ SQLite database initialized at: {SQLITE_DB_PATH}")
    return SQLITE_DB_PATH
