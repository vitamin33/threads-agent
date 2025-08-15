#!/usr/bin/env python3
"""
Enhanced Business Testing - Complete Solopreneur Metrics

Adds missing business-critical metrics to our MLflow tracking:
1. ROI and cost-per-content-piece analysis
2. Content engagement prediction scoring
3. Model reliability and error rates
4. Resource efficiency ratios
5. Real-world usage projections

Focus: Complete business decision framework for solopreneur content generation
"""

import asyncio
import logging
import time
import psutil
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import mlflow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedBusinessTester:
    """Enhanced testing with complete business metrics for solopreneur decisions."""
    
    def __init__(self):
        """Initialize enhanced business testing."""
        # Setup enhanced MLflow tracking
        mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
        self.experiment_name = "complete_solopreneur_analysis"
        
        # Create experiment with enhanced business focus
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment:
                self.experiment_id = experiment.experiment_id
            else:
                self.experiment_id = mlflow.create_experiment(
                    self.experiment_name,
                    tags={
                        "methodology": "enhanced_business_metrics",
                        "focus": "complete_solopreneur_content_strategy",
                        "metrics_version": "v2_enhanced",
                        "decision_support": "roi_content_quality_scaling"
                    }
                )
        except Exception:
            self.experiment_id = mlflow.create_experiment(self.experiment_name)
        
        mlflow.set_experiment(self.experiment_name)
        
        # Enhanced business content testing
        self.enhanced_business_tests = {
            "high_value_content": {
                "prompts": [
                    "Write a LinkedIn thought leadership post about AI cost optimization that will get 1000+ views:",
                    "Create a viral Twitter thread about Apple Silicon ML deployment (aim for 500+ retweets):",
                    "Draft a dev.to article intro about local model deployment (target: featured article):"
                ],
                "business_value_per_piece": 50.0,  # Estimated value of high-engagement content
                "target_engagement": "high"
            },
            "client_communication": {
                "prompts": [
                    "Write a professional project update email that builds client confidence:",
                    "Create a proposal summary that wins a $10k AI consulting contract:",
                    "Draft a technical explanation that impresses CTO-level stakeholders:"
                ],
                "business_value_per_piece": 100.0,  # High-value client communication
                "target_engagement": "professional"
            },
            "content_automation": {
                "prompts": [
                    "Generate a quick Twitter post about daily AI insights:",
                    "Create a LinkedIn comment response for industry discussions:",
                    "Write a brief technical tip for developer audience:"
                ],
                "business_value_per_piece": 5.0,  # High-volume, lower-value content
                "target_engagement": "automated"
            }
        }
        
        logger.info("Enhanced business testing framework ready")
    
    async def test_model_with_enhanced_metrics(self, model_name: str, display_name: str) -> Dict[str, Any]:
        """Test model with enhanced business metrics."""
        
        run_name = f"enhanced_{display_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                # === ENHANCED METADATA ===
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", display_name)
                mlflow.log_param("test_methodology", "enhanced_business_metrics_v2")
                mlflow.log_param("business_focus", "complete_solopreneur_analysis")
                
                # === MODEL LOADING WITH ERROR TRACKING ===
                load_start = time.time()
                load_attempts = 0
                load_errors = 0
                
                try:
                    load_attempts += 1
                    
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    if tokenizer.pad_token is None:
                        tokenizer.pad_token = tokenizer.eos_token
                    
                    device = "mps" if torch.backends.mps.is_available() else "cpu"
                    dtype = torch.float16 if device == "mps" else torch.float32
                    
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=dtype,
                        device_map=device if device != "cpu" else None,
                        low_cpu_mem_usage=True
                    )
                    
                    if device != "cpu":
                        model = model.to(device)
                    
                    load_time = time.time() - load_start
                    
                except Exception as e:
                    load_errors += 1
                    raise e
                
                # === ENHANCED MEMORY AND RESOURCE TRACKING ===
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_gb = memory_info.rss / (1024**3)
                
                # Resource efficiency calculation
                performance_per_gb = 1000 / (1411 * memory_gb) if memory_gb > 0 else 0  # Rough efficiency
                
                # === LOG INFRASTRUCTURE METRICS ===
                mlflow.log_metric("model_load_time_seconds", load_time)
                mlflow.log_metric("memory_usage_gb", memory_gb)
                mlflow.log_metric("load_success_rate", (load_attempts - load_errors) / load_attempts)
                mlflow.log_metric("performance_per_gb_ratio", performance_per_gb)
                
                mlflow.log_param("device", device)
                mlflow.log_param("apple_silicon_optimized", device == "mps")
                
                print(f"✅ {display_name} loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
                
                # === ENHANCED BUSINESS CONTENT TESTING ===
                all_test_results = []
                business_value_analysis = {}
                content_generation_rates = {}
                
                total_inference_errors = 0
                total_inference_attempts = 0
                
                for content_category, test_config in self.enhanced_business_tests.items():
                    print(f"📝 Testing {content_category} content...")
                    
                    category_latencies = []
                    category_qualities = []
                    category_engagement_scores = []
                    category_errors = 0
                    
                    for prompt in test_config["prompts"]:
                        total_inference_attempts += 1
                        
                        try:
                            # === ENHANCED INFERENCE WITH ERROR TRACKING ===
                            inference_start = time.time()
                            
                            inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                            if device != "cpu":
                                inputs = {k: v.to(device) for k, v in inputs.items()}
                            
                            with torch.no_grad():
                                outputs = model.generate(
                                    **inputs,
                                    max_new_tokens=100,
                                    temperature=0.8,
                                    do_sample=True,
                                    pad_token_id=tokenizer.pad_token_id
                                )
                            
                            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                            generated_content = response[len(prompt):].strip()
                            
                            inference_time_ms = (time.time() - inference_start) * 1000
                            tokens_generated = len(generated_content.split())
                            
                            # === ENHANCED QUALITY ASSESSMENT ===
                            quality_score = self._enhanced_quality_assessment(prompt, generated_content, content_category)
                            engagement_score = self._predict_engagement_potential(generated_content, content_category)
                            
                            category_latencies.append(inference_time_ms)
                            category_qualities.append(quality_score)
                            category_engagement_scores.append(engagement_score)
                            
                            all_test_results.append({
                                "category": content_category,
                                "prompt": prompt,
                                "response": generated_content,
                                "latency_ms": inference_time_ms,
                                "tokens": tokens_generated,
                                "quality": quality_score,
                                "engagement": engagement_score
                            })
                            
                        except Exception as e:
                            category_errors += 1
                            total_inference_errors += 1
                            logger.warning(f"Inference error for {content_category}: {e}")
                    
                    # === BUSINESS VALUE ANALYSIS PER CONTENT TYPE ===
                    if category_latencies:
                        avg_latency = sum(category_latencies) / len(category_latencies)
                        avg_quality = sum(category_qualities) / len(category_qualities)
                        avg_engagement = sum(category_engagement_scores) / len(category_engagement_scores)
                        
                        # Calculate business metrics
                        content_pieces_per_hour = 3600 / (avg_latency / 1000) if avg_latency > 0 else 0
                        cost_per_content_piece = (avg_latency / 1000 / 3600) * 0.005  # M4 Max power cost
                        value_per_piece = test_config["business_value_per_piece"]
                        roi_per_piece = value_per_piece - cost_per_content_piece
                        
                        business_value_analysis[content_category] = {
                            "avg_latency_ms": avg_latency,
                            "avg_quality_score": avg_quality,
                            "avg_engagement_score": avg_engagement,
                            "content_pieces_per_hour": content_pieces_per_hour,
                            "cost_per_content_piece": cost_per_content_piece,
                            "value_per_piece": value_per_piece,
                            "roi_per_piece": roi_per_piece,
                            "error_rate": category_errors / len(test_config["prompts"])
                        }
                        
                        # === LOG ENHANCED METRICS TO MLFLOW ===
                        mlflow.log_metric(f"{content_category}_avg_latency_ms", avg_latency)
                        mlflow.log_metric(f"{content_category}_avg_quality", avg_quality)
                        mlflow.log_metric(f"{content_category}_avg_engagement", avg_engagement)
                        mlflow.log_metric(f"{content_category}_pieces_per_hour", content_pieces_per_hour)
                        mlflow.log_metric(f"{content_category}_cost_per_piece", cost_per_content_piece)
                        mlflow.log_metric(f"{content_category}_roi_per_piece", roi_per_piece)
                        mlflow.log_metric(f"{content_category}_error_rate", category_errors / len(test_config["prompts"]))
                        
                        print(f"   📊 {content_category}: {avg_latency:.0f}ms, {content_pieces_per_hour:.1f}/hour, ${roi_per_piece:.4f} ROI")
                
                # === OVERALL ENHANCED BUSINESS METRICS ===
                overall_latency = sum(r["latency_ms"] for r in all_test_results) / len(all_test_results)
                overall_quality = sum(r["quality"] for r in all_test_results) / len(all_test_results)
                overall_engagement = sum(r["engagement"] for r in all_test_results) / len(all_test_results)
                
                # Model reliability
                success_rate = (total_inference_attempts - total_inference_errors) / total_inference_attempts
                error_rate = total_inference_errors / total_inference_attempts
                
                # Business efficiency metrics
                content_generation_rate = 3600 / (overall_latency / 1000)  # Content pieces per hour
                total_business_value = sum(bva["roi_per_piece"] for bva in business_value_analysis.values()) / len(business_value_analysis)
                
                # === LOG ENHANCED OVERALL METRICS ===
                mlflow.log_metric("enhanced_overall_latency_ms", overall_latency)
                mlflow.log_metric("enhanced_overall_quality", overall_quality)
                mlflow.log_metric("enhanced_overall_engagement", overall_engagement)
                mlflow.log_metric("model_reliability_success_rate", success_rate)
                mlflow.log_metric("model_error_rate", error_rate)
                mlflow.log_metric("content_generation_rate_per_hour", content_generation_rate)
                mlflow.log_metric("average_business_roi_per_piece", total_business_value)
                mlflow.log_metric("performance_per_gb_efficiency", performance_per_gb)
                
                # === SOLOPRENEUR DECISION METRICS ===
                # Daily content capacity
                daily_content_capacity = content_generation_rate * 8  # 8 hours of work
                
                # Monthly revenue potential (conservative estimate)
                monthly_revenue_potential = daily_content_capacity * 30 * 5.0  # $5 average per piece
                
                # Model deployment recommendation score
                deployment_score = (
                    (10 - min(10, overall_latency / 200)) +  # Speed score
                    overall_quality +                        # Quality score  
                    overall_engagement +                     # Engagement score
                    (success_rate * 10) +                   # Reliability score
                    min(10, performance_per_gb)             # Efficiency score
                ) / 5
                
                mlflow.log_metric("solopreneur_daily_content_capacity", daily_content_capacity)
                mlflow.log_metric("solopreneur_monthly_revenue_potential", monthly_revenue_potential)
                mlflow.log_metric("solopreneur_deployment_recommendation", deployment_score)
                
                # === BUSINESS TAGS ===
                mlflow.set_tag("business_tier", "high" if deployment_score > 7 else "medium" if deployment_score > 5 else "low")
                mlflow.set_tag("recommended_for_solopreneur", "yes" if deployment_score > 6 else "conditional")
                mlflow.set_tag("content_specialization", self._get_content_specialization(business_value_analysis))
                
                print(f"\\n📊 {display_name} Enhanced Business Analysis:")
                print(f"   🚀 Performance: {overall_latency:.0f}ms, {content_generation_rate:.1f} pieces/hour")
                print(f"   💰 Business: ${total_business_value:.4f} ROI/piece, {monthly_revenue_potential:.0f} monthly potential")
                print(f"   🎯 Quality: {overall_quality:.1f}/10 content, {overall_engagement:.1f}/10 engagement")
                print(f"   🔧 Reliability: {success_rate:.1%} success rate")
                print(f"   🏆 Deployment Score: {deployment_score:.1f}/10")
                
                return {
                    "model_name": model_name,
                    "display_name": display_name,
                    "enhanced_metrics": {
                        "overall_latency_ms": overall_latency,
                        "content_generation_rate": content_generation_rate,
                        "business_roi_per_piece": total_business_value,
                        "reliability_success_rate": success_rate,
                        "deployment_recommendation": deployment_score
                    },
                    "business_analysis": business_value_analysis,
                    "mlflow_run_id": run.info.run_id,
                    "success": True
                }
                
            except Exception as e:
                mlflow.log_param("error", str(e))
                mlflow.set_tag("status", "failed")
                logger.error(f"❌ Enhanced testing failed for {display_name}: {e}")
                return {"success": False, "error": str(e)}
    
    def _enhanced_quality_assessment(self, prompt: str, content: str, category: str) -> float:
        """Enhanced content quality assessment with business focus."""
        if not content or len(content.strip()) < 10:
            return 0.0
        
        score = 5.0
        words = content.split()
        
        # === LENGTH OPTIMIZATION ===
        if category == "high_value_content":
            # High-value content: 100-300 words optimal
            if 100 <= len(words) <= 300:
                score += 3.0
            elif 50 <= len(words) < 100:
                score += 1.0
            elif len(words) < 25:
                score -= 3.0
        elif category == "client_communication":
            # Professional: 75-250 words optimal
            if 75 <= len(words) <= 250:
                score += 3.0
            elif len(words) < 30:
                score -= 2.0
        elif category == "content_automation":
            # Quick content: 20-100 words optimal
            if 20 <= len(words) <= 100:
                score += 2.0
            elif len(words) < 10:
                score -= 3.0
        
        # === BUSINESS VOCABULARY ===
        high_value_terms = [
            "optimization", "strategy", "implementation", "scalable",
            "efficiency", "performance", "architecture", "solution"
        ]
        business_term_count = sum(1 for term in high_value_terms if term in content.lower())
        score += min(2.0, business_term_count * 0.4)
        
        # === PROFESSIONAL TONE ===
        professional_indicators = [".", ":", ";", "—"]
        if any(indicator in content for indicator in professional_indicators):
            score += 1.0
        
        return min(10.0, max(0.0, score))
    
    def _predict_engagement_potential(self, content: str, category: str) -> float:
        """Predict content engagement potential (0-10 scale)."""
        if not content:
            return 0.0
        
        engagement_score = 5.0
        
        # === ENGAGEMENT INDICATORS ===
        
        # Questions and calls to action
        if "?" in content:
            engagement_score += 1.0
        
        # Lists and structure
        if any(indicator in content for indicator in ["1.", "•", "-", ":"]):
            engagement_score += 1.0
        
        # Emotional language
        emotional_words = ["amazing", "incredible", "breakthrough", "game-changing", "powerful"]
        if any(word in content.lower() for word in emotional_words):
            engagement_score += 1.0
        
        # Technical credibility
        technical_terms = ["deployment", "optimization", "architecture", "implementation"]
        tech_count = sum(1 for term in technical_terms if term in content.lower())
        engagement_score += min(1.5, tech_count * 0.3)
        
        # Category-specific adjustments
        if category == "high_value_content":
            # High-value content needs hooks and insights
            if any(hook in content.lower() for hook in ["here's", "why", "how", "what"]):
                engagement_score += 1.0
        elif category == "client_communication":
            # Professional content needs clarity and confidence
            if any(phrase in content.lower() for phrase in ["pleased to", "confident", "delivered"]):
                engagement_score += 1.0
        
        return min(10.0, max(0.0, engagement_score))
    
    def _get_content_specialization(self, business_analysis: Dict[str, Any]) -> str:
        """Determine model's content specialization based on performance."""
        if not business_analysis:
            return "general"
        
        # Find best performing content category
        best_category = max(
            business_analysis.items(),
            key=lambda x: x[1]["roi_per_piece"]
        )
        
        return best_category[0]
    
    async def run_enhanced_testing_suite(self, models_to_test: List[Dict[str, str]]) -> Dict[str, Any]:
        """Run enhanced testing on all models."""
        print("🚀 ENHANCED BUSINESS TESTING SUITE")
        print("=" * 60)
        print(f"🎯 Testing {len(models_to_test)} models with enhanced business metrics")
        print("")
        
        results = []
        
        for model_config in models_to_test:
            try:
                result = await self.test_model_with_enhanced_metrics(
                    model_config["name"],
                    model_config["display_name"]
                )
                results.append(result)
                print("")
                
            except Exception as e:
                logger.error(f"Failed enhanced testing for {model_config['display_name']}: {e}")
                results.append({"success": False, "error": str(e)})
        
        # === CREATE ENHANCED COMPARISON SUMMARY ===
        successful_results = [r for r in results if r.get("success")]
        
        if successful_results:
            await self._create_enhanced_comparison_summary(successful_results)
        
        print("🏆 ENHANCED TESTING COMPLETE")
        print("=" * 60)
        print(f"✅ Models tested: {len(successful_results)}/{len(models_to_test)}")
        print("✅ Enhanced business metrics collected")
        print("✅ Solopreneur decision framework ready")
        print("")
        print("🔗 View enhanced results: mlflow ui --backend-store-uri ./enhanced_business_mlflow")
        
        return {
            "enhanced_results": results,
            "models_tested": len(successful_results),
            "experiment_name": self.experiment_name
        }
    
    async def _create_enhanced_comparison_summary(self, results: List[Dict[str, Any]]):
        """Create enhanced comparison summary."""
        with mlflow.start_run(run_name="enhanced_solopreneur_decision_matrix"):
            # === SOLOPRENEUR DECISION MATRIX ===
            mlflow.log_param("analysis_type", "enhanced_solopreneur_decision_matrix")
            mlflow.log_param("models_analyzed", len(results))
            
            # Find best performers for solopreneur needs
            best_roi = max(results, key=lambda x: x["enhanced_metrics"]["business_roi_per_piece"])
            fastest = min(results, key=lambda x: x["enhanced_metrics"]["overall_latency_ms"])
            most_reliable = max(results, key=lambda x: x["enhanced_metrics"]["reliability_success_rate"])
            
            mlflow.log_param("best_roi_model", best_roi["display_name"])
            mlflow.log_param("fastest_model", fastest["display_name"])
            mlflow.log_param("most_reliable_model", most_reliable["display_name"])
            
            # === SOLOPRENEUR RECOMMENDATIONS ===
            mlflow.set_tag("decision_matrix", "complete")
            mlflow.set_tag("business_ready", "solopreneur_optimized")
            
            logger.info("✅ Enhanced comparison summary created")


# === TEST CONFIGURATION ===
ENHANCED_TEST_MODELS = [
    {"name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "display_name": "TinyLlama-1.1B"},
    {"name": "microsoft/DialoGPT-medium", "display_name": "DialoGPT-Medium"},
    {"name": "bigscience/bloom-560m", "display_name": "BLOOM-560M"},
    {"name": "EleutherAI/gpt-neo-1.3B", "display_name": "GPT-Neo-1.3B"}
]


async def main():
    """Run enhanced business testing."""
    tester = EnhancedBusinessTester()
    
    try:
        results = await tester.run_enhanced_testing_suite(ENHANCED_TEST_MODELS)
        
        print("\\n🎉 ENHANCED BUSINESS ANALYSIS COMPLETE!")
        print("💼 Complete solopreneur decision framework ready")
        print("📊 Enhanced metrics for business optimization")
        
    except Exception as e:
        logger.error(f"❌ Enhanced testing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())