"""
Test Suite for Achievement Collector Integration with Content Scheduler

This test suite covers integration between Achievement Collector service
and the existing Content Scheduler endpoints.

New Endpoints to Test:
- POST /api/v1/content/achievement-based - Create content from achievements
- GET /api/v1/content/{id}/achievements - Get achievements used for content  
- POST /api/v1/schedules/achievement-digest - Schedule weekly achievement digest

Following TDD methodology - these tests will FAIL until we implement the functionality.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.orchestrator.main import app
from services.orchestrator.db.models import ContentItem, ContentSchedule
from services.orchestrator.scheduling_schemas import ContentItemCreate
from services.orchestrator.db import get_db_session


class TestAchievementBasedContentEndpoints:
    """Test new achievement-based content creation endpoints."""
    
    @pytest.fixture
    def client(self, db_session):
        def override_get_db_session():
            return db_session
        
        app.dependency_overrides[get_db_session] = override_get_db_session
        
        with TestClient(app) as test_client:
            yield test_client
        
        app.dependency_overrides.clear()
    
    def test_create_achievement_based_content_endpoint_fails(self, client):
        """Test POST /api/v1/content/achievement-based endpoint (will fail until implemented)."""
        
        request_payload = {
            "author_id": "test_author",
            "content_type": "blog_post",
            "target_platform": "linkedin",
            "company_context": "tech_startup",
            "achievement_filters": {
                "category": "development",
                "min_impact_score": 80.0,
                "min_business_value": 1000.0,
                "portfolio_ready": True
            },
            "max_achievements": 5,
            "priority_threshold": 75.0,
            "content_config": {
                "tone": "professional",
                "max_word_count": 500,
                "include_metrics": True
            }
        }
        
        # This will fail - endpoint doesn't exist yet
        response = client.post("/api/v1/content/achievement-based", json=request_payload)
        
        # Debug: Print response details if not 201
        if response.status_code != 201:
            print(f"Status: {response.status_code}, Response: {response.text}")
        
        assert response.status_code == 201
        response_data = response.json()
        
        assert "id" in response_data
        assert response_data["content_type"] == "blog_post"
        assert response_data["author_id"] == "test_author"
        assert "achievement_ids" in response_data["content_metadata"]
        assert len(response_data["content_metadata"]["achievement_ids"]) <= 5
        
        # Content should include achievement-derived data
        assert "achievements" in response_data["content"].lower() or \
               "impact" in response_data["content"].lower()
               
    def test_get_content_achievements_endpoint_fails(self, client):
        """Test GET /api/v1/content/{id}/achievements endpoint (will fail until implemented)."""
        
        # This will fail - endpoint doesn't exist yet
        response = client.get("/api/v1/content/123/achievements")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert "content_id" in response_data
        assert "achievements" in response_data
        assert isinstance(response_data["achievements"], list)
        assert "generation_metadata" in response_data
        
        # Should include achievement selection criteria used
        assert "selection_criteria" in response_data["generation_metadata"]
        assert "selected_count" in response_data["generation_metadata"]
        
    def test_schedule_achievement_digest_endpoint_fails(self, client):
        """Test POST /api/v1/schedules/achievement-digest endpoint (will fail until implemented)."""
        
        digest_request = {
            "author_id": "test_author",
            "platform": "linkedin",
            "scheduled_time": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "digest_config": {
                "week_start": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
                "week_end": datetime.now(timezone.utc).isoformat(),
                "min_impact_threshold": 80.0,
                "max_achievements": 10,
                "group_by_category": True
            },
            "content_config": {
                "tone": "professional",
                "include_stats": True,
                "highlight_top_achievement": True
            }
        }
        
        # This will fail - endpoint doesn't exist yet
        response = client.post("/api/v1/schedules/achievement-digest", json=digest_request)
        
        assert response.status_code == 201
        response_data = response.json()
        
        assert "schedule_id" in response_data
        assert "content_id" in response_data
        assert response_data["platform"] == "linkedin"
        assert response_data["content_type"] == "achievement_digest"
        
        # Should have generated digest content
        assert "digest_preview" in response_data
        assert "achievements_count" in response_data["digest_preview"]


class TestAchievementEventPublishing:
    """Test event publishing integration with achievement-based content creation."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch('services.orchestrator.achievement_integration.AchievementCollectorClient')
    def test_achievement_content_requested_event_published(self, mock_client_class, client):
        """Test that AchievementContentRequested event is published when creating achievement content."""
        
        # This will fail - event publishing integration doesn't exist yet
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.get_achievements.return_value = {
            'items': [
                {'id': 1, 'title': 'Test Achievement', 'impact_score': 90.0}
            ],
            'total': 1
        }
        
        request_payload = {
            "author_id": "test_author",
            "content_type": "blog_post",
            "target_platform": "linkedin",
            "achievement_filters": {"category": "development"},
            "max_achievements": 3
        }
        
        with patch('services.orchestrator.scheduling_router.publish_event') as mock_publish:
            # This will fail - endpoint doesn't exist yet
            response = client.post("/api/v1/content/achievement-based", json=request_payload)
            
            assert response.status_code == 201
            
            # Verify event was published
            mock_publish.assert_called_once()
            event_data = mock_publish.call_args[0][0]
            
            assert event_data['event_type'] == 'AchievementContentRequested'
            assert 'content_id' in event_data['payload']
            assert event_data['payload']['author_id'] == 'test_author'
            assert event_data['payload']['target_platform'] == 'linkedin'
            
    @patch('services.orchestrator.achievement_integration.AchievementCollectorClient')
    def test_achievement_content_generated_event_published(self, mock_client_class, client):
        """Test that AchievementContentGenerated event is published after content generation."""
        
        # This will fail - event publishing integration doesn't exist yet
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.get_achievements.return_value = {
            'items': [
                {'id': 1, 'title': 'Test Achievement 1', 'impact_score': 95.0},
                {'id': 2, 'title': 'Test Achievement 2', 'impact_score': 88.0}
            ],
            'total': 2
        }
        
        request_payload = {
            "author_id": "test_author",
            "content_type": "social_post",
            "target_platform": "twitter",
            "achievement_filters": {"min_impact_score": 85.0},
            "max_achievements": 2
        }
        
        with patch('services.orchestrator.scheduling_router.publish_event') as mock_publish:
            # This will fail - endpoint doesn't exist yet
            response = client.post("/api/v1/content/achievement-based", json=request_payload)
            
            assert response.status_code == 201
            
            # Should have published both request and generated events
            assert mock_publish.call_count == 2
            
            # Check the second event is AchievementContentGenerated
            generated_event = mock_publish.call_args_list[1][0][0]
            assert generated_event['event_type'] == 'AchievementContentGenerated'
            assert 'achievement_ids' in generated_event['payload']
            assert len(generated_event['payload']['achievement_ids']) == 2


class TestAchievementCollectorServiceIntegration:
    """Test actual HTTP integration with Achievement Collector service."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
        
    @patch('httpx.AsyncClient')
    def test_real_achievement_collector_api_integration(self, mock_httpx_client, client):
        """Test real HTTP calls to Achievement Collector service."""
        
        # Mock the HTTP response from achievement collector
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'id': 1,
                    'title': 'Database Optimization',
                    'impact_score': 95.0,
                    'business_value': '$5000',
                    'category': 'performance',
                    'time_saved_hours': 40.0
                },
                {
                    'id': 2,
                    'title': 'CI/CD Pipeline Setup', 
                    'impact_score': 88.0,
                    'business_value': '$3000',
                    'category': 'automation',
                    'time_saved_hours': 25.0
                }
            ],
            'total': 2
        }
        mock_response.status_code = 200
        
        # Configure the mock client
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response
        
        request_payload = {
            "author_id": "test_author",
            "content_type": "blog_post",
            "target_platform": "linkedin",
            "achievement_filters": {
                "category": "performance",
                "min_impact_score": 90.0
            },
            "max_achievements": 2
        }
        
        # This will fail - endpoint and HTTP integration doesn't exist yet
        response = client.post("/api/v1/content/achievement-based", json=request_payload)
        
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify achievement data was used in content generation
        content_metadata = response_data.get("content_metadata", {})
        assert "achievement_ids" in content_metadata
        assert content_metadata["achievement_ids"] == [1, 2]
        
        # Content should mention specific achievements
        content_text = response_data.get("content", "").lower()
        assert "database" in content_text or "optimization" in content_text
        assert "40" in response_data.get("content", "") or "hours" in content_text
        
    @patch('httpx.AsyncClient')
    def test_achievement_usage_tracking_integration(self, mock_httpx_client, client):
        """Test tracking achievement usage back to Achievement Collector."""
        
        # Mock achievement fetch response
        mock_get_response = Mock()
        mock_get_response.json.return_value = {
            'items': [{'id': 1, 'title': 'Test Achievement', 'impact_score': 90.0}],
            'total': 1
        }
        mock_get_response.status_code = 200
        
        # Mock usage tracking response
        mock_post_response = Mock()
        mock_post_response.json.return_value = {'status': 'tracked', 'id': 789}
        mock_post_response.status_code = 201
        
        # Configure the mock client
        mock_client_instance = AsyncMock()
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_get_response
        mock_client_instance.post.return_value = mock_post_response
        
        # Create achievement-based content
        create_request = {
            "author_id": "test_author",
            "content_type": "social_post",
            "target_platform": "twitter",
            "achievement_filters": {"min_impact_score": 85.0},
            "max_achievements": 1
        }
        
        # This will fail - endpoint doesn't exist yet
        create_response = client.post("/api/v1/content/achievement-based", json=create_request)
        assert create_response.status_code == 201
        
        content_id = create_response.json()["id"]
        
        # Simulate content performance data (this endpoint will also fail)
        performance_data = {
            "views": 1500,
            "likes": 120,
            "comments": 15,
            "shares": 8,
            "engagement_rate": 0.095
        }
        
        # This will fail - endpoint doesn't exist yet  
        track_response = client.post(f"/api/v1/content/{content_id}/track-performance", json=performance_data)
        assert track_response.status_code == 200
        
        # Verify usage was tracked back to Achievement Collector
        # Should have made POST request to track usage
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        
        assert '/achievements/track-usage' in call_args[1]['url']
        usage_payload = call_args[1]['json']
        assert 'achievement_ids' in usage_payload
        assert 'performance_metrics' in usage_payload
        assert usage_payload['performance_metrics']['engagement_rate'] == 0.095


class TestAchievementWebSocketIntegration:
    """Test WebSocket integration for real-time achievement updates."""
    
    @patch('websockets.connect')
    @pytest.mark.asyncio
    async def test_websocket_achievement_updates(self, mock_websocket_connect):
        """Test WebSocket connection for real-time achievement updates."""
        
        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket_connect.return_value.__aenter__.return_value = mock_websocket
        
        # Mock incoming achievement update
        mock_websocket.recv.side_effect = [
            '{"type": "achievement_created", "data": {"id": 123, "title": "New Achievement", "impact_score": 92.0}}',
            '{"type": "achievement_updated", "data": {"id": 124, "title": "Updated Achievement"}}'
        ]
        
        # This will fail - WebSocket integration doesn't exist yet
        from services.orchestrator.achievement_integration import AchievementWebSocketClient
        
        ws_client = AchievementWebSocketClient("ws://achievement-collector:8080/ws")
        
        updates = []
        async for update in ws_client.listen_for_updates():
            updates.append(update)
            if len(updates) >= 2:
                break
                
        assert len(updates) == 2
        assert updates[0]['type'] == 'achievement_created'
        assert updates[0]['data']['id'] == 123
        assert updates[1]['type'] == 'achievement_updated'
        

class TestAchievementContentSchedulingWorkflow:
    """Test end-to-end workflow of achievement-based content scheduling."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
        
    @patch('services.orchestrator.achievement_integration.AchievementCollectorClient')
    def test_complete_achievement_content_workflow(self, mock_client_class, client):
        """Test complete workflow from achievement selection to content scheduling."""
        
        # Mock Achievement Collector responses
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        mock_client.get_achievements.return_value = {
            'items': [
                {
                    'id': 1,
                    'title': 'Performance Optimization',
                    'impact_score': 95.0,
                    'business_value': '$8000',
                    'time_saved_hours': 50.0
                }
            ],
            'total': 1
        }
        
        mock_client.track_usage.return_value = {'status': 'tracked', 'id': 999}
        
        # Step 1: Create achievement-based content (will fail)
        content_request = {
            "author_id": "test_author",
            "content_type": "blog_post",
            "target_platform": "linkedin",
            "achievement_filters": {"min_impact_score": 90.0},
            "max_achievements": 1
        }
        
        content_response = client.post("/api/v1/content/achievement-based", json=content_request)
        assert content_response.status_code == 201
        
        content_id = content_response.json()["id"]
        
        # Step 2: Schedule the content (existing endpoint should work)
        schedule_request = {
            "content_item_id": content_id,
            "platform": "linkedin",
            "scheduled_time": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        }
        
        schedule_response = client.post("/api/v1/schedules", json=schedule_request)
        assert schedule_response.status_code == 201
        
        schedule_id = schedule_response.json()["id"]
        
        # Step 3: Verify content has achievement metadata
        content_detail_response = client.get(f"/api/v1/content/{content_id}")
        assert content_detail_response.status_code == 200
        
        content_data = content_detail_response.json()
        assert "achievement_ids" in content_data["content_metadata"]
        assert content_data["content_metadata"]["achievement_ids"] == [1]
        
        # Step 4: Get achievement details for this content (will fail)
        achievements_response = client.get(f"/api/v1/content/{content_id}/achievements")
        assert achievements_response.status_code == 200
        
        achievements_data = achievements_response.json()
        assert len(achievements_data["achievements"]) == 1
        assert achievements_data["achievements"][0]["title"] == "Performance Optimization"