#!/usr/bin/env python3
"""
MLflow Business Data Audit - Comprehensive Analysis

Analyzes all MLflow data to understand:
1. What models we've tested with real data
2. What business metrics we're collecting
3. What's missing for solopreneur decision-making
4. Recommendations for additional metrics

Focus: Business-critical KPIs for content generation model selection
"""

import mlflow
import json
from pathlib import Path
from typing import Dict, Any, List


class MLflowBusinessAuditor:
    """Audit MLflow data for business insights and gaps."""
    
    def __init__(self):
        """Initialize MLflow business auditor."""
        self.audit_results = {
            "experiments": {},
            "models_tested": {},
            "metrics_collected": set(),
            "business_insights": {},
            "missing_metrics": [],
            "recommendations": []
        }
    
    def audit_mlflow_repository(self, repo_path: str) -> Dict[str, Any]:
        """Audit a specific MLflow repository."""
        abs_path = Path.cwd() / repo_path
        
        if not abs_path.exists():
            return {"error": f"Repository {repo_path} not found"}
        
        mlflow.set_tracking_uri(f"file://{abs_path}")
        
        repo_analysis = {
            "repository": repo_path,
            "experiments": {},
            "total_runs": 0,
            "models_found": set(),
            "metrics_available": set(),
            "business_metrics": {}
        }
        
        try:
            experiments = mlflow.search_experiments()
            
            for exp in experiments:
                exp_analysis = {
                    "name": exp.name,
                    "experiment_id": exp.experiment_id,
                    "runs": [],
                    "models": set(),
                    "metrics": set()
                }
                
                # Get all runs for this experiment
                runs = mlflow.search_runs(experiment_ids=[exp.experiment_id])
                
                for _, run in runs.iterrows():
                    run_analysis = {
                        "run_id": run.name,
                        "status": run.get('status', 'unknown'),
                        "metrics": {},
                        "params": {},
                        "model_name": None
                    }
                    
                    # Extract model name
                    model_name = (
                        run.get('params.display_name') or 
                        run.get('params.model_name') or 
                        'Unknown'
                    )
                    run_analysis["model_name"] = model_name
                    
                    if model_name != 'Unknown':
                        exp_analysis["models"].add(model_name)
                        repo_analysis["models_found"].add(model_name)
                    
                    # Extract all metrics
                    for col in run.index:
                        if col.startswith('metrics.'):
                            metric_name = col.replace('metrics.', '')
                            metric_value = run[col]
                            
                            if pd.notna(metric_value):
                                run_analysis["metrics"][metric_name] = metric_value
                                exp_analysis["metrics"].add(metric_name)
                                repo_analysis["metrics_available"].add(metric_name)
                        
                        elif col.startswith('params.'):
                            param_name = col.replace('params.', '')
                            param_value = run[col]
                            
                            if pd.notna(param_value):
                                run_analysis["params"][param_name] = param_value
                    
                    exp_analysis["runs"].append(run_analysis)
                
                repo_analysis["experiments"][exp.name] = exp_analysis
                repo_analysis["total_runs"] += len(exp_analysis["runs"])
            
            return repo_analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_business_metrics_coverage(self, repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze what business metrics we have vs what we need."""
        
        available_metrics = repo_analysis.get("metrics_available", set())
        models_tested = repo_analysis.get("models_found", set())
        
        # Essential business metrics for solopreneurs
        essential_business_metrics = {
            "performance": [
                "overall_avg_latency_ms", "overall_tokens_per_second", 
                "memory_usage_gb", "load_time_seconds"
            ],
            "cost_analysis": [
                "cost_per_request_usd", "cost_savings_vs_openai_percent",
                "local_cost_per_request", "openai_cost_per_request"
            ],
            "content_specialization": [
                "twitter_content_avg_latency_ms", "linkedin_content_avg_latency_ms",
                "technical_content_avg_latency_ms", "business_content_avg_latency_ms"
            ],
            "quality_assessment": [
                "overall_avg_quality", "twitter_content_avg_quality",
                "linkedin_content_avg_quality", "technical_content_avg_quality"
            ],
            "business_scoring": [
                "overall_business_score", "speed_score", 
                "quality_score", "cost_efficiency_score"
            ],
            "scaling_analysis": [
                "scaling_models_on_m4_max", "scaling_daily_request_capacity"
            ]
        }
        
        coverage_analysis = {}
        missing_metrics = []
        
        for category, metrics in essential_business_metrics.items():
            available_count = sum(1 for metric in metrics if metric in available_metrics)
            coverage_percent = (available_count / len(metrics)) * 100
            
            coverage_analysis[category] = {
                "available": available_count,
                "total": len(metrics),
                "coverage_percent": coverage_percent,
                "missing": [m for m in metrics if m not in available_metrics]
            }
            
            missing_metrics.extend(coverage_analysis[category]["missing"])
        
        return {
            "models_tested": list(models_tested),
            "coverage_analysis": coverage_analysis,
            "missing_metrics": missing_metrics,
            "total_metrics_available": len(available_metrics)
        }
    
    def generate_business_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving business analytics."""
        recommendations = []
        
        models_tested = analysis.get("models_tested", [])
        coverage = analysis.get("coverage_analysis", {})
        
        # Model coverage recommendations
        if len(models_tested) < 4:
            recommendations.append(f"Test more models - currently have {len(models_tested)}, need 4+ for comparison")
        
        # Metric coverage recommendations  
        for category, data in coverage.items():
            if data["coverage_percent"] < 80:
                recommendations.append(f"Improve {category} metrics - only {data['coverage_percent']:.0f}% coverage")
        
        # Business-specific recommendations
        if "scaling_analysis" in coverage and coverage["scaling_analysis"]["coverage_percent"] < 100:
            recommendations.append("Add M4 Max scaling metrics for deployment planning")
        
        if "cost_analysis" in coverage and coverage["cost_analysis"]["coverage_percent"] < 100:
            recommendations.append("Complete cost analysis metrics for ROI calculations")
        
        # Content specialization
        if "content_specialization" in coverage and coverage["content_specialization"]["coverage_percent"] < 100:
            recommendations.append("Add content-type specific performance metrics")
        
        return recommendations
    
    def run_comprehensive_audit(self) -> Dict[str, Any]:
        """Run comprehensive audit of all MLflow data."""
        print("🔍 COMPREHENSIVE MLFLOW BUSINESS AUDIT")
        print("=" * 60)
        
        all_results = {}
        
        # Audit both repositories
        for repo in ["business_mlruns", "unified_model_comparison"]:
            print(f"\\n📊 Auditing {repo}...")
            repo_analysis = self.audit_mlflow_repository(repo)
            all_results[repo] = repo_analysis
            
            if "error" not in repo_analysis:
                print(f"   ✅ {repo_analysis['total_runs']} runs")
                print(f"   🏷️  Models: {list(repo_analysis['models_found'])}")
                print(f"   📈 Metrics: {len(repo_analysis['metrics_available'])}")
        
        # Analyze business metrics coverage
        print("\\n💼 BUSINESS METRICS COVERAGE ANALYSIS")
        print("=" * 50)
        
        # Use the repository with the most comprehensive data
        best_repo = max(
            (repo for repo in all_results.values() if "error" not in repo),
            key=lambda x: x.get("total_runs", 0),
            default={}
        )
        
        if best_repo:
            business_analysis = self.analyze_business_metrics_coverage(best_repo)
            
            print(f"✅ Models tested: {business_analysis['models_tested']}")
            print(f"📊 Total metrics: {business_analysis['total_metrics_available']}")
            print("")
            
            print("📈 Business Metrics Coverage:")
            for category, data in business_analysis["coverage_analysis"].items():
                coverage = data["coverage_percent"]
                status = "✅" if coverage >= 80 else "⚠️" if coverage >= 50 else "❌"
                print(f"   {status} {category}: {coverage:.0f}% ({data['available']}/{data['total']})")
                
                if data["missing"] and coverage < 100:
                    print(f"      Missing: {data['missing'][:2]}...")
            
            # Generate recommendations
            recommendations = self.generate_business_recommendations(business_analysis)
            
            print("\\n💡 BUSINESS RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
            
            # Missing critical metrics
            critical_missing = [
                m for m in business_analysis["missing_metrics"] 
                if any(keyword in m for keyword in ["cost", "business", "scaling"])
            ]
            
            if critical_missing:
                print("\\n🚨 CRITICAL MISSING METRICS:")
                for metric in critical_missing[:5]:
                    print(f"   • {metric}")
            
            return {
                "audit_summary": all_results,
                "business_analysis": business_analysis,
                "recommendations": recommendations,
                "critical_gaps": critical_missing
            }
        else:
            print("❌ No valid MLflow data found")
            return {"error": "No valid MLflow data"}


def main():
    """Run MLflow business audit."""
    auditor = MLflowBusinessAuditor()
    
    try:
        results = auditor.run_comprehensive_audit()
        
        # Save audit results
        audit_file = Path('mlflow_business_audit.json')
        with open(audit_file, 'w') as f:
            # Convert sets to lists for JSON serialization
            serializable_results = json.loads(json.dumps(results, default=list))
            json.dump(serializable_results, f, indent=2)
        
        print(f'\\n📄 Audit results saved: {audit_file}')
        
    except Exception as e:
        print(f'❌ Audit failed: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()"