"""Linear issue and epic tracker for automatic achievement generation."""

import asyncio
import os
from datetime import datetime
from typing import Dict, List, Optional


from ..api.schemas import AchievementCreate
from ..core.logging import setup_logging
from ..db.config import get_db
from ..api.routes.achievements import create_achievement_sync

logger = setup_logging(__name__)


class LinearTracker:
    """Tracks Linear issues and epics for achievement generation."""

    def __init__(self):
        self.linear_api_key = os.getenv("LINEAR_API_KEY")
        self.check_interval = int(os.getenv("LINEAR_CHECK_INTERVAL", "3600"))  # 1 hour
        self.last_sync_time = self._load_last_sync()

    def _load_last_sync(self) -> Optional[datetime]:
        """Load the last sync timestamp."""
        try:
            with open(".linear_last_sync", "r") as f:
                timestamp = float(f.read().strip())
                return datetime.fromtimestamp(timestamp)
        except FileNotFoundError:
            return None

    def _save_last_sync(self, timestamp: datetime):
        """Save the last sync timestamp."""
        with open(".linear_last_sync", "w") as f:
            f.write(str(timestamp.timestamp()))

    async def track_linear_updates(self):
        """Main loop to track Linear updates and create achievements."""
        while True:
            try:
                # Get completed issues since last sync
                completed_issues = await self._get_completed_issues()
                for issue in completed_issues:
                    await self._create_issue_achievement(issue)

                # Get completed epics/projects
                completed_projects = await self._get_completed_projects()
                for project in completed_projects:
                    await self._create_epic_achievement(project)

                self._save_last_sync(datetime.now())
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error tracking Linear updates: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes

    async def _get_completed_issues(self) -> List[Dict]:
        """Get issues completed since last sync using Linear MCP."""
        try:
            # Note: This is a placeholder for Linear MCP integration
            # In production, this would use the Linear MCP server via Claude
            # For testing, we'll return mock data or empty list

            # Example of what the MCP call would look like:
            # issues = await mcp_client.call_tool("mcp__linear__linear_searchIssues", {
            #     "states": ["Done", "Completed"],
            #     "limit": 50
            # })

            # For now, return empty list - will be connected when MCP is active
            logger.info("Linear MCP integration pending - returning empty list")
            return []
        except Exception as e:
            logger.error(f"Error fetching Linear issues: {e}")
            return []

    async def _get_completed_projects(self) -> List[Dict]:
        """Get projects/epics completed since last sync."""
        try:
            # Note: This is a placeholder for Linear MCP integration
            # In production, this would use the Linear MCP server via Claude

            # Example of what the MCP call would look like:
            # projects = await mcp_client.call_tool("mcp__linear__linear_getProjects", {})
            # Then filter for completed state

            logger.info("Linear MCP integration pending - returning empty list")
            return []
        except Exception as e:
            logger.error(f"Error fetching Linear projects: {e}")
            return []

    async def _create_issue_achievement(self, issue: Dict):
        """Create achievement from Linear issue."""
        # Determine category based on issue labels
        category = self._determine_category(issue.get("labels", []))

        # Extract skills from issue description and labels
        skills = self._extract_skills(issue)

        # Calculate scores based on issue metadata
        priority_scores = {
            "urgent": 90,
            "high": 75,
            "medium": 60,
            "low": 45,
            "none": 30,
        }
        priority = issue.get("priority", {}).get("name", "medium").lower()
        impact_score = priority_scores.get(priority, 60)

        # Estimate complexity from issue points/size
        estimate = issue.get("estimate", 3)
        complexity_score = min(90, 30 + estimate * 10)

        achievement_data = AchievementCreate(
            title=f"Completed: {issue.get('title', 'Linear Issue')}",
            category=category,
            description=issue.get("description", "Completed Linear issue"),
            started_at=datetime.fromisoformat(
                issue.get("startedAt", issue.get("createdAt"))
            ),
            completed_at=datetime.fromisoformat(issue.get("completedAt")),
            source_type="linear",
            source_id=issue.get("id"),
            tags=["linear", "issue"]
            + [label.get("name", "") for label in issue.get("labels", [])],
            skills_demonstrated=skills,
            metrics_after={
                "issue_id": issue.get("id"),
                "issue_number": issue.get("number"),
                "priority": priority,
                "estimate": estimate,
                "cycle": issue.get("cycle", {}).get("name")
                if issue.get("cycle")
                else None,
                "team": issue.get("team", {}).get("name")
                if issue.get("team")
                else None,
            },
            impact_score=impact_score,
            complexity_score=complexity_score,
            portfolio_ready=impact_score >= 70,
        )

        db = next(get_db())
        try:
            achievement = create_achievement_sync(db, achievement_data)
            logger.info(
                f"Created achievement for Linear issue {issue.get('identifier')}: {achievement.title}"
            )
        finally:
            db.close()

    async def _create_epic_achievement(self, project: Dict):
        """Create achievement from completed Linear project/epic."""
        # Calculate metrics from project issues
        total_issues = len(project.get("issues", []))
        total_points = sum(
            issue.get("estimate", 0) for issue in project.get("issues", [])
        )

        achievement_data = AchievementCreate(
            title=f"Epic Completed: {project.get('name', 'Linear Epic')}",
            category="project",
            description=project.get("description", "Completed Linear epic/project"),
            started_at=datetime.fromisoformat(
                project.get("startedAt", project.get("createdAt"))
            ),
            completed_at=datetime.fromisoformat(project.get("completedAt")),
            source_type="linear",
            source_id=f"project_{project.get('id')}",
            tags=["linear", "epic", "project"],
            skills_demonstrated=[
                "Project Management",
                "Agile Development",
                "Team Collaboration",
            ],
            metrics_after={
                "project_id": project.get("id"),
                "total_issues": total_issues,
                "total_points": total_points,
                "duration_days": (
                    datetime.fromisoformat(project.get("completedAt"))
                    - datetime.fromisoformat(
                        project.get("startedAt", project.get("createdAt"))
                    )
                ).days,
            },
            impact_score=min(95, 70 + total_issues * 2),  # Epics have high impact
            complexity_score=min(90, 60 + total_points),
            portfolio_ready=True,  # Epics are always portfolio-ready
        )

        db = next(get_db())
        try:
            achievement = create_achievement_sync(db, achievement_data)
            logger.info(
                f"Created achievement for Linear epic {project.get('name')}: {achievement.title}"
            )
        finally:
            db.close()

    def _determine_category(self, labels: List[Dict]) -> str:
        """Determine achievement category from Linear labels."""
        label_names = [label.get("name", "").lower() for label in labels]

        if any(label in label_names for label in ["bug", "fix", "bugfix"]):
            return "bugfix"
        elif any(label in label_names for label in ["feature", "enhancement"]):
            return "feature"
        elif any(label in label_names for label in ["performance", "optimization"]):
            return "performance"
        elif any(
            label in label_names for label in ["infrastructure", "devops", "ci/cd"]
        ):
            return "infrastructure"
        elif any(label in label_names for label in ["documentation", "docs"]):
            return "documentation"
        elif any(label in label_names for label in ["test", "testing"]):
            return "testing"
        else:
            return "development"

    def _extract_skills(self, issue: Dict) -> List[str]:
        """Extract skills from issue metadata."""
        skills = set()

        # From labels
        label_names = [label.get("name", "") for label in issue.get("labels", [])]
        for label in label_names:
            if "python" in label.lower():
                skills.add("Python")
            elif "javascript" in label.lower() or "js" in label.lower():
                skills.add("JavaScript")
            elif "react" in label.lower():
                skills.add("React")
            elif "docker" in label.lower():
                skills.add("Docker")
            elif "kubernetes" in label.lower() or "k8s" in label.lower():
                skills.add("Kubernetes")
            elif "api" in label.lower():
                skills.add("API Development")
            elif "database" in label.lower() or "db" in label.lower():
                skills.add("Database Design")
            elif "ml" in label.lower() or "machine learning" in label.lower():
                skills.add("Machine Learning")

        # From description
        description = (issue.get("description", "") or "").lower()
        if "mlflow" in description:
            skills.add("MLflow")
        if "langchain" in description:
            skills.add("LangChain")
        if "rag" in description:
            skills.add("RAG (Retrieval Augmented Generation)")
        if "prompt" in description:
            skills.add("Prompt Engineering")

        # Add general skills based on issue type
        skills.add("Problem Solving")
        skills.add("Agile Development")

        return list(skills)[:10]


class LinearWebhookHandler:
    """Handle Linear webhooks for real-time achievement tracking."""

    def __init__(self):
        self.tracker = LinearTracker()

    async def handle_webhook(self, event_type: str, data: Dict):
        """Process Linear webhook events."""
        if event_type == "Issue" and data.get("action") == "update":
            issue = data.get("data", {})
            if issue.get("state", {}).get("type") == "completed":
                await self.tracker._create_issue_achievement(issue)

        elif event_type == "Project" and data.get("action") == "update":
            project = data.get("data", {})
            if project.get("state") == "completed":
                await self.tracker._create_epic_achievement(project)
