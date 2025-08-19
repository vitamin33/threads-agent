#!/usr/bin/env python3
"""
OPT-2.7B Rigorous Validation - Critical Business Decision Test

CRITICAL TEST: Validate OPT-2.7B's claimed 9.3/10 quality with rigorous methodology

Pattern discovered: All models score 1-2 points lower with rigorous testing
- BLOOM-560M: 8.0 → 6.22 (1.8 points lower)
- TinyLlama: 6.5 → 5.20 (1.3 points lower)

OPT-2.7B Prediction: 9.3 → 7.3-8.3/10 (still likely leader)

This test determines your final business model selection!
"""

import asyncio
import statistics
import time
import psutil
from datetime import datetime

import mlflow


async def validate_opt_2_7b_rigorously():
    """Rigorously validate OPT-2.7B quality claim - critical business decision."""
    
    # Use unified MLflow location
    mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
    mlflow.set_experiment("rigorous_statistical_validation")
    
    run_name = f"CRITICAL_opt_2_7b_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with mlflow.start_run(run_name=run_name) as run:
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            model_name = "facebook/opt-2.7b"
            claimed_quality = 9.3
            
            # Critical validation metadata
            mlflow.log_param("model_name", model_name)
            mlflow.log_param("display_name", "OPT-2.7B-CRITICAL-VALIDATION")
            mlflow.log_param("claimed_quality", claimed_quality)
            mlflow.log_param("test_importance", "business_decision_critical")
            mlflow.log_param("pattern_expectation", "1_2_points_lower_than_claim")
            mlflow.log_param("rigorous_sample_size", 15)
            
            print("🚨 CRITICAL VALIDATION: OPT-2.7B")
            print("=" * 60)
            print("🎯 Claimed quality: 9.3/10 (highest claim)")
            print("📊 Pattern observed: Models score 1-2 points lower with rigor")
            print("🔬 Expected: 7.3-8.3/10 (still likely leader)")
            print("💼 Impact: Determines final business model selection")
            print("")
            
            # Load OPT-2.7B
            print("📦 Loading OPT-2.7B for critical validation...")
            load_start = time.time()
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "mps" else torch.float32,
                device_map=device if device != "cpu" else None,
                low_cpu_mem_usage=True
            )
            
            if device != "cpu":
                model = model.to(device)
            
            load_time = time.time() - load_start
            memory_gb = psutil.Process().memory_info().rss / (1024**3)
            
            mlflow.log_metric("critical_load_time", load_time)
            mlflow.log_metric("critical_memory_gb", memory_gb)
            mlflow.log_param("critical_device", device)
            
            print(f"✅ OPT-2.7B loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
            
            # Rigorous business content testing
            critical_prompts = [
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
            
            print(f"\\n🧪 Critical validation: {len(critical_prompts)} rigorous samples")
            
            quality_scores = []
            latencies = []
            business_scores = []
            technical_scores = []
            
            for i, prompt in enumerate(critical_prompts, 1):
                print(f"   Critical test {i:2d}/15: {prompt[:45]}...")
                
                inference_start = time.time()
                
                inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                if device != "cpu":
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=100,
                        temperature=0.8,
                        do_sample=True,
                        pad_token_id=tokenizer.pad_token_id
                    )
                
                response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                content = response[len(prompt):].strip()
                
                inference_time = (time.time() - inference_start) * 1000
                
                # Quality assessment
                business_q = assess_business_quality_critical(content)
                technical_q = assess_technical_quality_critical(content)
                composite_q = (business_q + technical_q) / 2
                
                quality_scores.append(composite_q)
                latencies.append(inference_time)
                business_scores.append(business_q)
                technical_scores.append(technical_q)
                
                print(f"      Quality: {composite_q:.1f}/10 (B:{business_q:.1f} T:{technical_q:.1f})")
            
            # Critical statistical analysis
            validated_quality = statistics.mean(quality_scores)
            std_quality = statistics.stdev(quality_scores)
            confidence_interval = 1.96 * (std_quality / (len(quality_scores) ** 0.5))
            
            mean_latency = statistics.mean(latencies)
            mean_business = statistics.mean(business_scores)
            mean_technical = statistics.mean(technical_scores)
            
            # Validation vs claim
            quality_difference = validated_quality - claimed_quality
            relative_error = abs(quality_difference) / claimed_quality * 100
            
            # Log critical validation metrics
            mlflow.log_metric("CRITICAL_validated_quality", validated_quality)
            mlflow.log_metric("CRITICAL_confidence_interval", confidence_interval)
            mlflow.log_metric("CRITICAL_vs_claimed_difference", quality_difference)
            mlflow.log_metric("CRITICAL_relative_error_percent", relative_error)
            mlflow.log_metric("CRITICAL_mean_latency", mean_latency)
            mlflow.log_metric("CRITICAL_business_quality", mean_business)
            mlflow.log_metric("CRITICAL_technical_quality", mean_technical)
            
            # Critical business decision
            if validated_quality >= 7.0:
                business_decision = "quality_leader_for_business_content"
                recommendation = "primary_model_for_lead_generation"
            elif validated_quality >= 6.0:
                business_decision = "good_quality_for_professional_content"
                recommendation = "suitable_for_business_use"
            elif validated_quality >= 5.0:
                business_decision = "moderate_quality_acceptable"
                recommendation = "consider_alternatives"
            else:
                business_decision = "insufficient_quality_for_business"
                recommendation = "not_recommended"
            
            mlflow.set_tag("CRITICAL_business_decision", business_decision)
            mlflow.set_tag("CRITICAL_recommendation", recommendation)
            mlflow.set_tag("validation_importance", "business_critical")
            
            print(f"\\n🚨 CRITICAL VALIDATION RESULTS - OPT-2.7B:")
            print("=" * 70)
            print(f"🎯 Validated Quality: {validated_quality:.2f} ± {confidence_interval:.2f} (95% CI)")
            print(f"📊 Claimed Quality: {claimed_quality}/10")
            print(f"📈 Difference: {quality_difference:+.2f} points ({relative_error:.1f}% error)")
            print(f"⚡ Latency: {mean_latency:.0f}ms")
            print(f"💾 Memory: {memory_gb:.1f}GB")
            print("")
            print(f"📊 Quality Breakdown:")
            print(f"   Business: {mean_business:.2f}/10")
            print(f"   Technical: {mean_technical:.2f}/10")
            print("")
            print(f"💼 Business Decision: {business_decision}")
            print(f"🎯 Recommendation: {recommendation}")
            
            # Final determination
            if validated_quality >= 7.0:
                print("\\n🏆 QUALITY LEADER CONFIRMED!")
                print("✅ OPT-2.7B suitable for lead-generating business content")
            elif validated_quality >= 6.0:
                print("\\n✅ GOOD QUALITY CONFIRMED!")
                print("Suitable for professional business content")
            else:
                print("\\n⚠️  QUALITY CONCERNS!")
                print("May need to find better models for business content")
            
            return {
                "validated_quality": validated_quality,
                "confidence_interval": confidence_interval,
                "business_decision": business_decision,
                "recommendation": recommendation,
                "success": True
            }
            
        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"❌ Critical OPT-2.7B validation failed: {e}")
            return {"success": False, "error": str(e)}


def assess_business_quality_critical(content):
    """Critical business quality assessment."""
    if not content or len(content.strip()) < 20:
        return 0.0
    
    score = 5.0
    words = content.split()
    
    # Professional length for business content
    if 80 <= len(words) <= 200:
        score += 3.0
    elif 50 <= len(words) < 80:
        score += 2.0
    elif len(words) < 30:
        score -= 3.0
    
    # Business vocabulary
    business_terms = ["optimization", "strategy", "implementation", "professional", "competitive", "advantage"]
    term_count = sum(1 for term in business_terms if term in content.lower())
    score += min(2.0, term_count * 0.3)
    
    return min(10.0, max(0.0, score))


def assess_technical_quality_critical(content):
    """Critical technical quality assessment."""
    score = 5.0
    
    technical_terms = ["deployment", "architecture", "performance", "infrastructure", "scalable"]
    term_count = sum(1 for term in technical_terms if term in content.lower())
    score += min(3.0, term_count * 0.6)
    
    # Apple Silicon specificity
    if any(term in content.lower() for term in ["apple silicon", "mps", "mlflow", "optimization"]):
        score += 2.0
    
    return min(10.0, max(0.0, score))


async def main():
    """Run critical OPT-2.7B validation."""
    print("🚨 CRITICAL VALIDATION: OPT-2.7B WITH RIGOROUS METHODOLOGY")
    print("=" * 70)
    print("🎯 Goal: Validate 9.3/10 claim with statistical rigor")
    print("📊 Expected: 7.3-8.3/10 (following observed pattern)")
    print("💼 Impact: Final business model selection decision")
    print("")
    
    try:
        results = await validate_opt_2_7b_rigorously()
        
        if results.get("success"):
            validated = results["validated_quality"]
            decision = results["business_decision"]
            
            print("\\n🎉 CRITICAL VALIDATION COMPLETE!")
            print(f"📊 OPT-2.7B rigorous quality: {validated:.2f}/10")
            print(f"💼 Business decision: {decision}")
            print("\\n🔗 View in unified dashboard: http://127.0.0.1:5000")
            print("📊 All rigorous results now in one location")
            
        else:
            print("❌ Critical validation failed")
            
    except Exception as e:
        print(f"❌ Critical testing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())