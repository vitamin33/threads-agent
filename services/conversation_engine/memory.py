"""Conversation memory system with PostgreSQL persistence and Redis caching."""

import os
import json
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    DateTime,
    Float,
    Integer,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class ConversationStateDB(Base):
    """Database model for conversation state."""

    __tablename__ = "conversation_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    current_state = Column(String(50), nullable=False)
    state_history = Column(JSON, default=list)
    user_profile = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    conversion_probability = Column(Float, default=0.0)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationTurnDB(Base):
    """Database model for individual conversation turns."""

    __tablename__ = "conversation_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(String(100), index=True, nullable=False)
    turn_number = Column(Integer, nullable=False)
    user_message = Column(Text, nullable=False)
    bot_message = Column(Text, nullable=False)
    state_before = Column(String(50), nullable=False)
    state_after = Column(String(50), nullable=False)
    intent_analysis = Column(JSON, default=dict)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


@dataclass
class ConversationMemory:
    """In-memory representation of conversation state."""

    conversation_id: str
    user_id: str
    current_state: str
    state_history: List[str]
    user_profile: Dict[str, Any]
    conversation_turns: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    conversion_probability: float = 0.0
    last_interaction: datetime = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["last_interaction"] = (
            self.last_interaction.isoformat() if self.last_interaction else None
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMemory":
        """Create from dictionary."""
        if "last_interaction" in data and data["last_interaction"]:
            data["last_interaction"] = datetime.fromisoformat(data["last_interaction"])
        return cls(**data)


class ConversationMemorySystem:
    """Manages conversation memory with PostgreSQL persistence and Redis caching."""

    def __init__(self):
        # PostgreSQL setup
        self.db_url = os.getenv(
            "DATABASE_URL", "postgresql://user:pass@localhost/conversations"
        )
        self.engine = create_engine(self.db_url, pool_size=10, max_overflow=20)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Redis setup
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
        )

        # Cache configuration
        self.cache_ttl = int(os.getenv("CONVERSATION_CACHE_TTL", "3600"))  # 1 hour
        self.cache_prefix = "conv:"

        # Create tables
        Base.metadata.create_all(bind=self.engine)

    async def get_conversation(
        self, conversation_id: str
    ) -> Optional[ConversationMemory]:
        """
        Get conversation from cache or database.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            ConversationMemory if found, None otherwise
        """
        # Try cache first
        cached = await self._get_from_cache(conversation_id)
        if cached:
            return cached

        # Fall back to database
        with self.SessionLocal() as session:
            db_conv = (
                session.query(ConversationStateDB)
                .filter_by(conversation_id=conversation_id)
                .first()
            )

            if not db_conv:
                return None

            # Get conversation turns
            turns = (
                session.query(ConversationTurnDB)
                .filter_by(conversation_id=conversation_id)
                .order_by(ConversationTurnDB.turn_number)
                .all()
            )

            # Build memory object
            memory = ConversationMemory(
                conversation_id=db_conv.conversation_id,
                user_id=db_conv.user_id,
                current_state=db_conv.current_state,
                state_history=db_conv.state_history or [],
                user_profile=db_conv.user_profile or {},
                conversation_turns=[self._turn_to_dict(turn) for turn in turns],
                metadata=db_conv.metadata or {},
                conversion_probability=db_conv.conversion_probability,
                last_interaction=db_conv.last_interaction,
            )

            # Cache for next time
            await self._save_to_cache(memory)

            return memory

    async def save_conversation(self, memory: ConversationMemory) -> None:
        """
        Save conversation to both cache and database.

        Args:
            memory: ConversationMemory to save
        """
        # Save to cache immediately
        await self._save_to_cache(memory)

        # Save to database
        with self.SessionLocal() as session:
            # Update or create conversation state
            db_conv = (
                session.query(ConversationStateDB)
                .filter_by(conversation_id=memory.conversation_id)
                .first()
            )

            if db_conv:
                # Update existing
                db_conv.current_state = memory.current_state
                db_conv.state_history = memory.state_history
                db_conv.user_profile = memory.user_profile
                db_conv.metadata = memory.metadata
                db_conv.conversion_probability = memory.conversion_probability
                db_conv.last_interaction = memory.last_interaction or datetime.utcnow()
                db_conv.updated_at = datetime.utcnow()
            else:
                # Create new
                db_conv = ConversationStateDB(
                    conversation_id=memory.conversation_id,
                    user_id=memory.user_id,
                    current_state=memory.current_state,
                    state_history=memory.state_history,
                    user_profile=memory.user_profile,
                    metadata=memory.metadata,
                    conversion_probability=memory.conversion_probability,
                    last_interaction=memory.last_interaction or datetime.utcnow(),
                )
                session.add(db_conv)

            session.commit()

    async def add_conversation_turn(
        self,
        conversation_id: str,
        user_message: str,
        bot_message: str,
        state_before: str,
        state_after: str,
        intent_analysis: Dict[str, Any],
        response_time_ms: int,
    ) -> None:
        """Add a new conversation turn."""
        with self.SessionLocal() as session:
            # Get current turn number
            max_turn = (
                session.query(ConversationTurnDB)
                .filter_by(conversation_id=conversation_id)
                .count()
            )

            # Create new turn
            turn = ConversationTurnDB(
                conversation_id=conversation_id,
                turn_number=max_turn + 1,
                user_message=user_message,
                bot_message=bot_message,
                state_before=state_before,
                state_after=state_after,
                intent_analysis=intent_analysis,
                response_time_ms=response_time_ms,
            )
            session.add(turn)
            session.commit()

        # Invalidate cache to force reload with new turn
        await self._invalidate_cache(conversation_id)

    async def get_active_conversations(self, hours: int = 24) -> List[str]:
        """Get list of active conversation IDs."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        with self.SessionLocal() as session:
            active = (
                session.query(ConversationStateDB.conversation_id)
                .filter(ConversationStateDB.last_interaction >= cutoff)
                .all()
            )

            return [conv[0] for conv in active]

    async def get_user_conversations(self, user_id: str) -> List[ConversationMemory]:
        """Get all conversations for a user."""
        with self.SessionLocal() as session:
            convs = (
                session.query(ConversationStateDB)
                .filter_by(user_id=user_id)
                .order_by(ConversationStateDB.last_interaction.desc())
                .all()
            )

            memories = []
            for conv in convs:
                memory = await self.get_conversation(conv.conversation_id)
                if memory:
                    memories.append(memory)

            return memories

    async def _get_from_cache(
        self, conversation_id: str
    ) -> Optional[ConversationMemory]:
        """Get conversation from Redis cache."""
        key = f"{self.cache_prefix}{conversation_id}"
        cached = self.redis_client.get(key)

        if cached:
            data = json.loads(cached)
            return ConversationMemory.from_dict(data)

        return None

    async def _save_to_cache(self, memory: ConversationMemory) -> None:
        """Save conversation to Redis cache."""
        key = f"{self.cache_prefix}{memory.conversation_id}"
        data = json.dumps(memory.to_dict())
        self.redis_client.setex(key, self.cache_ttl, data)

    async def _invalidate_cache(self, conversation_id: str) -> None:
        """Remove conversation from cache."""
        key = f"{self.cache_prefix}{conversation_id}"
        self.redis_client.delete(key)

    def _turn_to_dict(self, turn: ConversationTurnDB) -> Dict[str, Any]:
        """Convert database turn to dictionary."""
        return {
            "turn_number": turn.turn_number,
            "user_message": turn.user_message,
            "bot_message": turn.bot_message,
            "state_before": turn.state_before,
            "state_after": turn.state_after,
            "intent_analysis": turn.intent_analysis,
            "response_time_ms": turn.response_time_ms,
            "created_at": turn.created_at.isoformat(),
        }

    def analyze_conversation_patterns(self, conversation_id: str) -> Dict[str, Any]:
        """Analyze patterns in a conversation for insights."""
        with self.SessionLocal() as session:
            turns = (
                session.query(ConversationTurnDB)
                .filter_by(conversation_id=conversation_id)
                .order_by(ConversationTurnDB.turn_number)
                .all()
            )

            if not turns:
                return {}

            # Analyze patterns
            total_turns = len(turns)
            avg_response_time = (
                sum(t.response_time_ms or 0 for t in turns) / total_turns
            )
            state_transitions = [(t.state_before, t.state_after) for t in turns]

            # Find repeated objections
            objections = []
            for turn in turns:
                if turn.intent_analysis and "objection_type" in turn.intent_analysis:
                    objections.append(turn.intent_analysis["objection_type"])

            return {
                "total_turns": total_turns,
                "avg_response_time_ms": avg_response_time,
                "state_transitions": state_transitions,
                "repeated_objections": list(set(objections)),
                "conversion_journey_length": len(set(t.state_after for t in turns)),
                "stuck_in_state": turns[-1].state_after if turns else None,
            }
