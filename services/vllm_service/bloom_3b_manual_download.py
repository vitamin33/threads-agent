#!/usr/bin/env python3
"""
BLOOM-3B Manual Download and Testing - Fix Large Model Issues

Implements manual download strategy for BLOOM-3B to avoid timeout issues:
- Pre-download using HuggingFace CLI or manual caching
- Test locally cached model to avoid download during testing
- BLOOM-3B has high potential to beat OPT-2.7B's 9.3/10 quality
- BLOOM family proven successful (BLOOM-560M achieved 8.0/10)

Strategy: Fix download issues to test the most promising quality candidate
"""

import asyncio
import logging
import time
import psutil
import subprocess
from pathlib import Path
from datetime import datetime

import mlflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BloomManualDownloader:
    """Manual download and testing for BLOOM-3B."""
    
    def __init__(self):
        """Initialize BLOOM-3B manual downloader."""
        self.model_name = "bigscience/bloom-3b"
        self.cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        self.local_model_dir = Path.home() / ".cache" / "bloom_3b_manual"
        
        mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
        mlflow.set_experiment("complete_solopreneur_analysis")
        
        logger.info("BLOOM-3B manual downloader initialized")
    
    async def manual_download_bloom_3b(self) -> bool:
        """Manually download BLOOM-3B with proper timeout handling."""
        
        print("📦 MANUAL BLOOM-3B DOWNLOAD")
        print("=" * 50)
        print("🎯 Goal: Download BLOOM-3B to test against OPT-2.7B (9.3/10)")
        print("🔧 Strategy: Manual download with extended timeout")
        print("")
        
        try:
            # Method 1: Try standard download with extended timeout
            print("⬇️  Attempting standard download (15 minute timeout)...")
            
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            # Download tokenizer first (fast)
            tokenizer_start = time.time()
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            tokenizer_time = time.time() - tokenizer_start
            
            print(f"✅ Tokenizer downloaded: {tokenizer_time:.1f}s")
            
            # Download model with very long timeout
            print("⬇️  Downloading model weights (this may take 10-20 minutes)...")
            model_start = time.time()
            
            try:
                # Use asyncio with very long timeout for download
                model = await asyncio.wait_for(
                    asyncio.to_thread(
                        AutoModelForCausalLM.from_pretrained,
                        self.model_name,
                        cache_dir=str(self.cache_dir),
                        torch_dtype="auto",
                        low_cpu_mem_usage=True
                    ),
                    timeout=1800  # 30 minutes timeout
                )
                
                model_time = time.time() - model_start
                total_time = time.time() - tokenizer_start
                
                print(f"✅ Model downloaded successfully!")
                print(f"   Model download: {model_time:.1f}s ({model_time/60:.1f} minutes)")
                print(f"   Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
                
                # Clean up from memory after confirming download
                del model
                
                return True
                
            except asyncio.TimeoutError:
                print(f"❌ Download timeout after 30 minutes")
                return False
                
        except Exception as e:
            print(f"❌ Manual download failed: {e}")
            return False
    
    async def test_bloom_3b_quality_championship(self) -> dict:
        """Test BLOOM-3B for quality championship against OPT-2.7B."""
        
        print("\\n🏆 BLOOM-3B QUALITY CHAMPIONSHIP TEST")
        print("=" * 60)
        print("🎯 Challenge: Beat OPT-2.7B's 9.3/10 quality")
        print("🏅 BLOOM family advantage: BLOOM-560M proven (8.0/10)")
        print("")
        
        run_name = f"manual_bloom_3b_champion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                # Check if model is cached
                cached_files = list(self.cache_dir.rglob("*bloom-3b*"))
                
                if not cached_files:
                    print("❌ BLOOM-3B not in cache - need to download first")
                    download_success = await self.manual_download_bloom_3b()
                    
                    if not download_success:
                        mlflow.log_param("failure_reason", "download_failed")
                        return {"success": False, "error": "download_failed"}
                
                # Log championship metadata
                mlflow.log_param("model_name", self.model_name)
                mlflow.log_param("display_name", "BLOOM-3B-Manual-Champion")
                mlflow.log_param("challenge_target", "beat_opt_2_7b_9_3_quality")
                mlflow.log_param("download_method", "manual_extended_timeout")
                
                # Load model for testing
                print("🔧 Loading BLOOM-3B for quality testing...")
                
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                load_start = time.time()
                
                tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                device = "mps" if torch.backends.mps.is_available() else "cpu"
                
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    device_map=device if device != "cpu" else None,
                    low_cpu_mem_usage=True
                )
                
                if device != "cpu":
                    model = model.to(device)
                
                load_time = time.time() - load_start
                memory_gb = psutil.Process().memory_info().rss / (1024**3)
                
                mlflow.log_metric("manual_load_time", load_time)
                mlflow.log_metric("manual_memory_gb", memory_gb)
                mlflow.log_param("manual_device", device)
                
                print(f"✅ BLOOM-3B loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
                
                # Championship quality tests
                championship_prompts = [
                    "Write a LinkedIn thought leadership post about AI cost optimization that attracts enterprise consulting clients:",
                    "Create compelling technical marketing content about Apple Silicon ML deployment for business development:",
                    "Draft a professional proposal introduction that wins high-value AI consulting contracts:",
                    "Write authoritative content about multi-model deployment strategy for technical credibility:",
                    "Create executive-level communication about AI infrastructure optimization for C-suite engagement:"
                ]
                
                quality_scores = []
                latencies = []
                
                print("\\n🧪 Championship Quality Testing:")
                
                for i, prompt in enumerate(championship_prompts, 1):
                    print(f"   Test {i}/5: {prompt[:50]}...")
                    
                    inference_start = time.time()
                    
                    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                    if device != "cpu":
                        inputs = {k: v.to(device) for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=120,
                            temperature=0.8,
                            do_sample=True,
                            pad_token_id=tokenizer.pad_token_id
                        )
                    
                    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    content = response[len(prompt):].strip()
                    
                    inference_time = (time.time() - inference_start) * 1000
                    
                    # Enhanced quality assessment for championship
                    quality = self._assess_championship_quality(content)
                    
                    quality_scores.append(quality)
                    latencies.append(inference_time)
                    
                    print(f"      ⚡ {inference_time:.0f}ms, Quality: {quality:.1f}/10")
                
                # Championship results
                champion_quality = sum(quality_scores) / len(quality_scores)
                champion_latency = sum(latencies) / len(latencies)
                
                # Compare with current leader OPT-2.7B
                opt_quality = 9.3
                quality_improvement = champion_quality - opt_quality
                improvement_percent = (quality_improvement / opt_quality) * 100
                
                # Log championship metrics
                mlflow.log_metric("manual_overall_quality", champion_quality)
                mlflow.log_metric("manual_avg_latency_ms", champion_latency)
                mlflow.log_metric("manual_vs_opt_2_7b", quality_improvement)
                mlflow.log_metric("manual_improvement_percent", improvement_percent)
                
                # Championship decision
                if champion_quality > opt_quality:
                    championship_result = "bloom_3b_new_champion"
                    recommendation = "upgrade_to_bloom_3b"
                elif champion_quality >= 9.0:
                    championship_result = "excellent_alternative"
                    recommendation = "either_bloom_or_opt"
                else:
                    championship_result = "opt_2_7b_retains_title"
                    recommendation = "stay_with_opt_2_7b"
                
                mlflow.set_tag("championship_result", championship_result)
                mlflow.set_tag("manual_recommendation", recommendation)
                
                print(f"\\n🏆 BLOOM-3B CHAMPIONSHIP RESULTS:")
                print(f"   🎯 Quality: {champion_quality:.1f}/10")
                print(f"   📊 vs OPT-2.7B: {quality_improvement:+.1f} points ({improvement_percent:+.1f}%)")
                print(f"   ⚡ Speed: {champion_latency:.0f}ms")
                print(f"   💾 Memory: {memory_gb:.1f}GB")
                print(f"   🏆 Result: {championship_result}")
                
                if champion_quality > opt_quality:
                    print("\\n🎉 NEW ULTIMATE CHAMPION: BLOOM-3B!")
                    print("✅ Use BLOOM-3B for premium business content")
                elif champion_quality >= 9.0:
                    print("\\n✅ EXCELLENT ALTERNATIVE!")
                    print("Both BLOOM-3B and OPT-2.7B are excellent choices")
                else:
                    print("\\n📊 OPT-2.7B RETAINS CHAMPIONSHIP")
                    print("Continue using OPT-2.7B (9.3/10)")
                
                return {
                    "quality": champion_quality,
                    "vs_opt": quality_improvement,
                    "championship_result": championship_result,
                    "recommendation": recommendation,
                    "success": True
                }
                
            except Exception as e:
                mlflow.log_param("error", str(e))
                print(f"❌ BLOOM-3B championship test failed: {e}")
                return {"success": False, "error": str(e)}
    
    def _assess_championship_quality(self, content: str) -> float:
        """Championship-level quality assessment."""
        if not content or len(content.strip()) < 40:
            return 0.0
        
        score = 5.0
        words = content.split()
        
        # Championship content criteria
        if 100 <= len(words) <= 300:  # Professional length
            score += 3.0
        elif 60 <= len(words) < 100:
            score += 2.0
        elif len(words) < 30:
            score -= 3.0
        
        # Business excellence vocabulary
        excellence_terms = [
            "optimization", "strategy", "implementation", "architecture",
            "demonstrated", "proven", "expertise", "competitive", "advantage"
        ]
        excellence_count = sum(1 for term in excellence_terms if term in content.lower())
        score += min(2.0, excellence_count * 0.4)
        
        # Professional structure
        if content.count(".") >= 3:  # Multiple sentences
            score += 1.0
        
        return min(10.0, max(0.0, score))


async def main():
    """Test BLOOM-3B with manual download fix."""
    print("🔧 FIXING BLOOM-3B DOWNLOAD AND TESTING")
    print("=" * 60)
    print("Current champion: OPT-2.7B (9.3/10 quality)")
    print("Challenge: BLOOM-3B (3B parameters, proven BLOOM family)")
    print("")
    
    downloader = BloomManualDownloader()
    
    try:
        results = await downloader.test_bloom_3b_quality_championship()
        
        if results.get("success"):
            quality = results["quality"]
            
            if quality > 9.3:
                print("\\n🎉 NEW ULTIMATE CHAMPION: BLOOM-3B!")
                print(f"Quality: {quality:.1f}/10 (beats OPT-2.7B's 9.3/10)")
            else:
                print("\\n📊 Championship results logged to MLflow")
                
        print("\\n🔗 Check updated results: http://127.0.0.1:5000")
        
    except Exception as e:
        logger.error(f"❌ BLOOM-3B manual test failed: {e}")
        print("\\n📊 FALLBACK: OPT-2.7B (9.3/10) remains champion")


if __name__ == "__main__":
    asyncio.run(main())