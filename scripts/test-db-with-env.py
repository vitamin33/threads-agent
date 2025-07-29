#!/usr/bin/env python3
"""Test Database Connection with .env file"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import (
    create_engine,
    text,
)

# Load .env file
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("ACHIEVEMENT_DB_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set in .env file!")
    sys.exit(1)

print("🔍 Testing Database Connection...")
print("📍 Database URL found in .env")

# Try different connection approaches
urls_to_try = [
    DATABASE_URL,
    # Try with pooler format
    DATABASE_URL.replace("@db.", "@postgres.").replace(
        ".supabase.co:5432", "@aws-0-us-west-1.pooler.supabase.com:5432"
    ),
    # Try with direct connection on port 6543
    DATABASE_URL.replace(":5432", ":6543"),
]

for i, url in enumerate(urls_to_try, 1):
    print(f"\n🔄 Attempt {i}/3...")
    try:
        # Create engine
        engine = create_engine(url)

        # Test basic connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Connection successful!")

            # Get PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"📊 PostgreSQL: {version.split(',')[0]}")
            break
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}...")
        if i == len(urls_to_try):
            print(
                "\n💡 Please check your Supabase dashboard for the correct connection string."
            )
            print("   Go to: Settings → Database → Connection String")
            sys.exit(1)
