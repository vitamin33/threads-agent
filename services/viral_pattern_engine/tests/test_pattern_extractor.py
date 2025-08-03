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

        emotion = patterns["emotion_patterns"][0]
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
