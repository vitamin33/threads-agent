"""Tests for Historical PR Analyzer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime

from services.historical_pr_analyzer import HistoricalPRAnalyzer


class TestHistoricalPRAnalyzer:
    """Test Historical PR Analyzer functionality."""

    def test_analyzer_initialization(self):
        """Test that analyzer can be initialized with GitHub token."""
        analyzer = HistoricalPRAnalyzer(github_token="test-token")
        assert analyzer.github_token == "test-token"
        assert analyzer.rate_limit_remaining > 0

    @pytest.mark.asyncio
    async def test_fetch_all_prs_returns_list(self):
        """Test that fetch_all_prs returns a list of PRs."""
        analyzer = HistoricalPRAnalyzer(github_token="test-token")

        # Mock the GitHub API response
        mock_prs = [
            {
                "number": 1,
                "title": "Initial commit",
                "state": "closed",
                "merged_at": "2024-01-01T00:00:00Z",
            }
        ]

        with patch.object(
            analyzer, "_fetch_page", new_callable=AsyncMock
        ) as mock_fetch:
            # First call returns data, second returns empty list to stop pagination
            mock_fetch.side_effect = [mock_prs, []]

            prs = await analyzer.fetch_all_prs("threads-agent-stack/threads-agent")

            assert isinstance(prs, list)
            assert len(prs) == 1
            assert prs[0]["number"] == 1

    @pytest.mark.asyncio
    async def test_fetch_all_prs_handles_pagination(self):
        """Test that fetch_all_prs handles GitHub API pagination."""
        analyzer = HistoricalPRAnalyzer(github_token="test-token")

        # Mock paginated responses
        page1 = [{"number": 1}, {"number": 2}]
        page2 = [{"number": 3}, {"number": 4}]
        page3 = []  # Empty page indicates end

        with patch.object(
            analyzer, "_fetch_page", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.side_effect = [page1, page2, page3]

            prs = await analyzer.fetch_all_prs("owner/repo")

            assert len(prs) == 4
            assert [pr["number"] for pr in prs] == [1, 2, 3, 4]
            assert mock_fetch.call_count == 3

    @pytest.mark.asyncio
    async def test_respects_github_rate_limit(self):
        """Test that analyzer respects GitHub API rate limits."""
        analyzer = HistoricalPRAnalyzer(github_token="test-token")
        analyzer.rate_limit_remaining = 10

        # Mock response headers with rate limit info
        mock_headers = {
            "X-RateLimit-Remaining": "5",
            "X-RateLimit-Reset": str(int(datetime.now().timestamp()) + 3600),
        }

        with patch.object(
            analyzer, "_make_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = ([], mock_headers)

            await analyzer._fetch_page("owner/repo", 1)

            # Should update rate limit
            assert analyzer.rate_limit_remaining == 5

            # When rate limit is low, should wait
            analyzer.rate_limit_remaining = 1
            mock_headers["X-RateLimit-Remaining"] = "0"

            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await analyzer._fetch_page("owner/repo", 2)
                mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_pr_details(self):
        """Test collecting detailed PR data including files, commits, and reviews."""
        analyzer = HistoricalPRAnalyzer(github_token="test-token")

        pr_number = 123
        expected_details = {
            "number": pr_number,
            "title": "feat: Add new feature",
            "body": "Description of the feature",
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
            "commits": [
                {"sha": "abc123", "message": "Initial implementation"},
                {"sha": "def456", "message": "Fix tests"},
            ],
            "files": [
                {"filename": "feature.py", "additions": 80, "deletions": 30},
                {"filename": "test_feature.py", "additions": 20, "deletions": 20},
            ],
            "reviews": [
                {"user": "reviewer1", "state": "APPROVED"},
                {"user": "reviewer2", "state": "CHANGES_REQUESTED"},
            ],
            "labels": ["feature", "needs-review"],
            "merged_at": "2024-01-15T10:00:00Z",
            "created_at": "2024-01-10T10:00:00Z",
        }

        with patch.object(
            analyzer, "_get_pr_details", new_callable=AsyncMock
        ) as mock_details:
            mock_details.return_value = expected_details

            details = await analyzer.collect_pr_details("owner/repo", pr_number)

            assert details["number"] == pr_number
            assert details["additions"] == 100
            assert len(details["commits"]) == 2
            assert len(details["files"]) == 2
            assert details["files"][0]["filename"] == "feature.py"

    @pytest.mark.asyncio
    async def test_analyze_business_impact(self):
        """Test analyzing business impact of a PR."""
        analyzer = HistoricalPRAnalyzer(github_token="test-token")

        pr_data = {
            "number": 123,
            "title": "feat: Add payment processing",
            "body": "Implemented Stripe integration for payment processing",
            "additions": 500,
            "deletions": 100,
            "files": [
                {"filename": "payment_processor.py", "additions": 300},
                {"filename": "stripe_integration.py", "additions": 200},
            ],
        }

        expected_analysis = {
            "business_value": "HIGH",
            "impact_score": 85,
            "development_time_hours": 16,
            "roi_projection": {
                "potential_revenue_increase": "$50,000/month",
                "cost_savings": "$10,000/month",
                "payback_period_days": 30,
            },
            "key_benefits": [
                "Enables online payments",
                "Reduces manual processing",
                "Improves customer experience",
            ],
        }

        with patch.object(
            analyzer, "_call_ai_analyzer", new_callable=AsyncMock
        ) as mock_ai:
            mock_ai.return_value = expected_analysis

            impact = await analyzer.analyze_business_impact(pr_data)

            assert impact["business_value"] == "HIGH"
            assert impact["impact_score"] == 85
            assert impact["development_time_hours"] == 16
            assert "potential_revenue_increase" in impact["roi_projection"]

    @pytest.mark.asyncio
    async def test_analyze_repository_history(self):
        """Test analyzing complete repository PR history."""
        analyzer = HistoricalPRAnalyzer(github_token="test-token")

        # Mock PR list
        mock_prs = [
            {
                "number": 1,
                "title": "Initial commit",
                "merged_at": "2024-01-01T00:00:00Z",
            },
            {
                "number": 2,
                "title": "feat: Add auth",
                "merged_at": "2024-01-02T00:00:00Z",
            },
            {"number": 3, "title": "fix: Bug fix", "merged_at": "2024-01-03T00:00:00Z"},
        ]

        # Mock detailed PR data
        mock_details = {
            1: {"number": 1, "additions": 100, "deletions": 0},
            2: {"number": 2, "additions": 500, "deletions": 50},
            3: {"number": 3, "additions": 10, "deletions": 5},
        }

        # Mock business impact
        mock_impacts = {
            1: {"business_value": "LOW", "impact_score": 20},
            2: {"business_value": "HIGH", "impact_score": 90},
            3: {"business_value": "MEDIUM", "impact_score": 50},
        }

        with patch.object(
            analyzer, "fetch_all_prs", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_prs

            with patch.object(
                analyzer, "collect_pr_details", new_callable=AsyncMock
            ) as mock_details_fn:
                mock_details_fn.side_effect = lambda repo, num: mock_details[num]

                with patch.object(
                    analyzer, "analyze_business_impact", new_callable=AsyncMock
                ) as mock_impact:
                    mock_impact.side_effect = lambda pr: mock_impacts[pr["number"]]

                    results = await analyzer.analyze_repository_history("owner/repo")

                    assert results["total_prs"] == 3
                    assert results["analyzed_prs"] == 3
                    assert len(results["pr_analyses"]) == 3
                    assert results["high_impact_prs"] == 1
                    assert results["total_additions"] == 610
                    assert results["total_deletions"] == 55

    @pytest.mark.asyncio
    async def test_handles_api_errors_gracefully(self):
        """Test that analyzer handles API errors without crashing."""
        analyzer = HistoricalPRAnalyzer(github_token="test-token")

        with patch.object(
            analyzer, "_make_request", new_callable=AsyncMock
        ) as mock_request:
            # Simulate API error
            mock_request.side_effect = Exception("GitHub API error")

            # Should not crash, just return empty list
            prs = await analyzer.fetch_all_prs("owner/repo")
            assert prs == []

    def test_can_be_used_as_module(self):
        """Test that the module can be imported and used."""
        from services.historical_pr_analyzer import HistoricalPRAnalyzer

        # Should be able to create instance
        analyzer = HistoricalPRAnalyzer(github_token="test-token")
        assert analyzer is not None
        assert hasattr(analyzer, "fetch_all_prs")
        assert hasattr(analyzer, "collect_pr_details")
        assert hasattr(analyzer, "analyze_business_impact")
        assert hasattr(analyzer, "analyze_repository_history")

    @pytest.mark.asyncio
    async def test_progress_tracking(self):
        """Test that analyzer provides progress updates."""
        analyzer = HistoricalPRAnalyzer(github_token="test-token")

        # Create mock PRs with varying complexity
        mock_prs = []
        for i in range(10):
            mock_prs.append(
                {
                    "number": i + 1,
                    "title": f"PR #{i + 1}",
                    "additions": (i + 1) * 100,
                    "deletions": (i + 1) * 50,
                }
            )

        with patch.object(
            analyzer, "fetch_all_prs", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_prs

            with patch.object(
                analyzer, "collect_pr_details", new_callable=AsyncMock
            ) as mock_details:
                mock_details.side_effect = lambda repo, num: {
                    "number": num,
                    "additions": num * 100,
                }

                with patch.object(
                    analyzer, "analyze_business_impact", new_callable=AsyncMock
                ) as mock_impact:
                    mock_impact.return_value = {
                        "business_value": "MEDIUM",
                        "impact_score": 50,
                    }

                    results = await analyzer.analyze_repository_history("owner/repo")

                    # Should analyze all PRs
                    assert results["total_prs"] == 10
                    assert results["analyzed_prs"] == 10
                    assert mock_details.call_count == 10
                    assert mock_impact.call_count == 10
