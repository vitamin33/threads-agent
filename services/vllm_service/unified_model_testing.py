#!/usr/bin/env python3
"""
Unified Model Testing Framework - Consistent Business Analysis

Tests ALL models with the same methodology for fair comparison:
- Standardized business prompts across all models
- Consistent content quality assessment 
- Same cost calculation methodology
- Unified Apple Silicon optimization
- Comprehensive MLflow logging

Models to Test with Unified Framework:
1. TinyLlama-1.1B (retest with new methodology)
2. DialoGPT-Medium (retest with new methodology)
3. BLOOM-560M (new model)
4. GPT-Neo-1.3B (new model)

Solopreneur Business Focus:
- Content generation optimization
- Cost vs performance analysis
- Multi-model deployment strategy
- Apple Silicon M4 Max scaling
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import mlflow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UnifiedModelTester:
    """Unified testing framework for consistent model comparison."""
    
    def __init__(self):
        """Initialize unified testing framework."""
        # MLflow setup
        mlflow.set_tracking_uri("file:./unified_model_comparison")
        self.experiment_name = "unified_business_model_comparison"
        
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment:
                self.experiment_id = experiment.experiment_id
            else:
                self.experiment_id = mlflow.create_experiment(
                    self.experiment_name,
                    tags={
                        "methodology": "unified_consistent_testing",
                        "business_focus": "solopreneur_content_generation",
                        "platform": "apple_silicon_m4_max",
                        "comparison_type": "fair_apples_to_apples"
                    }
                )
        except Exception:
            self.experiment_id = mlflow.create_experiment(self.experiment_name)
        
        mlflow.set_experiment(self.experiment_name)
        
        # === STANDARDIZED BUSINESS TEST SUITE ===
        self.business_test_suite = {
            "twitter_content": [
                "Write a Twitter thread about AI cost optimization for startups:",
                "Create a viral tweet about Apple Silicon ML benefits:",
                "Draft a Twitter thread about remote work productivity:"
            ],
            "linkedin_content": [
                "Write a LinkedIn post about AI infrastructure engineering:",
                "Create a professional post about Apple Silicon for ML teams:",
                "Draft a thought leadership post about local model deployment:"
            ],
            "technical_content": [
                "Write a dev.to article intro about vLLM optimization:",
                "Explain microservices architecture for AI applications:",
                "Create technical documentation for model deployment:"
            ],
            "business_content": [
                "Draft a professional email about AI implementation strategy:",
                "Write a proposal summary for ML consulting services:",
                "Create a client update about performance optimization results:"
            ]
        }
        
        # Models to test with unified methodology
        self.models_to_test = [
            {
                "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                "display_name": "TinyLlama-1.1B",
                "category": "general_purpose",
                "expected_strength": "speed_and_efficiency"
            },
            {
                "name": "microsoft/DialoGPT-medium",
                "display_name": "DialoGPT-Medium", 
                "category": "conversational_specialist",
                "expected_strength": "social_media_content"
            },
            {
                "name": "bigscience/bloom-560m",
                "display_name": "BLOOM-560M",
                "category": "speed_champion", 
                "expected_strength": "fast_generation"
            },
            {
                "name": "EleutherAI/gpt-neo-1.3B",
                "display_name": "GPT-Neo-1.3B",
                "category": "technical_specialist",
                "expected_strength": "technical_writing"
            }
        ]
        
        logger.info(f"Unified testing framework ready: {len(self.models_to_test)} models, {sum(len(prompts) for prompts in self.business_test_suite.values())} test prompts")
    
    async def test_model_unified_methodology(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a model with unified business methodology."""
        model_name = model_config["name"]
        display_name = model_config["display_name"]
        
        print(f"\\n🧪 UNIFIED TESTING: {display_name}")
        print("=" * 60)
        
        run_name = f"unified_test_{display_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                # === STANDARDIZED METADATA ===
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", display_name)
                mlflow.log_param("model_category", model_config["category"])
                mlflow.log_param("expected_strength", model_config["expected_strength"])
                mlflow.log_param("test_methodology", "unified_business_framework")
                mlflow.log_param("test_date", datetime.now().isoformat())
                mlflow.log_param("platform", "apple_silicon_m4_max")
                
                # === STANDARDIZED MODEL LOADING ===
                load_start = time.time()
                
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                # Consistent Apple Silicon optimization
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
                
                # === STANDARDIZED MEMORY MEASUREMENT ===
                process = psutil.Process()
                memory_gb = process.memory_info().rss / (1024**3)
                
                mlflow.log_metric("load_time_seconds", load_time)
                mlflow.log_metric("memory_usage_gb", memory_gb)
                mlflow.log_param("device", device)
                mlflow.log_param("apple_mps_optimization", device == "mps")
                
                print(f"✅ Loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
                
                # === STANDARDIZED BUSINESS CONTENT TESTING ===
                all_test_results = []
                content_type_performance = {}
                
                for content_type, prompts in self.business_test_suite.items():
                    print(f"📝 Testing {content_type}...")
                    
                    type_latencies = []
                    type_qualities = []
                    type_tokens = []
                    
                    for prompt in prompts:
                        # === STANDARDIZED INFERENCE ===
                        inference_start = time.time()
                        
                        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
                        if device != "cpu":
                            inputs = {k: v.to(device) for k, v in inputs.items()}
                        
                        with torch.no_grad():
                            outputs = model.generate(
                                **inputs,
                                max_new_tokens=80,  # Consistent token limit
                                temperature=0.8,    # Consistent creativity
                                do_sample=True,
                                pad_token_id=tokenizer.pad_token_id,
                                early_stopping=True
                            )
                        
                        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        generated_content = response[len(prompt):].strip()
                        
                        inference_time_ms = (time.time() - inference_start) * 1000
                        tokens_generated = len(generated_content.split())
                        
                        # === STANDARDIZED QUALITY ASSESSMENT ===
                        quality_score = self._assess_business_quality(prompt, generated_content, content_type)
                        
                        test_result = {
                            "content_type": content_type,
                            "prompt": prompt,
                            "response": generated_content,
                            "inference_time_ms": inference_time_ms,
                            "tokens_generated": tokens_generated,
                            "quality_score": quality_score
                        }
                        
                        all_test_results.append(test_result)
                        type_latencies.append(inference_time_ms)
                        type_qualities.append(quality_score)
                        type_tokens.append(tokens_generated)
                    
                    # === CONTENT TYPE METRICS ===
                    avg_latency = sum(type_latencies) / len(type_latencies)
                    avg_quality = sum(type_qualities) / len(type_qualities)
                    avg_tokens = sum(type_tokens) / len(type_tokens)
                    
                    content_type_performance[content_type] = {
                        "avg_latency_ms": avg_latency,
                        "avg_quality_score": avg_quality,
                        "avg_tokens_generated": avg_tokens
                    }
                    
                    # Log to MLflow
                    mlflow.log_metric(f"{content_type}_avg_latency_ms", avg_latency)
                    mlflow.log_metric(f"{content_type}_avg_quality", avg_quality)
                    mlflow.log_metric(f"{content_type}_avg_tokens", avg_tokens)
                    
                    print(f"   📊 {content_type}: {avg_latency:.0f}ms, quality {avg_quality:.1f}/10")
                
                # === OVERALL BUSINESS METRICS ===
                overall_latency = sum(r["inference_time_ms"] for r in all_test_results) / len(all_test_results)
                overall_quality = sum(r["quality_score"] for r in all_test_results) / len(all_test_results)
                total_tokens = sum(r["tokens_generated"] for r in all_test_results)
                total_time_seconds = sum(r["inference_time_ms"] for r in all_test_results) / 1000
                tokens_per_second = total_tokens / total_time_seconds if total_time_seconds > 0 else 0
                
                # === STANDARDIZED COST ANALYSIS ===
                # M4 Max power consumption: 35W during ML workload
                power_cost_per_hour = (35 / 1000) * 0.15  # 35W * $0.15/kWh
                inference_cost = (overall_latency / 1000 / 3600) * power_cost_per_hour
                
                openai_cost_per_request = 0.000150  # Standard comparison
                cost_savings_percent = ((openai_cost_per_request - inference_cost) / openai_cost_per_request) * 100
                
                # === BUSINESS SCORING ===
                speed_score = max(0, 10 - (overall_latency / 200))
                quality_score = overall_quality
                cost_score = min(10, cost_savings_percent / 10)
                memory_score = max(0, 10 - memory_gb)
                
                business_score = (speed_score + quality_score + cost_score + memory_score) / 4
                
                # === LOG ALL BUSINESS METRICS ===
                mlflow.log_metric("overall_avg_latency_ms", overall_latency)
                mlflow.log_metric("overall_avg_quality", overall_quality)
                mlflow.log_metric("overall_tokens_per_second", tokens_per_second)
                mlflow.log_metric("overall_business_score", business_score)
                
                mlflow.log_metric("cost_per_request_usd", inference_cost)
                mlflow.log_metric("cost_savings_vs_openai_percent", cost_savings_percent)
                
                mlflow.log_metric("speed_score", speed_score)
                mlflow.log_metric("quality_score", quality_score)
                mlflow.log_metric("cost_efficiency_score", cost_score)
                mlflow.log_metric("memory_efficiency_score", memory_score)
                
                # === SCALING METRICS ===
                models_can_fit = int((36.0 * 0.85) / memory_gb)
                daily_capacity = (24 * 3600) / (overall_latency / 1000)
                
                mlflow.log_metric("scaling_models_on_m4_max", models_can_fit)
                mlflow.log_metric("scaling_daily_request_capacity", daily_capacity)
                
                # === BUSINESS TAGS ===
                mlflow.set_tag("test_version", "unified_v2")
                mlflow.set_tag("business_category", model_config["category"])
                mlflow.set_tag("recommended_use", model_config["expected_strength"])
                mlflow.set_tag("apple_silicon_optimized", "yes")
                
                print(f"\\n📊 {display_name} Unified Results:")
                print(f"   Performance: {overall_latency:.0f}ms, {tokens_per_second:.1f} tok/s")
                print(f"   Business Score: {business_score:.1f}/10")
                print(f"   Cost Savings: {cost_savings_percent:.1f}%")
                print(f"   Scaling: {models_can_fit} models on M4 Max")
                print(f"   MLflow Run: {run.info.run_id}")
                
                return {
                    "model_config": model_config,
                    "performance": {
                        "latency_ms": overall_latency,
                        "quality_score": overall_quality,
                        "tokens_per_second": tokens_per_second,
                        "memory_gb": memory_gb,
                        "load_time_s": load_time
                    },
                    "business": {
                        "cost_savings_percent": cost_savings_percent,
                        "business_score": business_score,
                        "scaling_capacity": models_can_fit,
                        "daily_capacity": daily_capacity
                    },
                    "content_performance": content_type_performance,
                    "mlflow_run_id": run.info.run_id,
                    "success": True
                }
                
            except Exception as e:
                mlflow.log_param("error", str(e))
                mlflow.set_tag("status", "failed")
                logger.error(f"❌ {display_name} unified test failed: {e}")
                return {"success": False, "error": str(e), "model_config": model_config}
    
    def _assess_business_quality(self, prompt: str, content: str, content_type: str) -> float:
        """Standardized business content quality assessment."""
        if not content or len(content.strip()) < 5:
            return 0.0
        
        score = 5.0  # Base score
        words = content.split()
        
        # === LENGTH APPROPRIATENESS ===
        if content_type == "twitter_content":
            # Twitter: 20-100 words optimal
            if 20 <= len(words) <= 100:
                score += 2.0
            elif len(words) < 10:
                score -= 3.0
        elif content_type in ["linkedin_content", "business_content"]:
            # Professional: 50-150 words optimal
            if 50 <= len(words) <= 150:
                score += 2.0
            elif len(words) < 25:
                score -= 2.0
        elif content_type == "technical_content":
            # Technical: 60-200 words optimal
            if 60 <= len(words) <= 200:
                score += 2.0
            elif len(words) < 30:
                score -= 2.0
        
        # === BUSINESS VOCABULARY ===
        business_terms = [
            "optimization", "strategy", "implementation", "solution",
            "performance", "efficiency", "deployment", "scalable"
        ]
        business_term_count = sum(1 for term in business_terms if term in content.lower())
        score += min(2.0, business_term_count * 0.5)
        
        # === COHERENCE CHECK ===
        if ". " in content or ":" in content:  # Has sentence structure
            score += 1.0
        
        return min(10.0, max(0.0, score))
    
    async def run_unified_comparison(self) -> Dict[str, Any]:
        """Run unified comparison of all models."""
        print("🚀 UNIFIED MODEL COMPARISON - CONSISTENT METHODOLOGY")
        print("=" * 70)
        print(f"📋 Testing {len(self.models_to_test)} models with {sum(len(prompts) for prompts in self.business_test_suite.values())} standardized prompts")
        print("")
        
        all_results = []
        successful_tests = []
        
        for model_config in self.models_to_test:
            try:
                result = await self.test_model_unified_methodology(model_config)
                all_results.append(result)
                
                if result.get("success"):
                    successful_tests.append(result)
                    
            except Exception as e:
                logger.error(f"Failed to test {model_config['display_name']}: {e}")
                all_results.append({"success": False, "error": str(e), "model_config": model_config})
        
        # === CREATE BUSINESS COMPARISON SUMMARY ===
        if successful_tests:
            await self._create_unified_comparison_summary(successful_tests)
        
        print(f"\\n🏆 UNIFIED COMPARISON COMPLETE")
        print("=" * 70)
        print(f"✅ Models tested: {len(successful_tests)}/{len(self.models_to_test)}")
        print("✅ Consistent methodology applied")
        print("✅ All data logged to MLflow")
        print("✅ Business comparison dashboard ready")
        print("")
        print("🔗 View results: mlflow ui --backend-store-uri ./unified_model_comparison")
        
        return {
            "experiment_name": self.experiment_name,
            "models_tested": len(successful_tests),
            "total_models": len(self.models_to_test),
            "results": all_results,
            "mlflow_tracking_uri": mlflow.get_tracking_uri()
        }
    
    async def _create_unified_comparison_summary(self, successful_tests: List[Dict[str, Any]]):
        """Create unified comparison summary in MLflow."""
        with mlflow.start_run(run_name="unified_comparison_summary"):
            # === COMPARISON METADATA ===
            mlflow.log_param("summary_type", "unified_model_comparison")
            mlflow.log_param("models_compared", len(successful_tests))
            mlflow.log_param("methodology", "standardized_business_testing")
            
            # === PERFORMANCE COMPARISON ===
            latencies = [t["performance"]["latency_ms"] for t in successful_tests]
            qualities = [t["performance"]["quality_score"] for t in successful_tests]
            throughputs = [t["performance"]["tokens_per_second"] for t in successful_tests]
            memories = [t["performance"]["memory_gb"] for t in successful_tests]
            business_scores = [t["business"]["business_score"] for t in successful_tests]
            
            # Best performers
            best_latency = min(latencies)
            best_quality = max(qualities)
            best_throughput = max(throughputs)
            best_memory_efficiency = min(memories)
            best_business_score = max(business_scores)
            
            mlflow.log_metric("comparison_best_latency_ms", best_latency)
            mlflow.log_metric("comparison_best_quality", best_quality)
            mlflow.log_metric("comparison_best_throughput_tps", best_throughput)
            mlflow.log_metric("comparison_best_memory_gb", best_memory_efficiency)
            mlflow.log_metric("comparison_best_business_score", best_business_score)
            
            # === BUSINESS RECOMMENDATIONS ===
            # Find winners by category
            speed_winner = min(successful_tests, key=lambda x: x["performance"]["latency_ms"])
            quality_winner = max(successful_tests, key=lambda x: x["performance"]["quality_score"])
            efficiency_winner = min(successful_tests, key=lambda x: x["performance"]["memory_gb"])
            
            mlflow.log_param("speed_champion", speed_winner["model_config"]["display_name"])
            mlflow.log_param("quality_champion", quality_winner["model_config"]["display_name"])
            mlflow.log_param("efficiency_champion", efficiency_winner["model_config"]["display_name"])
            
            # === PORTFOLIO TAGS ===
            mlflow.set_tag("portfolio_artifact", "unified_model_comparison")
            mlflow.set_tag("business_ready", "yes")
            mlflow.set_tag("interview_demo", "comprehensive_analysis")
            
            logger.info("✅ Unified comparison summary logged to MLflow")


async def main():
    """Run unified model testing."""
    tester = UnifiedModelTester()
    
    try:
        results = await tester.run_unified_comparison()
        
        print("\\n🎉 UNIFIED TESTING COMPLETE!")
        print("💼 Professional model comparison ready")
        print("📊 Consistent business data in MLflow")
        print("🎯 Portfolio-ready experiment tracking")
        
    except Exception as e:
        logger.error(f"❌ Unified testing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())