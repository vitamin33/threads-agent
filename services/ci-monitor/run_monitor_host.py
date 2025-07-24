#!/usr/bin/env python3
"""
Host-based CI Monitor Service
Runs directly on host to access Claude CLI
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitor_v3 import MultiRepoMonitor

if __name__ == "__main__":
    # Set up environment if not already set
    if not os.getenv("GITHUB_TOKEN"):
        os.environ["GITHUB_TOKEN"] = "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"

    # Run the monitor
    monitor = MultiRepoMonitor()
    monitor.monitor_loop()
