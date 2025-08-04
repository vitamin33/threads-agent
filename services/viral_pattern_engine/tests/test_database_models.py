"""Database integration tests for CRA-282 emotion trajectory SQLAlchemy models."""

import pytest
from datetime import datetime, timedelta
import hashlib

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.orchestrator.db import Base
from services.orchestrator.db.models import (
    EmotionTrajectory,
    EmotionSegment,
    EmotionTransition,
    EmotionTemplate,
    EmotionPerformance,
)


class TestEmotionTrajectoryModels:
    """Test cases for emotion trajectory database models."""

    @pytest.fixture
    def db_engine(self):
        """Create in-memory SQLite database for testing."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={
                "check_same_thread": False,
            },
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
    def sample_trajectory_data(self):
        """Sample data for emotion trajectory testing."""
        content = "I'm so excited about this amazing discovery! But I'm also worried about the implications."
        return {
            "post_id": "post_12345",
            "persona_id": "tech_enthusiast",
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "segment_count": 2,
            "total_duration_words": 15,
            "analysis_model": "bert_vader",
            "confidence_score": 0.85,
            "trajectory_type": "roller_coaster",
            "emotional_variance": 0.67,
            "peak_count": 1,
            "valley_count": 1,
            "transition_count": 1,
            # Emotion averages
            "joy_avg": 0.7,
            "anger_avg": 0.1,
            "fear_avg": 0.4,
            "sadness_avg": 0.2,
            "surprise_avg": 0.6,
            "disgust_avg": 0.1,
            "trust_avg": 0.3,
            "anticipation_avg": 0.5,
            # VADER sentiment
            "sentiment_compound": 0.25,
            "sentiment_positive": 0.6,
            "sentiment_neutral": 0.2,
            "sentiment_negative": 0.2,
            "processing_time_ms": 245,
        }

    def test_emotion_trajectory_creation_and_persistence(
        self, db_session, sample_trajectory_data
    ):
        """Test creating and persisting EmotionTrajectory model."""
        # Arrange
        trajectory = EmotionTrajectory(**sample_trajectory_data)

        # Act
        db_session.add(trajectory)
        db_session.commit()
        db_session.refresh(trajectory)

        # Assert
        assert trajectory.id is not None
        assert trajectory.post_id == "post_12345"
        assert trajectory.persona_id == "tech_enthusiast"
        assert trajectory.segment_count == 2
        assert trajectory.trajectory_type == "roller_coaster"
        assert trajectory.confidence_score == 0.85
        assert trajectory.joy_avg == 0.7
        assert trajectory.processing_time_ms == 245
        assert trajectory.created_at is not None
        assert trajectory.updated_at is not None

    def test_emotion_trajectory_dominant_emotion_property(
        self, db_session, sample_trajectory_data
    ):
        """Test dominant_emotion hybrid property calculation."""
        # Arrange - modify data to have clear dominant emotion
        sample_trajectory_data.update(
            {
                "joy_avg": 0.9,
                "anger_avg": 0.1,
                "fear_avg": 0.2,
                "sadness_avg": 0.1,
                "surprise_avg": 0.3,
                "disgust_avg": 0.1,
                "trust_avg": 0.4,
                "anticipation_avg": 0.2,
            }
        )
        trajectory = EmotionTrajectory(**sample_trajectory_data)

        # Act
        db_session.add(trajectory)
        db_session.commit()

        # Assert
        assert trajectory.dominant_emotion == "joy"

    def test_emotion_trajectory_relationships_cascade(
        self, db_session, sample_trajectory_data
    ):
        """Test cascade delete functionality for trajectory relationships."""
        # Arrange - Create trajectory with related records
        trajectory = EmotionTrajectory(**sample_trajectory_data)
        db_session.add(trajectory)
        db_session.flush()

        # Add segments
        segment1 = EmotionSegment(
            trajectory_id=trajectory.id,
            segment_index=0,
            content_text="I'm so excited about this amazing discovery!",
            word_count=8,
            sentence_count=1,
            joy_score=0.9,
            anger_score=0.1,
            fear_score=0.1,
            sadness_score=0.1,
            surprise_score=0.8,
            disgust_score=0.1,
            trust_score=0.3,
            anticipation_score=0.6,
            sentiment_compound=0.8,
            sentiment_positive=0.9,
            sentiment_neutral=0.1,
            sentiment_negative=0.0,
            dominant_emotion="joy",
            confidence_score=0.9,
            is_peak=True,
            is_valley=False,
        )

        segment2 = EmotionSegment(
            trajectory_id=trajectory.id,
            segment_index=1,
            content_text="But I'm also worried about the implications.",
            word_count=7,
            sentence_count=1,
            joy_score=0.2,
            anger_score=0.1,
            fear_score=0.7,
            sadness_score=0.3,
            surprise_score=0.1,
            disgust_score=0.1,
            trust_score=0.2,
            anticipation_score=0.1,
            sentiment_compound=-0.3,
            sentiment_positive=0.1,
            sentiment_neutral=0.3,
            sentiment_negative=0.6,
            dominant_emotion="fear",
            confidence_score=0.8,
            is_peak=False,
            is_valley=True,
        )

        # Add transition
        transition = EmotionTransition(
            trajectory_id=trajectory.id,
            from_segment_index=0,
            to_segment_index=1,
            from_emotion="joy",
            to_emotion="fear",
            transition_type="switching",
            intensity_change=-0.7,
            transition_speed=0.1,
            strength_score=0.8,
        )

        # Add performance record
        performance = EmotionPerformance(
            trajectory_id=trajectory.id,
            post_id=trajectory.post_id,
            persona_id=trajectory.persona_id,
            engagement_rate=0.08,
            likes_count=150,
            shares_count=25,
            comments_count=30,
            reach=2000,
            impressions=5000,
            emotion_effectiveness=0.75,
            predicted_engagement=0.07,
            actual_vs_predicted=0.01,
            measured_at=datetime.utcnow(),
        )

        db_session.add_all([segment1, segment2, transition, performance])
        db_session.commit()

        # Verify relationships exist
        assert len(trajectory.segments) == 2
        assert len(trajectory.transitions) == 1
        assert len(trajectory.performance) == 1

        # Act - Delete trajectory
        db_session.delete(trajectory)
        db_session.commit()

        # Assert - All related records should be cascade deleted
        remaining_segments = db_session.query(EmotionSegment).count()
        remaining_transitions = db_session.query(EmotionTransition).count()
        remaining_performance = db_session.query(EmotionPerformance).count()

        assert remaining_segments == 0
        assert remaining_transitions == 0
        assert remaining_performance == 0

    def test_emotion_segment_creation_and_indexing(
        self, db_session, sample_trajectory_data
    ):
        """Test EmotionSegment model creation and indexing."""
        # Arrange
        trajectory = EmotionTrajectory(**sample_trajectory_data)
        db_session.add(trajectory)
        db_session.flush()

        segment_data = {
            "trajectory_id": trajectory.id,
            "segment_index": 0,
            "content_text": "This is an amazing discovery that makes me feel excited!",
            "word_count": 10,
            "sentence_count": 1,
            "joy_score": 0.85,
            "anger_score": 0.05,
            "fear_score": 0.1,
            "sadness_score": 0.05,
            "surprise_score": 0.75,
            "disgust_score": 0.05,
            "trust_score": 0.6,
            "anticipation_score": 0.7,
            "sentiment_compound": 0.8,
            "sentiment_positive": 0.9,
            "sentiment_neutral": 0.1,
            "sentiment_negative": 0.0,
            "dominant_emotion": "joy",
            "confidence_score": 0.9,
            "is_peak": True,
            "is_valley": False,
        }

        # Act
        segment = EmotionSegment(**segment_data)
        db_session.add(segment)
        db_session.commit()

        # Assert
        retrieved_segment = (
            db_session.query(EmotionSegment)
            .filter_by(trajectory_id=trajectory.id, segment_index=0)
            .first()
        )

        assert retrieved_segment is not None
        assert retrieved_segment.content_text == segment_data["content_text"]
        assert retrieved_segment.joy_score == 0.85
        assert retrieved_segment.dominant_emotion == "joy"
        assert retrieved_segment.is_peak is True
        assert retrieved_segment.is_valley is False

    def test_emotion_transition_creation_and_queries(
        self, db_session, sample_trajectory_data
    ):
        """Test EmotionTransition model creation and query functionality."""
        # Arrange
        trajectory = EmotionTrajectory(**sample_trajectory_data)
        db_session.add(trajectory)
        db_session.flush()

        transitions_data = [
            {
                "trajectory_id": trajectory.id,
                "from_segment_index": 0,
                "to_segment_index": 1,
                "from_emotion": "joy",
                "to_emotion": "fear",
                "transition_type": "switching",
                "intensity_change": -0.6,
                "transition_speed": 0.08,
                "strength_score": 0.8,
            },
            {
                "trajectory_id": trajectory.id,
                "from_segment_index": 1,
                "to_segment_index": 2,
                "from_emotion": "fear",
                "to_emotion": "trust",
                "transition_type": "strengthening",
                "intensity_change": 0.4,
                "transition_speed": 0.05,
                "strength_score": 0.6,
            },
        ]

        # Act
        transitions = [EmotionTransition(**data) for data in transitions_data]
        db_session.add_all(transitions)
        db_session.commit()

        # Assert - Query by transition type
        switching_transitions = (
            db_session.query(EmotionTransition)
            .filter_by(transition_type="switching")
            .all()
        )
        assert len(switching_transitions) == 1
        assert switching_transitions[0].from_emotion == "joy"
        assert switching_transitions[0].to_emotion == "fear"

        # Assert - Query by emotion transition
        fear_transitions = (
            db_session.query(EmotionTransition)
            .filter(
                (EmotionTransition.from_emotion == "fear")
                | (EmotionTransition.to_emotion == "fear")
            )
            .all()
        )
        assert len(fear_transitions) == 2

        # Assert - Query by strength
        strong_transitions = (
            db_session.query(EmotionTransition)
            .filter(EmotionTransition.strength_score > 0.7)
            .all()
        )
        assert len(strong_transitions) == 1

    def test_emotion_template_creation_and_versioning(self, db_session):
        """Test EmotionTemplate model creation and versioning functionality."""
        # Arrange
        template_data = {
            "template_name": "curiosity_arc_v1",
            "template_type": "curiosity_arc",
            "pattern_description": "A pattern that builds curiosity through strategic emotional progression",
            "segment_count": 3,
            "optimal_duration_words": 50,
            "trajectory_pattern": "rising",
            "primary_emotions": ["curiosity", "anticipation", "surprise"],
            "emotion_sequence": '{"segments": [{"joy": 0.3, "anticipation": 0.8}, {"surprise": 0.9, "joy": 0.6}, {"trust": 0.7, "anticipation": 0.4}]}',
            "transition_patterns": '{"transitions": [{"type": "strengthening", "emotions": ["anticipation", "surprise"]}, {"type": "switching", "emotions": ["surprise", "trust"]}]}',
            "usage_count": 15,
            "average_engagement": 0.078,
            "engagement_correlation": 0.65,
            "effectiveness_score": 0.82,
            "version": 1,
            "is_active": True,
        }

        # Act
        template = EmotionTemplate(**template_data)
        db_session.add(template)
        db_session.commit()

        # Assert
        retrieved_template = (
            db_session.query(EmotionTemplate)
            .filter_by(template_name="curiosity_arc_v1")
            .first()
        )

        assert retrieved_template is not None
        assert retrieved_template.template_type == "curiosity_arc"
        assert retrieved_template.segment_count == 3
        assert "curiosity" in retrieved_template.primary_emotions
        assert retrieved_template.effectiveness_score == 0.82
        assert retrieved_template.is_active is True

        # Test version constraint
        template_v2 = EmotionTemplate(
            **{**template_data, "version": 2, "effectiveness_score": 0.88}
        )
        db_session.add(template_v2)
        db_session.commit()

        # Should have both versions
        all_versions = (
            db_session.query(EmotionTemplate)
            .filter_by(template_name="curiosity_arc_v1")
            .all()
        )
        assert len(all_versions) == 2

    def test_emotion_performance_metrics_and_analytics(
        self, db_session, sample_trajectory_data
    ):
        """Test EmotionPerformance model for tracking engagement correlations."""
        # Arrange
        trajectory = EmotionTrajectory(**sample_trajectory_data)
        db_session.add(trajectory)
        db_session.flush()

        performance_records = []
        base_date = datetime.utcnow()

        # Create performance data over time
        for i in range(5):
            performance_data = {
                "trajectory_id": trajectory.id,
                "post_id": f"post_{i}",
                "persona_id": "tech_enthusiast",
                "engagement_rate": 0.06 + (i * 0.01),  # Increasing engagement
                "likes_count": 100 + (i * 20),
                "shares_count": 10 + (i * 5),
                "comments_count": 15 + (i * 3),
                "reach": 1000 + (i * 200),
                "impressions": 3000 + (i * 500),
                "emotion_effectiveness": 0.6 + (i * 0.05),
                "predicted_engagement": 0.05 + (i * 0.01),
                "actual_vs_predicted": 0.01 + (i * 0.002),
                "measured_at": base_date + timedelta(days=i),
            }
            performance_records.append(EmotionPerformance(**performance_data))

        # Act
        db_session.add_all(performance_records)
        db_session.commit()

        # Assert - Query analytics
        avg_engagement = (
            db_session.query(text("AVG(engagement_rate)"))
            .select_from(EmotionPerformance)
            .scalar()
        )

        assert avg_engagement == 0.08  # (0.06 + 0.07 + 0.08 + 0.09 + 0.10) / 5

        # Query by persona
        persona_performance = (
            db_session.query(EmotionPerformance)
            .filter_by(persona_id="tech_enthusiast")
            .all()
        )
        assert len(persona_performance) == 5

        # Query by engagement threshold
        high_engagement = (
            db_session.query(EmotionPerformance)
            .filter(EmotionPerformance.engagement_rate > 0.08)
            .all()
        )
        assert len(high_engagement) == 2

        # Query recent performance
        recent_date = base_date + timedelta(days=2)
        recent_performance = (
            db_session.query(EmotionPerformance)
            .filter(EmotionPerformance.measured_at >= recent_date)
            .all()
        )
        assert len(recent_performance) == 3

    def test_database_constraints_and_validation(
        self, db_session, sample_trajectory_data
    ):
        """Test database constraints and data validation."""
        # Test content_hash uniqueness for deduplication
        trajectory1 = EmotionTrajectory(**sample_trajectory_data)
        db_session.add(trajectory1)
        db_session.commit()

        # Attempt to create duplicate with same content_hash
        trajectory2 = EmotionTrajectory(**sample_trajectory_data)
        trajectory2.post_id = "different_post"
        db_session.add(trajectory2)

        # Should be allowed (content_hash is indexed but not unique)
        db_session.commit()

        # Test foreign key constraint
        invalid_segment = EmotionSegment(
            trajectory_id=99999,  # Non-existent trajectory
            segment_index=0,
            content_text="Test",
            word_count=1,
            sentence_count=1,
            dominant_emotion="joy",
            confidence_score=0.8,
        )

        db_session.add(invalid_segment)

        with pytest.raises(Exception):  # Should raise foreign key constraint error
            db_session.commit()

    def test_model_indexes_performance(self, db_session):
        """Test that database indexes improve query performance."""
        # Create multiple trajectories for performance testing
        trajectories = []
        for i in range(100):
            trajectory_data = {
                "post_id": f"post_{i}",
                "persona_id": f"persona_{i % 10}",  # 10 different personas
                "content_hash": hashlib.sha256(f"content_{i}".encode()).hexdigest(),
                "segment_count": 2,
                "total_duration_words": 20,
                "trajectory_type": ["rising", "falling", "roller_coaster", "steady"][
                    i % 4
                ],
                "emotional_variance": 0.5,
                "joy_avg": 0.5,
                "anger_avg": 0.1,
                "fear_avg": 0.1,
                "sadness_avg": 0.1,
                "surprise_avg": 0.2,
                "disgust_avg": 0.1,
                "trust_avg": 0.3,
                "anticipation_avg": 0.4,
                "sentiment_compound": 0.2,
                "sentiment_positive": 0.5,
                "sentiment_neutral": 0.3,
                "sentiment_negative": 0.2,
            }
            trajectories.append(EmotionTrajectory(**trajectory_data))

        db_session.add_all(trajectories)
        db_session.commit()

        # Test indexed queries (should be fast)
        import time

        # Query by persona_id (indexed)
        start_time = time.time()
        persona_results = (
            db_session.query(EmotionTrajectory).filter_by(persona_id="persona_5").all()
        )
        persona_query_time = time.time() - start_time

        assert len(persona_results) == 10
        assert persona_query_time < 0.1  # Should be very fast with index

        # Query by trajectory_type (indexed)
        start_time = time.time()
        type_results = (
            db_session.query(EmotionTrajectory)
            .filter_by(trajectory_type="roller_coaster")
            .all()
        )
        type_query_time = time.time() - start_time

        assert len(type_results) == 25
        assert type_query_time < 0.1

    def test_model_serialization_and_json_fields(self, db_session):
        """Test JSON field handling in EmotionTemplate model."""
        # Arrange
        complex_emotion_sequence = {
            "segments": [
                {"joy": 0.3, "anticipation": 0.8, "surprise": 0.1},
                {"surprise": 0.9, "joy": 0.6, "anticipation": 0.4},
                {"trust": 0.7, "anticipation": 0.4, "joy": 0.5},
            ],
            "metadata": {
                "optimal_duration": "30-60 words",
                "target_audience": "tech enthusiasts",
            },
        }

        transition_patterns = {
            "transitions": [
                {
                    "type": "strengthening",
                    "emotions": ["anticipation", "surprise"],
                    "intensity": 0.8,
                },
                {
                    "type": "switching",
                    "emotions": ["surprise", "trust"],
                    "intensity": 0.6,
                },
            ],
            "rules": {"max_intensity_change": 0.9, "min_segment_duration": 5},
        }

        template_data = {
            "template_name": "complex_pattern_test",
            "template_type": "advanced_curiosity",
            "pattern_description": "Complex multi-stage emotional pattern",
            "segment_count": 3,
            "optimal_duration_words": 45,
            "trajectory_pattern": "rising",
            "primary_emotions": ["curiosity", "anticipation", "surprise", "trust"],
            "emotion_sequence": str(complex_emotion_sequence),  # JSON as string
            "transition_patterns": str(transition_patterns),  # JSON as string
            "effectiveness_score": 0.85,
        }

        # Act
        template = EmotionTemplate(**template_data)
        db_session.add(template)
        db_session.commit()

        # Assert
        retrieved_template = (
            db_session.query(EmotionTemplate)
            .filter_by(template_name="complex_pattern_test")
            .first()
        )

        assert retrieved_template is not None
        assert len(retrieved_template.primary_emotions) == 4
        assert "curiosity" in retrieved_template.primary_emotions

        # JSON fields should be stored as strings and be retrievable
        import json

        emotion_seq = json.loads(retrieved_template.emotion_sequence.replace("'", '"'))
        assert len(emotion_seq["segments"]) == 3
        assert emotion_seq["metadata"]["target_audience"] == "tech enthusiasts"

    def test_bulk_operations_performance(self, db_session):
        """Test bulk insert and update operations performance."""
        import time

        # Test bulk trajectory creation
        trajectories_data = []
        for i in range(500):
            trajectory_data = {
                "post_id": f"bulk_post_{i}",
                "persona_id": f"bulk_persona_{i % 20}",
                "content_hash": hashlib.sha256(
                    f"bulk_content_{i}".encode()
                ).hexdigest(),
                "segment_count": 2,
                "total_duration_words": 25,
                "trajectory_type": "steady",
                "emotional_variance": 0.3,
                "joy_avg": 0.4,
                "anger_avg": 0.1,
                "fear_avg": 0.1,
                "sadness_avg": 0.1,
                "surprise_avg": 0.1,
                "disgust_avg": 0.1,
                "trust_avg": 0.2,
                "anticipation_avg": 0.3,
                "sentiment_compound": 0.1,
                "sentiment_positive": 0.4,
                "sentiment_neutral": 0.5,
                "sentiment_negative": 0.1,
            }
            trajectories_data.append(trajectory_data)

        # Measure bulk insert performance
        start_time = time.time()
        trajectories = [EmotionTrajectory(**data) for data in trajectories_data]
        db_session.add_all(trajectories)
        db_session.commit()
        bulk_insert_time = time.time() - start_time

        # Should complete bulk operations in reasonable time
        assert bulk_insert_time < 5.0, (
            f"Bulk insert took {bulk_insert_time:.2f}s, expected <5s"
        )

        # Verify all records were inserted
        total_count = db_session.query(EmotionTrajectory).count()
        assert total_count == 500

    def test_complex_analytics_queries(self, db_session):
        """Test complex analytical queries across emotion models."""
        # Setup test data
        personas = ["tech_blogger", "lifestyle_guru", "fitness_coach"]
        trajectory_types = ["rising", "falling", "roller_coaster", "steady"]

        for i in range(30):
            persona = personas[i % len(personas)]
            traj_type = trajectory_types[i % len(trajectory_types)]

            trajectory = EmotionTrajectory(
                post_id=f"analytics_post_{i}",
                persona_id=persona,
                content_hash=hashlib.sha256(
                    f"analytics_content_{i}".encode()
                ).hexdigest(),
                segment_count=3,
                total_duration_words=40,
                trajectory_type=traj_type,
                emotional_variance=0.4 + (i % 5) * 0.1,
                joy_avg=0.3 + (i % 7) * 0.1,
                anger_avg=0.1,
                fear_avg=0.1,
                sadness_avg=0.1,
                surprise_avg=0.2 + (i % 4) * 0.1,
                disgust_avg=0.1,
                trust_avg=0.2 + (i % 3) * 0.1,
                anticipation_avg=0.3 + (i % 6) * 0.1,
                sentiment_compound=0.2,
                sentiment_positive=0.5,
                sentiment_neutral=0.3,
                sentiment_negative=0.2,
            )
            db_session.add(trajectory)
            db_session.flush()

            # Add performance data
            performance = EmotionPerformance(
                trajectory_id=trajectory.id,
                post_id=trajectory.post_id,
                persona_id=persona,
                engagement_rate=0.05 + (i % 8) * 0.01,
                likes_count=50 + i * 10,
                shares_count=5 + i * 2,
                comments_count=10 + i * 3,
                reach=800 + i * 100,
                impressions=2000 + i * 200,
                emotion_effectiveness=0.6 + (i % 5) * 0.05,
                predicted_engagement=0.04 + (i % 7) * 0.01,
                actual_vs_predicted=0.01,
                measured_at=datetime.utcnow(),
            )
            db_session.add(performance)

        db_session.commit()

        # Complex query 1: Average engagement by trajectory type
        from sqlalchemy import func

        engagement_by_type = (
            db_session.query(
                EmotionTrajectory.trajectory_type,
                func.avg(EmotionPerformance.engagement_rate).label("avg_engagement"),
            )
            .join(EmotionPerformance)
            .group_by(EmotionTrajectory.trajectory_type)
            .all()
        )

        assert len(engagement_by_type) == 4  # All trajectory types
        type_dict = {row[0]: row[1] for row in engagement_by_type}
        assert all(0.05 <= rate <= 0.15 for rate in type_dict.values())

        # Complex query 2: Top performing personas by emotion effectiveness
        top_personas = (
            db_session.query(
                EmotionPerformance.persona_id,
                func.avg(EmotionPerformance.emotion_effectiveness).label(
                    "avg_effectiveness"
                ),
                func.count(EmotionPerformance.id).label("post_count"),
            )
            .group_by(EmotionPerformance.persona_id)
            .order_by(func.avg(EmotionPerformance.emotion_effectiveness).desc())
            .limit(3)
            .all()
        )

        assert len(top_personas) == 3
        assert all(row[2] == 10 for row in top_personas)  # 10 posts per persona

        # Complex query 3: Correlation between emotional variance and engagement
        variance_engagement = (
            db_session.query(
                EmotionTrajectory.emotional_variance, EmotionPerformance.engagement_rate
            )
            .join(EmotionPerformance)
            .all()
        )

        assert len(variance_engagement) == 30

        # Calculate simple correlation
        variances = [row[0] for row in variance_engagement]
        engagements = [row[1] for row in variance_engagement]

        # Should have meaningful variance in data
        assert max(variances) > min(variances)
        assert max(engagements) > min(engagements)
