#!/usr/bin/env python3
"""
Manual script to fix the business_value column issue in production.

This script:
1. Checks the current column type
2. Updates it to TEXT if needed
3. Handles existing data gracefully
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def fix_business_value_column():
    """Fix the business_value column to use TEXT type"""

    # Get database URL
    db_url = os.getenv(
        "ACHIEVEMENT_DB_URL",
        "postgresql://postgres.lrhwzmbyqjpxtztkwnmj:5ycyf4j8bTFVaKsg@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
    )

    print("🔧 Fixing business_value column in achievements table")
    print("=" * 60)

    try:
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Check current column type
            result = conn.execute(
                text("""
                SELECT 
                    column_name, 
                    data_type, 
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'achievements' 
                AND column_name = 'business_value'
            """)
            )

            row = result.fetchone()
            if not row:
                print("❌ business_value column not found!")
                return False

            data_type = row[1]
            max_length = row[2]

            print(f"Current column type: {data_type}")
            if max_length:
                print(f"Current max length: {max_length}")

            # If it's already TEXT, we're done
            if data_type.lower() == "text":
                print("✅ Column is already TEXT type - no changes needed")
                return True

            # If it's VARCHAR(255), we need to change it
            if data_type.lower() == "character varying" and max_length == 255:
                print("\n🚀 Converting business_value from VARCHAR(255) to TEXT...")

                # First, let's check if any values would be truncated
                check_result = conn.execute(
                    text("""
                    SELECT COUNT(*) 
                    FROM achievements 
                    WHERE LENGTH(business_value) > 255
                """)
                )
                truncated_count = check_result.scalar()

                if truncated_count > 0:
                    print(f"⚠️  Warning: {truncated_count} values exceed 255 characters")

                # Alter the column type
                conn.execute(
                    text("""
                    ALTER TABLE achievements 
                    ALTER COLUMN business_value TYPE TEXT
                """)
                )

                conn.commit()
                print("✅ Successfully converted business_value to TEXT type")

                # Verify the change
                verify_result = conn.execute(
                    text("""
                    SELECT data_type 
                    FROM information_schema.columns
                    WHERE table_name = 'achievements' 
                    AND column_name = 'business_value'
                """)
                )

                new_type = verify_result.scalar()
                print(f"✅ Verified new column type: {new_type}")

                return True

            else:
                print(
                    f"⚠️  Unexpected column type: {data_type} with max_length: {max_length}"
                )
                return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_large_value_storage():
    """Test storing a large JSON value"""

    db_url = os.getenv(
        "ACHIEVEMENT_DB_URL",
        "postgresql://postgres.lrhwzmbyqjpxtztkwnmj:5ycyf4j8bTFVaKsg@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
    )

    print("\n🧪 Testing large value storage...")

    # Create a test JSON that would exceed 255 characters
    import json

    test_data = {
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
        },
        "source": "saves 8 hours per week for senior developers (4-person team)",
    }

    test_json = json.dumps(test_data)
    print(f"Test JSON length: {len(test_json)} characters")

    try:
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Try to update the first achievement as a test
            result = conn.execute(
                text("""
                UPDATE achievements 
                SET business_value = :test_value
                WHERE id = (SELECT id FROM achievements LIMIT 1)
                RETURNING id, LENGTH(business_value) as value_length
            """),
                {"test_value": test_json},
            )

            row = result.fetchone()
            if row:
                print(
                    f"✅ Successfully stored {row[1]} characters in achievement ID {row[0]}"
                )
                conn.commit()
                return True
            else:
                print("⚠️  No achievements found to test with")
                return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🛠️  Business Value Column Fix Script")
    print("=" * 60)

    # Fix the column
    if fix_business_value_column():
        # Test it
        if test_large_value_storage():
            print(
                "\n🎉 All tests passed! The business_value column is ready for large JSON values."
            )
        else:
            print("\n⚠️  Column fixed but test failed - please investigate")
    else:
        print("\n❌ Failed to fix column - manual intervention may be required")
