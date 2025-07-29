"""Auto-tracking service that monitors git commits and Linear issues."""

import asyncio
import os
import signal
import sys

from .github_pr_tracker import GitHubPRTracker
from .linear_tracker import LinearTracker
from ..core.logging import setup_logging

logger = setup_logging(__name__)


class AutoTracker:
    """Main service that coordinates all achievement auto-tracking."""

    def __init__(self):
        self.github_tracker = GitHubPRTracker()
        self.linear_tracker = LinearTracker()
        self.running = True

    async def start(self):
        """Start all tracking services."""
        logger.info("🚀 Starting Achievement Auto-Tracker...")

        # Create tasks for each tracker
        tasks = []

        # GitHub PR tracker
        if os.getenv("ENABLE_GITHUB_TRACKING", "true").lower() == "true":
            logger.info("✅ GitHub PR tracking enabled")
            tasks.append(asyncio.create_task(self.github_tracker.track_continuously()))
        else:
            logger.info("❌ GitHub PR tracking disabled")

        # Linear tracker
        if os.getenv("LINEAR_API_KEY"):
            logger.info("✅ Linear issue tracking enabled")
            tasks.append(
                asyncio.create_task(self.linear_tracker.track_linear_updates())
            )
        else:
            logger.info("❌ Linear tracking disabled (no API key)")

        # Future: MLflow tracker will be added here when E4.5 is implemented
        # if os.getenv("MLFLOW_TRACKING_URI"):
        #     logger.info("✅ MLflow tracking enabled")
        #     tasks.append(asyncio.create_task(self.mlflow_tracker.track_experiments()))

        if not tasks:
            logger.warning("⚠️  No tracking services enabled!")
            return

        # Run all trackers concurrently
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("🛑 Tracking services stopped")
        except Exception as e:
            logger.error(f"❌ Error in tracking services: {e}")
            raise

    def stop(self):
        """Stop all tracking services."""
        logger.info("🛑 Stopping Achievement Auto-Tracker...")
        self.running = False


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    """Main entry point for the auto-tracker service."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Create and start tracker
    tracker = AutoTracker()

    try:
        await tracker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        tracker.stop()


if __name__ == "__main__":
    # Run the auto-tracker
    asyncio.run(main())
