#!/usr/bin/env python3
"""
Verify Prompt Engineering Platform is working with real data
"""

import httpx
import sys


def check_service(url, name):
    """Check if a service is responding"""
    try:
        response = httpx.get(f"{url}/health", timeout=5.0)
        if response.status_code == 200:
            print(f"✅ {name} is healthy at {url}")
            return True
        else:
            print(f"❌ {name} returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name} is not responding: {e}")
        return False


def check_endpoints():
    """Check all required endpoints"""
    base_url = "http://localhost:8085"
    orchestrator_url = "http://localhost:8080"

    endpoints = [
        (f"{base_url}/api/v1/templates", "Templates API"),
        (f"{base_url}/api/v1/experiments", "A/B Testing API"),
        (f"{orchestrator_url}/metrics", "Orchestrator Metrics"),
    ]

    all_good = True
    for url, name in endpoints:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.text
                if len(data) > 100:
                    data = data[:100] + "..."
                print(f"✅ {name}: {data}")
            else:
                print(f"❌ {name}: Status {response.status_code}")
                all_good = False
        except Exception as e:
            print(f"❌ {name}: {e}")
            all_good = False

    return all_good


def verify_dashboard_data():
    """Verify dashboard can fetch real data"""
    print("\n📊 Verifying Dashboard Data Sources:")

    # Check templates
    try:
        response = httpx.get("http://localhost:8085/api/v1/templates")
        if response.status_code == 200:
            data = response.json()
            template_count = len(data.get("templates", []))
            print(f"✅ Found {template_count} templates")
            if template_count > 0:
                print(
                    f"   First template: {data['templates'][0].get('name', 'Unknown')}"
                )
        else:
            print(f"❌ Templates API error: {response.status_code}")
    except Exception as e:
        print(f"❌ Templates API error: {e}")

    # Check experiments
    try:
        response = httpx.get("http://localhost:8085/api/v1/experiments")
        if response.status_code == 200:
            data = response.json()
            exp_count = len(data.get("experiments", []))
            print(f"✅ Found {exp_count} experiments")
            if exp_count > 0:
                print(
                    f"   First experiment: {data['experiments'][0].get('name', 'Unknown')}"
                )
        else:
            print(f"❌ Experiments API error: {response.status_code}")
    except Exception as e:
        print(f"❌ Experiments API error: {e}")

    # Check metrics
    try:
        response = httpx.get("http://localhost:8080/metrics")
        if response.status_code == 200:
            print("✅ Metrics endpoint responding")
            # Parse some metrics
            metrics_text = response.text
            if "prompt_executions_total" in metrics_text:
                print("   Found prompt execution metrics")
        else:
            print(f"❌ Metrics API error: {response.status_code}")
    except Exception as e:
        print(f"❌ Metrics API error: {e}")


def main():
    """Main verification function"""
    print("🔍 Verifying Prompt Engineering Platform")
    print("=" * 50)

    # Check services
    print("\n🏥 Checking Service Health:")
    services_ok = True
    services_ok &= check_service("http://localhost:8085", "Prompt Engineering Service")
    services_ok &= check_service("http://localhost:8080", "Orchestrator Service")
    services_ok &= check_service("http://localhost:8501", "Streamlit Dashboard")

    if not services_ok:
        print("\n❌ Some services are not running!")
        sys.exit(1)

    # Check endpoints
    print("\n🔌 Checking API Endpoints:")
    endpoints_ok = check_endpoints()

    # Verify dashboard data
    verify_dashboard_data()

    # Summary
    print("\n" + "=" * 50)
    if services_ok and endpoints_ok:
        print("✅ All systems operational!")
        print("\n🎯 To view the dashboard:")
        print("1. Open http://localhost:8501")
        print("2. Click '🧪 Prompt Engineering' in sidebar")
        print("3. Data is now coming from real services!")
    else:
        print("❌ Some issues detected. Please check the logs above.")


if __name__ == "__main__":
    main()
