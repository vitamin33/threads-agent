"""
Test database integration for dashboard API.
Following TDD - write failing tests first to ensure all required tables exist.
"""

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from services.orchestrator.db.models import Base as OrchestratorBase, VariantPerformance
from services.pattern_analyzer.models import Base as PatternBase
from services.dashboard_api.main import app, get_db


def test_all_required_tables_exist_in_test_database():
    """
    Test that all required tables exist in the test database.
    This will fail until we fix the database setup in E2E tests.
    """
    # Create test database
    engine = create_engine("sqlite:///test_dashboard_integration.db")

    # Create all tables from both services
    OrchestratorBase.metadata.create_all(bind=engine)
    PatternBase.metadata.create_all(bind=engine)

    # Inspect database for required tables
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    # Verify required tables exist
    required_tables = [
        "variant_performance",  # From orchestrator
        "pattern_usage",  # From pattern_analyzer
        "posts",  # From orchestrator
        "tasks",  # From orchestrator
    ]

    for table in required_tables:
        assert table in table_names, (
            f"Required table '{table}' is missing from database"
        )


def test_pattern_usage_table_structure():
    """
    Test that pattern_usage table has the correct structure for dashboard integration.
    """
    engine = create_engine("sqlite:///test_dashboard_structure.db")
    PatternBase.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("pattern_usage")
    column_names = [col["name"] for col in columns]

    required_columns = [
        "id",
        "persona_id",
        "pattern_id",
        "post_id",
        "used_at",
        "engagement_rate",
        "created_at",
        "updated_at",
    ]

    for column in required_columns:
        assert column in column_names, (
            f"Required column '{column}' is missing from pattern_usage table"
        )


def test_variant_performance_table_structure():
    """
    Test that variant_performance table has the correct structure for dashboard.
    """
    engine = create_engine("sqlite:///test_dashboard_variant.db")
    OrchestratorBase.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    columns = inspector.get_columns("variant_performance")
    column_names = [col["name"] for col in columns]

    required_columns = [
        "id",
        "variant_id",
        "dimensions",
        "impressions",
        "successes",
        "last_used",
        "created_at",
    ]

    for column in required_columns:
        assert column in column_names, (
            f"Required column '{column}' is missing from variant_performance table"
        )


def test_e2e_database_setup_reproduces_pattern_usage_error():
    """
    Test that reproduces the actual E2E test error with pattern_usage table.
    This test should fail until we fix the E2E database setup.
    """
    import uuid

    # Simulate the exact E2E test database setup with unique DB
    db_name = f"test_e2e_reproduction_{uuid.uuid4().hex[:8]}.db"
    engine = create_engine(f"sqlite:///{db_name}")

    # This is what the E2E tests currently do - only create orchestrator tables
    OrchestratorBase.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Create test variant (this should work)
    db = TestingSessionLocal()
    variant_id = f"test_pattern_error_{uuid.uuid4().hex[:8]}"
    test_variant = VariantPerformance(
        variant_id=variant_id,
        dimensions={"pattern": "question_hook", "persona": "test_persona"},
        impressions=200,
        successes=30,
    )
    db.add(test_variant)
    db.commit()
    db.close()

    # Now try to make API request - this should fail with pattern_usage table error
    client = TestClient(app)
    response = client.get("/dashboard/variants")

    # This assertion will fail because the API call will error due to missing pattern_usage table
    # The response should be 200 with empty variants list (error handling), not 500
    assert response.status_code == 200

    data = response.json()
    # The variants list should be empty due to error handling, not because of successful processing
    assert data["variants"] == []

    # Cleanup
    app.dependency_overrides.clear()


def test_e2e_database_setup_with_all_tables_works_correctly():
    """
    Test that when we create ALL required tables, the dashboard API works correctly.
    This test demonstrates the fix for the E2E tests.
    """
    import uuid

    # Create database with ALL required tables using unique DB
    db_name = f"test_e2e_complete_{uuid.uuid4().hex[:8]}.db"
    engine = create_engine(f"sqlite:///{db_name}")

    # Create BOTH orchestrator and pattern analyzer tables
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

    # Create test variant with unique ID
    db = TestingSessionLocal()
    variant_id = f"test_complete_setup_{uuid.uuid4().hex[:8]}"
    test_variant = VariantPerformance(
        variant_id=variant_id,
        dimensions={"pattern": "question_hook", "persona": "test_persona"},
        impressions=200,
        successes=30,
    )
    db.add(test_variant)
    db.commit()
    db.close()

    # Now try to make API request - this should work correctly
    client = TestClient(app)
    response = client.get("/dashboard/variants")

    # Should return 200 with actual data
    assert response.status_code == 200

    data = response.json()
    # Should have actual variant data, not empty list
    assert len(data["variants"]) == 1

    variant = data["variants"][0]
    assert variant["variant_id"] == variant_id
    assert variant["impressions"] == 200
    assert variant["successes"] == 30
    assert variant["engagement_rate"] == 0.15  # 30/200
    assert "early_kill_status" in variant
    assert "pattern_fatigue_warning" in variant
    assert "freshness_score" in variant

    # Cleanup
    app.dependency_overrides.clear()
