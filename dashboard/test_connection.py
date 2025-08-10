#!/usr/bin/env python3
"""Test dashboard connections"""

import requests

print("Testing Dashboard Connections...")
print("=" * 50)

# Test Achievement Collector
try:
    response = requests.get("http://localhost:8000/achievements/", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Achievement Collector: Connected ({data['total']} achievements)")
    else:
        print(f"❌ Achievement Collector: HTTP {response.status_code}")
except Exception as e:
    print(f"❌ Achievement Collector: {e}")

# Test Orchestrator
try:
    response = requests.get("http://localhost:8080/health", timeout=5)
    if response.status_code == 200:
        print("✅ Orchestrator: Connected")
    else:
        print(f"❌ Orchestrator: HTTP {response.status_code}")
except Exception as e:
    print(f"❌ Orchestrator: {e}")

# Test Dashboard
try:
    response = requests.get("http://localhost:8501", timeout=5)
    if response.status_code == 200:
        print("✅ Dashboard: Running")
        if "Connection refused" in response.text:
            print("  ⚠️  But showing connection errors")
        else:
            print("  ✅ No connection errors detected")
    else:
        print(f"❌ Dashboard: HTTP {response.status_code}")
except Exception as e:
    print(f"❌ Dashboard: {e}")

print("=" * 50)
