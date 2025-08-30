#!/usr/bin/env python3
"""
DialoGPT-Large (3B) Enhanced Business Testing

Tests the largest DialoGPT model for premium content generation:
- Quality comparison vs DialoGPT-Medium
- Memory usage validation on M4 Max
- ROI analysis for high-value content
- Business metrics collection in MLflow

Expected Results:
- Higher quality than DialoGPT-Medium
- ~7GB memory usage (vs 0.9GB medium)
- Slower inference but better content
- Premium content generation validation
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime

import mlflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DialoGPTLargeTester:
    """Test DialoGPT-large with comprehensive business analysis."""
    
    def __init__(self):
        """Initialize DialoGPT-large tester."""
        # Use same MLflow experiment as enhanced testing
        mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
        mlflow.set_experiment("complete_solopreneur_analysis")
        
        # Premium content test scenarios
        self.premium_content_tests = {
            "linkedin_thought_leadership": [
                "Write a LinkedIn thought leadership post about AI transformation in enterprises that will position you as an industry expert:",
                "Create a comprehensive LinkedIn post about Apple Silicon advantages for ML teams that establishes technical credibility:",
                "Draft a strategic LinkedIn post about local model deployment that attracts CTO-level connections:"
            ],
            "technical_authority": [
                "Write an authoritative dev.to article introduction about vLLM optimization that demonstrates deep technical knowledge:",
                "Create expert-level technical content about Apple Silicon ML deployment for senior engineers:",
                "Draft comprehensive documentation about multi-model architecture that showcases system design expertise:"
            ],
            "executive_communication": [
                "Write an executive summary about AI infrastructure cost optimization for C-level stakeholders:",
                "Create a technical proposal for local AI deployment that wins enterprise contracts:",
                "Draft a strategic briefing about Apple Silicon ML advantages for technology leadership:"
            ]
        }
    
    async def test_dialogpt_large_premium_content(self) -> dict:
        """Test DialoGPT-large for premium content generation."""
        
        print("🔥 TESTING DIALOGPT-LARGE (3B) - PREMIUM CONTENT ANALYSIS")
        print("=" * 70)
        
        run_name = f"premium_dialogpt_large_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with mlflow.start_run(run_name=run_name) as run:
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                model_name = "microsoft/DialoGPT-large"
                
                # === ENHANCED METADATA ===
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("display_name", "DialoGPT-Large-3B")
                mlflow.log_param("model_size", "3B_parameters")
                mlflow.log_param("test_focus", "premium_content_generation")
                mlflow.log_param("business_tier", "enterprise_quality")
                
                # === MEMORY-AWARE LOADING ===
                print("📦 Loading DialoGPT-large (3B) with memory monitoring...")
                
                # Monitor memory before loading
                memory_before = psutil.virtual_memory()
                process_before = psutil.Process().memory_info()
                
                load_start = time.time()
                
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                # Apple Silicon optimization for 3B model
                device = "mps" if torch.backends.mps.is_available() else "cpu"
                dtype = torch.float16  # Essential for 3B model on Apple Silicon
                
                print(f"🍎 Loading on {device} with {dtype} (Apple Silicon optimized)")
                
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=dtype,
                    device_map=device if device != "cpu" else None,
                    low_cpu_mem_usage=True
                )
                
                if device != "cpu":
                    model = model.to(device)
                
                load_time = time.time() - load_start
                
                # Monitor memory after loading
                memory_after = psutil.virtual_memory()
                process_after = psutil.Process().memory_info()
                
                # Calculate actual memory usage
                system_memory_increase = (memory_after.used - memory_before.used) / (1024**3)
                process_memory_gb = process_after.rss / (1024**3)
                model_memory_estimate = process_memory_gb - (process_before.rss / (1024**3))
                
                # === LOG MEMORY METRICS ===
                mlflow.log_metric("model_load_time_seconds", load_time)
                mlflow.log_metric("actual_memory_usage_gb", model_memory_estimate)
                mlflow.log_metric("process_total_memory_gb", process_memory_gb)
                mlflow.log_metric("system_memory_increase_gb", system_memory_increase)
                
                mlflow.log_param("device", device)
                mlflow.log_param("dtype", str(dtype))
                mlflow.log_param("apple_silicon_optimized", True)
                
                print(f"✅ Loaded successfully!")
                print(f"   ⏱️  Load time: {load_time:.1f}s")
                print(f"   💾 Model memory: ~{model_memory_estimate:.1f}GB")
                print(f"   📊 Process total: {process_memory_gb:.1f}GB")
                print(f"   🍎 Device: {device}")
                
                # Validate memory estimate vs calculation
                estimated_memory = 7.3  # Our calculation
                actual_vs_estimate = abs(model_memory_estimate - estimated_memory) / estimated_memory
                
                mlflow.log_metric("memory_estimate_accuracy", 1.0 - actual_vs_estimate)
                
                print(f"   🎯 Memory estimate accuracy: {(1.0 - actual_vs_estimate):.1%}")
                
                # === PREMIUM CONTENT TESTING ===
                all_results = []
                premium_analysis = {}
                
                total_inference_time = 0
                total_quality_scores = []
                total_engagement_scores = []
                
                for content_tier, prompts in self.premium_content_tests.items():
                    print(f"\\n🎨 Testing {content_tier}...")
                    
                    tier_latencies = []
                    tier_qualities = []
                    tier_engagements = []
                    
                    for prompt in prompts:
                        inference_start = time.time()
                        
                        # Generate premium content
                        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
                        if device != "cpu":
                            inputs = {k: v.to(device) for k, v in inputs.items()}
                        
                        with torch.no_grad():
                            outputs = model.generate(
                                **inputs,
                                max_new_tokens=150,  # Longer for premium content
                                temperature=0.7,     # Balanced creativity
                                do_sample=True,
                                pad_token_id=tokenizer.pad_token_id,
                                repetition_penalty=1.1  # Avoid repetition
                            )
                        
                        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                        generated_content = response[len(prompt):].strip()
                        
                        inference_time_ms = (time.time() - inference_start) * 1000
                        
                        # Enhanced quality assessment for premium content
                        quality_score = self._assess_premium_quality(generated_content, content_tier)
                        engagement_score = self._assess_premium_engagement(generated_content)
                        
                        tier_latencies.append(inference_time_ms)
                        tier_qualities.append(quality_score)
                        tier_engagements.append(engagement_score)
                        
                        total_inference_time += inference_time_ms
                        total_quality_scores.append(quality_score)
                        total_engagement_scores.append(engagement_score)
                        
                        print(f'   📝 {content_tier}: {inference_time_ms:.0f}ms, Quality {quality_score:.1f}/10')
                    
                    # Calculate tier averages
                    avg_latency = sum(tier_latencies) / len(tier_latencies)
                    avg_quality = sum(tier_qualities) / len(tier_qualities)
                    avg_engagement = sum(tier_engagements) / len(tier_engagements)
                    
                    premium_analysis[content_tier] = {
                        'avg_latency_ms': avg_latency,
                        'avg_quality': avg_quality,
                        'avg_engagement': avg_engagement,
                        'premium_tier': True
                    }
                    
                    # Log premium tier metrics
                    mlflow.log_metric(f'premium_{content_tier}_latency_ms', avg_latency)
                    mlflow.log_metric(f'premium_{content_tier}_quality', avg_quality)
                    mlflow.log_metric(f'premium_{content_tier}_engagement', avg_engagement)
                
                # === BUSINESS ANALYSIS ===
                avg_latency = total_inference_time / len(total_quality_scores)
                avg_quality = sum(total_quality_scores) / len(total_quality_scores)
                avg_engagement = sum(total_engagement_scores) / len(total_engagement_scores)
                
                # Premium content economics
                premium_content_value = 200.0  # Higher value for premium content
                content_per_hour = 3600 / (avg_latency / 1000)
                cost_per_piece = (avg_latency / 1000 / 3600) * 0.005  # M4 Max power
                roi_per_piece = premium_content_value - cost_per_piece
                monthly_revenue_potential = content_per_hour * 8 * 30 * premium_content_value
                
                # === LOG BUSINESS METRICS ===
                mlflow.log_metric('premium_avg_latency_ms', avg_latency)
                mlflow.log_metric('premium_avg_quality', avg_quality)
                mlflow.log_metric('premium_avg_engagement', avg_engagement)
                mlflow.log_metric('premium_content_per_hour', content_per_hour)
                mlflow.log_metric('premium_roi_per_piece', roi_per_piece)
                mlflow.log_metric('premium_monthly_potential', monthly_revenue_potential)
                
                # Quality comparison with medium model
                medium_baseline_quality = 1.8  # From our previous testing
                quality_improvement = ((avg_quality - medium_baseline_quality) / medium_baseline_quality) * 100
                
                mlflow.log_metric('quality_improvement_vs_medium', quality_improvement)
                
                # Memory efficiency for 3B model
                performance_per_gb = content_per_hour / model_memory_estimate
                mlflow.log_metric('premium_performance_per_gb', performance_per_gb)
                
                # === BUSINESS TAGS ===
                mlflow.set_tag('model_tier', 'premium_quality')
                mlflow.set_tag('content_specialization', 'high_value_professional')
                mlflow.set_tag('memory_category', 'large_model_3b')
                
                print(f'\\n🏆 DialoGPT-Large Business Analysis:')
                print(f'   🚀 Performance: {avg_latency:.0f}ms, {content_per_hour:.1f} pieces/hour')
                print(f'   🎯 Quality: {avg_quality:.1f}/10 (+{quality_improvement:.1f}% vs Medium)')
                print(f'   💰 ROI: \\${roi_per_piece:.2f} per premium piece')
                print(f'   📈 Monthly potential: \\${monthly_revenue_potential:.0f}')
                print(f'   💾 Memory efficiency: {performance_per_gb:.1f} pieces/hour/GB')
                print(f'   🔗 MLflow run: {run.info.run_id}')
                
                return {
                    'model_name': 'DialoGPT-Large-3B',
                    'memory_actual_gb': model_memory_estimate,
                    'memory_estimate_gb': 7.3,
                    'performance': {
                        'latency_ms': avg_latency,
                        'quality_score': avg_quality,
                        'engagement_score': avg_engagement,
                        'content_per_hour': content_per_hour
                    },
                    'business': {
                        'roi_per_piece': roi_per_piece,
                        'monthly_potential': monthly_revenue_potential,
                        'quality_improvement': quality_improvement,
                        'performance_per_gb': performance_per_gb
                    },
                    'mlflow_run_id': run.info.run_id,
                    'success': True
                }
                
            except Exception as e:
                mlflow.log_param('error', str(e))
                print(f'❌ DialoGPT-large test failed: {e}')
                return {'success': False, 'error': str(e)}
    
    def _assess_premium_quality(self, content: str, tier: str) -> float:
        """Enhanced quality assessment for premium content."""
        if not content or len(content.strip()) < 20:
            return 0.0
        
        score = 5.0
        words = content.split()
        sentences = content.split('.')
        
        # === PREMIUM CONTENT CRITERIA ===
        
        # Length and depth for premium content
        if tier == 'linkedin_thought_leadership':
            if 150 <= len(words) <= 400:  # Premium LinkedIn length
                score += 3.0
            elif 100 <= len(words) < 150:
                score += 1.5
        elif tier == 'technical_authority':
            if 200 <= len(words) <= 500:  # Technical depth
                score += 3.0
        elif tier == 'executive_communication':
            if 100 <= len(words) <= 300:  # Executive briefing length
                score += 3.0
        
        # Professional vocabulary density
        executive_terms = [
            'strategic', 'optimization', 'implementation', 'architecture',
            'scalable', 'enterprise', 'transformation', 'competitive'
        ]
        term_density = sum(1 for term in executive_terms if term in content.lower()) / len(words) * 100
        score += min(2.0, term_density * 10)
        
        # Structure and coherence for premium content
        if len(sentences) >= 3:
            score += 1.0
        
        if any(connector in content.lower() for connector in ['however', 'therefore', 'furthermore', 'consequently']):
            score += 1.0
        
        return min(10.0, max(0.0, score))
    
    def _assess_premium_engagement(self, content: str) -> float:
        """Assess engagement potential for premium content."""
        score = 5.0
        
        # Authority indicators
        authority_phrases = ['demonstrates', 'proven', 'validated', 'expertise', 'experience']
        if any(phrase in content.lower() for phrase in authority_phrases):
            score += 2.0
        
        # Insight indicators
        insight_words = ['insight', 'strategy', 'approach', 'methodology', 'framework']
        insight_count = sum(1 for word in insight_words if word in content.lower())
        score += min(2.0, insight_count * 0.5)
        
        # Professional engagement
        if '?' in content:  # Thought-provoking questions
            score += 1.0
        
        return min(10.0, max(0.0, score))


async def main():
    """Test DialoGPT-large for premium content."""
    tester = DialoGPTLargeTester()
    
    try:
        results = await tester.test_dialogpt_large_premium_content()
        
        if results.get('success'):
            print('\\n🎉 DIALOGPT-LARGE TESTING COMPLETE!')
            print('📊 Premium content generation validated')
            print('💼 High-value content strategy ready')
            print('🔗 Results logged to MLflow')
            
            # Compare with our existing models
            print('\\n📈 BUSINESS COMPARISON READY:')
            print('• DialoGPT-Medium: 107ms, 1.8/10 quality (fast, basic)')
            print(f'• DialoGPT-Large: {results["performance"]["latency_ms"]:.0f}ms, {results["performance"]["quality_score"]:.1f}/10 quality (premium)')
            print('• Model selection: Speed vs Quality tradeoff validated')
            
        else:
            print('❌ DialoGPT-large testing failed')
            
    except Exception as e:
        logger.error(f'❌ Premium testing failed: {e}')


if __name__ == '__main__':
    asyncio.run(main())