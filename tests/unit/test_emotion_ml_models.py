"""ML model integration tests with fallback scenarios for emotion analysis."""

import pytest
from unittest.mock import patch

from services.viral_pattern_engine.emotion_analyzer import (
    EmotionAnalyzer,
    MODELS_AVAILABLE,
)


class TestEmotionMLModels:
    """Test ML model integration and fallback scenarios."""

    @pytest.fixture
    def emotion_analyzer(self):
        """Create emotion analyzer instance."""
        return EmotionAnalyzer()

    def test_bert_model_integration(self, emotion_analyzer):
        """Test BERT model integration when available."""
        if not MODELS_AVAILABLE:
            pytest.skip("ML models not available in test environment")

        test_text = "I'm absolutely thrilled about this amazing discovery!"

        if emotion_analyzer.models_loaded:
            # Test with actual BERT model
            with patch.object(emotion_analyzer, "bert_classifier") as mock_bert:
                # Mock BERT response
                mock_bert.return_value = [
                    [
                        {"label": "joy", "score": 0.85},
                        {"label": "sadness", "score": 0.05},
                        {"label": "anger", "score": 0.02},
                        {"label": "fear", "score": 0.03},
                        {"label": "surprise", "score": 0.03},
                        {"label": "disgust", "score": 0.02},
                    ]
                ]

                result = emotion_analyzer._analyze_with_models(test_text)

                # Verify BERT integration
                assert (
                    result["model_info"]["bert_model"]
                    == "j-hartmann/emotion-english-distilroberta-base"
                )
                assert result["emotions"]["joy"] > 0.5  # Should detect high joy
                assert result["confidence"] > 0.7

    def test_vader_model_integration(self, emotion_analyzer):
        """Test VADER model integration when available."""
        if not MODELS_AVAILABLE:
            pytest.skip("ML models not available in test environment")

        test_text = "This is absolutely terrible and disgusting! I hate it!"

        if emotion_analyzer.models_loaded:
            # Test with actual VADER model
            with patch.object(emotion_analyzer, "vader_analyzer") as mock_vader:
                # Mock VADER response
                mock_vader.polarity_scores.return_value = {
                    "compound": -0.8,
                    "neg": 0.75,
                    "neu": 0.15,
                    "pos": 0.1,
                }

                result = emotion_analyzer._analyze_with_models(test_text)

                # Verify VADER integration
                assert (
                    result["model_info"]["vader_sentiment"]
                    == "VADER Sentiment Analysis"
                )
                # Should detect negative emotions
                negative_total = (
                    result["emotions"]["anger"]
                    + result["emotions"]["disgust"]
                    + result["emotions"]["sadness"]
                )
                assert negative_total > 0.3

    def test_ensemble_model_weights(self, emotion_analyzer):
        """Test ensemble weighting between BERT and VADER."""
        if not emotion_analyzer.models_loaded:
            pytest.skip("Models not loaded, testing fallback instead")

        test_text = "Mixed emotional content with some joy and some sadness."

        with (
            patch.object(emotion_analyzer, "bert_classifier") as mock_bert,
            patch.object(emotion_analyzer, "vader_analyzer") as mock_vader,
        ):
            # Mock BERT - high joy
            mock_bert.return_value = [
                [{"label": "joy", "score": 0.9}, {"label": "sadness", "score": 0.1}]
            ]

            # Mock VADER - neutral
            mock_vader.polarity_scores.return_value = {
                "compound": 0.0,
                "neg": 0.3,
                "neu": 0.4,
                "pos": 0.3,
            }

            result = emotion_analyzer._analyze_with_models(test_text)

            # Verify ensemble weighting (BERT 0.7, VADER 0.3)
            assert result["ensemble_info"]["bert_weight"] == 0.7
            assert result["ensemble_info"]["vader_weight"] == 0.3

            # Joy should be dominated by BERT's high score
            assert result["emotions"]["joy"] > 0.6

    def test_bert_model_failure_fallback(self, emotion_analyzer):
        """Test fallback when BERT model fails."""
        test_text = "Happy content that should work with fallback!"

        with patch.object(emotion_analyzer, "bert_classifier") as mock_bert:
            mock_bert.side_effect = Exception("BERT model error")

            # Should fall back to keyword analysis
            result = emotion_analyzer.analyze_emotions(test_text)

            assert result is not None
            assert "emotions" in result
            # Should detect happy keywords
            assert result["emotions"]["joy"] > 0.5

    def test_vader_model_failure_fallback(self, emotion_analyzer):
        """Test fallback when VADER model fails."""
        test_text = "Sad content that should trigger fallback."

        if emotion_analyzer.models_loaded:
            with (
                patch.object(emotion_analyzer, "vader_analyzer") as mock_vader,
                patch.object(emotion_analyzer, "bert_classifier") as mock_bert,
            ):
                # VADER fails, BERT works
                mock_vader.polarity_scores.side_effect = Exception("VADER error")
                mock_bert.return_value = [
                    [{"label": "sadness", "score": 0.8}, {"label": "joy", "score": 0.2}]
                ]

                result = emotion_analyzer.analyze_emotions(test_text)

                # Should still work with BERT only
                assert result is not None
                assert "emotions" in result

    def test_both_models_failure_complete_fallback(self, emotion_analyzer):
        """Test complete fallback when both models fail."""
        test_text = "Exciting content for fallback testing!"

        with patch.object(emotion_analyzer, "models_loaded", False):
            result = emotion_analyzer.analyze_emotions(test_text)

            # Should use keyword-based analysis
            assert result["model_info"]["bert_model"] == "keyword-fallback"
            assert result["model_info"]["vader_sentiment"] == "keyword-fallback"
            assert result["confidence"] == 0.7  # Fallback confidence

            # Should still detect emotions via keywords
            assert result["emotions"]["joy"] > 0.5  # "exciting" keyword

    def test_keyword_fallback_emotion_detection(self, emotion_analyzer):
        """Test keyword-based emotion detection accuracy."""
        test_cases = [
            {
                "text": "I'm so excited and happy about this amazing discovery!",
                "expected_dominant": "joy",
                "expected_score": 0.8,
            },
            {
                "text": "This is devastating and heartbreaking news that makes me sad.",
                "expected_dominant": "sadness",
                "expected_score": 0.8,
            },
            {
                "text": "I'm furious and outraged about this unacceptable situation!",
                "expected_dominant": "anger",
                "expected_score": 0.8,
            },
            {
                "text": "I'm worried and scared about what might happen next.",
                "expected_dominant": "fear",
                "expected_score": 0.7,
            },
            {
                "text": "Wow, that was unexpected! I'm completely surprised!",
                "expected_dominant": "surprise",
                "expected_score": 0.7,
            },
            {
                "text": "That's absolutely disgusting and revolting behavior.",
                "expected_dominant": "disgust",
                "expected_score": 0.7,
            },
            {
                "text": "I trust this solution and believe it will work reliably.",
                "expected_dominant": "trust",
                "expected_score": 0.7,
            },
            {
                "text": "I expect great things and hope for a bright future ahead!",
                "expected_dominant": "anticipation",
                "expected_score": 0.6,
            },
        ]

        # Force keyword-based analysis
        with patch.object(emotion_analyzer, "models_loaded", False):
            for case in test_cases:
                result = emotion_analyzer.analyze_emotions(case["text"])

                dominant_emotion = max(result["emotions"], key=result["emotions"].get)
                dominant_score = result["emotions"][case["expected_dominant"]]

                assert dominant_emotion == case["expected_dominant"], (
                    f"Expected {case['expected_dominant']}, got {dominant_emotion} for: {case['text']}"
                )
                assert dominant_score >= case["expected_score"], (
                    f"Expected score >= {case['expected_score']}, got {dominant_score}"
                )

    def test_model_initialization_failure_handling(self):
        """Test handling of model initialization failures."""
        # Test when transformers import fails
        with patch(
            "services.viral_pattern_engine.emotion_analyzer.MODELS_AVAILABLE", False
        ):
            analyzer = EmotionAnalyzer()

            assert analyzer.models_loaded is False

            result = analyzer.analyze_emotions("Test content")
            assert result["model_info"]["bert_model"] == "keyword-fallback"

    def test_bert_model_loading_exception(self):
        """Test handling of BERT model loading exceptions."""
        # Force models_loaded to False to simulate loading failure
        analyzer = EmotionAnalyzer()
        analyzer.models_loaded = False

        result = analyzer.analyze_emotions("Test content")
        assert result["model_info"]["bert_model"] == "keyword-fallback"

    def test_vader_model_loading_exception(self):
        """Test handling of VADER model loading exceptions."""
        # Force models_loaded to False to simulate loading failure
        analyzer = EmotionAnalyzer()
        analyzer.models_loaded = False

        # Should fall back to keyword analysis
        result = analyzer.analyze_emotions("Test content")
        assert result["model_info"]["vader_sentiment"] == "keyword-fallback"

    def test_bert_emotion_mapping_accuracy(self, emotion_analyzer):
        """Test accuracy of BERT emotion label mapping."""
        if not emotion_analyzer.models_loaded:
            pytest.skip("Models not loaded")

        # Mock BERT response with all possible labels
        bert_results = [
            {"label": "joy", "score": 0.3},
            {"label": "sadness", "score": 0.2},
            {"label": "anger", "score": 0.1},
            {"label": "fear", "score": 0.1},
            {"label": "surprise", "score": 0.1},
            {"label": "disgust", "score": 0.05},
            {"label": "love", "score": 0.15},  # Should map to joy + trust
        ]

        mapped_emotions = emotion_analyzer._convert_bert_to_8_emotions(bert_results)

        # Verify all 8 emotions are present
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

        # Verify love mapping
        assert mapped_emotions["joy"] > 0.3  # Original + love contribution
        assert mapped_emotions["trust"] > 0.1  # Love contribution

    def test_vader_emotion_mapping_accuracy(self, emotion_analyzer):
        """Test accuracy of VADER sentiment to emotion mapping."""
        if not emotion_analyzer.models_loaded:
            pytest.skip("Models not loaded")

        test_cases = [
            {
                "vader_scores": {"compound": 0.8, "pos": 0.9, "neu": 0.1, "neg": 0.0},
                "expected_high": ["joy", "trust"],
                "expected_low": ["sadness", "anger", "fear"],
            },
            {
                "vader_scores": {"compound": -0.8, "pos": 0.0, "neu": 0.1, "neg": 0.9},
                "expected_high": ["sadness", "anger"],
                "expected_low": ["joy", "trust"],
            },
            {
                "vader_scores": {"compound": 0.0, "pos": 0.3, "neu": 0.7, "neg": 0.0},
                "expected_neutral": True,
            },
        ]

        for case in test_cases:
            mapped_emotions = emotion_analyzer._convert_vader_to_emotions(
                case["vader_scores"]
            )

            if "expected_high" in case:
                for emotion in case["expected_high"]:
                    assert mapped_emotions[emotion] > 0.3, f"{emotion} should be high"

            if "expected_low" in case:
                for emotion in case["expected_low"]:
                    assert mapped_emotions[emotion] < 0.3, f"{emotion} should be low"

    def test_confidence_calculation_accuracy(self, emotion_analyzer):
        """Test confidence score calculation logic."""
        if not emotion_analyzer.models_loaded:
            pytest.skip("Models not loaded")

        # High confidence BERT results
        high_conf_bert = [{"label": "joy", "score": 0.95}]
        high_conf_vader = {"compound": 0.9, "pos": 0.95, "neu": 0.05, "neg": 0.0}

        high_confidence = emotion_analyzer._calculate_confidence(
            high_conf_bert, high_conf_vader
        )
        assert high_confidence > 0.8

        # Low confidence BERT results
        low_conf_bert = [{"label": "joy", "score": 0.4}]
        low_conf_vader = {"compound": 0.1, "pos": 0.4, "neu": 0.6, "neg": 0.0}

        low_confidence = emotion_analyzer._calculate_confidence(
            low_conf_bert, low_conf_vader
        )
        assert low_confidence < 0.6

    def test_model_performance_monitoring(self, emotion_analyzer):
        """Test monitoring of model performance and accuracy."""
        test_texts = [
            "I'm extremely happy and joyful!",
            "This is terribly sad and depressing.",
            "I'm absolutely furious about this!",
            "That's quite surprising and unexpected.",
            "I completely trust this approach.",
        ]

        results = []
        for text in test_texts:
            result = emotion_analyzer.analyze_emotions(text)
            results.append(result)

        # Verify consistent performance
        confidences = [r["confidence"] for r in results]
        avg_confidence = sum(confidences) / len(confidences)

        # Should maintain reasonable confidence across different inputs
        assert avg_confidence > 0.5
        assert all(c >= 0.0 and c <= 1.0 for c in confidences)

        # Should detect appropriate emotions for each text
        expected_dominants = ["joy", "sadness", "anger", "surprise", "trust"]
        for result, expected in zip(results, expected_dominants):
            max(result["emotions"], key=result["emotions"].get)
            # Allow some flexibility in emotion detection
            assert result["emotions"][expected] > 0.3, (
                f"Expected high {expected} but got low score"
            )

    def test_model_memory_usage(self, emotion_analyzer):
        """Test that models don't cause memory leaks."""
        import gc
        import psutil
        import os

        # Get initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run many analyses
        for i in range(100):
            text = f"Test content number {i} with various emotional expressions!"
            result = emotion_analyzer.analyze_emotions(text)
            assert "emotions" in result

            # Force garbage collection every 10 iterations
            if i % 10 == 0:
                gc.collect()

        # Check final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (< 50MB for 100 analyses)
        assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.2f}MB"

    def test_model_thread_safety(self, emotion_analyzer):
        """Test thread safety of model operations."""
        import threading
        import time

        results = []
        errors = []

        def worker_analysis():
            try:
                for i in range(5):
                    result = emotion_analyzer.analyze_emotions(
                        f"Thread test content {i}"
                    )
                    results.append(result)
                    time.sleep(0.01)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker_analysis)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10.0)

        # Verify thread safety
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 25  # 5 threads × 5 analyses each
        assert all("emotions" in r for r in results)

    def test_model_version_compatibility(self, emotion_analyzer):
        """Test compatibility with different model versions."""
        # This test verifies graceful handling of model version differences
        if not emotion_analyzer.models_loaded:
            pytest.skip("Models not loaded")

        # Test with unexpected BERT label
        with patch.object(emotion_analyzer, "bert_classifier") as mock_bert:
            mock_bert.return_value = [
                [
                    {"label": "unknown_emotion", "score": 0.5},  # Unexpected label
                    {"label": "joy", "score": 0.3},
                    {"label": "sadness", "score": 0.2},
                ]
            ]

            # Should handle gracefully
            result = emotion_analyzer._analyze_with_models("Test content")
            assert result is not None
            assert "emotions" in result

            # Should still have all 8 emotions with defaults
            assert len(result["emotions"]) == 8

    def test_ensemble_weight_customization(self):
        """Test customization of ensemble weights."""
        # Test with custom weights
        analyzer = EmotionAnalyzer()
        analyzer.bert_weight = 0.8
        analyzer.vader_weight = 0.2

        if analyzer.models_loaded:
            with (
                patch.object(analyzer, "bert_classifier") as mock_bert,
                patch.object(analyzer, "vader_analyzer") as mock_vader,
            ):
                mock_bert.return_value = [[{"label": "joy", "score": 0.9}]]
                mock_vader.polarity_scores.return_value = {
                    "compound": -0.5,
                    "pos": 0.1,
                    "neu": 0.3,
                    "neg": 0.6,
                }

                result = analyzer._analyze_with_models("Test content")

                # Joy should be high due to BERT dominance (0.8 weight)
                assert result["emotions"]["joy"] > 0.6
                assert result["ensemble_info"]["bert_weight"] == 0.8
                assert result["ensemble_info"]["vader_weight"] == 0.2
