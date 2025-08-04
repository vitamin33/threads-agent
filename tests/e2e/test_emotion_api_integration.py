"""API integration tests for emotion trajectory endpoints."""

import pytest
from fastapi.testclient import TestClient

from services.viral_pattern_engine.main import app
from services.orchestrator.db import get_db_session


@pytest.mark.e2e
class TestEmotionAPIIntegration:
    """Test emotion trajectory API endpoints."""

    @pytest.fixture
    def viral_client(self):
        """Create test client for viral pattern engine API testing."""

        # For now, let's test without database dependency to isolate the core logic
        # We'll mock the database dependency
        def mock_db_session():
            from unittest.mock import MagicMock

            mock_session = MagicMock()
            mock_session.add = MagicMock()
            mock_session.commit = MagicMock()
            mock_session.flush = MagicMock()
            mock_session.refresh = MagicMock()
            mock_session.rollback = MagicMock()
            mock_session.get = MagicMock()
            mock_session.scalars = MagicMock()

            # Mock the trajectory and template objects
            mock_trajectory = MagicMock()
            mock_trajectory.id = 1
            mock_trajectory.post_id = "test_post"
            mock_trajectory.persona_id = "test_persona"
            mock_trajectory.trajectory_type = "rising"
            mock_trajectory.confidence_score = 0.8
            mock_trajectory.emotional_variance = 0.4
            mock_trajectory.peak_count = 1
            mock_trajectory.valley_count = 0
            mock_trajectory.created_at = None

            mock_template = MagicMock()
            mock_template.id = 1
            mock_template.template_name = "Test Template"
            mock_template.trajectory_pattern = "rising"
            mock_template.pattern_description = "Test description"
            mock_template.effectiveness_score = 0.8
            mock_template.is_active = True
            mock_template.usage_count = 1
            mock_template.average_engagement = 0.05
            mock_template.created_at = None
            mock_template.updated_at = None

            # Mock EmotionSegment and EmotionTransition for trajectory details
            mock_segment = MagicMock()
            mock_segment.segment_index = 0
            mock_segment.content_text = "Test segment"
            mock_segment.dominant_emotion = "joy"
            mock_segment.confidence_score = 0.8
            mock_segment.is_peak = False
            mock_segment.is_valley = False
            mock_segment.joy_score = 0.7
            mock_segment.anger_score = 0.1
            mock_segment.fear_score = 0.1
            mock_segment.sadness_score = 0.1
            mock_segment.surprise_score = 0.1
            mock_segment.disgust_score = 0.1
            mock_segment.trust_score = 0.5
            mock_segment.anticipation_score = 0.4

            mock_transition = MagicMock()
            mock_transition.from_segment_index = 0
            mock_transition.to_segment_index = 1
            mock_transition.from_emotion = "neutral"
            mock_transition.to_emotion = "joy"
            mock_transition.intensity_change = 0.3
            mock_transition.strength_score = 0.6

            # Configure mocks
            mock_session.refresh.side_effect = lambda obj: setattr(
                obj, "id", getattr(obj, "id", 1)
            )

            # Make get work dynamically based on model type
            def mock_get(model_class, id_value):
                if model_class.__name__ == "EmotionTrajectory":
                    return mock_trajectory
                elif model_class.__name__ == "EmotionTemplate":
                    return mock_template
                return None

            mock_session.get.side_effect = mock_get

            # Configure scalars for different query types
            mock_scalars_result = MagicMock()

            # Track what's being queried
            query_type = None

            def mock_scalars(query):
                # Detect what type of data is being queried
                nonlocal query_type
                query_str = str(query)
                if "EmotionSegment" in query_str:
                    query_type = "segments"
                elif "EmotionTransition" in query_str:
                    query_type = "transitions"
                elif "EmotionTemplate" in query_str:
                    query_type = "templates"
                else:
                    query_type = "trajectories"
                return mock_scalars_result

            def configure_scalars_all():
                # Return appropriate results based on query type
                if query_type == "segments":
                    return [mock_segment]
                elif query_type == "transitions":
                    return [mock_transition]
                elif query_type == "templates":
                    return [mock_template]
                else:
                    return [mock_trajectory]

            mock_scalars_result.all.side_effect = configure_scalars_all
            mock_session.scalars.side_effect = mock_scalars

            yield mock_session

        app.dependency_overrides[get_db_session] = mock_db_session
        client = TestClient(app)
        yield client
        # Clean up the override
        app.dependency_overrides.clear()

    def test_analyze_emotion_endpoint(self, viral_client):
        """Test POST /analyze/emotion endpoint."""
        # Arrange
        request_data = {
            "text": "I'm so excited about this amazing discovery! It's incredible.",
            "segments": None,
        }

        # Act
        response = viral_client.post("/analyze/emotion", json=request_data)

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert "emotions" in result
        assert "dominant_emotion" in result
        assert "confidence" in result
        assert isinstance(result["emotions"], dict)

    def test_analyze_emotion_trajectory_endpoint(self, viral_client):
        """Test POST /analyze/emotion-trajectory endpoint."""
        # Arrange
        segments = [
            {"text": "I was struggling with this problem."},
            {"text": "Then I found this amazing solution!"},
            {"text": "Now everything is perfect!"},
        ]
        request_data = {"segments": segments, "persona_id": "test_persona"}

        # Act
        response = viral_client.post("/analyze/emotion-trajectory", json=request_data)

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert "arc_type" in result
        assert "emotion_progression" in result
        assert "peak_segments" in result
        assert "valley_segments" in result
        assert "emotional_variance" in result
        assert "trajectory_id" in result
        assert result["persona_id"] == "test_persona"

    def test_analyze_emotion_transitions_endpoint(self, viral_client):
        """Test POST /analyze/emotion-transitions endpoint."""
        # Arrange
        segments = [
            {"text": "I was feeling anxious about this."},
            {"text": "But then I realized the solution!"},
            {"text": "Now I'm absolutely thrilled!"},
        ]
        request_data = {"segments": segments, "persona_id": "test_persona"}

        # Act
        response = viral_client.post("/analyze/emotion-transitions", json=request_data)

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert "transitions" in result
        assert "total_segments" in result
        assert "persona_id" in result
        assert len(result["transitions"]) == 2  # 3 segments = 2 transitions

    def test_create_emotion_template_endpoint(self, viral_client):
        """Test POST /templates/emotion endpoint."""
        # Arrange
        template_data = {
            "name": "Viral Hook Pattern",
            "trajectory_type": "rising",
            "emotion_sequence": ["anticipation", "surprise", "joy"],
            "description": "A pattern that creates immediate engagement",
        }

        # Act
        response = viral_client.post("/templates/emotion", json=template_data)

        # Assert
        assert response.status_code == 201
        result = response.json()

        assert result["name"] == "Viral Hook Pattern"
        assert result["trajectory_type"] == "rising"
        assert result["emotion_sequence"] == ["anticipation", "surprise", "joy"]
        assert result["is_active"] is True
        assert "template_id" in result

    def test_get_emotion_templates_endpoint(self, viral_client):
        """Test GET /templates/emotion endpoint."""
        # Arrange - First create a template
        template_data = {
            "name": "Test Template",
            "trajectory_type": "rising",
            "emotion_sequence": ["anticipation", "joy"],
            "description": "Test template for getting",
        }
        create_response = viral_client.post("/templates/emotion", json=template_data)
        assert create_response.status_code == 201

        # Act
        response = viral_client.get("/templates/emotion")

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert isinstance(result, list)
        assert len(result) >= 1
        for template in result:
            assert "template_id" in template
            assert "name" in template
            assert "effectiveness_score" in template

    def test_get_emotion_trajectory_by_id(self, viral_client):
        """Test GET /trajectories/emotion/{trajectory_id} endpoint."""
        # Arrange - First create a trajectory via the API
        segments = [
            {"text": "I was struggling with this problem."},
            {"text": "Then I found this amazing solution!"},
            {"text": "Now everything is perfect!"},
        ]
        create_response = viral_client.post(
            "/analyze/emotion-trajectory",
            json={"segments": segments, "persona_id": "test_persona"},
        )
        assert create_response.status_code == 200
        trajectory_id = create_response.json()["trajectory_id"]

        # Act
        response = viral_client.get(f"/trajectories/emotion/{trajectory_id}")

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["trajectory_id"] == trajectory_id
        assert "arc_type" in result
        assert "segments" in result
        assert "transitions" in result
        assert "metrics" in result
        assert result["persona_id"] == "test_persona"

    def test_get_emotion_trajectories_by_persona(self, viral_client):
        """Test GET /trajectories/emotion/persona/{persona_id} endpoint."""
        # Arrange - First create a trajectory for this persona
        persona_id = "viral_creator"
        segments = [
            {"text": "Starting my journey."},
            {"text": "Making great progress!"},
            {"text": "Achievement unlocked!"},
        ]
        create_response = viral_client.post(
            "/analyze/emotion-trajectory",
            json={"segments": segments, "persona_id": persona_id},
        )
        assert create_response.status_code == 200

        # Act
        response = viral_client.get(f"/trajectories/emotion/persona/{persona_id}")

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0]["persona_id"] == persona_id

    def test_batch_emotion_analysis_endpoint(self, viral_client):
        """Test POST /batch/emotion-analysis endpoint."""
        # Arrange
        texts = [
            "I'm so excited about this!",
            "This is really disappointing.",
            "What an amazing surprise!",
        ]

        # Act
        response = viral_client.post("/batch/emotion-analysis", json=texts)

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert "results" in result
        assert "total_texts" in result
        assert "total_processing_time_ms" in result
        assert len(result["results"]) == 3
        assert result["total_texts"] == 3

    def test_analyze_content_emotion_workflow_endpoint(self, viral_client):
        """Test POST /analyze/content-emotion-workflow endpoint."""
        # Arrange
        request_data = {
            "content": "I started with doubt. Then I discovered something amazing. Now I'm incredibly happy!"
        }

        # Act
        response = viral_client.post(
            "/analyze/content-emotion-workflow", json=request_data
        )

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert "segments" in result
        assert "trajectory" in result
        assert "patterns" in result
        assert "recommendations" in result
        assert len(result["segments"]) >= 2

    def test_update_template_performance_endpoint(self, viral_client):
        """Test PUT /templates/emotion/{template_id}/performance endpoint."""
        # Arrange - First create a template
        template_data = {
            "name": "Performance Test Template",
            "trajectory_type": "rising",
            "emotion_sequence": ["anticipation", "joy"],
            "description": "Template for performance testing",
        }
        create_response = viral_client.post("/templates/emotion", json=template_data)
        assert create_response.status_code == 201
        template_id = create_response.json()["template_id"]

        engagement_rate = 0.08
        views = 1000

        # Act
        response = viral_client.put(
            f"/templates/emotion/{template_id}/performance",
            params={"engagement_rate": engagement_rate, "views": views},
        )

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["template_id"] == template_id
        assert "effectiveness_score" in result
        assert result["usage_count"] >= 1  # Should be incremented
        assert "updated_at" in result

    def test_health_endpoint(self, viral_client):
        """Test GET /health endpoint."""
        # Act
        response = viral_client.get("/health")

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["status"] == "healthy"
        assert result["service"] == "viral_pattern_engine"
