#!/bin/bash
# Start the CI Monitor Service for all teammate repositories

echo "🤖 Starting CI Monitor Service..."
echo "Monitoring repositories:"
echo "  - Main workspace: threads-agent"
echo "  - Jordan Kim's workspace"
echo "  - Riley Morgan's workspace"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Ensure we're in the right directory
cd /Users/vitaliiserbyn/development/threads-agent

# Run the monitor
python3 services/ci-monitor/run_monitor_host.py