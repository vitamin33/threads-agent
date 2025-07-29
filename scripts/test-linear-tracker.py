#!/usr/bin/env python3
"""Test script for Linear tracker functionality."""

import asyncio
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


async def test_linear_tracker():
    """Test the Linear tracker with mock data."""
    from services.achievement_collector.services.linear_tracker import LinearTracker

    print("🔍 Testing Linear Tracker...")

    # Create tracker instance
    tracker = LinearTracker()

    # Test with mock issue data
    mock_issue = {
        "id": "TEST-123",
        "identifier": "TEST-123",
        "number": 123,
        "title": "Implement MLOps monitoring dashboard",
        "description": "Add MLflow integration and model performance tracking using Prometheus metrics",
        "state": {"name": "Done", "type": "completed"},
        "priority": {"name": "High"},
        "estimate": 5,
        "labels": [{"name": "mlops"}, {"name": "feature"}, {"name": "python"}],
        "startedAt": "2025-01-28T08:00:00Z",
        "completedAt": "2025-01-28T12:00:00Z",
        "createdAt": "2025-01-28T07:00:00Z",
        "cycle": {"name": "Sprint 12"},
        "team": {"name": "Backend"},
    }

    print("\n📋 Mock Issue Data:")
    print(f"  - Title: {mock_issue['title']}")
    print(f"  - Priority: {mock_issue['priority']['name']}")
    print(f"  - Labels: {', '.join([label['name'] for label in mock_issue['labels']])}")

    # Test category determination
    category = tracker._determine_category(mock_issue.get("labels", []))
    print(f"\n🏷️  Determined Category: {category}")

    # Test skills extraction
    skills = tracker._extract_skills(mock_issue)
    print(f"\n🛠️  Extracted Skills: {', '.join(skills)}")

    # Test achievement creation
    print("\n✨ Creating achievement from issue...")
    try:
        await tracker._create_issue_achievement(mock_issue)
        print("✅ Achievement created successfully!")
    except Exception as e:
        print(f"❌ Error creating achievement: {e}")
        import traceback

        traceback.print_exc()

    # Test with mock epic/project data
    mock_project = {
        "id": "EPIC-E4.2",
        "name": "Achievement Auto-Collection System",
        "description": "Implement automatic achievement tracking from git, Linear, and MLflow",
        "state": "completed",
        "startedAt": "2025-01-20T08:00:00Z",
        "completedAt": "2025-01-28T16:00:00Z",
        "createdAt": "2025-01-20T07:00:00Z",
        "issues": [{"estimate": 3}, {"estimate": 5}, {"estimate": 2}, {"estimate": 8}],
    }

    print("\n\n📊 Mock Epic Data:")
    print(f"  - Name: {mock_project['name']}")
    print(f"  - Total Issues: {len(mock_project['issues'])}")
    print(
        f"  - Total Points: {sum(i.get('estimate', 0) for i in mock_project['issues'])}"
    )

    print("\n✨ Creating achievement from epic...")
    try:
        await tracker._create_epic_achievement(mock_project)
        print("✅ Epic achievement created successfully!")
    except Exception as e:
        print(f"❌ Error creating epic achievement: {e}")
        import traceback

        traceback.print_exc()


async def test_linear_mcp_connection():
    """Test connection to Linear MCP server."""
    print("\n\n🔌 Testing Linear MCP Connection...")

    try:
        # Import MCP client
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        # Check if Linear MCP is configured
        linear_mcp_path = os.path.expanduser(
            "~/Library/Application Support/Claude/claude_desktop_config.json"
        )
        if os.path.exists(linear_mcp_path):
            print("✅ Linear MCP configuration found")

            # Try to connect to Linear MCP
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-linear"],
                env={
                    "LINEAR_API_KEY": os.getenv("LINEAR_API_KEY", ""),
                    "NODE_NO_WARNINGS": "1",
                },
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # List available tools
                    tools = await session.list_tools()
                    print(f"\n📦 Available Linear MCP tools: {len(tools.tools)}")
                    for tool in tools.tools[:5]:  # Show first 5
                        print(f"  - {tool.name}")

                    # Try to get viewer info
                    result = await session.call_tool("linear_getViewer", {})
                    print(f"\n👤 Linear User: {result.content[0].text}")
        else:
            print("⚠️  Linear MCP not configured in Claude desktop")

    except Exception as e:
        print(f"❌ Error connecting to Linear MCP: {e}")
        print("   Make sure Linear MCP server is installed and configured")


async def main():
    """Run all tests."""
    print("🚀 Linear Tracker Test Suite\n")

    # Test basic tracker functionality
    await test_linear_tracker()

    # Test MCP connection
    await test_linear_mcp_connection()

    print("\n\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
