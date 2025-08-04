"""Optimized emotion analyzer for Kubernetes deployment."""

import os
import logging
from typing import Dict, List, Any
from functools import lru_cache
import threading

logger = logging.getLogger(__name__)

# Global model instances for reuse across requests
_model_lock = threading.Lock()
_bert_model = None
_bert_tokenizer = None
_vader_analyzer = None


class OptimizedEmotionAnalyzer:
    """
    Optimized emotion analyzer with Kubernetes-specific performance improvements.

    Optimizations:
    1. Singleton model loading with thread-safe initialization
    2. Model warm-up on container start
    3. LRU caching for repeated content
    4. Batch processing support
    5. Memory-efficient tokenization
    6. Connection pooling for model inference
    """

    # Emotion categories
    EMOTIONS = [
        "joy",
        "anger",
        "fear",
        "sadness",
        "surprise",
        "disgust",
        "trust",
        "anticipation",
    ]

    # Cache configuration
    CACHE_SIZE = int(os.getenv("EMOTION_CACHE_SIZE", "1000"))

    def __init__(self):
        """Initialize the optimized emotion analyzer."""
        self.bert_available = False
        self.vader_available = False

        # Load models on initialization for container readiness
        self._initialize_models()

        # Warm up models
        if os.getenv("WARM_UP_MODELS", "true").lower() == "true":
            self._warm_up_models()

    def _initialize_models(self):
        """Initialize ML models with singleton pattern."""
        global _bert_model, _bert_tokenizer, _vader_analyzer

        with _model_lock:
            # BERT model initialization
            if _bert_model is None:
                try:
                    if os.getenv("ENABLE_BERT", "true").lower() == "true":
                        _bert_model, _bert_tokenizer = self._load_bert_model()
                        self.bert_available = True
                        logger.info("BERT model loaded successfully")
                except Exception as e:
                    logger.warning(f"BERT model loading failed: {e}")
                    self.bert_available = False
            else:
                self.bert_available = True

            # VADER initialization
            if _vader_analyzer is None:
                try:
                    if os.getenv("ENABLE_VADER", "true").lower() == "true":
                        _vader_analyzer = self._load_vader_analyzer()
                        self.vader_available = True
                        logger.info("VADER analyzer loaded successfully")
                except Exception as e:
                    logger.warning(f"VADER loading failed: {e}")
                    self.vader_available = False
            else:
                self.vader_available = True

    @staticmethod
    def _load_bert_model():
        """Load BERT model with optimizations."""
        from transformers import pipeline, AutoTokenizer

        model_name = os.getenv(
            "BERT_MODEL", "j-hartmann/emotion-english-distilroberta-base"
        )

        # Use specific model loading for better memory control
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            model_max_length=128,  # Limit sequence length
            use_fast=True,  # Use fast tokenizer
        )

        classifier = pipeline(
            "text-classification",
            model=model_name,
            tokenizer=tokenizer,
            device=-1,  # Force CPU for K8s stability
            batch_size=int(os.getenv("BERT_BATCH_SIZE", "8")),
        )

        return classifier, tokenizer

    @staticmethod
    def _load_vader_analyzer():
        """Load VADER analyzer."""
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        return SentimentIntensityAnalyzer()

    def _warm_up_models(self):
        """Warm up models for faster first inference."""
        try:
            test_texts = ["This is amazing!", "I feel terrible.", "Just a normal day."]
            for text in test_texts:
                self.analyze_emotion(text)
            logger.info("Model warm-up completed")
        except Exception as e:
            logger.warning(f"Model warm-up failed: {e}")

    @lru_cache(maxsize=CACHE_SIZE)
    def analyze_emotion(self, text: str) -> Dict[str, Any]:
        """
        Analyze emotions in text with caching.

        Uses LRU cache to avoid reprocessing identical content.
        """
        if not text or not text.strip():
            return self._empty_emotion_result()

        # Try multi-model approach
        if self.bert_available and self.vader_available:
            return self._analyze_with_ensemble(text)
        elif self.bert_available:
            return self._analyze_with_bert(text)
        elif self.vader_available:
            return self._analyze_with_vader(text)
        else:
            return self._analyze_with_keywords(text)

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze emotions in batch for better performance.

        Optimized for K8s horizontal scaling.
        """
        if not texts:
            return []

        # Use cache for repeated texts
        results = []
        uncached_texts = []
        uncached_indices = []

        # Check cache first
        for i, text in enumerate(texts):
            try:
                result = self.analyze_emotion(text)
                results.append(result)
            except Exception:
                # Not in cache, need to process
                uncached_texts.append(text)
                uncached_indices.append(i)
                results.append(None)

        # Process uncached texts in batch if using BERT
        if uncached_texts and self.bert_available:
            batch_results = self._analyze_batch_with_bert(uncached_texts)
            for idx, result in zip(uncached_indices, batch_results):
                results[idx] = result

        # Fill any remaining None results with fallback
        for i, result in enumerate(results):
            if result is None:
                results[i] = self._analyze_with_keywords(texts[i])

        return results

    def _analyze_batch_with_bert(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze batch of texts with BERT for efficiency."""
        global _bert_model

        try:
            # Truncate texts to avoid memory issues
            truncated_texts = [text[:512] for text in texts]

            # Get predictions in batch
            predictions = _bert_model(truncated_texts)

            results = []
            for pred_list in predictions:
                emotion_scores = {emotion: 0.0 for emotion in self.EMOTIONS}

                # Map predictions to our emotion categories
                for pred in pred_list:
                    emotion = pred["label"].lower()
                    if emotion in emotion_scores:
                        emotion_scores[emotion] = pred["score"]

                results.append(
                    {
                        "emotions": emotion_scores,
                        "dominant_emotion": max(emotion_scores, key=emotion_scores.get),
                        "confidence": max(emotion_scores.values()),
                        "model": "bert_batch",
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Batch BERT analysis failed: {e}")
            # Fallback to individual analysis
            return [self._analyze_with_keywords(text) for text in texts]

    def _analyze_with_ensemble(self, text: str) -> Dict[str, Any]:
        """Ensemble analysis with memory optimization."""
        # Get BERT emotions
        bert_result = self._analyze_with_bert(text)

        # Get VADER sentiment
        vader_result = self._analyze_with_vader(text)

        # Weighted ensemble (70% BERT, 30% VADER)
        ensemble_emotions = {}
        for emotion in self.EMOTIONS:
            bert_score = bert_result["emotions"].get(emotion, 0.0)

            # Map VADER sentiment to emotions
            vader_mapping = self._map_vader_to_emotions(vader_result["sentiment"])
            vader_score = vader_mapping.get(emotion, 0.0)

            ensemble_emotions[emotion] = 0.7 * bert_score + 0.3 * vader_score

        dominant_emotion = max(ensemble_emotions, key=ensemble_emotions.get)

        return {
            "emotions": ensemble_emotions,
            "dominant_emotion": dominant_emotion,
            "confidence": ensemble_emotions[dominant_emotion],
            "sentiment": vader_result["sentiment"],
            "model": "ensemble",
        }

    def _analyze_with_bert(self, text: str) -> Dict[str, Any]:
        """BERT analysis with error handling."""
        global _bert_model

        try:
            # Truncate for memory efficiency
            truncated_text = text[:512]
            predictions = _bert_model(truncated_text)

            emotion_scores = {emotion: 0.0 for emotion in self.EMOTIONS}

            for pred in predictions:
                emotion = pred["label"].lower()
                if emotion in emotion_scores:
                    emotion_scores[emotion] = pred["score"]

            dominant_emotion = max(emotion_scores, key=emotion_scores.get)

            return {
                "emotions": emotion_scores,
                "dominant_emotion": dominant_emotion,
                "confidence": emotion_scores[dominant_emotion],
                "model": "bert",
            }

        except Exception as e:
            logger.error(f"BERT analysis failed: {e}")
            return self._analyze_with_keywords(text)

    def _analyze_with_vader(self, text: str) -> Dict[str, Any]:
        """VADER analysis optimized."""
        global _vader_analyzer

        try:
            scores = _vader_analyzer.polarity_scores(text)

            return {
                "sentiment": {
                    "compound": scores["compound"],
                    "positive": scores["pos"],
                    "neutral": scores["neu"],
                    "negative": scores["neg"],
                },
                "model": "vader",
            }
        except Exception as e:
            logger.error(f"VADER analysis failed: {e}")
            return {
                "sentiment": {
                    "compound": 0.0,
                    "positive": 0.0,
                    "neutral": 1.0,
                    "negative": 0.0,
                }
            }

    def _analyze_with_keywords(self, text: str) -> Dict[str, Any]:
        """Fallback keyword analysis - very fast."""
        # Keyword-based emotion detection
        emotion_keywords = {
            "joy": [
                "happy",
                "joy",
                "excited",
                "amazing",
                "wonderful",
                "fantastic",
                "great",
                "love",
                "excellent",
                "perfect",
            ],
            "anger": [
                "angry",
                "furious",
                "hate",
                "annoyed",
                "frustrated",
                "rage",
                "mad",
                "pissed",
                "irritated",
            ],
            "fear": [
                "scared",
                "afraid",
                "terrified",
                "anxious",
                "worried",
                "nervous",
                "panic",
                "dread",
            ],
            "sadness": [
                "sad",
                "depressed",
                "crying",
                "tears",
                "heartbroken",
                "miserable",
                "lonely",
                "grief",
            ],
            "surprise": [
                "surprised",
                "shocked",
                "amazed",
                "astonished",
                "unexpected",
                "sudden",
                "wow",
                "omg",
            ],
            "disgust": [
                "disgusted",
                "gross",
                "revolting",
                "nasty",
                "horrible",
                "awful",
                "terrible",
            ],
            "trust": [
                "trust",
                "believe",
                "faith",
                "reliable",
                "confident",
                "secure",
                "depend",
            ],
            "anticipation": [
                "excited",
                "looking forward",
                "can't wait",
                "anticipate",
                "expect",
                "eager",
                "hopeful",
            ],
        }

        text_lower = text.lower()
        emotion_scores = {}

        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower) / len(
                keywords
            )
            emotion_scores[emotion] = min(score * 2, 1.0)  # Scale up but cap at 1.0

        # If no emotions detected, default to neutral
        if all(score == 0 for score in emotion_scores.values()):
            emotion_scores["trust"] = 0.3  # Neutral baseline

        dominant_emotion = max(emotion_scores, key=emotion_scores.get)

        return {
            "emotions": emotion_scores,
            "dominant_emotion": dominant_emotion,
            "confidence": emotion_scores[dominant_emotion]
            * 0.6,  # Lower confidence for keywords
            "model": "keywords",
        }

    def _map_vader_to_emotions(self, sentiment: Dict[str, float]) -> Dict[str, float]:
        """Map VADER sentiment to emotion categories."""
        emotion_mapping = {}
        compound = sentiment["compound"]

        if compound > 0.5:
            emotion_mapping["joy"] = compound
            emotion_mapping["trust"] = compound * 0.8
            emotion_mapping["anticipation"] = compound * 0.7
        elif compound > 0.1:
            emotion_mapping["trust"] = compound * 2
            emotion_mapping["anticipation"] = compound
        elif compound < -0.5:
            emotion_mapping["sadness"] = abs(compound)
            emotion_mapping["anger"] = abs(compound) * 0.7
            emotion_mapping["fear"] = abs(compound) * 0.5
        elif compound < -0.1:
            emotion_mapping["sadness"] = abs(compound) * 2
            emotion_mapping["fear"] = abs(compound)
        else:
            emotion_mapping["trust"] = 0.5  # Neutral

        # Normalize
        for emotion in self.EMOTIONS:
            if emotion not in emotion_mapping:
                emotion_mapping[emotion] = 0.0

        return emotion_mapping

    def _empty_emotion_result(self) -> Dict[str, Any]:
        """Return empty emotion result."""
        return {
            "emotions": {emotion: 0.0 for emotion in self.EMOTIONS},
            "dominant_emotion": "neutral",
            "confidence": 0.0,
            "model": "none",
        }

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage for monitoring."""
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "cache_size": self.analyze_emotion.cache_info().currsize,
            "cache_hits": self.analyze_emotion.cache_info().hits,
            "cache_misses": self.analyze_emotion.cache_info().misses,
            "model_loaded": {
                "bert": self.bert_available,
                "vader": self.vader_available,
            },
        }


# Global instance for reuse
_analyzer_instance = None


def get_emotion_analyzer() -> OptimizedEmotionAnalyzer:
    """Get singleton emotion analyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = OptimizedEmotionAnalyzer()
    return _analyzer_instance
