#!/usr/bin/env python3
"""
GODEL Business Specialist Testing - Reliable Business Model

Testing microsoft/GODEL-v1_1-base for business communication:
- 220M parameters (small, fast, reliable)
- Designed specifically for business dialogue
- Goal-oriented conversation specialist
- Perfect for client communication and sales

Strategy: Test a reliable, business-focused model
Size: Small enough to avoid download/memory issues
Expected: 7-8/10 quality with business specialization
"""

import asyncio
import time
import psutil
from datetime import datetime

import mlflow


async def test_godel_business_specialist():
    """Test GODEL for business communication specialization."""
    
    mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
    mlflow.set_experiment("complete_solopreneur_analysis")
    
    run_name = f"business_specialist_godel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with mlflow.start_run(run_name=run_name) as run:
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch
            
            model_name = "microsoft/GODEL-v1_1-base"
            
            # Business specialist metadata
            mlflow.log_param("model_name", model_name)
            mlflow.log_param("display_name", "GODEL-Business-Specialist")
            mlflow.log_param("specialization", "business_communication")
            mlflow.log_param("model_purpose", "goal_oriented_dialogue")
            mlflow.log_param("size_category", "small_reliable")
            
            print("💼 TESTING GODEL BUSINESS SPECIALIST")
            print("=" * 50)
            print("🎯 Focus: Business communication and client dialogue")
            print("📦 Size: 220M parameters (fast and reliable)")
            print("")
            
            load_start = time.time()
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            
            # GODEL is a Seq2Seq model
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "mps" else torch.float32,
                device_map=device if device != "cpu" else None,
                low_cpu_mem_usage=True
            )
            
            if device != "cpu":
                model = model.to(device)
            
            load_time = time.time() - load_start
            memory_gb = psutil.Process().memory_info().rss / (1024**3)
            
            mlflow.log_metric("specialist_load_time", load_time)
            mlflow.log_metric("specialist_memory_gb", memory_gb)
            mlflow.log_param("specialist_device", device)
            
            print(f"✅ GODEL loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
            
            # Business communication tests
            business_tests = [
                "Write a professional client email about project progress and next steps:",
                "Create a proposal summary for AI consulting services:",
                "Draft a LinkedIn message to potential business prospects:",
                "Write a client communication about technical implementation:",
                "Create a professional response to business inquiries:"
            ]
            
            quality_scores = []
            latencies = []
            
            print("\\n📝 Business Communication Testing:")
            
            for i, prompt in enumerate(business_tests, 1):
                print(f"   Test {i}/5: {prompt[:40]}...")
                
                inference_start = time.time()
                
                inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                if device != "cpu":
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=100,
                        temperature=0.7,
                        do_sample=True
                    )
                
                response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                inference_time = (time.time() - inference_start) * 1000
                
                # Business quality assessment
                words = len(response.split())
                quality = 5.0
                if 30 <= words <= 150:
                    quality += 3.0
                if any(term in response.lower() for term in ["professional", "implementation", "progress"]):
                    quality += 2.0
                
                quality_scores.append(min(10.0, quality))
                latencies.append(inference_time)
                
                print(f"      ⚡ {inference_time:.0f}ms, Quality: {quality:.1f}/10")
            
            # Overall business specialist results
            avg_quality = sum(quality_scores) / len(quality_scores)
            avg_latency = sum(latencies) / len(latencies)
            
            mlflow.log_metric("business_specialist_quality", avg_quality)
            mlflow.log_metric("business_specialist_latency_ms", avg_latency)
            
            # Compare with current options
            vs_bloom = avg_quality - 8.0
            
            mlflow.log_metric("specialist_vs_bloom_quality", vs_bloom)
            
            if avg_quality >= 7.0:
                recommendation = "excellent_business_communication"
            elif avg_quality >= 5.0:
                recommendation = "good_business_option"
            else:
                recommendation = "limited_business_use"
            
            mlflow.set_tag("business_specialist_recommendation", recommendation)
            
            print(f"\\n🏆 GODEL Business Specialist Results:")
            print(f"   💼 Quality: {avg_quality:.1f}/10")
            print(f"   ⚡ Speed: {avg_latency:.0f}ms")
            print(f"   📊 vs BLOOM-560M: {vs_bloom:+.1f} points")
            print(f"   💾 Memory: {memory_gb:.1f}GB")
            print(f"   🎯 Recommendation: {recommendation}")
            
            return {"quality": avg_quality, "recommendation": recommendation}
            
        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"❌ GODEL test failed: {e}")
            return {"success": False}


async def main():
    """Test GODEL business specialist."""
    print("💼 Testing GODEL for business communication specialization")
    print("🎯 Small, fast, business-focused model")
    print("")
    
    try:
        results = await test_godel_business_specialist()
        
        print("\\n✅ GODEL testing complete!")
        print("🔗 Results in MLflow: http://127.0.0.1:5000")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())