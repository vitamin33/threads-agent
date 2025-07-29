#!/usr/bin/env python3
"""Test Achievement Database Connection"""

import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.achievement_collector.db.config import get_db, engine, DATABASE_URL
from services.achievement_collector.db.models import Base, Achievement
from services.achievement_collector.api.schemas import AchievementCreate
from services.achievement_collector.api.routes.achievements import (
    create_achievement_sync,
)


async def test_database_connection():
    """Test database connection and basic operations"""
    print("🔍 Testing Achievement Database Connection...")
    print(
        f"📍 Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}"
    )

    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
            print("✅ Database connection successful!")

        # Create tables if not exist
        Base.metadata.create_all(bind=engine)
        print("✅ Database schema ready!")

        # Test creating an achievement
        db = next(get_db())
        try:
            test_achievement = AchievementCreate(
                title="Test CI/CD Achievement",
                category="technical",
                description="Testing database connection from CI workflow",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                source_type="test",
                source_id=f"test-{datetime.now().timestamp()}",
                tags=["test", "ci-cd"],
                skills_demonstrated=["PostgreSQL", "CI/CD", "Testing"],
                metrics_after={"test": True},
                impact_score=50,
                complexity_score=3,
                portfolio_ready=False,
            )

            achievement = create_achievement_sync(db, test_achievement)
            print(f"✅ Test achievement created: ID={achievement.id}")

            # Query it back
            retrieved = db.query(Achievement).filter_by(id=achievement.id).first()
            print(f"✅ Achievement retrieved: {retrieved.title}")

            # Clean up test data
            db.delete(retrieved)
            db.commit()
            print("✅ Test data cleaned up")

        finally:
            db.close()

        print("\n🎉 All tests passed! Database is ready for CI/CD usage.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Make sure to:")
        print("   1. Set DATABASE_URL environment variable")
        print("   2. Or create .env file with DATABASE_URL=postgresql://...")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_database_connection())
