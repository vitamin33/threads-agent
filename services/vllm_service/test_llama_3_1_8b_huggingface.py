#!/usr/bin/env python3
"""
Llama-3.1-8B HuggingFace Testing - Ultimate Quality Challenge

Testing meta-llama/Llama-3.1-8B-Instruct via our proven HuggingFace approach:
- 8B parameters (3x larger than OPT-2.7B champion)
- Manual Apple Silicon optimization (proven superior to Ollama)
- Expected 8.5-9.5/10 quality (highest potential)
- Memory: ~20GB (should fit M4 Max with careful management)

Goal: Find the ultimate quality leader for business content
Strategy: Use our proven manual optimization approach
"""

import asyncio
import statistics
import time
import psutil
import gc
from datetime import datetime

import mlflow


async def test_llama_3_1_8b_ultimate_quality():
    """Test Llama-3.1-8B for ultimate business content quality."""
    
    mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
    mlflow.set_experiment("rigorous_statistical_validation")
    
    run_name = f"ultimate_llama_3_1_8b_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with mlflow.start_run(run_name=run_name) as run:
        try:
            model_name = "meta-llama/Llama-3.1-8B-Instruct"
            
            # Log ultimate quality challenge metadata
            mlflow.log_param("model_name", model_name)
            mlflow.log_param("display_name", "Llama-3.1-8B-Ultimate")
            mlflow.log_param("model_size", "8B_parameters")
            mlflow.log_param("optimization_approach", "proven_manual_huggingface")
            mlflow.log_param("challenge_goal", "ultimate_quality_8_5_to_9_5")
            mlflow.log_param("vs_current_champion", "OPT_2_7B_8_40_quality")
            mlflow.log_param("memory_strategy", "careful_m4_max_management")
            
            print("🔥 LLAMA-3.1-8B ULTIMATE QUALITY CHALLENGE")
            print("=" * 60)
            print("🎯 Goal: Find ultimate quality leader (8.5-9.5/10)")
            print("📊 Model: 8B parameters (3x larger than OPT-2.7B)")
            print("🏆 Current champion: OPT-2.7B (8.40 ± 0.78/10)")
            print("🔧 Approach: Proven manual optimization (superior to Ollama)")
            print("")
            
            # === MEMORY PREPARATION ===
            print("Stage 1: 💾 Memory preparation for 8B model...")
            
            # Aggressive memory cleanup
            gc.collect()
            
            memory_before = psutil.virtual_memory()
            available_gb = memory_before.available / (1024**3)
            
            print(f"   📊 Available memory: {available_gb:.1f}GB")
            
            if available_gb < 20.0:
                print(f"   ⚠️  Limited memory - need careful management")
                # Additional cleanup
                for _ in range(3):
                    gc.collect()
                memory_after_cleanup = psutil.virtual_memory()
                print(f"   📊 After cleanup: {memory_after_cleanup.available / (1024**3):.1f}GB")
            
            mlflow.log_metric("ultimate_available_memory_gb", available_gb)
            
            # === MODEL LOADING ===
            print("\\nStage 2: 🧠 Loading Llama-3.1-8B with proven optimization...")
            
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            load_start = time.time()
            
            try:
                # Load tokenizer first
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                print("   ✅ Tokenizer loaded")
                
                # Our proven Apple Silicon optimization
                device = "mps" if torch.backends.mps.is_available() else "cpu"
                
                print(f"   🍎 Using proven Apple Silicon optimization: {device}")
                
                # Load 8B model with memory optimization
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16,  # Essential for 8B model
                    device_map=device if device != "cpu" else None,
                    low_cpu_mem_usage=True,
                    trust_remote_code=True  # May be needed for Llama
                )
                
                if device != "cpu":
                    model = model.to(device)
                
                load_time = time.time() - load_start
                
                # Memory validation
                memory_after = psutil.virtual_memory()
                model_memory_gb = (memory_before.available - memory_after.available) / (1024**3)
                
                mlflow.log_metric("ultimate_load_time", load_time)
                mlflow.log_metric("ultimate_model_memory_gb", model_memory_gb)
                mlflow.log_param("ultimate_device", device)
                
                print(f"   ✅ Llama-3.1-8B loaded successfully!")
                print(f"   ⏱️  Load time: {load_time:.1f}s")
                print(f"   💾 Memory used: {model_memory_gb:.1f}GB")
                print(f"   📊 Remaining: {memory_after.available / (1024**3):.1f}GB")
                
                if model_memory_gb > 22.0:
                    print(f"   ⚠️  High memory usage - monitoring carefully")
                
            except Exception as e:
                print(f"   ❌ 8B model loading failed: {e}")
                mlflow.log_param("ultimate_error", f"loading_failed_{e}")
                return {"success": False, "error": f"loading_failed_{e}"}
            
            # === ULTIMATE QUALITY TESTING ===
            print("\\nStage 3: 🏆 Ultimate business content quality testing...")
            
            ultimate_prompts = [
                "Write a LinkedIn thought leadership post about 'AI Infrastructure Cost Optimization: Real Enterprise Results' that attracts high-value consulting opportunities:",
                "Create compelling professional content about 'Apple Silicon ML Deployment: Competitive Advantage Analysis' that establishes technical authority:",
                "Draft a strategic business communication about 'Multi-Model AI Architecture: Performance and Cost Benefits' that wins enterprise contracts:",
                "Write authoritative technical content about 'Local AI Deployment: ROI Analysis and Implementation Strategy' that demonstrates expertise:",
                "Create executive-level communication about 'AI Cost Reduction: Methodology and Business Impact' that positions for leadership roles:",
                "Draft thought leadership content about 'Apple Silicon Optimization: Real Performance Results' that builds industry recognition:",
                "Write professional business content about 'MLflow Experiment Tracking: Enterprise Methodology' that showcases technical depth:",
                "Create strategic content about 'AI Infrastructure Transformation: Cost and Performance Analysis' that generates qualified leads:"
            ]
            
            ultimate_qualities = []
            ultimate_latencies = []
            
            print(f"   🧪 Testing {len(ultimate_prompts)} ultimate quality scenarios...")
            
            for i, prompt in enumerate(ultimate_prompts, 1):
                print(f"   Ultimate test {i}/8: {prompt[:55]}...")
                
                try:
                    inference_start = time.time()
                    
                    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                    if device != "cpu":
                        inputs = {k: v.to(device) for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=120,
                            temperature=0.7,  # Professional content
                            do_sample=True,
                            pad_token_id=tokenizer.pad_token_id
                        )
                    
                    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    content = response[len(prompt):].strip()
                    
                    inference_time = (time.time() - inference_start) * 1000
                    
                    # Ultimate quality assessment
                    ultimate_quality = assess_ultimate_business_quality(content)
                    
                    ultimate_qualities.append(ultimate_quality)
                    ultimate_latencies.append(inference_time)
                    
                    print(f"      ✅ {inference_time:.0f}ms, Quality: {ultimate_quality:.1f}/10")
                    
                except Exception as e:
                    print(f"      ❌ Test {i} failed: {e}")
            
            # === ULTIMATE QUALITY ANALYSIS ===
            if ultimate_qualities:
                llama_ultimate_quality = statistics.mean(ultimate_qualities)
                std_quality = statistics.stdev(ultimate_qualities) if len(ultimate_qualities) > 1 else 0
                confidence_interval = 1.96 * (std_quality / (len(ultimate_qualities) ** 0.5))
                llama_latency = statistics.mean(ultimate_latencies)
                
                # Compare with OPT-2.7B champion
                champion_quality = 8.40
                ultimate_improvement = llama_ultimate_quality - champion_quality
                improvement_percent = (ultimate_improvement / champion_quality) * 100
                
                # Log ultimate quality metrics
                mlflow.log_metric("ultimate_quality", llama_ultimate_quality)
                mlflow.log_metric("ultimate_confidence_interval", confidence_interval)
                mlflow.log_metric("ultimate_mean_latency", llama_latency)
                mlflow.log_metric("ultimate_vs_champion", ultimate_improvement)
                mlflow.log_metric("ultimate_improvement_percent", improvement_percent)
                
                # Ultimate quality decision
                if llama_ultimate_quality > champion_quality:
                    ultimate_result = "new_ultimate_quality_leader"
                    recommendation = "upgrade_to_llama_3_1_8b"
                elif llama_ultimate_quality >= 8.0:
                    ultimate_result = "excellent_quality_alternative"
                    recommendation = "either_llama_or_opt_excellent"
                else:
                    ultimate_result = "opt_2_7b_maintains_leadership"
                    recommendation = "continue_with_opt_2_7b"
                
                mlflow.set_tag("ultimate_result", ultimate_result)
                mlflow.set_tag("ultimate_recommendation", recommendation)
                
                print(f"\\n🔥 LLAMA-3.1-8B ULTIMATE QUALITY RESULTS:")
                print("=" * 70)
                print(f"🏆 Ultimate Quality: {llama_ultimate_quality:.2f} ± {confidence_interval:.2f}")
                print(f"🥇 OPT-2.7B Champion: {champion_quality:.2f} ± 0.78")
                print(f"📈 Quality Improvement: {ultimate_improvement:+.2f} points ({improvement_percent:+.1f}%)")
                print(f"⚡ Latency: {llama_latency:.0f}ms")
                print(f"💾 Memory: {model_memory_gb:.1f}GB")
                print(f"🏆 Result: {ultimate_result}")
                print(f"💼 Recommendation: {recommendation}")
                
                # Ultimate championship announcement
                if llama_ultimate_quality > champion_quality:
                    print("\\n🎉 NEW ULTIMATE CHAMPION: LLAMA-3.1-8B!")
                    print(f"✅ Quality improvement: {ultimate_improvement:+.2f} points")
                    print("🏆 Use Llama-3.1-8B for ultimate business content quality")
                elif llama_ultimate_quality >= 8.0:
                    print("\\n✅ EXCELLENT QUALITY ACHIEVED!")
                    print("Both Llama-3.1-8B and OPT-2.7B excellent for business")
                else:
                    print("\\n📊 OPT-2.7B MAINTAINS CHAMPIONSHIP")
                    print("Manual optimization validated across model sizes")
                
                return {
                    "ultimate_quality": llama_ultimate_quality,
                    "vs_champion": ultimate_improvement,
                    "ultimate_result": ultimate_result,
                    "memory_usage": model_memory_gb,
                    "success": True
                }
            else:
                return {"success": False, "error": "no_successful_ultimate_tests"}
                
        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"❌ Llama-3.1-8B ultimate test failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            # Aggressive cleanup for 8B model
            try:
                if 'model' in locals():
                    del model
                if 'tokenizer' in locals():
                    del tokenizer
                gc.collect()
                if 'device' in locals() and device == "mps":
                    torch.mps.empty_cache()
                print("   🧹 8B model memory cleanup completed")
            except Exception:
                pass


def assess_ultimate_business_quality(content: str) -> float:
    """Ultimate business content quality assessment."""
    if not content or len(content.strip()) < 40:
        return 0.0
    
    score = 5.0
    words = content.split()
    
    # Ultimate business content length
    if 120 <= len(words) <= 300:  # Ultimate professional length
        score += 3.0
    elif 100 <= len(words) < 120:
        score += 2.5
    elif len(words) < 60:
        score -= 2.0
    
    # Ultimate business vocabulary
    ultimate_terms = [
        "optimization", "strategy", "implementation", "architecture",
        "enterprise", "competitive", "advantage", "scalable",
        "demonstrated", "proven", "expertise", "leadership",
        "results", "achieved", "delivered", "validated"
    ]
    
    term_density = sum(1 for term in ultimate_terms if term in content.lower()) / len(words) * 100
    score += min(2.0, term_density * 25)  # Reward high professional vocabulary density
    
    return min(10.0, max(0.0, score))


async def main():
    """Test Llama-3.1-8B ultimate quality via HuggingFace."""
    print("🔥 LLAMA-3.1-8B ULTIMATE QUALITY CHALLENGE")
    print("=" * 70)
    print("🎯 Goal: Find ultimate quality leader for business content")
    print("📊 Model: 8B parameters (highest potential)")
    print("🔧 Method: Proven HuggingFace approach (superior to Ollama)")
    print("🏆 Benchmark: OPT-2.7B (8.40 ± 0.78/10)")
    print("")
    
    try:
        results = await test_llama_3_1_8b_ultimate_quality()
        
        if results.get("success"):
            quality = results["ultimate_quality"]
            improvement = results["vs_champion"]
            
            print("\\n🎉 LLAMA-3.1-8B ULTIMATE TESTING COMPLETE!")
            print(f"🔥 Ultimate quality: {quality:.2f}/10")
            print(f"📈 vs Champion: {improvement:+.2f} points")
            
            if quality > 8.40:
                print("\\n🥇 NEW ULTIMATE CHAMPION FOUND!")
            else:
                print("\\n📊 Ultimate quality results logged")
                
        print("\\n🔗 All results: http://127.0.0.1:5000")
        
    except Exception as e:
        print(f"❌ Ultimate quality test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())