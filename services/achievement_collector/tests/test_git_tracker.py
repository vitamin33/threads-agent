"""Unit tests for Git commit tracker."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from services.achievement_collector.services.git_tracker import GitCommitTracker


class TestGitCommitTracker:
    """Test Git commit tracker functionality."""

    @pytest.fixture
    def tracker(self):
        """Create a Git tracker instance."""
        with patch.dict(
            "os.environ",
            {"GIT_REPO_PATH": "/test/repo", "MIN_LINES_FOR_ACHIEVEMENT": "50"},
        ):
            return GitCommitTracker()

    def test_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.repo_path == "/test/repo"
        assert tracker.min_lines_changed == 50
        assert len(tracker.significant_patterns) > 0

    def test_is_significant_commit_by_pattern(self, tracker):
        """Test commit significance detection by pattern."""
        # Test significant patterns
        significant_commits = [
            {
                "message": "feat(api): add new endpoint",
                "lines_added": 10,
                "lines_deleted": 5,
            },
            {
                "message": "fix(auth): resolve login issue",
                "lines_added": 5,
                "lines_deleted": 3,
            },
            {
                "message": "perf(db): optimize queries",
                "lines_added": 20,
                "lines_deleted": 15,
            },
        ]

        for commit in significant_commits:
            assert tracker._is_significant_commit(commit) is True

    def test_is_significant_commit_by_lines(self, tracker):
        """Test commit significance detection by lines changed."""
        # Test by lines changed
        commit_many_lines = {
            "message": "Update documentation",
            "lines_added": 40,
            "lines_deleted": 20,
        }
        assert tracker._is_significant_commit(commit_many_lines) is True

        # Test not significant
        commit_few_lines = {
            "message": "Update readme",
            "lines_added": 5,
            "lines_deleted": 2,
        }
        assert tracker._is_significant_commit(commit_few_lines) is False

    def test_is_significant_commit_by_keywords(self, tracker):
        """Test commit significance detection by keywords."""
        keyword_commits = [
            {
                "message": "Implement user authentication",
                "lines_added": 5,
                "lines_deleted": 0,
            },
            {
                "message": "Add payment processing",
                "lines_added": 10,
                "lines_deleted": 0,
            },
            {
                "message": "Create API documentation",
                "lines_added": 15,
                "lines_deleted": 0,
            },
            {
                "message": "Build deployment pipeline",
                "lines_added": 8,
                "lines_deleted": 2,
            },
        ]

        for commit in keyword_commits:
            assert tracker._is_significant_commit(commit) is True

    def test_extract_skills_from_files(self, tracker):
        """Test skill extraction from file changes."""
        files = [
            {"name": "services/api/main.py", "added": 50, "deleted": 10},
            {"name": "docker-compose.yml", "added": 20, "deleted": 5},
            {"name": "services/mlflow/tracker.py", "added": 30, "deleted": 0},
            {"name": "tests/test_api.py", "added": 40, "deleted": 0},
        ]

        skills = tracker._extract_skills_from_files(files)

        assert "Python" in skills
        assert "Docker" in skills
        assert "MLflow" in skills
        assert "Testing" in skills

    def test_extract_skills_typescript(self, tracker):
        """Test TypeScript/JavaScript skill extraction."""
        files = [
            {"name": "src/components/Dashboard.tsx", "added": 100, "deleted": 20},
            {"name": "src/utils/api.ts", "added": 50, "deleted": 10},
        ]

        skills = tracker._extract_skills_from_files(files)
        assert "JavaScript/TypeScript" in skills

    def test_extract_skills_kubernetes(self, tracker):
        """Test Kubernetes/Helm skill extraction."""
        files = [
            {"name": "k8s/deployment.yaml", "added": 30, "deleted": 5},
            {"name": "helm/values.yaml", "added": 20, "deleted": 0},
        ]

        skills = tracker._extract_skills_from_files(files)
        assert "Kubernetes" in skills
        assert "Helm" in skills

    @pytest.mark.asyncio
    async def test_create_commit_achievement(self, tracker):
        """Test achievement creation from commit."""
        commit = {
            "hash": "abc123def456789",
            "author": "Test User",
            "email": "test@example.com",
            "timestamp": int(datetime.now().timestamp()),
            "message": "feat(auth): implement OAuth2 flow",
            "files_changed": 5,
            "lines_added": 150,
            "lines_deleted": 30,
            "files": [
                {"name": "services/auth/oauth.py", "added": 100, "deleted": 20},
                {"name": "tests/test_oauth.py", "added": 50, "deleted": 10},
            ],
        }

        # Mock the database and achievement creation
        with patch(
            "services.achievement_collector.services.git_tracker.get_db"
        ) as mock_get_db:
            with patch(
                "services.achievement_collector.services.git_tracker.create_achievement_sync"
            ) as mock_create:
                mock_db = Mock()
                mock_get_db.return_value = iter([mock_db])

                mock_achievement = Mock()
                mock_achievement.title = "Feat: implement OAuth2 flow"
                mock_achievement.id = 1
                mock_create.return_value = mock_achievement

                await tracker._create_commit_achievement(commit)

                # Verify achievement creation was called
                mock_create.assert_called_once()
                call_args = mock_create.call_args[0][1]

                # Verify achievement data
                assert call_args.title == "Feat: implement OAuth2 flow"
                assert call_args.category == "feature"
                assert call_args.source_type == "git"
                assert call_args.source_id == "abc123def456789"
                assert "Python" in call_args.skills_demonstrated
                assert "Testing" in call_args.skills_demonstrated
                # Impact score = min(90.0, 30.0 + (150 + 30) / 20) = min(90.0, 30.0 + 9) = 39.0
                assert call_args.impact_score == 39.0
                assert call_args.portfolio_ready is False  # 39.0 is not > 60

    @patch("subprocess.run")
    def test_get_new_commits(self, mock_run, tracker):
        """Test fetching new commits from git."""
        # Mock git log output
        git_output = """abc123|John Doe|john@example.com|1706439600|feat(api): add user endpoint
\t50\t10\tservices/api/users.py
\t30\t5\ttests/test_users.py
def456|Jane Smith|jane@example.com|1706440000|fix(db): connection timeout
\t20\t15\tservices/db/connection.py"""

        mock_run.return_value = Mock(returncode=0, stdout=git_output, stderr="")

        commits = tracker._get_new_commits()

        assert len(commits) == 2
        assert commits[0]["hash"] == "abc123"
        assert commits[0]["author"] == "John Doe"
        assert commits[0]["message"] == "feat(api): add user endpoint"
        assert commits[0]["files_changed"] == 2
        assert commits[0]["lines_added"] == 80
        assert commits[0]["lines_deleted"] == 15

        assert commits[1]["hash"] == "def456"
        assert commits[1]["message"] == "fix(db): connection timeout"

    def test_last_processed_commit_handling(self, tracker):
        """Test handling of last processed commit file."""
        # Test loading non-existent file
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = tracker._load_last_processed()
            assert result is None

        # Test saving commit hash
        mock_file = Mock()
        mock_open = Mock(return_value=mock_file)
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_file.write = Mock()

        with patch("builtins.open", mock_open):
            tracker._save_last_processed("test_hash_123")
            mock_open.assert_called_once_with(".last_processed_commit", "w")
            mock_file.write.assert_called_once_with("test_hash_123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
