#!/usr/bin/env python3
"""
Comprehensive CI deployment diagnostic tool.
Helps understand why fake-threads fails in CI but works locally.
"""

import subprocess
import json

# import yaml  # Optional - will work without it
from typing import Dict, Any


def run_command(cmd: str) -> Dict[str, Any]:
    """Run command and return results."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timeout",
            "returncode": -1,
        }


def get_pod_events(pod_name: str) -> Dict[str, Any]:
    """Get detailed pod events and status."""
    cmd = f"kubectl describe pod {pod_name}"
    result = run_command(cmd)
    return result


def analyze_values_file():
    """Analyze the values-ci-fast.yaml configuration."""
    print("\n🔍 ANALYZING VALUES-CI-FAST.YAML")
    print("=" * 50)

    try:
        with open("chart/values-ci-fast.yaml", "r") as f:
            values = yaml.safe_load(f)

        # Extract fake-threads config
        fake_threads_config = values.get("fakeThreads", {})
        print("fake-threads configuration:")
        print(json.dumps(fake_threads_config, indent=2))

        # Extract celery-worker config
        celery_config = values.get("celeryWorker", {})
        print("\ncelery-worker configuration:")
        print(json.dumps(celery_config, indent=2))

        return values
    except Exception as e:
        print(f"Error reading values file: {e}")
        return {}


def check_cluster_resources():
    """Check cluster resource availability."""
    print("\n🏗️ CLUSTER RESOURCE ANALYSIS")
    print("=" * 50)

    # Node resources
    nodes_cmd = "kubectl describe nodes"
    nodes = run_command(nodes_cmd)

    if nodes["success"]:
        lines = nodes["stdout"].split("\n")
        for i, line in enumerate(lines):
            if "Allocated resources" in line or "Resource" in line:
                # Print next 10 lines for resource info
                for j in range(i, min(i + 10, len(lines))):
                    if "cpu" in lines[j].lower() or "memory" in lines[j].lower():
                        print(f"  {lines[j]}")
                break

    # Get pods resource usage
    pods_cmd = "kubectl top pods 2>/dev/null || echo 'Metrics server not available'"
    pods_resources = run_command(pods_cmd)
    print(f"\nPod resources: {pods_resources['stdout']}")


def get_deployment_timeline(deployment_name: str):
    """Get deployment timeline and events."""
    print(f"\n⏱️ DEPLOYMENT TIMELINE: {deployment_name}")
    print("=" * 50)

    # Get deployment status
    deploy_cmd = f"kubectl describe deployment {deployment_name}"
    deploy = run_command(deploy_cmd)

    if deploy["success"]:
        lines = deploy["stdout"].split("\n")
        in_events = False
        for line in lines:
            if "Events:" in line:
                in_events = True
                print("Events:")
                continue
            if in_events and (
                line.strip().startswith("Type")
                or line.strip().startswith("Normal")
                or line.strip().startswith("Warning")
            ):
                print(f"  {line}")

    # Get pods for this deployment
    pods_cmd = f"kubectl get pods -l app={deployment_name} -o json"
    pods = run_command(pods_cmd)

    if pods["success"]:
        try:
            pod_data = json.loads(pods["stdout"])
            for pod in pod_data.get("items", []):
                pod_name = pod["metadata"]["name"]
                print(f"\n📦 Pod: {pod_name}")

                # Pod phase and conditions
                status = pod.get("status", {})
                phase = status.get("phase", "Unknown")
                print(f"  Phase: {phase}")

                # Container statuses
                container_statuses = status.get("containerStatuses", [])
                for container in container_statuses:
                    name = container.get("name")
                    ready = container.get("ready", False)
                    state = container.get("state", {})
                    print(
                        f"  Container {name}: ready={ready}, state={list(state.keys())}"
                    )

                    # If container is waiting, show reason
                    if "waiting" in state:
                        reason = state["waiting"].get("reason", "Unknown")
                        message = state["waiting"].get("message", "")
                        print(f"    Waiting: {reason} - {message}")

                    # If container has restarted, show reason
                    if "terminated" in state:
                        reason = state["terminated"].get("reason", "Unknown")
                        message = state["terminated"].get("message", "")
                        exit_code = state["terminated"].get("exitCode", "Unknown")
                        print(
                            f"    Terminated: {reason} (exit {exit_code}) - {message}"
                        )
        except json.JSONDecodeError as e:
            print(f"Error parsing pod JSON: {e}")


def check_service_connectivity():
    """Check if services can connect to each other."""
    print("\n🌐 SERVICE CONNECTIVITY CHECK")
    print("=" * 50)

    # Get service endpoints
    services_cmd = "kubectl get services"
    services = run_command(services_cmd)
    print(f"Services:\n{services['stdout']}")

    # Get endpoints
    endpoints_cmd = "kubectl get endpoints"
    endpoints = run_command(endpoints_cmd)
    print(f"\nEndpoints:\n{endpoints['stdout']}")


def analyze_health_check_failures():
    """Deep dive into health check failures."""
    print("\n🏥 HEALTH CHECK ANALYSIS")
    print("=" * 50)

    # Get all pods and check their health
    pods_cmd = "kubectl get pods -o json"
    pods_result = run_command(pods_cmd)

    if pods_result["success"]:
        try:
            pods_data = json.loads(pods_result["stdout"])
            for pod in pods_data.get("items", []):
                pod_name = pod["metadata"]["name"]

                if "fake-threads" in pod_name:
                    print(f"\n🔍 ANALYZING POD: {pod_name}")

                    # Show spec vs status for health checks
                    spec = pod.get("spec", {})
                    containers = spec.get("containers", [])

                    for container in containers:
                        container_name = container.get("name")
                        print(f"  Container: {container_name}")

                        # Liveness probe
                        liveness = container.get("livenessProbe", {})
                        if liveness:
                            print(f"    Liveness probe: {liveness}")

                        # Readiness probe
                        readiness = container.get("readinessProbe", {})
                        if readiness:
                            print(f"    Readiness probe: {readiness}")

                        # Show actual port configuration
                        ports = container.get("ports", [])
                        print(f"    Container ports: {ports}")

                    # Try to get logs if pod exists
                    logs_cmd = f"kubectl logs {pod_name} --tail=50"
                    logs = run_command(logs_cmd)
                    if logs["success"] and logs["stdout"]:
                        print(f"    Recent logs:\n{logs['stdout']}")

                    # Get detailed events
                    events_cmd = f"kubectl get events --field-selector involvedObject.name={pod_name}"
                    events = run_command(events_cmd)
                    if events["success"] and events["stdout"]:
                        print(f"    Events:\n{events['stdout']}")

        except json.JSONDecodeError as e:
            print(f"Error parsing pods JSON: {e}")


def simulate_ci_conditions():
    """Try to simulate CI conditions locally."""
    print("\n🎭 SIMULATING CI CONDITIONS")
    print("=" * 50)

    # Check if we're using the same image tags
    images_cmd = "docker images | grep -E '(fake-threads|celery-worker|persona-runtime|orchestrator):local'"
    images = run_command(images_cmd)
    print(f"Local images:\n{images['stdout']}")

    # Check k3d cluster version
    k3d_cmd = "k3d version"
    k3d_version = run_command(k3d_cmd)
    print(f"\nk3d version: {k3d_version['stdout']}")

    # Check kubectl version
    kubectl_cmd = "kubectl version --short"
    kubectl_version = run_command(kubectl_cmd)
    print(f"\nkubectl version: {kubectl_version['stdout']}")

    # Check if we have resource constraints
    limits_cmd = (
        "kubectl describe limitrange 2>/dev/null || echo 'No resource limits set'"
    )
    limits = run_command(limits_cmd)
    print(f"\nResource limits: {limits['stdout']}")


def main():
    """Main diagnostic function."""
    print("🚨 CI DEPLOYMENT DIAGNOSTIC TOOL")
    print("=" * 60)
    print("Analyzing why fake-threads works locally but fails in CI...")

    # Step 1: Analyze configuration
    values_config = analyze_values_file()

    # Step 2: Check cluster state
    check_cluster_resources()

    # Step 3: Get deployment timeline
    get_deployment_timeline("fake-threads")
    get_deployment_timeline("celery-worker")

    # Step 4: Check connectivity
    check_service_connectivity()

    # Step 5: Deep dive health checks
    analyze_health_check_failures()

    # Step 6: Simulate CI conditions
    simulate_ci_conditions()

    print("\n💡 RECOMMENDATIONS")
    print("=" * 50)
    print("1. Check pod logs for startup errors")
    print("2. Verify health check endpoints are accessible")
    print("3. Confirm resource limits aren't too restrictive")
    print("4. Test port connectivity between services")
    print("5. Compare local vs CI Kubernetes versions")


if __name__ == "__main__":
    main()
