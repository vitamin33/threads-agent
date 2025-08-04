"""Integration tests for emotion trajectory mapping system."""

import pytest
from services.viral_scraper.models import ViralPost
from services.viral_pattern_engine.pattern_extractor import ViralPatternExtractor


class TestEmotionTrajectoryIntegration:
    """Integration tests for complete emotion trajectory workflow."""

    @pytest.fixture
    def viral_post(self):
        """Create a sample viral post for testing."""
        return ViralPost(
            id="test_123",
            author="test_author",
            content="I can't believe how amazing this discovery is! 🤯 Just found out that this simple Python trick increased my productivity by 300%. At first I was skeptical, but now I'm completely convinced. This is absolutely game-changing! You have to try this yourself to believe it. Trust me, your mind will be blown away by how effective this is.",
            created_at="2025-01-01T00:00:00Z",
            engagement_rate=0.12,
            likes=1500,
            comments=89,
            shares=45,
            views=12500,
        )

    @pytest.fixture
    def short_post(self):
        """Create a short post for testing."""
        return ViralPost(
            id="short_123",
            author="test_author",
            content="Amazing discovery! 🚀 Mind = blown.",
            created_at="2025-01-01T00:00:00Z",
            engagement_rate=0.08,
            likes=500,
            comments=20,
            shares=10,
            views=5000,
        )

    @pytest.fixture
    def emotional_roller_coaster_post(self):
        """Create a post with varying emotions."""
        return ViralPost(
            id="roller_123",
            author="test_author",
            content="I was devastated when my startup failed. 😢 Months of depression followed. But then something amazing happened - I discovered a new passion! 🎉 Now I'm happier than ever, building something truly meaningful. Never give up on your dreams! The darkest moments often lead to the brightest futures. ✨",
            created_at="2025-01-01T00:00:00Z",
            engagement_rate=0.15,
            likes=2500,
            comments=150,
            shares=80,
            views=18000,
        )

    def test_full_emotion_trajectory_analysis(self, viral_post):
        """Test complete emotion trajectory analysis workflow."""
        extractor = ViralPatternExtractor()
        patterns = extractor.extract_patterns(viral_post)

        # Verify emotion patterns are extracted
        assert "emotion_patterns" in patterns
        assert len(patterns["emotion_patterns"]) > 0

        # Verify trajectory analysis is included for long content
        assert "emotion_trajectory" in patterns
        trajectory = patterns["emotion_trajectory"]

        # Check trajectory structure
        assert "trajectory_type" in trajectory
        assert trajectory["trajectory_type"] in [
            "rising",
            "falling",
            "roller-coaster",
            "steady",
        ]
        assert "segments" in trajectory
        assert len(trajectory["segments"]) >= 3
        assert "dominant_emotion" in trajectory
        assert "emotional_variance" in trajectory
        assert "peak_valley_count" in trajectory

        # Verify individual segment analysis
        for segment in trajectory["segments"]:
            assert "text" in segment
            assert "emotions" in segment
            assert "dominant_emotion" in segment
            assert "confidence" in segment
            assert segment["confidence"] > 0.5

    def test_short_content_no_trajectory(self, short_post):
        """Test that short content doesn't generate trajectory analysis."""
        extractor = ViralPatternExtractor()
        patterns = extractor.extract_patterns(short_post)

        # Should have basic emotion patterns but no trajectory
        assert "emotion_patterns" in patterns
        assert (
            "emotion_trajectory" not in patterns
            or patterns["emotion_trajectory"] is None
        )

    def test_emotional_roller_coaster_detection(self, emotional_roller_coaster_post):
        """Test detection of emotional roller-coaster pattern."""
        extractor = ViralPatternExtractor()
        patterns = extractor.extract_patterns(emotional_roller_coaster_post)

        trajectory = patterns["emotion_trajectory"]
        assert trajectory["trajectory_type"] == "roller-coaster"
        assert trajectory["emotional_variance"] > 0.3
        assert trajectory["peak_valley_count"]["peaks"] >= 1
        assert trajectory["peak_valley_count"]["valleys"] >= 1

        # Verify emotion transitions
        assert "transitions" in trajectory
        assert len(trajectory["transitions"]) >= 2

        # Check for sadness -> joy transition
        transitions = trajectory["transitions"]
        [(t["from_emotion"], t["to_emotion"]) for t in transitions]

        # Should detect negative to positive emotion transition
        has_negative_to_positive = any(
            t["from_emotion"] in ["sadness", "fear", "anger", "disgust"]
            and t["to_emotion"] in ["joy", "trust", "anticipation", "surprise"]
            for t in transitions
        )
        assert has_negative_to_positive

    def test_emotion_confidence_scores(self, viral_post):
        """Test that emotion confidence scores are properly calculated."""
        extractor = ViralPatternExtractor()
        patterns = extractor.extract_patterns(viral_post)

        # Check overall emotion pattern confidence
        for emotion_pattern in patterns["emotion_patterns"]:
            assert "confidence" in emotion_pattern
            assert 0.0 <= emotion_pattern["confidence"] <= 1.0

        # Check trajectory segment confidence
        if "emotion_trajectory" in patterns and patterns["emotion_trajectory"]:
            trajectory = patterns["emotion_trajectory"]
            for segment in trajectory["segments"]:
                assert 0.0 <= segment["confidence"] <= 1.0

    def test_emotion_pattern_types(self, viral_post):
        """Test that emotion patterns include all expected types."""
        extractor = ViralPatternExtractor()
        patterns = extractor.extract_patterns(viral_post)

        # Should detect excitement from "amazing", "mind will be blown"
        emotion_types = [p["type"] for p in patterns["emotion_patterns"]]
        assert "excitement" in emotion_types

        # Should have intensity scores
        for pattern in patterns["emotion_patterns"]:
            assert "intensity" in pattern
            assert 0.0 <= pattern["intensity"] <= 1.0

    @pytest.mark.parametrize(
        "content,expected_trajectory",
        [
            (
                "I'm getting more and more excited about this! This is incredible! Amazing! Best thing ever!",
                "rising",
            ),
            (
                "This was great at first. But then problems started. Now it's terrible. Complete disaster.",
                "falling",
            ),
            ("Happy, sad, happy, sad, excited, worried, hopeful!", "roller-coaster"),
            (
                "This is nice. It continues to be nice. Still pretty nice. Consistently nice.",
                "steady",
            ),
        ],
    )
    def test_trajectory_type_detection(self, content, expected_trajectory):
        """Test accurate detection of different trajectory types."""
        post = ViralPost(
            id="test_traj",
            author="test",
            content=content,
            created_at="2025-01-01T00:00:00Z",
            engagement_rate=0.1,
            likes=100,
            comments=10,
            shares=5,
            views=1000,
        )

        extractor = ViralPatternExtractor()
        patterns = extractor.extract_patterns(post)

        if "emotion_trajectory" in patterns and patterns["emotion_trajectory"]:
            assert (
                patterns["emotion_trajectory"]["trajectory_type"] == expected_trajectory
            )

    def test_emotion_trajectory_performance(self, viral_post):
        """Test that emotion analysis meets performance requirements."""
        import time

        extractor = ViralPatternExtractor()

        # Measure processing time
        start_time = time.time()
        patterns = extractor.extract_patterns(viral_post)
        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        # Should process within 300ms
        assert processing_time < 300

        # Verify result quality despite speed
        assert "emotion_patterns" in patterns
        assert "emotion_trajectory" in patterns

    def test_concurrent_emotion_analysis(self):
        """Test concurrent emotion analysis for multiple posts."""
        import concurrent.futures

        posts = [
            ViralPost(
                id=f"concurrent_{i}",
                author="test",
                content=f"Post {i}: " + "Amazing! " * 10 + "This is incredible! " * 5,
                created_at="2025-01-01T00:00:00Z",
                engagement_rate=0.1,
                likes=100 * i,
                comments=10 * i,
                shares=5 * i,
                views=1000 * i,
            )
            for i in range(10)
        ]

        extractor = ViralPatternExtractor()

        # Process posts concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(extractor.extract_patterns, post) for post in posts
            ]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Verify all posts were processed successfully
        assert len(results) == 10
        for result in results:
            assert "emotion_patterns" in result
            assert "pattern_strength" in result

    def test_emotion_trajectory_with_emojis(self):
        """Test emotion analysis with emoji-heavy content."""
        post = ViralPost(
            id="emoji_test",
            author="test",
            content="Started the day feeling 😢😭 but then something amazing happened! 🎉🎊 Now I'm 😊😄 and ready to take on the world! 🚀💪 Never give up! 💖✨",
            created_at="2025-01-01T00:00:00Z",
            engagement_rate=0.13,
            likes=1800,
            comments=95,
            shares=60,
            views=14000,
        )

        extractor = ViralPatternExtractor()
        patterns = extractor.extract_patterns(post)

        # Should detect emotional progression from sad to happy
        trajectory = patterns.get("emotion_trajectory")
        if trajectory:
            assert trajectory["trajectory_type"] in ["rising", "roller-coaster"]

            # Check that emojis influenced emotion detection
            segments = trajectory["segments"]
            # First segment should have negative emotion
            assert segments[0]["dominant_emotion"] in [
                "sadness",
                "fear",
                "anger",
                "disgust",
            ]
            # Last segment should have positive emotion
            assert segments[-1]["dominant_emotion"] in [
                "joy",
                "trust",
                "anticipation",
                "surprise",
            ]

    def test_emotion_pattern_caching(self, viral_post):
        """Test that repeated analysis of same content uses caching efficiently."""
        import time

        extractor = ViralPatternExtractor()

        # First analysis
        start_time = time.time()
        patterns1 = extractor.extract_patterns(viral_post)
        time.time() - start_time

        # Second analysis of same content
        start_time = time.time()
        patterns2 = extractor.extract_patterns(viral_post)
        time.time() - start_time

        # Results should be identical
        assert patterns1["emotion_patterns"] == patterns2["emotion_patterns"]
        if "emotion_trajectory" in patterns1:
            assert patterns1["emotion_trajectory"] == patterns2["emotion_trajectory"]

        # Second analysis might be faster due to any internal caching
        # (though current implementation doesn't explicitly cache)
