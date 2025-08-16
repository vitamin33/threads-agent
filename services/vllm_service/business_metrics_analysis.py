#!/usr/bin/env python3
"""
Business Metrics Analysis - AI-Powered Insights from MLflow Data

Analyzes all MLflow business metrics to provide clear recommendations:
1. Model quality ranking for lead generation
2. Cost-performance optimization insights  
3. Content specialization recommendations
4. Business decision framework
5. ROI analysis and projections

Focus: Clear business insights from complex MLflow data
"""

import mlflow
import pandas as pd
from pathlib import Path


def analyze_business_metrics():
    """Analyze MLflow business metrics for solopreneur decisions."""
    
    print("📊 AI-POWERED BUSINESS METRICS ANALYSIS")
    print("=" * 60)
    
    # Connect to MLflow
    mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
    
    try:
        # Get the main experiment
        experiment = mlflow.get_experiment_by_name("complete_solopreneur_analysis")
        
        if not experiment:
            print("❌ Experiment not found")
            return
        
        # Get all runs
        runs_df = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
        successful_runs = runs_df[runs_df['status'] == 'FINISHED']
        
        print(f"✅ Found {len(successful_runs)} successful model tests")
        print("")
        
        # === BUSINESS MODEL RANKING ===
        print("🏆 BUSINESS MODEL RANKING (Based on Real Data):")
        print("=" * 50)
        
        model_analysis = []
        
        for _, run in successful_runs.iterrows():
            model_name = run.get('params.display_name', 'Unknown')
            
            if model_name != 'Unknown':
                # Extract key business metrics
                quality = run.get('metrics.enhanced_overall_quality', run.get('metrics.lead_gen_overall_quality', 0))
                latency = run.get('metrics.enhanced_overall_latency_ms', run.get('metrics.premium_avg_latency_ms', 0))
                roi = run.get('metrics.average_business_roi_per_piece', 0)
                recommendation = run.get('metrics.solopreneur_deployment_recommendation', 0)
                memory = run.get('metrics.memory_usage_gb', 0)
                
                model_analysis.append({
                    'model': model_name,
                    'quality': quality,
                    'latency_ms': latency,
                    'roi_per_piece': roi,
                    'business_score': recommendation,
                    'memory_gb': memory
                })
        
        # Sort by quality (most important for business)
        model_analysis.sort(key=lambda x: x['quality'], reverse=True)
        
        print("Rank | Model                | Quality | Speed    | ROI/Piece | Business Score")
        print("-" * 75)
        
        for i, model in enumerate(model_analysis, 1):
            print(f"{i:2d}   | {model['model']:<18} | {model['quality']:5.1f}/10 | {model['latency_ms']:6.0f}ms | ${model['roi_per_piece']:7.2f} | {model['business_score']:6.1f}/10")
        
        print("")
        
        # === BUSINESS INSIGHTS ===
        print("💼 BUSINESS INSIGHTS FOR SOLOPRENEUR:")
        print("=" * 50)
        
        if model_analysis:
            best_quality = model_analysis[0]
            fastest_model = min(model_analysis, key=lambda x: x['latency_ms'])
            
            print(f"🥇 Quality Leader: {best_quality['model']} ({best_quality['quality']:.1f}/10)")
            print(f"   • Best for: Lead-generating content, client communication")
            print(f"   • Speed: {best_quality['latency_ms']:.0f}ms")
            print(f"   • ROI: ${best_quality['roi_per_piece']:.2f} per piece")
            print("")
            
            print(f"⚡ Speed Champion: {fastest_model['model']} ({fastest_model['latency_ms']:.0f}ms)")
            print(f"   • Best for: High-volume content automation") 
            print(f"   • Quality: {fastest_model['quality']:.1f}/10")
            print("")
            
            # Quality threshold analysis
            high_quality_models = [m for m in model_analysis if m['quality'] >= 7.0]
            
            print(f"✅ High-Quality Models (7.0+/10): {len(high_quality_models)}")
            for model in high_quality_models:
                print(f"   • {model['model']}: {model['quality']:.1f}/10 quality")
            
            if len(high_quality_models) == 0:
                print("⚠️  No models meet 7.0+ quality threshold for business content")
                print("💡 Recommendation: Test larger, more capable models")
        
        # === METRIC EXPLANATION ===
        print("\\n📖 METRIC EXPLANATION GUIDE:")
        print("=" * 50)
        
        print("🎯 Content Quality Metrics (0-10 scale):")
        print("  • enhanced_overall_quality: General content quality")
        print("  • lead_gen_*_quality: Lead generation content quality")
        print("  • *_content_avg_quality: Content type specific quality")
        print("  → Target: 8-9/10 for professional business content")
        print("")
        
        print("⚡ Performance Metrics:")
        print("  • *_latency_ms: Speed of content generation")
        print("  • content_generation_rate_per_hour: Pieces you can create per hour")
        print("  • memory_usage_gb: Apple Silicon M4 Max memory usage")
        print("  → Target: <1000ms for responsive content creation")
        print("")
        
        print("💰 Business ROI Metrics:")
        print("  • *_roi_per_piece: Profit potential per content piece")
        print("  • monthly_revenue_potential: Theoretical monthly earnings")
        print("  • cost_savings_vs_openai_percent: Savings vs API (target: 95%+)")
        print("  → Focus: ROI and cost efficiency")
        print("")
        
        print("📊 Business Decision Metrics:")
        print("  • solopreneur_deployment_recommendation: Overall score (0-10)")
        print("  • model_reliability_success_rate: Error rate (target: 100%)")
        print("  → Use for: Model selection decisions")
        print("")
        
        # === AI ANALYSIS RECOMMENDATION ===
        print("🤖 AI-POWERED ANALYSIS RECOMMENDATIONS:")
        print("=" * 50)
        
        if model_analysis:
            best_model = model_analysis[0]
            
            if best_model['quality'] >= 8.0:
                print("✅ EXCELLENT: Found enterprise-grade model for business content")
                print(f"   Use {best_model['model']} for lead generation")
            elif best_model['quality'] >= 6.0:
                print("⚠️  ACCEPTABLE: Decent quality but room for improvement")
                print("   Consider testing larger models for better quality")
            else:
                print("❌ INSUFFICIENT: Current models too low quality for business")
                print("   Must test higher-capacity models")
        
        print("\\n🎯 NEXT AI ANALYSIS STEPS:")
        print("1. Test facebook/opt-2.7b (larger model for quality boost)")
        print("2. Compare all models side-by-side in MLflow")
        print("3. Generate business decision matrix")
        print("4. Create content strategy recommendations")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()


def explain_mlflow_structure():
    """Explain MLflow structure for business users."""
    
    print("\\n📚 MLFLOW STRUCTURE EXPLANATION:")
    print("=" * 50)
    
    print("🔍 WHY 'REGISTERED MODELS' IS EMPTY (NORMAL):")
    print("• Registered Models = Production deployment registry")
    print("• We are in RESEARCH phase, testing multiple models")
    print("• Once we choose the best model, we would register it there")
    print("• Empty is correct for experimentation phase")
    print("")
    
    print("📊 WHY 'EXPERIMENTS' HAS YOUR DATA:")
    print("• Experiments = Research and comparison data")
    print("• Each run = one model test with business metrics")
    print("• Perfect for comparing models before production")
    print("• This is where all your business insights live")
    print("")
    
    print("🎯 HOW TO USE THE DATA:")
    print("1. Compare quality scores across models")
    print("2. Analyze ROI metrics for business decisions")
    print("3. Look at performance vs memory tradeoffs")
    print("4. Use business_score for final recommendations")


if __name__ == "__main__":
    try:
        analyze_business_metrics()
        explain_mlflow_structure()
        
        print("\\n🤖 AI ANALYSIS COMPLETE!")
        print("💼 Business decision insights ready")
        print("🔗 MLflow Dashboard: http://127.0.0.1:5000")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")