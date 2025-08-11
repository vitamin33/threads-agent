"""
Test Viral Engine Integration with Content Scheduler Pipeline

This module tests the integration between the Content Scheduler and Viral Engine
following TDD methodology. Each test represents a specific behavior requirement.

Feature: Viral Engine Integration (Feature 25-2)
- Integrate Content Scheduler with Viral Engine for real-time content optimization
- Enable pattern extraction, engagement prediction, and quality scoring
- Implement quality gate (minimum 60% quality score)
- Create event-driven communication using the Event Bus
- Add viral hook optimization and emotion trajectory mapping
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.orchestrator.main import app
from services.orchestrator.db.models import ContentItem
from services.orchestrator.db import get_db_session


class TestViralEngineIntegration:
    """Test viral engine integration with content scheduler"""

    def test_content_creation_triggers_quality_check_event(self, db_session: Session):
        """
        Test that creating content triggers a ContentQualityCheckRequested event

        GIVEN: A content item creation request
        WHEN: Content is created via POST /api/v1/content
        THEN: A ContentQualityCheckRequested event should be published to event bus
        """
        # Override the database dependency to use test database
        app.dependency_overrides[get_db_session] = lambda: db_session

        client = TestClient(app)

        content_data = {
            "title": "Test viral content",
            "content": "This is a test post about AI trends",
            "content_type": "social_post",
            "author_id": "test_author",
            "status": "draft",
        }

        # Mock the event bus publisher
        with patch(
            "services.orchestrator.scheduling_router.publish_event"
        ) as mock_publish:
            response = client.post("/api/v1/content", json=content_data)

        # Clean up the dependency override
        app.dependency_overrides.clear()

        assert response.status_code == 201

        # Verify event was published
        mock_publish.assert_called_once()

        # Check event details
        call_args = mock_publish.call_args
        event_data = call_args[0][0]  # First argument

        assert event_data["event_type"] == "ContentQualityCheckRequested"
        assert event_data["payload"]["content_id"] is not None
        assert event_data["payload"]["content"] == content_data["content"]
        assert event_data["payload"]["title"] == content_data["title"]

    def test_quality_gate_endpoint_returns_quality_score(self, db_session: Session):
        """
        Test that there's a quality gate endpoint that returns quality scores

        GIVEN: A quality gate check request
        WHEN: POST /api/v1/content/{id}/quality-check is called
        THEN: It should return a quality score and pass/fail decision
        """
        # This test will fail - the endpoint doesn't exist yet
        app.dependency_overrides[get_db_session] = lambda: db_session
        client = TestClient(app)

        # First create content to check
        content_data = {
            "title": "Test viral content",
            "content": "This is a test post about AI trends",
            "content_type": "social_post",
            "author_id": "test_author",
            "status": "draft",
        }

        with patch("services.orchestrator.scheduling_router.publish_event"):
            create_response = client.post("/api/v1/content", json=content_data)

        content_id = create_response.json()["id"]

        # Now test quality check endpoint - this will fail
        response = client.post(f"/api/v1/content/{content_id}/quality-check")

        app.dependency_overrides.clear()

        # Test will fail here - endpoint doesn't exist yet
        assert response.status_code == 200

        result = response.json()
        assert "quality_score" in result
        assert "passes_quality_gate" in result
        assert "feature_scores" in result
        assert isinstance(result["quality_score"], float)
        assert 0 <= result["quality_score"] <= 1
        assert isinstance(result["passes_quality_gate"], bool)

    @patch("services.orchestrator.scheduling_router.call_viral_engine_api")
    def test_quality_check_calls_viral_engine_api(
        self, mock_viral_api, db_session: Session
    ):
        """
        Test that quality check endpoint calls the viral engine API

        GIVEN: A content quality check request
        WHEN: The quality check endpoint is called
        THEN: It should call the viral engine's predict/engagement endpoint
        """
        # This test will fail - call_viral_engine_api doesn't exist yet
        app.dependency_overrides[get_db_session] = lambda: db_session
        client = TestClient(app)

        # Mock the viral engine response
        mock_viral_api.return_value = {
            "quality_score": 0.85,
            "predicted_engagement_rate": 0.12,
            "feature_scores": {
                "engagement_potential": 0.9,
                "readability": 0.8,
                "viral_hooks": 0.85,
            },
            "improvement_suggestions": ["Add more emotional triggers"],
        }

        # Create content first
        content_data = {
            "title": "AI will revolutionize everything",
            "content": "Here's why AI is the most important technology of our time...",
            "content_type": "social_post",
            "author_id": "test_author",
            "status": "draft",
        }

        with patch("services.orchestrator.scheduling_router.publish_event"):
            create_response = client.post("/api/v1/content", json=content_data)

        content_id = create_response.json()["id"]

        # Call quality check endpoint
        response = client.post(f"/api/v1/content/{content_id}/quality-check")

        app.dependency_overrides.clear()

        # Should call viral engine API
        mock_viral_api.assert_called_once()
        call_args = mock_viral_api.call_args[1]  # keyword arguments

        assert call_args["endpoint"] == "/predict/engagement"
        assert call_args["data"]["content"] == content_data["content"]

        # Should return viral engine results
        result = response.json()
        assert result["quality_score"] == 0.85
        assert result["passes_quality_gate"]  # 0.85 > 0.6

    def test_quality_scored_event_updates_content_status(self, db_session: Session):
        """
        Test that ContentQualityScored event can update content status

        GIVEN: A ContentQualityScored event is received
        WHEN: handle_quality_scored_event is called
        THEN: Content should be updated with quality score and status
        """
        # This test will fail - handle_quality_scored_event doesn't exist yet
        app.dependency_overrides[get_db_session] = lambda: db_session
        client = TestClient(app)

        # Create content first
        content_data = {
            "title": "Test content for scoring",
            "content": "This content will be quality scored",
            "content_type": "social_post",
            "author_id": "test_author",
            "status": "draft",
        }

        with patch("services.orchestrator.scheduling_router.publish_event"):
            create_response = client.post("/api/v1/content", json=content_data)

        content_id = create_response.json()["id"]

        # Simulate ContentQualityScored event
        quality_event_data = {
            "content_id": content_id,
            "quality_score": 0.45,  # Below 60% threshold
            "predicted_engagement_rate": 0.03,
            "passes_quality_gate": False,
            "feature_scores": {
                "engagement_potential": 0.4,
                "readability": 0.5,
                "viral_hooks": 0.45,
            },
            "improvement_suggestions": [
                "Add more compelling hook",
                "Increase emotional appeal",
            ],
        }

        # This should fail - function doesn't exist yet
        from services.orchestrator.scheduling_router import handle_quality_scored_event

        result = handle_quality_scored_event(quality_event_data, db_session)

        app.dependency_overrides.clear()

        # Check the result
        assert result  # Function should return True for success

        # Refresh the session and check that content was updated
        db_session.refresh(
            db_session.query(ContentItem).filter(ContentItem.id == content_id).first()
        )
        updated_content = (
            db_session.query(ContentItem).filter(ContentItem.id == content_id).first()
        )

        # Should update metadata with quality info
        assert updated_content.content_metadata is not None
        assert updated_content.content_metadata.get("quality_score") == 0.45
        assert not updated_content.content_metadata.get("passes_quality_gate")
        assert updated_content.content_metadata.get("viral_engine_processed")

        # Should not auto-publish low quality content
        assert updated_content.status != "published"
