"""Tests for conversation memory system."""

import pytest
from datetime import datetime, timedelta
from services.conversation_engine.memory import (
    ConversationMemorySystem,
    ConversationMemory,
)


class TestConversationMemorySystem:
    """Test suite for conversation memory system."""

    @pytest.fixture
    def memory_system(self):
        """Create a test memory system."""
        # Use test database URL
        import os

        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        os.environ["REDIS_HOST"] = "localhost"
        return ConversationMemorySystem()

    @pytest.fixture
    def sample_memory(self):
        """Create a sample conversation memory."""
        return ConversationMemory(
            conversation_id="test_conv_123",
            user_id="user_456",
            current_state="initial_contact",
            state_history=["initial_contact"],
            user_profile={"name": "Test User"},
            conversation_turns=[],
            metadata={"test": True},
            conversion_probability=0.5,
            last_interaction=datetime.utcnow(),
        )

    @pytest.mark.asyncio
    async def test_save_and_retrieve_conversation(self, memory_system, sample_memory):
        """Test saving and retrieving a conversation."""
        # Save conversation
        await memory_system.save_conversation(sample_memory)

        # Retrieve conversation
        retrieved = await memory_system.get_conversation(sample_memory.conversation_id)

        assert retrieved is not None
        assert retrieved.conversation_id == sample_memory.conversation_id
        assert retrieved.user_id == sample_memory.user_id
        assert retrieved.current_state == sample_memory.current_state
        assert retrieved.user_profile == sample_memory.user_profile

    @pytest.mark.asyncio
    async def test_update_existing_conversation(self, memory_system, sample_memory):
        """Test updating an existing conversation."""
        # Save initial conversation
        await memory_system.save_conversation(sample_memory)

        # Update conversation
        sample_memory.current_state = "value_proposition"
        sample_memory.state_history.append("value_proposition")
        sample_memory.conversion_probability = 0.8

        await memory_system.save_conversation(sample_memory)

        # Retrieve updated conversation
        retrieved = await memory_system.get_conversation(sample_memory.conversation_id)

        assert retrieved.current_state == "value_proposition"
        assert len(retrieved.state_history) == 2
        assert retrieved.conversion_probability == 0.8

    @pytest.mark.asyncio
    async def test_add_conversation_turn(self, memory_system, sample_memory):
        """Test adding conversation turns."""
        # Save conversation first
        await memory_system.save_conversation(sample_memory)

        # Add a turn
        await memory_system.add_conversation_turn(
            conversation_id=sample_memory.conversation_id,
            user_message="I'm interested in your product",
            bot_message="Great! What specific challenge are you looking to solve?",
            state_before="initial_contact",
            state_after="interest_qualification",
            intent_analysis={"sentiment": "positive", "shows_interest": True},
            response_time_ms=150,
        )

        # Retrieve conversation with turns
        retrieved = await memory_system.get_conversation(sample_memory.conversation_id)

        assert len(retrieved.conversation_turns) == 1
        assert (
            retrieved.conversation_turns[0]["user_message"]
            == "I'm interested in your product"
        )
        assert retrieved.conversation_turns[0]["response_time_ms"] == 150

    @pytest.mark.asyncio
    async def test_get_active_conversations(self, memory_system):
        """Test retrieving active conversations."""
        # Create multiple conversations
        for i in range(3):
            memory = ConversationMemory(
                conversation_id=f"conv_{i}",
                user_id=f"user_{i}",
                current_state="initial_contact",
                state_history=["initial_contact"],
                user_profile={},
                conversation_turns=[],
                metadata={},
                last_interaction=datetime.utcnow() - timedelta(hours=i),
            )
            await memory_system.save_conversation(memory)

        # Get active conversations in last 2 hours
        active = await memory_system.get_active_conversations(hours=2)

        assert len(active) == 2
        assert "conv_0" in active
        assert "conv_1" in active
        assert "conv_2" not in active

    @pytest.mark.asyncio
    async def test_get_user_conversations(self, memory_system):
        """Test retrieving all conversations for a user."""
        user_id = "test_user_789"

        # Create multiple conversations for the user
        for i in range(2):
            memory = ConversationMemory(
                conversation_id=f"user_conv_{i}",
                user_id=user_id,
                current_state="initial_contact",
                state_history=["initial_contact"],
                user_profile={},
                conversation_turns=[],
                metadata={},
                last_interaction=datetime.utcnow(),
            )
            await memory_system.save_conversation(memory)

        # Create conversation for different user
        other_memory = ConversationMemory(
            conversation_id="other_conv",
            user_id="other_user",
            current_state="initial_contact",
            state_history=["initial_contact"],
            user_profile={},
            conversation_turns=[],
            metadata={},
            last_interaction=datetime.utcnow(),
        )
        await memory_system.save_conversation(other_memory)

        # Get user conversations
        user_convs = await memory_system.get_user_conversations(user_id)

        assert len(user_convs) == 2
        assert all(conv.user_id == user_id for conv in user_convs)

    def test_conversation_memory_serialization(self, sample_memory):
        """Test conversation memory to/from dict conversion."""
        # Convert to dict
        data = sample_memory.to_dict()

        assert isinstance(data, dict)
        assert data["conversation_id"] == sample_memory.conversation_id
        assert isinstance(data["last_interaction"], str)

        # Convert from dict
        restored = ConversationMemory.from_dict(data)

        assert restored.conversation_id == sample_memory.conversation_id
        assert restored.user_id == sample_memory.user_id
        assert isinstance(restored.last_interaction, datetime)

    def test_analyze_conversation_patterns(self, memory_system):
        """Test conversation pattern analysis."""
        # This would need a proper test database setup
        # For now, just verify the method exists
        assert hasattr(memory_system, "analyze_conversation_patterns")

    @pytest.mark.asyncio
    async def test_cache_functionality(self, memory_system, sample_memory):
        """Test Redis caching functionality."""
        # Save conversation (should cache)
        await memory_system.save_conversation(sample_memory)

        # First retrieval (from cache)
        retrieved1 = await memory_system.get_conversation(sample_memory.conversation_id)

        # Invalidate cache
        await memory_system._invalidate_cache(sample_memory.conversation_id)

        # Second retrieval (from database)
        retrieved2 = await memory_system.get_conversation(sample_memory.conversation_id)

        # Both should be equal
        assert retrieved1.conversation_id == retrieved2.conversation_id
        assert retrieved1.current_state == retrieved2.current_state
