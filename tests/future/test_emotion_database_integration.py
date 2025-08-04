"""Database integration tests for emotion trajectory models."""

import pytest
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from services.orchestrator.db.models import (
    EmotionTrajectory,
    EmotionSegment,
    EmotionTransition,
    EmotionTemplate,
    EmotionPerformance,
)


@pytest.mark.e2e
class TestEmotionDatabaseIntegration:
    """Test database operations for emotion trajectory models."""

    def test_create_emotion_trajectory_with_segments(self, db_session: Session):
        """Test creating emotion trajectory with related segments."""
        # Arrange
        content_hash = hashlib.sha256("test content".encode()).hexdigest()

        trajectory = EmotionTrajectory(
            post_id="test_post_123",
            persona_id="viral_creator",
            content_hash=content_hash,
            segment_count=3,
            total_duration_words=150,
            analysis_model="bert_vader",
            confidence_score=0.85,
            trajectory_type="rising",
            emotional_variance=0.42,
            peak_count=2,
            valley_count=1,
            transition_count=2,
            joy_avg=0.7,
            anger_avg=0.1,
            fear_avg=0.15,
            sadness_avg=0.2,
            surprise_avg=0.45,
            disgust_avg=0.05,
            trust_avg=0.8,
            anticipation_avg=0.6,
            sentiment_compound=0.65,
            sentiment_positive=0.75,
            sentiment_neutral=0.15,
            sentiment_negative=0.1,
            processing_time_ms=245,
        )

        db_session.add(trajectory)
        db_session.flush()  # Get the ID without committing

        # Add segments
        segments = [
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=0,
                content_text="Let me tell you about this amazing discovery.",
                word_count=8,
                sentence_count=1,
                joy_score=0.6,
                anger_score=0.1,
                fear_score=0.1,
                sadness_score=0.1,
                surprise_score=0.3,
                disgust_score=0.05,
                trust_score=0.75,
                anticipation_score=0.5,
                sentiment_compound=0.5,
                sentiment_positive=0.7,
                sentiment_neutral=0.2,
                sentiment_negative=0.1,
                dominant_emotion="trust",
                confidence_score=0.8,
                is_peak=False,
                is_valley=False,
            ),
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=1,
                content_text="This is getting really exciting now!",
                word_count=6,
                sentence_count=1,
                joy_score=0.8,
                anger_score=0.1,
                fear_score=0.1,
                sadness_score=0.1,
                surprise_score=0.6,
                disgust_score=0.05,
                trust_score=0.8,
                anticipation_score=0.7,
                sentiment_compound=0.75,
                sentiment_positive=0.8,
                sentiment_neutral=0.1,
                sentiment_negative=0.1,
                dominant_emotion="joy",
                confidence_score=0.9,
                is_peak=True,
                is_valley=False,
            ),
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=2,
                content_text="OMG this is absolutely incredible!",
                word_count=5,
                sentence_count=1,
                joy_score=0.9,
                anger_score=0.05,
                fear_score=0.05,
                sadness_score=0.05,
                surprise_score=0.85,
                disgust_score=0.05,
                trust_score=0.85,
                anticipation_score=0.8,
                sentiment_compound=0.9,
                sentiment_positive=0.95,
                sentiment_neutral=0.05,
                sentiment_negative=0.0,
                dominant_emotion="joy",
                confidence_score=0.95,
                is_peak=True,
                is_valley=False,
            ),
        ]

        for segment in segments:
            db_session.add(segment)

        # Act
        db_session.commit()

        # Assert
        retrieved_trajectory = db_session.get(EmotionTrajectory, trajectory.id)
        assert retrieved_trajectory is not None
        assert retrieved_trajectory.post_id == "test_post_123"
        assert retrieved_trajectory.trajectory_type == "rising"
        assert retrieved_trajectory.dominant_emotion == "trust"
        assert len(retrieved_trajectory.segments) == 3

        # Check segment ordering
        ordered_segments = sorted(
            retrieved_trajectory.segments, key=lambda s: s.segment_index
        )
        assert ordered_segments[0].dominant_emotion == "trust"
        assert ordered_segments[1].dominant_emotion == "joy"
        assert ordered_segments[2].dominant_emotion == "joy"

        # Check peak detection
        peak_segments = [s for s in retrieved_trajectory.segments if s.is_peak]
        assert len(peak_segments) == 2

    def test_emotion_transitions_relationship(self, db_session: Session):
        """Test emotion transitions with proper relationships."""
        # Arrange
        trajectory = EmotionTrajectory(
            post_id="test_post_456",
            persona_id="viral_creator",
            content_hash=hashlib.sha256("transition test".encode()).hexdigest(),
            segment_count=3,
            total_duration_words=100,
            trajectory_type="roller_coaster",
            emotional_variance=0.75,
            peak_count=1,
            valley_count=1,
            transition_count=2,
            joy_avg=0.5,
            sadness_avg=0.3,
        )

        db_session.add(trajectory)
        db_session.flush()

        transitions = [
            EmotionTransition(
                trajectory_id=trajectory.id,
                from_segment_index=0,
                to_segment_index=1,
                from_emotion="joy",
                to_emotion="sadness",
                transition_type="joy_to_sadness",
                intensity_change=-0.4,
                transition_speed=0.8,
                strength_score=0.65,
            ),
            EmotionTransition(
                trajectory_id=trajectory.id,
                from_segment_index=1,
                to_segment_index=2,
                from_emotion="sadness",
                to_emotion="joy",
                transition_type="sadness_to_joy",
                intensity_change=0.5,
                transition_speed=0.9,
                strength_score=0.75,
            ),
        ]

        for transition in transitions:
            db_session.add(transition)

        # Act
        db_session.commit()

        # Assert
        retrieved_trajectory = db_session.get(EmotionTrajectory, trajectory.id)
        assert len(retrieved_trajectory.transitions) == 2

        # Check transition ordering
        ordered_transitions = sorted(
            retrieved_trajectory.transitions, key=lambda t: t.from_segment_index
        )
        assert ordered_transitions[0].from_emotion == "joy"
        assert ordered_transitions[0].to_emotion == "sadness"
        assert ordered_transitions[1].from_emotion == "sadness"
        assert ordered_transitions[1].to_emotion == "joy"

    def test_emotion_template_creation_and_retrieval(self, db_session: Session):
        """Test emotion template model with complex patterns."""
        # Arrange
        template = EmotionTemplate(
            template_name="Classic Hook-Build-Payoff",
            template_type="narrative_arc",
            pattern_description="A classic storytelling pattern that builds emotional tension before a satisfying resolution",
            segment_count=4,
            optimal_duration_words=200,
            trajectory_pattern="rising",
            primary_emotions=["anticipation", "surprise", "joy"],
            emotion_sequence='{"segments": [{"anticipation": 0.8}, {"anticipation": 0.9}, {"surprise": 0.85}, {"joy": 0.9}]}',
            transition_patterns='{"transitions": ["anticipation_to_anticipation", "anticipation_to_surprise", "surprise_to_joy"]}',
            usage_count=0,
            average_engagement=0.0,
            engagement_correlation=0.0,
            effectiveness_score=0.0,
            version=1,
            is_active=True,
        )

        # Act
        db_session.add(template)
        db_session.commit()

        # Assert
        retrieved_template = db_session.get(EmotionTemplate, template.id)
        assert retrieved_template is not None
        assert retrieved_template.template_name == "Classic Hook-Build-Payoff"
        assert retrieved_template.primary_emotions == [
            "anticipation",
            "surprise",
            "joy",
        ]
        assert retrieved_template.is_active is True

        # Test querying by template type
        narrative_templates = db_session.scalars(
            select(EmotionTemplate).where(
                EmotionTemplate.template_type == "narrative_arc"
            )
        ).all()
        assert len(narrative_templates) == 1
        assert narrative_templates[0].id == template.id

    def test_emotion_performance_metrics(self, db_session: Session):
        """Test emotion performance tracking with engagement metrics."""
        # Arrange
        trajectory = EmotionTrajectory(
            post_id="test_post_789",
            persona_id="viral_creator",
            content_hash=hashlib.sha256("performance test".encode()).hexdigest(),
            segment_count=2,
            total_duration_words=80,
            trajectory_type="steady",
            joy_avg=0.6,
            trust_avg=0.7,
        )

        db_session.add(trajectory)
        db_session.flush()

        performance = EmotionPerformance(
            trajectory_id=trajectory.id,
            post_id="test_post_789",
            persona_id="viral_creator",
            engagement_rate=0.08,  # 8% engagement rate
            likes_count=150,
            shares_count=25,
            comments_count=40,
            reach=2000,
            impressions=2500,
            emotion_effectiveness=0.72,
            predicted_engagement=0.075,
            actual_vs_predicted=0.005,  # Slight overperformance
            measured_at=datetime.utcnow(),
        )

        # Act
        db_session.add(performance)
        db_session.commit()

        # Assert
        retrieved_trajectory = db_session.get(EmotionTrajectory, trajectory.id)
        assert len(retrieved_trajectory.performance) == 1

        perf = retrieved_trajectory.performance[0]
        assert perf.engagement_rate == 0.08
        assert perf.likes_count == 150
        assert perf.emotion_effectiveness == 0.72
        assert perf.actual_vs_predicted > 0  # Outperformed prediction

    def test_cascade_delete_relationships(self, db_session: Session):
        """Test that deleting trajectory cascades to related records."""
        # Arrange
        trajectory = EmotionTrajectory(
            post_id="test_cascade",
            persona_id="test_persona",
            content_hash=hashlib.sha256("cascade test".encode()).hexdigest(),
            segment_count=2,
            total_duration_words=50,
            trajectory_type="steady",
        )

        db_session.add(trajectory)
        db_session.flush()

        segment = EmotionSegment(
            trajectory_id=trajectory.id,
            segment_index=0,
            content_text="Test segment",
            word_count=2,
            sentence_count=1,
            dominant_emotion="joy",
            confidence_score=0.5,
        )

        transition = EmotionTransition(
            trajectory_id=trajectory.id,
            from_segment_index=0,
            to_segment_index=1,
            from_emotion="joy",
            to_emotion="trust",
            transition_type="joy_to_trust",
            strength_score=0.3,
        )

        performance = EmotionPerformance(
            trajectory_id=trajectory.id,
            post_id="test_cascade",
            persona_id="test_persona",
            engagement_rate=0.05,
            measured_at=datetime.utcnow(),
        )

        db_session.add_all([segment, transition, performance])
        db_session.commit()

        trajectory_id = trajectory.id

        # Act - Delete the trajectory
        db_session.delete(trajectory)
        db_session.commit()

        # Assert - Related records should be deleted
        assert db_session.get(EmotionTrajectory, trajectory_id) is None

        remaining_segments = db_session.scalars(
            select(EmotionSegment).where(EmotionSegment.trajectory_id == trajectory_id)
        ).all()
        assert len(remaining_segments) == 0

        remaining_transitions = db_session.scalars(
            select(EmotionTransition).where(
                EmotionTransition.trajectory_id == trajectory_id
            )
        ).all()
        assert len(remaining_transitions) == 0

        remaining_performance = db_session.scalars(
            select(EmotionPerformance).where(
                EmotionPerformance.trajectory_id == trajectory_id
            )
        ).all()
        assert len(remaining_performance) == 0

    def test_emotion_trajectory_queries_with_indexes(self, db_session: Session):
        """Test optimized queries using database indexes."""
        # Arrange - Create multiple trajectories for different personas
        trajectories = []
        for i in range(5):
            trajectory = EmotionTrajectory(
                post_id=f"post_{i}",
                persona_id="viral_creator" if i % 2 == 0 else "storyteller",
                content_hash=hashlib.sha256(f"content_{i}".encode()).hexdigest(),
                segment_count=3,
                total_duration_words=100 + i * 10,
                trajectory_type="rising" if i % 2 == 0 else "falling",
                joy_avg=0.5 + i * 0.1,
                created_at=datetime.utcnow() - timedelta(days=i),
            )
            trajectories.append(trajectory)

        db_session.add_all(trajectories)
        db_session.commit()

        # Act & Assert - Test indexed queries

        # Query by persona_id (indexed)
        viral_creator_trajectories = db_session.scalars(
            select(EmotionTrajectory).where(
                EmotionTrajectory.persona_id == "viral_creator"
            )
        ).all()
        assert len(viral_creator_trajectories) == 3

        # Query by trajectory_type (indexed)
        rising_trajectories = db_session.scalars(
            select(EmotionTrajectory).where(
                EmotionTrajectory.trajectory_type == "rising"
            )
        ).all()
        assert len(rising_trajectories) == 3

        # Query by created_at (indexed) - recent trajectories
        recent_cutoff = datetime.utcnow() - timedelta(days=2)
        recent_trajectories = db_session.scalars(
            select(EmotionTrajectory).where(
                EmotionTrajectory.created_at >= recent_cutoff
            )
        ).all()
        assert len(recent_trajectories) >= 2

    def test_emotion_template_effectiveness_tracking(self, db_session: Session):
        """Test template effectiveness scoring and updates."""
        # Arrange
        template = EmotionTemplate(
            template_name="Viral Cliffhanger",
            template_type="engagement_hook",
            pattern_description="Creates suspense to drive engagement",
            segment_count=3,
            optimal_duration_words=120,
            trajectory_pattern="roller_coaster",
            primary_emotions=["anticipation", "surprise"],
            emotion_sequence='{"pattern": "anticipation_peak"}',
            transition_patterns='{"main": "anticipation_to_surprise"}',
            usage_count=10,
            average_engagement=0.12,
            engagement_correlation=0.73,
            effectiveness_score=0.85,
            version=1,
            is_active=True,
        )

        db_session.add(template)
        db_session.commit()

        # Act - Update effectiveness metrics
        template.usage_count += 5
        template.average_engagement = 0.135  # Improved engagement
        template.effectiveness_score = 0.88  # Higher effectiveness
        db_session.commit()

        # Assert
        retrieved_template = db_session.get(EmotionTemplate, template.id)
        assert retrieved_template.usage_count == 15
        assert retrieved_template.average_engagement == 0.135
        assert retrieved_template.effectiveness_score == 0.88

        # Test querying high-performing templates
        high_performing = db_session.scalars(
            select(EmotionTemplate)
            .where(EmotionTemplate.effectiveness_score >= 0.8)
            .where(EmotionTemplate.is_active)
        ).all()
        assert len(high_performing) >= 1
        assert template.id in [t.id for t in high_performing]

    def test_emotion_segment_peak_valley_queries(self, db_session: Session):
        """Test querying segments by peak/valley status."""
        # Arrange
        trajectory = EmotionTrajectory(
            post_id="peak_valley_test",
            persona_id="test_persona",
            content_hash=hashlib.sha256("peak valley content".encode()).hexdigest(),
            segment_count=5,
            total_duration_words=150,
            trajectory_type="roller_coaster",
            peak_count=2,
            valley_count=1,
        )

        db_session.add(trajectory)
        db_session.flush()

        segments = [
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=0,
                content_text="Starting neutral",
                word_count=2,
                sentence_count=1,
                dominant_emotion="trust",
                confidence_score=0.5,
                is_peak=False,
                is_valley=False,
            ),
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=1,
                content_text="Peak excitement!",
                word_count=2,
                sentence_count=1,
                dominant_emotion="joy",
                confidence_score=0.9,
                is_peak=True,
                is_valley=False,
            ),
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=2,
                content_text="Valley of sadness",
                word_count=3,
                sentence_count=1,
                dominant_emotion="sadness",
                confidence_score=0.8,
                is_peak=False,
                is_valley=True,
            ),
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=3,
                content_text="Another peak!",
                word_count=2,
                sentence_count=1,
                dominant_emotion="surprise",
                confidence_score=0.85,
                is_peak=True,
                is_valley=False,
            ),
            EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=4,
                content_text="Ending resolution",
                word_count=2,
                sentence_count=1,
                dominant_emotion="trust",
                confidence_score=0.7,
                is_peak=False,
                is_valley=False,
            ),
        ]

        db_session.add_all(segments)
        db_session.commit()

        # Act & Assert

        # Query peaks (indexed)
        peak_segments = db_session.scalars(
            select(EmotionSegment).where(EmotionSegment.is_peak)
        ).all()
        assert len(peak_segments) == 2
        assert all(s.is_peak for s in peak_segments)

        # Query valleys (indexed)
        valley_segments = db_session.scalars(
            select(EmotionSegment).where(EmotionSegment.is_valley)
        ).all()
        assert len(valley_segments) == 1
        assert valley_segments[0].dominant_emotion == "sadness"

        # Query by dominant emotion (indexed)
        joy_segments = db_session.scalars(
            select(EmotionSegment).where(EmotionSegment.dominant_emotion == "joy")
        ).all()
        assert len(joy_segments) == 1
        assert joy_segments[0].is_peak is True
