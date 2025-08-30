#!/usr/bin/env python3
"""
OPT-2.7B Business Content Testing - Quality Leader Candidate

Testing facebook/opt-2.7b to surpass BLOOM-560M (8.0/10 quality):
- 2.7B parameters for higher quality
- Business content generation focus
- Lead conversion optimization
- Professional marketing content

Target: Beat current leader BLOOM-560M (8.0/10 quality)
"""

import asyncio
import time
import psutil
from datetime import datetime

import mlflow


async def test_opt_2_7b():
    """Test OPT-2.7B for high-quality business content."""
    
    mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
    mlflow.set_experiment("complete_solopreneur_analysis")
    
    run_name = f"business_opt_2_7b_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with mlflow.start_run(run_name=run_name) as run:
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            model_name = "facebook/opt-2.7b"
            
            # Metadata
            mlflow.log_param("model_name", model_name)
            mlflow.log_param("display_name", "OPT-2.7B")
            mlflow.log_param("target_purpose", "beat_bloom_quality_leader")
            
            print("📦 Loading OPT-2.7B (targeting 9/10 quality)...")
            
            load_start = time.time()
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map=device if device != "cpu" else None,
                low_cpu_mem_usage=True
            )
            
            if device != "cpu":
                model = model.to(device)
            
            load_time = time.time() - load_start
            memory_gb = psutil.Process().memory_info().rss / (1024**3)
            
            mlflow.log_metric("load_time_seconds", load_time)
            mlflow.log_metric("memory_usage_gb", memory_gb)
            mlflow.log_param("device", device)
            
            print(f"✅ Loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
            
            # Business content tests
            business_prompts = [
                "Write a LinkedIn post about AI cost optimization that attracts consulting leads:",
                "Create a technical article intro about Apple Silicon ML deployment:",
                "Draft a professional proposal for AI infrastructure services:",
                "Write thought leadership content about local model deployment:",
                "Create marketing copy for AI consulting services:"
            ]
            
            quality_scores = []
            latencies = []
            
            for prompt in business_prompts:
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
                
                # Quality assessment
                words = len(content.split())
                quality = 5.0
                if 50 <= words <= 200:
                    quality += 3.0
                if any(term in content.lower() for term in ["optimization", "deployment", "strategy"]):
                    quality += 2.0
                
                quality_scores.append(min(10.0, quality))
                latencies.append(inference_time)
                
                print(f"   📝 {inference_time:.0f}ms, Quality: {quality:.1f}/10")
            
            # Overall metrics
            avg_quality = sum(quality_scores) / len(quality_scores)
            avg_latency = sum(latencies) / len(latencies)
            tokens_per_second = 100 * len(quality_scores) / (sum(latencies) / 1000)
            
            mlflow.log_metric("business_overall_quality", avg_quality)
            mlflow.log_metric("business_overall_latency_ms", avg_latency)
            mlflow.log_metric("business_tokens_per_second", tokens_per_second)
            
            # Compare with BLOOM-560M
            bloom_quality = 8.0
            quality_vs_bloom = avg_quality - bloom_quality
            
            mlflow.log_metric("quality_vs_bloom_leader", quality_vs_bloom)
            
            # Business recommendation
            if avg_quality > bloom_quality:
                recommendation = "new_quality_leader"
            elif avg_quality >= 7.0:
                recommendation = "strong_business_option"
            else:
                recommendation = "not_better_than_bloom"
            
            mlflow.set_tag("vs_bloom_comparison", recommendation)
            
            print(f"\\n🏆 OPT-2.7B Business Results:")
            print(f"   🎯 Quality: {avg_quality:.1f}/10 (vs BLOOM 8.0/10)")
            print(f"   ⚡ Speed: {avg_latency:.0f}ms")
            print(f"   💾 Memory: {memory_gb:.1f}GB")
            print(f"   📊 vs BLOOM: {quality_vs_bloom:+.1f} quality points")
            print(f"   💼 Recommendation: {recommendation}")
            
            if avg_quality > bloom_quality:
                print("\\n🎉 NEW QUALITY LEADER FOUND!")
                print("✅ OPT-2.7B beats BLOOM-560M for business content")
            elif avg_quality >= 7.0:
                print("\\n✅ STRONG BUSINESS OPTION")
                print("Good alternative to BLOOM-560M")
            else:
                print("\\n📊 BLOOM-560M remains quality leader")
            
            return {"quality": avg_quality, "recommendation": recommendation}
            
        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"❌ OPT-2.7B test failed: {e}")
            return {"success": False}


async def main():
    """Test OPT-2.7B for business content."""
    print("🚀 Testing facebook/opt-2.7b for business content quality")
    print("🎯 Goal: Beat BLOOM-560M's 8.0/10 quality score")
    print("")
    
    try:
        results = await test_opt_2_7b()
        
        print("\\n🔗 Check updated results in MLflow: http://127.0.0.1:5000")
        print("📊 All business metrics logged for comparison")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())