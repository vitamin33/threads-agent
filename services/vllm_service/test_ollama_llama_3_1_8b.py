#!/usr/bin/env python3
"""
Ollama Llama-3.1-8B Testing - Mac-Native Quality Championship

Testing Llama-3.1-8B-Instruct via Ollama for business content quality:
- Mac-native optimization with Apple Silicon acceleration
- Quantized model (q4_K_M ≈ 4.9GB) for memory efficiency
- 8B parameters (3x larger than OPT-2.7B) for quality improvement
- HTTP API integration for production deployment

Goal: Test if Llama-3.1-8B can beat OPT-2.7B's 8.40/10 quality
Expected: 8.5-9.5/10 quality with Mac-native optimization
"""

import asyncio
import json
import statistics
import time
import requests
from datetime import datetime

import mlflow


class OllamaLlamaTester:
    """Test Llama-3.1-8B via Ollama for business content quality."""
    
    def __init__(self):
        """Initialize Ollama Llama tester."""
        self.model_name = "llama3.1:8b-instruct"
        self.ollama_api_url = "http://localhost:11434"
        self.current_champion_quality = 8.40  # OPT-2.7B validated
        
        # Use existing MLflow for comparison
        mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
        mlflow.set_experiment("rigorous_statistical_validation")
    
    def check_ollama_status(self):
        """Check if Ollama is running and model is available."""
        
        print("🔍 CHECKING OLLAMA STATUS")
        print("=" * 50)
        
        try:
            # Check Ollama API
            response = requests.get(f"{self.ollama_api_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                print(f"✅ Ollama API running: {len(models)} models available")
                
                if self.model_name in model_names:
                    print(f"✅ {self.model_name} already downloaded")
                    return True, "model_ready"
                else:
                    print(f"⚠️  {self.model_name} not found, need to download")
                    print(f"   Available models: {model_names}")
                    return True, "need_download"
            else:
                print(f"❌ Ollama API error: {response.status_code}")
                return False, "api_error"
                
        except requests.exceptions.ConnectionError:
            print("❌ Ollama not running or not accessible")
            print("💡 Start with: ollama serve")
            return False, "not_running"
        except Exception as e:
            print(f"❌ Ollama check failed: {e}")
            return False, "error"
    
    def download_llama_model(self):
        """Download Llama-3.1-8B via Ollama."""
        
        print("📦 DOWNLOADING LLAMA-3.1-8B VIA OLLAMA")
        print("=" * 50)
        print("🎯 Model: llama3.1:8b-instruct (q4_K_M quantized)")
        print("💾 Expected size: ~4.9GB (vs 19.8GB unquantized)")
        print("⏱️  Expected time: 5-15 minutes")
        print("")
        
        try:
            # Download via Ollama API
            print("⬇️  Starting download...")
            
            response = requests.post(
                f"{self.ollama_api_url}/api/pull",
                json={"name": self.model_name},
                stream=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if response.status_code == 200:
                # Monitor download progress
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "status" in data:
                                print(f"   {data['status']}")
                            if data.get("status") == "success":
                                print("✅ Download completed successfully!")
                                return True
                        except json.JSONDecodeError:
                            pass
                
                return True
            else:
                print(f"❌ Download failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    async def test_llama_business_quality_ollama(self):
        """Test Llama-3.1-8B business content quality via Ollama API."""
        
        run_name = f"ollama_llama_3_1_8b_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                # Log Ollama testing metadata
                mlflow.log_param("model_name", self.model_name)
                mlflow.log_param("display_name", "Llama-3.1-8B-Ollama")
                mlflow.log_param("model_size", "8B_parameters")
                mlflow.log_param("optimization", "ollama_mac_native_quantized")
                mlflow.log_param("quantization", "q4_K_M")
                mlflow.log_param("memory_footprint", "4.9GB_quantized")
                mlflow.log_param("challenge_target", "beat_opt_2_7b_8_40_quality")
                
                print("🚀 OLLAMA LLAMA-3.1-8B BUSINESS QUALITY TEST")
                print("=" * 60)
                print("🎯 Goal: Beat OPT-2.7B's 8.40/10 quality")
                print("🍎 Optimization: Mac-native Ollama with quantization")
                print("💾 Memory: 4.9GB (75% reduction vs unquantized)")
                print("")
                
                # Business content test prompts (same as rigorous testing)
                business_prompts = [
                    "Write a LinkedIn post about AI cost optimization that attracts consulting leads:",
                    "Create professional content about Apple Silicon ML deployment for business:",
                    "Draft thought leadership about local model deployment advantages:",
                    "Write a LinkedIn article about AI infrastructure optimization success:",
                    "Create content about enterprise AI cost reduction strategies:",
                    "Draft professional content about ML deployment achievements:",
                    "Write strategic content about AI competitive advantages:",
                    "Create LinkedIn content about technical leadership in AI:",
                    "Draft professional content about AI implementation results:",
                    "Write thought leadership about ML infrastructure strategy:",
                    "Create content about AI transformation success stories:",
                    "Draft LinkedIn content about technical innovation in AI:",
                    "Write professional content about AI deployment optimization:",
                    "Create strategic content about ML cost management:",
                    "Draft LinkedIn content about AI technical excellence:"
                ]
                
                print(f"📊 Testing with {len(business_prompts)} business prompts...")
                
                quality_scores = []
                latencies = []
                business_scores = []
                technical_scores = []
                successful_tests = 0
                
                for i, prompt in enumerate(business_prompts, 1):
                    print(f"   Test {i:2d}/15: {prompt[:50]}...")
                    
                    try:
                        inference_start = time.time()
                        
                        # Ollama API call
                        response = requests.post(
                            f"{self.ollama_api_url}/api/generate",
                            json={
                                "model": self.model_name,
                                "prompt": prompt,
                                "stream": False,
                                "options": {
                                    "temperature": 0.8,
                                    "top_p": 0.9,
                                    "num_predict": 120  # Max tokens
                                }
                            },
                            timeout=60  # 1 minute per inference
                        )
                        
                        inference_time = (time.time() - inference_start) * 1000
                        
                        if response.status_code == 200:
                            result = response.json()
                            content = result.get("response", "").strip()
                            
                            # Business quality assessment (same methodology)
                            business_quality = self._assess_ollama_business_quality(content)
                            technical_quality = self._assess_ollama_technical_quality(content)
                            composite_quality = (business_quality + technical_quality) / 2
                            
                            quality_scores.append(composite_quality)
                            latencies.append(inference_time)
                            business_scores.append(business_quality)
                            technical_scores.append(technical_quality)
                            successful_tests += 1
                            
                            print(f"      ✅ {inference_time:.0f}ms, Quality: {composite_quality:.1f}/10 (B:{business_quality:.1f} T:{technical_quality:.1f})")
                            
                        else:
                            print(f"      ❌ API error: {response.status_code}")
                            
                    except Exception as e:
                        print(f"      ❌ Test {i} failed: {e}")
                
                # === OLLAMA BUSINESS ANALYSIS ===
                if quality_scores:
                    llama_quality = statistics.mean(quality_scores)
                    std_quality = statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0
                    confidence_interval = 1.96 * (std_quality / (len(quality_scores) ** 0.5))
                    
                    llama_latency = statistics.mean(latencies)
                    business_rating = statistics.mean(business_scores)
                    technical_rating = statistics.mean(technical_scores)
                    success_rate = successful_tests / len(business_prompts)
                    
                    # Compare with current champion
                    vs_opt_improvement = llama_quality - self.current_champion_quality
                    improvement_percent = (vs_opt_improvement / self.current_champion_quality) * 100
                    
                    # Log Ollama metrics
                    mlflow.log_metric("ollama_validated_quality", llama_quality)
                    mlflow.log_metric("ollama_confidence_interval", confidence_interval)
                    mlflow.log_metric("ollama_business_rating", business_rating)
                    mlflow.log_metric("ollama_technical_rating", technical_rating)
                    mlflow.log_metric("ollama_success_rate", success_rate)
                    mlflow.log_metric("ollama_mean_latency", llama_latency)
                    mlflow.log_metric("ollama_vs_opt_improvement", vs_opt_improvement)
                    mlflow.log_metric("ollama_improvement_percent", improvement_percent)
                    
                    # Business recommendation
                    if llama_quality > self.current_champion_quality and success_rate >= 0.8:
                        recommendation = "new_ollama_champion"
                        business_tier = "ultimate_business_content"
                    elif llama_quality >= 8.0:
                        recommendation = "excellent_ollama_alternative"
                        business_tier = "enterprise_grade"
                    elif llama_quality >= 7.0:
                        recommendation = "good_ollama_option"
                        business_tier = "professional_grade"
                    else:
                        recommendation = "opt_2_7b_remains_champion"
                        business_tier = "moderate_grade"
                    
                    mlflow.set_tag("ollama_recommendation", recommendation)
                    mlflow.set_tag("ollama_business_tier", business_tier)
                    mlflow.set_tag("ollama_optimization", "mac_native_quantized")
                    
                    print(f"\\n🏆 OLLAMA LLAMA-3.1-8B BUSINESS RESULTS:")
                    print("=" * 70)
                    print(f"📊 Business Quality: {llama_quality:.2f} ± {confidence_interval:.2f} (95% CI)")
                    print(f"🏢 Business Rating: {business_rating:.2f}/10")
                    print(f"🔧 Technical Rating: {technical_rating:.2f}/10")
                    print(f"⚡ Latency: {llama_latency:.0f}ms (Mac-native)")
                    print(f"💾 Memory: ~4.9GB (quantized)")
                    print(f"🔧 Success Rate: {success_rate:.1%}")
                    print(f"📊 vs OPT-2.7B: {vs_opt_improvement:+.2f} points ({improvement_percent:+.1f}%)")
                    print(f"🏆 Recommendation: {recommendation}")
                    print(f"🎯 Business Tier: {business_tier}")
                    
                    # Championship announcement
                    if llama_quality > self.current_champion_quality:
                        print("\\n🎉 NEW QUALITY CHAMPION: OLLAMA LLAMA-3.1-8B!")
                        print("✅ Use Llama-3.1-8B for ultimate business content quality")
                        print("🍎 Mac-native optimization beats transformers approach")
                    else:
                        print("\\n📊 Ollama results logged for comparison")
                        
                    return {
                        "ollama_quality": llama_quality,
                        "vs_champion": vs_opt_improvement,
                        "business_tier": business_tier,
                        "recommendation": recommendation,
                        "success": True
                    }
                else:
                    return {"success": False, "error": "no_successful_inferences"}
                    
            except Exception as e:
                mlflow.log_param("error", str(e))
                print(f"❌ Ollama test failed: {e}")
                return {"success": False, "error": str(e)}
    
    def _assess_ollama_business_quality(self, content: str) -> float:
        """Assess business content quality (same methodology as rigorous testing)."""
        if not content or len(content.strip()) < 30:
            return 0.0
        
        score = 5.0
        words = content.split()
        
        # Professional business length
        if 100 <= len(words) <= 250:  # Business content optimal
            score += 3.0
        elif 80 <= len(words) < 100:
            score += 2.0
        elif len(words) < 50:
            score -= 2.0
        
        # Business vocabulary
        business_terms = [
            "optimization", "strategy", "implementation", "professional",
            "enterprise", "competitive", "advantage", "scalable"
        ]
        term_count = sum(1 for term in business_terms if term in content.lower())
        score += min(2.0, term_count * 0.3)
        
        return min(10.0, max(0.0, score))
    
    def _assess_ollama_technical_quality(self, content: str) -> float:
        """Assess technical content quality."""
        score = 5.0
        
        # Technical authority terms
        technical_terms = [
            "deployment", "architecture", "performance", "infrastructure",
            "demonstrated", "implemented", "optimized", "validated"
        ]
        
        term_count = sum(1 for term in technical_terms if term in content.lower())
        score += min(3.0, term_count * 0.4)
        
        # Apple Silicon specificity
        if any(term in content.lower() for term in ["apple silicon", "m4 max", "optimization"]):
            score += 2.0
        
        return min(10.0, score)


async def main():
    """Test Ollama Llama-3.1-8B for business content quality."""
    print("🚀 OLLAMA LLAMA-3.1-8B BUSINESS CONTENT TESTING")
    print("=" * 70)
    print("🎯 Goal: Test if 8B model beats OPT-2.7B's 8.40/10 quality")
    print("🍎 Advantage: Mac-native optimization + quantization")
    print("💾 Memory: 4.9GB (75% reduction vs unquantized)")
    print("")
    
    tester = OllamaLlamaTester()
    
    try:
        # Check Ollama status
        ollama_ready, status = tester.check_ollama_status()
        
        if not ollama_ready:
            if status == "not_running":
                print("💡 Please start Ollama: ollama serve")
                print("Then run: ollama pull llama3.1:8b-instruct")
            return
        
        if status == "need_download":
            print("📦 Need to download model first...")
            print("Run: ollama pull llama3.1:8b-instruct")
            print("Then re-run this test")
            return
        
        # Test business content quality
        results = await tester.test_llama_business_quality_ollama()
        
        if results.get("success"):
            quality = results["ollama_quality"]
            improvement = results["vs_champion"]
            tier = results["business_tier"]
            
            print("\\n🎉 OLLAMA LLAMA-3.1-8B TESTING COMPLETE!")
            print(f"🏆 Business quality: {quality:.2f}/10")
            print(f"📊 vs OPT-2.7B: {improvement:+.2f} points")
            print(f"🎯 Business tier: {tier}")
            
            if quality > 8.40:
                print("\\n🥇 NEW CHAMPION: OLLAMA LLAMA-3.1-8B!")
                print("✅ Mac-native optimization delivers superior quality")
            else:
                print("\\n📊 Results logged for comparison")
                
        print("\\n🔗 All results: http://127.0.0.1:5000")
        
    except Exception as e:
        print(f"❌ Ollama testing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())