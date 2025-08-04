"""API integration tests for emotion trajectory endpoints."""

import pytest
import hashlib
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.orchestrator.main import app
from services.orchestrator.db.models import EmotionTrajectory, EmotionTemplate


@pytest.mark.e2e
class TestEmotionAPIIntegration:
    """Test emotion trajectory API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        return TestClient(app)

    @pytest.fixture
    def sample_content_segments(self):
        """Sample content segments for testing."""
        return [
            "Let me tell you about this amazing discovery.",
            "At first, I thought it was just another tool.",
            "But then something incredible happened!",
            "This completely changed my perspective on everything.",
        ]

    @pytest.fixture
    def mock_emotion_analysis_result(self):
        """Mock emotion analysis result."""
        return {
            "arc_type": "rising",
            "emotion_progression": [
                {
                    "joy": 0.6,
                    "trust": 0.8,
                    "anticipation": 0.5,
                    "anger": 0.1,
                    "fear": 0.1,
                    "sadness": 0.1,
                    "surprise": 0.3,
                    "disgust": 0.05,
                },
                {
                    "joy": 0.5,
                    "trust": 0.7,
                    "anticipation": 0.4,
                    "anger": 0.15,
                    "fear": 0.2,
                    "sadness": 0.3,
                    "surprise": 0.2,
                    "disgust": 0.1,
                },
                {
                    "joy": 0.85,
                    "trust": 0.8,
                    "anticipation": 0.9,
                    "anger": 0.05,
                    "fear": 0.05,
                    "sadness": 0.05,
                    "surprise": 0.8,
                    "disgust": 0.05,
                },
                {
                    "joy": 0.9,
                    "trust": 0.85,
                    "anticipation": 0.7,
                    "anger": 0.05,
                    "fear": 0.05,
                    "sadness": 0.05,
                    "surprise": 0.6,
                    "disgust": 0.05,
                },
            ],
            "peak_segments": [2, 3],
            "valley_segments": [1],
            "emotional_variance": 0.45,
        }

    def test_analyze_emotion_trajectory_endpoint(
        self, client, sample_content_segments, mock_emotion_analysis_result
    ):
        """Test POST /emotion/analyze_trajectory endpoint."""
        # Arrange
        request_payload = {
            "post_id": "test_post_123",
            "persona_id": "viral_creator",
            "content_segments": sample_content_segments,
            "metadata": {"total_words": 150, "analysis_model": "bert_vader"},
        }

        with patch(
            "services.viral_pattern_engine.trajectory_mapper.TrajectoryMapper.map_emotion_trajectory"
        ) as mock_mapper:
            mock_mapper.return_value = mock_emotion_analysis_result

            # Act
            response = client.post("/emotion/analyze_trajectory", json=request_payload)

            # Assert
            assert response.status_code == 200
            result = response.json()

            assert "trajectory_id" in result
            assert result["arc_type"] == "rising"
            assert result["emotional_variance"] == 0.45
            assert len(result["peak_segments"]) == 2
            assert len(result["valley_segments"]) == 1
            assert "processing_time_ms" in result
            assert result["processing_time_ms"] < 300  # Performance requirement

    def test_analyze_emotion_transitions_endpoint(
        self, client, sample_content_segments
    ):
        """Test POST /emotion/analyze_transitions endpoint."""
        # Arrange
        request_payload = {"content_segments": sample_content_segments}

        mock_transitions_result = {
            "transitions": [
                {"from_emotion": "trust", "to_emotion": "sadness", "strength": 0.4},
                {"from_emotion": "sadness", "to_emotion": "joy", "strength": 0.6},
                {"from_emotion": "joy", "to_emotion": "joy", "strength": 0.1},
            ],
            "dominant_transitions": [
                ("sadness_to_joy", 1),
                ("trust_to_sadness", 1),
                ("joy_to_joy", 1),
            ],
            "transition_strength": 0.367,
        }

        with patch(
            "services.viral_pattern_engine.trajectory_mapper.TrajectoryMapper.analyze_emotion_transitions"
        ) as mock_transitions:
            mock_transitions.return_value = mock_transitions_result

            # Act
            response = client.post("/emotion/analyze_transitions", json=request_payload)

            # Assert
            assert response.status_code == 200
            result = response.json()

            assert len(result["transitions"]) == 3
            assert result["transition_strength"] == 0.367
            assert len(result["dominant_transitions"]) == 3

            # Verify transition details
            transitions = result["transitions"]
            assert transitions[0]["from_emotion"] == "trust"
            assert transitions[1]["to_emotion"] == "joy"

    def test_get_emotion_trajectory_by_id(self, client, db_session: Session):
        """Test GET /emotion/trajectory/{trajectory_id} endpoint."""
        # Arrange - Create a trajectory in database
        trajectory = EmotionTrajectory(
            post_id="test_post_456",
            persona_id="viral_creator",
            content_hash=hashlib.sha256("test content".encode()).hexdigest(),
            segment_count=3,
            total_duration_words=120,
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
            processing_time_ms=245,
        )

        db_session.add(trajectory)
        db_session.commit()

        # Act
        response = client.get(f"/emotion/trajectory/{trajectory.id}")

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["id"] == trajectory.id
        assert result["post_id"] == "test_post_456"
        assert result["trajectory_type"] == "rising"
        assert result["dominant_emotion"] == "trust"
        assert result["emotional_variance"] == 0.42
        assert result["processing_time_ms"] == 245

    def test_get_emotion_trajectories_by_persona(self, client, db_session: Session):
        """Test GET /emotion/trajectories endpoint with persona filter."""
        # Arrange - Create multiple trajectories
        trajectories = [
            EmotionTrajectory(
                post_id=f"post_{i}",
                persona_id="viral_creator",
                content_hash=hashlib.sha256(f"content_{i}".encode()).hexdigest(),
                segment_count=3,
                total_duration_words=100,
                trajectory_type="rising" if i % 2 == 0 else "falling",
                joy_avg=0.5 + i * 0.1,
            )
            for i in range(3)
        ]

        # Add one trajectory for different persona
        trajectories.append(
            EmotionTrajectory(
                post_id="post_other",
                persona_id="storyteller",
                content_hash=hashlib.sha256("other content".encode()).hexdigest(),
                segment_count=2,
                total_duration_words=80,
                trajectory_type="steady",
                joy_avg=0.4,
            )
        )

        db_session.add_all(trajectories)
        db_session.commit()

        # Act
        response = client.get("/emotion/trajectories?persona_id=viral_creator&limit=10")

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert len(result["trajectories"]) == 3
        assert all(t["persona_id"] == "viral_creator" for t in result["trajectories"])
        assert result["total_count"] == 3

    def test_create_emotion_template_endpoint(self, client):
        """Test POST /emotion/templates endpoint."""
        # Arrange
        template_data = {
            "template_name": "Viral Hook Pattern",
            "template_type": "engagement_hook",
            "pattern_description": "A pattern that creates immediate engagement through emotional hooks",
            "segment_count": 3,
            "optimal_duration_words": 150,
            "trajectory_pattern": "rising",
            "primary_emotions": ["anticipation", "surprise", "joy"],
            "emotion_sequence": {
                "segments": [
                    {"anticipation": 0.8, "trust": 0.6},
                    {"anticipation": 0.9, "surprise": 0.3},
                    {"joy": 0.9, "surprise": 0.8},
                ]
            },
            "transition_patterns": {
                "transitions": ["anticipation_to_anticipation", "anticipation_to_joy"]
            },
        }

        # Act
        response = client.post("/emotion/templates", json=template_data)

        # Assert
        assert response.status_code == 201
        result = response.json()

        assert result["template_name"] == "Viral Hook Pattern"
        assert result["template_type"] == "engagement_hook"
        assert result["segment_count"] == 3
        assert result["primary_emotions"] == ["anticipation", "surprise", "joy"]
        assert result["is_active"] is True
        assert "template_id" in result

    def test_get_emotion_templates_by_effectiveness(self, client, db_session: Session):
        """Test GET /emotion/templates endpoint with effectiveness filtering."""
        # Arrange - Create templates with different effectiveness scores
        templates = [
            EmotionTemplate(
                template_name=f"Template {i}",
                template_type="narrative_arc",
                pattern_description=f"Pattern {i}",
                segment_count=3,
                optimal_duration_words=100,
                trajectory_pattern="rising",
                primary_emotions=["joy", "trust"],
                emotion_sequence='{"test": "data"}',
                transition_patterns='{"test": "pattern"}',
                effectiveness_score=0.5 + i * 0.2,
                usage_count=10 + i * 5,
                is_active=True,
            )
            for i in range(4)
        ]

        db_session.add_all(templates)
        db_session.commit()

        # Act
        response = client.get("/emotion/templates?min_effectiveness=0.8&limit=10")

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert len(result["templates"]) == 2  # Only templates with effectiveness >= 0.8
        assert all(t["effectiveness_score"] >= 0.8 for t in result["templates"])

        # Should be ordered by effectiveness descending
        effectiveness_scores = [t["effectiveness_score"] for t in result["templates"]]
        assert effectiveness_scores == sorted(effectiveness_scores, reverse=True)

    def test_update_template_performance_endpoint(self, client, db_session: Session):
        """Test PUT /emotion/templates/{template_id}/performance endpoint."""
        # Arrange
        template = EmotionTemplate(
            template_name="Performance Test Template",
            template_type="test_type",
            pattern_description="Test template",
            segment_count=3,
            optimal_duration_words=100,
            trajectory_pattern="rising",
            primary_emotions=["joy"],
            emotion_sequence='{"test": "data"}',
            transition_patterns='{"test": "pattern"}',
            usage_count=5,
            average_engagement=0.06,
            effectiveness_score=0.7,
            is_active=True,
        )

        db_session.add(template)
        db_session.commit()

        performance_update = {
            "usage_count_increment": 3,
            "new_engagement_rate": 0.08,
            "engagement_correlation": 0.75,
        }

        # Act
        response = client.put(
            f"/emotion/templates/{template.id}/performance", json=performance_update
        )

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["usage_count"] == 8  # 5 + 3
        assert result["average_engagement"] > 0.06  # Should be updated
        assert result["engagement_correlation"] == 0.75

    def test_analyze_content_emotion_workflow_endpoint(
        self, client, sample_content_segments
    ):
        """Test POST /emotion/analyze_content endpoint (full workflow)."""
        # Arrange
        request_payload = {
            "post_id": "workflow_test_123",
            "persona_id": "viral_creator",
            "content": "This is an amazing discovery! I can't believe how incredible this is. It completely changed everything for me.",
            "segment_strategy": "sentence",  # Split by sentences
            "store_results": True,
            "match_templates": True,
        }

        with (
            patch("services.viral_pattern_engine.emotion_analyzer.EmotionAnalyzer"),
            patch(
                "services.viral_pattern_engine.trajectory_mapper.TrajectoryMapper"
            ) as mock_mapper,
        ):
            # Mock the full workflow
            mock_mapper_instance = mock_mapper.return_value
            mock_mapper_instance.map_emotion_trajectory.return_value = {
                "arc_type": "rising",
                "emotion_progression": [{"joy": 0.8}],
                "peak_segments": [1],
                "valley_segments": [],
                "emotional_variance": 0.65,
            }

            # Act
            response = client.post("/emotion/analyze_content", json=request_payload)

            # Assert
            assert response.status_code == 200
            result = response.json()

            assert "trajectory_id" in result
            assert result["arc_type"] == "rising"
            assert result["processing_time_ms"] < 300
            assert len(result["segments"]) == 3
            assert len(result["transitions"]) >= 1

            # Verify storage was requested
            assert result.get("stored") is True

    def test_emotion_analysis_error_handling(self, client):
        """Test error handling in emotion analysis endpoints."""
        # Test invalid content
        response = client.post(
            "/emotion/analyze_trajectory",
            json={
                "post_id": "test",
                "persona_id": "test",
                "content_segments": [],  # Empty segments
            },
        )
        assert response.status_code == 400

        # Test missing required fields
        response = client.post(
            "/emotion/analyze_trajectory",
            json={
                "content_segments": ["test content"]
                # Missing post_id and persona_id
            },
        )
        assert response.status_code == 400

        # Test invalid trajectory ID
        response = client.get("/emotion/trajectory/999999")
        assert response.status_code == 404

    def test_emotion_api_performance_monitoring(self, client, sample_content_segments):
        """Test that API endpoints meet performance requirements."""
        # Arrange
        request_payload = {
            "post_id": "performance_test",
            "persona_id": "test_persona",
            "content_segments": sample_content_segments,
        }

        with patch(
            "services.viral_pattern_engine.trajectory_mapper.TrajectoryMapper.map_emotion_trajectory"
        ) as mock_mapper:
            mock_mapper.return_value = {
                "arc_type": "rising",
                "emotion_progression": [{"joy": 0.7}] * 4,
                "peak_segments": [2],
                "valley_segments": [0],
                "emotional_variance": 0.4,
            }

            # Act & Assert - Measure response time
            import time

            start_time = time.time()
            response = client.post("/emotion/analyze_trajectory", json=request_payload)
            end_time = time.time()

            response_time_ms = (end_time - start_time) * 1000

            assert response.status_code == 200
            assert response_time_ms < 300  # Performance requirement

            result = response.json()
            assert "processing_time_ms" in result
            assert result["processing_time_ms"] < 300

    def test_batch_emotion_analysis_endpoint(self, client):
        """Test POST /emotion/analyze_batch endpoint for multiple content pieces."""
        # Arrange
        batch_request = {
            "analyses": [
                {
                    "post_id": "batch_1",
                    "persona_id": "viral_creator",
                    "content_segments": ["Happy content!", "Very excited now!"],
                },
                {
                    "post_id": "batch_2",
                    "persona_id": "viral_creator",
                    "content_segments": [
                        "Sad beginning.",
                        "Getting better.",
                        "Much happier!",
                    ],
                },
                {
                    "post_id": "batch_3",
                    "persona_id": "storyteller",
                    "content_segments": ["Neutral start.", "Staying steady."],
                },
            ],
            "store_results": False,
            "parallel_processing": True,
        }

        with patch(
            "services.viral_pattern_engine.trajectory_mapper.TrajectoryMapper.map_emotion_trajectory"
        ) as mock_mapper:
            # Return different results for each analysis
            mock_mapper.side_effect = [
                {
                    "arc_type": "rising",
                    "emotion_progression": [{"joy": 0.8}],
                    "peak_segments": [1],
                    "valley_segments": [],
                    "emotional_variance": 0.3,
                },
                {
                    "arc_type": "rising",
                    "emotion_progression": [{"joy": 0.9}],
                    "peak_segments": [2],
                    "valley_segments": [0],
                    "emotional_variance": 0.6,
                },
                {
                    "arc_type": "steady",
                    "emotion_progression": [{"trust": 0.7}],
                    "peak_segments": [],
                    "valley_segments": [],
                    "emotional_variance": 0.1,
                },
            ]

            # Act
            response = client.post("/emotion/analyze_batch", json=batch_request)

            # Assert
            assert response.status_code == 200
            result = response.json()

            assert len(result["results"]) == 3
            assert (
                result["batch_processing_time_ms"] < 1000
            )  # Batch performance requirement

            # Verify individual results
            results = result["results"]
            assert results[0]["post_id"] == "batch_1"
            assert results[0]["arc_type"] == "rising"
            assert results[1]["post_id"] == "batch_2"
            assert results[2]["post_id"] == "batch_3"
            assert results[2]["arc_type"] == "steady"
