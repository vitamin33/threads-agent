#!/usr/bin/env python3
"""
Apply the business_value field expansion migration to the database.

This script can be run locally or in CI/CD to ensure the database schema is updated
before the achievement tracker runs.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text


def check_and_apply_migration():
    """Check if migration is needed and apply it"""
    
    # Get database URL
    db_url = os.getenv(
        'DATABASE_URL',
        os.getenv(
            'ACHIEVEMENT_DB_URL',
            'postgresql://postgres.lrhwzmbyqjpxtztkwnmj:5ycyf4j8bTFVaKsg@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
        )
    )
    
    print("🔧 Checking business_value field migration status...")
    
    try:
        # Create engine
        engine = create_engine(db_url)
        
        # Check current column type
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'achievements' 
                AND column_name = 'business_value'
            """))
            
            row = result.fetchone()
            if row:
                data_type = row[1]
                max_length = row[2]
                
                print(f"Current business_value field: {data_type}")
                if max_length:
                    print(f"  Max length: {max_length}")
                
                if data_type == 'character varying' and max_length == 255:
                    print("❌ Field needs migration to TEXT type")
                    
                    # Run alembic migration
                    alembic_cfg = Config("alembic.ini")
                    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
                    
                    # Set script location
                    alembic_cfg.set_main_option(
                        "script_location", 
                        str(Path(__file__).parent.parent / "db" / "alembic")
                    )
                    
                    print("🚀 Running migration...")
                    command.upgrade(alembic_cfg, "003_expand_business_value")
                    
                    print("✅ Migration completed successfully!")
                    
                elif data_type == 'text':
                    print("✅ Field already migrated to TEXT type")
                else:
                    print(f"⚠️  Unexpected field type: {data_type}")
            else:
                print("❌ achievements table or business_value column not found")
                
    except Exception as e:
        print(f"❌ Error during migration check: {e}")
        return False
    
    return True


def verify_migration():
    """Verify the migration was successful"""
    
    db_url = os.getenv(
        'DATABASE_URL',
        os.getenv(
            'ACHIEVEMENT_DB_URL',
            'postgresql://postgres.lrhwzmbyqjpxtztkwnmj:5ycyf4j8bTFVaKsg@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
        )
    )
    
    try:
        engine = create_engine(db_url)
        
        # Test storing a large JSON value
        test_json = {
            "total_value": 208000,
            "currency": "USD",
            "period": "yearly",
            "type": "time_savings",
            "confidence": 0.7,
            "method": "time_calculation",
            "breakdown": {
                "hours_saved_annually": 1664.0,
                "hourly_rate": 125.0,
                "role_assumed": "senior",
                "team_multiplier": 4,
                "base_hours_per_person": 416.0,
                "additional_notes": "This is a test of storing large JSON values in the business_value field"
            },
            "source": "saves 8 hours per week for senior developers (4-person team)"
        }
        
        import json
        test_value = json.dumps(test_json)
        
        print(f"\n📏 Testing with JSON length: {len(test_value)} characters")
        
        with engine.connect() as conn:
            # Try to update a test record (or insert if needed)
            conn.execute(text("""
                UPDATE achievements 
                SET business_value = :test_value
                WHERE id = (SELECT id FROM achievements LIMIT 1)
            """), {"test_value": test_value})
            
            conn.commit()
            
        print("✅ Successfully stored large JSON value!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    print("🎯 Business Value Field Migration Script")
    print("=" * 50)
    
    # Check and apply migration
    if check_and_apply_migration():
        print("\n🔍 Verifying migration...")
        if verify_migration():
            print("\n🎉 Migration successful! The business_value field can now store large JSON objects.")
        else:
            print("\n⚠️  Migration applied but verification failed")
            sys.exit(1)
    else:
        print("\n❌ Migration failed")
        sys.exit(1)