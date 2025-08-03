#!/usr/bin/env python3
"""
Quick performance test for anomaly detector to verify SLA compliance.
"""

import time
import sys
import os

# Add the parent directory to the path so we can import our module
sys.path.append(os.path.dirname(__file__))

from anomaly_detector import AnomalyDetector


def main():
    detector = AnomalyDetector()

    # Performance test: run 1000 detections
    print("Running performance test...")
    start = time.time()

    for i in range(1000):
        detector.detect_cost_anomaly(0.025, 0.020, "ai_jesus")
        detector.detect_viral_coefficient_drop(0.65, 1.0, "ai_jesus")
        detector.detect_pattern_fatigue(0.85, "ai_jesus")

    duration = time.time() - start

    print(f"✅ 1000 detections completed in {duration:.4f}s")
    print(f"⚡ Average per detection: {(duration / 1000) * 1000:.2f}ms")
    print(f"🎯 Well under 60s SLA: {duration < 60}")

    # Single detection breakdown
    start = time.time()
    result = detector.detect_cost_anomaly(0.030, 0.020, "ai_jesus")
    single_duration = time.time() - start

    print("\n📊 Single anomaly detection:")
    print(f"   Duration: {single_duration * 1000:.2f}ms")
    print(f"   Result: {result.metric_name if result else 'No anomaly'}")
    print(f"   Severity: {result.severity if result else 'N/A'}")
    print(f"   Confidence: {result.confidence if result else 'N/A'}")


if __name__ == "__main__":
    main()
