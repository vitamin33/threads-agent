# /services/orchestrator/db/__init__.py
import os

from dotenv import load_dotenv  # optional; dev-only
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

PG_DSN = os.getenv(
    "POSTGRES_DSN",
    "postgresql+psycopg2://user:pass@postgres:5432/threads",
)

engine = create_engine(PG_DSN, pool_pre_ping=True, pool_size=5)

Session = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


__all__ = ["Base", "engine", "Session"]
