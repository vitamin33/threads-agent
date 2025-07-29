#!/usr/bin/env python3
"""Setup Achievement Database for CI/CD usage"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from services.achievement_collector.db.models import Base
from services.achievement_collector.db.config import DATABASE_URL


def setup_database():
    """Create all tables in PostgreSQL"""
    print("🔧 Setting up database...")
    print(
        f"📍 Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}"
    )

    # Create engine
    engine = create_engine(DATABASE_URL)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")

    # Verify tables
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        )

        tables = [row[0] for row in result]
        print(f"📊 Created tables: {', '.join(tables)}")

        # Check achievements table structure
        result = conn.execute(
            text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'achievements'
            ORDER BY ordinal_position
        """)
        )

        print("\n📋 Achievements table structure:")
        for col_name, data_type in result:
            print(f"   - {col_name}: {data_type}")


if __name__ == "__main__":
    setup_database()
