import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from services.orchestrator.db import Base
from services.orchestrator.db.models import VariantPerformance
from services.orchestrator.thompson_sampling import update_variant_performance


class TestVariantPerformanceUpdates:
    """Test updating variant performance after impressions/engagements."""
    
    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_update_variant_performance_increments_impressions(self, db_session):
        """Test that updating performance increments impressions."""
        # Arrange
        variant = VariantPerformance(
            variant_id="v_test",
            dimensions={"hook_style": "question", "emotion": "curiosity"},
            impressions=100,
            successes=10
        )
        db_session.add(variant)
        db_session.commit()
        
        # Act
        update_variant_performance(db_session, "v_test", impression=True, success=False)
        
        # Assert
        updated = db_session.query(VariantPerformance).filter_by(variant_id="v_test").first()
        assert updated.impressions == 101
        assert updated.successes == 10
    
    def test_update_variant_performance_increments_successes(self, db_session):
        """Test that updating performance increments successes."""
        # Arrange
        import time
        variant = VariantPerformance(
            variant_id="v_test",
            dimensions={"hook_style": "question", "emotion": "curiosity"},
            impressions=100,
            successes=10
        )
        db_session.add(variant)
        db_session.commit()
        
        original_last_used = variant.last_used
        time.sleep(0.01)  # Small delay to ensure time difference
        
        # Act
        update_variant_performance(db_session, "v_test", impression=True, success=True)
        
        # Assert
        updated = db_session.query(VariantPerformance).filter_by(variant_id="v_test").first()
        assert updated.impressions == 101
        assert updated.successes == 11
        assert updated.last_used > original_last_used