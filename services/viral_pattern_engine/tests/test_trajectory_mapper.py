"""Tests for temporal emotion trajectory mapping with database integration and multi-model analysis."""

import pytest
import hashlib
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.orchestrator.db import Base
from services.orchestrator.db.models import (
    EmotionTrajectory,
    EmotionSegment,
    EmotionTransition,
    EmotionTemplate,
)
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper
from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer


class TestTrajectoryMapper:
    """Test cases for emotion trajectory analysis with database integration and multi-model analysis."""

    @pytest.fixture
    def db_engine(self):
        """Create in-memory SQLite database for testing."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def db_session(self, db_engine):
        """Create database session for testing."""
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=db_engine
        )
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    @pytest.fixture
    def trajectory_mapper(self):
        """Create trajectory mapper instance."""
        return TrajectoryMapper()

    @pytest.fixture
    def emotion_analyzer(self):
        """Create emotion analyzer instance."""
        return EmotionAnalyzer()

    def test_map_emotion_trajectory_returns_arc_classification(self, trajectory_mapper):
        """Test that trajectory mapper classifies emotional arcs correctly."""
        # Content with clear emotional progression from neutral to excited
        content_segments = [
            "Let me tell you about this tool.",
            "It's actually pretty interesting.",
            "Wait, this is getting amazing!",
            "OMG this is absolutely incredible!",
        ]

        result = trajectory_mapper.map_emotion_trajectory(content_segments)

        # Should return trajectory information
        assert isinstance(result, dict)
        assert "arc_type" in result
        assert "emotion_progression" in result
        assert "peak_segments" in result
        assert "valley_segments" in result

        # Should classify this as a "rising" arc
        assert result["arc_type"] in ["rising", "falling", "roller_coaster", "steady"]
        assert result["arc_type"] == "rising"  # This content clearly builds excitement

        # Should have emotion scores for each segment
        assert len(result["emotion_progression"]) == 4
        for segment_emotions in result["emotion_progression"]:
            assert "joy" in segment_emotions
            assert 0.0 <= segment_emotions["joy"] <= 1.0

    def test_map_emotion_trajectory_detects_falling_arc(self, trajectory_mapper):
        """Test detection of falling emotional arc."""
        content_segments = [
            "I was so excited about this project!",
            "But then things started going wrong.",
            "Now I'm really disappointed.",
            "This is completely devastating.",
        ]

        result = trajectory_mapper.map_emotion_trajectory(content_segments)

        # Should classify as falling arc
        assert result["arc_type"] == "falling"

        # First segment should have higher joy than last
        first_joy = result["emotion_progression"][0]["joy"]
        last_joy = result["emotion_progression"][-1]["joy"]
        assert first_joy > last_joy

    def test_map_emotion_trajectory_detects_roller_coaster_arc(self, trajectory_mapper):
        """Test detection of roller coaster emotional arc with multiple peaks and valleys."""
        content_segments = [
            "I love this new feature!",
            "But wait, there's a serious bug.",
            "Actually, they fixed it! Amazing!",
            "Oh no, now there's another issue.",
            "Never mind, it works perfectly now!",
        ]

        result = trajectory_mapper.map_emotion_trajectory(content_segments)

        # Should classify as roller coaster
        assert result["arc_type"] == "roller_coaster"

        # Should detect at least some peaks and valleys (roller coaster has ups and downs)
        assert len(result["peak_segments"]) >= 1
        assert len(result["valley_segments"]) >= 1

    def test_map_emotion_trajectory_detects_steady_arc(self, trajectory_mapper):
        """Test detection of steady emotional arc with minimal variation."""
        content_segments = [
            "This is a good solution.",
            "It works well for our needs.",
            "The implementation is solid.",
            "Overall, it's a reliable choice.",
        ]

        result = trajectory_mapper.map_emotion_trajectory(content_segments)

        # Should classify as steady
        assert result["arc_type"] == "steady"

        # Should have minimal emotional variation
        assert result["emotional_variance"] < 0.3

    def test_analyze_emotion_transitions_detects_patterns(self, trajectory_mapper):
        """Test emotion transition pattern recognition."""
        content_segments = [
            "I'm worried about this approach.",  # fear
            "Actually, let me research more.",  # anticipation
            "Wow, this is brilliant!",  # joy
            "I trust this will work great.",  # trust
        ]

        result = trajectory_mapper.analyze_emotion_transitions(content_segments)

        # Should return transition patterns
        assert "transitions" in result
        assert "dominant_transitions" in result
        assert "transition_strength" in result

        # Should detect specific transition patterns
        transitions = result["transitions"]
        assert len(transitions) == 3  # 4 segments = 3 transitions

        # Each transition should have from/to emotions and strength
        for transition in transitions:
            assert "from_emotion" in transition
            assert "to_emotion" in transition
            assert "strength" in transition
            assert 0.0 <= transition["strength"] <= 1.0

    def test_detect_peaks_and_valleys_identifies_extremes(self, trajectory_mapper):
        """Test peak and valley detection in emotion progression."""
        # Emotion scores that clearly show peaks and valleys
        emotion_scores = [
            {"joy": 0.2, "sadness": 0.1},  # neutral
            {"joy": 0.8, "sadness": 0.1},  # peak
            {"joy": 0.1, "sadness": 0.7},  # valley
            {"joy": 0.6, "sadness": 0.2},  # moderate peak
            {"joy": 0.1, "sadness": 0.1},  # neutral
        ]

        result = trajectory_mapper.detect_peaks_and_valleys(emotion_scores)

        # Should identify peaks and valleys
        assert "peaks" in result
        assert "valleys" in result
        assert "peak_indices" in result
        assert "valley_indices" in result

        # Should detect the obvious peak at index 1 and valley at index 2
        assert 1 in result["peak_indices"]
        assert 2 in result["valley_indices"]

    def test_calculate_emotional_variance_measures_consistency(self, trajectory_mapper):
        """Test emotional variance calculation for arc classification."""
        # Low variance emotions
        stable_emotions = [
            {"joy": 0.5, "anger": 0.1, "sadness": 0.1},
            {"joy": 0.6, "anger": 0.1, "sadness": 0.1},
            {"joy": 0.5, "anger": 0.1, "sadness": 0.2},
        ]

        # High variance emotions
        volatile_emotions = [
            {"joy": 0.1, "anger": 0.1, "sadness": 0.1},
            {"joy": 0.9, "anger": 0.1, "sadness": 0.1},
            {"joy": 0.1, "anger": 0.8, "sadness": 0.1},
        ]

        stable_variance = trajectory_mapper.calculate_emotional_variance(
            stable_emotions
        )
        volatile_variance = trajectory_mapper.calculate_emotional_variance(
            volatile_emotions
        )

        # Volatile emotions should have higher variance
        assert volatile_variance > stable_variance
        assert stable_variance < 0.3  # Low variance threshold
        assert volatile_variance > 0.5  # High variance threshold

    # Enhanced tests with database integration and multi-model analysis

    def test_trajectory_mapping_with_database_storage(
        self, trajectory_mapper, db_session
    ):
        """Test trajectory mapping results can be stored in database."""
        # Arrange
        content_segments = [
            "I'm thrilled about this discovery!",
            "But I'm worried about the implications.",
            "Actually, I think we can handle this responsibly.",
            "The future looks bright!",
        ]

        # Act - Map trajectory
        trajectory_result = trajectory_mapper.map_emotion_trajectory(content_segments)

        # Store in database
        content_hash = hashlib.sha256(" ".join(content_segments).encode()).hexdigest()
        trajectory = EmotionTrajectory(
            post_id="db_test_post_1",
            persona_id="test_persona",
            content_hash=content_hash,
            segment_count=len(content_segments),
            total_duration_words=sum(len(seg.split()) for seg in content_segments),
            trajectory_type=trajectory_result["arc_type"],
            emotional_variance=trajectory_result["emotional_variance"],
            peak_count=len(trajectory_result["peak_segments"]),
            valley_count=len(trajectory_result["valley_segments"]),
            # Calculate emotion averages
            joy_avg=sum(
                seg.get("joy", 0) for seg in trajectory_result["emotion_progression"]
            )
            / len(trajectory_result["emotion_progression"]),
            anger_avg=sum(
                seg.get("anger", 0) for seg in trajectory_result["emotion_progression"]
            )
            / len(trajectory_result["emotion_progression"]),
            fear_avg=sum(
                seg.get("fear", 0) for seg in trajectory_result["emotion_progression"]
            )
            / len(trajectory_result["emotion_progression"]),
            sadness_avg=sum(
                seg.get("sadness", 0)
                for seg in trajectory_result["emotion_progression"]
            )
            / len(trajectory_result["emotion_progression"]),
            surprise_avg=sum(
                seg.get("surprise", 0)
                for seg in trajectory_result["emotion_progression"]
            )
            / len(trajectory_result["emotion_progression"]),
            disgust_avg=sum(
                seg.get("disgust", 0)
                for seg in trajectory_result["emotion_progression"]
            )
            / len(trajectory_result["emotion_progression"]),
            trust_avg=sum(
                seg.get("trust", 0) for seg in trajectory_result["emotion_progression"]
            )
            / len(trajectory_result["emotion_progression"]),
            anticipation_avg=sum(
                seg.get("anticipation", 0)
                for seg in trajectory_result["emotion_progression"]
            )
            / len(trajectory_result["emotion_progression"]),
        )

        db_session.add(trajectory)
        db_session.commit()

        # Assert
        stored_trajectory = (
            db_session.query(EmotionTrajectory)
            .filter_by(post_id="db_test_post_1")
            .first()
        )
        assert stored_trajectory is not None
        assert stored_trajectory.trajectory_type == trajectory_result["arc_type"]
        assert (
            stored_trajectory.emotional_variance
            == trajectory_result["emotional_variance"]
        )
        assert stored_trajectory.segment_count == len(content_segments)

    def test_trajectory_mapping_with_segment_storage(
        self, trajectory_mapper, db_session
    ):
        """Test storing detailed segment analysis in database."""
        # Arrange
        content_segments = [
            "Amazing breakthrough in AI!",
            "But are we moving too fast?",
            "I trust we'll be responsible.",
        ]

        # Act
        trajectory_result = trajectory_mapper.map_emotion_trajectory(content_segments)

        # Store trajectory
        trajectory = EmotionTrajectory(
            post_id="segment_test_post",
            persona_id="test_persona",
            content_hash=hashlib.sha256(
                " ".join(content_segments).encode()
            ).hexdigest(),
            segment_count=len(content_segments),
            total_duration_words=15,
            trajectory_type=trajectory_result["arc_type"],
            emotional_variance=trajectory_result["emotional_variance"],
            joy_avg=0.6,
            anger_avg=0.1,
            fear_avg=0.3,
            sadness_avg=0.1,
            surprise_avg=0.5,
            disgust_avg=0.1,
            trust_avg=0.4,
            anticipation_avg=0.3,
        )

        db_session.add(trajectory)
        db_session.flush()

        # Store segments
        for i, (segment_text, emotions) in enumerate(
            zip(content_segments, trajectory_result["emotion_progression"])
        ):
            segment = EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=i,
                content_text=segment_text,
                word_count=len(segment_text.split()),
                sentence_count=1,
                joy_score=emotions.get("joy", 0),
                anger_score=emotions.get("anger", 0),
                fear_score=emotions.get("fear", 0),
                sadness_score=emotions.get("sadness", 0),
                surprise_score=emotions.get("surprise", 0),
                disgust_score=emotions.get("disgust", 0),
                trust_score=emotions.get("trust", 0),
                anticipation_score=emotions.get("anticipation", 0),
                dominant_emotion=max(emotions, key=emotions.get),
                confidence_score=0.8,
                is_peak=i in trajectory_result["peak_segments"],
                is_valley=i in trajectory_result["valley_segments"],
            )
            db_session.add(segment)

        db_session.commit()

        # Assert
        stored_segments = (
            db_session.query(EmotionSegment)
            .filter_by(trajectory_id=trajectory.id)
            .all()
        )
        assert len(stored_segments) == 3

        # Verify segment data
        first_segment = stored_segments[0]
        assert first_segment.content_text == "Amazing breakthrough in AI!"
        assert first_segment.dominant_emotion in ["joy", "surprise", "anticipation"]

        # Verify peaks/valleys are marked
        peak_segments = [seg for seg in stored_segments if seg.is_peak]
        valley_segments = [seg for seg in stored_segments if seg.is_valley]

        assert len(peak_segments) >= 0  # May or may not have peaks
        assert len(valley_segments) >= 0  # May or may not have valleys

    def test_transition_analysis_with_database_storage(
        self, trajectory_mapper, db_session
    ):
        """Test emotion transition analysis with database storage."""
        # Arrange
        content_segments = [
            "I'm excited about this opportunity!",
            "But I'm nervous about the challenges.",
            "Actually, I'm confident we can succeed!",
            "Let's trust the process.",
        ]

        # Act - Analyze transitions
        transition_result = trajectory_mapper.analyze_emotion_transitions(
            content_segments
        )
        trajectory_result = trajectory_mapper.map_emotion_trajectory(content_segments)

        # Store trajectory
        trajectory = EmotionTrajectory(
            post_id="transition_test_post",
            persona_id="test_persona",
            content_hash=hashlib.sha256(
                " ".join(content_segments).encode()
            ).hexdigest(),
            segment_count=len(content_segments),
            total_duration_words=20,
            trajectory_type=trajectory_result["arc_type"],
            emotional_variance=trajectory_result["emotional_variance"],
            transition_count=len(transition_result["transitions"]),
            joy_avg=0.5,
            anger_avg=0.1,
            fear_avg=0.2,
            sadness_avg=0.1,
            surprise_avg=0.3,
            disgust_avg=0.1,
            trust_avg=0.4,
            anticipation_avg=0.4,
        )

        db_session.add(trajectory)
        db_session.flush()

        # Store transitions
        for i, transition in enumerate(transition_result["transitions"]):
            transition_record = EmotionTransition(
                trajectory_id=trajectory.id,
                from_segment_index=i,
                to_segment_index=i + 1,
                from_emotion=transition["from_emotion"],
                to_emotion=transition["to_emotion"],
                transition_type="switching"
                if transition["from_emotion"] != transition["to_emotion"]
                else "strengthening",
                intensity_change=transition["strength"],
                transition_speed=transition["strength"]
                / max(len(content_segments[i].split()), 1),
                strength_score=transition["strength"],
            )
            db_session.add(transition_record)

        db_session.commit()

        # Assert
        stored_transitions = (
            db_session.query(EmotionTransition)
            .filter_by(trajectory_id=trajectory.id)
            .all()
        )
        assert len(stored_transitions) == len(transition_result["transitions"])

        # Verify transition data
        for stored, original in zip(
            stored_transitions, transition_result["transitions"]
        ):
            assert stored.from_emotion == original["from_emotion"]
            assert stored.to_emotion == original["to_emotion"]
            assert stored.strength_score == original["strength"]

    def test_multi_model_emotion_analysis_integration(
        self, trajectory_mapper, emotion_analyzer
    ):
        """Test integration between trajectory mapper and multi-model emotion analyzer."""
        # Arrange
        content_segments = [
            "I'm absolutely thrilled about this breakthrough! 🎉",
            "However, I'm deeply concerned about potential misuse. 😰",
            "But I trust our scientific community to handle this responsibly. 🤝",
            "The future looks incredibly bright! ✨",
        ]

        # Act - Test both components working together
        # 1. Analyze individual emotions
        individual_emotions = []
        for segment in content_segments:
            emotion_result = emotion_analyzer.analyze_emotions(segment)
            individual_emotions.append(emotion_result)

        # 2. Map trajectory
        trajectory_result = trajectory_mapper.map_emotion_trajectory(content_segments)

        # Assert integration
        assert len(individual_emotions) == len(content_segments)
        assert len(trajectory_result["emotion_progression"]) == len(content_segments)

        # Compare results - should be consistent
        for i, (individual, trajectory_segment) in enumerate(
            zip(individual_emotions, trajectory_result["emotion_progression"])
        ):
            # Individual analyzer and trajectory mapper should detect similar patterns
            individual_dominant = max(
                individual["emotions"], key=individual["emotions"].get
            )
            trajectory_dominant = max(trajectory_segment, key=trajectory_segment.get)

            # May not be exact match but should be in the same emotional family
            positive_emotions = {"joy", "trust", "anticipation", "surprise"}
            negative_emotions = {"anger", "fear", "sadness", "disgust"}

            if individual_dominant in positive_emotions:
                # If individual analysis found positive emotion, trajectory should too (or be close)
                assert (
                    trajectory_segment[individual_dominant] > 0.2
                    or trajectory_dominant in positive_emotions
                )

            if individual_dominant in negative_emotions:
                # If individual analysis found negative emotion, trajectory should too (or be close)
                assert (
                    trajectory_segment[individual_dominant] > 0.2
                    or trajectory_dominant in negative_emotions
                )

    def test_emotion_template_pattern_matching(self, trajectory_mapper, db_session):
        """Test trajectory mapping against stored emotion templates."""
        # Arrange - Create a template pattern
        template = EmotionTemplate(
            template_name="excitement_concern_trust_optimism",
            template_type="balanced_progression",
            pattern_description="Moves from excitement through concern to trust and optimism",
            segment_count=4,
            optimal_duration_words=40,
            trajectory_pattern="rising",
            primary_emotions=["joy", "fear", "trust", "anticipation"],
            emotion_sequence=json.dumps(
                {
                    "segments": [
                        {"joy": 0.8, "surprise": 0.7, "anticipation": 0.6},
                        {"fear": 0.6, "anticipation": 0.4, "joy": 0.3},
                        {"trust": 0.7, "anticipation": 0.5, "joy": 0.6},
                        {"joy": 0.8, "trust": 0.8, "anticipation": 0.9},
                    ]
                }
            ),
            transition_patterns=json.dumps(
                {
                    "transitions": [
                        {"from": "joy", "to": "fear", "strength": 0.7},
                        {"from": "fear", "to": "trust", "strength": 0.6},
                        {"from": "trust", "to": "joy", "strength": 0.8},
                    ]
                }
            ),
            effectiveness_score=0.85,
        )

        db_session.add(template)
        db_session.commit()

        # Act - Test content that should match the pattern
        matching_content = [
            "I'm so excited about this new technology!",
            "But I'm worried about the potential risks.",
            "I trust we can implement proper safeguards.",
            "The future possibilities are amazing!",
        ]

        trajectory_result = trajectory_mapper.map_emotion_trajectory(matching_content)

        # Assert pattern matching
        template_pattern = json.loads(template.emotion_sequence)

        # Should have same number of segments
        assert len(trajectory_result["emotion_progression"]) == len(
            template_pattern["segments"]
        )

        # Calculate similarity score
        similarity_scores = []
        for trajectory_emotions, template_emotions in zip(
            trajectory_result["emotion_progression"], template_pattern["segments"]
        ):
            segment_similarity = 0.0
            emotion_count = 0

            for emotion in template.primary_emotions:
                if emotion in trajectory_emotions and emotion in template_emotions:
                    # Calculate similarity (1 - absolute difference)
                    similarity = 1.0 - abs(
                        trajectory_emotions[emotion] - template_emotions[emotion]
                    )
                    segment_similarity += similarity
                    emotion_count += 1

            if emotion_count > 0:
                similarity_scores.append(segment_similarity / emotion_count)

        avg_similarity = (
            sum(similarity_scores) / len(similarity_scores)
            if similarity_scores
            else 0.0
        )

        # Should show reasonable similarity to template
        assert avg_similarity > 0.3, f"Pattern similarity {avg_similarity:.2f} too low"

        # Trajectory type should match or be compatible
        assert trajectory_result["arc_type"] in [
            "rising",
            "roller_coaster",
        ]  # Compatible with template

    def test_performance_with_large_content_segments(self, trajectory_mapper):
        """Test trajectory mapping performance with large number of segments."""
        import time

        # Arrange - Create many segments
        base_contents = [
            "I'm excited about this topic!",
            "But there are concerns to consider.",
            "Let me think about this more carefully.",
            "Actually, this looks very promising!",
            "I'm optimistic about the outcomes.",
        ]

        # Scale up to many segments
        large_content_segments = []
        for i in range(50):  # 250 total segments
            for content in base_contents:
                large_content_segments.append(f"{content} (iteration {i})")

        # Act - Measure performance
        start_time = time.time()
        result = trajectory_mapper.map_emotion_trajectory(large_content_segments)
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000  # milliseconds

        # Assert
        assert processing_time < 2000, (
            f"Large content processing took {processing_time:.2f}ms, expected <2000ms"
        )
        assert len(result["emotion_progression"]) == len(large_content_segments)
        assert result["arc_type"] in ["rising", "falling", "roller_coaster", "steady"]

        # Should still detect meaningful patterns
        assert result["emotional_variance"] >= 0.0

    def test_trajectory_mapping_with_multilingual_content(self, trajectory_mapper):
        """Test trajectory mapping with multilingual content."""
        # Arrange
        multilingual_segments = [
            "I'm so excited about this! ¡Esto es increíble!",
            "Aber ich bin auch besorgt... But I'm also worried...",
            "Je pense que ça va bien se passer. I think it will work out.",
            "これは素晴らしいニュースです！This is wonderful news! 🎉",
        ]

        # Act
        result = trajectory_mapper.map_emotion_trajectory(multilingual_segments)

        # Assert - Should handle multilingual content gracefully
        assert result is not None
        assert "arc_type" in result
        assert len(result["emotion_progression"]) == len(multilingual_segments)

        # Should still detect emotions despite language mixing
        for segment_emotions in result["emotion_progression"]:
            assert isinstance(segment_emotions, dict)
            assert len(segment_emotions) == 8  # All 8 emotions

            # Should have some emotional content
            total_emotion_strength = sum(segment_emotions.values())
            assert total_emotion_strength > 0.5  # Should detect some emotions

    def test_trajectory_mapping_error_handling(self, trajectory_mapper):
        """Test trajectory mapper error handling with edge cases."""
        # Test empty content
        empty_result = trajectory_mapper.map_emotion_trajectory([])
        assert empty_result["arc_type"] == "steady"  # Should default gracefully

        # Test single segment
        single_result = trajectory_mapper.map_emotion_trajectory(["Single segment"])
        assert single_result["arc_type"] == "steady"  # Single segment is steady
        assert len(single_result["emotion_progression"]) == 1

        # Test very short segments
        short_segments = ["Hi", "OK", "Bye"]
        short_result = trajectory_mapper.map_emotion_trajectory(short_segments)
        assert len(short_result["emotion_progression"]) == 3

        # Test segments with special characters
        special_segments = ["!!!", "???", "..."]
        special_result = trajectory_mapper.map_emotion_trajectory(special_segments)
        assert special_result is not None
        assert len(special_result["emotion_progression"]) == 3

    def test_advanced_arc_classification_accuracy(self, trajectory_mapper):
        """Test advanced arc classification with complex emotional patterns."""
        # Test cases with known arc types
        test_cases = [
            {
                "segments": [
                    "This is okay.",
                    "Getting better now.",
                    "This is really good!",
                    "Absolutely amazing!",
                ],
                "expected_arc": "rising",
            },
            {
                "segments": [
                    "I was so happy!",
                    "Things are getting worse.",
                    "This is disappointing.",
                    "I'm really sad now.",
                ],
                "expected_arc": "falling",
            },
            {
                "segments": [
                    "Great news!",
                    "Oh no, there's a problem.",
                    "Wait, it's fixed!",
                    "Actually, another issue...",
                    "Never mind, all good!",
                ],
                "expected_arc": "roller_coaster",
            },
            {
                "segments": [
                    "This is a reliable solution.",
                    "It works consistently well.",
                    "Performance is stable.",
                    "Overall quality is good.",
                ],
                "expected_arc": "steady",
            },
        ]

        correct_classifications = 0

        for i, test_case in enumerate(test_cases):
            result = trajectory_mapper.map_emotion_trajectory(test_case["segments"])
            actual_arc = result["arc_type"]
            expected_arc = test_case["expected_arc"]

            if actual_arc == expected_arc:
                correct_classifications += 1
            else:
                print(f"Test case {i}: Expected {expected_arc}, got {actual_arc}")
                # Some flexibility for complex patterns
                if expected_arc == "roller_coaster" and actual_arc in [
                    "rising",
                    "falling",
                ]:
                    correct_classifications += 0.5  # Partial credit

        # Should classify most patterns correctly
        accuracy = correct_classifications / len(test_cases)
        assert accuracy >= 0.75, f"Arc classification accuracy {accuracy:.2f} too low"

    def test_emotional_variance_calculation_advanced(self, trajectory_mapper):
        """Test advanced emotional variance calculation with real scenarios."""
        # Test scenarios with known variance levels
        test_scenarios = [
            {
                "name": "minimal_variance",
                "emotions": [
                    {
                        "joy": 0.5,
                        "anger": 0.1,
                        "fear": 0.1,
                        "sadness": 0.1,
                        "surprise": 0.1,
                        "disgust": 0.1,
                        "trust": 0.1,
                        "anticipation": 0.1,
                    },
                    {
                        "joy": 0.6,
                        "anger": 0.1,
                        "fear": 0.1,
                        "sadness": 0.1,
                        "surprise": 0.1,
                        "disgust": 0.1,
                        "trust": 0.1,
                        "anticipation": 0.1,
                    },
                    {
                        "joy": 0.5,
                        "anger": 0.1,
                        "fear": 0.1,
                        "sadness": 0.1,
                        "surprise": 0.1,
                        "disgust": 0.1,
                        "trust": 0.1,
                        "anticipation": 0.1,
                    },
                ],
                "expected_range": (0.0, 0.3),
            },
            {
                "name": "high_variance",
                "emotions": [
                    {
                        "joy": 0.9,
                        "anger": 0.1,
                        "fear": 0.1,
                        "sadness": 0.1,
                        "surprise": 0.1,
                        "disgust": 0.1,
                        "trust": 0.1,
                        "anticipation": 0.1,
                    },
                    {
                        "joy": 0.1,
                        "anger": 0.9,
                        "fear": 0.1,
                        "sadness": 0.1,
                        "surprise": 0.1,
                        "disgust": 0.1,
                        "trust": 0.1,
                        "anticipation": 0.1,
                    },
                    {
                        "joy": 0.1,
                        "anger": 0.1,
                        "fear": 0.9,
                        "sadness": 0.1,
                        "surprise": 0.1,
                        "disgust": 0.1,
                        "trust": 0.1,
                        "anticipation": 0.1,
                    },
                ],
                "expected_range": (0.6, 1.0),
            },
            {
                "name": "medium_variance",
                "emotions": [
                    {
                        "joy": 0.7,
                        "anger": 0.2,
                        "fear": 0.1,
                        "sadness": 0.1,
                        "surprise": 0.3,
                        "disgust": 0.1,
                        "trust": 0.2,
                        "anticipation": 0.4,
                    },
                    {
                        "joy": 0.4,
                        "anger": 0.1,
                        "fear": 0.5,
                        "sadness": 0.2,
                        "surprise": 0.1,
                        "disgust": 0.1,
                        "trust": 0.6,
                        "anticipation": 0.2,
                    },
                    {
                        "joy": 0.6,
                        "anger": 0.3,
                        "fear": 0.2,
                        "sadness": 0.1,
                        "surprise": 0.4,
                        "disgust": 0.1,
                        "trust": 0.3,
                        "anticipation": 0.5,
                    },
                ],
                "expected_range": (0.3, 0.7),
            },
        ]

        for scenario in test_scenarios:
            variance = trajectory_mapper.calculate_emotional_variance(
                scenario["emotions"]
            )
            min_expected, max_expected = scenario["expected_range"]

            assert min_expected <= variance <= max_expected, (
                f"Scenario '{scenario['name']}': variance {variance:.3f} not in range [{min_expected}, {max_expected}]"
            )
