import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from services.orchestrator.db import Base
from services.orchestrator.db.models import VariantPerformance


class TestVariantPerformanceModel:
    """Test the VariantPerformance database model."""
    
    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_create_variant_performance_record(self, db_session):
        """Test creating a new variant performance record."""
        # Arrange
        variant_performance = VariantPerformance(
            variant_id="v_123",
            dimensions={
                "hook_style": "question",
                "emotion": "curiosity",
                "length": "short",
                "cta": "learn_more"
            },
            impressions=100,
            successes=10,
            last_used=datetime.now(timezone.utc)
        )
        
        # Act
        db_session.add(variant_performance)
        db_session.commit()
        
        # Assert
        saved = db_session.query(VariantPerformance).filter_by(variant_id="v_123").first()
        assert saved is not None
        assert saved.variant_id == "v_123"
        assert saved.dimensions["hook_style"] == "question"
        assert saved.impressions == 100
        assert saved.successes == 10
        assert saved.success_rate == 0.1  # 10/100