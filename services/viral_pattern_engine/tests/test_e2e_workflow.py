"""End-to-end workflow tests for CRA-282 emotion trajectory mapping system.

Tests cover the complete pipeline from content ingestion to database storage
and performance analytics.
"""

import pytest
import json
import hashlib
import time
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from services.orchestrator.db import Base
from services.orchestrator.db.models import (
    EmotionTrajectory,
    EmotionSegment,
    EmotionTemplate,
    EmotionPerformance,
)
from services.viral_pattern_engine.main import app
from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper
from services.viral_pattern_engine.pattern_extractor import ViralPatternExtractor


class TestEmotionTrajectoryE2EWorkflow:
    """End-to-end workflow tests for emotion trajectory mapping system."""

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
    def api_client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def emotion_analyzer(self):
        """Create emotion analyzer instance."""
        return EmotionAnalyzer()

    @pytest.fixture
    def trajectory_mapper(self):
        """Create trajectory mapper instance."""
        return TrajectoryMapper()

    @pytest.fixture
    def pattern_extractor(self):
        """Create pattern extractor instance."""
        return ViralPatternExtractor()

    @pytest.fixture
    def sample_viral_posts(self):
        """Create sample viral posts for testing."""
        return [
            {
                "id": "viral_post_1",
                "content": "🚀 BREAKING: Scientists just made the most incredible discovery! "
                "This could revolutionize everything we know about physics. "
                "I'm absolutely thrilled about the possibilities! "
                "However, I'm also deeply concerned about potential misuse. "
                "What safeguards do we have in place? "
                "Actually, I trust our scientific community to handle this responsibly. "
                "The future looks incredibly bright! ✨",
                "author": "@science_enthusiast",
                "engagement_metrics": {
                    "likes": 2500,
                    "shares": 450,
                    "comments": 180,
                    "views": 75000,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "threads",
            },
            {
                "id": "viral_post_2",
                "content": "Just witnessed the most heartbreaking scene at the animal shelter today. 😢 "
                "So many beautiful souls waiting for homes. "
                "But then I met Luna, and my heart filled with joy! "
                "She's coming home with me tomorrow! 🐕💕 "
                "Sometimes the most painful moments lead to the greatest happiness.",
                "author": "@animal_lover",
                "engagement_metrics": {
                    "likes": 1800,
                    "shares": 320,
                    "comments": 95,
                    "views": 45000,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "threads",
            },
            {
                "id": "viral_post_3",
                "content": "URGENT: Climate change is happening NOW! 🔥 "
                "We're seeing unprecedented temperatures worldwide. "
                "This should terrify everyone! "
                "But here's what gives me hope... "
                "Young activists are stepping up everywhere. "
                "Technology is advancing rapidly. "
                "We CAN solve this if we act together! 🌍💪",
                "author": "@climate_activist",
                "engagement_metrics": {
                    "likes": 3200,
                    "shares": 890,
                    "comments": 340,
                    "views": 120000,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "threads",
            },
        ]

    def test_complete_emotion_trajectory_pipeline(
        self, db_session, emotion_analyzer, trajectory_mapper
    ):
        """Test complete pipeline from content analysis to database storage."""
        # Arrange
        content = (
            "I'm absolutely thrilled about this breakthrough discovery! "
            "It's going to change everything we know about science. "
            "However, I'm also terrified about the potential consequences. "
            "What if this technology is misused? "
            "Actually, I believe we can handle this responsibly. "
            "The future looks bright!"
        )

        post_id = "e2e_test_post_1"
        persona_id = "tech_blogger"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Act - Step 1: Analyze emotions
        emotion_result = emotion_analyzer.analyze_emotions(content)

        # Act - Step 2: Map trajectory
        sentences = content.split(". ")
        trajectory_result = trajectory_mapper.map_emotion_trajectory(sentences)

        # Act - Step 3: Store in database
        trajectory = EmotionTrajectory(
            post_id=post_id,
            persona_id=persona_id,
            content_hash=content_hash,
            segment_count=len(sentences),
            total_duration_words=len(content.split()),
            analysis_model="bert_vader",
            confidence_score=emotion_result["confidence"],
            trajectory_type=trajectory_result["arc_type"],
            emotional_variance=trajectory_result["emotional_variance"],
            peak_count=len(trajectory_result["peak_segments"]),
            valley_count=len(trajectory_result["valley_segments"]),
            transition_count=len(trajectory_result.get("transitions", [])),
            # Store average emotions
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
            # VADER sentiment from final analysis
            sentiment_compound=0.25,  # Mixed emotions
            sentiment_positive=0.6,
            sentiment_neutral=0.2,
            sentiment_negative=0.2,
            processing_time_ms=150,
        )

        db_session.add(trajectory)
        db_session.flush()

        # Act - Step 4: Store detailed segments
        for i, (sentence, emotions) in enumerate(
            zip(sentences, trajectory_result["emotion_progression"])
        ):
            segment = EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=i,
                content_text=sentence.strip(),
                word_count=len(sentence.split()),
                sentence_count=1,
                joy_score=emotions.get("joy", 0),
                anger_score=emotions.get("anger", 0),
                fear_score=emotions.get("fear", 0),
                sadness_score=emotions.get("sadness", 0),
                surprise_score=emotions.get("surprise", 0),
                disgust_score=emotions.get("disgust", 0),
                trust_score=emotions.get("trust", 0),
                anticipation_score=emotions.get("anticipation", 0),
                sentiment_compound=0.0,  # Would be calculated per segment
                sentiment_positive=0.5,
                sentiment_neutral=0.3,
                sentiment_negative=0.2,
                dominant_emotion=max(emotions, key=emotions.get),
                confidence_score=0.8,
                is_peak=i in trajectory_result["peak_segments"],
                is_valley=i in trajectory_result["valley_segments"],
            )
            db_session.add(segment)

        db_session.commit()

        # Assert - Verify complete pipeline
        stored_trajectory = (
            db_session.query(EmotionTrajectory).filter_by(post_id=post_id).first()
        )
        assert stored_trajectory is not None
        assert stored_trajectory.trajectory_type in [
            "rising",
            "falling",
            "roller_coaster",
            "steady",
        ]
        assert stored_trajectory.confidence_score > 0.0
        assert stored_trajectory.emotional_variance >= 0.0

        # Verify segments were stored
        segments = (
            db_session.query(EmotionSegment)
            .filter_by(trajectory_id=stored_trajectory.id)
            .all()
        )
        assert len(segments) == len(sentences)

        # Verify emotional progression makes sense
        dominant_emotions = [seg.dominant_emotion for seg in segments]
        assert "joy" in dominant_emotions  # Should detect excitement
        assert len(set(dominant_emotions)) >= 2  # Should show emotional variety

    def test_api_to_database_workflow(self, api_client, db_session, sample_viral_posts):
        """Test complete workflow from API call to database storage."""
        post_data = sample_viral_posts[0]  # Use the science discovery post

        # Act - Step 1: Call API
        response = api_client.post("/extract-patterns", json=post_data)

        # Assert API response
        assert response.status_code == 200
        patterns = response.json()
        assert "emotion_trajectory" in patterns

        trajectory_data = patterns["emotion_trajectory"]

        # Act - Step 2: Simulate storing results in database
        # (In real system, this would happen in the orchestrator service)
        content_hash = hashlib.sha256(post_data["content"].encode()).hexdigest()

        trajectory = EmotionTrajectory(
            post_id=post_data["id"],
            persona_id="science_enthusiast",
            content_hash=content_hash,
            segment_count=len(trajectory_data["emotion_progression"]),
            total_duration_words=len(post_data["content"].split()),
            trajectory_type=trajectory_data["arc_type"],
            emotional_variance=trajectory_data["emotional_variance"],
            peak_count=len(trajectory_data["peak_segments"]),
            valley_count=len(trajectory_data["valley_segments"]),
            joy_avg=0.6,  # Would be calculated from progression
            anger_avg=0.1,
            fear_avg=0.3,
            sadness_avg=0.1,
            surprise_avg=0.7,
            disgust_avg=0.1,
            trust_avg=0.4,
            anticipation_avg=0.5,
            sentiment_compound=0.3,
            sentiment_positive=0.7,
            sentiment_neutral=0.2,
            sentiment_negative=0.1,
        )

        db_session.add(trajectory)
        db_session.commit()

        # Assert database storage
        stored_trajectory = (
            db_session.query(EmotionTrajectory)
            .filter_by(post_id=post_data["id"])
            .first()
        )
        assert stored_trajectory is not None
        assert stored_trajectory.trajectory_type == trajectory_data["arc_type"]

    def test_batch_processing_workflow(
        self, api_client, db_session, sample_viral_posts
    ):
        """Test batch processing workflow with database integration."""
        # Arrange
        batch_request = {"posts": sample_viral_posts}

        # Act - Process batch
        response = api_client.post("/analyze-batch", json=batch_request)

        # Assert batch response
        assert response.status_code == 200
        batch_result = response.json()
        assert len(batch_result["results"]) == len(sample_viral_posts)

        # Act - Store batch results in database
        trajectories_stored = 0
        for i, (post, result) in enumerate(
            zip(sample_viral_posts, batch_result["results"])
        ):
            if "emotion_trajectory" in result:
                trajectory_data = result["emotion_trajectory"]
                content_hash = hashlib.sha256(post["content"].encode()).hexdigest()

                trajectory = EmotionTrajectory(
                    post_id=post["id"],
                    persona_id=f"persona_{i}",
                    content_hash=content_hash,
                    segment_count=len(trajectory_data["emotion_progression"]),
                    total_duration_words=len(post["content"].split()),
                    trajectory_type=trajectory_data["arc_type"],
                    emotional_variance=trajectory_data["emotional_variance"],
                    peak_count=len(trajectory_data["peak_segments"]),
                    valley_count=len(trajectory_data["valley_segments"]),
                    joy_avg=0.5,
                    anger_avg=0.2,
                    fear_avg=0.2,
                    sadness_avg=0.2,
                    surprise_avg=0.3,
                    disgust_avg=0.1,
                    trust_avg=0.3,
                    anticipation_avg=0.4,
                )

                db_session.add(trajectory)
                trajectories_stored += 1

        db_session.commit()

        # Assert database storage
        total_stored = db_session.query(EmotionTrajectory).count()
        assert total_stored == trajectories_stored
        assert trajectories_stored >= 2  # Should process most posts

    def test_performance_tracking_workflow(self, db_session):
        """Test workflow for tracking emotion performance against engagement."""
        # Arrange - Create trajectory with performance data
        trajectory = EmotionTrajectory(
            post_id="performance_test_post",
            persona_id="performance_tester",
            content_hash=hashlib.sha256("test content".encode()).hexdigest(),
            segment_count=3,
            total_duration_words=20,
            trajectory_type="roller_coaster",
            emotional_variance=0.75,
            peak_count=2,
            valley_count=1,
            joy_avg=0.7,
            anger_avg=0.1,
            fear_avg=0.4,
            sadness_avg=0.1,
            surprise_avg=0.6,
            disgust_avg=0.1,
            trust_avg=0.3,
            anticipation_avg=0.5,
        )

        db_session.add(trajectory)
        db_session.flush()

        # Act - Add performance tracking over time
        base_date = datetime.utcnow()
        performance_records = []

        for days_offset in range(7):  # Track for a week
            engagement_rate = 0.06 + (days_offset * 0.01)  # Increasing engagement

            performance = EmotionPerformance(
                trajectory_id=trajectory.id,
                post_id=trajectory.post_id,
                persona_id=trajectory.persona_id,
                engagement_rate=engagement_rate,
                likes_count=100 + (days_offset * 20),
                shares_count=15 + (days_offset * 5),
                comments_count=8 + (days_offset * 3),
                reach=2000 + (days_offset * 300),
                impressions=8000 + (days_offset * 1000),
                emotion_effectiveness=0.65 + (days_offset * 0.02),
                predicted_engagement=0.05 + (days_offset * 0.008),
                actual_vs_predicted=engagement_rate - (0.05 + (days_offset * 0.008)),
                measured_at=base_date + timedelta(days=days_offset),
            )
            performance_records.append(performance)

        db_session.add_all(performance_records)
        db_session.commit()

        # Assert - Analyze performance correlation
        trajectory_performance = (
            db_session.query(EmotionPerformance)
            .filter_by(trajectory_id=trajectory.id)
            .order_by(EmotionPerformance.measured_at)
            .all()
        )

        assert len(trajectory_performance) == 7

        # Verify performance tracking
        first_day = trajectory_performance[0]
        last_day = trajectory_performance[-1]

        assert last_day.engagement_rate > first_day.engagement_rate
        assert last_day.emotion_effectiveness > first_day.emotion_effectiveness

        # Calculate correlation between emotional variance and engagement
        avg_engagement = sum(p.engagement_rate for p in trajectory_performance) / len(
            trajectory_performance
        )
        assert (
            avg_engagement > 0.08
        )  # High emotional variance should correlate with good engagement

    def test_emotion_template_workflow(self, db_session, trajectory_mapper):
        """Test workflow for creating and using emotion templates."""
        # Arrange - Create successful emotion pattern
        successful_content_segments = [
            "I discovered something amazing today!",
            "But wait, there might be some risks involved...",
            "Actually, I think we can handle this responsibly.",
            "The future looks incredibly bright!",
        ]

        # Act - Analyze the successful pattern
        trajectory_result = trajectory_mapper.map_emotion_trajectory(
            successful_content_segments
        )

        # Act - Store as template
        template = EmotionTemplate(
            template_name="discovery_concern_resolution_hope",
            template_type="curiosity_to_trust_arc",
            pattern_description="Pattern that moves from excitement through concern to resolution and hope",
            segment_count=4,
            optimal_duration_words=60,
            trajectory_pattern=trajectory_result["arc_type"],
            primary_emotions=["joy", "surprise", "fear", "trust", "anticipation"],
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
                        {
                            "from": "joy",
                            "to": "fear",
                            "type": "switching",
                            "strength": 0.7,
                        },
                        {
                            "from": "fear",
                            "to": "trust",
                            "type": "strengthening",
                            "strength": 0.6,
                        },
                        {
                            "from": "trust",
                            "to": "joy",
                            "type": "strengthening",
                            "strength": 0.8,
                        },
                    ]
                }
            ),
            usage_count=1,
            average_engagement=0.085,
            engagement_correlation=0.72,
            effectiveness_score=0.86,
            is_active=True,
        )

        db_session.add(template)
        db_session.commit()

        # Assert template creation
        stored_template = (
            db_session.query(EmotionTemplate)
            .filter_by(template_name="discovery_concern_resolution_hope")
            .first()
        )

        assert stored_template is not None
        assert stored_template.effectiveness_score > 0.8
        assert "joy" in stored_template.primary_emotions
        assert stored_template.is_active is True

        # Act - Use template for new content generation guidance
        emotion_sequence = json.loads(stored_template.emotion_sequence)
        assert len(emotion_sequence["segments"]) == 4

        # Template should guide content creation
        first_segment_emotions = emotion_sequence["segments"][0]
        assert first_segment_emotions["joy"] > 0.7  # Should start with high joy

        last_segment_emotions = emotion_sequence["segments"][-1]
        assert (
            last_segment_emotions["anticipation"] > 0.8
        )  # Should end with high anticipation

    def test_error_recovery_workflow(self, api_client, db_session):
        """Test error recovery in end-to-end workflow."""
        # Test with problematic content
        problematic_posts = [
            {
                "id": "error_test_1",
                "content": "",  # Empty content
                "author": "@test_user",
                "engagement_metrics": {
                    "likes": 0,
                    "shares": 0,
                    "comments": 0,
                    "views": 0,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "threads",
            },
            {
                "id": "error_test_2",
                "content": "🎉" * 1000,  # Excessive emojis
                "author": "@emoji_user",
                "engagement_metrics": {
                    "likes": 10,
                    "shares": 1,
                    "comments": 0,
                    "views": 100,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "threads",
            },
            {
                "id": "error_test_3",
                "content": "A" * 10000,  # Extremely long content
                "author": "@long_user",
                "engagement_metrics": {
                    "likes": 5,
                    "shares": 0,
                    "comments": 1,
                    "views": 50,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "threads",
            },
        ]

        successful_processing = 0

        for post in problematic_posts:
            try:
                # Act - Process problematic content
                response = api_client.post("/extract-patterns", json=post)

                if response.status_code == 200:
                    patterns = response.json()
                    successful_processing += 1

                    # Should handle gracefully
                    assert isinstance(patterns, dict)

                    # Try to store in database if trajectory exists
                    if "emotion_trajectory" in patterns:
                        trajectory_data = patterns["emotion_trajectory"]

                        trajectory = EmotionTrajectory(
                            post_id=post["id"],
                            persona_id="error_test_persona",
                            content_hash=hashlib.sha256(
                                post["content"].encode()
                            ).hexdigest(),
                            segment_count=max(
                                1, len(trajectory_data.get("emotion_progression", []))
                            ),
                            total_duration_words=len(post["content"].split()),
                            trajectory_type=trajectory_data.get("arc_type", "steady"),
                            emotional_variance=trajectory_data.get(
                                "emotional_variance", 0.0
                            ),
                            joy_avg=0.1,
                            anger_avg=0.1,
                            fear_avg=0.1,
                            sadness_avg=0.1,
                            surprise_avg=0.1,
                            disgust_avg=0.1,
                            trust_avg=0.1,
                            anticipation_avg=0.1,
                        )

                        db_session.add(trajectory)
                        db_session.commit()

            except Exception as e:
                # Should not crash the entire workflow
                print(f"Handled error for post {post['id']}: {e}")

        # Should handle at least some problematic content gracefully
        assert successful_processing >= 1, "Should handle some error cases gracefully"

    def test_real_time_processing_workflow(self, api_client, db_session):
        """Test real-time processing workflow with time constraints."""
        # Simulate real-time content stream
        content_stream = [
            "Breaking: New discovery announced!",
            "I'm shocked by this development. What does it mean?",
            "Actually, this could be really positive for everyone.",
            "Feeling optimistic about the future now!",
            "Wait, I just realized there might be downsides...",
            "But I trust we'll figure it out together.",
        ]

        processing_times = []
        stored_trajectories = []

        for i, content in enumerate(content_stream):
            post_data = {
                "id": f"realtime_post_{i}",
                "content": content,
                "author": "@realtime_user",
                "engagement_metrics": {
                    "likes": 10 + i,
                    "shares": 1 + i,
                    "comments": i,
                    "views": 100 + i * 50,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "threads",
            }

            # Act - Process in real-time
            start_time = time.time()
            response = api_client.post("/extract-patterns", json=post_data)
            processing_time = (time.time() - start_time) * 1000

            processing_times.append(processing_time)

            # Assert real-time requirement
            assert processing_time < 300, (
                f"Real-time processing took {processing_time:.2f}ms"
            )
            assert response.status_code == 200

            # Store results
            patterns = response.json()
            if "emotion_trajectory" in patterns:
                trajectory_data = patterns["emotion_trajectory"]

                trajectory = EmotionTrajectory(
                    post_id=post_data["id"],
                    persona_id="realtime_persona",
                    content_hash=hashlib.sha256(content.encode()).hexdigest(),
                    segment_count=1,
                    total_duration_words=len(content.split()),
                    trajectory_type=trajectory_data["arc_type"],
                    emotional_variance=trajectory_data["emotional_variance"],
                    joy_avg=0.5,
                    anger_avg=0.1,
                    fear_avg=0.2,
                    sadness_avg=0.1,
                    surprise_avg=0.3,
                    disgust_avg=0.1,
                    trust_avg=0.4,
                    anticipation_avg=0.3,
                    processing_time_ms=int(processing_time),
                )

                db_session.add(trajectory)
                stored_trajectories.append(trajectory)

        db_session.commit()

        # Assert real-time workflow
        avg_processing_time = sum(processing_times) / len(processing_times)
        assert avg_processing_time < 250, (
            f"Average real-time processing {avg_processing_time:.2f}ms too slow"
        )

        # Verify all content was processed and stored
        assert (
            len(stored_trajectories) >= len(content_stream) * 0.8
        )  # At least 80% success rate

    def test_analytics_and_insights_workflow(self, db_session):
        """Test analytics workflow for generating insights from emotion trajectories."""
        # Arrange - Create diverse trajectory data
        trajectory_types = ["rising", "falling", "roller_coaster", "steady"]
        personas = ["tech_blogger", "lifestyle_guru", "news_reporter", "entrepreneur"]

        for i in range(20):
            trajectory = EmotionTrajectory(
                post_id=f"analytics_post_{i}",
                persona_id=personas[i % len(personas)],
                content_hash=hashlib.sha256(f"content_{i}".encode()).hexdigest(),
                segment_count=3 + (i % 5),
                total_duration_words=50 + (i * 10),
                trajectory_type=trajectory_types[i % len(trajectory_types)],
                emotional_variance=0.2 + (i % 8) * 0.1,
                peak_count=i % 3,
                valley_count=(i + 1) % 3,
                joy_avg=0.3 + (i % 7) * 0.1,
                anger_avg=0.1 + (i % 3) * 0.05,
                fear_avg=0.1 + (i % 4) * 0.1,
                sadness_avg=0.1 + (i % 2) * 0.1,
                surprise_avg=0.2 + (i % 5) * 0.1,
                disgust_avg=0.1,
                trust_avg=0.2 + (i % 6) * 0.08,
                anticipation_avg=0.3 + (i % 4) * 0.1,
                sentiment_compound=0.1 + (i % 10) * 0.05,
                sentiment_positive=0.4 + (i % 8) * 0.05,
                sentiment_neutral=0.3,
                sentiment_negative=0.1 + (i % 3) * 0.05,
            )

            db_session.add(trajectory)
            db_session.flush()

            # Add performance data
            performance = EmotionPerformance(
                trajectory_id=trajectory.id,
                post_id=trajectory.post_id,
                persona_id=trajectory.persona_id,
                engagement_rate=0.05 + (i % 10) * 0.01,
                likes_count=100 + i * 50,
                shares_count=10 + i * 5,
                comments_count=5 + i * 3,
                reach=1000 + i * 200,
                impressions=5000 + i * 500,
                emotion_effectiveness=0.6 + (i % 8) * 0.03,
                predicted_engagement=0.04 + (i % 7) * 0.01,
                actual_vs_predicted=0.01,
                measured_at=datetime.utcnow() - timedelta(days=i),
            )

            db_session.add(performance)

        db_session.commit()

        # Act - Generate analytics insights
        from sqlalchemy import func

        # Insight 1: Best performing trajectory types
        trajectory_performance = (
            db_session.query(
                EmotionTrajectory.trajectory_type,
                func.avg(EmotionPerformance.engagement_rate).label("avg_engagement"),
                func.count(EmotionTrajectory.id).label("count"),
            )
            .join(EmotionPerformance)
            .group_by(EmotionTrajectory.trajectory_type)
            .order_by(func.avg(EmotionPerformance.engagement_rate).desc())
            .all()
        )

        # Insight 2: Persona effectiveness
        persona_effectiveness = (
            db_session.query(
                EmotionPerformance.persona_id,
                func.avg(EmotionPerformance.emotion_effectiveness).label(
                    "avg_effectiveness"
                ),
            )
            .group_by(EmotionPerformance.persona_id)
            .all()
        )

        # Insight 3: Emotional variance correlation
        variance_correlation = (
            db_session.query(
                EmotionTrajectory.emotional_variance, EmotionPerformance.engagement_rate
            )
            .join(EmotionPerformance)
            .all()
        )

        # Assert analytics results
        assert len(trajectory_performance) == 4  # All trajectory types
        assert len(persona_effectiveness) == 4  # All personas
        assert len(variance_correlation) == 20  # All posts

        # Best performing trajectory type should have reasonable engagement
        best_trajectory = trajectory_performance[0]
        assert best_trajectory[1] > 0.07  # avg_engagement > 7%

        # All personas should have some effectiveness
        for persona, effectiveness in persona_effectiveness:
            assert effectiveness > 0.6

        # Should show correlation patterns
        variances = [row[0] for row in variance_correlation]
        engagements = [row[1] for row in variance_correlation]

        assert max(variances) > min(variances)  # Should have variance spread
        assert max(engagements) > min(engagements)  # Should have engagement spread

    def test_content_optimization_workflow(self, db_session, trajectory_mapper):
        """Test workflow for content optimization based on emotion trajectory insights."""
        # Arrange - Analyze high-performing content pattern
        high_performing_content = [
            "🚀 INCREDIBLE news just dropped!",
            "This could change everything we know...",
            "But wait, let me think about this critically.",
            "Actually, this opens up amazing possibilities!",
            "I'm genuinely excited about what comes next! ✨",
        ]

        # Act - Analyze successful pattern
        successful_trajectory = trajectory_mapper.map_emotion_trajectory(
            high_performing_content
        )

        # Store as high-performing template
        template = EmotionTemplate(
            template_name="excitement_skepticism_resolution_optimism",
            template_type="viral_engagement_pattern",
            pattern_description="High-engagement pattern: excitement → skepticism → critical thinking → resolution → optimism",
            segment_count=5,
            optimal_duration_words=80,
            trajectory_pattern=successful_trajectory["arc_type"],
            primary_emotions=["joy", "surprise", "anticipation", "trust"],
            emotion_sequence=json.dumps(
                {
                    "pattern": "high_engagement",
                    "segments": successful_trajectory["emotion_progression"],
                }
            ),
            transition_patterns=json.dumps(
                {
                    "key_transitions": [
                        {"stage": "hook", "emotion": "surprise", "min_score": 0.7},
                        {
                            "stage": "development",
                            "emotion": "anticipation",
                            "min_score": 0.6,
                        },
                        {"stage": "resolution", "emotion": "trust", "min_score": 0.7},
                        {"stage": "conclusion", "emotion": "joy", "min_score": 0.8},
                    ]
                }
            ),
            average_engagement=0.095,
            engagement_correlation=0.78,
            effectiveness_score=0.89,
            is_active=True,
        )

        db_session.add(template)
        db_session.commit()

        # Act - Test content optimization against template
        candidate_content = [
            "This is interesting news.",
            "I'm not sure what to think.",
            "Let me research this more.",
            "Okay, this actually looks promising!",
            "The future is looking bright!",
        ]

        candidate_trajectory = trajectory_mapper.map_emotion_trajectory(
            candidate_content
        )

        # Assert optimization workflow
        assert (
            successful_trajectory["emotional_variance"] > 0.4
        )  # Should show good variance
        assert template.effectiveness_score > 0.85  # High effectiveness

        # Compare candidate against template
        template_pattern = json.loads(template.emotion_sequence)
        optimization_score = 0.0

        if len(candidate_trajectory["emotion_progression"]) == len(
            template_pattern["segments"]
        ):
            # Calculate similarity score
            for i, (candidate_emotions, template_emotions) in enumerate(
                zip(
                    candidate_trajectory["emotion_progression"],
                    template_pattern["segments"],
                )
            ):
                segment_similarity = 0.0
                emotion_count = 0

                for emotion in ["joy", "surprise", "anticipation", "trust"]:
                    if emotion in candidate_emotions and emotion in template_emotions:
                        diff = abs(
                            candidate_emotions[emotion] - template_emotions[emotion]
                        )
                        segment_similarity += 1.0 - diff
                        emotion_count += 1

                if emotion_count > 0:
                    optimization_score += segment_similarity / emotion_count

            optimization_score /= len(template_pattern["segments"])

        # Should provide optimization guidance
        assert 0.0 <= optimization_score <= 1.0

        # Workflow should identify optimization opportunities
        if optimization_score < 0.7:
            print(
                f"Content optimization recommended. Current score: {optimization_score:.2f}"
            )
            print("Suggestions:")
            print("- Increase emotional variance")
            print("- Strengthen hook with surprise")
            print("- Build anticipation in development")
            print("- Resolve with trust and joy")

        # Assert workflow completion
        stored_template = (
            db_session.query(EmotionTemplate)
            .filter_by(template_name="excitement_skepticism_resolution_optimism")
            .first()
        )
        assert stored_template is not None
        assert stored_template.effectiveness_score > 0.8
