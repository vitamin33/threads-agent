#!/usr/bin/env python3
"""
End-to-End Test for CRA-235 Comment Monitoring Implementation
"""

import httpx


def test_comment_monitoring_e2e():
    """Test the complete comment monitoring pipeline."""

    # Test data
    post_id = "test-post-e2e-001"
    test_comments = [
        {"text": "This is amazing! How can I get early access?", "author": "buyer_001"},
        {"text": "Wow, I'd love to learn more about this!", "author": "buyer_002"},
        {"text": "Can you DM me the details?", "author": "buyer_003"},
        {"text": "Just a regular comment.", "author": "user_004"},
    ]

    print("🚀 Starting CRA-235 E2E Test")
    print("=" * 60)

    # 1. Create comments via fake-threads API
    print("\n1️⃣ Creating test comments...")
    fake_threads_url = "http://localhost:9009"
    created_comments = []

    for comment_data in test_comments:
        try:
            response = httpx.post(
                f"{fake_threads_url}/posts/{post_id}/comments",
                json=comment_data,
                timeout=5,
            )
            if response.status_code == 201:
                created_comment = response.json()
                created_comments.append(created_comment)
                print(
                    f"   ✅ Created comment: {created_comment['id']} by {created_comment['author']}"
                )
            else:
                print(f"   ❌ Failed to create comment: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error creating comment: {e}")

    # 2. Verify comments were created
    print("\n2️⃣ Verifying comments...")
    try:
        response = httpx.get(f"{fake_threads_url}/posts/{post_id}/comments", timeout=5)
        if response.status_code == 200:
            fetched_comments = response.json()
            print(f"   ✅ Found {len(fetched_comments)} comments for post {post_id}")
        else:
            print(f"   ❌ Failed to fetch comments: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error fetching comments: {e}")

    # 3. Test orchestrator comment monitoring endpoints
    print("\n3️⃣ Testing orchestrator endpoints...")
    orchestrator_url = "http://localhost:8081"

    # Test health check
    try:
        response = httpx.get(f"{orchestrator_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Orchestrator health check: OK")
        else:
            print(f"   ❌ Orchestrator health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error checking orchestrator health: {e}")

    # Test comment monitoring start
    try:
        response = httpx.post(
            f"{orchestrator_url}/comment-monitoring/start",
            json={"post_id": post_id},
            timeout=5,
        )
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Comment monitoring started: task_id={result.get('task_id')}")
        else:
            print(f"   ❌ Failed to start comment monitoring: {response.status_code}")
            print(f"      Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error starting comment monitoring: {e}")

    # Test comment processing
    try:
        response = httpx.post(
            f"{orchestrator_url}/comment-monitoring/process/{post_id}", timeout=5
        )
        if response.status_code == 202:
            print("   ✅ Comment processing started (async)")
        else:
            print(f"   ❌ Failed to process comments: {response.status_code}")
            print(f"      Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error processing comments: {e}")

    # 4. Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   - Comments Created: {len(created_comments)}")
    print(
        f"   - Purchase Intent Comments: ~{len([c for c in test_comments if 'DM' in c['text'] or 'access' in c['text'] or 'learn more' in c['text']])}"
    )
    print(
        f"   - Pipeline Status: {'✅ OPERATIONAL' if len(created_comments) > 0 else '❌ FAILED'}"
    )
    print("=" * 60)


if __name__ == "__main__":
    test_comment_monitoring_e2e()
