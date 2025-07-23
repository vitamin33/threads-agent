#!/bin/bash
set -e

echo "🔧 Setting up Linear MCP Server for Threads Agent Stack"
echo "======================================================="

# Check if LINEAR_API_KEY is provided
if [ -z "$1" ]; then
    echo "❌ Error: LINEAR_API_KEY not provided"
    echo "Usage: ./scripts/setup-linear-mcp.sh YOUR_LINEAR_API_KEY"
    exit 1
fi

LINEAR_API_KEY=$1

# Navigate to MCP directory
cd mcp/linear

# Create .env file
echo "📝 Creating .env file..."
cat > .env << EOF
LINEAR_API_KEY=$LINEAR_API_KEY
EOF

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create MCP config for Claude Desktop
echo "🔧 Creating MCP configuration..."
MCP_CONFIG_DIR="$HOME/.config/claude/mcp"
mkdir -p "$MCP_CONFIG_DIR"

# Check if config file exists
if [ -f "$MCP_CONFIG_DIR/servers.json" ]; then
    echo "⚠️  MCP config already exists. Backing up..."
    cp "$MCP_CONFIG_DIR/servers.json" "$MCP_CONFIG_DIR/servers.json.backup"
fi

# Create or update the MCP config
cat > "$MCP_CONFIG_DIR/servers.json" << EOF
{
  "linear": {
    "command": "node",
    "args": ["$(pwd)/index.js"],
    "env": {
      "LINEAR_API_KEY": "$LINEAR_API_KEY"
    }
  }
}
EOF

echo "✅ Linear MCP Server setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Restart Claude Desktop to load the new MCP server"
echo "2. You'll have access to these Linear tools:"
echo "   - linear_list_issues: List and filter issues"
echo "   - linear_create_issue: Create new issues"
echo "   - linear_update_issue: Update existing issues"
echo "   - linear_get_issue: Get issue details"
echo "   - linear_list_teams: List all teams"
echo ""
echo "💡 Example usage in Claude:"
echo "   'List all Linear issues in progress'"
echo "   'Create a Linear issue for implementing search feature'"