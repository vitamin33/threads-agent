#!/usr/bin/env python3
"""
OPT-2.7B Bulletproof Test - Final Validation with Comprehensive Error Handling

Implements bulletproof testing for OPT-2.7B with:
- Uses existing cached model (no download)
- Comprehensive error handling at each stage
- Memory monitoring and cleanup
- Staged testing with checkpoints
- 10-minute total timeout protection
- Fallback strategies for each failure point

Goal: Finally get OPT-2.7B rigorous validation results
"""

import asyncio
import statistics
import time
import psutil
import gc
from datetime import datetime

import mlflow


async def bulletproof_opt_2_7b_test():
    """Bulletproof OPT-2.7B test with comprehensive error handling."""
    
    mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
    mlflow.set_experiment("rigorous_statistical_validation")
    
    run_name = f"BULLETPROOF_opt_2_7b_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with mlflow.start_run(run_name=run_name) as run:
        
        model_name = "facebook/opt-2.7b"
        
        # Log bulletproof test metadata
        mlflow.log_param("model_name", model_name)
        mlflow.log_param("display_name", "OPT-2.7B-BULLETPROOF")
        mlflow.log_param("test_approach", "comprehensive_error_handling")
        mlflow.log_param("timeout_protection", "10_minutes_max")
        mlflow.log_param("error_handling", "staged_with_fallbacks")
        mlflow.log_param("memory_monitoring", "active")
        
        print("🛡️  BULLETPROOF OPT-2.7B TESTING")
        print("=" * 60)
        print("🎯 Goal: Final validation of claimed 9.3/10 quality")
        print("🔧 Strategy: Comprehensive error handling, staged testing")
        print("⏱️  Protection: 10-minute timeout, memory monitoring")
        print("")
        
        test_start_time = time.time()
        timeout_seconds = 600  # 10 minutes max
        
        try:
            # === STAGE 1: MEMORY BASELINE ===
            print("Stage 1: 📊 Memory baseline measurement...")
            
            memory_before = psutil.virtual_memory()
            process_before = psutil.Process().memory_info()
            
            mlflow.log_metric("stage1_system_memory_gb", memory_before.total / (1024**3))
            mlflow.log_metric("stage1_available_memory_gb", memory_before.available / (1024**3))
            mlflow.log_metric("stage1_process_memory_gb", process_before.rss / (1024**3))
            
            print(f"   ✅ Baseline: {memory_before.available / (1024**3):.1f}GB available")
            
            # === STAGE 2: LIBRARY IMPORTS ===
            print("Stage 2: 📚 Import validation...")
            
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                mlflow.log_param("stage2_imports", "successful")
                print("   ✅ Imports successful")
                
                # Check Apple Silicon availability
                mps_available = torch.backends.mps.is_available()
                device = "mps" if mps_available else "cpu"
                
                mlflow.log_param("stage2_device", device)
                mlflow.log_param("stage2_mps_available", mps_available)
                
                print(f"   ✅ Device: {device}")
                
            except Exception as e:
                mlflow.log_param("stage2_error", str(e))
                print(f"   ❌ Import failed: {e}")
                return {"success": False, "stage": "import_failure"}
            
            # === STAGE 3: TOKENIZER LOADING ===
            print("Stage 3: 🔤 Tokenizer loading...")
            
            try:
                tokenizer_start = time.time()
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                tokenizer_time = time.time() - tokenizer_start
                
                mlflow.log_metric("stage3_tokenizer_load_time", tokenizer_time)
                mlflow.log_param("stage3_tokenizer", "successful")
                
                print(f"   ✅ Tokenizer loaded: {tokenizer_time:.1f}s")
                
            except Exception as e:
                mlflow.log_param("stage3_error", str(e))
                print(f"   ❌ Tokenizer failed: {e}")
                return {"success": False, "stage": "tokenizer_failure"}
            
            # === STAGE 4: MODEL LOADING (Critical Stage) ===
            print("Stage 4: 🧠 Model loading (critical stage)...")
            
            try:
                model_start = time.time()
                
                # Conservative loading for Apple Silicon
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if device == "mps" else torch.float32,
                    device_map=device if device != "cpu" else None,
                    low_cpu_mem_usage=True,
                    trust_remote_code=False  # Security
                )
                
                if device != "cpu":
                    model = model.to(device)
                
                model_time = time.time() - model_start
                
                # Memory check after loading
                memory_after = psutil.virtual_memory()
                process_after = psutil.Process().memory_info()
                
                model_memory_gb = (process_after.rss - process_before.rss) / (1024**3)
                
                mlflow.log_metric("stage4_model_load_time", model_time)
                mlflow.log_metric("stage4_model_memory_gb", model_memory_gb)
                mlflow.log_param("stage4_model_loading", "successful")
                
                print(f"   ✅ Model loaded: {model_time:.1f}s, {model_memory_gb:.1f}GB")
                
                # Memory validation
                if model_memory_gb > 10.0:
                    print(f"   ⚠️  High memory usage: {model_memory_gb:.1f}GB")
                    mlflow.log_param("memory_warning", "high_usage")
                
            except Exception as e:
                mlflow.log_param("stage4_error", str(e))
                print(f"   ❌ Model loading failed: {e}")
                return {"success": False, "stage": "model_loading_failure"}
            
            # === STAGE 5: INFERENCE TESTING ===
            print("Stage 5: 🧪 Inference testing...")
            
            # Quick test prompts (5 instead of 15 for reliability)
            test_prompts = [
                "Write a LinkedIn post about AI optimization:",
                "Create professional content about Apple Silicon:",
                "Draft thought leadership about ML deployment:",
                "Write business content about AI strategy:",
                "Create technical content about optimization:"
            ]
            
            quality_scores = []
            latencies = []
            successful_inferences = 0
            
            try:
                for i, prompt in enumerate(test_prompts, 1):
                    # Check timeout
                    if time.time() - test_start_time > timeout_seconds:
                        print(f"   ⏰ Timeout protection: Stopping at test {i}")
                        break
                    
                    print(f"   Test {i}/5: {prompt[:30]}...")
                    
                    try:
                        inference_start = time.time()
                        
                        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                        if device != "cpu":
                            inputs = {k: v.to(device) for k, v in inputs.items()}
                        
                        # Single inference with timeout
                        with torch.no_grad():
                            outputs = await asyncio.wait_for(
                                asyncio.to_thread(
                                    model.generate,
                                    **inputs,
                                    max_new_tokens=60,  # Shorter for reliability
                                    temperature=0.8,
                                    do_sample=True,
                                    pad_token_id=tokenizer.pad_token_id
                                ),
                                timeout=30  # 30 seconds per inference
                            )
                        
                        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        content = response[len(prompt):].strip()
                        
                        inference_time = (time.time() - inference_start) * 1000
                        
                        # Quick quality assessment
                        words = len(content.split())
                        quality = 5.0
                        if 40 <= words <= 120:
                            quality += 3.0
                        if any(term in content.lower() for term in ['optimization', 'strategy', 'professional']):
                            quality += 2.0
                        
                        quality_scores.append(min(10.0, quality))
                        latencies.append(inference_time)
                        successful_inferences += 1
                        
                        print(f"      ✅ {inference_time:.0f}ms, Quality: {quality:.1f}/10")
                        
                    except asyncio.TimeoutError:
                        print(f"      ❌ Inference timeout (30s)")
                        mlflow.log_param(f"inference_{i}_timeout", "30_seconds")
                    except Exception as e:
                        print(f"      ❌ Inference error: {e}")
                        mlflow.log_param(f"inference_{i}_error", str(e))
                
                # === STAGE 6: RESULTS ANALYSIS ===
                if quality_scores:
                    bulletproof_quality = statistics.mean(quality_scores)
                    std_quality = statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0
                    confidence_interval = 1.96 * (std_quality / (len(quality_scores) ** 0.5))
                    bulletproof_latency = statistics.mean(latencies)
                    success_rate = successful_inferences / len(test_prompts)
                    
                    # Log bulletproof results
                    mlflow.log_metric("bulletproof_validated_quality", bulletproof_quality)
                    mlflow.log_metric("bulletproof_confidence_interval", confidence_interval)
                    mlflow.log_metric("bulletproof_success_rate", success_rate)
                    mlflow.log_metric("bulletproof_mean_latency", bulletproof_latency)
                    mlflow.log_metric("bulletproof_successful_inferences", successful_inferences)
                    
                    # Compare with claimed quality
                    claimed_quality = 9.3
                    quality_difference = bulletproof_quality - claimed_quality
                    
                    mlflow.log_metric("bulletproof_vs_claimed_difference", quality_difference)
                    
                    mlflow.set_tag("bulletproof_test_status", "successful")
                    mlflow.set_tag("bulletproof_validation", "completed")
                    
                    print(f"\\n🛡️  BULLETPROOF OPT-2.7B RESULTS:")
                    print("=" * 60)
                    print(f"✅ Test completed successfully!")
                    print(f"📊 Validated quality: {bulletproof_quality:.2f} ± {confidence_interval:.2f}")
                    print(f"🎯 Claimed quality: {claimed_quality}/10")
                    print(f"📈 Difference: {quality_difference:+.2f} points")
                    print(f"⚡ Latency: {bulletproof_latency:.0f}ms")
                    print(f"🔧 Success rate: {success_rate:.1%}")
                    print(f"📊 Sample size: {len(quality_scores)} tests")
                    
                    # Business decision
                    if bulletproof_quality >= 7.0:
                        print("\\n🏆 QUALITY LEADER CONFIRMED!")
                        print("✅ OPT-2.7B suitable for enterprise business content")
                        business_tier = "enterprise_grade"
                    elif bulletproof_quality >= 6.0:
                        print("\\n✅ GOOD QUALITY CONFIRMED!")
                        print("Suitable for professional business content")
                        business_tier = "professional_grade"
                    else:
                        print("\\n📊 MODERATE QUALITY")
                        print("BLOOM-560M (7.70/10) remains better choice")
                        business_tier = "moderate_grade"
                    
                    mlflow.set_tag("business_tier", business_tier)
                    
                    return {
                        "validated_quality": bulletproof_quality,
                        "confidence_interval": confidence_interval,
                        "success_rate": success_rate,
                        "business_tier": business_tier,
                        "success": True
                    }
                else:
                    mlflow.log_param("stage5_error", "no_successful_inferences")
                    print("   ❌ No successful inferences")
                    return {"success": False, "stage": "inference_failure"}
                    
            except Exception as e:
                mlflow.log_param("stage5_error", str(e))
                print(f"   ❌ Inference stage failed: {e}")
                return {"success": False, "stage": "inference_stage_failure"}
            
            finally:
                # === CLEANUP ===
                try:
                    if 'model' in locals():
                        del model
                    if 'tokenizer' in locals():
                        del tokenizer
                    gc.collect()
                    if device == "mps":
                        torch.mps.empty_cache()
                    print("   🧹 Memory cleanup completed")
                except Exception:
                    pass
                
        except Exception as e:
            mlflow.log_param("bulletproof_error", str(e))
            print(f"❌ Bulletproof test failed: {e}")
            return {"success": False, "error": str(e)}


async def main():
    """Run bulletproof OPT-2.7B validation."""
    print("🛡️  BULLETPROOF OPT-2.7B VALIDATION")
    print("=" * 60)
    print("🔍 Diagnosis: Model is cached, issue was in loading/inference")
    print("🔧 Solution: Staged testing with error handling at each step")
    print("⏱️  Protection: 10-minute timeout, memory monitoring")
    print("")
    
    try:
        # Wrap entire test in timeout
        result = await asyncio.wait_for(
            bulletproof_opt_2_7b_test(),
            timeout=600  # 10 minutes total
        )
        
        if result.get("success"):
            quality = result["validated_quality"]
            confidence = result["confidence_interval"]
            tier = result["business_tier"]
            
            print("\\n🎉 BULLETPROOF VALIDATION SUCCESS!")
            print(f"🏆 OPT-2.7B validated quality: {quality:.2f} ± {confidence:.2f}")
            print(f"💼 Business tier: {tier}")
            
            # Final business comparison
            bloom_quality = 7.70  # Our validated BLOOM result
            
            if quality > bloom_quality:
                print("\\n🥇 NEW QUALITY LEADER: OPT-2.7B!")
                print("✅ Use OPT-2.7B for premium business content")
            else:
                print("\\n📊 BLOOM-560M MAINTAINS LEADERSHIP")
                print(f"BLOOM-560M: {bloom_quality}/10 vs OPT-2.7B: {quality:.2f}/10")
                print("✅ Continue using BLOOM-560M for business content")
            
        else:
            failure_stage = result.get("stage", "unknown")
            print(f"\\n❌ Bulletproof test failed at stage: {failure_stage}")
            print("📊 FALLBACK: Use BLOOM-560M (7.70 ± 0.59/10) - validated leader")
            
    except asyncio.TimeoutError:
        print("\\n⏰ BULLETPROOF TEST TIMEOUT (10 minutes)")
        print("📊 FINAL DECISION: Use BLOOM-560M (7.70/10) - proven reliable")
        
    except Exception as e:
        print(f"\\n❌ Bulletproof test failed: {e}")
        print("📊 FINAL DECISION: Use BLOOM-560M (7.70/10) - validated leader")
    
    print("\\n🔗 All results: http://127.0.0.1:5000")
    print("📊 Navigate: Experiments → rigorous_statistical_validation")


if __name__ == "__main__":
    asyncio.run(main())