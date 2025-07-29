#!/usr/bin/env python3
"""Debug Supabase Connection URL"""

import re

print("🔍 Supabase URL Debugger")
print("=" * 50)
print("\nPlease check your Supabase dashboard:")
print("1. Go to Settings → Database")
print("2. Look for 'Connection string' section")
print("3. You should see multiple options:\n")
print("   - URI")
print("   - PSQL")
print("   - .NET")
print("   - JDBC")
print("   - Python")
print("   - etc.\n")

url = input("Paste the URI (first option) here: ").strip()

if url:
    print(f"\n📋 Analyzing URL: {url[:50]}...")

    # Extract project reference
    match = re.search(r"@db\.([a-z]+)\.supabase\.co", url)
    if match:
        project_ref = match.group(1)
        print(f"✅ Project Reference: {project_ref}")
        print("✅ URL format looks correct!")

        # Check if it's the pooler format
        if "pooler.supabase.com" in url:
            print("📌 Using pooler connection")
        else:
            print("📌 Using direct connection")

        print("\n🔧 Next steps:")
        print("1. Update .env file with this URL")
        print("2. Update GitHub secret ACHIEVEMENT_DB_URL")
        print("3. Make sure password is correct")
    else:
        print("❌ Could not extract project reference")
        print("\n💡 URL should look like:")
        print(
            "   postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres"
        )
else:
    print("\n❌ No URL provided")
