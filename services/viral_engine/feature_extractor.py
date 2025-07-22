# services/viral_engine/feature_extractor.py
from __future__ import annotations

import re
from typing import Dict, List

import nltk  # type: ignore
import numpy as np

# Download required NLTK data (run once)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)

try:
    nltk.data.find("vader_lexicon")
except LookupError:
    nltk.download("vader_lexicon", quiet=True)

from nltk.sentiment.vader import SentimentIntensityAnalyzer  # type: ignore


class AdvancedFeatureExtractor:
    """
    Advanced feature extraction for engagement prediction.
    Extracts linguistic, sentiment, and structural features from text.
    """

    def __init__(self) -> None:
        self.sia = SentimentIntensityAnalyzer()

        # Power words that drive engagement
        self.power_words = {
            "action": ["now", "today", "immediately", "quick", "fast", "instant"],
            "emotion": [
                "amazing",
                "shocking",
                "incredible",
                "unbelievable",
                "mind-blowing",
            ],
            "exclusivity": ["secret", "exclusive", "limited", "only", "special"],
            "urgency": ["urgent", "breaking", "alert", "warning", "critical"],
            "social": ["everyone", "nobody", "people", "community", "together"],
        }

        # Engagement trigger patterns
        self.trigger_patterns = {
            "list": re.compile(
                r"\d+\s+(ways|reasons|tips|tricks|hacks|things|steps)", re.I
            ),
            "how_to": re.compile(r"how\s+to\s+\w+", re.I),
            "question": re.compile(r"[?]|^(why|what|when|where|who|how)\s", re.I),
            "negation": re.compile(r"(don't|never|stop|avoid|no\s+more)", re.I),
            "comparison": re.compile(r"(better|worse|more|less)\s+than", re.I),
        }

    def extract_all_features(self, text: str) -> Dict[str, float]:
        """Extract comprehensive feature set from text"""
        features = {}

        # Basic text statistics
        features.update(self._extract_text_stats(text))

        # Sentiment features
        features.update(self._extract_sentiment_features(text))

        # Linguistic features
        features.update(self._extract_linguistic_features(text))

        # Engagement pattern features
        features.update(self._extract_engagement_patterns(text))

        # Power word features
        features.update(self._extract_power_word_features(text))

        return features

    def _extract_text_stats(self, text: str) -> Dict[str, float]:
        """Extract basic text statistics"""
        words = text.split()
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

        stats: Dict[str, float] = {
            "word_count": float(len(words)),
            "sentence_count": float(len(sentences)),
            "avg_word_length": (
                float(np.mean([len(w) for w in words])) if words else 0.0
            ),
            "avg_sentence_length": (
                float(np.mean([len(s.split()) for s in sentences]))
                if sentences
                else 0.0
            ),
            "exclamation_count": float(text.count("!")),
            "question_count": float(text.count("?")),
            "capital_ratio": sum(1 for c in text if c.isupper()) / max(len(text), 1),
        }

        # Normalize counts by text length
        text_length = max(len(words), 1)
        for key in ["exclamation_count", "question_count"]:
            stats[key] = stats[key] / text_length

        return stats

    def _extract_sentiment_features(self, text: str) -> Dict[str, float]:
        """Extract sentiment and emotion features using VADER"""
        scores = self.sia.polarity_scores(text)

        # Calculate emotion intensity
        emotion_intensity = abs(scores["compound"])

        # Detect emotional volatility (mixed emotions)
        volatility = scores["pos"] * scores["neg"] * 4  # High when both are present

        return {
            "sentiment_positive": scores["pos"],
            "sentiment_negative": scores["neg"],
            "sentiment_neutral": scores["neu"],
            "sentiment_compound": scores["compound"],
            "emotion_intensity": emotion_intensity,
            "emotion_volatility": volatility,
        }

    def _extract_linguistic_features(self, text: str) -> Dict[str, float]:
        """Extract linguistic complexity features"""
        words = text.lower().split()

        # Vocabulary diversity (type-token ratio)
        unique_words = set(words)
        vocabulary_diversity = len(unique_words) / max(len(words), 1)

        # Personal pronouns (creates connection)
        personal_pronouns = ["i", "you", "we", "us", "our", "your"]
        pronoun_count = sum(1 for w in words if w in personal_pronouns)
        pronoun_ratio = pronoun_count / max(len(words), 1)

        # Active voice indicators (more engaging)
        active_indicators = ["is", "are", "will", "do", "does", "make", "creates"]
        active_count = sum(1 for w in words if w in active_indicators)
        active_ratio = active_count / max(len(words), 1)

        return {
            "vocabulary_diversity": vocabulary_diversity,
            "personal_pronoun_ratio": pronoun_ratio,
            "active_voice_ratio": active_ratio,
        }

    def _extract_engagement_patterns(self, text: str) -> Dict[str, float]:
        """Extract known engagement-driving patterns"""
        pattern_scores = {}

        for pattern_name, pattern in self.trigger_patterns.items():
            matches = len(pattern.findall(text))
            pattern_scores[f"pattern_{pattern_name}"] = min(1.0, matches / 2)

        # Check for cliffhangers and open loops
        cliffhanger_phrases = ["but", "however", "although", "despite", "yet"]
        cliffhanger_score = sum(
            1 for phrase in cliffhanger_phrases if phrase in text.lower()
        )
        pattern_scores["cliffhanger_score"] = min(1.0, cliffhanger_score / 3)

        return pattern_scores

    def _extract_power_word_features(self, text: str) -> Dict[str, float]:
        """Extract power word usage features"""
        text_lower = text.lower()
        words = text_lower.split()

        power_scores: Dict[str, float] = {}
        total_power_words = 0

        for category, word_list in self.power_words.items():
            count = sum(1 for word in word_list if word in text_lower)
            power_scores[f"power_{category}"] = float(count)
            total_power_words += count

        # Normalize by text length
        for key in power_scores:
            power_scores[key] = power_scores[key] / max(len(words), 1)

        power_scores["power_word_density"] = total_power_words / max(len(words), 1)

        return power_scores

    def create_feature_vector(self, text: str) -> np.ndarray:
        """Create numerical feature vector for ML models"""
        features = self.extract_all_features(text)

        # Ensure consistent ordering
        feature_names = sorted(features.keys())
        vector = np.array([features[name] for name in feature_names])

        return vector

    def get_feature_names(self) -> List[str]:
        """Get ordered list of feature names"""
        # Generate dummy text to extract all possible features
        dummy_text = "This is a test? Amazing! How to do it better than before."
        features = self.extract_all_features(dummy_text)
        return sorted(features.keys())
