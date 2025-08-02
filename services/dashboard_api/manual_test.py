#!/usr/bin/env python3
"""Manual test script for dashboard API."""

import requests
import json
import asyncio
import websockets
import threading
import time
import uvicorn
from main import app


def start_server():
    """Start the dashboard server."""
    uvicorn.run(app, host="127.0.0.1", port=8081, log_level="error")


def test_api_endpoints():
    """Test REST API endpoints."""
    print("🧪 Testing API Endpoints")
    print("-" * 40)

    try:
        # Health check
        response = requests.get("http://127.0.0.1:8081/")
        print(f"✅ Health Check: {response.json()}")

        # Metrics endpoint
        response = requests.get("http://127.0.0.1:8081/api/metrics/ai-jesus")
        data = response.json()
        print(f"✅ Metrics Structure: {list(data.keys())}")
        print(f"   - Active Variants: {len(data['active_variants'])}")
        print(f"   - Early Kills Today: {data['early_kills_today']['kills_today']}")
        print(
            f"   - Optimization Suggestions: {len(data['optimization_opportunities'])}"
        )

        # Active variants endpoint
        response = requests.get("http://127.0.0.1:8081/api/variants/ai-jesus/active")
        print(f"✅ Active Variants: {response.json()}")

        return True
    except Exception as e:
        print(f"❌ API Test Error: {e}")
        return False


async def test_websocket():
    """Test WebSocket connection."""
    print("\n🔌 Testing WebSocket Connection")
    print("-" * 40)

    try:
        uri = "ws://127.0.0.1:8081/dashboard/ws/ai-jesus"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket Connected")

            # Should receive initial data
            initial_data = await asyncio.wait_for(websocket.recv(), timeout=3)
            data = json.loads(initial_data)
            print(f"✅ Initial Data: type={data['type']}")
            print(f"   - Data keys: {list(data['data'].keys())}")

            # Send ping
            await websocket.send('{"type": "ping"}')
            pong = await asyncio.wait_for(websocket.recv(), timeout=1)
            pong_data = json.loads(pong)
            print(f"✅ Ping/Pong: {pong_data}")

            # Send refresh request
            await websocket.send('{"type": "refresh"}')
            refresh_data = await asyncio.wait_for(websocket.recv(), timeout=1)
            refresh_parsed = json.loads(refresh_data)
            print(f"✅ Refresh: type={refresh_parsed['type']}")

        return True
    except Exception as e:
        print(f"❌ WebSocket Test Error: {e}")
        return False


def main():
    """Run manual tests."""
    print("🚀 CRA-234 Dashboard Manual Test")
    print("=" * 50)

    # Start server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    print("⏳ Starting server...")
    time.sleep(3)  # Wait for server to start

    # Test API endpoints
    api_success = test_api_endpoints()

    # Test WebSocket
    ws_success = asyncio.run(test_websocket())

    # Summary
    print("\n📊 Test Summary")
    print("-" * 40)
    print(f"API Endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"WebSocket: {'✅ PASS' if ws_success else '❌ FAIL'}")

    if api_success and ws_success:
        print("\n🎉 All manual tests PASSED!")
        print("Dashboard is ready for production deployment!")
    else:
        print("\n⚠️ Some tests failed - check implementation")


if __name__ == "__main__":
    main()
