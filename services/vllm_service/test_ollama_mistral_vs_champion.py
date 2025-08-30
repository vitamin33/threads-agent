#!/usr/bin/env python3
"""
Ollama Mistral vs Champion Test - Mac-Native Optimization

Testing Mistral-7B via Ollama against our validated champion OPT-2.7B:
- Mac-native Ollama optimization vs manual HuggingFace optimization
- Quantized 4.4GB vs unquantized 19.8GB memory comparison
- 7B parameters vs 2.7B parameters quality comparison
- HTTP API vs PyTorch inference performance comparison

Goal: Validate if Mac-native Ollama approach beats our manual optimization
Current champion: OPT-2.7B (8.40 ± 0.78/10)
"""

import asyncio
import json
import statistics
import time
import requests
from datetime import datetime

import mlflow


async def test_ollama_mistral_vs_champion():
    """Test Ollama Mistral against OPT-2.7B champion."""
    
    mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
    mlflow.set_experiment("rigorous_statistical_validation")
    
    run_name = f"ollama_mistral_vs_champion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with mlflow.start_run(run_name=run_name) as run:
        try:
            # Log Ollama vs Champion comparison metadata
            mlflow.log_param("model_name", "mistral:latest")
            mlflow.log_param("display_name", "Mistral-7B-Ollama")
            mlflow.log_param("optimization_approach", "ollama_mac_native")
            mlflow.log_param("vs_champion", "OPT-2.7B_8.40_quality")
            mlflow.log_param("memory_comparison", "4.4GB_vs_19.8GB")
            mlflow.log_param("api_type", "ollama_http_api")
            
            print("🏆 OLLAMA MISTRAL VS CHAMPION COMPARISON")
            print("=" * 60)
            print("🥇 Current Champion: OPT-2.7B (8.40 ± 0.78/10)")
            print("🥊 Challenger: Mistral-7B via Ollama (Mac-native)")
            print("💾 Memory: 4.4GB (Ollama) vs 19.8GB (HuggingFace)")
            print("🎯 Test: Business content quality comparison")
            print("")
            
            # Check Ollama API availability
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code != 200:
                    raise Exception("Ollama API not responding")
                
                models = response.json().get("models", [])
                mistral_available = any("mistral" in model["name"] for model in models)
                
                if not mistral_available:
                    raise Exception("Mistral model not found in Ollama")
                
                print("✅ Ollama API ready, Mistral model available")
                
            except Exception as e:
                print(f"❌ Ollama setup issue: {e}")
                mlflow.log_param("error", f"ollama_setup_{e}")
                return {"success": False, "error": str(e)}
            
            # === BUSINESS CONTENT QUALITY COMPARISON ===
            print("\\n🧪 Business Content Quality Testing (Ollama vs Champion):")
            
            # Same business prompts as rigorous testing for fair comparison
            comparison_prompts = [
                "Write a LinkedIn post about AI cost optimization that attracts consulting leads:",
                "Create professional content about Apple Silicon ML deployment for business:",
                "Draft thought leadership about local model deployment advantages:",
                "Write a LinkedIn article about AI infrastructure optimization success:",
                "Create content about enterprise AI cost reduction strategies:",
                "Draft professional content about ML deployment achievements:",
                "Write strategic content about AI competitive advantages:",
                "Create LinkedIn content about technical leadership in AI:",
                "Draft professional content about AI implementation results:",
                "Write thought leadership about ML infrastructure strategy:"
            ]
            
            mistral_qualities = []
            mistral_latencies = []
            successful_tests = 0
            
            for i, prompt in enumerate(comparison_prompts, 1):
                print(f"   Test {i:2d}/10: {prompt[:50]}...")
                
                try:
                    inference_start = time.time()
                    
                    # Ollama HTTP API call
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "mistral:latest",
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.8,
                                "top_p": 0.9,
                                "num_predict": 120
                            }
                        },
                        timeout=60
                    )
                    
                    inference_time = (time.time() - inference_start) * 1000
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result.get("response", "").strip()
                        
                        # Same quality assessment as champion testing
                        business_quality = assess_business_quality_comparison(content)
                        
                        mistral_qualities.append(business_quality)
                        mistral_latencies.append(inference_time)
                        successful_tests += 1
                        
                        print(f"      ✅ {inference_time:.0f}ms, Quality: {business_quality:.1f}/10")
                    else:
                        print(f"      ❌ API error: {response.status_code}")
                        
                except Exception as e:
                    print(f"      ❌ Test {i} failed: {e}")
            
            # === CHAMPION COMPARISON ANALYSIS ===
            if mistral_qualities:
                mistral_quality = statistics.mean(mistral_qualities)
                std_quality = statistics.stdev(mistral_qualities) if len(mistral_qualities) > 1 else 0
                confidence_interval = 1.96 * (std_quality / (len(mistral_qualities) ** 0.5))
                mistral_latency = statistics.mean(mistral_latencies)
                success_rate = successful_tests / len(comparison_prompts)
                
                # Compare with OPT-2.7B champion
                champion_quality = 8.40
                quality_difference = mistral_quality - champion_quality
                improvement_percent = (quality_difference / champion_quality) * 100
                
                # Log comprehensive comparison metrics
                mlflow.log_metric("ollama_mistral_quality", mistral_quality)
                mlflow.log_metric("ollama_confidence_interval", confidence_interval)
                mlflow.log_metric("ollama_mean_latency", mistral_latency)
                mlflow.log_metric("ollama_success_rate", success_rate)
                mlflow.log_metric("ollama_vs_champion_difference", quality_difference)
                mlflow.log_metric("ollama_improvement_percent", improvement_percent)
                
                # Optimization comparison
                mlflow.log_metric("memory_efficiency_vs_champion", (19.8 - 4.4) / 19.8 * 100)  # 77% reduction
                
                # Championship decision
                if mistral_quality > champion_quality and success_rate >= 0.8:
                    championship_result = "ollama_mistral_new_champion"
                    recommendation = "upgrade_to_ollama_mistral"
                elif mistral_quality >= 8.0:
                    championship_result = "ollama_mistral_excellent_alternative"
                    recommendation = "either_mistral_or_opt_excellent"
                else:
                    championship_result = "opt_2_7b_maintains_championship"
                    recommendation = "continue_with_opt_2_7b"
                
                mlflow.set_tag("ollama_championship_result", championship_result)
                mlflow.set_tag("ollama_recommendation", recommendation)
                mlflow.set_tag("optimization_comparison", "ollama_vs_manual")
                
                print(f"\\n🏆 OLLAMA MISTRAL VS CHAMPION RESULTS:")
                print("=" * 70)
                print(f"📊 Mistral Quality: {mistral_quality:.2f} ± {confidence_interval:.2f}")
                print(f"🥇 OPT-2.7B Champion: {champion_quality:.2f} ± 0.78")
                print(f"📈 Quality Difference: {quality_difference:+.2f} points ({improvement_percent:+.1f}%)")
                print(f"⚡ Mistral Latency: {mistral_latency:.0f}ms (Ollama)")
                print(f"💾 Memory Efficiency: 77% reduction (4.4GB vs 19.8GB)")
                print(f"🔧 Success Rate: {success_rate:.1%}")
                print(f"🏆 Championship: {championship_result}")
                print(f"💼 Recommendation: {recommendation}")
                
                # Final decision announcement
                if mistral_quality > champion_quality:
                    print("\\n🎉 NEW CHAMPION: OLLAMA MISTRAL!")
                    print("✅ Mac-native optimization delivers superior results")
                    print("💾 77% memory reduction with better quality")
                elif mistral_quality >= 8.0:
                    print("\\n✅ EXCELLENT ALTERNATIVE!")
                    print("Both Ollama Mistral and OPT-2.7B excellent for business")
                else:
                    print("\\n📊 OPT-2.7B MAINTAINS CHAMPIONSHIP")
                    print("Manual optimization approach validated")
                
                return {
                    "mistral_quality": mistral_quality,
                    "vs_champion": quality_difference,
                    "memory_efficiency": 77.0,
                    "championship_result": championship_result,
                    "success": True
                }
            else:
                return {"success": False, "error": "no_successful_tests"}
                
        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"❌ Ollama Mistral test failed: {e}")
            return {"success": False, "error": str(e)}


def assess_business_quality_comparison(content: str) -> float:
    """Same quality assessment as champion testing for fair comparison."""
    if not content or len(content.strip()) < 30:
        return 0.0
    
    score = 5.0
    words = content.split()
    
    # Professional business length
    if 100 <= len(words) <= 250:
        score += 3.0
    elif 80 <= len(words) < 100:
        score += 2.0
    elif len(words) < 50:
        score -= 2.0
    
    # Business vocabulary (same criteria as champion)
    business_terms = [
        "optimization", "strategy", "implementation", "professional",
        "enterprise", "competitive", "advantage", "scalable"
    ]
    term_count = sum(1 for term in business_terms if term in content.lower())
    score += min(2.0, term_count * 0.3)
    
    return min(10.0, max(0.0, score))


async def main():
    """Test Ollama Mistral vs OPT-2.7B champion."""
    print("🥊 OLLAMA MISTRAL VS OPT-2.7B CHAMPIONSHIP MATCH")
    print("=" * 70)
    print("🥇 Champion: OPT-2.7B (8.40 ± 0.78/10, 19.8GB)")
    print("🥊 Challenger: Mistral-7B (Ollama, 4.4GB)")
    print("🎯 Goal: Test Mac-native vs manual optimization")
    print("")
    
    try:
        results = await test_ollama_mistral_vs_champion()
        
        if results.get("success"):
            quality = results["mistral_quality"]
            vs_champion = results["vs_champion"]
            
            print("\\n🎉 OLLAMA MISTRAL TESTING COMPLETE!")
            print(f"📊 Quality: {quality:.2f}/10")
            print(f"📈 vs Champion: {vs_champion:+.2f} points")
            print(f"💾 Memory efficiency: {results['memory_efficiency']:.0f}% reduction")
            
            if quality > 8.40:
                print("\\n🥇 NEW CHAMPION: OLLAMA MISTRAL!")
            else:
                print("\\n📊 Championship comparison complete")
                
        print("\\n🔗 All results: http://127.0.0.1:5000")
        
    except Exception as e:
        print(f"❌ Championship test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())