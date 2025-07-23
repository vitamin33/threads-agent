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


class HookVariant(Base):
    __tablename__ = "hook_variants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    variant_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    batch_id: Mapped[str] = mapped_column(Text, index=True)
    post_id: Mapped[int] = mapped_column(BigInteger, nullable=True)  # FK to posts when posted
    pattern_id: Mapped[str] = mapped_column(Text, index=True)
    pattern_category: Mapped[str] = mapped_column(Text)
    emotion_modifier: Mapped[str] = mapped_column(Text, nullable=True)
    hook_content: Mapped[str] = mapped_column(Text)
    template: Mapped[str] = mapped_column(Text)
    original_content: Mapped[str] = mapped_column(Text)
    persona_id: Mapped[str] = mapped_column(Text)
    expected_engagement_rate: Mapped[float] = mapped_column(default=0.0)
    actual_engagement_rate: Mapped[float] = mapped_column(nullable=True)
    impressions: Mapped[int] = mapped_column(default=0)
    engagements: Mapped[int] = mapped_column(default=0)
    selected_for_posting: Mapped[bool] = mapped_column(default=False)
    experiment_id: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
