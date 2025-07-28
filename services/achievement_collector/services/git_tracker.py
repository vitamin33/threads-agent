"""Git commit and PR tracker for automatic achievement generation."""

import asyncio
import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional


from ..api.schemas import AchievementCreate
from ..core.logging import setup_logging
from ..db.config import get_db
from ..api.routes.achievements import create_achievement_sync

logger = setup_logging(__name__)


class GitCommitTracker:
    """Tracks git commits and creates achievements for significant changes."""

    def __init__(self):
        self.repo_path = os.getenv("GIT_REPO_PATH", ".")
        self.min_lines_changed = int(os.getenv("MIN_LINES_FOR_ACHIEVEMENT", "50"))
        self.significant_patterns = [
            r"feat\(.*\):",  # New feature
            r"fix\(.*\):",  # Bug fix
            r"perf\(.*\):",  # Performance improvement
            r"refactor\(.*\):",  # Code refactoring
            r"test\(.*\):",  # Test improvements
            r"docs\(.*\):",  # Documentation
            r"ci\(.*\):",  # CI/CD changes
        ]
        self.last_processed_commit = self._load_last_processed()

    def _load_last_processed(self) -> Optional[str]:
        """Load the last processed commit hash from file."""
        try:
            with open(".last_processed_commit", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def _save_last_processed(self, commit_hash: str):
        """Save the last processed commit hash."""
        with open(".last_processed_commit", "w") as f:
            f.write(commit_hash)

    async def track_commits(self):
        """Main loop to track commits and create achievements."""
        while True:
            try:
                new_commits = self._get_new_commits()
                for commit in new_commits:
                    if self._is_significant_commit(commit):
                        await self._create_commit_achievement(commit)

                if new_commits:
                    self._save_last_processed(new_commits[-1]["hash"])

                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error tracking commits: {e}")
                await asyncio.sleep(60)

    def _get_new_commits(self) -> List[Dict]:
        """Get commits since last processed."""
        try:
            # Get commit log
            since_arg = (
                f"--since={self.last_processed_commit}"
                if self.last_processed_commit
                else "--max-count=10"
            )

            cmd = [
                "git",
                "log",
                since_arg,
                "--pretty=format:%H|%an|%ae|%at|%s",
                "--numstat",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.repo_path
            )
            if result.returncode != 0:
                logger.error(f"Git command failed: {result.stderr}")
                return []

            commits = []
            current_commit = None

            for line in result.stdout.split("\n"):
                if "|" in line and not line.startswith("\t"):
                    # New commit line
                    if current_commit:
                        commits.append(current_commit)

                    parts = line.split("|")
                    current_commit = {
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "timestamp": int(parts[3]),
                        "message": parts[4],
                        "files_changed": 0,
                        "lines_added": 0,
                        "lines_deleted": 0,
                        "files": [],
                    }
                elif line.startswith("\t") and current_commit:
                    # File stats line
                    parts = line.strip().split("\t")
                    if len(parts) == 3:
                        added = int(parts[0]) if parts[0] != "-" else 0
                        deleted = int(parts[1]) if parts[1] != "-" else 0
                        filename = parts[2]

                        current_commit["files_changed"] += 1
                        current_commit["lines_added"] += added
                        current_commit["lines_deleted"] += deleted
                        current_commit["files"].append(
                            {"name": filename, "added": added, "deleted": deleted}
                        )

            if current_commit:
                commits.append(current_commit)

            return commits

        except Exception as e:
            logger.error(f"Error getting commits: {e}")
            return []

    def _is_significant_commit(self, commit: Dict) -> bool:
        """Determine if a commit is significant enough for an achievement."""
        # Check if commit message matches significant patterns
        for pattern in self.significant_patterns:
            if re.match(pattern, commit["message"], re.IGNORECASE):
                return True

        # Check if enough lines changed
        total_changes = commit["lines_added"] + commit["lines_deleted"]
        if total_changes >= self.min_lines_changed:
            return True

        # Check for specific keywords in commit message
        keywords = [
            "implement",
            "add",
            "create",
            "build",
            "deploy",
            "optimize",
            "refactor",
        ]
        message_lower = commit["message"].lower()
        if any(keyword in message_lower for keyword in keywords):
            return True

        return False

    async def _create_commit_achievement(self, commit: Dict):
        """Create achievement from commit data."""
        # Extract feature/module from commit message
        match = re.match(r"(\w+)\((.*?)\):\s*(.*)", commit["message"])
        if match:
            commit_type = match.group(1)
            scope = match.group(2)
            description = match.group(3)
        else:
            commit_type = "update"
            scope = "general"
            description = commit["message"]

        # Determine category based on commit type
        category_map = {
            "feat": "feature",
            "fix": "bugfix",
            "perf": "performance",
            "refactor": "refactoring",
            "test": "testing",
            "docs": "documentation",
            "ci": "infrastructure",
        }
        category = category_map.get(commit_type, "development")

        # Extract skills from files changed
        skills = self._extract_skills_from_files(commit["files"])

        # Calculate impact score based on changes
        impact_score = min(
            90.0, 30.0 + (commit["lines_added"] + commit["lines_deleted"]) / 20
        )

        # Create achievement
        achievement_data = AchievementCreate(
            title=f"{commit_type.title()}: {description[:100]}",
            category=category,
            description=f"Implemented {description}. Modified {commit['files_changed']} files with {commit['lines_added']} additions and {commit['lines_deleted']} deletions.",
            started_at=datetime.fromtimestamp(
                commit["timestamp"] - 3600
            ),  # Assume 1 hour work
            completed_at=datetime.fromtimestamp(commit["timestamp"]),
            source_type="git",
            source_id=commit["hash"],
            tags=["git", commit_type, scope]
            + [f["name"].split("/")[0] for f in commit["files"][:3]],
            skills_demonstrated=skills,
            metrics_after={
                "commit_hash": commit["hash"],
                "files_changed": commit["files_changed"],
                "lines_added": commit["lines_added"],
                "lines_deleted": commit["lines_deleted"],
                "commit_type": commit_type,
                "scope": scope,
            },
            impact_score=impact_score,
            complexity_score=min(85.0, 40.0 + commit["files_changed"] * 5),
            portfolio_ready=impact_score > 60,
        )

        db = next(get_db())
        try:
            achievement = create_achievement_sync(db, achievement_data)
            logger.info(
                f"Created achievement for commit {commit['hash'][:8]}: {achievement.title}"
            )
        finally:
            db.close()

    def _extract_skills_from_files(self, files: List[Dict]) -> List[str]:
        """Extract skills demonstrated based on files modified."""
        skills = set()

        for file_info in files:
            filename = file_info["name"].lower()

            # Language/framework detection
            if filename.endswith(".py"):
                skills.add("Python")
            elif filename.endswith((".js", ".jsx", ".ts", ".tsx")):
                skills.add("JavaScript/TypeScript")
            elif filename.endswith(".go"):
                skills.add("Go")
            elif filename.endswith((".yml", ".yaml")):
                skills.add("YAML Configuration")

            # Tool/technology detection
            if "docker" in filename:
                skills.add("Docker")
            elif "kubernetes" in filename or "k8s" in filename:
                skills.add("Kubernetes")
            elif "helm" in filename:
                skills.add("Helm")
            elif "terraform" in filename:
                skills.add("Terraform")
            elif "github" in filename or ".github" in filename:
                skills.add("GitHub Actions")

            # Service detection
            if "services/" in filename:
                parts = filename.split("/")
                if len(parts) > 1:
                    service_name = parts[1]
                    if service_name in [
                        "orchestrator",
                        "celery_worker",
                        "persona_runtime",
                    ]:
                        skills.add(
                            f"{service_name.replace('_', ' ').title()} Development"
                        )

            # MLOps specific
            if "mlflow" in filename:
                skills.add("MLflow")
            elif "model" in filename or "ml" in filename:
                skills.add("Machine Learning")
            elif "pipeline" in filename:
                skills.add("Pipeline Development")

            # Testing
            if "test" in filename:
                skills.add("Testing")
                if "e2e" in filename:
                    skills.add("E2E Testing")
                elif "unit" in filename:
                    skills.add("Unit Testing")

        return list(skills)[:10]  # Limit to 10 skills


class GitHubPRTracker:
    """Tracks GitHub PRs for achievements."""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER", "threads-agent-stack")
        self.repo_name = os.getenv("GITHUB_REPO_NAME", "threads-agent")

    async def track_merged_prs(self):
        """Track merged PRs and create achievements."""
        # This will be implemented after we have the GitHub API setup
        # For now, we'll rely on commit tracking
        pass
