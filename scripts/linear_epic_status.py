#!/usr/bin/env python3
"""
Linear Epic Status Checker

Fetches epics E5 through E12 from Linear API and provides recommendations
for parallel work considering E6 is already in progress.

Usage:
    export LINEAR_API_KEY=your_api_key_here
    python scripts/linear_epic_status.py

Requirements:
    - LINEAR_API_KEY environment variable
    - requests library (included in requirements.txt)
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

import requests


@dataclass
class EpicStatus:
    """Data class to hold epic information"""

    identifier: str
    name: str
    status: str
    progress: float
    assignees: List[str]
    issue_count: int
    completed_count: int
    priority: str
    url: str
    description: Optional[str] = None


class LinearAPI:
    """Linear API client for fetching epic information"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        self.base_url = "https://api.linear.app/graphql"

    def gql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GraphQL query with error handling"""
        try:
            response = requests.post(
                self.base_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                print(f"❌ Linear API errors: {result['errors']}")
                sys.exit(1)

            return cast(Dict[str, Any], result["data"])
        except requests.RequestException as e:
            print(f"❌ Request failed: {e}")
            sys.exit(1)

    def fetch_epics(self, epic_names: List[str]) -> List[EpicStatus]:
        """Fetch epic information for given epic names"""
        epics = []

        for epic_name in epic_names:
            epic_data = self._fetch_single_epic(epic_name)
            if epic_data:
                epics.append(epic_data)

        return epics

    def _fetch_single_epic(self, epic_name: str) -> Optional[EpicStatus]:
        """Fetch information for a single epic"""
        # First, find the project by name pattern
        project_query = """
        query GetProject($name: String!) {
            projects(filter: { name: { contains: $name } }) {
                nodes {
                    id
                    name
                    description
                    state
                    progress
                    url
                    lead {
                        name
                    }
                    members {
                        nodes {
                            name
                        }
                    }
                }
            }
        }
        """

        data = self.gql(project_query, {"name": epic_name})
        projects = data["projects"]["nodes"]

        if not projects:
            print(f"⚠️  Epic {epic_name} not found")
            return None

        project = projects[0]

        # Now fetch issues for this project
        issues_query = """
        query GetProjectIssues($projectId: ID!) {
            issues(filter: { project: { id: { eq: $projectId } } }) {
                nodes {
                    id
                    identifier
                    title
                    priority
                    state {
                        name
                        type
                    }
                    assignee {
                        name
                    }
                }
            }
        }
        """

        issues_data = self.gql(issues_query, {"projectId": project["id"]})
        issues = issues_data["issues"]["nodes"]

        # Calculate metrics
        total_issues = len(issues)
        completed_issues = len([i for i in issues if i["state"]["type"] == "completed"])
        progress = (completed_issues / total_issues * 100) if total_issues > 0 else 0

        # Get assignees
        assignees = list(
            set(
                [
                    issue["assignee"]["name"]
                    for issue in issues
                    if issue["assignee"] and issue["assignee"]["name"]
                ]
            )
        )

        # Add project lead if exists
        if project.get("lead") and project["lead"]["name"]:
            assignees.append(f"{project['lead']['name']} (Lead)")

        # Get status
        status = project.get("state", "Unknown")
        if progress == 100:
            status = "Completed"
        elif progress > 0:
            status = "In Progress"
        else:
            status = "Not Started"

        return EpicStatus(
            identifier=epic_name,
            name=project["name"],
            status=status,
            progress=progress,
            assignees=assignees,
            issue_count=total_issues,
            completed_count=completed_issues,
            priority="Medium",  # Default, as this info isn't always available at project level
            url=project.get("url", ""),
            description=project.get("description"),
        )


class EpicAnalyzer:
    """Analyzes epic status and provides recommendations"""

    @staticmethod
    def recommend_next_epic(epics: List[EpicStatus], current_epic: str = "E6") -> str:
        """Recommend which epic to start next for parallel work"""
        recommendations = []

        # Filter out completed and current epics
        available_epics = [
            e
            for e in epics
            if e.status != "Completed" and current_epic not in e.identifier
        ]

        if not available_epics:
            return "🎉 All epics are completed or only E6 remains!"

        # Scoring criteria
        for epic in available_epics:
            score = 0
            reasons = []

            # Prefer not started epics for clean parallel work
            if epic.status == "Not Started":
                score += 30
                reasons.append("clean start")

            # Avoid epics with too many assignees (potential conflicts)
            if len(epic.assignees) == 0:
                score += 20
                reasons.append("no conflicts")
            elif len(epic.assignees) <= 2:
                score += 10
                reasons.append("minimal team overlap")
            else:
                score -= 10
                reasons.append("many assignees")

            # Prefer epics with smaller scope for faster completion
            if epic.issue_count <= 5:
                score += 15
                reasons.append("small scope")
            elif epic.issue_count <= 10:
                score += 5
                reasons.append("medium scope")

            # Sequential preference (earlier epics might have dependencies)
            epic_num = int(epic.identifier[1:]) if epic.identifier[1:].isdigit() else 0
            if epic_num <= 8:
                score += 10
                reasons.append("earlier in sequence")

            recommendations.append({"epic": epic, "score": score, "reasons": reasons})

        # Sort by score and return recommendation
        recommendations.sort(key=lambda x: cast(int, x["score"]), reverse=True)
        best = recommendations[0]

        epic_obj = cast(EpicStatus, best["epic"])
        reasons_list = cast(List[str], best["reasons"])
        return f"""🎯 Recommended: {epic_obj.identifier}
   Reasons: {", ".join(reasons_list)}
   Score: {best["score"]}/70"""


def print_epic_summary(epics: List[EpicStatus]) -> None:
    """Print a formatted summary of all epics"""
    print("\n" + "=" * 80)
    print("📋 LINEAR EPIC STATUS REPORT (E5-E12)")
    print("=" * 80)

    for epic in sorted(epics, key=lambda x: x.identifier):
        status_emoji = {
            "Completed": "✅",
            "In Progress": "🔄",
            "Not Started": "⭕",
        }.get(epic.status, "❓")

        print(f"\n{status_emoji} {epic.identifier}: {epic.name}")
        print(f"   Status: {epic.status}")
        print(
            f"   Progress: {epic.progress:.1f}% ({epic.completed_count}/{epic.issue_count} tasks)"
        )

        if epic.assignees:
            print(f"   Team: {', '.join(epic.assignees)}")
        else:
            print("   Team: Unassigned")

        if epic.description and len(epic.description) > 0:
            desc = (
                epic.description[:100] + "..."
                if len(epic.description) > 100
                else epic.description
            )
            print(f"   Description: {desc}")

        if epic.url:
            print(f"   URL: {epic.url}")

        print("-" * 80)


def main() -> None:
    """Main execution function"""
    # Check for API key
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("❌ Error: LINEAR_API_KEY environment variable not set")
        print(
            "Usage: export LINEAR_API_KEY=your_api_key && python scripts/linear_epic_status.py"
        )
        sys.exit(1)

    # Initialize API client
    client = LinearAPI(api_key)

    # Define epic names to search for
    epic_names = [f"E{i}" for i in range(5, 13)]  # E5 through E12

    print("🔍 Fetching epic information from Linear...")

    # Fetch epic data
    epics = client.fetch_epics(epic_names)

    if not epics:
        print("❌ No epics found. Check your LINEAR_API_KEY and epic names.")
        sys.exit(1)

    # Print summary
    print_epic_summary(epics)

    # Provide recommendation
    analyzer = EpicAnalyzer()
    recommendation = analyzer.recommend_next_epic(epics, current_epic="E6")

    print("\n" + "=" * 80)
    print("🤖 PARALLEL WORK RECOMMENDATION")
    print("=" * 80)
    print("Current: E6 (In Progress)")
    print(recommendation)
    print("\n💡 Tip: Choose epics with minimal team overlap and clear scope")
    print("=" * 80)


if __name__ == "__main__":
    main()
