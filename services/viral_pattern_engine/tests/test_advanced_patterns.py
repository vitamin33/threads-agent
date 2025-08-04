"""Tests for advanced viral pattern detection."""

import pytest
from datetime import datetime
from services.viral_scraper.models import ViralPost
from services.viral_pattern_engine.pattern_extractor import ViralPatternExtractor


class TestAdvancedPatterns:
    """Test cases for advanced pattern detection features."""

    @pytest.fixture
    def extractor(self):
        """Create pattern extractor instance."""
        return ViralPatternExtractor()

    @pytest.fixture
    def post_with_numbers(self):
        """Post with specific numbers/statistics."""
        return ViralPost(
            content="This AI tool increased my productivity by 300% in just 2 weeks! Here are the exact numbers...",
            account_id="test_user",
            post_url="https://threads.net/test/numbers",
            timestamp=datetime.now(),
            likes=3000,
            comments=500,
            shares=250,
            engagement_rate=0.88,
            performance_percentile=97.0,
        )

    @pytest.fixture
    def post_with_story_hook(self):
        """Post using story-based hook."""
        return ViralPost(
            content="3 months ago I was struggling with data analysis. Today I built an AI system that processes 10TB in minutes. Here's how...",
            account_id="test_user",
            post_url="https://threads.net/test/story",
            timestamp=datetime.now(),
            likes=2500,
            comments=400,
            shares=180,
            engagement_rate=0.91,
            performance_percentile=96.5,
        )

    @pytest.fixture
    def post_with_curiosity_gap(self):
        """Post with curiosity gap pattern."""
        return ViralPost(
            content="The secret that top AI engineers don't want you to know about prompt engineering (thread)",
            account_id="test_user",
            post_url="https://threads.net/test/curiosity",
            timestamp=datetime.now(),
            likes=4000,
            comments=600,
            shares=300,
            engagement_rate=0.94,
            performance_percentile=99.2,
        )

    def test_extract_statistical_pattern(self, extractor, post_with_numbers):
        """Test extraction of statistical/number-based patterns."""
        patterns = extractor.extract_patterns(post_with_numbers)

        assert "hook_patterns" in patterns

        # Should detect numerical pattern
        numerical_patterns = [
            p for p in patterns["hook_patterns"] if p["type"] == "statistical"
        ]
        assert len(numerical_patterns) > 0

        pattern = numerical_patterns[0]
        assert pattern["confidence"] > 0.6
        assert (
            "{percentage}" in pattern["template"] or "{number}" in pattern["template"]
        )

    def test_extract_story_transformation_pattern(
        self, extractor, post_with_story_hook
    ):
        """Test extraction of before/after transformation story patterns."""
        patterns = extractor.extract_patterns(post_with_story_hook)

        assert "hook_patterns" in patterns

        # Should detect transformation story pattern
        story_patterns = [
            p for p in patterns["hook_patterns"] if p["type"] == "transformation_story"
        ]
        assert len(story_patterns) > 0

        pattern = story_patterns[0]
        assert pattern["confidence"] > 0.7
        assert "before_state" in pattern
        assert "after_state" in pattern

    def test_extract_curiosity_gap_pattern(self, extractor, post_with_curiosity_gap):
        """Test extraction of curiosity gap patterns."""
        patterns = extractor.extract_patterns(post_with_curiosity_gap)

        assert "hook_patterns" in patterns

        # Should detect curiosity gap pattern
        curiosity_patterns = [
            p for p in patterns["hook_patterns"] if p["type"] == "curiosity_gap"
        ]
        assert len(curiosity_patterns) > 0

        pattern = curiosity_patterns[0]
        assert pattern["confidence"] > 0.8
        assert (
            "secret" in pattern["triggers"]
            or "don't want you to know" in pattern["triggers"]
        )

    def test_content_structure_analysis(self, extractor, post_with_story_hook):
        """Test content structure analysis."""
        patterns = extractor.extract_patterns(post_with_story_hook)

        assert "structure_patterns" in patterns
        assert len(patterns["structure_patterns"]) > 0

        structure = patterns["structure_patterns"][0]
        assert "length_category" in structure  # short/medium/long
        assert "has_thread_indicator" in structure  # (thread), 🧵, etc.
        assert "sentence_count" in structure
        assert "reading_time_seconds" in structure

    def test_engagement_correlation_scoring(self, extractor, post_with_curiosity_gap):
        """Test engagement correlation with pattern strength."""
        patterns = extractor.extract_patterns(post_with_curiosity_gap)

        # High-performing post with strong patterns should have high correlation score
        assert patterns["engagement_score"] > 0.9

        # Should have correlation metadata
        assert "pattern_strength" in patterns
        assert patterns["pattern_strength"] >= 0.8  # Strong patterns detected

    def test_multiple_pattern_detection(self, extractor):
        """Test detection of multiple patterns in single post."""
        multi_pattern_post = ViralPost(
            content="🚨 BREAKING: Just discovered this incredible AI secret that increased my income by 400%! The results will shock you (thread) 🧵",
            account_id="test_user",
            post_url="https://threads.net/test/multi",
            timestamp=datetime.now(),
            likes=5000,
            comments=800,
            shares=400,
            engagement_rate=0.96,
            performance_percentile=99.8,
        )

        patterns = extractor.extract_patterns(multi_pattern_post)

        # Should detect multiple hook patterns
        assert len(patterns["hook_patterns"]) >= 2

        # Should detect multiple emotion patterns
        assert len(patterns["emotion_patterns"]) >= 1

        # Should have high pattern strength due to multiple patterns
        assert patterns["pattern_strength"] >= 0.9
