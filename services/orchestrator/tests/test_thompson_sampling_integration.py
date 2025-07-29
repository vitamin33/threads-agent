import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from services.orchestrator.db import Base
from services.orchestrator.db.models import VariantPerformance
from services.orchestrator.thompson_sampling import load_variants_from_db, select_top_variants_for_persona


class TestThompsonSamplingIntegration:
    """Test Thompson Sampling integration with database."""
    
    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_load_variants_from_db(self, db_session):
        """Test loading variant performance data from database."""
        # Arrange - Create some test data
        variants = [
            VariantPerformance(
                variant_id="v_001",
                dimensions={"hook_style": "question", "emotion": "curiosity", "length": "short", "cta": "learn_more"},
                impressions=1000,
                successes=100
            ),
            VariantPerformance(
                variant_id="v_002", 
                dimensions={"hook_style": "statement", "emotion": "urgency", "length": "long", "cta": "follow_now"},
                impressions=500,
                successes=150
            ),
            VariantPerformance(
                variant_id="v_003",
                dimensions={"hook_style": "story", "emotion": "excitement", "length": "medium", "cta": "share_thoughts"},
                impressions=0,
                successes=0
            )
        ]
        db_session.add_all(variants)
        db_session.commit()
        
        # Act
        loaded_variants = load_variants_from_db(db_session)
        
        # Assert
        assert len(loaded_variants) == 3
        assert all("variant_id" in v for v in loaded_variants)
        assert all("dimensions" in v for v in loaded_variants)
        assert all("performance" in v for v in loaded_variants)
        
        # Check specific variant
        v1 = next(v for v in loaded_variants if v["variant_id"] == "v_001")
        assert v1["performance"]["impressions"] == 1000
        assert v1["performance"]["successes"] == 100
        assert v1["dimensions"]["hook_style"] == "question"
    
    def test_select_top_variants_for_persona_with_db(self, db_session):
        """Test selecting variants for a specific persona using database."""
        # Arrange - Create test data
        variants = [
            VariantPerformance(
                variant_id="tech_v1",
                dimensions={"hook_style": "question", "emotion": "curiosity", "length": "short", "cta": "learn_more"},
                impressions=2000,
                successes=1200  # 60% success rate
            ),
            VariantPerformance(
                variant_id="tech_v2",
                dimensions={"hook_style": "statement", "emotion": "urgency", "length": "long", "cta": "follow_now"},
                impressions=1000,
                successes=100  # 10% success rate
            )
        ]
        db_session.add_all(variants)
        db_session.commit()
        
        # Act
        selected_ids = select_top_variants_for_persona(
            db_session,
            persona_id="tech_influencer",
            top_k=2,
            min_impressions=100
        )
        
        # Assert
        assert len(selected_ids) == 2
        assert "tech_v1" in selected_ids
        assert "tech_v2" in selected_ids