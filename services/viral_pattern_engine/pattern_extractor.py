"""Viral pattern extraction engine for analyzing viral content patterns."""

import re
from typing import Dict, List, Any
from services.viral_scraper.models import ViralPost
from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper


class ViralPatternExtractor:
    """Extracts viral patterns from post content using ML and NLP techniques."""

    def __init__(self):
        """Initialize the pattern extractor with advanced emotion analysis capabilities."""
        self.emotion_analyzer = EmotionAnalyzer()
        self.trajectory_mapper = TrajectoryMapper()

    def extract_patterns(self, post: ViralPost) -> Dict[str, Any]:
        """
        Extract patterns from a viral post.

        Args:
            post: ViralPost to analyze

        Returns:
            Dictionary containing extracted patterns with structure:
            {
                "hook_patterns": [...],
                "emotion_patterns": [...],
                "structure_patterns": [...],
                "engagement_score": float,
                "pattern_strength": float
            }
        """
        # Initialize the basic structure
        patterns = {
            "hook_patterns": [],
            "emotion_patterns": [],
            "structure_patterns": [],
            "engagement_score": 0.0,
            "pattern_strength": 0.0,
        }

        content = post.content.lower()
        original_content = post.content

        # Hook pattern detection
        patterns["hook_patterns"].extend(
            self._extract_hook_patterns(content, original_content)
        )

        # Emotion pattern detection (enhanced with multi-model analysis)
        patterns["emotion_patterns"].extend(
            self._extract_emotion_patterns(original_content)
        )

        # Emotion trajectory analysis for longer content
        patterns["emotion_trajectory"] = self._extract_emotion_trajectory(
            original_content
        )

        # Structure pattern detection
        patterns["structure_patterns"].extend(
            self._extract_structure_patterns(original_content)
        )

        # Engagement score based on post performance
        patterns["engagement_score"] = min(post.engagement_rate, 1.0)

        # Calculate pattern strength based on detected patterns
        patterns["pattern_strength"] = self._calculate_pattern_strength(patterns)

        return patterns

    def _extract_hook_patterns(
        self, content: str, original_content: str
    ) -> List[Dict[str, Any]]:
        """Extract hook patterns from content."""
        hook_patterns = []

        # Discovery pattern
        if "just discovered" in content and any(
            word in content for word in ["python", "library", "tool", "ai", "secret"]
        ):
            hook_patterns.append(
                {
                    "type": "discovery",
                    "template": "Just discovered this incredible {tool} that {benefit}!",
                    "confidence": 0.8,
                }
            )

        # Statistical pattern (numbers/percentages)
        if re.search(r"\d+%|\d+x|\d+ times|increased.*by \d+", content):
            hook_patterns.append(
                {
                    "type": "statistical",
                    "template": "This {tool} increased my {metric} by {percentage}%!",
                    "confidence": 0.7,
                }
            )

        # Transformation story pattern
        if re.search(r"\d+ months? ago.*today|was.*now|before.*after", content):
            hook_patterns.append(
                {
                    "type": "transformation_story",
                    "template": "{time_ago} I was {before_state}. Today I {after_state}.",
                    "confidence": 0.8,
                    "before_state": "struggling",
                    "after_state": "successful",
                }
            )

        # Curiosity gap pattern
        if any(
            phrase in content
            for phrase in [
                "secret",
                "don't want you to know",
                "won't tell you",
                "hidden",
            ]
        ):
            triggers = [
                phrase
                for phrase in [
                    "secret",
                    "don't want you to know",
                    "won't tell you",
                    "hidden",
                ]
                if phrase in content
            ]
            hook_patterns.append(
                {
                    "type": "curiosity_gap",
                    "template": "The {secret} that {authority} don't want you to know about {topic}",
                    "confidence": 0.9,
                    "triggers": triggers,
                }
            )

        # Urgency/Breaking pattern
        if any(
            word in content for word in ["breaking", "urgent", "🚨", "alert", "just in"]
        ):
            hook_patterns.append(
                {
                    "type": "urgency",
                    "template": "🚨 BREAKING: {news_content}",
                    "confidence": 0.8,
                }
            )

        return hook_patterns

    def _extract_emotion_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract emotion patterns from content using advanced multi-model analysis."""
        emotion_patterns = []

        # Use advanced emotion analyzer for comprehensive emotion detection
        emotion_analysis = self.emotion_analyzer.analyze_emotions(content)

        # Convert to the pattern format expected by the system
        emotion_pattern = {
            "emotions": emotion_analysis["emotions"],
            "confidence": emotion_analysis["confidence"],
            "model_info": emotion_analysis["model_info"],
            "ensemble_info": emotion_analysis["ensemble_info"],
        }

        emotion_patterns.append(emotion_pattern)

        # Keep backward compatibility: add legacy excitement pattern if joy is high
        if emotion_analysis["emotions"]["joy"] > 0.7:
            emotion_patterns.append(
                {
                    "type": "excitement",
                    "intensity": emotion_analysis["emotions"]["joy"],
                    "confidence": emotion_analysis["confidence"],
                }
            )

        return emotion_patterns

    def _extract_emotion_trajectory(self, content: str) -> Dict[str, Any]:
        """Extract emotion trajectory for longer content by segmenting and analyzing progression."""
        # Only analyze trajectory for content longer than 50 words
        word_count = len(content.split())
        if word_count < 50:
            return {
                "arc_type": "steady",
                "emotion_progression": [],
                "segments_analyzed": 0,
            }

        # Segment content by sentences for trajectory analysis
        sentences = [
            s.strip() for s in content.split(".") if s.strip() and len(s.strip()) > 10
        ]

        if len(sentences) < 3:
            # Not enough segments for trajectory analysis
            return {
                "arc_type": "steady",
                "emotion_progression": [],
                "segments_analyzed": len(sentences),
            }

        # Use trajectory mapper to analyze emotion progression
        trajectory_result = self.trajectory_mapper.map_emotion_trajectory(sentences)
        trajectory_result["segments_analyzed"] = len(sentences)

        return trajectory_result

    def _extract_structure_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract content structure patterns."""
        structure_patterns = []

        # Basic structure analysis
        sentence_count = len([s for s in content.split(".") if s.strip()])
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)  # Assuming 200 words per minute

        # Determine length category
        if word_count < 20:
            length_category = "short"
        elif word_count < 100:
            length_category = "medium"
        else:
            length_category = "long"

        # Check for thread indicators
        has_thread_indicator = any(
            indicator in content.lower()
            for indicator in ["(thread)", "🧵", "thread:", "1/"]
        )

        structure_patterns.append(
            {
                "length_category": length_category,
                "has_thread_indicator": has_thread_indicator,
                "sentence_count": sentence_count,
                "reading_time_seconds": reading_time * 60,
                "word_count": word_count,
            }
        )

        return structure_patterns

    def _calculate_pattern_strength(self, patterns: Dict[str, Any]) -> float:
        """Calculate overall pattern strength based on detected patterns."""
        strength = 0.0

        # Hook patterns contribute most to strength
        hook_strength = len(patterns["hook_patterns"]) * 0.4
        strength += hook_strength

        # Emotion patterns contribute
        emotion_strength = len(patterns["emotion_patterns"]) * 0.3
        strength += emotion_strength

        # Structure patterns contribute
        structure_strength = len(patterns["structure_patterns"]) * 0.2
        strength += structure_strength

        # Bonus for multiple pattern types (synergy effect)
        pattern_types = sum(
            [
                1 if patterns["hook_patterns"] else 0,
                1 if patterns["emotion_patterns"] else 0,
                1 if patterns["structure_patterns"] else 0,
            ]
        )
        if pattern_types >= 2:
            strength += 0.2  # Synergy bonus

        # Cap at 1.0
        return min(strength, 1.0)
