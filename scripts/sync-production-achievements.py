#!/usr/bin/env python3
"""
Sync Production Achievement Data to Local Cluster

This script safely syncs your Supabase achievement data to the local k3d cluster
for testing portfolio API integration without affecting production.
"""

import os
import sys
import subprocess

# Production Supabase connection
PROD_DB_URL = "postgresql://postgres.lrhwzmbyqjpxtztkwnmj:5ycyf4j8bTFVaKsg@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"


def export_production_achievements():
    """Export achievements from production Supabase database."""
    try:
        print("📥 Exporting achievements from production Supabase...")

        # Export achievements data
        export_cmd = [
            "psql",
            PROD_DB_URL,
            "-c",
            """
            COPY (
                SELECT id, title, description, category, started_at, completed_at,
                       duration_hours, impact_score, complexity_score, business_value,
                       time_saved_hours, performance_improvement_pct, source_type,
                       source_id, source_url, evidence, metrics_before, metrics_after,
                       tags, skills_demonstrated, ai_summary, ai_impact_analysis,
                       ai_technical_analysis, portfolio_ready, portfolio_section,
                       display_priority, linkedin_post_id, linkedin_published_at,
                       github_gist_id, blog_post_url, metadata, created_at, updated_at
                FROM achievements
                WHERE portfolio_ready = true
                ORDER BY impact_score DESC
            ) TO STDOUT WITH CSV HEADER;
            """,
        ]

        result = subprocess.run(export_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Export failed: {result.stderr}")
            return None

        print(f"✅ Exported {len(result.stdout.split())} lines of achievement data")
        return result.stdout

    except Exception as e:
        print(f"❌ Error exporting achievements: {e}")
        return None


def import_to_local_cluster(csv_data):
    """Import achievement data to local k3d cluster."""
    try:
        print("📤 Importing achievements to local k3d cluster...")

        # Save CSV data to temporary file
        with open("/tmp/achievements_export.csv", "w") as f:
            f.write(csv_data)

        # Copy CSV file to postgres pod
        copy_cmd = [
            "kubectl",
            "cp",
            "/tmp/achievements_export.csv",
            "postgres-0:/tmp/achievements_import.csv",
        ]

        subprocess.run(copy_cmd, check=True)

        # Import data to local database
        import_cmd = [
            "kubectl",
            "exec",
            "postgres-0",
            "--",
            "psql",
            "-U",
            "postgres",
            "-d",
            "threads_agent",
            "-c",
            """
            -- Clear existing achievement data
            TRUNCATE TABLE achievements RESTART IDENTITY CASCADE;
            
            -- Import production data
            COPY achievements (
                id, title, description, category, started_at, completed_at,
                duration_hours, impact_score, complexity_score, business_value,
                time_saved_hours, performance_improvement_pct, source_type,
                source_id, source_url, evidence, metrics_before, metrics_after,
                tags, skills_demonstrated, ai_summary, ai_impact_analysis,
                ai_technical_analysis, portfolio_ready, portfolio_section,
                display_priority, linkedin_post_id, linkedin_published_at,
                github_gist_id, blog_post_url, metadata, created_at, updated_at
            ) FROM '/tmp/achievements_import.csv' WITH CSV HEADER;
            
            -- Update sequence
            SELECT setval('achievements_id_seq', (SELECT MAX(id) FROM achievements));
            """,
        ]

        result = subprocess.run(import_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Import failed: {result.stderr}")
            return False

        print("✅ Successfully imported achievements to local cluster")

        # Cleanup
        os.remove("/tmp/achievements_export.csv")

        return True

    except Exception as e:
        print(f"❌ Error importing to local cluster: {e}")
        return False


def validate_sync():
    """Validate that the sync was successful."""
    try:
        print("🔍 Validating sync...")

        # Check local database
        check_cmd = [
            "kubectl",
            "exec",
            "postgres-0",
            "--",
            "psql",
            "-U",
            "postgres",
            "-d",
            "threads_agent",
            "-c",
            """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN portfolio_ready = true THEN 1 END) as ready,
                AVG(impact_score) as avg_impact
            FROM achievements;
            """,
        ]

        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Local database validation:")
            print(result.stdout)
            return True
        else:
            print(f"❌ Validation failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error validating sync: {e}")
        return False


if __name__ == "__main__":
    print("🔄 Production to Local Achievement Data Sync")
    print("=" * 50)

    # Step 1: Export from production
    csv_data = export_production_achievements()
    if not csv_data:
        print("❌ Failed to export production data")
        sys.exit(1)

    # Step 2: Import to local
    success = import_to_local_cluster(csv_data)
    if not success:
        print("❌ Failed to import to local cluster")
        sys.exit(1)

    # Step 3: Validate
    if validate_sync():
        print("\n🎉 Achievement data sync completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Test portfolio API with real achievement data")
        print("2. Validate all endpoints work correctly")
        print("3. Copy frontend to temp_frontend/ for analysis")
        print("4. Design production deployment strategy")
    else:
        print("❌ Sync validation failed")
        sys.exit(1)
