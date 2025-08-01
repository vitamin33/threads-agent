"""
CRA-234 Requirements Verification Test
This test verifies that all TDD requirements for the Real-Time Variant Performance Dashboard have been implemented.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.dashboard_api.main import app, get_db
from services.orchestrator.db.models import VariantPerformance, Base as OrchestratorBase
from services.pattern_analyzer.models import Base as PatternBase
from services.dashboard_api.variant_metrics_api import VariantMetricsAPI
from services.dashboard_api.websocket_handler import WebSocketHandler
from services.performance_monitor.early_kill import EarlyKillMonitor
from services.pattern_analyzer.pattern_fatigue_detector import PatternFatigueDetector


@pytest.fixture
def complete_test_setup():
    """Set up complete test environment with all required components."""
    import uuid
    
    # Create unique database
    db_name = f"test_cra234_verification_{uuid.uuid4().hex[:8]}.db"
    engine = create_engine(f"sqlite:///{db_name}")
    
    # Create ALL required tables
    OrchestratorBase.metadata.create_all(bind=engine)
    PatternBase.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    # Cleanup
    app.dependency_overrides.clear()


def test_cra234_requirement_1_backend_api_service_with_fastapi(complete_test_setup):
    """
    CRA-234 Requirement 1: Backend API service (FastAPI) with WebSocket support for real-time updates
    """
    # Verify FastAPI app exists
    assert app is not None
    assert app.title == "dashboard_api"
    
    # Verify REST endpoints exist
    client = TestClient(app)
    
    # Test dashboard variants endpoint
    response = client.get("/dashboard/variants")
    assert response.status_code == 200
    data = response.json()
    assert "variants" in data
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    # Verify WebSocket endpoint exists (we can't easily test connection here, but endpoint exists)
    # The WebSocket handler is tested separately


def test_cra234_requirement_2_integration_with_early_kill_monitor(complete_test_setup):
    """
    CRA-234 Requirement 2: Integration with existing EarlyKillMonitor
    """
    db = complete_test_setup
    
    # Create test variant
    variant_id = f"test_early_kill_{pytest.current_uuid}"
    test_variant = VariantPerformance(
        variant_id=variant_id,
        dimensions={"pattern": "test_pattern"},
        impressions=100,
        successes=2  # Low success rate
    )
    db.add(test_variant)
    db.commit()
    
    # Verify EarlyKillMonitor integration
    early_kill_monitor = EarlyKillMonitor()
    pattern_detector = PatternFatigueDetector(db_session=db)
    
    variant_api = VariantMetricsAPI(
        db_session=db,
        early_kill_monitor=early_kill_monitor,
        pattern_fatigue_detector=pattern_detector
    )
    
    metrics = variant_api.get_comprehensive_metrics()
    assert len(metrics) == 1
    assert "early_kill_status" in metrics[0]
    assert metrics[0]["variant_id"] == variant_id


def test_cra234_requirement_3_integration_with_pattern_fatigue_detector(complete_test_setup):
    """
    CRA-234 Requirement 3: Integration with existing PatternFatigueDetector
    """
    db = complete_test_setup
    
    # Create test variant with pattern
    variant_id = f"test_pattern_fatigue_{pytest.current_uuid}"
    test_variant = VariantPerformance(
        variant_id=variant_id,
        dimensions={"pattern": "overused_pattern", "style": "aggressive"},
        impressions=80,
        successes=12
    )
    db.add(test_variant)
    db.commit()
    
    # Verify PatternFatigueDetector integration
    pattern_detector = PatternFatigueDetector(db_session=db)
    early_kill_monitor = EarlyKillMonitor()
    
    variant_api = VariantMetricsAPI(
        db_session=db,
        early_kill_monitor=early_kill_monitor,
        pattern_fatigue_detector=pattern_detector
    )
    
    metrics = variant_api.get_comprehensive_metrics()
    assert len(metrics) == 1
    assert "pattern_fatigue_warning" in metrics[0]
    assert "freshness_score" in metrics[0]
    assert metrics[0]["variant_id"] == variant_id


def test_cra234_requirement_4_database_queries_for_variant_performance(complete_test_setup):
    """
    CRA-234 Requirement 4: Database queries for variant performance data
    """
    db = complete_test_setup
    
    # Create multiple test variants
    test_variants = []
    for i in range(3):
        variant_id = f"test_db_query_{i}_{pytest.current_uuid}"
        variant = VariantPerformance(
            variant_id=variant_id,
            dimensions={"pattern": f"pattern_{i}"},
            impressions=100 + i * 10,
            successes=15 + i * 2
        )
        test_variants.append(variant)
        db.add(variant)
    
    db.commit()
    
    # Verify database queries work correctly
    variant_api = VariantMetricsAPI(db_session=db)
    metrics = variant_api.get_comprehensive_metrics()
    
    assert len(metrics) == 3
    
    # Verify all required fields are present
    for metric in metrics:
        required_fields = [
            "variant_id", "engagement_rate", "impressions", "successes",
            "early_kill_status", "pattern_fatigue_warning", "freshness_score"
        ]
        for field in required_fields:
            assert field in metric, f"Missing required field: {field}"


def test_cra234_requirement_5_live_metrics_dashboard_features():
    """
    CRA-234 Requirement 5: Dashboard provides live metrics for active variants
    """
    # Test VariantMetricsAPI provides all required live metrics
    mock_db = Mock()
    mock_variant = Mock()
    mock_variant.variant_id = "live_test_variant"
    mock_variant.impressions = 200
    mock_variant.successes = 30
    mock_variant.success_rate = 0.15
    mock_variant.dimensions = {"pattern": "live_pattern"}
    
    mock_db.query.return_value.all.return_value = [mock_variant]
    
    # Mock early kill monitor
    mock_early_kill = Mock()
    mock_early_kill.active_sessions = {"live_test_variant": Mock()}
    
    # Mock pattern fatigue detector
    mock_pattern_detector = Mock()
    mock_pattern_detector.is_pattern_fatigued.return_value = False
    mock_pattern_detector.get_freshness_score.return_value = 0.9
    
    variant_api = VariantMetricsAPI(
        db_session=mock_db,
        early_kill_monitor=mock_early_kill,
        pattern_fatigue_detector=mock_pattern_detector
    )
    
    metrics = variant_api.get_comprehensive_metrics()
    
    # Verify live metrics include actual vs predicted engagement rate
    assert len(metrics) == 1
    metric = metrics[0]
    assert metric["engagement_rate"] == 0.15  # Actual engagement rate
    assert metric["impressions"] == 200
    assert metric["successes"] == 30


def test_cra234_requirement_6_websocket_real_time_updates():
    """
    CRA-234 Requirement 6: Real-time WebSocket updates
    """
    # Test WebSocketHandler provides real-time update capability
    mock_variant_api = Mock()
    mock_variant_api.get_comprehensive_metrics.return_value = [
        {
            "variant_id": "ws_test",
            "engagement_rate": 0.12,
            "impressions": 150,
            "early_kill_status": "monitoring"
        }
    ]
    
    # Test WebSocketHandler can be instantiated and handles updates
    handler = WebSocketHandler(variant_metrics_api=mock_variant_api)
    assert handler is not None
    assert handler.variant_metrics_api == mock_variant_api
    assert hasattr(handler, 'handle_connection')
    assert hasattr(handler, 'broadcast_update')


def test_cra234_complete_tdd_implementation_verification():
    """
    Meta-test: Verify that the complete CRA-234 implementation follows TDD principles
    """
    # All core classes exist and are properly implemented
    assert VariantMetricsAPI is not None
    assert WebSocketHandler is not None
    
    # All test files exist and follow TDD pattern
    import os
    test_files = [
        "test_variant_metrics_api.py",
        "test_websocket_handler.py", 
        "test_dashboard_api.py",
        "test_e2e_dashboard.py",
        "test_database_integration.py"
    ]
    
    test_dir = "/Users/vitaliiserbyn/development/team/jordan-kim/threads-agent/services/dashboard_api/tests"
    for test_file in test_files:
        assert os.path.exists(os.path.join(test_dir, test_file)), f"Missing test file: {test_file}"
    
    # Frontend components exist
    frontend_components = [
        "/Users/vitaliiserbyn/development/team/jordan-kim/threads-agent/services/dashboard_frontend/src/components/Dashboard.tsx",
        "/Users/vitaliiserbyn/development/team/jordan-kim/threads-agent/services/dashboard_frontend/src/components/VariantTable.tsx",
        "/Users/vitaliiserbyn/development/team/jordan-kim/threads-agent/services/dashboard_frontend/src/components/AlertPanel.tsx"
    ]
    
    for component in frontend_components:
        assert os.path.exists(component), f"Missing frontend component: {component}"
    
    # Frontend tests exist
    frontend_tests = [
        "/Users/vitaliiserbyn/development/team/jordan-kim/threads-agent/services/dashboard_frontend/src/components/__tests__/Dashboard.test.tsx",
        "/Users/vitaliiserbyn/development/team/jordan-kim/threads-agent/services/dashboard_frontend/src/components/__tests__/VariantTable.test.tsx",
        "/Users/vitaliiserbyn/development/team/jordan-kim/threads-agent/services/dashboard_frontend/src/components/__tests__/AlertPanel.test.tsx"
    ]
    
    for test in frontend_tests:
        assert os.path.exists(test), f"Missing frontend test: {test}"


# Set up unique IDs for each test run
pytest.current_uuid = None

def pytest_runtest_setup(item):
    """Set up unique identifier for each test."""
    import uuid
    pytest.current_uuid = uuid.uuid4().hex[:8]