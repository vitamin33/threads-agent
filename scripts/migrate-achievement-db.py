#!/usr/bin/env python3
"""Migrate achievement database to add social media columns."""

import os
import sys
import sqlite3

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def migrate_database():
    """Add social media columns to achievements table."""
    db_path = os.path.join(project_root, "test_achievements.db")

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return

    print(f"📊 Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(achievements)")
        columns = [row[1] for row in cursor.fetchall()]

        migrations = []

        if "linkedin_post_id" not in columns:
            migrations.append(
                "ALTER TABLE achievements ADD COLUMN linkedin_post_id VARCHAR(255)"
            )

        if "linkedin_published_at" not in columns:
            migrations.append(
                "ALTER TABLE achievements ADD COLUMN linkedin_published_at DATETIME"
            )

        if "github_gist_id" not in columns:
            migrations.append(
                "ALTER TABLE achievements ADD COLUMN github_gist_id VARCHAR(255)"
            )

        if "blog_post_url" not in columns:
            migrations.append(
                "ALTER TABLE achievements ADD COLUMN blog_post_url VARCHAR(500)"
            )

        if migrations:
            print(f"\n🔧 Running {len(migrations)} migrations...")
            for sql in migrations:
                print(f"   - {sql}")
                cursor.execute(sql)

            conn.commit()
            print("\n✅ Migrations completed successfully!")
        else:
            print("\n✅ Database is already up to date!")

        # Show table structure
        print("\n📋 Current table structure:")
        cursor.execute("PRAGMA table_info(achievements)")
        for row in cursor.fetchall():
            print(f"   {row[1]:30} {row[2]:15}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    print("🚀 Achievement Database Migration\n")
    migrate_database()
