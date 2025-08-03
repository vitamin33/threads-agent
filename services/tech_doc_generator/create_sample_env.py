#!/usr/bin/env python3
"""
Create a sample .env file for the tech doc generator
"""

import os


def create_sample_env():
    """Create a sample .env file with instructions"""

    env_content = """# Tech Doc Generator Environment Variables
# Copy this to .env and fill in your actual keys

# Required for content generation
OPENAI_API_KEY=your_openai_api_key_here

# Platform API Keys (add as you set them up)

# Dev.to - Easiest to set up (2 minutes)
# Get from: https://dev.to/settings/extensions
DEVTO_API_KEY=

# LinkedIn - Medium difficulty (10 minutes)
# Requires OAuth setup at https://www.linkedin.com/developers/
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_AUTHOR_ID=

# Threads (Meta) - Easy to set up (5 minutes)
# Requires Instagram Professional account
# Get from: https://developers.facebook.com/
THREADS_ACCESS_TOKEN=
THREADS_USER_ID=
THREADS_USERNAME=your_threads_username

# Twitter/X - Hardest (1-2 days for approval)
# Apply at: https://developer.twitter.com/
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_BEARER_TOKEN=

# Optional: GitHub for gists
GITHUB_TOKEN=

# Optional: Medium (requires approval)
MEDIUM_ACCESS_TOKEN=

# Database (optional, uses SQLite by default)
DATABASE_URL=sqlite:///./tech_doc_generator.db

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# Service Configuration
ANALYSIS_DEPTH=medium  # shallow, medium, deep
MAX_ARTICLE_LENGTH=5000
MIN_INSIGHT_SCORE=7.0
DEFAULT_PUBLISH_DELAY_HOURS=2
MAX_DAILY_ARTICLES=3
"""

    # Check if .env already exists
    if os.path.exists(".env"):
        print("⚠️  .env file already exists!")
        response = input("Overwrite? (y/n): ")
        if response.lower() != "y":
            print("Keeping existing .env file.")
            return

    # Write the sample env file
    with open(".env.sample", "w") as f:
        f.write(env_content)

    print("✅ Created .env.sample file")
    print("\nNext steps:")
    print("1. Copy .env.sample to .env")
    print("2. Add your API keys")
    print("3. Start with OPENAI_API_KEY and DEVTO_API_KEY")
    print("\n💡 Tip: You can test without publishing by using mock mode!")


if __name__ == "__main__":
    create_sample_env()
