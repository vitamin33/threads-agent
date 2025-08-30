#!/usr/bin/env python3
"""
OPT-2.7B Quality Leader Testing

Testing facebook/opt-2.7b to challenge BLOOM-560M's 8.0/10 quality leadership:
- 2.7B parameters for enhanced content quality
- Business-focused content generation
- Lead generation and conversion optimization
- Comprehensive MLflow business metrics

Goal: Achieve 8-9/10 quality for professional business content
Current leader: BLOOM-560M (8.0/10 quality, 2,031ms)
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime
from typing import Dict, Any

import mlflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OPT27BQualityTester:
    """Test OPT-2.7B to challenge current quality leadership."""
    
    def __init__(self):
        """Initialize OPT-2.7B quality tester."""
        mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
        mlflow.set_experiment("complete_solopreneur_analysis")
        
        # Business content quality tests
        self.business_quality_tests = [
            {
                "type": "linkedin_thought_leadership",
                "prompt": "Write a LinkedIn thought leadership post about 'How Apple Silicon M4 Max Transforms AI Development: Real Performance Results' that positions you as a technical authority and attracts consulting opportunities:",
                "target_quality": 9.0,
                "business_value": "high_value_leads"
            },
            {
                "type": "technical_marketing", 
                "prompt": "Create compelling marketing content about 'Multi-Model AI Deployment: 98% Cost Savings Strategy' that demonstrates expertise and generates client interest:",
                "target_quality": 8.5,
                "business_value": "technical_credibility"
            },
            {
                "type": "client_proposal",
                "prompt": "Write a professional proposal introduction for 'AI Infrastructure Optimization Services' that wins enterprise contracts and showcases technical competence:",
                "target_quality": 9.0,
                "business_value": "enterprise_sales"
            },
            {
                "type": "content_marketing",
                "prompt": "Create engaging content about 'Local AI Deployment Success Story: Real Results from Apple Silicon Testing' that builds authority and attracts prospects:",
                "target_quality": 8.0,
                "business_value": "content_marketing"
            },
            {
                "type": "technical_documentation",
                "prompt": "Write comprehensive technical documentation about 'Apple Silicon ML Optimization: Production Deployment Guide' that demonstrates deep expertise:",
                "target_quality": 8.5,
                "business_value": "technical_authority"
            }
        ]
    
    async def test_opt_2_7b_quality_leadership(self) -> Dict[str, Any]:
        """Test OPT-2.7B for quality leadership in business content."""
        
        print("🏆 TESTING OPT-2.7B FOR QUALITY LEADERSHIP")
        print("=" * 60)
        print("🎯 Goal: Beat BLOOM-560M's 8.0/10 quality score")
        print("")
        
        run_name = f"quality_leader_opt_2_7b_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                model_name = "facebook/opt-2.7b"
                
                # === QUALITY LEADERSHIP METADATA ===
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", "OPT-2.7B-Quality-Leader")
                mlflow.log_param("business_purpose", "quality_leadership_challenge")
                mlflow.log_param("target_quality", "beat_bloom_8_0")
                mlflow.log_param("model_size", "2.7B_parameters")
                mlflow.log_param("architecture", "opt_transformer")
                
                # === MEMORY-MONITORED LOADING ===
                print("📦 Loading OPT-2.7B (2.7B parameters)...")
                print("💾 Expected memory: ~5GB (safe for M4 Max)")
                
                memory_before = psutil.virtual_memory()
                process_before = psutil.Process().memory_info()
                
                load_start = time.time()
                
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                device = "mps" if torch.backends.mps.is_available() else "cpu"
                dtype = torch.float16  # Essential for 2.7B model
                
                print(f"🍎 Apple Silicon optimization: {device}, {dtype}")
                
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=dtype,
                    device_map=device if device != "cpu" else None,
                    low_cpu_mem_usage=True
                )
                
                if device != "cpu":
                    model = model.to(device)
                
                load_time = time.time() - load_start
                
                # Precise memory tracking
                memory_after = psutil.virtual_memory()
                process_after = psutil.Process().memory_info()
                
                model_memory_gb = (process_after.rss - process_before.rss) / (1024**3)
                system_memory_increase = (memory_after.used - memory_before.used) / (1024**3)
                
                mlflow.log_metric("quality_model_load_time", load_time)
                mlflow.log_metric("quality_model_memory_gb", model_memory_gb)
                mlflow.log_metric("quality_system_memory_increase", system_memory_increase)
                mlflow.log_param("quality_device", device)
                mlflow.log_param("quality_optimization", "apple_silicon_fp16")
                
                print(f"✅ Loaded successfully!")
                print(f"   ⏱️  Load time: {load_time:.1f}s")
                print(f"   💾 Model memory: {model_memory_gb:.1f}GB")
                print(f"   🍎 Device: {device}")
                
                # === QUALITY-FOCUSED BUSINESS TESTING ===
                quality_results = []
                total_quality_scores = []
                total_latencies = []
                business_value_scores = []
                
                for test in self.business_quality_tests:
                    print(f"\\n📝 Testing {test['type']} (target: {test['target_quality']}/10)...")
                    
                    inference_start = time.time()
                    
                    inputs = tokenizer(test['prompt'], return_tensors="pt", padding=True, truncation=True, max_length=512)
                    if device != "cpu":
                        inputs = {k: v.to(device) for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=150,  # Sufficient for business content
                            temperature=0.7,     # Balanced for professional content
                            do_sample=True,
                            pad_token_id=tokenizer.pad_token_id,
                            repetition_penalty=1.1
                        )
                    
                    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    generated_content = response[len(test['prompt']):].strip()
                    
                    inference_time_ms = (time.time() - inference_start) * 1000
                    
                    # === ENHANCED QUALITY ASSESSMENT ===
                    business_quality = self._assess_business_content_quality(generated_content, test['type'])
                    business_value = self._assess_business_value(generated_content, test['business_value'])
                    
                    quality_results.append({
                        "type": test['type'],
                        "quality": business_quality,
                        "latency_ms": inference_time_ms,
                        "business_value": business_value,
                        "content": generated_content[:100] + "..." if len(generated_content) > 100 else generated_content
                    })
                    
                    total_quality_scores.append(business_quality)
                    total_latencies.append(inference_time_ms)
                    business_value_scores.append(business_value)
                    
                    # Log individual test metrics
                    mlflow.log_metric(f"quality_{test['type']}_score", business_quality)
                    mlflow.log_metric(f"quality_{test['type']}_latency_ms", inference_time_ms)
                    mlflow.log_metric(f"quality_{test['type']}_business_value", business_value)
                    
                    print(f"   📊 Quality: {business_quality:.1f}/10 (target: {test['target_quality']}/10)")
                    print(f"   ⚡ Speed: {inference_time_ms:.0f}ms")
                    print(f"   💼 Business value: {business_value:.1f}/10")
                
                # === OVERALL QUALITY LEADERSHIP ANALYSIS ===
                avg_quality = sum(total_quality_scores) / len(total_quality_scores)
                avg_latency = sum(total_latencies) / len(total_latencies)
                avg_business_value = sum(business_value_scores) / len(business_value_scores)
                
                # Compare with current leader BLOOM-560M
                bloom_quality = 8.0
                quality_improvement = avg_quality - bloom_quality
                quality_improvement_percent = (quality_improvement / bloom_quality) * 100
                
                # Business metrics
                content_per_hour = 3600 / (avg_latency / 1000)
                cost_per_piece = (avg_latency / 1000 / 3600) * 0.005  # M4 Max power
                roi_per_piece = avg_business_value * 10 - cost_per_piece  # Business value scoring
                
                # === LOG COMPREHENSIVE QUALITY METRICS ===
                mlflow.log_metric("enhanced_overall_quality", avg_quality)
                mlflow.log_metric("enhanced_overall_latency_ms", avg_latency)
                mlflow.log_metric("enhanced_business_value", avg_business_value)
                mlflow.log_metric("quality_vs_bloom_leader", quality_improvement)
                mlflow.log_metric("quality_improvement_percent", quality_improvement_percent)
                mlflow.log_metric("content_generation_rate_per_hour", content_per_hour)
                mlflow.log_metric("business_roi_per_piece", roi_per_piece)
                
                # Quality leadership assessment
                if avg_quality > bloom_quality:
                    leadership_status = "new_quality_leader"
                    recommendation = "primary_business_model"
                elif avg_quality >= 7.5:
                    leadership_status = "strong_quality_competitor"
                    recommendation = "excellent_business_option"
                elif avg_quality >= 6.0:
                    leadership_status = "decent_quality_alternative"
                    recommendation = "good_business_option"
                else:
                    leadership_status = "insufficient_quality"
                    recommendation = "not_recommended_for_business"
                
                mlflow.set_tag("quality_leadership_status", leadership_status)
                mlflow.set_tag("business_recommendation", recommendation)
                mlflow.set_tag("vs_bloom_comparison", "tested")
                
                print(f"\\n🏆 OPT-2.7B QUALITY LEADERSHIP RESULTS:")
                print("=" * 60)
                print(f"   🎯 Quality Score: {avg_quality:.1f}/10")
                print(f"   📊 vs BLOOM-560M: {quality_improvement:+.1f} points ({quality_improvement_percent:+.1f}%)")
                print(f"   ⚡ Average Speed: {avg_latency:.0f}ms")
                print(f"   💼 Business Value: {avg_business_value:.1f}/10")
                print(f"   💰 ROI per piece: ${roi_per_piece:.2f}")
                print(f"   📈 Capacity: {content_per_hour:.0f} pieces/hour")
                print(f"   🏆 Status: {leadership_status}")
                print(f"   💼 Recommendation: {recommendation}")
                
                # Result announcement
                if avg_quality > bloom_quality:
                    print("\\n🎉 NEW QUALITY LEADER FOUND!")
                    print(f"✅ OPT-2.7B ({avg_quality:.1f}/10) beats BLOOM-560M ({bloom_quality}/10)")
                    print("🎯 Recommended for lead-generating business content")
                elif avg_quality >= 7.5:
                    print("\\n✅ STRONG QUALITY COMPETITOR!")
                    print(f"OPT-2.7B ({avg_quality:.1f}/10) close to BLOOM-560M ({bloom_quality}/10)")
                    print("🎯 Excellent option for business content")
                else:
                    print("\\n📊 BLOOM-560M REMAINS QUALITY LEADER")
                    print(f"OPT-2.7B ({avg_quality:.1f}/10) vs BLOOM-560M ({bloom_quality}/10)")
                
                print(f"\\n🔗 MLflow Run: {run.info.run_id}")
                print("📊 All metrics logged to MLflow for comparison")
                
                return {
                    "model_name": "OPT-2.7B",
                    "quality_score": avg_quality,
                    "vs_bloom_improvement": quality_improvement,
                    "leadership_status": leadership_status,
                    "recommendation": recommendation,
                    "business_metrics": {
                        "latency_ms": avg_latency,
                        "business_value": avg_business_value,
                        "roi_per_piece": roi_per_piece,
                        "content_per_hour": content_per_hour
                    },
                    "quality_results": quality_results,
                    "mlflow_run_id": run.info.run_id,
                    "success": True
                }
                
            except Exception as e:
                mlflow.log_param("error", str(e))
                mlflow.set_tag("status", "failed")
                logger.error(f"❌ OPT-2.7B quality test failed: {e}")
                return {"success": False, "error": str(e)}
    
    def _assess_business_content_quality(self, content: str, content_type: str) -> float:
        """Enhanced business content quality assessment."""
        if not content or len(content.strip()) < 40:
            return 0.0
        
        score = 5.0
        words = content.split()
        sentences = content.split(".")
        
        # === LENGTH AND STRUCTURE ===
        if content_type in ["linkedin_thought_leadership", "technical_marketing"]:
            if 120 <= len(words) <= 300:  # Optimal for professional posts
                score += 3.0
            elif 80 <= len(words) < 120:
                score += 2.0
            elif len(words) < 50:
                score -= 3.0
        elif content_type in ["client_proposal", "technical_documentation"]:
            if 150 <= len(words) <= 400:  # Professional documentation length
                score += 3.0
            elif len(words) < 75:
                score -= 3.0
        elif content_type == "content_marketing":
            if 100 <= len(words) <= 250:  # Marketing content optimal
                score += 3.0
        
        # === PROFESSIONAL VOCABULARY ===
        professional_terms = [
            "implemented", "optimized", "demonstrated", "achieved", "delivered",
            "strategy", "architecture", "solution", "performance", "results",
            "expertise", "experience", "proven", "validated", "scalable"
        ]
        
        professional_density = sum(1 for term in professional_terms if term in content.lower())
        score += min(2.0, professional_density * 0.3)
        
        # === TECHNICAL AUTHORITY ===
        if content_type in ["technical_marketing", "technical_documentation"]:
            technical_terms = [
                "deployment", "optimization", "architecture", "implementation",
                "performance", "scalability", "infrastructure", "framework"
            ]
            technical_count = sum(1 for term in technical_terms if term in content.lower())
            score += min(2.0, technical_count * 0.4)
        
        # === ENGAGEMENT FACTORS ===
        if "?" in content:  # Questions engage readers
            score += 0.5
        
        if any(connector in content.lower() for connector in ["however", "therefore", "furthermore"]):
            score += 0.5
        
        # === BUSINESS IMPACT INDICATORS ===
        impact_terms = ["save", "reduce", "improve", "optimize", "advantage", "competitive"]
        impact_count = sum(1 for term in impact_terms if term in content.lower())
        score += min(1.0, impact_count * 0.3)
        
        return min(10.0, max(0.0, score))
    
    def _assess_business_value(self, content: str, business_value_type: str) -> float:
        """Assess business value potential of the content."""
        score = 5.0
        
        # === VALUE PROPOSITION CLARITY ===
        value_phrases = [
            "cost savings", "roi", "competitive advantage", "efficiency gains",
            "performance improvement", "optimization results", "proven results"
        ]
        value_count = sum(1 for phrase in value_phrases if phrase in content.lower())
        score += min(3.0, value_count * 0.8)
        
        # === CREDIBILITY BUILDING ===
        credibility_terms = [
            "demonstrated", "proven", "validated", "achieved", "delivered",
            "implemented", "optimized", "expertise", "experience"
        ]
        credibility_count = sum(1 for term in credibility_terms if term in content.lower())
        score += min(2.0, credibility_count * 0.5)
        
        # === SPECIFICITY AND NUMBERS ===
        import re
        numbers = re.findall(r'\\d+%|\\$[\\d,]+|\\d+x|\\d+GB|\\d+ms', content)
        if numbers:
            score += min(2.0, len(numbers) * 0.5)
        
        return min(10.0, max(0.0, score))


async def main():
    """Test OPT-2.7B for quality leadership."""
    print("🚀 TESTING OPT-2.7B TO CHALLENGE BLOOM'S QUALITY LEADERSHIP")
    print("🎯 Current leader: BLOOM-560M (8.0/10 quality)")
    print("🎯 Goal: Achieve 8-9/10 quality for business content")
    print("")
    
    tester = OPT27BQualityTester()
    
    try:
        results = await tester.test_opt_2_7b_quality_leadership()
        
        if results.get("success"):
            quality = results["quality_score"]
            improvement = results["vs_bloom_improvement"]
            status = results["leadership_status"]
            
            print("\\n🎉 OPT-2.7B QUALITY TESTING COMPLETE!")
            print("=" * 60)
            
            if quality > 8.0:
                print("🏆 NEW QUALITY LEADER FOUND!")
                print(f"   Quality: {quality:.1f}/10 (beats BLOOM's 8.0/10)")
                print("   ✅ RECOMMENDED for lead-generating business content")
            elif quality >= 7.5:
                print("✅ STRONG QUALITY COMPETITOR!")
                print(f"   Quality: {quality:.1f}/10 (close to BLOOM's 8.0/10)")
                print("   ✅ Excellent alternative for business content")
            else:
                print("📊 BLOOM-560M MAINTAINS QUALITY LEADERSHIP")
                print(f"   OPT-2.7B: {quality:.1f}/10 vs BLOOM: 8.0/10")
            
            print(f"\\n📈 Status: {status}")
            print(f"🔗 MLflow comparison: http://127.0.0.1:5000")
            print("💡 Check MLflow to compare all models side-by-side")
            
        else:
            print("❌ OPT-2.7B testing failed")
            
    except Exception as e:
        logger.error(f"❌ Quality testing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())