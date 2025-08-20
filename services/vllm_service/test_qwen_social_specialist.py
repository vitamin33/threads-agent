#!/usr/bin/env python3
"""
Qwen-2.5-7B Social Media Specialist Testing

Testing Qwen-2.5-7B-Instruct for social media content specialization:
- 128k context length for long-form content
- Multilingual capabilities for diverse content
- Social media optimization
- Expected 8.0-8.5/10 quality for social content

Goal: Test if Qwen beats OPT-2.7B (8.40/10) for social media use cases
Specialty: LinkedIn, Twitter, social automation content
"""

import asyncio
import json
import statistics
import time
import requests
from datetime import datetime

import mlflow


async def test_qwen_social_media_specialist():
    """Test Qwen-2.5-7B for social media content specialization."""
    
    mlflow.set_tracking_uri("file:./enhanced_business_mlflow")
    mlflow.set_experiment("rigorous_statistical_validation")
    
    run_name = f"qwen_social_specialist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    with mlflow.start_run(run_name=run_name) as run:
        try:
            # Log social media specialist metadata
            mlflow.log_param("model_name", "qwen2.5:7b")
            mlflow.log_param("display_name", "Qwen-2.5-7B-Social-Specialist")
            mlflow.log_param("specialization", "social_media_long_context")
            mlflow.log_param("context_length", "128k_tokens")
            mlflow.log_param("multilingual", "yes")
            mlflow.log_param("challenge_target", "beat_opt_2_7b_for_social_content")
            
            print("🌟 QWEN-2.5-7B SOCIAL MEDIA SPECIALIST TESTING")
            print("=" * 60)
            print("🎯 Goal: Test social media content specialization")
            print("📱 Focus: LinkedIn, Twitter, social automation")
            print("🌐 Features: 128k context + multilingual")
            print("🥇 Benchmark: OPT-2.7B (8.40/10) general business content")
            print("")
            
            # Check Qwen availability
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                models = response.json().get("models", [])
                qwen_available = any("qwen" in model["name"] for model in models)
                
                if not qwen_available:
                    raise Exception("Qwen model not found - still downloading")
                
                print("✅ Qwen-2.5-7B ready for social media testing")
                
            except Exception as e:
                print(f"❌ Qwen not ready: {e}")
                mlflow.log_param("error", f"qwen_not_ready_{e}")
                return {"success": False, "error": str(e)}
            
            # === SOCIAL MEDIA CONTENT SPECIALIZATION TESTS ===
            print("\\n📱 Social Media Content Specialization Testing:")
            
            social_media_prompts = [
                {
                    "type": "linkedin_thought_leadership",
                    "prompt": "Write a LinkedIn thought leadership post about 'AI Cost Optimization: Real Results from Local Deployment' that establishes technical authority and attracts consulting opportunities:",
                    "target_platform": "linkedin",
                    "content_goal": "thought_leadership"
                },
                {
                    "type": "twitter_technical_thread",
                    "prompt": "Write a Twitter thread about 'Apple Silicon ML Performance: Measured Results' that showcases technical expertise and attracts industry attention:",
                    "target_platform": "twitter",
                    "content_goal": "technical_showcase"
                },
                {
                    "type": "linkedin_professional_update",
                    "prompt": "Create a professional LinkedIn update about 'MLflow Experiment Tracking: Enterprise Methodology' that demonstrates MLOps expertise:",
                    "target_platform": "linkedin",
                    "content_goal": "professional_expertise"
                },
                {
                    "type": "social_engagement_content",
                    "prompt": "Write engaging social media content about 'Local AI vs Cloud: Performance and Cost Analysis' that generates discussion and shares:",
                    "target_platform": "social_general",
                    "content_goal": "engagement_generation"
                },
                {
                    "type": "technical_authority_content",
                    "prompt": "Create authoritative technical content about 'Multi-Model Deployment Architecture' that establishes industry expertise:",
                    "target_platform": "technical_social",
                    "content_goal": "authority_building"
                }
            ]
            
            qwen_social_qualities = []
            qwen_social_latencies = []
            social_engagement_scores = []
            platform_optimization_scores = []
            
            for test in social_media_prompts:
                print(f"\\n   📱 {test['type']} ({test['target_platform']}):")
                print(f"      Goal: {test['content_goal']}")
                
                try:
                    inference_start = time.time()
                    
                    # Qwen social media generation
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "qwen2.5:7b",
                            "prompt": test['prompt'],
                            "stream": False,
                            "options": {
                                "temperature": 0.8,  # Social content creativity
                                "top_p": 0.9,
                                "num_predict": 150   # Longer for social content
                            }
                        },
                        timeout=60
                    )
                    
                    inference_time = (time.time() - inference_start) * 1000
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result.get("response", "").strip()
                        
                        # Social media quality assessment
                        social_quality = assess_social_media_quality(content, test['target_platform'])
                        engagement_potential = assess_engagement_potential(content, test['content_goal'])
                        
                        qwen_social_qualities.append(social_quality)
                        qwen_social_latencies.append(inference_time)
                        social_engagement_scores.append(engagement_potential)
                        
                        print(f"      ✅ {inference_time:.0f}ms")
                        print(f"      📊 Social Quality: {social_quality:.1f}/10")
                        print(f"      🎯 Engagement: {engagement_potential:.1f}/10")
                    else:
                        print(f"      ❌ API error: {response.status_code}")
                        
                except Exception as e:
                    print(f"      ❌ Test failed: {e}")
            
            # === SOCIAL MEDIA SPECIALIST ANALYSIS ===
            if qwen_social_qualities:
                qwen_social_quality = statistics.mean(qwen_social_qualities)
                confidence_interval = 1.96 * (statistics.stdev(qwen_social_qualities) / (len(qwen_social_qualities) ** 0.5)) if len(qwen_social_qualities) > 1 else 0
                qwen_engagement = statistics.mean(social_engagement_scores)
                qwen_latency = statistics.mean(qwen_social_latencies)
                
                # Compare with OPT-2.7B for social content
                opt_champion_quality = 8.40
                social_vs_champion = qwen_social_quality - opt_champion_quality
                
                # Log social media specialist metrics
                mlflow.log_metric("qwen_social_quality", qwen_social_quality)
                mlflow.log_metric("qwen_social_confidence", confidence_interval)
                mlflow.log_metric("qwen_engagement_potential", qwen_engagement)
                mlflow.log_metric("qwen_social_latency", qwen_latency)
                mlflow.log_metric("qwen_vs_champion_social", social_vs_champion)
                
                # Social media recommendation
                if qwen_social_quality > opt_champion_quality:
                    social_recommendation = "qwen_superior_for_social_media"
                    social_tier = "social_media_champion"
                elif qwen_social_quality >= 8.0:
                    social_recommendation = "qwen_excellent_for_social_media"
                    social_tier = "social_media_specialist"
                elif qwen_social_quality >= 7.0:
                    social_recommendation = "qwen_good_for_social_media"
                    social_tier = "social_media_capable"
                else:
                    social_recommendation = "opt_better_for_social_media"
                    social_tier = "general_content_better"
                
                mlflow.set_tag("qwen_social_recommendation", social_recommendation)
                mlflow.set_tag("qwen_social_tier", social_tier)
                mlflow.set_tag("specialization_focus", "social_media_content")
                
                print(f"\\n🌟 QWEN SOCIAL MEDIA SPECIALIST RESULTS:")
                print("=" * 70)
                print(f"📱 Social Quality: {qwen_social_quality:.2f} ± {confidence_interval:.2f}")
                print(f"🎯 Engagement Potential: {qwen_engagement:.2f}/10")
                print(f"⚡ Social Latency: {qwen_latency:.0f}ms")
                print(f"📊 vs OPT-2.7B: {social_vs_champion:+.2f} points")
                print(f"🏆 Social Media Tier: {social_tier}")
                print(f"💼 Recommendation: {social_recommendation}")
                
                # Social media specialization decision
                if qwen_social_quality > opt_champion_quality:
                    print("\\n🎉 NEW SOCIAL MEDIA CHAMPION: QWEN-2.5-7B!")
                    print("✅ Superior for LinkedIn, Twitter, social automation")
                elif qwen_social_quality >= 8.0:
                    print("\\n✅ EXCELLENT SOCIAL MEDIA SPECIALIST!")
                    print("Perfect for social content, OPT-2.7B for general business")
                else:
                    print("\\n📊 OPT-2.7B REMAINS SUPERIOR")
                    print("Better for general business content including social")
                
                return {
                    "qwen_social_quality": qwen_social_quality,
                    "engagement_potential": qwen_engagement,
                    "vs_champion": social_vs_champion,
                    "social_tier": social_tier,
                    "success": True
                }
            else:
                return {"success": False, "error": "no_social_tests_completed"}
                
        except Exception as e:
            mlflow.log_param("error", str(e))
            print(f"❌ Qwen social media test failed: {e}")
            return {"success": False, "error": str(e)}


def assess_social_media_quality(content: str, platform: str) -> float:
    """Assess social media content quality."""
    if not content or len(content.strip()) < 20:
        return 0.0
    
    score = 5.0
    words = content.split()
    
    # Platform-specific length optimization
    if platform == "twitter":
        if 50 <= len(words) <= 100:  # Twitter optimal
            score += 3.0
    elif platform == "linkedin":
        if 100 <= len(words) <= 280:  # LinkedIn optimal
            score += 3.0
    else:
        if 80 <= len(words) <= 200:  # General social
            score += 3.0
    
    # Social media vocabulary
    social_terms = ["insights", "tips", "strategy", "results", "proven", "game-changing"]
    term_count = sum(1 for term in social_terms if term in content.lower())
    score += min(2.0, term_count * 0.4)
    
    return min(10.0, score)


def assess_engagement_potential(content: str, goal: str) -> float:
    """Assess social media engagement potential."""
    score = 5.0
    
    # Engagement indicators
    if "?" in content:  # Questions engage
        score += 1.0
    
    # Authority building
    if any(term in content.lower() for term in ["proven", "results", "achieved"]):
        score += 2.0
    
    # Call to action
    if any(cta in content.lower() for cta in ["share", "thoughts", "discuss"]):
        score += 1.0
    
    # Professional credibility
    if any(term in content.lower() for term in ["expertise", "experience", "demonstrated"]):
        score += 1.0
    
    return min(10.0, score)


async def main():
    """Test Qwen social media specialization."""
    print("🌟 QWEN-2.5-7B SOCIAL MEDIA SPECIALIST TESTING")
    print("=" * 70)
    print("🎯 Specialty: Social media + long context (128k)")
    print("📱 Focus: LinkedIn, Twitter, social automation")
    print("🥇 Benchmark: OPT-2.7B (8.40/10)")
    print("")
    
    # Check if Qwen is ready
    try:
        models_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = models_response.json().get("models", [])
        qwen_ready = any("qwen" in model["name"] for model in models)
        
        if qwen_ready:
            print("✅ Qwen-2.5-7B ready for testing!")
            results = await test_qwen_social_media_specialist()
            
            if results.get("success"):
                quality = results["qwen_social_quality"]
                engagement = results["engagement_potential"]
                
                print("\\n🎉 QWEN SOCIAL MEDIA TESTING COMPLETE!")
                print(f"📱 Social Quality: {quality:.2f}/10")
                print(f"🎯 Engagement: {engagement:.2f}/10")
                
            print("\\n🔗 Results: http://127.0.0.1:5000")
            
        else:
            print("⏳ Qwen-2.5-7B still downloading...")
            print("💡 Run again when download completes")
            
    except Exception as e:
        print(f"❌ Qwen testing setup failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())