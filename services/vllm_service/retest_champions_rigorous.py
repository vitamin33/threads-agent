#!/usr/bin/env python3
"""
Re-test Champions with Rigorous Methodology

Re-validates our top models with enterprise-grade statistical rigor:
1. OPT-2.7B: Validate claimed 9.3/10 quality with 15-sample testing
2. TinyLlama-1.1B: Re-test baseline with rigorous methodology
3. DialoGPT-Medium: Validate speed champion with quality assessment

Goal: Get statistically validated quality rankings for business decisions
Method: 15 prompts per model, multiple quality dimensions, confidence intervals
"""

import asyncio
import statistics
import time
import psutil
from datetime import datetime

import mlflow


class ChampionRigorousTester:
    """Re-test champions with rigorous statistical methodology."""
    
    def __init__(self):
        """Initialize champion re-tester."""
        mlflow.set_tracking_uri("file:./champion_rigorous_testing")
        self.experiment_name = "champion_validation_rigorous"
        
        # Create rigorous validation experiment
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment:
                self.experiment_id = experiment.experiment_id
            else:
                self.experiment_id = mlflow.create_experiment(
                    self.experiment_name,
                    tags={
                        "purpose": "validate_champion_claims_with_rigor",
                        "methodology": "statistical_significance_testing",
                        "sample_size": "15_prompts_per_model",
                        "analysis": "confidence_intervals_multiple_dimensions",
                        "business_focus": "accurate_model_selection"
                    }
                )
        except Exception:
            self.experiment_id = mlflow.create_experiment(self.experiment_name)
        
        mlflow.set_experiment(self.experiment_name)
        
        # Rigorous business content test suite
        self.validation_prompts = [
            "Write a LinkedIn post about AI cost optimization that attracts consulting clients:",
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
    
    async def rigorous_champion_validation(self, model_name: str, display_name: str, claimed_quality: float) -> dict:
        """Validate champion model with rigorous methodology."""
        
        run_name = f"validation_{display_name.lower().replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                # Log validation metadata
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", display_name)
                mlflow.log_param("claimed_quality", claimed_quality)
                mlflow.log_param("validation_method", "rigorous_15_sample_statistical")
                mlflow.log_param("confidence_level", "95_percent")
                mlflow.log_param("quality_dimensions", "business_technical_length_structure")
                
                print(f"🔬 RIGOROUS VALIDATION: {display_name}")
                print("=" * 60)
                print(f"🎯 Claimed quality: {claimed_quality}/10")
                print("📊 Validation: 15 samples, statistical analysis")
                print("🔍 Goal: Confirm or revise quality claim")
                print("")
                
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
                
                mlflow.log_metric("validation_load_time", load_time)
                mlflow.log_metric("validation_memory_gb", memory_gb)
                mlflow.log_param("validation_device", device)
                
                print(f"✅ Model loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
                
                # === RIGOROUS QUALITY TESTING ===
                print("\\n📊 Rigorous quality validation (15 samples):")
                
                business_qualities = []
                technical_qualities = []
                length_qualities = []
                structure_qualities = []
                composite_qualities = []
                latencies = []
                
                for i, prompt in enumerate(self.validation_prompts, 1):
                    print(f"   Sample {i:2d}/15: {prompt[:45]}...")
                    
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
                    
                    # === MULTIPLE QUALITY DIMENSIONS ===
                    business_q = self._assess_business_quality_rigorous(content)
                    technical_q = self._assess_technical_quality_rigorous(content)
                    length_q = self._assess_length_quality_rigorous(content)
                    structure_q = self._assess_structure_quality_rigorous(content)
                    
                    composite_q = (business_q + technical_q + length_q + structure_q) / 4
                    
                    business_qualities.append(business_q)
                    technical_qualities.append(technical_q)
                    length_qualities.append(length_q)
                    structure_qualities.append(structure_q)
                    composite_qualities.append(composite_q)
                    latencies.append(inference_time)
                    
                    print(f"      Quality: {composite_q:.1f}/10 (B:{business_q:.1f} T:{technical_q:.1f} L:{length_q:.1f} S:{structure_q:.1f})")
                
                # === STATISTICAL ANALYSIS ===
                mean_quality = statistics.mean(composite_qualities)
                std_quality = statistics.stdev(composite_qualities)
                confidence_interval = 1.96 * (std_quality / (len(composite_qualities) ** 0.5))
                
                mean_latency = statistics.mean(latencies)
                std_latency = statistics.stdev(latencies)
                
                # Quality dimension means
                mean_business = statistics.mean(business_qualities)
                mean_technical = statistics.mean(technical_qualities)
                mean_length = statistics.mean(length_qualities)
                mean_structure = statistics.mean(structure_qualities)
                
                # === VALIDATION ANALYSIS ===
                quality_difference = mean_quality - claimed_quality
                relative_error = abs(quality_difference) / claimed_quality * 100
                
                # Statistical significance of difference from claim
                if std_quality > 0:
                    t_stat_vs_claim = quality_difference / (std_quality / (len(composite_qualities) ** 0.5))
                    claim_significantly_different = abs(t_stat_vs_claim) > 1.96
                else:
                    t_stat_vs_claim = 0
                    claim_significantly_different = False
                
                # === LOG RIGOROUS VALIDATION METRICS ===
                mlflow.log_metric("rigorous_validated_quality", mean_quality)
                mlflow.log_metric("rigorous_quality_std", std_quality)
                mlflow.log_metric("rigorous_confidence_interval", confidence_interval)
                mlflow.log_metric("rigorous_sample_size", len(composite_qualities))
                
                mlflow.log_metric("rigorous_mean_latency", mean_latency)
                mlflow.log_metric("rigorous_latency_std", std_latency)
                
                mlflow.log_metric("rigorous_business_quality", mean_business)
                mlflow.log_metric("rigorous_technical_quality", mean_technical)
                mlflow.log_metric("rigorous_length_quality", mean_length)
                mlflow.log_metric("rigorous_structure_quality", mean_structure)
                
                mlflow.log_metric("validation_vs_claimed_difference", quality_difference)
                mlflow.log_metric("validation_relative_error_percent", relative_error)
                mlflow.log_metric("validation_claim_significantly_different", 1.0 if claim_significantly_different else 0.0)
                
                # === VALIDATION CONCLUSION ===
                if abs(quality_difference) < confidence_interval:
                    validation_result = "claim_validated_within_confidence"
                    accuracy = "accurate_claim"
                elif quality_difference > 0:
                    validation_result = "quality_higher_than_claimed"
                    accuracy = "conservative_original_estimate"
                else:
                    validation_result = "quality_lower_than_claimed"
                    accuracy = "optimistic_original_estimate"
                
                mlflow.set_tag("validation_result", validation_result)
                mlflow.set_tag("claim_accuracy", accuracy)
                mlflow.set_tag("statistical_rigor", "validated")
                
                print(f"\\n🔬 RIGOROUS VALIDATION RESULTS: {display_name}")
                print("=" * 70)
                print(f"📊 Validated Quality: {mean_quality:.2f} ± {confidence_interval:.2f} (95% CI)")
                print(f"🎯 Claimed Quality: {claimed_quality}/10")
                print(f"📈 Difference: {quality_difference:+.2f} points ({relative_error:.1f}% error)")
                print(f"📊 Statistical significance: {'Yes' if claim_significantly_different else 'No'}")
                print(f"⚡ Latency: {mean_latency:.0f} ± {std_latency:.0f}ms")
                print(f"🔬 Sample size: {len(composite_qualities)} tests")
                print("")
                print(f"📊 Quality Dimensions:")
                print(f"   Business: {mean_business:.2f}/10")
                print(f"   Technical: {mean_technical:.2f}/10") 
                print(f"   Length: {mean_length:.2f}/10")
                print(f"   Structure: {mean_structure:.2f}/10")
                print("")
                print(f"✅ Validation: {validation_result}")
                print(f"🎯 Accuracy: {accuracy}")
                
                return {
                    "validated_quality": mean_quality,
                    "confidence_interval": confidence_interval,
                    "claimed_quality": claimed_quality,
                    "quality_difference": quality_difference,
                    "validation_result": validation_result,
                    "sample_size": len(composite_qualities),
                    "statistical_rigor": True,
                    "success": True
                }
                
            except Exception as e:
                mlflow.log_param("error", str(e))
                print(f"❌ Rigorous validation failed: {e}")
                return {"success": False, "error": str(e)}
    
    def _assess_business_quality_rigorous(self, content: str) -> float:
        """Rigorous business quality assessment."""
        if not content or len(content.strip()) < 20:
            return 0.0
        
        score = 5.0
        words = content.split()
        
        # Professional length
        if 80 <= len(words) <= 200:
            score += 3.0
        elif 50 <= len(words) < 80:
            score += 2.0
        elif len(words) < 30:
            score -= 3.0
        
        # Business vocabulary
        business_terms = ["optimization", "strategy", "implementation", "professional", "competitive"]
        term_count = sum(1 for term in business_terms if term in content.lower())
        score += min(2.0, term_count * 0.4)
        
        return min(10.0, max(0.0, score))
    
    def _assess_technical_quality_rigorous(self, content: str) -> float:
        """Rigorous technical quality assessment."""
        score = 5.0
        
        technical_terms = ["deployment", "architecture", "performance", "infrastructure", "scalable"]
        term_count = sum(1 for term in technical_terms if term in content.lower())
        score += min(3.0, term_count * 0.6)
        
        # Apple Silicon specificity
        if any(term in content.lower() for term in ["apple silicon", "mps", "m4 max", "metal"]):
            score += 2.0
        
        return min(10.0, max(0.0, score))
    
    def _assess_length_quality_rigorous(self, content: str) -> float:
        """Rigorous length quality assessment."""
        words = len(content.split())
        
        if 100 <= words <= 200:  # Optimal business content length
            return 10.0
        elif 80 <= words < 100 or 200 < words <= 250:
            return 8.0
        elif 50 <= words < 80:
            return 6.0
        elif words < 30:
            return 2.0
        else:
            return 5.0
    
    def _assess_structure_quality_rigorous(self, content: str) -> float:
        """Rigorous structure quality assessment."""
        score = 5.0
        
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if len(sentences) >= 3:
            score += 2.0
        elif len(sentences) >= 2:
            score += 1.0
        
        if ':' in content:
            score += 1.0
        if ';' in content:
            score += 0.5
        
        # Professional connectors
        connectors = ['however', 'therefore', 'furthermore', 'additionally']
        if any(conn in content.lower() for conn in connectors):
            score += 1.0
        
        return min(10.0, score)


async def main():
    """Re-test champions with rigorous methodology."""
    print("🔬 RIGOROUS CHAMPION VALIDATION")
    print("=" * 60)
    print("🎯 Goal: Validate claimed quality scores with statistical rigor")
    print("📊 Method: 15 samples, confidence intervals, multiple dimensions")
    print("")
    
    tester = ChampionRigorousTester()
    
    # Champions to re-validate with rigorous testing
    champions_to_validate = [
        {
            "name": "facebook/opt-2.7b",
            "display_name": "OPT-2.7B-Champion",
            "claimed_quality": 9.3,
            "status": "current_quality_leader"
        },
        {
            "name": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "display_name": "TinyLlama-Baseline",
            "claimed_quality": 6.5,
            "status": "balanced_baseline"
        },
        {
            "name": "microsoft/DialoGPT-medium",
            "display_name": "DialoGPT-Speed-Champion",
            "claimed_quality": 1.8,
            "status": "speed_champion_low_quality"
        }
    ]
    
    validation_results = {}
    
    for champion in champions_to_validate:
        print(f"\\n🧪 Validating {champion['display_name']}")
        print(f"   Claimed: {champion['claimed_quality']}/10 quality")
        print(f"   Status: {champion['status']}")
        
        try:
            result = await tester.rigorous_champion_validation(
                champion["name"],
                champion["display_name"], 
                champion["claimed_quality"]
            )
            
            validation_results[champion["display_name"]] = result
            
            if result.get("success"):
                validated = result["validated_quality"]
                claimed = result["claimed_quality"]
                difference = result["quality_difference"]
                confidence = result["confidence_interval"]
                
                print(f"\\n📊 Validation Summary:")
                print(f"   Validated: {validated:.2f} ± {confidence:.2f}")
                print(f"   Claimed: {claimed}/10")
                print(f"   Difference: {difference:+.2f} points")
                
                if abs(difference) < confidence:
                    print("   ✅ CLAIM VALIDATED within confidence interval")
                elif difference > 0:
                    print("   📈 QUALITY HIGHER than claimed (conservative estimate)")
                else:
                    print("   📉 QUALITY LOWER than claimed (optimistic estimate)")
                    
        except Exception as e:
            print(f"   ❌ Validation failed: {e}")
            validation_results[champion["display_name"]] = {"success": False, "error": str(e)}
    
    # === FINAL RIGOROUS RANKING ===
    print("\\n🏆 RIGOROUS QUALITY RANKING (Statistically Validated)")
    print("=" * 70)
    
    successful_validations = [(name, result) for name, result in validation_results.items() if result.get("success")]
    
    if successful_validations:
        # Sort by validated quality
        successful_validations.sort(key=lambda x: x[1]["validated_quality"], reverse=True)
        
        print("Rank | Model                | Validated Quality | Claimed | Difference | Status")
        print("-" * 80)
        
        for rank, (model_name, result) in enumerate(successful_validations, 1):
            validated = result["validated_quality"]
            claimed = result["claimed_quality"]
            diff = result["quality_difference"]
            confidence = result["confidence_interval"]
            
            print(f"{rank:2d}   | {model_name:<18} | {validated:5.2f} ± {confidence:.2f}  | {claimed:5.1f}   | {diff:+5.2f}    | {'✅ Validated' if abs(diff) < confidence else '🔄 Revised'}")
        
        print("")
        
        # Business recommendation based on rigorous results
        best_model = successful_validations[0]
        best_quality = best_model[1]["validated_quality"]
        best_confidence = best_model[1]["confidence_interval"]
        
        print("💼 RIGOROUS BUSINESS RECOMMENDATION:")
        print(f"✅ Quality Leader: {best_model[0]}")
        print(f"📊 Validated Quality: {best_quality:.2f} ± {best_confidence:.2f}")
        print(f"🔬 Statistical Confidence: 95% (rigorous methodology)")
        print(f"🎯 Business Use: Enterprise-grade content generation")
        
        if best_quality >= 8.0:
            print("🏆 EXCELLENT: Enterprise-grade quality for lead generation")
        elif best_quality >= 6.0:
            print("✅ GOOD: Professional-grade quality for business content")
        else:
            print("⚠️  MODERATE: Acceptable for general business use")
    
    print("\\n🔗 Rigorous results: mlflow ui --backend-store-uri ./champion_rigorous_testing --port 5004")
    print("💼 Interview ready: Statistical model validation expertise")


if __name__ == "__main__":
    asyncio.run(main())