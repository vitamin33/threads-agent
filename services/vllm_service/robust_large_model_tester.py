#!/usr/bin/env python3
"""
Robust Large Model Tester - Production-Grade Download and Testing

Handles large model downloads (2B+ parameters) with best practices:
- Background downloads with progress tracking
- Extended timeouts for large models
- Robust error handling and recovery
- MLflow logging with proper status tracking
- Apple Silicon optimization for large models

Models to test with robust approach:
- facebook/opt-2.7b (2.7B) - Quality challenger
- bigscience/bloom-3b (3B) - BLOOM family quality boost
"""

import asyncio
import logging
import time
import psutil
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import mlflow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RobustLargeModelTester:
    """Robust testing framework for large models with proper download management."""
    
    def __init__(self):
        """Initialize robust large model tester."""
        mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
        mlflow.set_experiment("complete_solopreneur_analysis")
        
        # Extended timeouts for large models
        self.download_timeout = 1800  # 30 minutes for download
        self.inference_timeout = 300   # 5 minutes per inference
        self.total_test_timeout = 2400  # 40 minutes total
        
        # Cache directory for pre-downloads
        self.model_cache = Path.home() / ".cache" / "robust_model_testing"
        self.model_cache.mkdir(parents=True, exist_ok=True)
        
        logger.info("Robust large model tester initialized")
    
    async def pre_download_model(self, model_name: str, display_name: str) -> bool:
        """Pre-download model with progress tracking."""
        print(f"📦 PRE-DOWNLOADING {display_name}")
        print("=" * 50)
        print(f"Model: {model_name}")
        print(f"Timeout: {self.download_timeout}s ({self.download_timeout/60:.0f} minutes)")
        print("")
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            # Pre-download tokenizer (fast)
            print("⬇️  Downloading tokenizer...")
            start_time = time.time()
            
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(self.model_cache)
            )
            
            tokenizer_time = time.time() - start_time
            print(f"✅ Tokenizer downloaded: {tokenizer_time:.1f}s")
            
            # Pre-download model (slow)
            print("⬇️  Downloading model weights (this may take 10-15 minutes)...")
            model_start = time.time()
            
            # Use asyncio timeout for long downloads
            try:
                model = await asyncio.wait_for(
                    asyncio.to_thread(
                        AutoModelForCausalLM.from_pretrained,
                        model_name,
                        cache_dir=str(self.model_cache),
                        torch_dtype="auto",
                        low_cpu_mem_usage=True
                    ),
                    timeout=self.download_timeout
                )
                
                model_time = time.time() - model_start
                total_time = time.time() - start_time
                
                print(f"✅ Model downloaded: {model_time:.1f}s")
                print(f"📊 Total download time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
                
                # Clean up model from memory after download
                del model
                
                return True
                
            except asyncio.TimeoutError:
                print(f"❌ Download timeout after {self.download_timeout}s")
                return False
                
        except Exception as e:
            print(f"❌ Pre-download failed: {e}")
            return False
    
    async def test_large_model_robust(self, model_name: str, display_name: str) -> Dict[str, Any]:
        """Test large model with robust error handling."""
        
        run_name = f"robust_{display_name.lower().replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                # Log robust testing metadata
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", display_name)
                mlflow.log_param("test_approach", "robust_large_model_handling")
                mlflow.log_param("download_timeout", self.download_timeout)
                mlflow.log_param("inference_timeout", self.inference_timeout)
                
                print(f"🧪 ROBUST TESTING: {display_name}")
                print("=" * 60)
                
                # Step 1: Pre-download check
                download_success = await self.pre_download_model(model_name, display_name)
                
                mlflow.log_metric("download_success", 1.0 if download_success else 0.0)
                
                if not download_success:
                    mlflow.log_param("failure_stage", "download")
                    return {"success": False, "error": "download_failed"}
                
                # Step 2: Load model for testing
                print("\\n🔧 Loading model for testing...")
                
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                load_start = time.time()
                
                tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    cache_dir=str(self.model_cache)
                )
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                device = "mps" if torch.backends.mps.is_available() else "cpu"
                dtype = torch.float16 if device == "mps" else torch.float32
                
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    cache_dir=str(self.model_cache),
                    torch_dtype=dtype,
                    device_map=device if device != "cpu" else None,
                    low_cpu_mem_usage=True
                )
                
                if device != "cpu":
                    model = model.to(device)
                
                load_time = time.time() - load_start
                memory_gb = psutil.Process().memory_info().rss / (1024**3)
                
                mlflow.log_metric("robust_load_time", load_time)
                mlflow.log_metric("robust_memory_gb", memory_gb)
                mlflow.log_param("robust_device", device)
                
                print(f"✅ Model loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
                
                # Step 3: Business content testing with timeouts
                print("\\n📝 Business content testing...")
                
                business_prompts = [
                    "Write a LinkedIn post about AI cost optimization:",
                    "Create a technical article intro about Apple Silicon:",
                    "Draft a professional proposal for AI services:"
                ]
                
                quality_scores = []
                latencies = []
                successful_inferences = 0
                
                for i, prompt in enumerate(business_prompts, 1):
                    print(f"   Test {i}/3: {prompt[:40]}...")
                    
                    try:
                        inference_start = time.time()
                        
                        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                        if device != "cpu":
                            inputs = {k: v.to(device) for k, v in inputs.items()}
                        
                        # Use timeout for inference
                        with torch.no_grad():
                            outputs = await asyncio.wait_for(
                                asyncio.to_thread(
                                    model.generate,
                                    **inputs,
                                    max_new_tokens=80,
                                    temperature=0.8,
                                    do_sample=True,
                                    pad_token_id=tokenizer.pad_token_id
                                ),
                                timeout=self.inference_timeout
                            )
                        
                        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        content = response[len(prompt):].strip()
                        
                        inference_time = (time.time() - inference_start) * 1000
                        
                        # Quality assessment
                        words = len(content.split())
                        quality = 5.0
                        if 40 <= words <= 150:
                            quality += 3.0
                        if any(term in content.lower() for term in ["optimization", "strategy", "professional"]):
                            quality += 2.0
                        
                        quality_scores.append(min(10.0, quality))
                        latencies.append(inference_time)
                        successful_inferences += 1
                        
                        print(f"      ✅ {inference_time:.0f}ms, Quality: {quality:.1f}/10")
                        
                    except asyncio.TimeoutError:
                        print(f"      ❌ Timeout after {self.inference_timeout}s")
                    except Exception as e:
                        print(f"      ❌ Error: {e}")
                
                # Calculate results
                if quality_scores:
                    avg_quality = sum(quality_scores) / len(quality_scores)
                    avg_latency = sum(latencies) / len(latencies)
                    success_rate = successful_inferences / len(business_prompts)
                    
                    # Compare with BLOOM-560M leader
                    bloom_quality = 8.0
                    vs_bloom = avg_quality - bloom_quality
                    
                    # Log comprehensive metrics
                    mlflow.log_metric("robust_overall_quality", avg_quality)
                    mlflow.log_metric("robust_avg_latency_ms", avg_latency)
                    mlflow.log_metric("robust_success_rate", success_rate)
                    mlflow.log_metric("robust_vs_bloom_quality", vs_bloom)
                    mlflow.log_metric("robust_successful_inferences", successful_inferences)
                    
                    # Business recommendation
                    if avg_quality > bloom_quality and success_rate >= 0.8:
                        recommendation = "new_quality_leader"
                    elif avg_quality >= 7.0 and success_rate >= 0.6:
                        recommendation = "good_business_option"
                    else:
                        recommendation = "bloom_560m_remains_leader"
                    
                    mlflow.set_tag("robust_recommendation", recommendation)
                    mlflow.set_tag("test_completion_status", "successful")
                    
                    print(f"\\n🏆 {display_name} ROBUST TEST RESULTS:")
                    print(f"   🎯 Quality: {avg_quality:.1f}/10 (vs BLOOM 8.0/10)")
                    print(f"   ⚡ Speed: {avg_latency:.0f}ms")
                    print(f"   🔧 Success rate: {success_rate:.1%}")
                    print(f"   📊 vs BLOOM: {vs_bloom:+.1f} points")
                    print(f"   💼 Recommendation: {recommendation}")
                    
                    if avg_quality > bloom_quality:
                        print("\\n🎉 NEW QUALITY LEADER FOUND!")
                    
                    return {
                        "quality": avg_quality,
                        "vs_bloom": vs_bloom,
                        "success_rate": success_rate,
                        "recommendation": recommendation,
                        "success": True
                    }
                else:
                    mlflow.log_param("failure_stage", "all_inferences_failed")
                    return {"success": False, "error": "all_inferences_failed"}
                    
            except Exception as e:
                mlflow.log_param("error", str(e))
                mlflow.set_tag("test_completion_status", "failed")
                logger.error(f"❌ {display_name} robust test failed: {e}")
                return {"success": False, "error": str(e)}


async def test_large_models_with_robust_handling():
    """Test large models with robust download and error handling."""
    
    print("🚀 ROBUST LARGE MODEL TESTING")
    print("=" * 60)
    print("🎯 Goal: Complete OPT-2.7B and BLOOM-3B testing")
    print("🔧 Approach: Extended timeouts, background downloads, error handling")
    print("")
    
    tester = RobustLargeModelTester()
    
    # Models to test with robust approach
    large_models = [
        {
            "name": "facebook/opt-2.7b",
            "display_name": "OPT-2.7B-Robust",
            "expected_quality": "8-9/10",
            "challenge": "beat_bloom_quality"
        },
        {
            "name": "bigscience/bloom-3b", 
            "display_name": "BLOOM-3B-Robust",
            "expected_quality": "8-9/10",
            "challenge": "bloom_family_upgrade"
        }
    ]
    
    results = {}
    
    for model_config in large_models:
        model_name = model_config["name"]
        display_name = model_config["display_name"]
        
        print(f"\\n🧪 Testing {display_name}")
        print(f"Expected quality: {model_config['expected_quality']}")
        print(f"Challenge: {model_config['challenge']}")
        
        try:
            # Test with extended timeout handling
            result = await asyncio.wait_for(
                tester.test_large_model_robust(model_name, display_name),
                timeout=tester.total_test_timeout
            )
            
            results[display_name] = result
            
            if result.get("success"):
                quality = result["quality"]
                vs_bloom = result["vs_bloom"]
                
                if quality > 8.0:
                    print(f"🎉 {display_name}: NEW QUALITY LEADER ({quality:.1f}/10)!")
                elif quality >= 7.0:
                    print(f"✅ {display_name}: Strong option ({quality:.1f}/10)")
                else:
                    print(f"📊 {display_name}: BLOOM-560M remains leader ({quality:.1f}/10)")
            else:
                print(f"❌ {display_name}: Test failed")
                
        except asyncio.TimeoutError:
            print(f"❌ {display_name}: Test timed out after {tester.total_test_timeout}s")
            results[display_name] = {"success": False, "error": "total_timeout"}
            
        except Exception as e:
            print(f"❌ {display_name}: Unexpected error - {e}")
            results[display_name] = {"success": False, "error": str(e)}
    
    # Summary
    print("\\n🏆 ROBUST TESTING SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in results.values() if r.get("success")]
    
    if successful_tests:
        best_result = max(successful_tests, key=lambda x: x["quality"])
        
        print(f"✅ Successful tests: {len(successful_tests)}/{len(large_models)}")
        print(f"🏆 Best quality: {best_result['quality']:.1f}/10")
        
        # Compare with BLOOM-560M
        bloom_quality = 8.0
        if best_result["quality"] > bloom_quality:
            print(f"🎉 NEW QUALITY LEADER FOUND!")
            print("✅ Upgrade from BLOOM-560M recommended")
        else:
            print(f"📊 BLOOM-560M maintains leadership ({bloom_quality}/10)")
            print("✅ Continue using BLOOM-560M for business content")
    else:
        print("❌ All large model tests failed")
        print("✅ BLOOM-560M (8.0/10) remains your best choice")
    
    print("\\n🔗 All results logged to MLflow: http://127.0.0.1:5000")
    
    return results


async def main():
    """Run robust large model testing."""
    print("🔧 FIXING LARGE MODEL TESTING ISSUES")
    print("=" * 60)
    print("Problem: OPT-2.7B and BLOOM-3B failed due to timeouts")
    print("Solution: Robust download handling with extended timeouts")
    print("")
    
    try:
        results = await test_large_models_with_robust_handling()
        
        print("\\n🎯 ROBUST TESTING COMPLETE!")
        print("📊 Check MLflow for updated results")
        print("💼 Business decision framework updated")
        
    except Exception as e:
        logger.error(f"❌ Robust testing failed: {e}")
        print("\\n📊 FALLBACK RECOMMENDATION:")
        print("✅ Use BLOOM-560M (8.0/10 quality) - proven and reliable")


if __name__ == "__main__":
    asyncio.run(main())