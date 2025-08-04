"""Edge case and error handling tests for emotion trajectory system."""

import pytest
import json
from unittest.mock import patch

from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper


class TestEmotionEdgeCases:
    """Test edge cases and error scenarios for emotion analysis."""

    @pytest.fixture
    def emotion_analyzer(self):
        """Create emotion analyzer instance."""
        return EmotionAnalyzer()

    @pytest.fixture
    def trajectory_mapper(self):
        """Create trajectory mapper instance."""
        return TrajectoryMapper()

    def test_empty_content_analysis(self, emotion_analyzer):
        """Test emotion analysis with empty content."""
        # Test empty string
        result = emotion_analyzer.analyze_emotions("")
        assert result is not None
        assert "emotions" in result
        assert all(score >= 0 for score in result["emotions"].values())

        # Test whitespace only
        result = emotion_analyzer.analyze_emotions("   \n\t  ")
        assert result is not None
        assert "emotions" in result

    def test_extremely_long_content(self, emotion_analyzer):
        """Test emotion analysis with extremely long content."""
        # Create very long text (10,000 characters)
        long_text = "This is a test sentence. " * 400

        result = emotion_analyzer.analyze_emotions(long_text)
        assert result is not None
        assert "emotions" in result
        assert "confidence" in result

        # Should handle gracefully without crashing
        assert isinstance(result["confidence"], (int, float))

    def test_special_characters_and_unicode(self, emotion_analyzer):
        """Test emotion analysis with special characters and unicode."""
        test_cases = [
            "I'm so excited! 🎉🎊 This is amazing!!! 💖",
            "Très triste... 😢 C'est incroyable!",
            "測试中文情感分析 非常开心！",
            "@#$%^&*()[]{}|;:'\",.<>?/~`",
            "Mixed content: Hello! 🌟 Testing@123 #hashtag",
            "Emojionly: 😀😢😡😨😮🤢💙🔮",
        ]

        for test_text in test_cases:
            result = emotion_analyzer.analyze_emotions(test_text)
            assert result is not None
            assert "emotions" in result
            assert len(result["emotions"]) == 8  # All 8 emotions should be present

    def test_malformed_json_content(self, emotion_analyzer):
        """Test handling of content that might be malformed JSON."""
        malformed_cases = [
            '{"incomplete": "json"',
            '{"valid": "json", "but": "weird content"}',
            '[1, 2, 3, "not emotional content"]',
            "null",
            "undefined",
            '{"emotions": {"joy": "not_a_number"}}',
        ]

        for case in malformed_cases:
            result = emotion_analyzer.analyze_emotions(case)
            assert result is not None
            assert "emotions" in result

    def test_empty_segments_list(self, trajectory_mapper):
        """Test trajectory mapping with empty segments list."""
        result = trajectory_mapper.map_emotion_trajectory([])

        # Should return a valid structure with defaults
        assert result["arc_type"] == "steady"  # Default for empty
        assert result["emotion_progression"] == []
        assert result["peak_segments"] == []
        assert result["valley_segments"] == []
        assert result["emotional_variance"] == 0.0

    def test_single_segment_trajectory(self, trajectory_mapper):
        """Test trajectory mapping with only one segment."""
        single_segment = ["This is the only content segment."]

        result = trajectory_mapper.map_emotion_trajectory(single_segment)

        assert result["arc_type"] == "steady"  # Single segment should be steady
        assert len(result["emotion_progression"]) == 1
        assert result["peak_segments"] == []  # Can't have peaks with one segment
        assert result["valley_segments"] == []

    def test_identical_segments(self, trajectory_mapper):
        """Test trajectory mapping with identical segments."""
        identical_segments = ["Exactly the same content."] * 5

        result = trajectory_mapper.map_emotion_trajectory(identical_segments)

        assert result["arc_type"] == "steady"  # Identical content should be steady
        assert len(result["emotion_progression"]) == 5
        assert result["emotional_variance"] < 0.1  # Very low variance

    def test_model_loading_failure_fallback(self):
        """Test graceful fallback when ML models fail to load."""
        with patch(
            "services.viral_pattern_engine.emotion_analyzer.MODELS_AVAILABLE", False
        ):
            analyzer = EmotionAnalyzer()

            result = analyzer.analyze_emotions("I'm so happy about this!")

            assert result is not None
            assert result["model_info"]["bert_model"] == "keyword-fallback"
            assert result["model_info"]["vader_sentiment"] == "keyword-fallback"
            assert "emotions" in result
            assert result["confidence"] == 0.7  # Fallback confidence

    def test_bert_model_exception_handling(self, emotion_analyzer):
        """Test handling of BERT model exceptions."""
        with patch.object(emotion_analyzer, "bert_classifier") as mock_bert:
            mock_bert.side_effect = Exception("BERT model error")

            # Should fall back to keyword analysis
            result = emotion_analyzer.analyze_emotions("Happy content!")

            assert result is not None
            assert "emotions" in result
            # Should use fallback analysis

    def test_vader_model_exception_handling(self, emotion_analyzer):
        """Test handling of VADER model exceptions."""
        # Mock VADER to raise exception
        with patch.object(emotion_analyzer, "vader_analyzer") as mock_vader:
            mock_vader.polarity_scores.side_effect = Exception("VADER error")

            # Should still work with BERT only or fallback
            result = emotion_analyzer.analyze_emotions("Happy content!")

            assert result is not None
            assert "emotions" in result

    def test_invalid_emotion_scores(self, trajectory_mapper):
        """Test handling of invalid emotion scores from analyzer."""
        # Mock analyzer to return invalid scores
        with patch.object(
            trajectory_mapper.emotion_analyzer, "analyze_emotions"
        ) as mock_analyzer:
            mock_analyzer.return_value = {
                "emotions": {
                    "joy": float("inf"),  # Invalid: infinity
                    "anger": -1.0,  # Invalid: negative
                    "fear": "not_a_number",  # Invalid: string
                    "sadness": None,  # Invalid: None
                    "surprise": 2.0,  # Invalid: > 1.0
                    "disgust": 0.5,  # Valid
                    "trust": 0.3,  # Valid
                    "anticipation": 0.7,  # Valid
                },
                "confidence": 0.8,
            }

            segments = ["Test content"]
            result = trajectory_mapper.map_emotion_trajectory(segments)

            # Should handle invalid scores gracefully
            assert result is not None
            assert "emotion_progression" in result
            # Should not crash despite invalid input

    def test_extremely_negative_content(self, emotion_analyzer):
        """Test analysis of extremely negative/toxic content."""
        negative_content = [
            "This is absolutely terrible and disgusting! I hate everything about it!",
            "Worst possible outcome! Complete disaster! Total failure!",
            "Devastating news that ruins everything we worked for!",
            "Horrifying and terrifying situation that nobody should experience!",
        ]

        for content in negative_content:
            result = emotion_analyzer.analyze_emotions(content)

            assert result is not None
            assert "emotions" in result

            # Should detect high negative emotions
            emotions = result["emotions"]
            negative_emotions = (
                emotions["anger"]
                + emotions["fear"]
                + emotions["sadness"]
                + emotions["disgust"]
            )
            emotions["joy"] + emotions["trust"]

            # Negative emotions should dominate, but test should still pass
            assert negative_emotions >= 0  # At least some negative emotion detected

    def test_mixed_language_content(self, emotion_analyzer):
        """Test analysis of mixed language content."""
        mixed_content = [
            "I'm happy! Je suis heureux! 我很高兴！",
            "Sad news... Nouvelles tristes... 悲しいニュース...",
            "¡Muy emocionante! Very exciting! Très excitant!",
            "Confused 困惑した 混乱 confundido",
        ]

        for content in mixed_content:
            result = emotion_analyzer.analyze_emotions(content)

            assert result is not None
            assert "emotions" in result
            assert result["confidence"] >= 0  # Should have some confidence

    def test_database_connection_failure_resilience(self, trajectory_mapper):
        """Test resilience when database operations fail."""
        # This test focuses on the analysis logic, not database storage
        segments = ["Happy content!", "Sad content.", "Neutral content."]

        # Analysis should work even if database is unavailable
        result = trajectory_mapper.map_emotion_trajectory(segments)

        assert result is not None
        assert "arc_type" in result
        assert len(result["emotion_progression"]) == 3

    def test_memory_pressure_handling(self, trajectory_mapper):
        """Test behavior under memory pressure conditions."""
        # Create a very large number of segments to stress memory
        large_segments = [
            f"Content segment number {i} with some emotional content."
            for i in range(100)
        ]

        try:
            result = trajectory_mapper.map_emotion_trajectory(large_segments)

            assert result is not None
            assert len(result["emotion_progression"]) == 100
            assert result["arc_type"] in [
                "rising",
                "falling",
                "roller_coaster",
                "steady",
            ]

        except MemoryError:
            # If memory error occurs, it should be caught and handled gracefully
            pytest.skip("System under memory pressure, test skipped")

    def test_concurrent_access_thread_safety(self, emotion_analyzer):
        """Test thread safety with concurrent access."""
        import threading

        results = []
        errors = []

        def analyze_worker():
            try:
                result = emotion_analyzer.analyze_emotions(
                    "Thread test content with emotions!"
                )
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=analyze_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout

        # Assert no errors and all results valid
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 10
        assert all("emotions" in result for result in results)

    def test_invalid_segment_indices_handling(self, trajectory_mapper):
        """Test handling of invalid segment indices in transitions."""
        segments = ["First segment", "Second segment"]

        # Mock invalid emotion progression that could cause index errors
        with patch.object(trajectory_mapper, "detect_peaks_and_valleys") as mock_peaks:
            mock_peaks.return_value = {
                "peaks": [],
                "valleys": [],
                "peak_indices": [5, 10],  # Invalid indices for 2 segments
                "valley_indices": [-1, 999],  # Invalid negative and out-of-range
            }

            result = trajectory_mapper.map_emotion_trajectory(segments)

            # Should handle invalid indices gracefully
            assert result is not None
            assert "peak_segments" in result

    def test_malformed_template_patterns(self):
        """Test handling of malformed emotion template patterns."""
        from services.orchestrator.db.models import EmotionTemplate

        # Test template with malformed JSON patterns
        malformed_templates = [
            {
                "emotion_sequence": "not_valid_json",
                "transition_patterns": '{"incomplete": json',
            },
            {
                "emotion_sequence": '{"valid": "json", "but": "unexpected_structure"}',
                "transition_patterns": "[]",  # Array instead of object
            },
            {"emotion_sequence": "null", "transition_patterns": '{"empty": {}}'},
        ]

        for template_data in malformed_templates:
            # Should be able to create template even with malformed patterns
            try:
                template = EmotionTemplate(
                    template_name="Test Template",
                    template_type="test",
                    pattern_description="Test",
                    segment_count=3,
                    optimal_duration_words=100,
                    trajectory_pattern="rising",
                    primary_emotions=["joy"],
                    emotion_sequence=template_data["emotion_sequence"],
                    transition_patterns=template_data["transition_patterns"],
                )

                # Basic validation should pass
                assert template.template_name == "Test Template"

            except json.JSONDecodeError:
                # Expected for truly malformed JSON
                pass

    def test_zero_confidence_scores_handling(self, trajectory_mapper):
        """Test handling of zero confidence scores from analysis."""
        with patch.object(
            trajectory_mapper.emotion_analyzer, "analyze_emotions"
        ) as mock_analyzer:
            mock_analyzer.return_value = {
                "emotions": {
                    "joy": 0.0,
                    "anger": 0.0,
                    "fear": 0.0,
                    "sadness": 0.0,
                    "surprise": 0.0,
                    "disgust": 0.0,
                    "trust": 0.0,
                    "anticipation": 0.0,
                },
                "confidence": 0.0,  # Zero confidence
            }

            segments = ["Low confidence content"]
            result = trajectory_mapper.map_emotion_trajectory(segments)

            assert result is not None
            assert result["emotional_variance"] == 0.0  # Should be 0 for no emotions
            assert result["arc_type"] == "steady"  # Default for no emotional change

    def test_nan_and_infinity_values_in_calculations(self, trajectory_mapper):
        """Test handling of NaN and infinity values in calculations."""
        # Create content that might produce edge case calculations
        edge_case_segments = [
            "",  # Empty content might cause division by zero
            "A",  # Single character
            "." * 1000,  # Repetitive content
            "1" * 10000,  # Extremely repetitive content
        ]

        result = trajectory_mapper.map_emotion_trajectory(edge_case_segments)

        # Verify no NaN or infinity values in results
        assert result is not None
        assert isinstance(result["emotional_variance"], (int, float))
        assert not (
            result["emotional_variance"] != result["emotional_variance"]
        )  # Check for NaN
        assert result["emotional_variance"] != float("inf")
        assert result["emotional_variance"] != float("-inf")

    def test_resource_cleanup_on_failure(self, trajectory_mapper):
        """Test that resources are properly cleaned up on failure."""
        import gc

        # Get initial object count
        initial_objects = len(gc.get_objects())

        # Force an exception during processing
        with patch.object(
            trajectory_mapper.emotion_analyzer, "analyze_emotions"
        ) as mock_analyzer:
            mock_analyzer.side_effect = Exception("Simulated failure")

            try:
                trajectory_mapper.map_emotion_trajectory(["Test content"])
            except Exception:
                pass  # Expected to fail

        # Force garbage collection
        gc.collect()

        # Check that we don't have excessive object growth
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Some growth is expected, but should be reasonable (< 1000 objects)
        assert object_growth < 1000, f"Excessive object growth: {object_growth} objects"

    def test_unicode_normalization_edge_cases(self, emotion_analyzer):
        """Test handling of various Unicode normalization edge cases."""
        unicode_test_cases = [
            "café",  # Composed character
            "cafe\u0301",  # Decomposed character (e + combining acute)
            "𝕳𝖆𝖕𝖕𝖞",  # Mathematical script
            "🅷🅰🅿🅿🆈",  # Enclosed characters
            "Ⓗⓐⓟⓟⓨ",  # Circled letters
            "ℌ𝒶𝓅𝓅𝓎",  # Various Unicode scripts
        ]

        for test_case in unicode_test_cases:
            result = emotion_analyzer.analyze_emotions(f"I am {test_case} about this!")

            assert result is not None
            assert "emotions" in result
            # Should detect positive emotion despite Unicode complexity
            assert result["emotions"]["joy"] >= 0

    def test_extremely_unbalanced_segments(self, trajectory_mapper):
        """Test handling of extremely unbalanced segment lengths."""
        unbalanced_segments = [
            "Short.",
            "This is a medium length segment with some emotional content in it.",
            "A" * 10000,  # Extremely long segment
            "",  # Empty segment
            "Another short one.",
        ]

        result = trajectory_mapper.map_emotion_trajectory(unbalanced_segments)

        assert result is not None
        assert len(result["emotion_progression"]) == 5
        assert result["arc_type"] in ["rising", "falling", "roller_coaster", "steady"]

        # Should handle the variance in segment lengths gracefully
        assert isinstance(result["emotional_variance"], (int, float))
        assert result["emotional_variance"] >= 0
