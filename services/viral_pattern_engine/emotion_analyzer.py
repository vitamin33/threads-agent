"""Multi-model emotion analysis for viral content."""

from typing import Dict, Any
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from transformers import pipeline
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    MODELS_AVAILABLE = True
except ImportError:
    # Fallback for testing environments without ML dependencies
    MODELS_AVAILABLE = False


class EmotionAnalyzer:
    """Multi-model emotion detector using BERT and VADER for comprehensive emotion analysis."""

    def __init__(self):
        """Initialize the emotion analyzer with BERT and VADER models."""
        self.bert_model_name = "j-hartmann/emotion-english-distilroberta-base"
        self.bert_weight = 0.7
        self.vader_weight = 0.3

        if MODELS_AVAILABLE:
            try:
                # Initialize BERT emotion classifier
                self.bert_classifier = pipeline(
                    "text-classification",
                    model=self.bert_model_name,
                    return_all_scores=True,
                )

                # Initialize VADER sentiment analyzer
                self.vader_analyzer = SentimentIntensityAnalyzer()

                self.models_loaded = True
            except Exception:
                # Fallback to keyword-based analysis if models fail to load
                self.models_loaded = False
        else:
            self.models_loaded = False

    def analyze_emotions(self, text: str) -> Dict[str, Any]:
        """
        Analyze emotions in text using multiple models.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary with emotions and their confidence scores plus model metadata
        """
        if self.models_loaded:
            return self._analyze_with_models(text)
        else:
            return self._analyze_with_keywords(text)

    def _analyze_with_models(self, text: str) -> Dict[str, Any]:
        """Analyze emotions using BERT and VADER models."""
        # Get BERT emotion scores
        bert_results = self.bert_classifier(text)[0]

        # Convert BERT results to our 8-emotion format
        bert_emotions = self._convert_bert_to_8_emotions(bert_results)

        # Get VADER sentiment scores
        vader_scores = self.vader_analyzer.polarity_scores(text)
        vader_emotions = self._convert_vader_to_emotions(vader_scores)

        # Ensemble the results
        final_emotions = self._ensemble_emotions(bert_emotions, vader_emotions)

        # Calculate overall confidence
        confidence = self._calculate_confidence(bert_results, vader_scores)
        
        # Find dominant emotion
        dominant_emotion = max(final_emotions, key=final_emotions.get)

        return {
            "emotions": final_emotions,
            "dominant_emotion": dominant_emotion,
            "confidence": confidence,
            "model_info": {
                "bert_model": self.bert_model_name,
                "vader_sentiment": "VADER Sentiment Analysis",
            },
            "ensemble_info": {
                "bert_weight": self.bert_weight,
                "vader_weight": self.vader_weight,
            },
        }

    def _analyze_with_keywords(self, text: str) -> Dict[str, Any]:
        """Fallback keyword-based analysis for environments without ML models."""
        text_lower = text.lower()

        # Initialize all 8 emotions with base scores
        emotions = {
            "joy": 0.1,
            "anger": 0.1,
            "fear": 0.1,
            "sadness": 0.1,
            "surprise": 0.1,
            "disgust": 0.1,
            "trust": 0.1,
            "anticipation": 0.1,
        }

        # Enhanced keyword-based emotion detection
        if any(
            word in text_lower
            for word in [
                "excited",
                "happy",
                "amazing",
                "incredible",
                "wonderful",
                "love",
                "great",
            ]
        ):
            emotions["joy"] = 0.8
            emotions["sadness"] = 0.1

        if any(
            word in text_lower
            for word in ["devastated", "heartbroken", "worst", "sad", "terrible"]
        ):
            emotions["sadness"] = 0.8
            emotions["joy"] = 0.1

        if any(
            word in text_lower
            for word in ["furious", "outraged", "unacceptable", "infuriating", "angry"]
        ):
            emotions["anger"] = 0.8
            emotions["trust"] = 0.2

        if any(
            word in text_lower for word in ["worried", "scared", "afraid", "anxious"]
        ):
            emotions["fear"] = 0.7
            emotions["trust"] = 0.2

        if any(
            word in text_lower for word in ["surprised", "shocked", "unexpected", "wow"]
        ):
            emotions["surprise"] = 0.7

        if any(
            word in text_lower for word in ["disgusting", "revolting", "gross", "awful"]
        ):
            emotions["disgust"] = 0.7

        if any(
            word in text_lower for word in ["trust", "reliable", "confident", "believe"]
        ):
            emotions["trust"] = 0.7

        if any(
            word in text_lower for word in ["expect", "hope", "anticipate", "future"]
        ):
            emotions["anticipation"] = 0.6

        # Find dominant emotion
        dominant_emotion = max(emotions, key=emotions.get)
        
        return {
            "emotions": emotions,
            "dominant_emotion": dominant_emotion,
            "confidence": 0.7,  # Moderate confidence for keyword-based analysis
            "model_info": {
                "bert_model": "keyword-fallback",
                "vader_sentiment": "keyword-fallback",
            },
            "ensemble_info": {"bert_weight": 0.7, "vader_weight": 0.3},
        }

    def _convert_bert_to_8_emotions(self, bert_results) -> Dict[str, float]:
        """Convert BERT emotion labels to our 8-emotion taxonomy."""
        # BERT model returns: joy, sadness, anger, fear, surprise, disgust, love
        # We need: joy, anger, fear, sadness, surprise, disgust, trust, anticipation

        emotion_map = {}
        for result in bert_results:
            label = result["label"].lower()
            score = result["score"]

            if label in ["joy", "anger", "fear", "sadness", "surprise", "disgust"]:
                emotion_map[label] = score
            elif label == "love":
                # Map love to joy and trust
                emotion_map["joy"] = emotion_map.get("joy", 0) + score * 0.6
                emotion_map["trust"] = emotion_map.get("trust", 0) + score * 0.4

        # Fill in missing emotions with low scores
        final_emotions = {
            "joy": emotion_map.get("joy", 0.1),
            "anger": emotion_map.get("anger", 0.1),
            "fear": emotion_map.get("fear", 0.1),
            "sadness": emotion_map.get("sadness", 0.1),
            "surprise": emotion_map.get("surprise", 0.1),
            "disgust": emotion_map.get("disgust", 0.1),
            "trust": emotion_map.get("trust", 0.1),
            "anticipation": emotion_map.get("anticipation", 0.1),
        }

        return final_emotions

    def _convert_vader_to_emotions(self, vader_scores) -> Dict[str, float]:
        """Convert VADER sentiment scores to emotion scores."""
        # VADER returns: compound, pos, neu, neg
        pos = vader_scores["pos"]
        neg = vader_scores["neg"]
        compound = vader_scores["compound"]

        emotions = {
            "joy": pos * 0.8 if compound > 0.1 else 0.1,
            "trust": pos * 0.6 if compound > 0.3 else 0.1,
            "anticipation": pos * 0.4 if compound > 0.0 else 0.1,
            "sadness": neg * 0.7 if compound < -0.1 else 0.1,
            "anger": neg * 0.6 if compound < -0.3 else 0.1,
            "fear": neg * 0.5 if compound < -0.2 else 0.1,
            "disgust": neg * 0.4 if compound < -0.4 else 0.1,
            "surprise": abs(compound) * 0.3 if abs(compound) > 0.5 else 0.1,
        }

        return emotions

    def _ensemble_emotions(self, bert_emotions, vader_emotions) -> Dict[str, float]:
        """Combine BERT and VADER emotion scores using weighted ensemble."""
        final_emotions = {}

        for emotion in bert_emotions:
            bert_score = bert_emotions[emotion]
            vader_score = vader_emotions[emotion]

            # Weighted average
            final_score = (
                bert_score * self.bert_weight + vader_score * self.vader_weight
            )
            final_emotions[emotion] = min(1.0, max(0.0, final_score))  # Clamp to [0, 1]

        return final_emotions

    def _calculate_confidence(self, bert_results, vader_scores) -> float:
        """Calculate overall confidence based on model agreement."""
        # Get highest BERT confidence
        bert_confidence = max([r["score"] for r in bert_results])

        # VADER confidence based on compound score magnitude
        vader_confidence = min(1.0, abs(vader_scores["compound"]) + 0.3)

        # Average the confidences
        overall_confidence = (
            bert_confidence * self.bert_weight + vader_confidence * self.vader_weight
        )

        return round(overall_confidence, 3)
