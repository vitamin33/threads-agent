"""API integration tests for emotion trajectory endpoints."""

import pytest
from fastapi.testclient import TestClient

from services.viral_pattern_engine.main import app


@pytest.mark.e2e
class TestEmotionAPIIntegration:
    """Test emotion trajectory API endpoints."""

    @pytest.fixture
    def viral_client(self):
        """Create test client for viral pattern engine API testing."""
        return TestClient(app)

    def test_analyze_emotion_endpoint(self, viral_client):
        """Test POST /analyze/emotion endpoint."""
        # Arrange
        request_data = {
            "text": "I'm so excited about this amazing discovery! It's incredible.",
            "segments": None
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
            {"text": "Now everything is perfect!"}
        ]
        request_data = {
            "segments": segments,
            "persona_id": "test_persona"
        }

        # Act
        response = viral_client.post("/analyze/emotion-trajectory", json=request_data)

        # Assert
        assert response.status_code == 200
        result = response.json()
        
        assert "arc_type" in result
        assert "segments" in result
        assert "transitions" in result
        assert "metrics" in result
        assert result["persona_id"] == "test_persona"

    def test_analyze_emotion_transitions_endpoint(self, viral_client):
        """Test POST /analyze/emotion-transitions endpoint."""
        # Arrange
        segments = [
            {"text": "I was feeling anxious about this."},
            {"text": "But then I realized the solution!"},
            {"text": "Now I'm absolutely thrilled!"}
        ]
        request_data = {
            "segments": segments,
            "persona_id": "test_persona"
        }

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
            "description": "A pattern that creates immediate engagement"
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
        # Act
        trajectory_id = 12345
        response = viral_client.get(f"/trajectories/emotion/{trajectory_id}")

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["trajectory_id"] == trajectory_id
        assert result["arc_type"] == "rising"
        assert "segments" in result
        assert "transitions" in result
        assert "metrics" in result

    def test_get_emotion_trajectories_by_persona(self, viral_client):
        """Test GET /trajectories/emotion/persona/{persona_id} endpoint."""
        # Act
        persona_id = "viral_creator"
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
            "What an amazing surprise!"
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
        response = viral_client.post("/analyze/content-emotion-workflow", json=request_data)

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
        # Arrange
        template_id = 1
        engagement_rate = 0.08
        views = 1000

        # Act
        response = viral_client.put(
            f"/templates/emotion/{template_id}/performance",
            params={"engagement_rate": engagement_rate, "views": views}
        )

        # Assert
        assert response.status_code == 200
        result = response.json()

        assert result["template_id"] == template_id
        assert result["effectiveness_score"] == 0.8  # 0.08 * 10
        assert result["usage_count"] == views
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