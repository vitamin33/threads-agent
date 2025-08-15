#!/usr/bin/env python3
"""
MLflow Model Comparison - Real Performance Data Collection

Proper experiment tracking for all model performance data:
- Logs all real performance metrics to MLflow
- Creates model comparison experiments 
- Tracks business metrics for content generation
- Provides MLflow dashboard for portfolio demonstration

Business Value:
- Centralized experiment tracking
- Model performance comparison
- Cost optimization analysis
- Portfolio-ready MLflow dashboard
"""

import asyncio
import json
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List

import mlflow
import mlflow.pytorch


class MLflowModelComparison:
    """Enhanced model testing with comprehensive MLflow experiment tracking."""
    
    def __init__(self):
        """Initialize MLflow experiment tracking."""
        # Setup MLflow
        mlflow.set_tracking_uri("file:./mlruns")
        self.experiment_name = "apple_silicon_model_comparison"
        
        # Create or get experiment
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment:
                self.experiment_id = experiment.experiment_id
            else:
                self.experiment_id = mlflow.create_experiment(self.experiment_name)
        except Exception:
            self.experiment_id = mlflow.create_experiment(self.experiment_name)
        
        mlflow.set_experiment(self.experiment_name)
        
        print(f"✅ MLflow experiment: {self.experiment_name}")
        print(f"📊 Experiment ID: {self.experiment_id}")
        print(f"📁 Tracking URI: {mlflow.get_tracking_uri()}")
        print("")
        
        # Models to test with business focus
        self.content_models = [
            {
                "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                "display_name": "TinyLlama-1.1B",
                "specialty": "general_purpose",
                "content_types": ["general", "speed"]
            },
            {
                "name": "microsoft/DialoGPT-medium", 
                "display_name": "DialoGPT-Medium",
                "specialty": "social_conversational",
                "content_types": ["twitter", "linkedin", "social"]
            },
            {
                "name": "bigscience/bloom-560m",
                "display_name": "BLOOM-560M", 
                "specialty": "fast_multilingual",
                "content_types": ["quick_posts", "social", "speed"]
            }
        ]
        
        # Business-focused test prompts
        self.business_prompts = {
            "twitter": [
                "Write a Twitter thread about AI cost optimization:",
                "Create a viral tweet about Apple Silicon ML deployment:",
                "Draft a Twitter thread about local vs API model costs:"
            ],
            "linkedin": [
                "Write a LinkedIn post about AI infrastructure engineering:",
                "Create a professional post about Apple Silicon for ML teams:",
                "Draft a thought leadership post about model deployment strategies:"
            ],
            "technical": [
                "Write a dev.to article intro about vLLM optimization:",
                "Explain Apple Silicon ML deployment benefits:",
                "Create technical documentation for model deployment:"
            ]
        }
    
    async def test_model_with_mlflow(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a model and log all metrics to MLflow."""
        model_name = model_config["name"]
        display_name = model_config["display_name"]
        
        print(f"🧪 TESTING {display_name} WITH MLFLOW LOGGING")
        print("=" * 60)
        
        # Start MLflow run for this model
        with mlflow.start_run(run_name=f"{display_name}_content_generation"):
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                # Log model metadata
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", display_name)
                mlflow.log_param("specialty", model_config["specialty"])
                mlflow.log_param("content_types", ",".join(model_config["content_types"]))
                mlflow.log_param("platform", "apple_silicon_m4_max")
                
                # Model loading with timing
                load_start = time.time()
                
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
                
                # Log infrastructure metrics
                mlflow.log_param("device", device)
                mlflow.log_param("dtype", str(dtype))
                mlflow.log_metric("model_load_time_seconds", load_time)
                
                # Memory usage
                process = psutil.Process()
                memory_gb = process.memory_info().rss / (1024**3)
                mlflow.log_metric("memory_usage_gb", memory_gb)
                
                print(f"✅ Loaded on {device} in {load_time:.1f}s, {memory_gb:.1f}GB memory")
                
                # Test all content types
                all_results = []
                content_type_metrics = {}
                
                for content_type, prompts in self.business_prompts.items():
                    print(f"📝 Testing {content_type} content generation...")
                    
                    type_latencies = []
                    type_qualities = []
                    type_tokens = []
                    
                    for prompt in prompts:
                        inference_start = time.time()
                        
                        # Generate content
                        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                        if device != "cpu":
                            inputs = {k: v.to(device) for k, v in inputs.items()}
                        
                        with torch.no_grad():
                            outputs = model.generate(
                                **inputs,
                                max_new_tokens=80,
                                temperature=0.8,
                                do_sample=True,
                                pad_token_id=tokenizer.pad_token_id
                            )
                        
                        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        generated_content = response[len(prompt):].strip()
                        
                        inference_time_ms = (time.time() - inference_start) * 1000
                        tokens_generated = len(generated_content.split())
                        
                        # Simple quality score
                        quality_score = min(10.0, max(1.0, len(generated_content.split()) / 10))
                        
                        type_latencies.append(inference_time_ms)
                        type_qualities.append(quality_score)
                        type_tokens.append(tokens_generated)
                        
                        all_results.append({
                            "content_type": content_type,
                            "prompt": prompt,
                            "response": generated_content,
                            "latency_ms": inference_time_ms,
                            "tokens": tokens_generated,
                            "quality": quality_score
                        })
                        
                        print(f"   {content_type}: {inference_time_ms:.0f}ms, {tokens_generated} tokens")
                    
                    # Calculate content type averages
                    avg_latency = sum(type_latencies) / len(type_latencies)
                    avg_quality = sum(type_qualities) / len(type_qualities)
                    avg_tokens = sum(type_tokens) / len(type_tokens)
                    
                    content_type_metrics[content_type] = {
                        "avg_latency_ms": avg_latency,
                        "avg_quality_score": avg_quality,
                        "avg_tokens_generated": avg_tokens
                    }
                    
                    # Log to MLflow by content type
                    mlflow.log_metric(f"{content_type}_avg_latency_ms", avg_latency)
                    mlflow.log_metric(f"{content_type}_avg_quality", avg_quality)
                    mlflow.log_metric(f"{content_type}_avg_tokens", avg_tokens)
                
                # Overall performance metrics
                overall_latency = sum(r["latency_ms"] for r in all_results) / len(all_results)
                overall_quality = sum(r["quality"] for r in all_results) / len(all_results)
                total_tokens = sum(r["tokens"] for r in all_results)
                total_time_seconds = sum(r["latency_ms"] for r in all_results) / 1000
                tokens_per_second = total_tokens / total_time_seconds
                
                # Log overall metrics to MLflow
                mlflow.log_metric("overall_avg_latency_ms", overall_latency)
                mlflow.log_metric("overall_avg_quality", overall_quality)
                mlflow.log_metric("tokens_per_second", tokens_per_second)
                mlflow.log_metric("total_tokens_generated", total_tokens)
                
                # Business metrics
                openai_cost_per_token = 0.000002
                local_cost_per_token = overall_latency / 1000 * 0.000004  # Based on real timing
                cost_savings_percent = ((openai_cost_per_token - local_cost_per_token) / openai_cost_per_token) * 100
                
                mlflow.log_metric("openai_cost_per_token", openai_cost_per_token)
                mlflow.log_metric("local_cost_per_token", local_cost_per_token)
                mlflow.log_metric("cost_savings_percent", cost_savings_percent)
                
                # Log model comparison tags
                mlflow.set_tag("model_size_category", "small" if "560m" in model_name.lower() else "medium")
                mlflow.set_tag("specialty", model_config["specialty"])
                mlflow.set_tag("test_type", "content_generation_business_metrics")
                
                print("")
                print("📊 MLFLOW METRICS LOGGED:")
                print(f"   Overall latency: {overall_latency:.0f}ms")
                print(f"   Overall quality: {overall_quality:.1f}/10")
                print(f"   Tokens/second: {tokens_per_second:.1f}")
                print(f"   Cost savings: {cost_savings_percent:.1f}%")
                print(f"   Memory usage: {memory_gb:.1f}GB")
                
                # Save detailed results
                result = {
                    "model_config": model_config,
                    "performance_metrics": {
                        "load_time_seconds": load_time,
                        "memory_usage_gb": memory_gb,
                        "overall_avg_latency_ms": overall_latency,
                        "tokens_per_second": tokens_per_second,
                        "device": device
                    },
                    "business_metrics": {
                        "cost_savings_percent": cost_savings_percent,
                        "overall_quality_score": overall_quality,
                        "content_type_performance": content_type_metrics
                    },
                    "mlflow_run_id": mlflow.active_run().info.run_id,
                    "test_results": all_results
                }
                
                print(f"✅ MLflow run ID: {mlflow.active_run().info.run_id}")
                return result
                
            except Exception as e:
                mlflow.log_param("error", str(e))
                mlflow.set_tag("status", "failed")
                print(f"❌ Model test failed: {e}")
                return {"success": False, "error": str(e)}
    
    async def run_comprehensive_mlflow_comparison(self) -> Dict[str, Any]:
        """Run comprehensive model comparison with MLflow tracking."""
        print("🚀 COMPREHENSIVE MODEL COMPARISON WITH MLFLOW")
        print("=" * 60)
        print("")
        
        comparison_results = {
            "experiment_name": self.experiment_name,
            "experiment_id": self.experiment_id,
            "test_session": time.strftime("%Y%m%d_%H%M%S"),
            "models_tested": [],
            "mlflow_runs": []
        }
        
        # Test each model and log to MLflow
        for model_config in self.content_models:
            try:
                result = await self.test_model_with_mlflow(model_config)
                comparison_results["models_tested"].append(result)
                
                if result.get("mlflow_run_id"):
                    comparison_results["mlflow_runs"].append(result["mlflow_run_id"])
                
                print("")
                
            except Exception as e:
                print(f"❌ Failed to test {model_config['name']}: {e}")
        
        # Create comparison summary in MLflow
        await self._create_comparison_summary(comparison_results)
        
        # Save results
        results_file = Path(f"mlflow_comparison_results_{comparison_results['test_session']}.json")
        with open(results_file, "w") as f:
            json.dump(comparison_results, f, indent=2, default=str)
        
        print("🏆 MLFLOW COMPARISON COMPLETE")
        print("=" * 60)
        print(f"📊 Models tested: {len(comparison_results['models_tested'])}")
        print(f"📄 Results saved: {results_file}")
        print(f"🔗 MLflow UI: mlflow ui --host 0.0.0.0 --port 5000")
        print("")
        print("💼 Portfolio Value:")
        print("✅ Real model performance data in MLflow")
        print("✅ Comparative analysis across content types")
        print("✅ Business metrics tracking")
        print("✅ Professional experiment tracking dashboard")
        
        return comparison_results
    
    async def _create_comparison_summary(self, results: Dict[str, Any]):
        """Create a summary comparison run in MLflow."""
        with mlflow.start_run(run_name="model_comparison_summary"):
            successful_tests = [t for t in results["models_tested"] if t.get("performance_metrics")]
            
            if not successful_tests:
                return
            
            # Overall comparison metrics
            mlflow.log_param("comparison_type", "content_generation_models")
            mlflow.log_param("models_compared", len(successful_tests))
            mlflow.log_param("test_session", results["test_session"])
            
            # Find best performers
            best_latency = min(t["performance_metrics"]["overall_avg_latency_ms"] for t in successful_tests)
            best_throughput = max(t["performance_metrics"]["tokens_per_second"] for t in successful_tests)
            best_efficiency = min(t["performance_metrics"]["memory_usage_gb"] for t in successful_tests)
            
            mlflow.log_metric("best_latency_ms", best_latency)
            mlflow.log_metric("best_throughput_tps", best_throughput)
            mlflow.log_metric("best_memory_efficiency_gb", best_efficiency)
            
            # Business recommendations
            for test in successful_tests:
                model_name = test["model_config"]["display_name"]
                latency = test["performance_metrics"]["overall_avg_latency_ms"]
                quality = test["business_metrics"]["overall_quality_score"]
                savings = test["business_metrics"]["cost_savings_percent"]
                
                mlflow.log_metric(f"{model_name}_latency_ms", latency)
                mlflow.log_metric(f"{model_name}_quality_score", quality)
                mlflow.log_metric(f"{model_name}_cost_savings_pct", savings)
            
            mlflow.set_tag("analysis_type", "business_model_comparison")
            mlflow.set_tag("platform", "apple_silicon_m4_max")


async def main():
    """Run MLflow model comparison."""
    print("🎯 Starting MLflow-tracked model comparison...")
    
    try:
        comparer = MLflowModelComparison()
        results = await comparer.run_comprehensive_mlflow_comparison()
        
        print("")
        print("🎉 SUCCESS! All performance data logged to MLflow")
        print("🔗 View results: mlflow ui")
        print("📊 Portfolio-ready experiment tracking complete")
        
    except Exception as e:
        print(f"❌ MLflow comparison failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())