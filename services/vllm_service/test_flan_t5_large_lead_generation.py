#!/usr/bin/env python3
"""
FLAN-T5-Large Lead Generation Testing

Testing google/flan-t5-large for high-quality business content:
- Instruction-tuned for business tasks
- Expected 8-9/10 quality vs current 1.8/10
- Lead generation and conversion optimization
- Professional marketing content

Business Focus:
- LinkedIn posts that generate consulting leads
- Technical content that builds authority
- Client communication that closes deals
- Marketing copy that converts prospects
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


class FlanT5LeadGenerationTester:
    """Test FLAN-T5-Large for lead-generating business content."""
    
    def __init__(self):
        """Initialize lead generation tester."""
        mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
        mlflow.set_experiment("complete_solopreneur_analysis")
        
        # Lead generation content tests
        self.lead_generation_scenarios = [
            {
                "type": "linkedin_lead_magnet",
                "prompt": "Write a LinkedIn post about 'How I Reduced AI Infrastructure Costs by 98% Using Apple Silicon' that attracts potential consulting clients and positions me as an expert:",
                "target_leads": "ai_infrastructure_consulting",
                "conversion_value": 5000
            },
            {
                "type": "technical_authority", 
                "prompt": "Create a dev.to article introduction about 'Production-Ready Multi-Model Deployment on Apple Silicon M4 Max' that establishes technical credibility:",
                "target_leads": "technical_consulting_hiring",
                "conversion_value": 3000
            },
            {
                "type": "client_proposal",
                "prompt": "Write a professional proposal summary for 'AI Cost Optimization Implementation Services' that wins enterprise contracts:",
                "target_leads": "enterprise_contracts",
                "conversion_value": 15000
            },
            {
                "type": "thought_leadership",
                "prompt": "Create a strategic analysis about 'Local AI Deployment: The Competitive Advantage' that positions me as an industry thought leader:",
                "target_leads": "speaking_opportunities_partnerships",
                "conversion_value": 10000
            }
        ]
    
    async def test_flan_t5_large_lead_generation(self) -> Dict[str, Any]:
        """Test FLAN-T5-Large for lead generation content."""
        
        print("💼 TESTING FLAN-T5-LARGE FOR LEAD GENERATION")
        print("=" * 60)
        
        run_name = f"lead_generation_flan_t5_large_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
                import torch
                
                model_name = "google/flan-t5-large"
                
                # === LEAD GENERATION METADATA ===
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", "FLAN-T5-Large-770M")
                mlflow.log_param("business_focus", "lead_generation_optimization")
                mlflow.log_param("content_purpose", "high_converting_business_content")
                mlflow.log_param("target_quality", "enterprise_grade_8_plus")
                
                # === MODEL LOADING ===
                print(f"📦 Loading {model_name} for lead generation testing...")
                
                load_start = time.time()
                
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                
                device = "mps" if torch.backends.mps.is_available() else "cpu"
                dtype = torch.float16
                
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name,
                    torch_dtype=dtype,
                    device_map=device if device != "cpu" else None,
                    low_cpu_mem_usage=True
                )
                
                if device != "cpu":
                    model = model.to(device)
                
                load_time = time.time() - load_start
                
                # Memory tracking
                process = psutil.Process()
                memory_gb = process.memory_info().rss / (1024**3)
                
                mlflow.log_metric("lead_gen_load_time", load_time)
                mlflow.log_metric("lead_gen_memory_gb", memory_gb)
                mlflow.log_param("lead_gen_device", device)
                
                print(f"✅ Loaded: {load_time:.1f}s, {memory_gb:.1f}GB, {device}")
                
                # === LEAD GENERATION CONTENT TESTING ===
                lead_gen_results = []
                total_quality_scores = []
                total_conversion_scores = []
                total_latencies = []
                
                for scenario in self.lead_generation_scenarios:
                    print(f"\\n🎯 Testing {scenario['type']}...")
                    
                    inference_start = time.time()
                    
                    # FLAN-T5 optimized input format
                    input_text = f"Generate high-quality business content: {scenario['prompt']}"
                    
                    inputs = tokenizer(input_text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                    if device != "cpu":
                        inputs = {k: v.to(device) for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        outputs = model.generate(
                            **inputs,
                            max_new_tokens=250,  # Longer for business content
                            temperature=0.6,     # More focused for business
                            do_sample=True,
                            early_stopping=True
                        )
                    
                    generated_content = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    
                    inference_time_ms = (time.time() - inference_start) * 1000
                    
                    # === BUSINESS QUALITY ASSESSMENT ===
                    business_quality = self._assess_lead_generation_quality(generated_content, scenario['type'])
                    conversion_score = self._assess_conversion_potential(generated_content, scenario)
                    
                    # Lead generation economics
                    cost_per_piece = (inference_time_ms / 1000 / 3600) * 0.005
                    potential_revenue = (conversion_score / 10) * 0.05 * scenario['conversion_value']  # 5% max conversion
                    roi = potential_revenue - cost_per_piece
                    
                    result = {
                        "scenario_type": scenario['type'],
                        "prompt": scenario['prompt'],
                        "generated_content": generated_content,
                        "inference_time_ms": inference_time_ms,
                        "business_quality": business_quality,
                        "conversion_score": conversion_score,
                        "potential_revenue": potential_revenue,
                        "roi": roi,
                        "target_leads": scenario['target_leads']
                    }
                    
                    lead_gen_results.append(result)
                    total_quality_scores.append(business_quality)
                    total_conversion_scores.append(conversion_score)
                    total_latencies.append(inference_time_ms)
                    
                    # Log individual scenario metrics
                    mlflow.log_metric(f"lead_gen_{scenario['type']}_quality", business_quality)
                    mlflow.log_metric(f"lead_gen_{scenario['type']}_conversion", conversion_score)
                    mlflow.log_metric(f"lead_gen_{scenario['type']}_latency_ms", inference_time_ms)
                    mlflow.log_metric(f"lead_gen_{scenario['type']}_roi", roi)
                    
                    print(f"   📊 Quality: {business_quality:.1f}/10, Conversion: {conversion_score:.1f}/10, ROI: ${roi:.2f}")
                
                # === OVERALL LEAD GENERATION ANALYSIS ===
                avg_quality = sum(total_quality_scores) / len(total_quality_scores)
                avg_conversion = sum(total_conversion_scores) / len(total_conversion_scores)
                avg_latency = sum(total_latencies) / len(total_latencies)
                avg_roi = sum(r['roi'] for r in lead_gen_results) / len(lead_gen_results)
                
                # Business comparison with existing models
                quality_vs_bloom = ((avg_quality - 8.0) / 8.0) * 100  # vs BLOOM-560M
                quality_vs_dialogpt = ((avg_quality - 1.8) / 1.8) * 100  # vs DialoGPT-Medium
                
                # === LOG COMPREHENSIVE LEAD GENERATION METRICS ===
                mlflow.log_metric("lead_gen_overall_quality", avg_quality)
                mlflow.log_metric("lead_gen_overall_conversion", avg_conversion)
                mlflow.log_metric("lead_gen_overall_latency_ms", avg_latency)
                mlflow.log_metric("lead_gen_average_roi", avg_roi)
                mlflow.log_metric("lead_gen_quality_vs_bloom", quality_vs_bloom)
                mlflow.log_metric("lead_gen_quality_vs_dialogpt", quality_vs_dialogpt)
                
                # Lead generation capacity
                leads_per_hour = 3600 / (avg_latency / 1000)
                daily_lead_generation_capacity = leads_per_hour * 8  # 8 hours work
                monthly_revenue_potential = daily_lead_generation_capacity * 30 * avg_roi
                
                mlflow.log_metric("lead_gen_leads_per_hour", leads_per_hour)
                mlflow.log_metric("lead_gen_daily_capacity", daily_lead_generation_capacity)
                mlflow.log_metric("lead_gen_monthly_revenue", monthly_revenue_potential)
                
                # === BUSINESS RECOMMENDATION ===
                if avg_quality >= 8.0 and avg_conversion >= 7.0:
                    recommendation = "primary_lead_generation_model"
                    business_grade = "enterprise"
                elif avg_quality >= 6.0 and avg_conversion >= 5.0:
                    recommendation = "suitable_for_business_content"
                    business_grade = "professional"
                else:
                    recommendation = "not_suitable_for_lead_generation"
                    business_grade = "basic"
                
                mlflow.set_tag("lead_generation_recommendation", recommendation)
                mlflow.set_tag("business_content_grade", business_grade)
                mlflow.set_tag("conversion_optimization", "tested")
                
                print(f"\\n🏆 FLAN-T5-Large Lead Generation Analysis:")
                print(f"   🎯 Quality: {avg_quality:.1f}/10 (vs {8.0:.1f}/10 BLOOM)")
                print(f"   💰 Conversion: {avg_conversion:.1f}/10 lead potential")
                print(f"   ⚡ Speed: {avg_latency:.0f}ms") 
                print(f"   💵 ROI: ${avg_roi:.2f} average per piece")
                print(f"   📈 Monthly potential: ${monthly_revenue_potential:.0f}")
                print(f"   🏆 Business grade: {business_grade}")
                print(f"   💼 Recommendation: {recommendation}")
                
                # Show sample content for evaluation
                if lead_gen_results:
                    best_result = max(lead_gen_results, key=lambda x: x['business_quality'])
                    print(f"\\n📝 Best Generated Content Sample ({best_result['scenario_type']}):")
                    print(f"   Quality: {best_result['business_quality']:.1f}/10")
                    print(f"   Content: {best_result['generated_content'][:200]}...")
                
                return {
                    "model_name": "FLAN-T5-Large-770M",
                    "lead_generation_metrics": {
                        "quality_score": avg_quality,
                        "conversion_potential": avg_conversion,
                        "average_roi": avg_roi,
                        "business_grade": business_grade
                    },
                    "comparison": {
                        "vs_bloom_quality": quality_vs_bloom,
                        "vs_dialogpt_quality": quality_vs_dialogpt
                    },
                    "results": lead_gen_results,
                    "mlflow_run_id": run.info.run_id,
                    "success": True
                }
                
            except Exception as e:
                mlflow.log_param("error", str(e))
                print(f"❌ FLAN-T5-Large test failed: {e}")
                return {"success": False, "error": str(e)}
    
    def _assess_lead_generation_quality(self, content: str, content_type: str) -> float:
        """Assess content quality specifically for lead generation."""
        if not content or len(content.strip()) < 50:
            return 0.0
        
        score = 5.0
        words = content.split()
        
        # Professional length for lead generation
        if 100 <= len(words) <= 350:
            score += 3.0
        elif 50 <= len(words) < 100:
            score += 1.0
        elif len(words) < 30:
            score -= 4.0
        
        # Authority and expertise indicators
        authority_terms = [
            "implemented", "delivered", "optimized", "achieved", "proven",
            "demonstrated", "expertise", "experience", "results", "successful"
        ]
        authority_count = sum(1 for term in authority_terms if term in content.lower())
        score += min(3.0, authority_count * 0.5)
        
        # Value proposition clarity
        value_terms = ["save", "reduce", "optimize", "improve", "advantage", "benefit"]
        value_count = sum(1 for term in value_terms if term in content.lower())
        score += min(2.0, value_count * 0.4)
        
        return min(10.0, max(0.0, score))
    
    def _assess_conversion_potential(self, content: str, scenario: Dict[str, Any]) -> float:
        """Assess lead conversion potential."""
        score = 5.0
        
        # Credibility building
        if any(phrase in content.lower() for phrase in ["proven", "validated", "demonstrated", "achieved"]):
            score += 2.0
        
        # Problem/solution clarity
        if any(word in content.lower() for word in ["challenge", "solution", "problem", "optimize"]):
            score += 1.5
        
        # Specificity and numbers
        import re
        numbers = re.findall(r'\d+%|\$[\d,]+|\d+x', content)
        if numbers:
            score += min(2.0, len(numbers) * 0.5)
        
        # Professional tone
        if not any(casual in content.lower() for casual in ["awesome", "cool", "wow", "yeah"]):
            score += 1.0
        
        return min(10.0, max(0.0, score))


async def main():
    """Test FLAN-T5-Large for lead generation."""
    print("🎯 Starting FLAN-T5-Large lead generation testing...")
    print("Target: High-quality business content that converts prospects to clients")
    print("")
    
    tester = FlanT5LeadGenerationTester()
    
    try:
        results = await tester.test_flan_t5_large_lead_generation()
        
        if results.get("success"):
            quality = results["lead_generation_metrics"]["quality_score"]
            conversion = results["lead_generation_metrics"]["conversion_potential"]
            grade = results["lead_generation_metrics"]["business_grade"]
            
            print("\\n🎉 FLAN-T5-LARGE LEAD GENERATION TESTING COMPLETE!")
            print("=" * 60)
            
            if quality >= 8.0:
                print("🏆 BREAKTHROUGH: Enterprise-grade content quality achieved!")
                print(f"   Quality: {quality:.1f}/10 (target: 8+)")
                print(f"   Conversion potential: {conversion:.1f}/10")
                print("   ✅ RECOMMENDED for lead generation content")
            elif quality >= 6.0:
                print("✅ GOOD: Professional-grade content quality")
                print(f"   Quality: {quality:.1f}/10")
                print("   ✅ Suitable for business content")
            else:
                print("⚠️  Content quality needs improvement")
                print(f"   Quality: {quality:.1f}/10 (target: 8+)")
            
            print(f"\\n📊 Business Grade: {grade}")
            print(f"🔗 MLflow Run: {results['mlflow_run_id']}")
            print("\\n💡 Check MLflow dashboard for detailed metrics comparison")
            
        else:
            print("❌ FLAN-T5-Large testing failed")
            
    except Exception as e:
        logger.error(f"❌ Lead generation testing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())