#!/bin/bash
# Enhanced CI Monitor Runner Script
# Supports multiple repositories and proper volume mounts

# Stop any existing monitor
echo "Stopping existing monitor..."
docker stop ci-monitor 2>/dev/null
docker rm ci-monitor 2>/dev/null

# Configuration for all three teammate repositories
REPOS_CONFIG='[
  {
    "owner": "threads-agent-stack",
    "name": "threads-agent",
    "local_path": "/repos/threads-agent"
  },
  {
    "owner": "threads-agent-stack",
    "name": "threads-agent",
    "local_path": "/repos/team/jordan-kim/threads-agent"
  },
  {
    "owner": "threads-agent-stack",
    "name": "threads-agent",
    "local_path": "/repos/team/riley-morgan/threads-agent"
  }
]'

# Build the image
echo "Building CI monitor image..."
docker build -t ci-monitor:local .

# Run the monitor with proper mounts
echo "Starting CI monitor..."
docker run -d \
  --name ci-monitor \
  -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  -e GITHUB_TOKEN="${GITHUB_TOKEN:-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}" \
  -e MONITORED_REPOS="${MONITORED_REPOS:-$REPOS_CONFIG}" \
  -e MONITOR_INTERVAL="${MONITOR_INTERVAL:-60}" \
  -e AUTO_APPROVE="${AUTO_APPROVE:-true}" \
  -v /Users/vitaliiserbyn/development:/repos:rw \
  -v /Users/vitaliiserbyn/.kube:/root/.kube:ro \
  -v /usr/local/bin/claude:/usr/local/bin/claude:ro \
  -v /Users/vitaliiserbyn/.config/claude:/root/.config/claude:ro \
  --network host \
  ci-monitor:local

echo "Monitor started. View logs with: docker logs -f ci-monitor"
echo ""
echo "To add more repositories, update MONITORED_REPOS environment variable"
echo "To stop: docker stop ci-monitor"