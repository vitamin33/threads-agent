"""Multi-Platform Publishing Engine for Threads Agent.

This package provides the core publishing infrastructure for distributing content
across multiple platforms including Dev.to, LinkedIn, Twitter, Threads, and Medium.

Key Components:
- PublishingEngine: Main orchestrator for multi-platform publishing
- PlatformAdapter: Base interface for platform-specific implementations
- Celery tasks: Async processing and retry mechanisms
- Rate limiting and error handling
"""

__version__ = "1.0.0"
