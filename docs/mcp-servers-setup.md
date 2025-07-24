# MCP Servers Setup Guide for Threads-Agent

## Overview
This guide documents the setup and configuration of Model Context Protocol (MCP) servers for the threads-agent project.

## Installed MCP Servers

### 1. SearXNG MCP Server (Free Alternative to Brave Search)
**Purpose**: Competitive analysis and viral content research
**Status**: ✅ Installed and configured
**Installation**: `npm install -g mcp-searxng`
**Setup**: Run `./scripts/setup-searxng.sh` then `cd .searxng && docker-compose up -d`
**Use Cases**:
- Research trending AI/ML content on Threads
- Analyze competitor engagement strategies
- Discover viral content patterns
- Access multiple search engines (DuckDuckGo, Qwant, Google, Bing)
**Advantages**:
- 100% free, no API key required
- Privacy-respecting metasearch
- Self-hosted, no rate limits
- JSON API for programmatic access

### 2. Slack MCP Server
**Purpose**: Notifications for Level 9 system alerts
**Status**: ✅ Installed (deprecated package warning)
**Installation**: `npm install -g @modelcontextprotocol/server-slack`
**Configuration Required**:
- SLACK_BOT_TOKEN
- SLACK_TEAM_ID
- SLACK_CHANNEL_IDS
**Use Cases**:
- Alert on high-priority system failures
- Notify when engagement drops below threshold
- Send revenue milestone notifications

### 3. SQLite MCP Server
**Purpose**: Local data experimentation
**Status**: ⚠️ Requires Python package manager (uvx/pipx)
**Installation**:
```bash
# Option 1: Using uvx (recommended)
uvx install mcp-server-sqlite

# Option 2: Using pipx
pipx install mcp-server-sqlite
```
**Use Cases**:
- Test content generation patterns locally
- Experiment with engagement data
- Prototype new persona behaviors

### 4. Docker MCP Server
**Purpose**: Container management for k8s setup
**Status**: ⚠️ Package not found in npm registry
**Alternative**: Use Docker CLI directly via Bash tool
**Use Cases**:
- Manage container lifecycle
- Monitor container resources
- Debug k8s pod issues

## Claude Settings Configuration

To enable these MCP servers, add the following to your Claude settings:

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-brave-api-key"
      }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token",
        "SLACK_TEAM_ID": "your-team-id",
        "SLACK_CHANNEL_IDS": "C1234567890,C0987654321"
      }
    },
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./data/threads-agent.db"]
    }
  }
}
```

## Environment Variables Required

### Brave Search
- `BRAVE_API_KEY`: Get from https://brave.com/search/api/ (pending)

### Slack (✅ Configured)
- `SLACK_BOT_TOKEN`: xoxb-8970898560864-8950765486740-LPDfpEPZ5cEFWNcN7RLplgoR
- `SLACK_TEAM_ID`: T08UJSEGGRE
- `SLACK_CHANNEL_IDS`: alerts (Channel ID: C08UZMT9D6J)
- `SLACK_SIGNING_SECRET`: d14a59f32d23120a6cbd391e24f0e4c1
- Bot Name: roi-agent-bot

## Integration with Threads-Agent

### 1. Competitive Analysis (Brave Search)
- Research trending AI personas and content styles
- Monitor competitor engagement rates
- Identify viral content patterns for each persona

### 2. Alert System (Slack)
- Critical: Service downtime, database failures
- Warning: Low engagement rates, high costs
- Info: Daily summaries, revenue milestones

### 3. Data Experimentation (SQLite)
- Store and analyze local engagement metrics
- Test new content generation strategies
- Prototype persona behavior modifications

### 4. Container Management (Docker)
- Monitor k3d cluster health
- Debug service deployments
- Manage resource allocation

## Next Steps

1. Obtain API keys for Brave Search and Slack
2. Install uvx or pipx for Python-based MCP servers
3. Configure MCP servers in Claude settings
4. Test each integration with the threads-agent system

## Troubleshooting

### Deprecated Package Warnings
The npm packages show deprecation warnings but still function. Monitor for official replacements.

### Python Package Installation
If uvx/pipx aren't available:
```bash
# Install pipx
brew install pipx
pipx ensurepath

# Or install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Docker MCP Alternative
Use the existing Docker CLI integration via Bash tool:
```bash
just docker-status  # Check Docker daemon
kubectl get pods    # Manage k8s containers
```
