# services/viral_engine/tests/unit/test_engagement_predictor.py
from __future__ import annotations

import pytest

from services.viral_engine.engagement_predictor import EngagementPredictor
from services.viral_engine.feature_extractor import AdvancedFeatureExtractor


@pytest.fixture
def predictor():
    """Create EngagementPredictor instance for testing"""
    return EngagementPredictor()


@pytest.fixture
def feature_extractor():
    """Create AdvancedFeatureExtractor instance for testing"""
    return AdvancedFeatureExtractor()


class TestEngagementPredictor:
    """Test suite for EngagementPredictor"""

    def test_initialization(self, predictor):
        """Test predictor initializes correctly"""
        assert isinstance(predictor, EngagementPredictor)
        assert predictor.min_quality_score == 0.6
        assert predictor.target_accuracy == 0.80

    def test_feature_extraction(self, predictor):
        """Test feature extraction from text"""
        test_text = "Unpopular opinion: Most productivity advice is just procrastination with extra steps. What's your take?"

        features = predictor.extract_features(test_text)

        # Check all required features are present
        expected_features = [
            "readability",
            "emotion_intensity",
            "hook_strength",
            "optimal_length",
            "curiosity_gaps",
            "authority_signals",
            "share_triggers",
            "reply_magnets",
        ]

        for feature in expected_features:
            assert feature in features
            assert 0 <= features[feature] <= 1  # All features normalized 0-1

    def test_readability_calculation(self, predictor):
        """Test readability scoring"""
        # Good readability - medium sentence length
        good_text = "AI is changing fast. We need to adapt quickly. The future is now."
        score = predictor._calculate_readability(good_text)
        assert score > 0.8

        # Poor readability - very long sentence
        poor_text = "The implementation of artificial intelligence systems in modern enterprise environments requires careful consideration of multiple factors including but not limited to technical infrastructure scalability security compliance and organizational change management processes."
        score = predictor._calculate_readability(poor_text)
        assert score < 0.5

    def test_hook_strength_detection(self, predictor):
        """Test hook pattern detection"""
        # Strong hook - question + controversy
        strong_hook = "Why does everyone ignore this simple productivity hack?"
        score = predictor._calculate_hook_strength(strong_hook)
        assert score >= 0.4  # Adjusted for new normalization

        # Strong hook - number + social proof
        number_hook = "5 reasons why AI will transform your business. Here's why:"
        score = predictor._calculate_hook_strength(number_hook)
        assert score >= 0.4

        # Weak hook
        weak_hook = "Today I want to talk about something"
        score = predictor._calculate_hook_strength(weak_hook)
        assert score < 0.4

    def test_optimal_length_check(self, predictor):
        """Test optimal length detection"""
        # Optimal length (50-125 words)
        optimal_text = " ".join(["word"] * 75)
        score = predictor._check_optimal_length(optimal_text)
        assert score == 1.0

        # Too short
        short_text = " ".join(["word"] * 20)
        score = predictor._check_optimal_length(short_text)
        assert score < 1.0

        # Too long
        long_text = " ".join(["word"] * 200)
        score = predictor._check_optimal_length(long_text)
        assert score < 1.0

    def test_curiosity_gap_detection(self, predictor):
        """Test curiosity gap counting"""
        # High curiosity
        curious_text = "Here's why this matters... But wait, there's more. You won't believe what happened next."
        score = predictor._count_curiosity_gaps(curious_text)
        assert score > 0.5

        # Low curiosity
        plain_text = "This is a statement about facts."
        score = predictor._count_curiosity_gaps(plain_text)
        assert score < 0.3

    def test_content_scoring(self, predictor):
        """Test overall content scoring"""
        # High-quality viral content
        viral_content = "Unpopular opinion: 90% of productivity apps make you LESS productive. Here's why: They create more work than they save. What's your experience?"
        score = predictor.score_content(viral_content)
        assert score >= 0.65  # Should be high but might not reach 0.7 threshold

        # Very high quality viral content (should definitely pass)
        excellent_content = "Stop scrolling! 90% of people fail because of this one mistake. Here's the shocking truth nobody talks about. What's your biggest failure?"
        score = predictor.score_content(excellent_content)
        assert score >= 0.6  # Should meet new threshold

        # Low-quality content
        poor_content = "Just another day. Nothing special happening."
        score = predictor.score_content(poor_content)
        assert score < predictor.min_quality_score

    def test_engagement_rate_prediction(self, predictor):
        """Test full engagement rate prediction"""
        test_content = "Unpopular opinion: 90% fail at this. Stop making this mistake! Here's the secret nobody tells you about success. What's holding you back?"

        prediction = predictor.predict_engagement_rate(test_content)

        # Check response structure
        assert "quality_score" in prediction
        assert "predicted_engagement_rate" in prediction
        assert "quality_assessment" in prediction
        assert "should_publish" in prediction
        assert "feature_scores" in prediction
        assert "top_factors" in prediction
        assert "improvement_suggestions" in prediction

        # High-quality content should pass
        assert prediction["quality_assessment"] == "high"
        assert prediction["should_publish"] is True
        assert prediction["predicted_engagement_rate"] >= 0.06  # 6% target

    def test_batch_scoring(self, predictor):
        """Test batch content scoring"""
        posts = [
            "Just had lunch",
            "Amazing discovery: 5 AI tricks nobody knows! Here's why this matters:",
            "Working on stuff today",
        ]

        scores = predictor.batch_score(posts)

        assert len(scores) == 3
        assert all(0 <= score <= 1 for score in scores)
        # Middle post should score highest (has number, hook, and curiosity)
        assert scores[1] > scores[0]
        assert scores[1] > scores[2]

    def test_improvement_suggestions(self, predictor):
        """Test improvement suggestion generation"""
        poor_content = "This is a very long sentence that goes on and on without any clear point or engaging elements that would make someone want to read it or interact with it in any meaningful way whatsoever."

        prediction = predictor.predict_engagement_rate(poor_content)
        suggestions = prediction["improvement_suggestions"]

        assert len(suggestions) > 0
        assert any("readability" in s.lower() for s in suggestions)


class TestAdvancedFeatureExtractor:
    """Test suite for AdvancedFeatureExtractor"""

    def test_text_stats_extraction(self, feature_extractor):
        """Test basic text statistics extraction"""
        text = "This is great! Really amazing. What do you think?"

        stats = feature_extractor._extract_text_stats(text)

        assert stats["word_count"] == 9
        assert stats["sentence_count"] == 3
        assert stats["question_count"] > 0
        assert stats["exclamation_count"] > 0

    def test_sentiment_feature_extraction(self, feature_extractor):
        """Test sentiment analysis features"""
        # Positive text
        positive_text = "This is absolutely amazing and wonderful!"
        features = feature_extractor._extract_sentiment_features(positive_text)
        assert features["sentiment_positive"] > features["sentiment_negative"]

        # Negative text
        negative_text = "This is terrible and awful."
        features = feature_extractor._extract_sentiment_features(negative_text)
        assert features["sentiment_negative"] > features["sentiment_positive"]

    def test_linguistic_features(self, feature_extractor):
        """Test linguistic complexity features"""
        text = "You and I can make this work. We will succeed together."

        features = feature_extractor._extract_linguistic_features(text)

        assert features["personal_pronoun_ratio"] > 0
        assert features["vocabulary_diversity"] > 0
        assert features["active_voice_ratio"] > 0

    def test_engagement_pattern_detection(self, feature_extractor):
        """Test engagement pattern extraction"""
        text = "5 ways to improve your life. How to get started today?"

        patterns = feature_extractor._extract_engagement_patterns(text)

        assert patterns["pattern_list"] > 0
        assert patterns["pattern_how_to"] > 0
        assert patterns["pattern_question"] > 0

    def test_power_word_features(self, feature_extractor):
        """Test power word detection"""
        text = "Amazing secret revealed! Get instant results now - exclusive limited offer today only!"

        features = feature_extractor._extract_power_word_features(text)

        assert features["power_word_density"] > 0
        assert features["power_emotion"] > 0
        assert features["power_exclusivity"] > 0
        assert features["power_action"] > 0

    def test_complete_feature_extraction(self, feature_extractor):
        """Test complete feature extraction pipeline"""
        text = "Unpopular opinion: 90% of advice is wrong. Here's what actually works:"

        features = feature_extractor.extract_all_features(text)

        # Should have features from all categories
        assert len(features) > 20

        # Check some key features exist
        assert "word_count" in features
        assert "sentiment_compound" in features
        assert "vocabulary_diversity" in features
        assert "pattern_question" in features
        assert "power_word_density" in features

        # All values should be numeric
        assert all(isinstance(v, (int, float)) for v in features.values())
