"""Temporal emotion trajectory mapping for viral content analysis."""

from typing import List, Dict, Any
from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer


class TrajectoryMapper:
    """Maps emotion trajectories over content segments and classifies emotional arcs."""

    def __init__(self):
        """Initialize the trajectory mapper with emotion analyzer."""
        self.emotion_analyzer = EmotionAnalyzer()

    def map_emotion_trajectory(self, content_segments: List[str]) -> Dict[str, Any]:
        """
        Map emotion trajectory across content segments.

        Args:
            content_segments: List of text segments to analyze

        Returns:
            Dictionary containing arc classification and emotion progression
        """
        # Analyze emotions for each segment
        emotion_progression = []
        for segment in content_segments:
            segment_emotions = self.emotion_analyzer.analyze_emotions(segment)[
                "emotions"
            ]
            emotion_progression.append(segment_emotions)

        # Classify the emotional arc
        arc_type = self._classify_emotional_arc(emotion_progression)

        # Detect peaks and valleys
        peaks_valleys = self.detect_peaks_and_valleys(emotion_progression)

        # Calculate emotional variance
        emotional_variance = self.calculate_emotional_variance(emotion_progression)

        return {
            "arc_type": arc_type,
            "emotion_progression": emotion_progression,
            "peak_segments": peaks_valleys["peak_indices"],
            "valley_segments": peaks_valleys["valley_indices"],
            "emotional_variance": emotional_variance,
        }

    def analyze_emotion_transitions(
        self, content_segments: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze emotion transitions between content segments.

        Args:
            content_segments: List of text segments to analyze

        Returns:
            Dictionary containing transition patterns and strengths
        """
        # Get emotion progression
        emotion_progression = []
        for segment in content_segments:
            segment_emotions = self.emotion_analyzer.analyze_emotions(segment)[
                "emotions"
            ]
            emotion_progression.append(segment_emotions)

        transitions = []
        for i in range(len(emotion_progression) - 1):
            current_emotions = emotion_progression[i]
            next_emotions = emotion_progression[i + 1]

            # Find dominant emotions
            current_dominant = max(current_emotions, key=current_emotions.get)
            next_dominant = max(next_emotions, key=next_emotions.get)

            # Calculate transition strength
            strength = abs(
                next_emotions[next_dominant] - current_emotions[current_dominant]
            )

            transitions.append(
                {
                    "from_emotion": current_dominant,
                    "to_emotion": next_dominant,
                    "strength": round(strength, 3),
                }
            )

        # Find most common transitions
        transition_counts = {}
        for transition in transitions:
            key = f"{transition['from_emotion']}_to_{transition['to_emotion']}"
            transition_counts[key] = transition_counts.get(key, 0) + 1

        dominant_transitions = sorted(
            transition_counts.items(), key=lambda x: x[1], reverse=True
        )

        return {
            "transitions": transitions,
            "dominant_transitions": dominant_transitions,
            "transition_strength": sum(t["strength"] for t in transitions)
            / len(transitions)
            if transitions
            else 0,
        }

    def detect_peaks_and_valleys(
        self, emotion_scores: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Detect peaks and valleys in emotion progression.

        Args:
            emotion_scores: List of emotion score dictionaries

        Returns:
            Dictionary containing peak and valley information
        """
        if len(emotion_scores) < 3:
            return {
                "peaks": [],
                "valleys": [],
                "peak_indices": [],
                "valley_indices": [],
            }

        # Calculate overall emotional intensity for each segment
        intensities = []
        for emotions in emotion_scores:
            # Use joy as primary positive emotion and sadness as primary negative
            intensity = emotions.get("joy", 0) - emotions.get("sadness", 0)
            intensities.append(intensity)

        peak_indices = []
        valley_indices = []

        # Find local maxima and minima
        for i in range(1, len(intensities) - 1):
            # Peak: higher than both neighbors
            if (
                intensities[i] > intensities[i - 1]
                and intensities[i] > intensities[i + 1]
            ):
                peak_indices.append(i)
            # Valley: lower than both neighbors
            elif (
                intensities[i] < intensities[i - 1]
                and intensities[i] < intensities[i + 1]
            ):
                valley_indices.append(i)

        return {
            "peaks": [emotion_scores[i] for i in peak_indices],
            "valleys": [emotion_scores[i] for i in valley_indices],
            "peak_indices": peak_indices,
            "valley_indices": valley_indices,
        }

    def calculate_emotional_variance(
        self, emotion_scores: List[Dict[str, float]]
    ) -> float:
        """
        Calculate emotional variance across segments.

        Args:
            emotion_scores: List of emotion score dictionaries

        Returns:
            Variance measure (0.0 = no variance, 1.0 = maximum variance)
        """
        if len(emotion_scores) < 2:
            return 0.0

        # Calculate variance for all emotions to get full emotional volatility
        all_emotions = [
            "joy",
            "sadness",
            "anger",
            "fear",
            "surprise",
            "disgust",
            "trust",
            "anticipation",
        ]
        total_variance = 0
        emotion_count = 0

        for emotion in all_emotions:
            values = [scores.get(emotion, 0) for scores in emotion_scores]
            if any(
                val > 0.1 for val in values
            ):  # Only consider emotions that are actually present
                mean_val = sum(values) / len(values)
                variance = sum((val - mean_val) ** 2 for val in values) / len(values)
                total_variance += variance
                emotion_count += 1

        if emotion_count == 0:
            return 0.0

        # Normalize and scale up for better detection
        normalized_variance = (
            total_variance / emotion_count
        ) * 4  # Scale up for better sensitivity
        return round(min(1.0, normalized_variance), 3)

    def _classify_emotional_arc(
        self, emotion_progression: List[Dict[str, float]]
    ) -> str:
        """
        Classify the overall emotional arc of the content.

        Args:
            emotion_progression: List of emotion scores for each segment

        Returns:
            Arc type: "rising", "falling", "roller_coaster", or "steady"
        """
        if len(emotion_progression) < 2:
            return "steady"

        # Calculate overall emotional trajectory using joy as primary indicator
        joy_scores = [emotions.get("joy", 0) for emotions in emotion_progression]

        # Calculate trend
        first_joy = joy_scores[0]
        last_joy = joy_scores[-1]
        joy_change = last_joy - first_joy

        # Calculate variance to detect volatility
        variance = self.calculate_emotional_variance(emotion_progression)

        # Detect peaks and valleys for roller coaster pattern
        peaks_valleys = self.detect_peaks_and_valleys(emotion_progression)
        num_peaks = len(peaks_valleys["peak_indices"])
        num_valleys = len(peaks_valleys["valley_indices"])

        # Check for roller coaster pattern first (alternating peaks and valleys)
        # Roller coaster: high variance with alternating pattern, regardless of overall trend
        if variance > 0.4 and (num_peaks >= 1 and num_valleys >= 1):
            # Additional check: look for alternating pattern in joy scores
            joy_changes = []
            for i in range(1, len(joy_scores)):
                joy_changes.append(joy_scores[i] - joy_scores[i - 1])

            # Count direction changes (sign changes in consecutive differences)
            direction_changes = 0
            for i in range(1, len(joy_changes)):
                if (joy_changes[i] > 0 and joy_changes[i - 1] < 0) or (
                    joy_changes[i] < 0 and joy_changes[i - 1] > 0
                ):
                    direction_changes += 1

            # If we have multiple direction changes, it's a roller coaster
            if direction_changes >= 2:
                return "roller_coaster"

        # Classification logic - overall trend
        if abs(joy_change) > 0.3:  # Strong overall trend
            if joy_change > 0.3:
                return "rising"
            else:
                return "falling"
        else:  # Weak overall trend
            if variance < 0.2:
                return "steady"
            else:
                # Default to slight trend if any
                if joy_change > 0.1:
                    return "rising"
                elif joy_change < -0.1:
                    return "falling"
                else:
                    return "steady"
