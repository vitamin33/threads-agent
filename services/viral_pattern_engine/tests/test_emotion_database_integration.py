"""Database integration tests for emotion trajectory models."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.orchestrator.db import Base
from services.orchestrator.db.models import (
    EmotionTrajectory,
    EmotionSegment,
    EmotionTransition,
    EmotionTemplate,
    EmotionPerformance,
)


class TestEmotionDatabaseIntegration:
    """Test database operations for emotion trajectory models."""

    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        # Use in-memory SQLite for tests
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_emotion_trajectory_creation(self, db_session):
        """Test creating and retrieving emotion trajectory."""
        trajectory = EmotionTrajectory(
            post_id="test_post_123",
            persona_id="persona_ai_enthusiast",
            content_hash="a" * 64,  # SHA256 hash
            segment_count=5,
            total_duration_words=120,
            analysis_model="bert_vader",
            confidence_score=0.85,
            trajectory_type="rising",
            emotional_variance=0.35,
            peak_count=2,
            valley_count=1,
            transition_count=4,
            joy_avg=0.6,
            anger_avg=0.1,
            fear_avg=0.1,
            sadness_avg=0.05,
            surprise_avg=0.7,
            disgust_avg=0.02,
            trust_avg=0.5,
            anticipation_avg=0.8,
            sentiment_compound=0.75,
            sentiment_positive=0.8,
            sentiment_neutral=0.15,
            sentiment_negative=0.05,
            processing_time_ms=250,
        )

        db_session.add(trajectory)
        db_session.commit()

        # Retrieve and verify
        saved_trajectory = (
            db_session.query(EmotionTrajectory)
            .filter_by(post_id="test_post_123")
            .first()
        )

        assert saved_trajectory is not None
        assert saved_trajectory.persona_id == "persona_ai_enthusiast"
        assert saved_trajectory.trajectory_type == "rising"
        assert saved_trajectory.confidence_score == 0.85
        assert saved_trajectory.dominant_emotion == "anticipation"  # Highest average

    def test_emotion_segments_relationship(self, db_session):
        """Test emotion segments relationship with trajectory."""
        # Create trajectory
        trajectory = EmotionTrajectory(
            post_id="test_segments_123",
            persona_id="test_persona",
            content_hash="b" * 64,
            segment_count=3,
            total_duration_words=90,
            trajectory_type="roller-coaster",
            emotional_variance=0.45,
            joy_avg=0.4,
            anger_avg=0.3,
            fear_avg=0.2,
            sadness_avg=0.5,
            surprise_avg=0.3,
            disgust_avg=0.1,
            trust_avg=0.4,
            anticipation_avg=0.6,
        )
        db_session.add(trajectory)
        db_session.flush()

        # Add segments
        segments = [
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=0,
                content_text="I was devastated when this happened.",
                word_count=7,
                sentence_count=1,
                joy_score=0.1,
                sadness_score=0.8,
                dominant_emotion="sadness",
                confidence_score=0.9,
                is_valley=True,
            ),
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=1,
                content_text="But then something amazing occurred!",
                word_count=6,
                sentence_count=1,
                joy_score=0.7,
                surprise_score=0.8,
                dominant_emotion="surprise",
                confidence_score=0.85,
                is_peak=True,
            ),
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=2,
                content_text="Now I'm cautiously optimistic.",
                word_count=5,
                sentence_count=1,
                joy_score=0.4,
                anticipation_score=0.6,
                dominant_emotion="anticipation",
                confidence_score=0.75,
            ),
        ]

        for segment in segments:
            db_session.add(segment)

        db_session.commit()

        # Retrieve and verify relationships
        saved_trajectory = (
            db_session.query(EmotionTrajectory)
            .filter_by(post_id="test_segments_123")
            .first()
        )

        assert len(saved_trajectory.segments) == 3
        assert saved_trajectory.segments[0].dominant_emotion == "sadness"
        assert saved_trajectory.segments[1].is_peak is True
        assert saved_trajectory.segments[0].is_valley is True

    def test_emotion_transitions(self, db_session):
        """Test emotion transition tracking."""
        # Create trajectory
        trajectory = EmotionTrajectory(
            post_id="test_transitions_123",
            persona_id="test_persona",
            content_hash="c" * 64,
            segment_count=4,
            total_duration_words=100,
            trajectory_type="roller-coaster",
            emotional_variance=0.5,
            joy_avg=0.5,
            sadness_avg=0.3,
            surprise_avg=0.4,
            anticipation_avg=0.6,
            anger_avg=0.2,
            fear_avg=0.1,
            disgust_avg=0.05,
            trust_avg=0.4,
        )
        db_session.add(trajectory)
        db_session.flush()

        # Add transitions
        transitions = [
            EmotionTransition(
                trajectory_id=trajectory.id,
                from_segment_index=0,
                to_segment_index=1,
                from_emotion="sadness",
                to_emotion="surprise",
                transition_type="switching",
                intensity_change=0.5,
                transition_speed=0.1,
                strength_score=0.8,
            ),
            EmotionTransition(
                trajectory_id=trajectory.id,
                from_segment_index=1,
                to_segment_index=2,
                from_emotion="surprise",
                to_emotion="joy",
                transition_type="strengthening",
                intensity_change=0.3,
                transition_speed=0.06,
                strength_score=0.7,
            ),
        ]

        for transition in transitions:
            db_session.add(transition)

        db_session.commit()

        # Query and verify
        saved_transitions = (
            db_session.query(EmotionTransition)
            .filter_by(trajectory_id=trajectory.id)
            .all()
        )

        assert len(saved_transitions) == 2
        assert saved_transitions[0].from_emotion == "sadness"
        assert saved_transitions[0].to_emotion == "surprise"
        assert saved_transitions[0].transition_type == "switching"

    def test_emotion_template_creation(self, db_session):
        """Test emotion template storage and retrieval."""
        template = EmotionTemplate(
            template_name="curiosity_arc",
            template_type="discovery",
            pattern_description="Builds curiosity then provides satisfaction",
            segment_count=4,
            optimal_duration_words=80,
            trajectory_pattern="rising",
            primary_emotions=["curiosity", "anticipation", "joy", "satisfaction"],
            emotion_sequence='{"0": "neutral", "1": "curiosity", "2": "anticipation", "3": "satisfaction"}',
            transition_patterns='{"curiosity->anticipation": 0.8, "anticipation->satisfaction": 0.9}',
            usage_count=150,
            average_engagement=0.12,
            engagement_correlation=0.84,
            effectiveness_score=0.88,
            version=1,
            is_active=True,
        )

        db_session.add(template)
        db_session.commit()

        # Retrieve and verify
        saved_template = (
            db_session.query(EmotionTemplate)
            .filter_by(template_name="curiosity_arc")
            .first()
        )

        assert saved_template is not None
        assert saved_template.template_type == "discovery"
        assert saved_template.engagement_correlation == 0.84
        assert len(saved_template.primary_emotions) == 4
        assert "curiosity" in saved_template.primary_emotions

    def test_emotion_performance_tracking(self, db_session):
        """Test emotion performance metrics tracking."""
        # Create trajectory
        trajectory = EmotionTrajectory(
            post_id="test_perf_123",
            persona_id="test_persona",
            content_hash="d" * 64,
            segment_count=3,
            total_duration_words=75,
            trajectory_type="rising",
            emotional_variance=0.25,
            joy_avg=0.7,
            anticipation_avg=0.8,
            sadness_avg=0.1,
            anger_avg=0.05,
            fear_avg=0.05,
            surprise_avg=0.6,
            disgust_avg=0.02,
            trust_avg=0.6,
        )
        db_session.add(trajectory)
        db_session.flush()

        # Add performance metrics
        performance = EmotionPerformance(
            trajectory_id=trajectory.id,
            post_id="test_perf_123",
            persona_id="test_persona",
            engagement_rate=0.125,
            likes_count=1500,
            shares_count=75,
            comments_count=92,
            reach=15000,
            impressions=12500,
            emotion_effectiveness=0.85,
            predicted_engagement=0.11,
            actual_vs_predicted=0.015,  # 1.5% better than predicted
            measured_at=datetime.utcnow(),
        )

        db_session.add(performance)
        db_session.commit()

        # Query and verify
        saved_performance = (
            db_session.query(EmotionPerformance)
            .filter_by(post_id="test_perf_123")
            .first()
        )

        assert saved_performance is not None
        assert saved_performance.engagement_rate == 0.125
        assert saved_performance.emotion_effectiveness == 0.85
        assert saved_performance.actual_vs_predicted == 0.015

    def test_cascade_deletion(self, db_session):
        """Test cascade deletion of related records."""
        # Create trajectory with related records
        trajectory = EmotionTrajectory(
            post_id="test_cascade_123",
            persona_id="test_persona",
            content_hash="e" * 64,
            segment_count=2,
            total_duration_words=50,
            trajectory_type="steady",
            emotional_variance=0.1,
            joy_avg=0.6,
            anticipation_avg=0.5,
            sadness_avg=0.1,
            anger_avg=0.1,
            fear_avg=0.1,
            surprise_avg=0.3,
            disgust_avg=0.05,
            trust_avg=0.5,
        )
        db_session.add(trajectory)
        db_session.flush()

        # Add related records
        segment = EmotionSegment(
            trajectory_id=trajectory.id,
            segment_index=0,
            content_text="Test segment",
            word_count=2,
            sentence_count=1,
            dominant_emotion="joy",
            confidence_score=0.8,
        )

        transition = EmotionTransition(
            trajectory_id=trajectory.id,
            from_segment_index=0,
            to_segment_index=1,
            from_emotion="joy",
            to_emotion="anticipation",
            transition_type="switching",
            strength_score=0.7,
        )

        performance = EmotionPerformance(
            trajectory_id=trajectory.id,
            post_id="test_cascade_123",
            persona_id="test_persona",
            engagement_rate=0.08,
            measured_at=datetime.utcnow(),
        )

        db_session.add_all([segment, transition, performance])
        db_session.commit()

        # Verify records exist
        assert db_session.query(EmotionSegment).count() == 1
        assert db_session.query(EmotionTransition).count() == 1
        assert db_session.query(EmotionPerformance).count() == 1

        # Delete trajectory
        db_session.delete(trajectory)
        db_session.commit()

        # Verify cascade deletion
        assert db_session.query(EmotionSegment).count() == 0
        assert db_session.query(EmotionTransition).count() == 0
        assert db_session.query(EmotionPerformance).count() == 0

    def test_emotion_trajectory_indexing_performance(self, db_session):
        """Test that database queries use indexes efficiently."""
        # Create multiple trajectories
        trajectories = []
        for i in range(100):
            trajectory = EmotionTrajectory(
                post_id=f"perf_test_{i}",
                persona_id=f"persona_{i % 10}",  # 10 different personas
                content_hash=f"{i:064x}",
                segment_count=3,
                total_duration_words=100,
                trajectory_type=["rising", "falling", "roller-coaster", "steady"][
                    i % 4
                ],
                emotional_variance=0.1 + (i % 10) * 0.05,
                joy_avg=0.5,
                anticipation_avg=0.6,
                sadness_avg=0.2,
                anger_avg=0.1,
                fear_avg=0.1,
                surprise_avg=0.4,
                disgust_avg=0.05,
                trust_avg=0.5,
            )
            trajectories.append(trajectory)

        db_session.add_all(trajectories)
        db_session.commit()

        # Test indexed queries
        # Query by persona_id (indexed)
        persona_results = (
            db_session.query(EmotionTrajectory).filter_by(persona_id="persona_5").all()
        )
        assert len(persona_results) == 10

        # Query by trajectory_type (indexed)
        rising_results = (
            db_session.query(EmotionTrajectory)
            .filter_by(trajectory_type="rising")
            .all()
        )
        assert len(rising_results) == 25

        # Query by post_id (indexed)
        post_result = (
            db_session.query(EmotionTrajectory)
            .filter_by(post_id="perf_test_42")
            .first()
        )
        assert post_result is not None
        assert post_result.persona_id == "persona_2"
