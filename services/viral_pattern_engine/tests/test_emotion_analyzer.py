"""Tests for advanced emotion analysis using multi-model approach."""

import pytest
from unittest.mock import patch
from services.viral_pattern_engine.emotion_analyzer import (
    EmotionAnalyzer,
)


class TestEmotionAnalyzer:
    """Test cases for multi-model emotion detection."""

    @pytest.fixture
    def emotion_analyzer(self):
        """Create emotion analyzer instance."""
        return EmotionAnalyzer()

    def test_analyze_emotions_returns_8_distinct_emotions(self, emotion_analyzer):
        """Test that emotion analyzer detects 8+ distinct emotions with confidence scores."""
        text = "I'm so excited and happy about this amazing discovery! It's incredible!"

        result = emotion_analyzer.analyze_emotions(text)

        # Should return a dictionary with emotion categories
        assert isinstance(result, dict)
        assert "emotions" in result

        emotions = result["emotions"]

        # Must detect at least 8 distinct emotions
        expected_emotions = [
            "joy",
            "anger",
            "fear",
            "sadness",
            "surprise",
            "disgust",
            "trust",
            "anticipation",
        ]
        for emotion in expected_emotions:
            assert emotion in emotions, f"Missing emotion: {emotion}"

        # Each emotion should have a confidence score between 0 and 1
        for emotion, score in emotions.items():
            assert 0.0 <= score <= 1.0, (
                f"Invalid confidence score for {emotion}: {score}"
            )

        # Primary emotion should be joy/excitement for this text
        assert emotions["joy"] > 0.7, "Expected high joy score for excited text"

    def test_analyze_emotions_sad_text_detects_sadness(self, emotion_analyzer):
        """Test that sad text is correctly identified with high sadness score."""
        text = "I'm so devastated and heartbroken. This is the worst day of my life."

        result = emotion_analyzer.analyze_emotions(text)
        emotions = result["emotions"]

        # Sadness should be the dominant emotion
        assert emotions["sadness"] > 0.7, "Expected high sadness score for sad text"
        # Joy should be low
        assert emotions["joy"] < 0.3, "Expected low joy score for sad text"

    def test_analyze_emotions_angry_text_detects_anger(self, emotion_analyzer):
        """Test that angry text is correctly identified with high anger score."""
        text = (
            "I'm furious and outraged! This is absolutely unacceptable and infuriating!"
        )

        result = emotion_analyzer.analyze_emotions(text)
        emotions = result["emotions"]

        # Anger should be the dominant emotion
        assert emotions["anger"] > 0.7, "Expected high anger score for angry text"
        # Trust should be low
        assert emotions["trust"] < 0.3, "Expected low trust score for angry text"

    def test_analyze_emotions_returns_bert_model_metadata(self, emotion_analyzer):
        """Test that the analyzer returns BERT model information and confidence scores."""
        text = "This is amazing and wonderful!"

        result = emotion_analyzer.analyze_emotions(text)

        # Should include model metadata
        assert "model_info" in result
        assert "bert_model" in result["model_info"]
        assert "vader_sentiment" in result["model_info"]

        # Should include overall confidence
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_analyze_emotions_supports_ensemble_weighting(self, emotion_analyzer):
        """Test that BERT and VADER results are combined with proper weighting."""
        text = "I love this so much but I'm also worried about the future."

        result = emotion_analyzer.analyze_emotions(text)

        # Should contain ensemble information
        assert "ensemble_info" in result
        assert "bert_weight" in result["ensemble_info"]
        assert "vader_weight" in result["ensemble_info"]

        # Weights should sum to 1.0
        bert_weight = result["ensemble_info"]["bert_weight"]
        vader_weight = result["ensemble_info"]["vader_weight"]
        assert abs((bert_weight + vader_weight) - 1.0) < 0.01

    def test_analyze_emotions_performance_requirement(self, emotion_analyzer):
        """Test that emotion analysis completes within performance requirements."""
        import time

        text = (
            "This is a longer piece of text that contains multiple emotions and sentiments. "
            "I'm excited about some parts but worried about others. It's amazing how complex "
            "human emotions can be in a single piece of content."
        )

        start_time = time.time()
        result = emotion_analyzer.analyze_emotions(text)
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Should complete within 300ms requirement
        assert processing_time < 300, (
            f"Processing took {processing_time}ms, expected <300ms"
        )

        # Should still return valid results
        assert "emotions" in result
        assert len(result["emotions"]) == 8

    def test_analyze_emotions_with_neutral_content(self, emotion_analyzer):
        """Test emotion analysis with neutral, non-emotional content."""
        text = "This is a factual statement about the weather today. It is currently 72 degrees."

        result = emotion_analyzer.analyze_emotions(text)
        emotions = result["emotions"]

        # No emotion should be extremely high for neutral content
        for emotion, score in emotions.items():
            assert score <= 0.6, (
                f"Neutral content should not have high {emotion} score: {score}"
            )

        # Trust might be slightly higher for factual content
        assert emotions["trust"] >= emotions["anger"]
        assert emotions["trust"] >= emotions["fear"]

    def test_analyze_emotions_mixed_emotions(self, emotion_analyzer):
        """Test analysis of content with mixed emotional signals."""
        text = (
            "I'm excited about the opportunity but scared about the challenges ahead. "
            "It's surprising how something can be both thrilling and terrifying."
        )

        result = emotion_analyzer.analyze_emotions(text)
        emotions = result["emotions"]

        # Should detect multiple emotions
        high_emotions = [emotion for emotion, score in emotions.items() if score > 0.4]
        assert len(high_emotions) >= 2, (
            "Mixed emotional content should trigger multiple emotions"
        )

        # Should detect both positive and negative emotions
        positive_sum = emotions["joy"] + emotions["trust"] + emotions["anticipation"]
        negative_sum = emotions["fear"] + emotions["sadness"] + emotions["anger"]

        assert positive_sum > 0.3, "Should detect positive emotions"
        assert negative_sum > 0.3, "Should detect negative emotions"

    def test_analyze_emotions_edge_case_content(self, emotion_analyzer):
        """Test emotion analysis with edge case content types."""
        edge_cases = [
            ("", "empty string"),
            ("   \n\t  ", "whitespace only"),
            ("!!!", "punctuation only"),
            ("123 456 789", "numbers only"),
            ("aaaaaaaaaaaa", "repeated characters"),
            ("🎉🎊💖😢😡", "emoji only"),
        ]

        for text, description in edge_cases:
            result = emotion_analyzer.analyze_emotions(text)

            # Should handle gracefully without crashing
            assert result is not None, f"Failed to handle {description}"
            assert "emotions" in result, f"Missing emotions for {description}"
            assert len(result["emotions"]) == 8, (
                f"Wrong emotion count for {description}"
            )

            # All scores should be valid
            for emotion, score in result["emotions"].items():
                assert 0.0 <= score <= 1.0, (
                    f"Invalid score for {emotion} in {description}: {score}"
                )

    def test_analyze_emotions_with_unicode_content(self, emotion_analyzer):
        """Test emotion analysis with various Unicode characters."""
        unicode_texts = [
            "Je suis très heureux aujourd'hui! 🌟",  # French with emoji
            "我很高兴！这真是太棒了！",  # Chinese
            "Я очень рад этому открытию!",  # Russian
            "¡Estoy muy emocionado por esto!",  # Spanish
            "これは素晴らしいニュースです！",  # Japanese
        ]

        for text in unicode_texts:
            result = emotion_analyzer.analyze_emotions(text)

            assert result is not None
            assert "emotions" in result
            assert result["confidence"] > 0.0

            # Should detect some positive emotion in happy texts
            positive_emotions = result["emotions"]["joy"] + result["emotions"]["trust"]
            assert positive_emotions > 0.2, f"Should detect positive emotion in: {text}"

    def test_analyze_emotions_model_fallback_scenario(self, emotion_analyzer):
        """Test fallback to keyword analysis when models fail."""
        test_text = "I'm absolutely thrilled and excited about this amazing discovery!"

        # Test with models disabled
        with patch.object(emotion_analyzer, "models_loaded", False):
            result = emotion_analyzer.analyze_emotions(test_text)

            # Should use fallback analysis
            assert result["model_info"]["bert_model"] == "keyword-fallback"
            assert result["model_info"]["vader_sentiment"] == "keyword-fallback"
            assert result["confidence"] == 0.7  # Fallback confidence

            # Should still detect joy from keywords
            assert result["emotions"]["joy"] > 0.6

    def test_bert_emotion_mapping_accuracy(self, emotion_analyzer):
        """Test accuracy of BERT emotion label mapping."""
        if not emotion_analyzer.models_loaded:
            pytest.skip("Models not loaded, testing fallback scenario")

        # Mock BERT results with known labels
        mock_bert_results = [
            {"label": "joy", "score": 0.8},
            {"label": "sadness", "score": 0.1},
            {"label": "love", "score": 0.6},  # Should map to joy + trust
            {"label": "fear", "score": 0.3},
            {"label": "unknown_label", "score": 0.2},  # Should be ignored
        ]

        mapped_emotions = emotion_analyzer._convert_bert_to_8_emotions(
            mock_bert_results
        )

        # Verify mapping
        assert mapped_emotions["joy"] > 0.8  # Original + love contribution
        assert mapped_emotions["trust"] > 0.1  # Love contribution
        assert mapped_emotions["sadness"] == 0.1
        assert mapped_emotions["fear"] == 0.3

        # All 8 emotions should be present
        expected_emotions = {
            "joy",
            "anger",
            "fear",
            "sadness",
            "surprise",
            "disgust",
            "trust",
            "anticipation",
        }
        assert set(mapped_emotions.keys()) == expected_emotions

    def test_vader_emotion_mapping_accuracy(self, emotion_analyzer):
        """Test accuracy of VADER sentiment to emotion mapping."""
        if not emotion_analyzer.models_loaded:
            pytest.skip("Models not loaded")

        test_cases = [
            {
                "vader_scores": {"compound": 0.8, "pos": 0.9, "neu": 0.1, "neg": 0.0},
                "expected_high": ["joy", "trust"],
                "expected_low": ["sadness", "anger"],
            },
            {
                "vader_scores": {"compound": -0.8, "pos": 0.0, "neu": 0.1, "neg": 0.9},
                "expected_high": ["sadness", "anger"],
                "expected_low": ["joy", "trust"],
            },
            {
                "vader_scores": {"compound": 0.9, "pos": 0.95, "neu": 0.05, "neg": 0.0},
                "expected_high": ["joy", "trust", "anticipation"],
                "expected_surprise": True,  # High compound should trigger surprise
            },
        ]

        for case in test_cases:
            mapped_emotions = emotion_analyzer._convert_vader_to_emotions(
                case["vader_scores"]
            )

            if "expected_high" in case:
                for emotion in case["expected_high"]:
                    assert mapped_emotions[emotion] > 0.3, (
                        f"{emotion} should be high for case {case}"
                    )

            if "expected_low" in case:
                for emotion in case["expected_low"]:
                    assert mapped_emotions[emotion] < 0.3, (
                        f"{emotion} should be low for case {case}"
                    )

            if case.get("expected_surprise"):
                assert mapped_emotions["surprise"] > 0.25, (
                    "High compound score should trigger surprise"
                )

    def test_ensemble_weighting_calculation(self, emotion_analyzer):
        """Test ensemble weighting between BERT and VADER results."""
        if not emotion_analyzer.models_loaded:
            pytest.skip("Models not loaded")

        bert_emotions = {
            "joy": 0.9,
            "anger": 0.1,
            "fear": 0.1,
            "sadness": 0.1,
            "surprise": 0.2,
            "disgust": 0.1,
            "trust": 0.8,
            "anticipation": 0.3,
        }

        vader_emotions = {
            "joy": 0.3,
            "anger": 0.7,
            "fear": 0.4,
            "sadness": 0.6,
            "surprise": 0.2,
            "disgust": 0.3,
            "trust": 0.2,
            "anticipation": 0.1,
        }

        # Test with default weights (0.7 BERT, 0.3 VADER)
        final_emotions = emotion_analyzer._ensemble_emotions(
            bert_emotions, vader_emotions
        )

        # Joy should be dominated by BERT (0.9 * 0.7 + 0.3 * 0.3 = 0.72)
        expected_joy = 0.9 * 0.7 + 0.3 * 0.3
        assert abs(final_emotions["joy"] - expected_joy) < 0.01

        # Anger should be influenced by VADER (0.1 * 0.7 + 0.7 * 0.3 = 0.28)
        expected_anger = 0.1 * 0.7 + 0.7 * 0.3
        assert abs(final_emotions["anger"] - expected_anger) < 0.01

        # All values should be clamped to [0, 1]
        for emotion, score in final_emotions.items():
            assert 0.0 <= score <= 1.0, (
                f"Score {score} for {emotion} not in valid range"
            )

    def test_confidence_calculation_logic(self, emotion_analyzer):
        """Test confidence score calculation logic."""
        if not emotion_analyzer.models_loaded:
            pytest.skip("Models not loaded")

        # High confidence scenario
        high_bert = [{"label": "joy", "score": 0.95}]
        high_vader = {"compound": 0.9, "pos": 0.9, "neu": 0.1, "neg": 0.0}

        high_confidence = emotion_analyzer._calculate_confidence(high_bert, high_vader)
        assert high_confidence > 0.85, (
            f"Expected high confidence, got {high_confidence}"
        )

        # Low confidence scenario
        low_bert = [{"label": "joy", "score": 0.4}]
        low_vader = {"compound": 0.1, "pos": 0.3, "neu": 0.7, "neg": 0.0}

        low_confidence = emotion_analyzer._calculate_confidence(low_bert, low_vader)
        assert low_confidence < 0.6, f"Expected low confidence, got {low_confidence}"

        # Confidence should be within valid range
        assert 0.0 <= high_confidence <= 1.0
        assert 0.0 <= low_confidence <= 1.0

    def test_analyze_emotions_consistency(self, emotion_analyzer):
        """Test consistency of emotion analysis across multiple runs."""
        text = "I'm really excited about this new opportunity!"

        results = []
        for _ in range(5):
            result = emotion_analyzer.analyze_emotions(text)
            results.append(result)

        # Results should be consistent
        for i in range(1, len(results)):
            # Dominant emotion should be the same
            dominant_1 = max(results[0]["emotions"], key=results[0]["emotions"].get)
            dominant_i = max(results[i]["emotions"], key=results[i]["emotions"].get)

            assert dominant_1 == dominant_i, (
                f"Inconsistent dominant emotion: {dominant_1} vs {dominant_i}"
            )

            # Confidence should be similar (within 10%)
            conf_diff = abs(results[0]["confidence"] - results[i]["confidence"])
            assert conf_diff < 0.1, f"Confidence varies too much: {conf_diff}"

    def test_extreme_emotion_content_handling(self, emotion_analyzer):
        """Test handling of extremely emotional content."""
        extreme_cases = [
            {
                "text": "ABSOLUTELY AMAZING INCREDIBLE FANTASTIC WONDERFUL PERFECT BRILLIANT!!!",
                "expected_emotion": "joy",
                "min_score": 0.8,
            },
            {
                "text": "TERRIBLE AWFUL HORRIBLE DISGUSTING WORST NIGHTMARE DISASTER!!!",
                "expected_emotion": "disgust",
                "min_score": 0.6,
            },
            {
                "text": "FURIOUS ENRAGED OUTRAGED LIVID ANGRY INFURIATING UNACCEPTABLE!!!",
                "expected_emotion": "anger",
                "min_score": 0.7,
            },
            {
                "text": "TERRIFIED PETRIFIED HORRIFIED SCARED FRIGHTENED PANICKED!!!",
                "expected_emotion": "fear",
                "min_score": 0.6,
            },
        ]

        for case in extreme_cases:
            result = emotion_analyzer.analyze_emotions(case["text"])
            emotions = result["emotions"]

            # Should detect the expected extreme emotion
            actual_score = emotions[case["expected_emotion"]]
            assert actual_score >= case["min_score"], (
                f"Expected {case['expected_emotion']} >= {case['min_score']}, got {actual_score}"
            )

    def test_model_error_recovery(self, emotion_analyzer):
        """Test recovery from model errors during analysis."""
        test_text = "This is a test for error recovery scenarios."

        # Test BERT model error
        if emotion_analyzer.models_loaded:
            with patch.object(emotion_analyzer, "bert_classifier") as mock_bert:
                mock_bert.side_effect = Exception("BERT model error")

                result = emotion_analyzer.analyze_emotions(test_text)

                # Should fallback gracefully
                assert result is not None
                assert "emotions" in result
                assert result["confidence"] >= 0  # Should have some confidence

    def test_memory_efficiency_large_text(self, emotion_analyzer):
        """Test memory efficiency with large text inputs."""
        import psutil
        import os

        # Create large text (10KB)
        large_text = (
            "This is emotional content with joy, sadness, and excitement. " * 200
        )

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Analyze large text multiple times
        for _ in range(10):
            result = emotion_analyzer.analyze_emotions(large_text)
            assert "emotions" in result

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (< 20MB)
        assert memory_growth < 20, f"Excessive memory growth: {memory_growth:.2f}MB"

    def test_analyze_emotions_statistical_properties(self, emotion_analyzer):
        """Test statistical properties of emotion analysis results."""
        # Test with various content types
        test_texts = [
            "I'm happy and excited!",
            "This is sad and disappointing.",
            "I'm angry and frustrated!",
            "This is surprising and unexpected!",
            "I trust this completely.",
            "I'm fearful and worried.",
            "This is disgusting and revolting.",
            "I anticipate great things ahead!",
        ]

        all_results = []
        for text in test_texts:
            result = emotion_analyzer.analyze_emotions(text)
            all_results.append(result)

        # Statistical properties
        confidences = [r["confidence"] for r in all_results]
        [r["emotions"]["joy"] for r in all_results]

        # Confidence distribution should be reasonable
        avg_confidence = sum(confidences) / len(confidences)
        assert avg_confidence > 0.5, "Average confidence should be reasonable"

        # Should show emotion variety across different texts
        dominant_emotions = [
            max(r["emotions"], key=r["emotions"].get) for r in all_results
        ]
        unique_dominants = set(dominant_emotions)
        assert len(unique_dominants) >= 4, "Should detect variety in dominant emotions"
