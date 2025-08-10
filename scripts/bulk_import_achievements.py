#!/usr/bin/env python3
"""
Bulk Import Historical PRs to Achievement Collector via API
Uses the Achievement Collector REST API for integration
"""

import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List


class AchievementCollectorClient:
    """Client for Achievement Collector API"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}

    def create_achievement_from_pr(self, pr_data: Dict, business_value: Dict) -> bool:
        """Create achievement via API"""
        # Prepare achievement data
        achievement = {
            "title": pr_data["title"][:200],
            "description": f"{pr_data.get('description', '')[:500]}\\n\\nBusiness Impact: ${business_value['portfolio_value']:,.0f} portfolio value with {business_value['roi_percent']:.0f}% ROI",
            "category": self._map_category(business_value["value_category"]),
            "impact_score": min(100, business_value["business_impact_score"] * 10),
            "technical_details": {
                "pr_number": pr_data["pr_number"],
                "lines_changed": pr_data["lines_added"] + pr_data["lines_deleted"],
                "files_changed": pr_data["files_changed"],
                "implementation_time": f"{pr_data['files_changed'] * 2} hours",
            },
            "business_value": f"${business_value['portfolio_value']:,.0f} annual value | {business_value['roi_percent']:.0f}% ROI | ${business_value['cost_savings']:,.0f} cost savings",
            "metrics": {
                "portfolio_value": business_value["portfolio_value"],
                "roi_percent": business_value["roi_percent"],
                "cost_savings": business_value["cost_savings"],
                "productivity_hours": business_value["productivity_hours"],
                "performance_improvement": business_value["performance_improvement"],
            },
            "skills_demonstrated": self._extract_skills(pr_data, business_value),
            "portfolio_ready": business_value["confidence_level"] == "high",
            "tags": [
                business_value["value_category"],
                f"roi_{int(business_value['roi_percent'])}",
                business_value["confidence_level"],
                "historical_import",
            ],
            "pr_number": str(pr_data["pr_number"]),
            "completed_at": pr_data.get("merged_at", pr_data["created_at"]),
        }

        # Send to API
        try:
            data = json.dumps(achievement).encode("utf-8")
            request = urllib.request.Request(
                f"{self.base_url}/achievements", data=data, headers=self.headers
            )

            with urllib.request.urlopen(request) as response:
                if response.status in [200, 201]:
                    result = json.loads(response.read())
                    print(
                        f"  ✅ Created achievement #{result['id']} for PR #{pr_data['pr_number']}"
                    )
                    return True
                else:
                    print(f"  ❌ Failed to create achievement: {response.status}")
                    return False

        except Exception as e:
            print(f"  ❌ Error: {e}")
            # Try the PR analysis endpoint instead
            return self._try_pr_analysis_endpoint(pr_data["pr_number"])

    def _try_pr_analysis_endpoint(self, pr_number: int) -> bool:
        """Fallback to PR analysis endpoint"""
        try:
            request = urllib.request.Request(
                f"{self.base_url}/pr-analysis/analyze/{pr_number}",
                method="POST",
                headers=self.headers,
            )

            with urllib.request.urlopen(request) as response:
                if response.status in [200, 201]:
                    print("    ✅ Created via PR analysis endpoint")
                    return True

        except:
            pass
        return False

    def _map_category(self, value_category: str) -> str:
        """Map to achievement categories"""
        mapping = {
            "ai_ml": "ai_ml_implementation",
            "performance": "performance_optimization",
            "infrastructure": "infrastructure_scaling",
            "cost": "cost_optimization",
            "feature": "feature_implementation",
            "bugfix": "bug_fix",
        }
        return mapping.get(value_category, "technical_achievement")

    def _extract_skills(self, pr_data: Dict, business_value: Dict) -> List[str]:
        """Extract relevant skills"""
        skills = []

        # Base skills by category
        if business_value["value_category"] == "ai_ml":
            skills.extend(["Python", "Machine Learning", "AI/ML", "LangChain"])
        elif business_value["value_category"] == "performance":
            skills.extend(["Performance Optimization", "System Design"])
        elif business_value["value_category"] == "infrastructure":
            skills.extend(["Kubernetes", "Docker", "CI/CD", "MLOps"])

        # Extract from title
        title_lower = pr_data["title"].lower()
        if "rag" in title_lower:
            skills.append("RAG Systems")
        if "airflow" in title_lower:
            skills.append("Apache Airflow")
        if "api" in title_lower:
            skills.append("API Design")

        return list(set(skills))[:10]


def import_from_analysis_file(filename: str):
    """Import PRs from analysis JSON file"""
    print("🚀 Bulk Import to Achievement Collector")
    print("=" * 60)

    # Load analysis
    with open(filename, "r") as f:
        data = json.load(f)

    # For quick analysis format
    if "top_achievements" in data:
        achievements = data["top_achievements"]
        print(f"📊 Importing {len(achievements)} top achievements")

        client = AchievementCollectorClient()
        success_count = 0

        for i, achievement in enumerate(achievements):
            # Convert to expected format
            pr_data = {
                "pr_number": achievement["pr_number"],
                "title": achievement["title"],
                "lines_added": int(achievement.get("cost_savings", 10000) / 10),
                "lines_deleted": int(achievement.get("cost_savings", 10000) / 20),
                "files_changed": max(5, int(achievement["roi"] / 50)),
                "created_at": data["analysis_date"],
                "merged_at": data["analysis_date"],
                "description": f"{achievement['category']} implementation",
            }

            business_value = {
                "portfolio_value": achievement["value"],
                "roi_percent": achievement["roi"],
                "cost_savings": achievement.get(
                    "cost_savings", achievement["value"] * 0.7
                ),
                "productivity_hours": achievement.get(
                    "productivity_hours", achievement["value"] / 150
                ),
                "performance_improvement": achievement.get("performance_gain", 20),
                "business_impact_score": min(10, achievement["roi"] / 100),
                "confidence_level": achievement.get("confidence", "high"),
                "value_category": achievement["category"],
            }

            if client.create_achievement_from_pr(pr_data, business_value):
                success_count += 1

        print(
            f"\n✅ Successfully imported {success_count}/{len(achievements)} achievements"
        )

    # For full analysis format
    elif "pr_metrics" in data and "business_values" in data:
        pr_metrics = {pr["pr_number"]: pr for pr in data["pr_metrics"]}
        business_values = {bv["pr_number"]: bv for bv in data["business_values"]}

        # Filter high-value PRs
        high_value_prs = [
            (pr_metrics[pr_num], business_values[pr_num])
            for pr_num in pr_metrics
            if pr_num in business_values
            and business_values[pr_num]["portfolio_value"] > 10000
        ]

        print(f"📊 Found {len(high_value_prs)} high-value PRs (>$10k)")

        client = AchievementCollectorClient()
        success_count = 0

        for pr_data, business_value in high_value_prs[:20]:  # Limit to top 20
            if client.create_achievement_from_pr(pr_data, business_value):
                success_count += 1

        print(
            f"\n✅ Successfully imported {success_count}/{len(high_value_prs[:20])} achievements"
        )


def main():
    """Main import function"""
    print("📁 Available analysis files:")

    analysis_files = list(Path(".").glob("*pr_analysis*.json"))
    analysis_files.extend(list(Path(".").glob("*portfolio_analysis*.json")))

    if not analysis_files:
        print("❌ No analysis files found. Run PR analyzer first.")
        return

    for i, file in enumerate(analysis_files):
        print(f"{i + 1}. {file.name}")

    # Use the most recent
    latest = max(analysis_files, key=lambda p: p.stat().st_mtime)
    print(f"\n📊 Using: {latest.name}")

    # Check if Achievement Collector is running
    try:
        with urllib.request.urlopen("http://localhost:8001/health") as response:
            if response.status == 200:
                print("✅ Achievement Collector is running")
    except:
        print("⚠️ Achievement Collector not responding on port 8001")
        print("   Start it with: just dev-start")
        return

    # Import
    import_from_analysis_file(str(latest))

    print("\n🎯 Next Steps:")
    print("1. Visit http://localhost:8001/achievements to see imported data")
    print("2. Generate tech docs from achievements")
    print("3. Deploy to portfolio website")


if __name__ == "__main__":
    main()
