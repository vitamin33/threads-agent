"""
Tests for anomaly detection API endpoints.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch
from services.finops_engine.fastapi_app import app

client = TestClient(app)


def test_detect_anomalies_endpoint():
    """Test the anomaly detection endpoint."""
    request_data = {
        "cost_per_post": 0.03,  # Above $0.02 threshold
        "viral_coefficient": 1.0,  # Below 1.5 baseline
        "pattern_usage_count": 100,
        "pattern_name": "viral_hook",
        "engagement_rate": 0.06,
    }

    response = client.post("/anomaly/detect", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert "anomalies_detected" in data
    assert data["anomalies_detected"] >= 2  # Cost and viral coefficient anomalies
    assert "anomalies" in data
    assert data["models_updated"] is True


def test_send_anomaly_alert_endpoint():
    """Test the alert sending endpoint."""
    with patch(
        "finops_engine.alert_channels.AlertChannelManager.send_alert"
    ) as mock_send:
        mock_send.return_value = {
            "slack": {"status": "success"},
            "discord": {"status": "success"},
            "telegram": {"status": "skipped", "reason": "Not configured"},
            "webhook": {"status": "success"},
        }

        request_data = {
            "alert_data": {
                "title": "Cost Anomaly Detected",
                "message": "Cost per post exceeded threshold",
                "severity": "critical",
                "cost": 0.05,
                "threshold": 0.02,
            },
            "channels": ["slack", "discord", "telegram", "webhook"],
        }

        response = client.post("/anomaly/alert", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["alerts_sent"] == 3  # 3 successful
        assert "channel_results" in data


def test_get_anomaly_thresholds():
    """Test getting current anomaly thresholds."""
    response = client.get("/anomaly/thresholds")
    assert response.status_code == 200

    data = response.json()
    assert "cost_per_post" in data
    assert data["cost_per_post"]["target"] == 0.02
    assert data["cost_per_post"]["warning_threshold"] == 0.25

    assert "viral_coefficient" in data
    assert data["viral_coefficient"]["drop_threshold"] == 0.7

    assert "pattern_fatigue" in data
    assert data["pattern_fatigue"]["warning_threshold"] == 0.8


def test_update_anomaly_thresholds():
    """Test updating anomaly thresholds."""
    response = client.put(
        "/anomaly/thresholds",
        params={"cost_baseline": 0.025, "viral_drop_threshold": 0.6},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["cost_per_post"]["target"] == 0.025
    assert data["viral_coefficient"]["drop_threshold"] == 0.6

    # Reset to defaults
    client.put(
        "/anomaly/thresholds",
        params={"cost_baseline": 0.02, "viral_drop_threshold": 0.7},
    )


def test_get_model_statistics():
    """Test getting model statistics."""
    # First, update models with some data
    request_data = {
        "cost_per_post": 0.02,
        "viral_coefficient": 1.5,
        "pattern_usage_count": 10,
        "pattern_name": "test_pattern",
        "engagement_rate": 0.07,
    }
    client.post("/anomaly/detect", json=request_data)

    response = client.get("/anomaly/models/stats")
    assert response.status_code == 200

    data = response.json()
    assert "statistical_model" in data
    assert data["statistical_model"]["data_points"] >= 1

    assert "trend_model" in data
    assert "seasonal_model" in data
    assert "fatigue_model" in data


def test_reset_anomaly_models():
    """Test resetting anomaly models."""
    # Reset specific models
    response = client.post(
        "/anomaly/models/reset", json={"models": ["statistical", "trend"]}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["models_reset"]["statistical"] == "reset"
    assert data["models_reset"]["trend"] == "reset"
    assert "seasonal" not in data["models_reset"]

    # Reset all models
    response = client.post("/anomaly/models/reset")
    assert response.status_code == 200

    data = response.json()
    assert len(data["models_reset"]) == 4


def test_anomaly_detection_integration():
    """Test full anomaly detection and alerting flow."""
    # 1. Update thresholds
    client.put("/anomaly/thresholds", params={"cost_baseline": 0.015})

    # 2. Detect anomalies
    request_data = {
        "cost_per_post": 0.025,  # Above new threshold
        "viral_coefficient": 1.8,
        "pattern_usage_count": 150,
        "pattern_name": "overused_pattern",
        "engagement_rate": 0.08,
    }

    detect_response = client.post("/anomaly/detect", json=request_data)
    assert detect_response.status_code == 200

    anomalies = detect_response.json()["anomalies"]
    assert len(anomalies) > 0

    # 3. Send alert for first anomaly
    if anomalies:
        with patch(
            "finops_engine.alert_channels.AlertChannelManager.send_alert"
        ) as mock_send:
            mock_send.return_value = {"slack": {"status": "success"}}

            alert_data = {
                "alert_data": {
                    "title": f"{anomalies[0]['metric_name']} Anomaly",
                    "message": f"Current: {anomalies[0]['current_value']}, Baseline: {anomalies[0]['baseline']}",
                    "severity": anomalies[0]["severity"],
                },
                "channels": ["slack"],
            }

            alert_response = client.post("/anomaly/alert", json=alert_data)
            assert alert_response.status_code == 200
            assert alert_response.json()["alerts_sent"] == 1

    # 4. Check model statistics
    stats_response = client.get("/anomaly/models/stats")
    assert stats_response.status_code == 200

    # 5. Reset everything
    client.post("/anomaly/models/reset")
    client.put("/anomaly/thresholds", params={"cost_baseline": 0.02})
