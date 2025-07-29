#!/usr/bin/env python3
"""Test Supabase Database Connection - Minimal Dependencies"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Only import what we need
from sqlalchemy import (
    create_engine,
    text,
    Column,
    Integer,
    String,
    DateTime,
    BigInteger,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not set!")
    sys.exit(1)

print("🔍 Testing Supabase Database Connection...")
print(f"📍 Database: {DATABASE_URL.split('@')[1].split('/')[0]}")

try:
    # Create engine
    engine = create_engine(DATABASE_URL)

    # Test basic connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Connected to PostgreSQL: {version}")

    # Create base
    Base = declarative_base()

    # Define Achievement model (simplified)
    class Achievement(Base):
        __tablename__ = "achievements"

        id = Column(BigInteger, primary_key=True)
        title = Column(String(255), nullable=False)
        category = Column(String(50), nullable=False)
        description = Column(String, nullable=True)
        impact_score = Column(Integer, default=50)
        created_at = Column(DateTime, default=datetime.utcnow)

    # Create tables
    print("📊 Creating tables if not exist...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created/verified!")

    # Test insert
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Create test achievement
        test_achievement = Achievement(
            title="Test Achievement from CI",
            category="technical",
            description="Testing Supabase connection",
            impact_score=75,
        )
        session.add(test_achievement)
        session.commit()
        print(f"✅ Test achievement created with ID: {test_achievement.id}")

        # Query it back
        count = session.query(Achievement).count()
        print(f"📈 Total achievements in database: {count}")

        # Clean up test data
        session.delete(test_achievement)
        session.commit()
        print("✅ Test data cleaned up")

    finally:
        session.close()

    print("\n🎉 Supabase connection successful!")
    print("✅ Database is ready for CI/CD achievement tracking!")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)
