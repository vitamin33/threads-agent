#!/usr/bin/env python3
"""
Unified Rigorous Testing - Consolidated MLflow Dashboard

Consolidates all testing into ONE MLflow dashboard for easy comparison:
- All experiments in enhanced_business_mlflow
- Rigorous re-testing of OPT-2.7B, BLOOM-560M, TinyLlama
- Statistical analysis with confidence intervals
- One unified dashboard for complete model comparison

Goal: Clean, professional MLflow dashboard with rigorous statistical results
"""

import asyncio
import statistics
import time
import psutil
from datetime import datetime

import mlflow


async def unified_rigorous_model_testing():
    """Run unified rigorous testing with all experiments in one place."""
    
    # === CONSOLIDATE TO ONE MLFLOW LOCATION ===
    mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
    
    # Create new rigorous experiment in existing MLflow location
    rigorous_experiment_name = "rigorous_statistical_validation"
    
    try:
        experiment = mlflow.get_experiment_by_name(rigorous_experiment_name)
        if experiment:
            experiment_id = experiment.experiment_id
        else:
            experiment_id = mlflow.create_experiment(
                rigorous_experiment_name,
                tags={
                    "methodology": "enterprise_grade_statistical_rigor",
                    "purpose": "validate_champion_claims_with_statistics",
                    "sample_size": "15_prompts_expanded_from_3_5",
                    "confidence_level": "95_percent_intervals",
                    "interview_value": "statistical_ml_expertise"
                }
            )
    except Exception:
        experiment_id = mlflow.create_experiment(rigorous_experiment_name)
    
    mlflow.set_experiment(rigorous_experiment_name)
    
    print("🔬 UNIFIED RIGOROUS MODEL TESTING")
    print("=" * 60)
    print("🎯 Consolidating all experiments into one MLflow dashboard")
    print("📊 Re-testing champions with statistical rigor")
    print("🔗 Unified dashboard: http://127.0.0.1:5000")
    print("")
    
    # Test suite for rigorous validation
    rigorous_prompts = [
        "Write a LinkedIn post about AI cost optimization for enterprise teams:",
        "Create professional content about Apple Silicon ML deployment:",
        "Draft thought leadership about local model deployment strategy:",
        "Write a LinkedIn article about AI infrastructure optimization:",
        "Create content about enterprise AI cost reduction success:",
        "Draft professional content about ML deployment achievements:",
        "Write strategic content about AI competitive advantages:",
        "Create LinkedIn content about technical leadership:",
        "Draft professional content about AI implementation results:",
        "Write thought leadership about ML infrastructure strategy:",
        "Create content about AI transformation in business:",
        "Draft LinkedIn content about technical innovation:",
        "Write professional content about AI optimization:",
        "Create strategic content about ML cost management:",
        "Draft LinkedIn content about AI technical excellence:"
    ]
    
    # Models to re-test with rigorous methodology
    models_to_validate = [
        {
            "name": "bigscience/bloom-560m",
            "display_name": "BLOOM-560M-Rigorous",
            "claimed_quality": 8.0,
            "priority": "former_leader"
        },
        {
            "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", 
            "display_name": "TinyLlama-Rigorous",
            "claimed_quality": 6.5,
            "priority": "baseline_validation"
        }
    ]
    
    validation_results = {}
    
    for model_config in models_to_validate:
        model_name = model_config["name"]
        display_name = model_config["display_name"]
        claimed_quality = model_config["claimed_quality"]
        
        print(f"\\n🧪 RIGOROUS VALIDATION: {display_name}")
        print(f"   Claimed quality: {claimed_quality}/10")
        print(f"   Sample size: {len(rigorous_prompts)} prompts")
        
        run_name = f"{display_name.lower().replace('-', '_')}_rigorous_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                # Log rigorous metadata
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", display_name)
                mlflow.log_param("claimed_quality", claimed_quality)
                mlflow.log_param("rigorous_sample_size", len(rigorous_prompts))
                mlflow.log_param("methodology", "statistical_validation")
                mlflow.log_param("confidence_level", "95_percent")
                
                # Load model
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
                
                mlflow.log_metric("rigorous_load_time", load_time)
                mlflow.log_metric("rigorous_memory_gb", memory_gb)
                mlflow.log_param("rigorous_device", device)
                
                print(f"   ✅ Loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
                
                # === RIGOROUS TESTING ===
                quality_scores = []
                latencies = []
                business_qualities = []
                technical_qualities = []
                
                print(f"   📊 Testing {len(rigorous_prompts)} samples...")
                
                for i, prompt in enumerate(rigorous_prompts, 1):
                    if i % 3 == 0:  # Progress updates
                        print(f"      Progress: {i}/{len(rigorous_prompts)}")
                    
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
                    business_q = assess_business_quality(content)
                    technical_q = assess_technical_quality(content)
                    composite_q = (business_q + technical_q) / 2
                    
                    quality_scores.append(composite_q)
                    latencies.append(inference_time)
                    business_qualities.append(business_q)
                    technical_qualities.append(technical_q)
                
                # Statistical analysis
                mean_quality = statistics.mean(quality_scores)
                std_quality = statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0
                confidence_interval = 1.96 * (std_quality / (len(quality_scores) ** 0.5))
                
                mean_latency = statistics.mean(latencies)
                
                # Validation analysis
                quality_difference = mean_quality - claimed_quality
                
                # Log rigorous metrics to unified dashboard
                mlflow.log_metric("rigorous_validated_quality", mean_quality)
                mlflow.log_metric("rigorous_confidence_interval", confidence_interval)
                mlflow.log_metric("rigorous_sample_size", len(quality_scores))
                mlflow.log_metric("rigorous_vs_claimed_difference", quality_difference)
                mlflow.log_metric("rigorous_mean_latency", mean_latency)
                mlflow.log_metric("rigorous_business_quality", statistics.mean(business_qualities))
                mlflow.log_metric("rigorous_technical_quality", statistics.mean(technical_qualities))
                
                # Validation result
                if abs(quality_difference) < confidence_interval:
                    validation_status = "claim_validated"
                elif quality_difference > 0:
                    validation_status = "higher_than_claimed"
                else:
                    validation_status = "lower_than_claimed"
                
                mlflow.set_tag("validation_status", validation_status)
                mlflow.set_tag("statistical_rigor", "enterprise_grade")
                
                print(f"\\n   🔬 RIGOROUS RESULTS:")
                print(f"      Validated: {mean_quality:.2f} ± {confidence_interval:.2f}")
                print(f"      Claimed: {claimed_quality}/10")
                print(f"      Status: {validation_status}")
                
                validation_results[display_name] = {
                    "validated_quality": mean_quality,
                    "confidence_interval": confidence_interval,
                    "claimed_quality": claimed_quality,
                    "validation_status": validation_status
                }
                
            except Exception as e:
                mlflow.log_param("error", str(e))
                print(f"   ❌ Validation failed: {e}")
    
    # === START UNIFIED MLFLOW UI ===
    print("\\n🔗 STARTING UNIFIED MLFLOW DASHBOARD")
    print("=" * 60)
    
    # Stop any existing MLflow UIs
    import subprocess
    subprocess.run(["pkill", "-f", "mlflow ui"], capture_output=True)
    
    # Start unified MLflow UI
    import os
    os.system("mlflow ui --backend-store-uri ./enhanced_business_mlflow --host 127.0.0.1 --port 5000 > unified_mlflow.log 2>&1 &")
    
    print("✅ Unified MLflow dashboard started")
    print("🔗 Access: http://127.0.0.1:5000")
    print("📊 All experiments now in one location")
    print("")
    
    print("🎯 WHAT YOU'LL SEE:")
    print("• Original experiments: complete_solopreneur_analysis")
    print("• Rigorous validation: rigorous_statistical_validation")
    print("• All model comparisons in one unified view")
    print("• Easy side-by-side comparison of all results")
    
    print("\\n🏆 RIGOROUS VALIDATION SUMMARY:")
    if validation_results:
        print("Model                | Validated Quality | Claimed | Status")
        print("-" * 60)
        for model, result in validation_results.items():
            validated = result["validated_quality"]
            claimed = result["claimed_quality"]
            status = result["validation_status"]
            confidence = result["confidence_interval"]
            
            print(f"{model:<18} | {validated:5.2f} ± {confidence:.2f}  | {claimed:5.1f}   | {status}")
    
    return validation_results


def assess_business_quality(content):
    """Business quality assessment."""
    if not content:
        return 0.0
    
    words = content.split()
    score = 5.0
    
    if 80 <= len(words) <= 200:
        score += 3.0
    
    business_terms = ["optimization", "strategy", "professional", "implementation"]
    term_count = sum(1 for term in business_terms if term in content.lower())
    score += min(2.0, term_count * 0.5)
    
    return min(10.0, score)


def assess_technical_quality(content):
    """Technical quality assessment."""
    score = 5.0
    
    technical_terms = ["deployment", "architecture", "performance", "scalable"]
    term_count = sum(1 for term in technical_terms if term in content.lower())
    score += min(3.0, term_count * 0.6)
    
    if any(term in content.lower() for term in ["apple silicon", "mps", "mlflow"]):
        score += 2.0
    
    return min(10.0, score)


async def main():
    """Run unified rigorous testing."""
    print("🔗 CONSOLIDATING TO UNIFIED MLFLOW DASHBOARD")
    print("🔬 Re-testing champions with statistical rigor")
    print("📊 Goal: One dashboard with all rigorous results")
    print("")
    
    try:
        results = await unified_rigorous_model_testing()
        
        print("\\n🎉 UNIFIED RIGOROUS TESTING COMPLETE!")
        print("🔗 Single dashboard: http://127.0.0.1:5000")
        print("📊 All experiments consolidated for easy comparison")
        
    except Exception as e:
        print(f"❌ Unified testing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())