"""
TDD Tests for Unified Adaptive Achievement Tracker

This test suite implements comprehensive failing tests for the enhanced achievement
tracking system that generates portfolio-optimized data for serbyn.pro job positioning.

Following strict TDD: Write failing tests first, then implement minimal code to pass.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch


class TestEnhancedDatabaseSchema:
    """Test enhanced database schema with AI/MLOps specific fields"""

    def test_achievement_model_has_portfolio_optimization_fields(self):
        """FAILING TEST: Achievement model should have portfolio optimization fields"""
        
        from services.achievement_collector.db.models import Achievement
        
        # Create achievement instance
        achievement = Achievement()
        
        # Should have enhanced portfolio fields
        assert hasattr(achievement, 'pr_type')  # TECHNICAL_ACHIEVEMENT, WORKFLOW_IMPROVEMENT, etc.
        assert hasattr(achievement, 'job_relevance_scores')  # MLOps vs AI Platform scoring
        assert hasattr(achievement, 'quantified_business_impact')  # Structured financial metrics
        assert hasattr(achievement, 'portfolio_narrative')  # Multi-persona stories
        assert hasattr(achievement, 'visual_evidence')  # Screenshots, charts for portfolio
        assert hasattr(achievement, 'ai_job_strategy_alignment')  # AI_JOB_STRATEGY.md goals

    def test_job_relevance_scores_structure(self):
        """FAILING TEST: Job relevance scores should have proper structure for AI/MLOps roles"""
        
        from services.achievement_collector.db.models import Achievement
        
        achievement = Achievement()
        
        # Test job relevance scores structure
        test_scores = {
            "mlops_engineer": {
                "score": 85,
                "relevant_skills": ["MLflow", "model_deployment", "monitoring"],
                "missing_skills": ["Kubeflow", "Feast"],
                "career_impact": "High - directly relevant to MLOps engineering"
            },
            "ai_platform_engineer": {
                "score": 90,
                "relevant_skills": ["vLLM", "cost_optimization", "SLO_monitoring"],
                "missing_skills": ["Bedrock"],
                "career_impact": "Very High - core platform engineering skills"
            },
            "genai_product_engineer": {
                "score": 75,
                "relevant_skills": ["LLM_integration", "RAG", "prompt_engineering"],
                "missing_skills": ["fine_tuning"],
                "career_impact": "Medium - relevant for product engineering"
            }
        }
        
        achievement.job_relevance_scores = test_scores
        
        # Should be able to store and retrieve structured job scoring
        assert achievement.job_relevance_scores is not None
        assert "mlops_engineer" in achievement.job_relevance_scores
        assert achievement.job_relevance_scores["mlops_engineer"]["score"] == 85

    def test_quantified_business_impact_structure(self):
        """FAILING TEST: Quantified business impact should store structured financial metrics"""
        
        from services.achievement_collector.db.models import Achievement
        
        achievement = Achievement()
        
        # Test structured business impact
        test_impact = {
            "financial_impact": {
                "cost_savings": {
                    "amount": 180000,
                    "currency": "USD", 
                    "timeframe": "annual",
                    "confidence": 0.85,
                    "methodology": "GPU cost reduction analysis"
                },
                "revenue_impact": {
                    "amount": 50000,
                    "currency": "USD",
                    "timeframe": "quarterly", 
                    "confidence": 0.75
                }
            },
            "performance_impact": {
                "latency_improvement": {
                    "before_p95": 2500,
                    "after_p95": 800,
                    "improvement_pct": 68,
                    "unit": "milliseconds"
                },
                "throughput_improvement": {
                    "before": 100,
                    "after": 350,
                    "improvement_pct": 250,
                    "unit": "requests_per_second"
                }
            }
        }
        
        achievement.quantified_business_impact = test_impact
        
        # Should store structured financial and performance data
        assert achievement.quantified_business_impact["financial_impact"]["cost_savings"]["amount"] == 180000
        assert achievement.quantified_business_impact["performance_impact"]["latency_improvement"]["improvement_pct"] == 68


class TestTypeAwareAchievementCreation:
    """Test achievement creation that adapts based on PR type detection"""

    def test_create_technical_achievement_from_mlops_pr(self):
        """FAILING TEST: Should create marketing-optimized achievement for technical PRs"""
        
        from services.achievement_collector.services.adaptive_achievement_creator import AdaptiveAchievementCreator
        
        creator = AdaptiveAchievementCreator()
        
        # Technical Achievement PR data with adaptive analysis results
        pr_data = {
            "pr_number": 127,
            "title": "feat: implement MLflow cost optimization with 60% GPU savings",
            "body": "Comprehensive MLflow integration reducing GPU costs by $180k annually through vLLM optimization and automated scaling.",
            "adaptive_analysis": {
                "pr_type": "TECHNICAL_ACHIEVEMENT",
                "business_impact_score": 9,
                "technical_depth_score": 8,
                "mlops_relevance_score": 9,
                "marketing_content_score": 8,
                "overall_marketing_score": 85,
                "content_generation_decision": True
            }
        }
        
        achievement = creator.create_from_pr_analysis(pr_data)
        
        # Should create marketing-optimized achievement
        assert achievement["pr_type"] == "TECHNICAL_ACHIEVEMENT"
        assert achievement["portfolio_ready"] == True
        assert achievement["marketing_potential"] == "HIGH"
        
        # Should have job-specific scoring
        assert "mlops_engineer" in achievement["job_relevance_scores"]
        assert achievement["job_relevance_scores"]["mlops_engineer"]["score"] >= 80
        
        # Should have quantified business impact
        assert "financial_impact" in achievement["quantified_business_impact"]
        assert achievement["quantified_business_impact"]["financial_impact"]["cost_savings"]["amount"] == 180000

    def test_create_workflow_achievement_from_ci_pr(self):
        """FAILING TEST: Should create process-optimized achievement for workflow PRs"""
        
        from services.achievement_collector.services.adaptive_achievement_creator import AdaptiveAchievementCreator
        
        creator = AdaptiveAchievementCreator()
        
        # Workflow Improvement PR data
        pr_data = {
            "pr_number": 128,
            "title": "workflow: implement adaptive PR analysis automation",
            "body": "Enhanced CI/CD with intelligent PR analysis providing developer feedback and process optimization.",
            "adaptive_analysis": {
                "pr_type": "WORKFLOW_IMPROVEMENT", 
                "process_improvement_score": 7,
                "developer_experience_score": 8,
                "automation_value_score": 7,
                "overall_workflow_score": 72,
                "content_generation_decision": False
            }
        }
        
        achievement = creator.create_from_pr_analysis(pr_data)
        
        # Should create process-focused achievement
        assert achievement["pr_type"] == "WORKFLOW_IMPROVEMENT"
        assert achievement["portfolio_ready"] == True  # Still valuable for portfolio
        assert achievement["marketing_potential"] == "LOW"  # Not for marketing content
        
        # Should emphasize process and leadership skills
        assert "process_optimization" in achievement["skills_demonstrated"]
        assert "automation" in achievement["skills_demonstrated"]
        
        # Should have developer productivity impact
        assert "productivity_impact" in achievement["quantified_business_impact"]


class TestJobSpecificScoringSystem:
    """Test job-specific scoring system for AI/MLOps role alignment"""

    def test_mlops_engineer_scoring_prioritizes_mlops_skills(self):
        """FAILING TEST: MLOps Engineer scoring should prioritize MLflow, Kubernetes, monitoring"""
        
        from services.achievement_collector.services.job_scoring_engine import JobScoringEngine
        
        scorer = JobScoringEngine()
        
        # Achievement with strong MLOps components
        achievement_data = {
            "title": "MLflow Model Registry with Automated Rollback",
            "description": "Implemented production MLflow registry with SLO-based rollback and monitoring",
            "skills_demonstrated": ["MLflow", "Kubernetes", "Prometheus", "Model Deployment", "SLO Monitoring"],
            "business_impact": "99.9% uptime, $120k cost savings, 60% deployment time reduction",
            "technologies": ["MLflow", "Kubernetes", "Docker", "Prometheus", "Grafana"]
        }
        
        scores = scorer.calculate_job_relevance_scores(achievement_data)
        
        # MLOps Engineer should score highest
        assert scores["mlops_engineer"]["score"] >= 85
        assert "MLflow" in scores["mlops_engineer"]["relevant_skills"]
        assert "Kubernetes" in scores["mlops_engineer"]["relevant_skills"]
        assert "Model Deployment" in scores["mlops_engineer"]["relevant_skills"]
        
        # Should identify career impact
        assert scores["mlops_engineer"]["career_impact"] == "High - directly relevant to MLOps engineering"

    def test_ai_platform_engineer_scoring_prioritizes_infrastructure(self):
        """FAILING TEST: AI Platform Engineer scoring should prioritize vLLM, cost optimization, infrastructure"""
        
        from services.achievement_collector.services.job_scoring_engine import JobScoringEngine
        
        scorer = JobScoringEngine()
        
        achievement_data = {
            "title": "vLLM Cost Optimization with GPU Auto-scaling", 
            "description": "Reduced AI inference costs by 60% through vLLM deployment and intelligent GPU scaling",
            "skills_demonstrated": ["vLLM", "Cost Optimization", "GPU Management", "Auto-scaling", "Infrastructure"],
            "business_impact": "$200k annual savings, 300% performance improvement",
            "technologies": ["vLLM", "Kubernetes", "CUDA", "Prometheus"]
        }
        
        scores = scorer.calculate_job_relevance_scores(achievement_data)
        
        # AI Platform Engineer should score highest
        assert scores["ai_platform_engineer"]["score"] >= 90
        assert "vLLM" in scores["ai_platform_engineer"]["relevant_skills"]
        assert "Cost Optimization" in scores["ai_platform_engineer"]["relevant_skills"]
        
        # Should score higher than other roles for this achievement
        assert scores["ai_platform_engineer"]["score"] > scores["mlops_engineer"]["score"]

    def test_genai_product_engineer_scoring_prioritizes_llm_integration(self):
        """FAILING TEST: GenAI Product Engineer scoring should prioritize LLM, RAG, prompt engineering"""
        
        from services.achievement_collector.services.job_scoring_engine import JobScoringEngine
        
        scorer = JobScoringEngine()
        
        achievement_data = {
            "title": "RAG Pipeline with Advanced Prompt Engineering",
            "description": "Built production RAG system with multi-modal LLM integration and prompt optimization",
            "skills_demonstrated": ["LLM Integration", "RAG", "Prompt Engineering", "Vector Databases", "OpenAI API"],
            "business_impact": "40% improvement in response quality, 25% cost reduction",
            "technologies": ["LangChain", "Qdrant", "OpenAI", "Embedding Models"]
        }
        
        scores = scorer.calculate_job_relevance_scores(achievement_data)
        
        # GenAI Product Engineer should score highest
        assert scores["genai_product_engineer"]["score"] >= 85
        assert "LLM Integration" in scores["genai_product_engineer"]["relevant_skills"]
        assert "RAG" in scores["genai_product_engineer"]["relevant_skills"]
        assert "Prompt Engineering" in scores["genai_product_engineer"]["relevant_skills"]


class TestMultiPersonaStoryGeneration:
    """Test multi-persona story generation for different audiences"""

    def test_generate_technical_lead_narrative(self):
        """FAILING TEST: Should generate technical leadership narrative for technical leads"""
        
        from services.achievement_collector.services.portfolio_story_generator import PortfolioStoryGenerator
        
        generator = PortfolioStoryGenerator()
        
        achievement_data = {
            "title": "MLflow Production Platform Implementation",
            "quantified_business_impact": {
                "financial_impact": {"cost_savings": {"amount": 180000, "timeframe": "annual"}},
                "performance_impact": {"latency_improvement": {"improvement_pct": 65}}
            },
            "technical_details": {
                "architecture": "Microservices with Kubernetes orchestration",
                "scalability": "Auto-scaling based on demand",
                "monitoring": "Comprehensive observability with Prometheus"
            }
        }
        
        technical_story = generator.generate_narrative(achievement_data, persona="technical_lead")
        
        # Should emphasize technical architecture and implementation
        assert "architecture" in technical_story["narrative"].lower()
        assert "implementation" in technical_story["narrative"].lower()
        assert "scalability" in technical_story["narrative"].lower()
        
        # Should include specific technical metrics
        assert "65%" in technical_story["narrative"]
        assert technical_story["target_audience"] == "technical_lead"
        assert technical_story["story_type"] == "technical_deep_dive"

    def test_generate_hiring_manager_narrative(self):
        """FAILING TEST: Should generate business impact narrative for hiring managers"""
        
        from services.achievement_collector.services.portfolio_story_generator import PortfolioStoryGenerator
        
        generator = PortfolioStoryGenerator()
        
        achievement_data = {
            "title": "AI Infrastructure Cost Optimization",
            "quantified_business_impact": {
                "financial_impact": {"cost_savings": {"amount": 200000, "timeframe": "annual"}},
                "operational_impact": {"deployment_frequency": {"improvement": "7x faster"}}
            },
            "team_impact": {
                "team_size": 4,
                "productivity_improvement": "40%",
                "incident_reduction": "80%"
            }
        }
        
        hiring_manager_story = generator.generate_narrative(achievement_data, persona="hiring_manager")
        
        # Should emphasize business value and team leadership
        assert "$200,000" in hiring_manager_story["narrative"]
        assert "team" in hiring_manager_story["narrative"].lower()
        assert "productivity" in hiring_manager_story["narrative"].lower()
        
        # Should include leadership indicators
        assert any(word in hiring_manager_story["narrative"].lower() for word in ["led", "managed", "improved"])
        assert hiring_manager_story["target_audience"] == "hiring_manager"
        assert hiring_manager_story["story_type"] == "business_impact_showcase"

    def test_generate_cto_narrative(self):
        """FAILING TEST: Should generate strategic impact narrative for CTOs"""
        
        from services.achievement_collector.services.portfolio_story_generator import PortfolioStoryGenerator
        
        generator = PortfolioStoryGenerator()
        
        achievement_data = {
            "title": "Enterprise AI Platform Architecture",
            "strategic_impact": {
                "scalability": "Supports 10x growth without infrastructure changes",
                "competitive_advantage": "6-month faster time-to-market for AI features",
                "risk_mitigation": "Automated failover reduces downtime by 95%"
            },
            "quantified_business_impact": {
                "financial_impact": {"revenue_impact": {"amount": 500000, "timeframe": "annual"}}
            }
        }
        
        cto_story = generator.generate_narrative(achievement_data, persona="cto")
        
        # Should emphasize strategic business impact and scalability
        assert "strategic" in cto_story["narrative"].lower()
        assert "scalability" in cto_story["narrative"].lower()
        assert "competitive" in cto_story["narrative"].lower()
        assert "$500,000" in cto_story["narrative"]
        
        assert cto_story["target_audience"] == "cto"
        assert cto_story["story_type"] == "strategic_impact"


class TestBusinessImpactQuantification:
    """Test structured business impact quantification system"""

    def test_extract_financial_metrics_from_pr_description(self):
        """FAILING TEST: Should extract and structure financial metrics from PR descriptions"""
        
        from services.achievement_collector.services.business_impact_extractor import BusinessImpactExtractor
        
        extractor = BusinessImpactExtractor()
        
        pr_description = """
        This MLflow optimization delivers significant business value:
        
        💰 Cost Savings: $180,000 annual reduction in GPU costs
        ⚡ Performance: 60% faster model training 
        📈 Efficiency: 300% improvement in resource utilization
        🔒 Reliability: 99.9% uptime with automated rollback
        """
        
        financial_metrics = extractor.extract_financial_impact(pr_description)
        
        # Should extract structured financial data
        assert financial_metrics["cost_savings"]["amount"] == 180000
        assert financial_metrics["cost_savings"]["currency"] == "USD"
        assert financial_metrics["cost_savings"]["timeframe"] == "annual"
        assert financial_metrics["cost_savings"]["confidence"] >= 0.8

    def test_extract_performance_metrics_with_before_after(self):
        """FAILING TEST: Should extract performance improvements with before/after comparisons"""
        
        from services.achievement_collector.services.business_impact_extractor import BusinessImpactExtractor
        
        extractor = BusinessImpactExtractor()
        
        pr_description = """
        Performance optimization results:
        - Latency: Reduced from 2.5s to 800ms (68% improvement)
        - Throughput: Increased from 100 to 350 RPS (250% improvement)  
        - Error rate: Decreased from 5% to 0.1% (98% improvement)
        - Memory usage: Reduced from 8GB to 3GB (62.5% improvement)
        """
        
        performance_metrics = extractor.extract_performance_impact(pr_description)
        
        # Should extract before/after performance data
        assert performance_metrics["latency"]["before"] == 2.5
        assert performance_metrics["latency"]["after"] == 0.8
        assert performance_metrics["latency"]["improvement_pct"] == 68
        assert performance_metrics["latency"]["unit"] == "seconds"
        
        assert performance_metrics["throughput"]["improvement_pct"] == 250
        assert performance_metrics["error_rate"]["improvement_pct"] == 98


class TestVisualEvidenceManagement:
    """Test visual evidence management for portfolio display"""

    def test_create_visual_evidence_from_achievement_data(self):
        """FAILING TEST: Should create visual evidence items for portfolio display"""
        
        from services.achievement_collector.services.visual_evidence_manager import VisualEvidenceManager
        
        manager = VisualEvidenceManager()
        
        achievement_data = {
            "title": "MLflow Model Performance Dashboard",
            "quantified_business_impact": {
                "performance_impact": {
                    "accuracy_improvement": {"before": 0.85, "after": 0.92, "improvement_pct": 8.2},
                    "latency_improvement": {"before": 1200, "after": 350, "improvement_pct": 70.8}
                }
            },
            "technologies": ["MLflow", "Grafana", "Prometheus"]
        }
        
        visual_evidence = manager.create_visual_evidence(achievement_data)
        
        # Should create portfolio-ready visual elements
        assert "performance_chart" in visual_evidence
        assert visual_evidence["performance_chart"]["chart_type"] == "before_after_comparison"
        assert visual_evidence["performance_chart"]["title"] == "Model Performance Improvements"
        
        # Should include technology architecture diagram
        assert "architecture_diagram" in visual_evidence
        assert visual_evidence["architecture_diagram"]["components"] == ["MLflow", "Grafana", "Prometheus"]

    def test_generate_metrics_dashboard_screenshot_metadata(self):
        """FAILING TEST: Should generate metadata for metrics dashboard screenshots"""
        
        from services.achievement_collector.services.visual_evidence_manager import VisualEvidenceManager
        
        manager = VisualEvidenceManager()
        
        metrics_data = {
            "dashboard_type": "grafana_mlops",
            "metrics_displayed": ["model_accuracy", "inference_latency", "cost_per_prediction"],
            "time_range": "30_days",
            "key_improvements": ["70% latency reduction", "45% cost savings"]
        }
        
        screenshot_metadata = manager.generate_dashboard_metadata(metrics_data)
        
        # Should create portfolio-ready screenshot metadata
        assert screenshot_metadata["evidence_type"] == "metrics_dashboard"
        assert screenshot_metadata["portfolio_value"] == "HIGH"
        assert "Demonstrates MLOps monitoring expertise" in screenshot_metadata["description"]
        assert screenshot_metadata["recommended_placement"] == "technical_achievements_section"


class TestAIJobStrategyAlignment:
    """Test alignment tracking with AI_JOB_STRATEGY.md goals"""

    def test_track_mlflow_integration_progress(self):
        """FAILING TEST: Should track MLflow integration progress toward AI_JOB_STRATEGY.md goals"""
        
        from services.achievement_collector.services.strategy_alignment_tracker import StrategyAlignmentTracker
        
        tracker = StrategyAlignmentTracker()
        
        achievement_data = {
            "title": "MLflow Model Registry Implementation",
            "technologies": ["MLflow", "Model Registry", "Evaluation Pipeline"],
            "business_impact": "Automated model deployment with 99.5% success rate"
        }
        
        alignment = tracker.calculate_strategy_alignment(achievement_data)
        
        # Should track progress toward MLflow mastery goal
        assert alignment["ai_job_strategy_goals"]["mlflow_integration"]["progress"] >= 0.8
        assert alignment["ai_job_strategy_goals"]["mlflow_integration"]["evidence"] == "Production model registry implementation"
        
        # Should identify remaining gaps
        assert "slo_gates" in alignment["remaining_gaps"]
        assert alignment["strategy_completion_percentage"] >= 40

    def test_track_slo_gates_implementation(self):
        """FAILING TEST: Should track SLO-gated CI progress"""
        
        from services.achievement_collector.services.strategy_alignment_tracker import StrategyAlignmentTracker
        
        tracker = StrategyAlignmentTracker()
        
        achievement_data = {
            "title": "SLO-gated CI Pipeline with Automated Rollback",
            "technologies": ["SLO Monitoring", "Automated Rollback", "p95 Latency Gates"],
            "performance_metrics": {
                "p95_latency": {"threshold": 500, "achieved": 300, "unit": "ms"},
                "error_rate": {"threshold": 1, "achieved": 0.1, "unit": "percent"}
            }
        }
        
        alignment = tracker.calculate_strategy_alignment(achievement_data)
        
        # Should track SLO gates progress
        assert alignment["ai_job_strategy_goals"]["slo_gates"]["progress"] >= 0.9
        assert alignment["ai_job_strategy_goals"]["slo_gates"]["evidence"] == "Production SLO-gated CI with <500ms p95 latency"

    def test_track_cost_optimization_expertise(self):
        """FAILING TEST: Should track cost optimization expertise development"""
        
        from services.achievement_collector.services.strategy_alignment_tracker import StrategyAlignmentTracker
        
        tracker = StrategyAlignmentTracker()
        
        achievement_data = {
            "title": "AI Infrastructure Cost Optimization",
            "quantified_business_impact": {
                "financial_impact": {
                    "cost_savings": {"amount": 240000, "timeframe": "annual"},
                    "cost_reduction_pct": 60
                }
            },
            "technologies": ["Cost Analysis", "Resource Optimization", "FinOps"]
        }
        
        alignment = tracker.calculate_strategy_alignment(achievement_data)
        
        # Should track cost optimization mastery
        assert alignment["ai_job_strategy_goals"]["cost_optimization"]["progress"] >= 0.8
        assert alignment["ai_job_strategy_goals"]["cost_optimization"]["savings_demonstrated"] >= 200000


class TestUnifiedAdaptivePRAnalysisIntegration:
    """Test integration of adaptive PR analysis with achievement creation"""

    def test_unified_workflow_creates_portfolio_optimized_achievements(self):
        """FAILING TEST: Unified workflow should use PR analysis results to create optimized achievements"""
        
        from services.achievement_collector.services.unified_achievement_tracker import UnifiedAchievementTracker
        
        tracker = UnifiedAchievementTracker()
        
        # Complete PR data with adaptive analysis results
        complete_pr_data = {
            "pr_basic_data": {
                "number": 129,
                "title": "feat: implement enterprise MLflow platform with cost monitoring",
                "body": "Production MLflow deployment with $200k annual savings and 99.9% uptime",
                "additions": 850,
                "deletions": 120,
                "changed_files": 12
            },
            "adaptive_analysis_results": {
                "pr_type": "TECHNICAL_ACHIEVEMENT",
                "business_impact_score": 9,
                "technical_depth_score": 8,
                "mlops_relevance_score": 9,
                "overall_marketing_score": 88,
                "content_generation_decision": True,
                "recommended_platforms": ["linkedin", "devto", "medium"]
            },
            "github_metadata": {
                "files_changed": [
                    {"filename": "services/mlflow_service/deployment.py", "changes": 350},
                    {"filename": "monitoring/grafana/mlops-dashboard.json", "changes": 180}
                ],
                "labels": ["mlops", "cost-optimization", "production"]
            }
        }
        
        achievement = tracker.create_unified_achievement(complete_pr_data)
        
        # Should create comprehensive portfolio-optimized achievement
        assert achievement["pr_type"] == "TECHNICAL_ACHIEVEMENT"
        assert achievement["portfolio_ready"] == True
        assert achievement["marketing_automation_triggered"] == True
        
        # Should have job-specific scoring
        assert achievement["job_relevance_scores"]["mlops_engineer"]["score"] >= 85
        
        # Should have quantified business impact
        assert achievement["quantified_business_impact"]["financial_impact"]["cost_savings"]["amount"] == 200000
        
        # Should have multi-persona narratives
        assert "technical_lead" in achievement["portfolio_narrative"]
        assert "hiring_manager" in achievement["portfolio_narrative"]
        
        # Should align with AI job strategy
        assert achievement["ai_job_strategy_alignment"]["mlflow_integration"]["progress"] >= 0.8
        
        # Should trigger marketing content generation
        assert achievement["marketing_content_generated"] == True
        assert "linkedin" in achievement["marketing_platforms_used"]

    def test_workflow_pr_creates_process_optimized_achievement(self):
        """FAILING TEST: Workflow PRs should create process-focused achievements"""
        
        from services.achievement_collector.services.unified_achievement_tracker import UnifiedAchievementTracker
        
        tracker = UnifiedAchievementTracker()
        
        workflow_pr_data = {
            "pr_basic_data": {
                "title": "workflow: implement automated code quality gates",
                "body": "Enhanced CI/CD with automated testing and quality validation improving developer productivity"
            },
            "adaptive_analysis_results": {
                "pr_type": "WORKFLOW_IMPROVEMENT",
                "process_improvement_score": 8,
                "developer_experience_score": 7,
                "overall_workflow_score": 75,
                "content_generation_decision": False
            }
        }
        
        achievement = tracker.create_unified_achievement(workflow_pr_data)
        
        # Should create process-focused achievement
        assert achievement["pr_type"] == "WORKFLOW_IMPROVEMENT"
        assert achievement["portfolio_ready"] == True  # Still valuable for leadership demonstration
        assert achievement["marketing_automation_triggered"] == False  # No marketing content
        
        # Should emphasize process and leadership skills
        assert "process_optimization" in achievement["skills_demonstrated"]
        assert "team_productivity" in achievement["business_impact_category"]
        
        # Should have appropriate narrative for leadership roles
        assert "improved team efficiency" in achievement["portfolio_narrative"]["technical_lead"]["narrative"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])