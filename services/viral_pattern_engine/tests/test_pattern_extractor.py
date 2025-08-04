"""Tests for viral pattern extraction."""

import pytest
from datetime import datetime
from services.viral_scraper.models import ViralPost
from services.viral_pattern_engine.pattern_extractor import ViralPatternExtractor


class TestViralPatternExtractor:
    """Test cases for viral pattern extraction."""

    @pytest.fixture
    def viral_post_hook_pattern(self):
        """Sample viral post with a clear hook pattern."""
        return ViralPost(
            content="Just discovered this incredible Python library that automates 90% of my data analysis!",
            account_id="test_user",
            post_url="https://threads.net/test/post1",
            timestamp=datetime.now(),
            likes=1500,
            comments=300,
            shares=150,
            engagement_rate=0.85,
            performance_percentile=95.0,
        )

    @pytest.fixture
    def viral_post_emotion_pattern(self):
        """Sample viral post with strong emotional content."""
        return ViralPost(
            content="I can't believe how AMAZING this new AI tool is! Mind-blown! 🤯",
            account_id="test_user",
            post_url="https://threads.net/test/post2",
            timestamp=datetime.now(),
            likes=2000,
            comments=450,
            shares=200,
            engagement_rate=0.92,
            performance_percentile=98.5,
        )

    @pytest.fixture
    def extractor(self):
        """Create pattern extractor instance."""
        return ViralPatternExtractor()

    def test_extract_hook_pattern_discovery_template(
        self, extractor, viral_post_hook_pattern
    ):
        """Test extraction of 'just discovered' hook pattern."""
        patterns = extractor.extract_patterns(viral_post_hook_pattern)

        assert patterns is not None
        assert "hook_patterns" in patterns
        assert len(patterns["hook_patterns"]) > 0

        hook_pattern = patterns["hook_patterns"][0]
        assert "discovery" in hook_pattern["type"]
        assert (
            "{tool}" in hook_pattern["template"]
            or "{library}" in hook_pattern["template"]
        )
        assert hook_pattern["confidence"] > 0.7

    def test_extract_emotion_pattern_excitement(
        self, extractor, viral_post_emotion_pattern
    ):
        """Test extraction of emotional patterns."""
        patterns = extractor.extract_patterns(viral_post_emotion_pattern)

        assert patterns is not None
        assert "emotion_patterns" in patterns
        assert len(patterns["emotion_patterns"]) > 0

        # Check for new advanced emotion analysis format
        emotion = patterns["emotion_patterns"][0]
        if "emotions" in emotion:
            # New format: advanced multi-model analysis
            assert (
                emotion["emotions"]["joy"] > 0.7
            )  # Should detect high joy for "AMAZING" content
            assert emotion["confidence"] > 0.6
        else:
            # Legacy format: backward compatibility
            assert emotion["type"] in ["excitement", "amazement", "surprise"]
            assert emotion["intensity"] > 0.7
            assert emotion["confidence"] > 0.6

    def test_extract_patterns_returns_dict_structure(
        self, extractor, viral_post_hook_pattern
    ):
        """Test that extract_patterns returns expected dictionary structure."""
        patterns = extractor.extract_patterns(viral_post_hook_pattern)

        # Test the basic structure exists
        expected_keys = [
            "hook_patterns",
            "emotion_patterns",
            "structure_patterns",
            "engagement_score",
        ]
        for key in expected_keys:
            assert key in patterns, f"Missing key: {key}"

    def test_extract_patterns_with_low_performing_post(self, extractor):
        """Test pattern extraction with low-performing post."""
        low_performance_post = ViralPost(
            content="Regular post without special patterns.",
            account_id="test_user",
            post_url="https://threads.net/test/post3",
            timestamp=datetime.now(),
            likes=10,
            comments=2,
            shares=0,
            engagement_rate=0.15,
            performance_percentile=25.0,
        )

        patterns = extractor.extract_patterns(low_performance_post)

        # Should still return structure but with empty or low-confidence patterns
        assert patterns is not None
        assert patterns["engagement_score"] < 0.5

    def test_extract_patterns_uses_advanced_emotion_analysis(self, extractor):
        """Test that pattern extractor uses advanced multi-model emotion analysis."""
        post_with_complex_emotions = ViralPost(
            content="I'm so excited about this project but also worried about the deadlines. It's amazing how challenging and rewarding this work can be!",
            account_id="test_user",
            post_url="https://threads.net/test/complex",
            timestamp=datetime.now(),
            likes=1000,
            comments=200,
            shares=100,
            engagement_rate=0.75,
            performance_percentile=85.0,
        )

        patterns = extractor.extract_patterns(post_with_complex_emotions)

        # Should use advanced emotion analysis
        assert "emotion_patterns" in patterns
        emotion_patterns = patterns["emotion_patterns"]
        assert len(emotion_patterns) > 0

        # Should detect multiple emotions with confidence scores
        emotion_pattern = emotion_patterns[0]
        assert "emotions" in emotion_pattern
        assert "confidence" in emotion_pattern
        assert "model_info" in emotion_pattern

        # Should detect at least joy and fear from the content
        emotions = emotion_pattern["emotions"]
        assert emotions["joy"] > 0.3  # excited, amazing
        assert emotions["fear"] > 0.1  # worried

    def test_extract_patterns_includes_emotion_trajectory_for_long_content(
        self, extractor
    ):
        """Test that pattern extractor includes emotion trajectory for multi-segment content."""
        # Long content that can be segmented (>50 words for trajectory analysis)
        long_content = (
            "Let me share my detailed experience with this revolutionary new development tool that has completely transformed my workflow. "
            "At first, I was genuinely skeptical about its capabilities and wondered if it could truly deliver on all the promised features. "
            "But then I tried it out for the first time and was completely amazed by how intuitive and powerful it actually turned out to be! "
            "However, I did encounter some frustrating bugs and technical issues that initially made me question my decision to adopt this solution. "
            "Thankfully, the support team was absolutely incredible and they fixed everything quickly while providing excellent customer service throughout the entire process."
        )

        post_with_trajectory = ViralPost(
            content=long_content,
            account_id="test_user",
            post_url="https://threads.net/test/trajectory",
            timestamp=datetime.now(),
            likes=2000,
            comments=400,
            shares=250,
            engagement_rate=0.88,
            performance_percentile=95.0,
        )

        patterns = extractor.extract_patterns(post_with_trajectory)

        # Should include emotion trajectory analysis
        assert "emotion_trajectory" in patterns
        trajectory = patterns["emotion_trajectory"]

        assert "arc_type" in trajectory
        assert trajectory["arc_type"] in [
            "rising",
            "falling",
            "roller_coaster",
            "steady",
        ]
        assert "emotion_progression" in trajectory
        assert len(trajectory["emotion_progression"]) > 1  # Multiple segments
