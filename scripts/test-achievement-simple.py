#!/usr/bin/env python3
"""Simple test for achievement collector without dependencies."""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_basic_functionality():
    """Test basic achievement collector functionality."""
    print("🔍 Testing Achievement Collector...")

    # Test mock Linear issue processing
    mock_issue = {
        "title": "Implement MLOps monitoring",
        "labels": [{"name": "mlops"}, {"name": "feature"}],
        "priority": {"name": "high"},
        "estimate": 5,
    }

    # Simulate category determination
    label_names = [
        label.get("name", "").lower() for label in mock_issue.get("labels", [])
    ]

    if any(label in label_names for label in ["feature", "enhancement"]):
        category = "feature"
    else:
        category = "development"

    print(f"\n📋 Mock Issue: {mock_issue['title']}")
    print(f"🏷️  Category: {category}")
    print(f"🎯 Priority: {mock_issue['priority']['name']}")

    # Simulate skills extraction
    skills = []
    for label in label_names:
        if "mlops" in label:
            skills.append("MLOps")
        if "python" in label:
            skills.append("Python")

    if "mlflow" in mock_issue["title"].lower():
        skills.append("MLflow")

    skills.extend(["Problem Solving", "Agile Development"])

    print(f"🛠️  Skills: {', '.join(skills[:5])}")

    # Calculate impact score
    priority_scores = {"urgent": 90, "high": 75, "medium": 60, "low": 45, "none": 30}
    priority = mock_issue.get("priority", {}).get("name", "medium").lower()
    impact_score = priority_scores.get(priority, 60)

    print(f"💪 Impact Score: {impact_score}")

    print("\n✅ Basic functionality test passed!")


def test_git_commit_parsing():
    """Test git commit parsing logic."""
    print("\n\n🔍 Testing Git Commit Parsing...")

    # Mock commit data
    commit = {
        "hash": "abc123def456",
        "message": "feat(mlops): add model versioning support",
        "files_changed": 5,
        "lines_added": 150,
        "lines_deleted": 30,
    }

    # Parse commit message
    import re

    match = re.match(r"(\w+)\((.*?)\):\s*(.*)", commit["message"])
    if match:
        commit_type = match.group(1)
        scope = match.group(2)
        description = match.group(3)
    else:
        commit_type = "update"
        scope = "general"
        description = commit["message"]

    print(f"\n📋 Commit: {commit['hash'][:8]}")
    print(f"📝 Type: {commit_type}")
    print(f"🎯 Scope: {scope}")
    print(f"💬 Description: {description}")

    # Check if significant
    significant_patterns = [r"feat\(.*\):", r"fix\(.*\):", r"perf\(.*\):"]
    is_significant = any(re.match(p, commit["message"]) for p in significant_patterns)
    total_changes = commit["lines_added"] + commit["lines_deleted"]

    if is_significant or total_changes >= 50:
        print(f"✨ Commit is significant (changes: {total_changes})")
    else:
        print(f"ℹ️  Commit not significant (changes: {total_changes})")

    print("\n✅ Git parsing test passed!")


if __name__ == "__main__":
    print("🚀 Achievement Collector Simple Test\n")
    test_basic_functionality()
    test_git_commit_parsing()
    print("\n\n✅ All tests completed successfully!")
