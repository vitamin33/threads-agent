"""GitHub PR tracker for achievement collection."""

import os
import re
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json


from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Achievement
from services.achievement_collector.api.schemas import AchievementCreate
from services.achievement_collector.api.routes.achievements import (
    create_achievement_sync,
)


class GitHubPRTracker:
    """Tracks merged PRs and creates achievements."""

    def __init__(self, repo_path: str = None):
        """Initialize GitHub PR tracker.

        Args:
            repo_path: Path to git repository (defaults to current directory)
        """
        self.repo_path = repo_path or os.getcwd()
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.min_changes_for_achievement = int(
            os.getenv("MIN_PR_CHANGES_FOR_ACHIEVEMENT", "50")
        )
        self.check_interval = int(os.getenv("PR_CHECK_INTERVAL", "300"))  # 5 minutes

    async def track_continuously(self):
        """Continuously track merged PRs."""
        print("🚀 Starting GitHub PR tracker...")
        print(f"📁 Repository: {self.repo_path}")
        print(f"⏱️  Check interval: {self.check_interval}s")

        while True:
            try:
                await self.check_recent_prs()
            except Exception as e:
                print(f"❌ Error checking PRs: {e}")

            await asyncio.sleep(self.check_interval)

    async def check_recent_prs(self):
        """Check for recently merged PRs."""
        # Use gh CLI to get merged PRs from last 7 days
        since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        try:
            # Get merged PRs using gh CLI
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--state",
                    "merged",
                    "--limit",
                    "20",
                    "--json",
                    "number,title,body,mergedAt,author,files,additions,deletions,labels,reviews,commits,url",
                    "--search",
                    f"merged:>={since}",
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )

            prs = json.loads(result.stdout)

            for pr in prs:
                await self._process_pr(pr)

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Error running gh CLI: {e}")
            print("   Make sure 'gh' is installed and authenticated")
        except json.JSONDecodeError as e:
            print(f"⚠️  Error parsing PR data: {e}")

    async def _process_pr(self, pr_data: Dict[str, Any]):
        """Process a single PR and create achievement if significant."""
        pr_number = pr_data["number"]

        # Check if we've already tracked this PR
        db = next(get_db())
        try:
            existing = (
                db.query(Achievement)
                .filter_by(source_type="github_pr", source_id=f"PR-{pr_number}")
                .first()
            )

            if existing:
                return

            # Check if PR is significant
            if self._is_significant_pr(pr_data):
                await self._create_pr_achievement(pr_data)
                print(f"✅ Created achievement for PR #{pr_number}")

        finally:
            db.close()

    def _is_significant_pr(self, pr_data: Dict[str, Any]) -> bool:
        """Determine if a PR is significant enough for an achievement."""
        # Calculate total changes
        total_changes = pr_data.get("additions", 0) + pr_data.get("deletions", 0)

        # Check various significance criteria
        if total_changes >= self.min_changes_for_achievement:
            return True

        # Check for important labels
        important_labels = ["feature", "enhancement", "breaking-change", "security"]
        pr_labels = [label["name"].lower() for label in pr_data.get("labels", [])]
        if any(label in pr_labels for label in important_labels):
            return True

        # Check for meaningful PR patterns
        title_lower = pr_data.get("title", "").lower()
        significant_patterns = [
            r"feat(\(.*\))?:",
            r"fix(\(.*\))?:.*critical",
            r"perf(\(.*\))?:",
            r"security:",
            r"breaking change:",
        ]

        for pattern in significant_patterns:
            if re.search(pattern, title_lower):
                return True

        return False

    async def _create_pr_achievement(self, pr_data: Dict[str, Any]):
        """Create an achievement from PR data."""
        # Extract PR metadata
        pr_number = pr_data["number"]
        title = pr_data.get("title", f"PR #{pr_number}")
        body = pr_data.get("body", "")
        author = pr_data.get("author", {}).get("login", "unknown")
        merged_at = pr_data.get("mergedAt", datetime.now().isoformat())

        # Parse merged date
        try:
            merged_date = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
        except Exception:
            merged_date = datetime.now()

        # Extract skills from files changed
        skills = self._extract_skills_from_pr(pr_data)

        # Determine category
        category = self._determine_category_from_pr(pr_data)

        # Calculate impact score
        impact_score = self._calculate_pr_impact_score(pr_data)

        # Get PR metrics
        metrics = {
            "pr_number": pr_number,
            "files_changed": len(pr_data.get("files", [])),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
            "commits_count": len(pr_data.get("commits", [])),
            "reviewers_count": len(pr_data.get("reviews", [])),
            "total_changes": pr_data.get("additions", 0) + pr_data.get("deletions", 0),
        }

        # Create achievement
        achievement_data = AchievementCreate(
            title=f"Shipped: {title}",
            category=category,
            description=self._generate_pr_description(pr_data, body),
            started_at=merged_date - timedelta(days=2),  # Estimate
            completed_at=merged_date,
            source_type="github_pr",
            source_id=f"PR-{pr_number}",
            tags=self._extract_tags_from_pr(pr_data),
            skills_demonstrated=skills[:10],  # Limit to 10 skills
            metrics_after=metrics,
            impact_score=impact_score,
            complexity_score=self._calculate_complexity_score(metrics),
            portfolio_ready=impact_score >= 70,
            metadata={
                "pr_url": pr_data.get("url", ""),
                "author": author,
                "labels": [label["name"] for label in pr_data.get("labels", [])],
            },
        )

        # Save to database
        db = next(get_db())
        try:
            create_achievement_sync(db, achievement_data)
        finally:
            db.close()

    def _extract_skills_from_pr(self, pr_data: Dict[str, Any]) -> List[str]:
        """Extract skills from PR files and content."""
        skills = set()

        # Extract from file extensions
        file_skills = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".go": "Go",
            ".rs": "Rust",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".json": "JSON",
            ".sql": "SQL",
            ".sh": "Bash",
            ".dockerfile": "Docker",
            "Dockerfile": "Docker",
            ".k8s.yaml": "Kubernetes",
            "Chart.yaml": "Helm",
        }

        files = pr_data.get("files", [])
        for file in files:
            filename = file.get("filename", "")
            for ext, skill in file_skills.items():
                if filename.endswith(ext) or filename == ext:
                    skills.add(skill)

        # Extract from PR labels
        label_skills = {
            "frontend": ["React", "Frontend Development"],
            "backend": ["Backend Development", "API Design"],
            "database": ["Database Design", "SQL"],
            "devops": ["DevOps", "CI/CD"],
            "testing": ["Testing", "Test Automation"],
            "documentation": ["Technical Writing", "Documentation"],
            "performance": ["Performance Optimization"],
            "security": ["Security", "Security Best Practices"],
            "api": ["API Design", "REST"],
            "graphql": ["GraphQL"],
            "docker": ["Docker", "Containerization"],
            "kubernetes": ["Kubernetes", "Container Orchestration"],
            "ai": ["AI/ML", "Machine Learning"],
            "data": ["Data Engineering", "Data Analysis"],
        }

        for label in pr_data.get("labels", []):
            label_name = label.get("name", "").lower()
            for key, label_skills_list in label_skills.items():
                if key in label_name:
                    skills.update(label_skills_list)

        # Add general skills
        skills.update(["Git", "Code Review", "Collaboration"])

        # Add specific skills based on PR patterns
        title = pr_data.get("title", "").lower()
        body = pr_data.get("body", "").lower()

        if "refactor" in title or "refactor" in body:
            skills.add("Code Refactoring")
        if "optimize" in title or "performance" in title:
            skills.add("Performance Optimization")
        if "test" in title or "testing" in body:
            skills.add("Testing")
        if "fix" in title:
            skills.add("Debugging")
        if "feature" in title or "implement" in title:
            skills.add("Feature Development")

        return list(skills)

    def _determine_category_from_pr(self, pr_data: Dict[str, Any]) -> str:
        """Determine achievement category from PR data."""
        title = pr_data.get("title", "").lower()
        labels = [label.get("name", "").lower() for label in pr_data.get("labels", [])]

        # Check title patterns
        if any(
            pattern in title for pattern in ["feat:", "feature", "implement", "add"]
        ):
            return "feature"
        elif any(pattern in title for pattern in ["fix:", "bug", "patch"]):
            return "bugfix"
        elif any(pattern in title for pattern in ["perf:", "optimize", "performance"]):
            return "optimization"
        elif any(pattern in title for pattern in ["refactor:", "refactoring"]):
            return "refactoring"
        elif any(pattern in title for pattern in ["docs:", "documentation"]):
            return "documentation"
        elif any(pattern in title for pattern in ["test:", "testing"]):
            return "testing"
        elif any(pattern in title for pattern in ["chore:", "ci:", "build:"]):
            return "infrastructure"

        # Check labels
        if "feature" in labels or "enhancement" in labels:
            return "feature"
        elif "bug" in labels:
            return "bugfix"
        elif "documentation" in labels:
            return "documentation"
        elif "testing" in labels:
            return "testing"

        return "development"

    def _calculate_pr_impact_score(self, pr_data: Dict[str, Any]) -> float:
        """Calculate impact score based on PR metrics."""
        score = 50.0  # Base score

        # Size impact (up to 20 points)
        total_changes = pr_data.get("additions", 0) + pr_data.get("deletions", 0)
        if total_changes >= 500:
            score += 20
        elif total_changes >= 200:
            score += 15
        elif total_changes >= 100:
            score += 10
        elif total_changes >= 50:
            score += 5

        # File count impact (up to 10 points)
        files_changed = len(pr_data.get("files", []))
        if files_changed >= 10:
            score += 10
        elif files_changed >= 5:
            score += 7
        elif files_changed >= 3:
            score += 5

        # Review engagement (up to 10 points)
        reviews = pr_data.get("reviews", [])
        if len(reviews) >= 3:
            score += 10
        elif len(reviews) >= 2:
            score += 7
        elif len(reviews) >= 1:
            score += 5

        # Label bonuses (up to 10 points)
        important_labels = ["feature", "breaking-change", "security", "performance"]
        pr_labels = [label["name"].lower() for label in pr_data.get("labels", [])]
        label_bonus = sum(2.5 for label in important_labels if label in pr_labels)
        score += min(label_bonus, 10)

        return min(score, 100.0)

    def _calculate_complexity_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate complexity score from PR metrics."""
        score = 40.0  # Base complexity

        # File diversity - handle both field names
        files_changed = metrics.get("files_changed", metrics.get("changed_files", 0))
        if files_changed >= 10:
            score += 20
        elif files_changed >= 5:
            score += 10

        # Code volume - calculate total from additions + deletions
        total_changes = metrics.get("total_changes", 0)
        if total_changes == 0:  # If not provided, calculate from additions + deletions
            total_changes = metrics.get("additions", 0) + metrics.get("deletions", 0)
        
        if total_changes >= 1000:  # Adjusted thresholds for better scoring
            score += 25
        elif total_changes >= 500:
            score += 20
        elif total_changes >= 200:
            score += 10
        elif total_changes >= 50:
            score += 5

        # Review complexity - handle both field names
        reviewers_count = metrics.get("reviewers_count", metrics.get("review_count", 0))
        if reviewers_count >= 3:
            score += 10
        elif reviewers_count >= 2:
            score += 5

        # Commit count (more commits might indicate iterative complexity)
        commits_count = metrics.get("commits_count", metrics.get("commits", 0))
        if commits_count >= 10:
            score += 10
        elif commits_count >= 5:
            score += 5

        return min(score, 100.0)

    def _generate_pr_description(self, pr_data: Dict[str, Any], body: str) -> str:
        """Generate a comprehensive description from PR data."""
        description_parts = []

        # Add PR body if meaningful
        if body and len(body) > 20:
            # Clean up GitHub-specific formatting
            clean_body = body.replace("## ", "").replace("### ", "")
            clean_body = re.sub(r"<!--.*?-->", "", clean_body, flags=re.DOTALL)
            clean_body = clean_body.strip()

            if clean_body:
                description_parts.append(clean_body[:500])  # Limit length

        # Add metrics summary
        metrics_summary = (
            f"This pull request included {pr_data.get('additions', 0)} additions "
            f"and {pr_data.get('deletions', 0)} deletions across "
            f"{len(pr_data.get('files', []))} files."
        )
        description_parts.append(metrics_summary)

        # Add review summary if available
        reviews = pr_data.get("reviews", [])
        if reviews:
            description_parts.append(
                f"The code was reviewed by {len(reviews)} team members before merging."
            )

        return " ".join(description_parts)

    def _extract_tags_from_pr(self, pr_data: Dict[str, Any]) -> List[str]:
        """Extract relevant tags from PR data."""
        tags = []

        # Add labels as tags
        for label in pr_data.get("labels", []):
            tags.append(label["name"].lower())

        # Extract from title
        title = pr_data.get("title", "").lower()
        if "feat" in title or "feature" in title:
            tags.append("feature")
        if "fix" in title:
            tags.append("bugfix")
        if "perf" in title:
            tags.append("performance")
        if "refactor" in title:
            tags.append("refactoring")

        # Add PR number as tag
        tags.append(f"pr-{pr_data['number']}")

        # Add language tags from files
        has_python = any(
            f.get("filename", "").endswith(".py") for f in pr_data.get("files", [])
        )
        has_js = any(
            f.get("filename", "").endswith((".js", ".ts"))
            for f in pr_data.get("files", [])
        )

        if has_python:
            tags.append("python")
        if has_js:
            tags.append("javascript")

        return list(set(tags))[:20]  # Unique tags, max 20


async def main():
    """Run the GitHub PR tracker."""
    tracker = GitHubPRTracker()
    await tracker.track_continuously()


if __name__ == "__main__":
    asyncio.run(main())
