#!/usr/bin/env python3
"""
Test script to verify Dev.to API posting with real credentials
"""

import asyncio
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DEVTO_API_KEY = os.getenv("DEVTO_API_KEY")


async def test_devto_api():
    """Test Dev.to API with a simple test post"""

    if not DEVTO_API_KEY:
        print("❌ DEVTO_API_KEY not found in environment variables")
        return False

    print(f"✅ Found Dev.to API key: {DEVTO_API_KEY[:10]}...")

    # Test article content
    test_article = {
        "article": {
            "title": f"Test Post - AI/MLOps Achievement Showcase {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "body_markdown": """# Testing Dev.to API Integration

This is a test post to verify our API integration is working correctly.

## Key Features Being Tested:
- API Authentication ✅
- Article Creation 📝
- Markdown Formatting 🎨
- Tag Support 🏷️

### Code Example
```python
def hello_devto():
    return "Hello from threads-agent!"
```

## Achievement Collector Integration
Our achievement collector service tracks:
- GitHub PR metrics
- Linear task completion
- Code quality improvements
- Business value delivered

---

*This is an automated test post that will be deleted shortly.*
""",
            "published": False,  # Keep as draft for safety
            "tags": ["test", "api", "automation"],
            "description": "Testing Dev.to API integration for threads-agent project",
        }
    }

    headers = {"api-key": DEVTO_API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            print("\n📤 Sending test article to Dev.to...")
            response = await client.post(
                "https://dev.to/api/articles", json=test_article, headers=headers
            )

            if response.status_code == 201:
                result = response.json()
                print(f"\n✅ SUCCESS! Article created as draft")
                print(f"📝 Article ID: {result.get('id')}")
                print(f"🔗 URL: {result.get('url')}")
                print(f"📅 Created at: {result.get('created_at')}")
                print(f"🏷️  Tags: {result.get('tag_list')}")

                # Get user info
                user_response = await client.get(
                    "https://dev.to/api/users/me", headers={"api-key": DEVTO_API_KEY}
                )

                if user_response.status_code == 200:
                    user = user_response.json()
                    print(
                        f"\n👤 Authenticated as: {user.get('name')} (@{user.get('username')})"
                    )
                    print(f"📧 Email: {user.get('email')}")

                return True

            else:
                print(f"\n❌ Failed to create article")
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return False


async def test_fetch_articles():
    """Test fetching existing articles"""

    headers = {"api-key": DEVTO_API_KEY}

    async with httpx.AsyncClient() as client:
        try:
            print("\n📥 Fetching your articles...")
            response = await client.get(
                "https://dev.to/api/articles/me/all", headers=headers
            )

            if response.status_code == 200:
                articles = response.json()
                print(f"\n📚 Found {len(articles)} articles")

                for i, article in enumerate(articles[:5]):  # Show first 5
                    print(f"\n{i + 1}. {article.get('title')}")
                    print(f"   📅 {article.get('published_at') or 'Draft'}")
                    print(f"   ❤️  {article.get('positive_reactions_count')} reactions")
                    print(f"   💬 {article.get('comments_count')} comments")
                    print(f"   🔗 {article.get('url')}")

                return True
            else:
                print(f"❌ Failed to fetch articles: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error fetching articles: {str(e)}")
            return False


async def main():
    """Run all tests"""
    print("🚀 Testing Dev.to API Integration\n")

    # Test creating article
    create_success = await test_devto_api()

    # Test fetching articles
    fetch_success = await test_fetch_articles()

    if create_success and fetch_success:
        print("\n✅ All tests passed! Dev.to integration is working correctly.")
        print("\n📌 Next steps:")
        print("1. The test article was created as a DRAFT")
        print("2. You can publish it manually from Dev.to dashboard")
        print("3. Or delete it if it was just for testing")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
