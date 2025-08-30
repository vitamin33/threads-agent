#!/usr/bin/env python3
"""
FLAN-T5-XL (3B) Business Content Testing - Lead Generation Focus

Testing google/flan-t5-xl for high-quality business content that converts:
- Instruction-tuned for business tasks
- Expected 9/10 quality vs current 1.8/10
- Premium business content generation
- Lead-generating marketing copy

Business Content Tests:
- LinkedIn thought leadership (lead magnets)
- Technical marketing content (credibility building)
- Client communication (relationship building)
- Sales and proposal content (conversion optimization)

Expected Results:
- 8-9/10 content quality (vs current 1.8/10)
- Professional marketing copy quality
- Lead-generating content capability
- Enterprise-level business writing
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


class FlanT5BusinessTester:
    """Test FLAN-T5-XL for high-quality business content generation."""
    
    def __init__(self):
        """Initialize FLAN-T5 business tester."""
        # Use same MLflow experiment for comparison
        mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
        mlflow.set_experiment("complete_solopreneur_analysis")
        
        # Lead-generation focused content tests
        self.lead_generation_tests = {
            "linkedin_lead_magnets": {
                "prompts": [
                    "Write a LinkedIn post about '5 AI Cost Optimization Strategies That Saved Companies $100k+' that attracts potential consulting clients:",
                    "Create a thought leadership LinkedIn post about 'Apple Silicon ML Deployment: The Competitive Advantage Tech Leaders Are Missing' that generates leads:",
                    "Draft a LinkedIn post about 'How I Built a Multi-Model AI System That Cuts Costs 98%' that showcases expertise and attracts prospects:"
                ],
                "conversion_goal": "consulting_leads",
                "target_audience": "CTOs_tech_leaders",
                "value_per_lead": 5000.0  # Average consulting contract value
            },
            "technical_credibility_content": {
                "prompts": [
                    "Write a dev.to article introduction about 'Production-Ready vLLM Deployment on Apple Silicon' that establishes technical authority:",
                    "Create technical content about 'Multi-Model Architecture: Scaling AI on M4 Max' that demonstrates system design expertise:",
                    "Draft documentation about 'Apple Silicon ML Optimization: Real Performance Results' that shows hands-on experience:"
                ],
                "conversion_goal": "technical_credibility",
                "target_audience": "senior_engineers_architects",
                "value_per_lead": 2000.0  # Technical consulting/hiring
            },
            "sales_and_proposals": {
                "prompts": [
                    "Write a professional proposal summary for 'AI Infrastructure Optimization Services' that wins enterprise contracts:",
                    "Create a compelling project brief about 'Local AI Deployment Strategy' that secures client commitment:",
                    "Draft an executive summary about 'AI Cost Optimization Implementation' that gets C-level approval:"
                ],
                "conversion_goal": "direct_sales",
                "target_audience": "enterprise_decision_makers", 
                "value_per_lead": 10000.0  # Enterprise contract value
            }
        }
    
    async def test_flan_t5_xl_business_content(self) -> dict:
        """Test FLAN-T5-XL for business content quality and lead generation potential."""
        
        print("🔥 TESTING FLAN-T5-XL (3B) - HIGH-QUALITY BUSINESS CONTENT")
        print("=" * 70)
        
        run_name = f"business_flan_t5_xl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
                import torch
                
                model_name = "google/flan-t5-xl"
                
                # === BUSINESS METADATA ===
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", "FLAN-T5-XL-3B")
                mlflow.log_param("model_type", "instruction_tuned_business")
                mlflow.log_param("business_focus", "lead_generation_content")
                mlflow.log_param("quality_target", "enterprise_grade")
                mlflow.log_param("conversion_optimization", "yes")
                
                # === MEMORY-MONITORED LOADING ===
                print("📦 Loading FLAN-T5-XL (3B) for business content generation...")
                
                memory_before = psutil.virtual_memory()
                process_before = psutil.Process().memory_info()
                
                load_start = time.time()
                
                # FLAN-T5 uses different model class (Seq2Seq)
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                
                device = "mps" if torch.backends.mps.is_available() else "cpu"
                dtype = torch.float16
                
                print(f"🍎 Loading with Apple Silicon optimization: {device}, {dtype}")
                
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    model_name,
                    torch_dtype=dtype,
                    device_map=device if device != "cpu" else None,
                    low_cpu_mem_usage=True
                )
                
                if device != "cpu":
                    model = model.to(device)
                
                load_time = time.time() - load_start
                
                # Memory analysis
                memory_after = psutil.virtual_memory()
                process_after = psutil.Process().memory_info()
                model_memory_gb = (process_after.rss - process_before.rss) / (1024**3)
                
                mlflow.log_metric("business_model_load_time", load_time)
                mlflow.log_metric("business_model_memory_gb", model_memory_gb)
                mlflow.log_param("business_device", device)
                mlflow.log_param("business_optimization", "apple_silicon_flan_t5")
                
                print(f"✅ Loaded successfully!")
                print(f"   ⏱️  Load time: {load_time:.1f}s")
                print(f"   💾 Model memory: {model_memory_gb:.1f}GB")
                print(f"   🍎 Device: {device}")
                
                # === BUSINESS CONTENT GENERATION TESTING ===
                business_results = {}
                total_quality_scores = []
                total_conversion_scores = []
                total_latencies = []
                
                for content_category, test_config in self.lead_generation_tests.items():
                    print(f"\\n💼 Testing {content_category}...")
                    
                    category_latencies = []
                    category_qualities = []
                    category_conversions = []
                    
                    for prompt in test_config["prompts"]:
                        print(f"   📝 Generating: {prompt[:60]}...")
                        
                        inference_start = time.time()
                        
                        # FLAN-T5 uses different input format
                        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
                        if device != "cpu":
                            inputs = {k: v.to(device) for k, v in inputs.items()}
                        
                        with torch.no_grad():
                            outputs = model.generate(
                                **inputs,
                                max_new_tokens=200,  # Longer for business content
                                temperature=0.7,     # Balanced creativity
                                do_sample=True,
                                early_stopping=True
                            )
                        
                        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        
                        inference_time_ms = (time.time() - inference_start) * 1000
                        
                        # === BUSINESS QUALITY ASSESSMENT ===
                        business_quality = self._assess_business_quality(response, content_category)
                        conversion_potential = self._assess_conversion_potential(response, test_config)
                        
                        category_latencies.append(inference_time_ms)
                        category_qualities.append(business_quality)
                        category_conversions.append(conversion_potential)
                        
                        total_latencies.append(inference_time_ms)
                        total_quality_scores.append(business_quality)
                        total_conversion_scores.append(conversion_potential)
                        
                        print(f"      ⚡ {inference_time_ms:.0f}ms, Quality: {business_quality:.1f}/10, Conversion: {conversion_potential:.1f}/10")
                    
                    # === CATEGORY BUSINESS ANALYSIS ===
                    avg_latency = sum(category_latencies) / len(category_latencies)
                    avg_quality = sum(category_qualities) / len(category_qualities)
                    avg_conversion = sum(category_conversions) / len(category_conversions)
                    
                    # Lead generation economics
                    content_per_hour = 3600 / (avg_latency / 1000)
                    cost_per_piece = (avg_latency / 1000 / 3600) * 0.005
                    value_per_lead = test_config["value_per_lead"]
                    
                    # Conversion rate estimate (based on quality)
                    conversion_rate = min(0.10, avg_conversion / 100)  # Up to 10% conversion
                    expected_leads_per_piece = conversion_rate
                    revenue_per_piece = expected_leads_per_piece * value_per_lead
                    roi_per_piece = revenue_per_piece - cost_per_piece
                    
                    business_results[content_category] = {
                        "avg_latency_ms": avg_latency,
                        "avg_quality": avg_quality,
                        "avg_conversion_potential": avg_conversion,
                        "content_per_hour": content_per_hour,
                        "expected_leads_per_piece": expected_leads_per_piece,
                        "revenue_per_piece": revenue_per_piece,
                        "roi_per_piece": roi_per_piece
                    }
                    
                    # === LOG TO MLFLOW ===
                    mlflow.log_metric(f"business_{content_category}_quality", avg_quality)
                    mlflow.log_metric(f"business_{content_category}_conversion", avg_conversion)
                    mlflow.log_metric(f"business_{content_category}_latency_ms", avg_latency)
                    mlflow.log_metric(f"business_{content_category}_leads_per_piece", expected_leads_per_piece)
                    mlflow.log_metric(f"business_{content_category}_revenue_per_piece", revenue_per_piece)
                    mlflow.log_metric(f"business_{content_category}_roi", roi_per_piece)
                    
                    print(f"   📊 {content_category}: {avg_quality:.1f}/10 quality, {avg_conversion:.1f}/10 conversion, ${roi_per_piece:.2f} ROI")
                
                # === OVERALL BUSINESS ANALYSIS ===
                overall_latency = sum(total_latencies) / len(total_latencies)
                overall_quality = sum(total_quality_scores) / len(total_quality_scores)
                overall_conversion = sum(total_conversion_scores) / len(total_conversion_scores)
                
                # Business performance vs current models
                quality_vs_dialogpt_medium = ((overall_quality - 1.8) / 1.8) * 100  # vs DialoGPT-Medium
                quality_vs_bloom = ((overall_quality - 8.0) / 8.0) * 100  # vs BLOOM-560M
                
                # === LOG COMPREHENSIVE BUSINESS METRICS ===
                mlflow.log_metric("business_overall_quality", overall_quality)
                mlflow.log_metric("business_overall_conversion_potential", overall_conversion)
                mlflow.log_metric("business_overall_latency_ms", overall_latency)
                mlflow.log_metric("business_quality_improvement_vs_dialogpt", quality_vs_dialogpt_medium)
                mlflow.log_metric("business_quality_vs_bloom", quality_vs_bloom)
                
                # Lead generation capacity
                avg_revenue_per_piece = sum(br["revenue_per_piece"] for br in business_results.values()) / len(business_results)
                daily_revenue_potential = (3600 / (overall_latency / 1000)) * 8 * avg_revenue_per_piece
                
                mlflow.log_metric("business_avg_revenue_per_piece", avg_revenue_per_piece)
                mlflow.log_metric("business_daily_revenue_potential", daily_revenue_potential)
                
                # Business recommendation
                if overall_quality >= 8.0 and overall_conversion >= 7.0:
                    business_tier = "enterprise_grade"
                    recommendation = "primary_business_model"
                elif overall_quality >= 6.0:
                    business_tier = "professional_grade"
                    recommendation = "secondary_business_model"
                else:
                    business_tier = "basic_grade"
                    recommendation = "not_recommended_for_business"
                
                mlflow.set_tag("business_content_tier", business_tier)
                mlflow.set_tag("business_recommendation", recommendation)
                mlflow.set_tag("lead_generation_capable", "yes" if overall_conversion >= 7.0 else "limited")
                
                print(f"\\n🏆 FLAN-T5-XL Business Analysis:")
                print(f"   🎯 Quality: {overall_quality:.1f}/10 (vs 1.8/10 DialoGPT-Medium)")
                print(f"   💰 Conversion: {overall_conversion:.1f}/10 lead potential") 
                print(f"   ⚡ Speed: {overall_latency:.0f}ms")
                print(f"   💵 Revenue: ${avg_revenue_per_piece:.2f} per piece")
                print(f"   📈 Daily potential: ${daily_revenue_potential:.0f}")
                print(f"   🏆 Business tier: {business_tier}")
                print(f"   💼 Recommendation: {recommendation}")
                
                return {
                    "model_name": "FLAN-T5-XL-3B",
                    "business_performance": {
                        "quality_score": overall_quality,
                        "conversion_potential": overall_conversion,
                        "quality_improvement": quality_vs_dialogpt_medium,
                        "latency_ms": overall_latency
                    },
                    "lead_generation": {
                        "revenue_per_piece": avg_revenue_per_piece,
                        "daily_revenue_potential": daily_revenue_potential,
                        "business_tier": business_tier,
                        "recommendation": recommendation
                    },
                    "category_analysis": business_results,
                    "mlflow_run_id": run.info.run_id,
                    "success": True
                }
                
            except Exception as e:
                mlflow.log_param("error", str(e))
                mlflow.set_tag("status", "failed")
                print(f"❌ FLAN-T5-XL test failed: {e}")
                return {"success": False, "error": str(e)}
    
    def _assess_business_quality(self, content: str, category: str) -> float:
        """Assess business content quality for lead generation."""
        if not content or len(content.strip()) < 30:
            return 0.0
        
        score = 5.0
        words = content.split()
        
        # === BUSINESS CONTENT CRITERIA ===
        
        # Professional length
        if category == "linkedin_lead_magnets":
            if 150 <= len(words) <= 300:  # LinkedIn optimal length
                score += 3.0
            elif len(words) < 50:
                score -= 4.0
        elif category == "technical_credibility_content":
            if 200 <= len(words) <= 400:  # Technical depth required
                score += 3.0
        elif category == "sales_and_proposals":
            if 100 <= len(words) <= 250:  # Executive summary length
                score += 3.0
        
        # Business vocabulary and authority
        authority_terms = [
            "proven", "demonstrated", "validated", "expertise", "experience",
            "implemented", "delivered", "optimized", "achieved", "results"
        ]
        authority_count = sum(1 for term in authority_terms if term in content.lower())
        score += min(2.0, authority_count * 0.4)
        
        # Professional structure
        if content.count(".") >= 3:  # Multiple sentences
            score += 1.0
        
        if any(structure in content for structure in [":", "1.", "•", "-"]):  # Structured content
            score += 1.0
        
        return min(10.0, max(0.0, score))
    
    def _assess_conversion_potential(self, content: str, test_config: Dict[str, Any]) -> float:
        """Assess lead conversion potential of the content."""
        score = 5.0
        
        # === CONVERSION INDICATORS ===
        
        # Authority and credibility
        credibility_phrases = [
            "proven results", "demonstrated", "implemented", "achieved",
            "optimized", "delivered", "validated", "expertise"
        ]
        credibility_count = sum(1 for phrase in credibility_phrases if phrase in content.lower())
        score += min(3.0, credibility_count * 0.6)
        
        # Value proposition clarity
        value_indicators = [
            "save", "reduce", "optimize", "improve", "increase",
            "competitive advantage", "roi", "cost savings"
        ]
        value_count = sum(1 for indicator in value_indicators if indicator in content.lower())
        score += min(2.0, value_count * 0.4)
        
        # Call-to-action potential
        if any(cta in content.lower() for cta in ["contact", "discuss", "learn more", "?"]):
            score += 1.0
        
        # Target audience alignment
        audience = test_config.get("target_audience", "")
        if "cto" in audience and any(term in content.lower() for term in ["technical", "architecture", "system"]):
            score += 1.0
        elif "enterprise" in audience and any(term in content.lower() for term in ["strategy", "implementation", "roi"]):
            score += 1.0
        
        return min(10.0, max(0.0, score))


async def main():
    """Test FLAN-T5-XL for business content generation."""
    tester = FlanT5BusinessTester()
    
    try:
        print("🎯 Testing FLAN-T5-XL for high-quality business content that generates leads...")
        print("")
        
        results = await tester.test_flan_t5_xl_business_content()
        
        if results.get("success"):
            print("\\n🎉 FLAN-T5-XL BUSINESS TESTING COMPLETE!")
            print("")
            
            # Business comparison with current models
            quality = results["business_performance"]["quality_score"]
            conversion = results["business_performance"]["conversion_potential"]
            
            print("📊 BUSINESS CONTENT QUALITY COMPARISON:")
            print(f"   FLAN-T5-XL: {quality:.1f}/10 quality, {conversion:.1f}/10 conversion")
            print("   DialoGPT-Medium: 1.8/10 quality (comparison baseline)")
            print("   BLOOM-560M: 8.0/10 quality (current best)")
            print("")
            
            if quality >= 8.0:
                print("✅ BREAKTHROUGH: Enterprise-grade content quality achieved!")
                print("🎯 Recommended for lead generation and business content")
            elif quality >= 6.0:
                print("✅ GOOD: Professional-grade content quality")
                print("🎯 Suitable for business content with some optimization")
            else:
                print("⚠️  Quality needs improvement for business use")
            
            print("\\n🔗 All results logged to MLflow for comparison")
            print("📊 View at: http://localhost:5000")
            
        else:
            print("❌ FLAN-T5-XL testing failed")
            
    except Exception as e:
        logger.error(f"❌ Business testing failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())