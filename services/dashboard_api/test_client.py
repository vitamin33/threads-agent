#!/usr/bin/env python3
"""Simple test client to verify dashboard API is working."""

import requests
import json
import time
import sys

def test_dashboard_api():
    """Test the dashboard API endpoints."""
    base_url = "http://localhost:8081"
    
    print("🧪 Testing Dashboard API")
    print("=" * 40)
    
    # Test health endpoint
    try:
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Health check: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection refused - server not running?")
        print("   💡 Start server with: ./start_dashboard.sh")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test metrics endpoint
    try:
        print("2. Testing metrics endpoint...")
        response = requests.get(f"{base_url}/api/metrics/ai-jesus", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Metrics received:")
            print(f"      - Active variants: {len(data['active_variants'])}")
            print(f"      - Early kills today: {data['early_kills_today']['kills_today']}")
            print(f"      - Optimization suggestions: {len(data['optimization_opportunities'])}")
        else:
            print(f"   ❌ Metrics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test active variants endpoint
    try:
        print("3. Testing active variants endpoint...")
        response = requests.get(f"{base_url}/api/variants/ai-jesus/active", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Active variants: {len(data['variants'])} variants")
        else:
            print(f"   ❌ Active variants failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print("\n🎉 All API tests passed!")
    print("Dashboard is working correctly!")
    return True

def main():
    """Run the test client."""
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        print("⏳ Waiting for server to start...")
        time.sleep(3)
    
    success = test_dashboard_api()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()