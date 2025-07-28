#!/bin/bash
# Setup unified MCP configuration for all 3 virtual teammates

set -e

echo "🔧 Setting up unified MCP configuration for multi-teammate system..."

# Create user-level Claude directory
mkdir -p ~/.claude

# Create unified MCP configuration
cat > ~/.claude/mcp-config.json << 'EOF'
{
  "mcpServers": {
    "searxng": {
      "command": "mcp-searxng",
      "args": ["--url", "http://localhost:8888"],
      "env": {}
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-8970898560864-8950765486740-LPDfpEPZ5cEFWNcN7RLplgoR",
        "SLACK_TEAM_ID": "T08V06BA8KH",
        "SLACK_CHANNEL_IDS": "alerts"
      }
    },
    "redis": {
      "command": "redis-mcp",
      "args": [],
      "env": {
        "REDIS_URL": "redis://localhost:6379"
      }
    },
    "kubernetes": {
      "command": "mcp-server-kubernetes",
      "args": ["--kubeconfig", "$HOME/.kube/config", "--context", "k3d-threads-agent"],
      "env": {}
    },
    "postgresql": {
      "command": "postgres-mcp-server",
      "args": [],
      "env": {
        "PGHOST": "localhost",
        "PGPORT": "5432",
        "PGUSER": "postgres",
        "PGPASSWORD": "postgres",
        "PGDATABASE": "threads_agent"
      }
    },
    "openai": {
      "command": "openai-mcp-server",
      "args": [],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    },
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "$HOME/.claude/shared-data/threads-metrics.db"]
    },
    "linear": {
      "command": "node",
      "args": ["$HOME/.claude/shared-mcp/linear/index.js"],
      "env": {
        "LINEAR_API_KEY": "lin_api_VIi0UyD5KDmiqSum9o7Rfgehs0zSKHQinh3gYngK"
      }
    }
  }
}
EOF

# Create shared data directory for SQLite
mkdir -p ~/.claude/shared-data

# Create shared MCP directory
mkdir -p ~/.claude/shared-mcp/linear

# Check if Linear MCP exists in any repo and copy to shared location
FOUND_LINEAR=false
for TEAMMATE in "jordan-kim" "riley-morgan" "alex-chen"; do
    LINEAR_PATH="$HOME/development/team/$TEAMMATE/threads-agent/mcp/linear/index.js"
    if [ -f "$LINEAR_PATH" ]; then
        echo "📦 Found Linear MCP in $TEAMMATE's repo, copying to shared location..."
        cp -r "$(dirname "$LINEAR_PATH")"/* ~/.claude/shared-mcp/linear/
        FOUND_LINEAR=true
        break
    fi
done

if [ "$FOUND_LINEAR" = false ]; then
    echo "⚠️  Warning: Linear MCP not found in any teammate repository"
    echo "   You'll need to manually copy it to ~/.claude/shared-mcp/linear/"
fi

# Remove project-level MCP configs to avoid conflicts
echo ""
echo "🧹 Cleaning up project-level MCP configs to prevent conflicts..."
for TEAMMATE in "jordan-kim" "riley-morgan" "alex-chen"; do
    MCP_CONFIG="$HOME/development/team/$TEAMMATE/threads-agent/.claude/mcp-config.json"
    if [ -f "$MCP_CONFIG" ]; then
        echo "   Backing up and removing: $MCP_CONFIG"
        mv "$MCP_CONFIG" "$MCP_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    fi
done

echo ""
echo "✅ Unified MCP configuration complete!"
echo ""
echo "📍 Configuration location: ~/.claude/mcp-config.json"
echo "📍 Shared Linear MCP: ~/.claude/shared-mcp/linear/"
echo "📍 Shared SQLite DB: ~/.claude/shared-data/threads-metrics.db"
echo ""
echo "🔄 All 3 virtual teammates now share the same MCP servers!"
echo ""
echo "Note: The filesystem MCP has been removed from the unified config"
echo "      since it was repository-specific. Add it back per-project if needed."