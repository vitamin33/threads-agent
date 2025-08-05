"""
Tests for Achievement Collector API Client
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.clients.achievement_client import (
    AchievementClient,
    Achievement,
    AchievementListResponse,
    get_achievement_client,
)


@pytest.fixture
def mock_achievement():
    """Sample achievement data"""
    return {
        "id": 1,
        "title": "Implemented Kubernetes Auto-scaling",
        "description": "Reduced infrastructure costs by 40% through intelligent auto-scaling",
        "category": "infrastructure",
        "impact_score": 85.5,
        "business_value": "$50K annual savings",
        "technical_details": {
            "technology": "Kubernetes HPA",
            "metrics": ["CPU", "Memory", "Custom Metrics"],
        },
        "metrics": {"cost_reduction": 40.0, "performance_improvement": 25.0},
        "tags": ["kubernetes", "cost-optimization", "devops"],
        "portfolio_ready": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@pytest.fixture
def achievement_client():
    """Achievement client instance"""
    return AchievementClient(
        base_url="http://test-collector:8000", api_key="test-api-key"
    )


@pytest.mark.asyncio
async def test_get_achievement_success(achievement_client, mock_achievement):
    """Test successful achievement fetch"""
    with patch.object(achievement_client, "_client") as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_achievement)

        mock_client.get = AsyncMock(return_value=mock_response)
        achievement_client._client = mock_client

        result = await achievement_client.get_achievement(1)

        assert isinstance(result, Achievement)
        assert result.id == 1
        assert result.title == "Implemented Kubernetes Auto-scaling"
        assert result.impact_score == 85.5

        mock_client.get.assert_called_once_with("/achievements/1")


@pytest.mark.asyncio
async def test_get_achievement_not_found(achievement_client):
    """Test achievement not found returns None"""
    with patch.object(achievement_client, "_client") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 404

        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )
        )
        achievement_client._client = mock_client

        result = await achievement_client.get_achievement(999)
        assert result is None


@pytest.mark.asyncio
async def test_list_achievements_with_filters(achievement_client, mock_achievement):
    """Test listing achievements with various filters"""
    mock_response_data = {
        "achievements": [mock_achievement],
        "total": 1,
        "page": 1,
        "page_size": 20,
    }

    with patch.object(achievement_client, "_client") as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_response_data)

        mock_client.get = AsyncMock(return_value=mock_response)
        achievement_client._client = mock_client

        result = await achievement_client.list_achievements(
            category="infrastructure",
            min_impact_score=80.0,
            portfolio_ready_only=True,
            tags=["kubernetes", "devops"],
        )

        assert isinstance(result, AchievementListResponse)
        assert result.total == 1
        assert len(result.achievements) == 1
        assert result.achievements[0].id == 1

        # Verify API call parameters
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["category"] == "infrastructure"
        assert params["min_impact_score"] == 80.0
        assert params["portfolio_ready_only"] is True
        assert params["tags"] == "kubernetes,devops"


@pytest.mark.asyncio
async def test_get_by_category(achievement_client, mock_achievement):
    """Test getting achievements by category"""
    mock_response_data = {
        "achievements": [mock_achievement],
        "total": 1,
        "page": 1,
        "page_size": 10,
    }

    with patch.object(achievement_client, "list_achievements") as mock_list:
        mock_list.return_value = AchievementListResponse(**mock_response_data)

        results = await achievement_client.get_by_category("infrastructure", limit=5)

        assert len(results) == 1
        assert results[0].category == "infrastructure"

        mock_list.assert_called_once_with(
            category="infrastructure",
            page_size=5,
            sort_by="impact_score",
            sort_order="desc",
        )


@pytest.mark.asyncio
async def test_get_recent_achievements(achievement_client, mock_achievement):
    """Test getting recent high-impact achievements"""
    mock_response_data = {
        "achievements": [mock_achievement],
        "total": 1,
        "page": 1,
        "page_size": 20,
    }

    with patch.object(achievement_client, "list_achievements") as mock_list:
        mock_list.return_value = AchievementListResponse(**mock_response_data)

        results = await achievement_client.get_recent_achievements(
            days=7, min_impact_score=75.0
        )

        assert len(results) == 1
        assert results[0].impact_score >= 75.0

        # Verify date filter was applied
        call_args = mock_list.call_args[1]
        assert "start_date" in call_args
        assert call_args["min_impact_score"] == 75.0
        assert call_args["portfolio_ready_only"] is True


@pytest.mark.asyncio
async def test_batch_get_achievements(achievement_client, mock_achievement):
    """Test batch fetching multiple achievements"""
    achievement2 = mock_achievement.copy()
    achievement2["id"] = 2
    achievement2["title"] = "Another Achievement"

    with patch.object(achievement_client, "get_achievement") as mock_get:
        mock_get.side_effect = [
            Achievement(**mock_achievement),
            Achievement(**achievement2),
            None,  # Third one not found
        ]

        results = await achievement_client.batch_get_achievements([1, 2, 999])

        assert len(results) == 2
        assert results[0].id == 1
        assert results[1].id == 2
        assert mock_get.call_count == 3


@pytest.mark.asyncio
async def test_caching_behavior(achievement_client, mock_achievement):
    """Test that caching prevents duplicate API calls"""
    with patch.object(achievement_client, "_client") as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_achievement)

        mock_client.get = AsyncMock(return_value=mock_response)
        achievement_client._client = mock_client

        # First call should hit API
        result1 = await achievement_client.get_achievement(1)
        assert mock_client.get.call_count == 1

        # Second call should use cache
        result2 = await achievement_client.get_achievement(1)
        assert mock_client.get.call_count == 1  # No additional call

        assert result1.id == result2.id


@pytest.mark.asyncio
async def test_context_manager_usage():
    """Test using client as async context manager"""
    async with AchievementClient(base_url="http://test:8000") as client:
        assert client._client is not None
        assert isinstance(client._client, httpx.AsyncClient)


def test_singleton_client():
    """Test that get_achievement_client returns singleton"""
    client1 = get_achievement_client()
    client2 = get_achievement_client()
    assert client1 is client2


@pytest.mark.asyncio
async def test_retry_on_failure(achievement_client, mock_achievement):
    """Test retry logic on transient failures"""
    with patch.object(achievement_client, "_client") as mock_client:
        # First two calls fail, third succeeds
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=mock_achievement)

        mock_client.get = AsyncMock(
            side_effect=[
                httpx.ConnectError("Connection failed"),
                httpx.ConnectError("Connection failed"),
                mock_response,
            ]
        )
        achievement_client._client = mock_client

        result = await achievement_client.get_achievement(1)

        assert result is not None
        assert result.id == 1
        assert mock_client.get.call_count == 3


@pytest.mark.asyncio
async def test_batch_get_optimized_endpoint(achievement_client, mock_achievement):
    """Test the new optimized batch-get endpoint"""
    achievement2 = mock_achievement.copy()
    achievement2["id"] = 2
    achievement2["title"] = "Second Achievement"

    with patch.object(achievement_client, "_make_request") as mock_request:
        mock_request.return_value = [mock_achievement, achievement2]

        results = await achievement_client.batch_get_achievements([1, 2])

        assert len(results) == 2
        assert results[0].id == 1
        assert results[1].id == 2

        mock_request.assert_called_once_with(
            "POST", "/tech-doc-integration/batch-get", json={"achievement_ids": [1, 2]}
        )


@pytest.mark.asyncio
async def test_get_recent_highlights_optimized(achievement_client, mock_achievement):
    """Test the new get_recent_highlights method using optimized endpoint"""
    with patch.object(achievement_client, "_make_request") as mock_request:
        mock_request.return_value = [mock_achievement]

        results = await achievement_client.get_recent_highlights(
            days=14, min_impact_score=80.0, limit=5
        )

        assert len(results) == 1
        assert results[0].id == 1
        assert results[0].impact_score == 85.5

        mock_request.assert_called_once_with(
            "POST",
            "/tech-doc-integration/recent-highlights",
            params={"days": 14, "min_impact_score": 80.0, "limit": 5},
        )


@pytest.mark.asyncio
async def test_get_company_targeted(achievement_client, mock_achievement):
    """Test the new get_company_targeted method"""
    # Create AI/ML focused achievement
    ai_achievement = mock_achievement.copy()
    ai_achievement["category"] = "ai_ml"
    ai_achievement["tags"] = ["ai", "machine-learning", "automation"]
    ai_achievement["title"] = "AI Content Generation Pipeline"

    with patch.object(achievement_client, "_make_request") as mock_request:
        mock_request.return_value = [ai_achievement]

        results = await achievement_client.get_company_targeted(
            company_name="anthropic", categories=["ai_ml", "automation"], limit=10
        )

        assert len(results) == 1
        assert results[0].category == "ai_ml"
        assert "ai" in results[0].tags

        mock_request.assert_called_once_with(
            "POST",
            "/tech-doc-integration/company-targeted",
            params={
                "company_name": "anthropic",
                "categories": ["ai_ml", "automation"],
                "limit": 10,
            },
        )


@pytest.mark.asyncio
async def test_get_company_targeted_without_categories(
    achievement_client, mock_achievement
):
    """Test company targeting without category filter"""
    with patch.object(achievement_client, "_make_request") as mock_request:
        mock_request.return_value = [mock_achievement]

        results = await achievement_client.get_company_targeted("notion")

        assert len(results) == 1

        mock_request.assert_called_once_with(
            "POST",
            "/tech-doc-integration/company-targeted",
            params={"company_name": "notion", "limit": 20},
        )


@pytest.mark.asyncio
async def test_make_request_get_method(achievement_client):
    """Test _make_request with GET method"""
    with patch.object(achievement_client, "_client") as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"test": "data"})

        mock_client.get = AsyncMock(return_value=mock_response)
        achievement_client._client = mock_client

        result = await achievement_client._make_request(
            "GET", "/test", params={"q": "test"}
        )

        assert result == {"test": "data"}
        mock_client.get.assert_called_once_with("/test", params={"q": "test"})


@pytest.mark.asyncio
async def test_make_request_post_method(achievement_client):
    """Test _make_request with POST method"""
    with patch.object(achievement_client, "_client") as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"created": True})

        mock_client.post = AsyncMock(return_value=mock_response)
        achievement_client._client = mock_client

        result = await achievement_client._make_request(
            "POST", "/create", json={"data": "test"}
        )

        assert result == {"created": True}
        mock_client.post.assert_called_once_with("/create", json={"data": "test"})


@pytest.mark.asyncio
async def test_make_request_404_handling(achievement_client):
    """Test _make_request handles 404 correctly"""
    with patch.object(achievement_client, "_client") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 404

        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )
        )
        achievement_client._client = mock_client

        result = await achievement_client._make_request("GET", "/not-found")

        assert result is None


@pytest.mark.asyncio
async def test_make_request_unsupported_method(achievement_client):
    """Test _make_request with unsupported HTTP method"""
    with pytest.raises(ValueError, match="Unsupported method: PATCH"):
        await achievement_client._make_request("PATCH", "/test")


@pytest.mark.asyncio
async def test_batch_get_empty_list(achievement_client):
    """Test batch_get_achievements with empty achievement_ids list"""
    result = await achievement_client.batch_get_achievements([])
    assert result == []


@pytest.mark.asyncio
async def test_get_recent_highlights_no_results(achievement_client):
    """Test get_recent_highlights when no achievements found"""
    with patch.object(achievement_client, "_make_request") as mock_request:
        mock_request.return_value = None

        results = await achievement_client.get_recent_highlights()

        assert results == []


@pytest.mark.asyncio
async def test_get_company_targeted_no_results(achievement_client):
    """Test get_company_targeted when no achievements found"""
    with patch.object(achievement_client, "_make_request") as mock_request:
        mock_request.return_value = None

        results = await achievement_client.get_company_targeted("unknown-company")

        assert results == []
