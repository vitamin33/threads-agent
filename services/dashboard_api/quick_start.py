#!/usr/bin/env python3
"""
Quick start script for the dashboard API.
This will check everything and start the server with clear instructions.
"""

import os
import sys
import subprocess


def check_environment():
    """Check if we're in the right environment."""
    print("🔍 Checking environment...")

    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Not in dashboard_api directory!")
        print("   Run: cd services/dashboard_api")
        return False

    # Check if virtual environment is activated
    if not os.environ.get("VIRTUAL_ENV"):
        print("❌ Virtual environment not activated!")
        print("   Run: source ../../venv/bin/activate")
        return False

    # Check if dependencies are available
    try:
        import uvicorn  # noqa: F401
        import fastapi  # noqa: F401

        print("✅ Dependencies OK")
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("   Run: pip install fastapi uvicorn")
        return False

    print("✅ Environment ready!")
    return True


def start_server():
    """Start the dashboard server."""
    print("\n🚀 Starting Dashboard API Server...")
    print("=" * 50)
    print("Server will be available at:")
    print("  📍 http://localhost:8081/")
    print("  📊 http://localhost:8081/api/metrics/ai-jesus")
    print("  🔌 ws://localhost:8081/dashboard/ws/ai-jesus")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Start the server
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8081",
                "--reload",
            ]
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return False

    return True


def main():
    """Main function."""
    print("🎯 CRA-234 Dashboard Quick Start")
    print("=" * 40)

    # Check environment
    if not check_environment():
        print("\n💡 Fix the issues above and try again")
        sys.exit(1)

    # Start server
    start_server()


if __name__ == "__main__":
    main()
