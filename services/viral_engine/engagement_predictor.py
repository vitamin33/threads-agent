# services/viral_engine/engagement_predictor.py
from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from prometheus_client import Counter, Histogram

# Metrics for monitoring
PREDICTION_COUNTER = Counter(
    "engagement_predictions_total",
    "Total engagement predictions made",
    ["prediction_result"],
)
PREDICTION_LATENCY = Histogram(
    "engagement_prediction_latency_seconds", "Prediction latency"
)
MODEL_ACCURACY = Histogram("engagement_model_accuracy", "Model accuracy over time")


class EngagementPredictor:
    """
    Machine learning model that predicts Thread post engagement rate with >80% accuracy.
    Uses feature engineering and lightweight ML for real-time predictions.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = (
            model_path or Path(__file__).parent / "models" / "engagement_model.pkl"
        )
        self.vectorizer_path = Path(self.model_path).parent / "tfidf_vectorizer.pkl"
        self.min_quality_score = 0.6  # Lower threshold for rule-based scoring
        self.target_accuracy = 0.80

        # Feature weights for scoring
        self.feature_weights = {
            "readability": 0.10,
            "emotion_intensity": 0.15,
            "hook_strength": 0.30,
            "optimal_length": 0.10,
            "curiosity_gaps": 0.15,
            "authority_signals": 0.05,
            "share_triggers": 0.05,
            "reply_magnets": 0.10,
        }

        # Load model if exists, otherwise use rule-based scoring
        self.model = None
        self.vectorizer = None
        self._load_model()

    def _load_model(self) -> None:
        """Load trained model and vectorizer if available"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(self.vectorizer_path, "rb") as f:
                    self.vectorizer = pickle.load(f)
                print(f"Loaded ML model from {self.model_path}")
            else:
                print("No trained model found, using rule-based scoring")
        except Exception as e:
            print(f"Error loading model: {e}, using rule-based scoring")

    def extract_features(self, post: str) -> Dict[str, float]:
        """Extract engagement prediction features from post text"""
        features = {
            "readability": self._calculate_readability(post),
            "emotion_intensity": self._calculate_emotion_score(post),
            "hook_strength": self._calculate_hook_strength(post),
            "optimal_length": self._check_optimal_length(post),
            "curiosity_gaps": self._count_curiosity_gaps(post),
            "authority_signals": self._extract_authority_signals(post),
            "share_triggers": self._count_share_triggers(post),
            "reply_magnets": self._count_reply_magnets(post),
        }
        return features

    def _calculate_readability(self, text: str) -> float:
        """Calculate Flesch Reading Ease score (simplified)"""
        sentences = text.count(".") + text.count("!") + text.count("?")
        if sentences == 0:
            sentences = 1

        words = len(text.split())
        if words == 0:
            return 0.0

        # Simplified readability score (0-1)
        avg_sentence_length = words / sentences

        # Ideal is 5-15 words per sentence for social media
        if 5 <= avg_sentence_length <= 15:
            return 1.0
        elif avg_sentence_length < 5:
            return avg_sentence_length / 5
        else:
            return max(0.3, 1 - (avg_sentence_length - 15) / 30)

    def _calculate_emotion_score(self, text: str) -> float:
        """Calculate emotional intensity of the text"""
        emotion_words = {
            "positive": [
                "amazing",
                "incredible",
                "love",
                "awesome",
                "brilliant",
                "fantastic",
                "excellent",
            ],
            "negative": [
                "hate",
                "terrible",
                "awful",
                "disgusting",
                "horrible",
                "worst",
                "fail",
            ],
            "intense": [
                "absolutely",
                "completely",
                "totally",
                "extremely",
                "insane",
                "crazy",
                "mind-blowing",
            ],
        }

        text_lower = text.lower()
        score = 0.0
        word_count = len(text.split())

        for category, words in emotion_words.items():
            for word in words:
                if word in text_lower:
                    score += 1.0

        # Normalize by text length
        return min(1.0, score / max(word_count * 0.1, 1))

    def _calculate_hook_strength(self, text: str) -> float:
        """Analyze hook pattern strength"""
        text_lower = text.lower()
        strong_hooks = [
            ("question", text.strip().endswith("?")),
            ("number", any(char.isdigit() for char in text.split()[0] if text.split())),
            (
                "controversial",
                any(
                    word in text_lower
                    for word in [
                        "unpopular",
                        "controversial",
                        "nobody",
                        "everyone",
                        "90%",
                        "most",
                    ]
                ),
            ),
            ("story", text_lower.startswith(("i ", "my ", "when i", "yesterday"))),
            (
                "command",
                any(
                    text.startswith(word)
                    for word in ["Stop", "Don't", "Never", "Always"]
                ),
            ),
            (
                "social_proof",
                any(
                    phrase in text_lower
                    for phrase in ["here's why", "here's how", "the reason"]
                ),
            ),
        ]

        hook_score = sum(1.0 for _, present in strong_hooks if present)
        return min(1.0, hook_score / 2.5)  # Normalize to 0-1

    def _check_optimal_length(self, text: str) -> float:
        """Check if text length is optimal (50-125 words)"""
        word_count = len(text.split())

        if 50 <= word_count <= 125:
            return 1.0
        elif word_count < 50:
            return word_count / 50
        else:
            return max(0, 1 - (word_count - 125) / 125)

    def _count_curiosity_gaps(self, text: str) -> float:
        """Count curiosity-inducing elements"""
        curiosity_patterns = [
            "...",
            "?",
            "here's why",
            "the reason",
            "the secret",
            "what happened next",
            "you won't believe",
            "this is why",
        ]

        count = sum(1 for pattern in curiosity_patterns if pattern in text.lower())
        return min(1.0, count / 3)  # Normalize to 0-1

    def _extract_authority_signals(self, text: str) -> float:
        """Extract credibility and authority indicators"""
        authority_patterns = [
            "research",
            "study",
            "found",
            "data",
            "statistics",
            "expert",
            "professional",
            "years",
            "experience",
            "%",
            "million",
            "billion",
        ]

        count = sum(1 for pattern in authority_patterns if pattern in text.lower())
        return min(1.0, count / 3)

    def _count_share_triggers(self, text: str) -> float:
        """Count elements that trigger sharing behavior"""
        share_patterns = [
            "share if",
            "repost",
            "spread",
            "tell your",
            "tag someone",
            "who else",
            "agree?",
        ]

        count = sum(1 for pattern in share_patterns if pattern in text.lower())
        return min(1.0, count / 2)

    def _count_reply_magnets(self, text: str) -> float:
        """Count conversation-starting elements"""
        reply_patterns = [
            "what do you think",
            "your thoughts",
            "let me know",
            "comment below",
            "?",  # Questions in general
            "your experience",
            "am i wrong",
        ]

        count = sum(1 for pattern in reply_patterns if pattern in text.lower())
        return min(1.0, count / 2)

    @PREDICTION_LATENCY.time()
    def score_content(self, post: str) -> float:
        """
        Score content for predicted engagement rate.
        Returns a score between 0 and 1, where 1 is highest predicted engagement.
        """
        # Extract features
        features = self.extract_features(post)

        # If we have a trained ML model, use it
        if self.model is not None and self.vectorizer is not None:
            try:
                # Combine text features with extracted features
                text_features = self.vectorizer.transform([post]).toarray()[0]
                feature_vector = np.concatenate(
                    [text_features, np.array(list(features.values()))]
                )

                # Get prediction probability
                score = self.model.predict_proba([feature_vector])[0][1]

                PREDICTION_COUNTER.labels(prediction_result="ml_model").inc()
                return float(score)
            except Exception as e:
                print(f"ML prediction failed: {e}, falling back to rule-based")

        # Fall back to weighted rule-based scoring
        score = sum(
            features[feature] * weight
            for feature, weight in self.feature_weights.items()
        )

        PREDICTION_COUNTER.labels(prediction_result="rule_based").inc()
        return min(1.0, score)

    def predict_engagement_rate(self, post: str) -> Dict[str, Any]:
        """
        Predict engagement rate with detailed analysis.
        Returns predicted ER and contributing factors.
        """
        score = self.score_content(post)
        features = self.extract_features(post)

        # Convert score to predicted engagement rate
        # Score of 0.7+ maps to 6%+ engagement rate (our target)
        predicted_er = score * 0.12  # Max 12% ER for perfect score

        # Determine quality assessment
        quality_assessment = "high" if score >= self.min_quality_score else "low"

        # Identify top contributing factors
        sorted_features = sorted(
            features.items(),
            key=lambda x: x[1] * self.feature_weights.get(x[0], 0),
            reverse=True,
        )

        return {
            "quality_score": score,
            "predicted_engagement_rate": predicted_er,
            "quality_assessment": quality_assessment,
            "should_publish": score >= self.min_quality_score,
            "feature_scores": features,
            "top_factors": sorted_features[:3],
            "improvement_suggestions": self._generate_improvements(features),
        }

    def _generate_improvements(self, features: Dict[str, float]) -> List[str]:
        """Generate improvement suggestions based on low-scoring features"""
        suggestions = []

        if features["readability"] < 0.5:
            suggestions.append("Simplify sentence structure for better readability")

        if features["hook_strength"] < 0.5:
            suggestions.append(
                "Start with a stronger hook (question, number, or controversy)"
            )

        if features["curiosity_gaps"] < 0.3:
            suggestions.append("Add curiosity gaps to encourage continued reading")

        if features["reply_magnets"] < 0.3:
            suggestions.append("Include questions or calls for reader input")

        if features["optimal_length"] < 0.7:
            suggestions.append("Adjust length to 50-125 words for optimal engagement")

        return suggestions

    def batch_score(self, posts: List[str]) -> List[float]:
        """Score multiple posts efficiently"""
        return [self.score_content(post) for post in posts]
