#!/usr/bin/env python3
"""
Integration Script: Historical PR Analyzer → Achievement Collector
Imports historical PR analysis results into the Achievement Collector system
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.achievement_collector.db.config import SessionLocal
from services.achievement_collector.db.models import Achievement
from services.achievement_collector.api.schemas import AchievementCreate


class HistoricalPRIntegrator:
    """Integrates historical PR analysis into Achievement Collector"""

    def __init__(self, analysis_file: str):
        self.analysis_file = analysis_file
        self.db = SessionLocal()

    def load_analysis_results(self) -> Dict:
        """Load PR analysis results from JSON file"""
        with open(self.analysis_file, "r") as f:
            return json.load(f)

    def create_achievement_from_pr(
        self, pr_data: Dict, business_value: Dict
    ) -> Optional[Achievement]:
        """Create achievement record from PR analysis data"""
        try:
            # Check if achievement already exists
            existing = (
                self.db.query(Achievement)
                .filter(Achievement.pr_number == str(pr_data["pr_number"]))
                .first()
            )

            if existing:
                print(
                    f"  ⚠️ PR #{pr_data['pr_number']} already exists, updating metrics..."
                )
                # Update with new business value metrics
                existing.metadata_json = {
                    **(existing.metadata_json or {}),
                    "portfolio_value": business_value["portfolio_value"],
                    "roi_percent": business_value["roi_percent"],
                    "cost_savings": business_value["cost_savings"],
                    "productivity_hours": business_value["productivity_hours"],
                    "performance_improvement": business_value[
                        "performance_improvement"
                    ],
                    "value_category": business_value["value_category"],
                    "confidence_level": business_value["confidence_level"],
                    "business_impact_score": business_value["business_impact_score"],
                }
                self.db.commit()
                return existing

            # Create new achievement
            achievement_data = AchievementCreate(
                title=pr_data["title"][:200],  # Limit title length
                description=f"{pr_data.get('description', '')}\\n\\nBusiness Value: ${business_value['portfolio_value']:,.0f} | ROI: {business_value['roi_percent']:.0f}%",
                category=self._map_category(business_value["value_category"]),
                impact_score=min(
                    100, business_value["business_impact_score"] * 10
                ),  # Scale to 0-100
                technical_details={
                    "pr_number": pr_data["pr_number"],
                    "lines_added": pr_data["lines_added"],
                    "lines_deleted": pr_data["lines_deleted"],
                    "files_changed": pr_data["files_changed"],
                    "author": pr_data["author"],
                    "merged_at": pr_data.get("merged_at"),
                },
                business_value=f"${business_value['portfolio_value']:,.0f} annual value, {business_value['roi_percent']:.0f}% ROI",
                metrics={
                    "portfolio_value": business_value["portfolio_value"],
                    "roi_percent": business_value["roi_percent"],
                    "cost_savings": business_value["cost_savings"],
                    "productivity_hours": business_value["productivity_hours"],
                    "performance_improvement": business_value[
                        "performance_improvement"
                    ],
                },
                skills_demonstrated=[
                    skill for skill in self._extract_skills(pr_data, business_value)
                ],
                portfolio_ready=business_value["confidence_level"] == "high",
                pr_number=str(pr_data["pr_number"]),
                created_at=datetime.fromisoformat(
                    pr_data["created_at"].replace("Z", "+00:00")
                ),
                completed_at=datetime.fromisoformat(
                    pr_data.get("merged_at", pr_data["created_at"]).replace(
                        "Z", "+00:00"
                    )
                ),
                metadata_json={
                    "value_category": business_value["value_category"],
                    "confidence_level": business_value["confidence_level"],
                    "business_impact_score": business_value["business_impact_score"],
                    "labels": pr_data.get("labels", []),
                },
            )

            # Save to database
            db_achievement = Achievement(**achievement_data.dict())
            self.db.add(db_achievement)
            self.db.commit()
            self.db.refresh(db_achievement)

            print(
                f"  ✅ Created achievement for PR #{pr_data['pr_number']}: {pr_data['title'][:50]}..."
            )
            return db_achievement

        except Exception as e:
            print(
                f"  ❌ Error creating achievement for PR #{pr_data['pr_number']}: {e}"
            )
            self.db.rollback()
            return None

    def _map_category(self, value_category: str) -> str:
        """Map value category to achievement category"""
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
        """Extract skills from PR data"""
        skills = []

        # Category-based skills
        category_skills = {
            "ai_ml": ["Machine Learning", "AI/ML", "Python", "LangChain", "OpenAI"],
            "performance": ["Performance Optimization", "Caching", "Async Programming"],
            "infrastructure": ["Kubernetes", "Docker", "CI/CD", "DevOps", "MLOps"],
            "cost": ["FinOps", "Cost Optimization", "Resource Management"],
            "feature": ["Feature Development", "API Design", "System Design"],
            "bugfix": ["Debugging", "Problem Solving", "Testing"],
        }

        skills.extend(category_skills.get(business_value["value_category"], []))

        # Extract from title/description
        title_lower = pr_data["title"].lower()
        if "rag" in title_lower or "retrieval" in title_lower:
            skills.append("RAG Systems")
        if "airflow" in title_lower:
            skills.append("Apache Airflow")
        if (
            "docker" in title_lower
            or "kubernetes" in title_lower
            or "k8s" in title_lower
        ):
            skills.append("Container Orchestration")

        return list(set(skills))[:10]  # Limit to 10 skills

    def import_historical_prs(self):
        """Import all historical PRs into Achievement Collector"""
        print("🚀 Starting Historical PR Import to Achievement Collector")
        print("=" * 60)

        # Load analysis results
        data = self.load_analysis_results()

        if "pr_metrics" not in data or "business_values" not in data:
            print("❌ Invalid analysis file format")
            return

        pr_metrics = data["pr_metrics"]
        business_values = data["business_values"]

        print(f"📊 Found {len(pr_metrics)} PRs to import")
        print("-" * 60)

        # Create mapping
        pr_map = {pr["pr_number"]: pr for pr in pr_metrics}
        bv_map = {bv["pr_number"]: bv for bv in business_values}

        # Process each PR
        success_count = 0
        update_count = 0
        error_count = 0

        for pr_number in pr_map:
            if pr_number not in bv_map:
                continue

            pr_data = pr_map[pr_number]
            business_value = bv_map[pr_number]

            # Only import high-value PRs
            if business_value["portfolio_value"] < 5000:
                continue

            result = self.create_achievement_from_pr(pr_data, business_value)
            if result:
                if result.created_at == result.updated_at:
                    success_count += 1
                else:
                    update_count += 1
            else:
                error_count += 1

        # Summary
        print("\n" + "=" * 60)
        print("📊 IMPORT SUMMARY")
        print("=" * 60)
        print(f"✅ New achievements created: {success_count}")
        print(f"🔄 Existing achievements updated: {update_count}")
        print(f"❌ Errors: {error_count}")
        print(f"📊 Total processed: {success_count + update_count + error_count}")

        # Get total portfolio value
        total_value = (
            self.db.query(Achievement).filter(Achievement.metrics != None).all()
        )

        portfolio_sum = sum(
            a.metrics.get("portfolio_value", 0) for a in total_value if a.metrics
        )

        print(
            f"\n💰 Total Portfolio Value in Achievement Collector: ${portfolio_sum:,.2f}"
        )
        print(
            "✅ Integration complete! Your achievements now have business value metrics."
        )

        self.db.close()


def main():
    """Main integration function"""
    # Find the most recent analysis file
    analysis_files = list(Path(".").glob("*pr_analysis*.json"))

    if not analysis_files:
        print("❌ No PR analysis files found. Run the analyzer first:")
        print("   python3 simple_pr_analyzer.py")
        return

    # Use the most recent file
    latest_file = max(analysis_files, key=lambda p: p.stat().st_mtime)
    print(f"📁 Using analysis file: {latest_file}")

    # Check if running in the right environment
    if not Path("services/achievement_collector").exists():
        print("❌ Please run from the project root directory")
        return

    # Run integration
    integrator = HistoricalPRIntegrator(str(latest_file))
    integrator.import_historical_prs()


if __name__ == "__main__":
    main()
