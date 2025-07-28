#!/usr/bin/env python3
"""Test comprehensive PR analyzer."""

import os

# Set environment variables before imports
os.environ["USE_SQLITE"] = "true"
os.environ["OPENAI_API_KEY"] = "test"

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.achievement_collector.services.comprehensive_pr_analyzer import (
    ComprehensivePRAnalyzer,
)


async def test_comprehensive_analyzer():
    """Test comprehensive PR analysis."""

    analyzer = ComprehensivePRAnalyzer()

    # Mock PR data
    pr_data = {
        "number": 123,
        "title": "Optimize API performance with Redis caching",
        "body": "This PR implements Redis caching to reduce database load and improve API response times by 40%.",
        "created_at": "2025-01-28T10:00:00Z",
        "merged_at": "2025-01-28T14:00:00Z",
        "html_url": "https://github.com/test/repo/pull/123",
        "user": {"login": "test_user"},
        "labels": [{"name": "performance"}, {"name": "backend"}],
    }

    # Mock commit SHAs
    base_sha = "abc123"
    head_sha = "def456"

    try:
        # Analyze the PR
        analysis = await analyzer.analyze_pr(pr_data, base_sha, head_sha)

        print("✅ PR Analysis completed")
        print(f"   Metadata keys: {list(analysis.get('metadata', {}).keys())}")
        print(f"   Code metrics: {bool(analysis.get('code_metrics'))}")
        print(f"   Performance metrics: {bool(analysis.get('performance_metrics'))}")
        print(f"   Business metrics: {bool(analysis.get('business_metrics'))}")
        print(f"   Composite scores: {analysis.get('composite_scores', {})}")

        # Check that key analysis sections exist
        expected_sections = [
            "metadata",
            "code_metrics",
            "performance_metrics",
            "business_metrics",
            "quality_metrics",
            "composite_scores",
        ]

        missing_sections = [
            section for section in expected_sections if section not in analysis
        ]
        if missing_sections:
            print(f"⚠️  Missing sections: {missing_sections}")
        else:
            print("✅ All expected analysis sections present")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_comprehensive_analyzer())
    sys.exit(0 if success else 1)