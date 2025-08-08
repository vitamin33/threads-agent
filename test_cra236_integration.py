#!/usr/bin/env python3
"""
CRA-236 Integration Test
Tests the conversation engine deployed on local k3d cluster
"""

import requests
import sys
import subprocess
import time
from datetime import datetime


def port_forward_service():
    """Start port forwarding for conversation-engine service"""
    try:
        # Start port forwarding in background
        proc = subprocess.Popen(
            ["kubectl", "port-forward", "svc/conversation-engine", "8082:8080"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give it time to establish connection
        time.sleep(2)
        return proc
    except Exception as e:
        print(f"Failed to start port forwarding: {e}")
        return None


def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8082/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "conversation_engine"
        print("✅ Health endpoint test passed")
        return True
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False


def test_conversation_creation():
    """Test conversation creation"""
    try:
        payload = {
            "user_id": "test_user_integration_123",
            "initial_message": "Hi, I'm interested in your AI automation services",
        }

        response = requests.post(
            "http://localhost:8082/conversations", json=payload, timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert data["state"] == "initial_contact"

        print(f"✅ Conversation creation test passed - ID: {data['conversation_id']}")
        return data["conversation_id"]
    except Exception as e:
        print(f"❌ Conversation creation test failed: {e}")
        return None


def test_conversation_transition(conversation_id):
    """Test conversation state transition"""
    try:
        payload = {
            "user_message": "I want to know more about pricing and implementation timeline",
            "user_name": "John Doe",
        }

        response = requests.post(
            f"http://localhost:8082/conversations/{conversation_id}/transition",
            json=payload,
            timeout=15,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conversation_id
        assert data["previous_state"] == "initial_contact"
        assert data["state"] in ["interest_qualification", "value_proposition"]

        print(f"✅ Conversation transition test passed - State: {data['state']}")
        return True
    except Exception as e:
        print(f"❌ Conversation transition test failed: {e}")
        return False


def test_conversation_retrieval(conversation_id):
    """Test conversation retrieval"""
    try:
        response = requests.get(
            f"http://localhost:8082/conversations/{conversation_id}", timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conversation_id
        assert "current_state" in data
        assert "user_id" in data
        assert "conversation_turns" in data

        print(
            f"✅ Conversation retrieval test passed - Turns: {len(data['conversation_turns'])}"
        )
        return True
    except Exception as e:
        print(f"❌ Conversation retrieval test failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("🚀 Starting CRA-236 Conversation Engine Integration Tests")
    print(f"📅 Test started at: {datetime.now().isoformat()}")
    print()

    # Start port forwarding
    print("🔧 Setting up port forwarding...")
    port_forward_proc = port_forward_service()
    if not port_forward_proc:
        print("❌ Failed to setup port forwarding")
        sys.exit(1)

    try:
        # Run tests
        tests_passed = 0
        total_tests = 4

        # Test 1: Health check
        if test_health_endpoint():
            tests_passed += 1

        # Test 2: Conversation creation
        conversation_id = test_conversation_creation()
        if conversation_id:
            tests_passed += 1

            # Test 3: Conversation transition
            if test_conversation_transition(conversation_id):
                tests_passed += 1

            # Test 4: Conversation retrieval
            if test_conversation_retrieval(conversation_id):
                tests_passed += 1

        print()
        print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")

        if tests_passed == total_tests:
            print("🎉 All CRA-236 integration tests passed!")
            print("✅ Conversation Engine is working correctly on k3d cluster")
            return 0
        else:
            print("❌ Some tests failed")
            return 1

    finally:
        # Cleanup port forwarding
        if port_forward_proc:
            port_forward_proc.terminate()
            port_forward_proc.wait()
            print("🧹 Cleaned up port forwarding")


if __name__ == "__main__":
    sys.exit(main())
