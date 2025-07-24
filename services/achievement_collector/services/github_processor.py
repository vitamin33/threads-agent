# GitHub Webhook Processor

import re
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from core.logging import setup_logging
from db.models import Achievement, GitCommit, GitHubPR

logger = setup_logging(__name__)


class GitHubProcessor:
    """Process GitHub webhook events into achievements"""
    
    def __init__(self):
        # Patterns for identifying significant changes
        self.significant_patterns = [
            r"feat\b",
            r"feature\b",
            r"fix\b",
            r"perf\b",
            r"refactor\b",
            r"security\b",
            r"breaking\b",
        ]
        
        # File extensions that indicate code changes
        self.code_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
            ".rs", ".cpp", ".c", ".h", ".cs", ".rb", ".php",
        }
    
    async def process_pull_request(
        self,
        payload: Dict,
        db: Session,
    ) -> Optional[Achievement]:
        """Process pull request events"""
        
        pr = payload.get("pull_request", {})
        action = payload.get("action")
        
        # Only process merged PRs
        if action != "closed" or not pr.get("merged"):
            return None
        
        # Check if PR already processed
        existing = db.query(GitHubPR).filter(
            GitHubPR.pr_number == pr["number"]
        ).first()
        
        if existing:
            logger.info(f"PR #{pr['number']} already processed")
            return None
        
        # Calculate metrics
        created_at = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        merged_at = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
        review_time = (merged_at - created_at).total_seconds() / 3600
        
        # Determine category from PR title and labels
        category = self._determine_category(pr["title"], pr.get("labels", []))
        
        # Create achievement
        achievement = Achievement(
            title=f"PR #{pr['number']}: {pr['title']}",
            description=pr.get("body", "No description provided"),
            category=category,
            started_at=created_at,
            completed_at=merged_at,
            duration_hours=review_time,
            source_type="github",
            source_id=str(pr["number"]),
            source_url=pr["html_url"],
            tags=self._extract_tags(pr),
            skills_demonstrated=self._extract_skills(pr),
            evidence={
                "pr_number": pr["number"],
                "commits": pr.get("commits", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "changed_files": pr.get("changed_files", 0),
            },
        )
        
        db.add(achievement)
        db.flush()  # Get the ID
        
        # Create GitHub PR record
        github_pr = GitHubPR(
            achievement_id=achievement.id,
            pr_number=pr["number"],
            title=pr["title"],
            description=pr.get("body", ""),
            state="merged",
            created_at=created_at,
            merged_at=merged_at,
            review_time_hours=review_time,
            comments_count=pr.get("comments", 0) + pr.get("review_comments", 0),
            commits_count=pr.get("commits", 0),
            files_changed=pr.get("changed_files", 0),
            additions=pr.get("additions", 0),
            deletions=pr.get("deletions", 0),
        )
        
        db.add(github_pr)
        db.commit()
        
        logger.info(f"Created achievement for PR #{pr['number']}")
        
        return achievement
    
    async def process_workflow_run(
        self,
        payload: Dict,
        db: Session,
    ) -> Optional[Achievement]:
        """Process CI/CD workflow events"""
        
        run = payload.get("workflow_run", {})
        
        # Only process successful runs that indicate deployment
        if run.get("conclusion") != "success":
            return None
        
        # Check if it's a deployment workflow
        workflow_name = run.get("name", "").lower()
        if not any(word in workflow_name for word in ["deploy", "release", "publish"]):
            return None
        
        # Create achievement for successful deployment
        started_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        completed_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
        duration = (completed_at - started_at).total_seconds() / 3600
        
        achievement = Achievement(
            title=f"Successful Deployment: {run['name']}",
            description=f"Successfully completed {workflow_name} workflow",
            category="infrastructure",
            started_at=started_at,
            completed_at=completed_at,
            duration_hours=duration,
            source_type="ci",
            source_id=str(run["id"]),
            source_url=run["html_url"],
            tags=["deployment", "ci/cd", workflow_name],
            skills_demonstrated=["DevOps", "CI/CD", "Automation"],
            evidence={
                "workflow": run["name"],
                "run_number": run["run_number"],
                "attempt": run["run_attempt"],
                "duration_seconds": (completed_at - started_at).total_seconds(),
            },
        )
        
        db.add(achievement)
        db.commit()
        
        logger.info(f"Created achievement for workflow run #{run['id']}")
        
        return achievement
    
    async def process_push(
        self,
        payload: Dict,
        db: Session,
    ) -> Optional[Achievement]:
        """Process push events for significant commits"""
        
        commits = payload.get("commits", [])
        
        # Filter for significant commits
        significant_commits = []
        
        for commit in commits:
            message = commit.get("message", "")
            
            # Check if commit message indicates significance
            if any(re.search(pattern, message, re.IGNORECASE) for pattern in self.significant_patterns):
                significant_commits.append(commit)
        
        if not significant_commits:
            return None
        
        # Don't create achievements for single commits (wait for PR)
        if len(significant_commits) == 1:
            # Just store the commit for reference
            commit = significant_commits[0]
            
            git_commit = GitCommit(
                sha=commit["id"],
                message=commit["message"],
                author=commit["author"]["name"],
                timestamp=datetime.fromisoformat(commit["timestamp"].replace("Z", "+00:00")),
                files_changed=len(commit.get("added", [])) + len(commit.get("modified", [])) + len(commit.get("removed", [])),
                additions=0,  # Not available in push webhook
                deletions=0,  # Not available in push webhook
                is_significant=True,
            )
            
            db.add(git_commit)
            db.commit()
            
            logger.info(f"Stored significant commit {commit['id'][:7]}")
            
        return None
    
    async def process_issue(
        self,
        payload: Dict,
        db: Session,
    ) -> Optional[Achievement]:
        """Process issue events"""
        
        issue = payload.get("issue", {})
        action = payload.get("action")
        
        # Only process closed issues that represent completed work
        if action != "closed":
            return None
        
        # Check labels for significance
        labels = [label["name"] for label in issue.get("labels", [])]
        
        # Skip non-work issues
        if any(label in labels for label in ["question", "duplicate", "wontfix", "invalid"]):
            return None
        
        # Require work-related labels
        if not any(label in labels for label in ["bug", "enhancement", "feature", "task"]):
            return None
        
        created_at = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
        closed_at = datetime.fromisoformat(issue["closed_at"].replace("Z", "+00:00"))
        duration = (closed_at - created_at).total_seconds() / 3600
        
        # Determine category from labels
        if "bug" in labels:
            category = "bugfix"
        elif "feature" in labels or "enhancement" in labels:
            category = "feature"
        else:
            category = "feature"  # Default
        
        achievement = Achievement(
            title=f"Issue #{issue['number']}: {issue['title']}",
            description=issue.get("body", "No description provided"),
            category=category,
            started_at=created_at,
            completed_at=closed_at,
            duration_hours=duration,
            source_type="github",
            source_id=f"issue-{issue['number']}",
            source_url=issue["html_url"],
            tags=labels,
            skills_demonstrated=self._skills_from_labels(labels),
            evidence={
                "issue_number": issue["number"],
                "comments": issue.get("comments", 0),
                "labels": labels,
            },
        )
        
        db.add(achievement)
        db.commit()
        
        logger.info(f"Created achievement for issue #{issue['number']}")
        
        return achievement
    
    def _determine_category(self, title: str, labels: list) -> str:
        """Determine achievement category from PR title and labels"""
        
        title_lower = title.lower()
        label_names = [label.get("name", "").lower() for label in labels]
        
        # Check labels first
        if "bug" in label_names or "bugfix" in label_names:
            return "bugfix"
        elif "security" in label_names:
            return "security"
        elif "performance" in label_names:
            return "performance"
        elif "documentation" in label_names or "docs" in label_names:
            return "documentation"
        elif "test" in label_names or "testing" in label_names:
            return "testing"
        elif "infrastructure" in label_names or "devops" in label_names:
            return "infrastructure"
        
        # Check title patterns
        if re.search(r"\bfix\b|\bbug\b", title_lower):
            return "bugfix"
        elif re.search(r"\bfeat\b|\bfeature\b|\badd\b", title_lower):
            return "feature"
        elif re.search(r"\bperf\b|\boptimiz", title_lower):
            return "optimization"
        elif re.search(r"\brefactor\b", title_lower):
            return "architecture"
        elif re.search(r"\bsecurity\b|\bvuln", title_lower):
            return "security"
        elif re.search(r"\bdoc\b|\bdocs\b", title_lower):
            return "documentation"
        elif re.search(r"\btest\b", title_lower):
            return "testing"
        
        return "feature"  # Default
    
    def _extract_tags(self, pr: Dict) -> list:
        """Extract tags from PR data"""
        
        tags = []
        
        # Add label names as tags
        for label in pr.get("labels", []):
            tags.append(label["name"])
        
        # Extract technology tags from title
        title = pr.get("title", "")
        tech_keywords = [
            "python", "javascript", "typescript", "react", "vue", "angular",
            "docker", "kubernetes", "aws", "gcp", "azure", "ci/cd",
            "api", "database", "redis", "postgresql", "mongodb",
        ]
        
        for keyword in tech_keywords:
            if keyword in title.lower():
                tags.append(keyword)
        
        return list(set(tags))  # Remove duplicates
    
    def _extract_skills(self, pr: Dict) -> list:
        """Extract demonstrated skills from PR"""
        
        skills = []
        
        # Based on file types changed
        # Note: This would require additional API call to get files
        # For now, use basic heuristics
        
        title = pr.get("title", "").lower()
        body = pr.get("body", "").lower()
        
        # Language skills
        if "python" in title or "python" in body:
            skills.append("Python")
        if any(js in title or js in body for js in ["javascript", "js", "node"]):
            skills.append("JavaScript")
        
        # Framework skills
        if "react" in title or "react" in body:
            skills.append("React")
        if "fastapi" in title or "fastapi" in body:
            skills.append("FastAPI")
        
        # DevOps skills
        if any(word in title or word in body for word in ["docker", "kubernetes", "k8s"]):
            skills.append("DevOps")
        
        # Database skills
        if any(word in title or word in body for word in ["database", "sql", "postgresql", "mongodb"]):
            skills.append("Database Design")
        
        # General skills based on PR size
        if pr.get("additions", 0) + pr.get("deletions", 0) > 1000:
            skills.append("Large-scale Refactoring")
        
        if pr.get("changed_files", 0) > 20:
            skills.append("Complex Integration")
        
        return list(set(skills))  # Remove duplicates
    
    def _skills_from_labels(self, labels: list) -> list:
        """Extract skills from issue labels"""
        
        skill_map = {
            "frontend": ["Frontend Development", "UI/UX"],
            "backend": ["Backend Development", "API Design"],
            "database": ["Database Design", "SQL"],
            "security": ["Security", "Vulnerability Assessment"],
            "performance": ["Performance Optimization", "Profiling"],
            "testing": ["Testing", "Test Automation"],
            "documentation": ["Technical Writing", "Documentation"],
            "devops": ["DevOps", "CI/CD", "Infrastructure"],
        }
        
        skills = []
        
        for label in labels:
            label_lower = label.lower()
            for key, skill_list in skill_map.items():
                if key in label_lower:
                    skills.extend(skill_list)
        
        return list(set(skills))  # Remove duplicates