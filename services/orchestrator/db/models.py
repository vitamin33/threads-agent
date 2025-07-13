# /services/orchestrator/db/models.py
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    persona_id: Mapped[str] = mapped_column(Text)
    hook: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    tokens_used: Mapped[int] = mapped_column(default=0)
    ts: Mapped[datetime] = mapped_column(default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    payload: Mapped[dict[str, Any]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="queued")
