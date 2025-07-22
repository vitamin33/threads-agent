# services/viral_engine/tests/unit/test_reply_magnetizer.py
from __future__ import annotations

import pytest

from services.viral_engine.reply_magnetizer import ReplyMagnetizer


@pytest.fixture
def reply_magnetizer():
    """Create ReplyMagnetizer instance for testing"""
    return ReplyMagnetizer()


class TestReplyMagnetizer:
    """Test suite for ReplyMagnetizer"""

    def test_initialization(self, reply_magnetizer):
        """Test reply magnetizer initializes correctly"""
        assert isinstance(reply_magnetizer, ReplyMagnetizer)
        assert "question_hooks" in reply_magnetizer.conversation_starters
        assert "controversy_triggers" in reply_magnetizer.conversation_starters
        assert "engagement_calls" in reply_magnetizer.conversation_starters
        assert "ai-jesus" in reply_magnetizer.persona_styles
        assert "ai-elon" in reply_magnetizer.persona_styles

    def test_magnet_injection_basic(self, reply_magnetizer):
        """Test basic magnet injection"""
        content = "AI is transforming how we work and live."
        persona_id = "ai-jesus"

        enhanced, metadata = reply_magnetizer.inject_reply_magnets(
            content, persona_id, magnet_count=1
        )

        # Check enhancement
        assert enhanced != content
        assert len(enhanced) > len(content)

        # Check metadata
        assert len(metadata) == 1
        assert metadata[0]["persona_id"] == persona_id
        assert "magnet_type" in metadata[0]
        assert "magnet_text" in metadata[0]
        assert "position" in metadata[0]

    def test_multiple_magnets(self, reply_magnetizer):
        """Test injecting multiple magnets"""
        content = "This is a test post about AI and technology trends."

        enhanced, metadata = reply_magnetizer.inject_reply_magnets(
            content, "ai-elon", magnet_count=2
        )

        assert len(metadata) == 2
        # Should have different positions
        positions = [m["position"] for m in metadata]
        assert len(set(positions)) >= 1  # At least one unique position

    def test_persona_specific_magnets(self, reply_magnetizer):
        """Test persona-specific magnet selection"""
        content = "Let's discuss the future of humanity."

        # Test AI Jesus persona
        enhanced_jesus, metadata_jesus = reply_magnetizer.inject_reply_magnets(
            content, "ai-jesus"
        )

        # Test AI Elon persona
        enhanced_elon, metadata_elon = reply_magnetizer.inject_reply_magnets(
            content, "ai-elon"
        )

        # They should produce different results
        assert enhanced_jesus != enhanced_elon

        # Check for persona-appropriate types
        jesus_types = metadata_jesus[0]["magnet_type"]
        elon_types = metadata_elon[0]["magnet_type"]

        assert jesus_types in ["question_hooks", "engagement_calls"]
        assert elon_types in ["controversy_triggers", "authority_questions"]

    def test_content_analysis(self, reply_magnetizer):
        """Test content analysis functionality"""
        # Test with question
        content_with_question = "What do you think about AI?"
        analysis1 = reply_magnetizer._analyze_content(content_with_question)
        assert analysis1["has_question"] is True

        # Test with list
        content_with_list = "Here are 3 reasons: 1. Speed 2. Scale 3. Impact"
        analysis2 = reply_magnetizer._analyze_content(content_with_list)
        assert analysis2["has_list"] is True

        # Test with controversy
        content_with_controversy = "Unpopular opinion: Everyone is wrong about this."
        analysis3 = reply_magnetizer._analyze_content(content_with_controversy)
        assert analysis3["has_controversy"] is True

    def test_position_strategies(self, reply_magnetizer):
        """Test different position strategies"""
        content = "First sentence. Middle sentence. Last sentence."

        # Test ending position
        enhanced, metadata = reply_magnetizer.inject_reply_magnets(
            content, "test", magnet_count=1
        )

        # Most likely at end (70% probability)
        assert metadata[0]["position_strategy"] in ["ending", "middle", "beginning"]

        # Verify actual injection
        if metadata[0]["position"] == "end":
            assert enhanced.endswith(metadata[0]["magnet_text"])

    def test_magnet_removal(self, reply_magnetizer):
        """Test magnet removal functionality"""
        # Create content with known magnets
        content_with_magnets = (
            "This is great. What's your experience with this? Drop a 🔥 if you agree"
        )

        cleaned = reply_magnetizer.remove_magnets(content_with_magnets)

        assert "What's your experience with this?" not in cleaned
        assert "Drop a 🔥 if you agree" not in cleaned
        assert "This is great." in cleaned

    def test_contextual_magnet_selection(self, reply_magnetizer):
        """Test that magnets are selected based on content context"""
        # Content with existing controversy should get question hooks
        controversial_content = "Unpopular opinion: All social media is toxic."

        enhanced, metadata = reply_magnetizer.inject_reply_magnets(
            controversial_content,
            "default",
            magnet_types=["question_hooks", "controversy_triggers"],
        )

        # Should prefer question hooks since content already has controversy
        assert metadata[0]["magnet_type"] == "question_hooks"

    def test_custom_magnet_usage(self, reply_magnetizer):
        """Test that custom persona magnets are sometimes used"""
        content = "Let's explore this together."

        # Run multiple times to test probability
        used_custom = False
        for _ in range(20):
            enhanced, metadata = reply_magnetizer.inject_reply_magnets(
                content, "ai-jesus"
            )
            if (
                metadata[0]["magnet_text"]
                in reply_magnetizer.persona_styles["ai-jesus"]["custom_magnets"]
            ):
                used_custom = True
                break

        # Should use custom magnets at least once in 20 tries (30% probability)
        assert used_custom

    def test_performance_analytics(self, reply_magnetizer):
        """Test performance analytics structure"""
        analytics = reply_magnetizer.get_magnet_performance()

        assert "magnet_type_performance" in analytics
        assert "best_performers" in analytics
        assert "recommendations" in analytics

        # Check structure
        perf = analytics["magnet_type_performance"]
        assert "question_hooks" in perf
        assert "avg_replies" in perf["question_hooks"]
        assert "engagement_rate" in perf["question_hooks"]
