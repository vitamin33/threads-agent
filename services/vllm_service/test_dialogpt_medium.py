#!/usr/bin/env python3
"""
DialoGPT-Medium Testing for Content Generation Comparison

Testing microsoft/DialoGPT-medium for social media content generation:
- Specialized for conversational content and social media
- Compare with TinyLlama results for business metrics
- Focus on Twitter threads, LinkedIn posts, social engagement

Business Questions:
1. Is DialoGPT better for social content than TinyLlama?
2. What's the performance/quality tradeoff?
3. Memory usage comparison for scaling decisions?
4. Cost impact of using specialized vs general models?
"""

import asyncio
import json
import time
import psutil
from pathlib import Path

class DialoGPTContentTester:
    """Test DialoGPT-medium for content generation business metrics."""
    
    def __init__(self):
        """Initialize tester."""
        self.model_name = "microsoft/DialoGPT-medium"
        self.test_prompts = [
            # Social media content (DialoGPT specialty)
            "Write a Twitter thread about AI cost optimization for startups:",
            "Create a LinkedIn post about Apple Silicon for ML engineers:",
            "Draft a professional response to 'What's your AI strategy?':",
            
            # Technical content (comparison with TinyLlama)
            "Explain vLLM benefits for local deployment:",
            "Write a dev.to article intro about model optimization:",
            "Create documentation for Apple Silicon ML setup:"
        ]
        
        # Load previous results for comparison
        self.baseline_results = self._load_baseline_results()
    
    def _load_baseline_results(self):
        """Load TinyLlama results for comparison."""
        try:
            results_file = Path("real_test_results/real_test_results_20250815_151921.json")
            if results_file.exists():
                with open(results_file) as f:
                    data = json.load(f)
                
                # Find TinyLlama results
                for test in data.get("model_tests", []):
                    if "TinyLlama" in test.get("display_name", ""):
                        return test
            return None
        except Exception:
            return None
    
    async def test_dialogpt_medium(self) -> dict:
        """Test DialoGPT-medium with business-focused metrics."""
        print("🧪 TESTING DIALOGPT-MEDIUM FOR CONTENT GENERATION")
        print("=" * 60)
        
        test_result = {
            "model_name": self.model_name,
            "display_name": "DialoGPT Medium (1.5B)",
            "test_timestamp": time.time(),
            "business_focus": "social_media_content_generation"
        }
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            print(f"📦 Loading {self.model_name} for social content testing...")
            load_start = time.time()
            
            # Load model optimized for Apple Silicon
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            dtype = torch.float16 if device == "mps" else torch.float32
            
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                device_map=device if device != "cpu" else None,
                low_cpu_mem_usage=True
            )
            
            if device != "cpu":
                model = model.to(device)
            
            load_time = time.time() - load_start
            
            # Measure real memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_gb = memory_info.rss / (1024**3)
            
            print(f"✅ Loaded in {load_time:.1f}s on {device}")
            print(f"💾 Memory usage: {memory_gb:.1f}GB RSS")
            print("")
            
            # Test content generation with business metrics
            content_results = []
            
            for i, prompt in enumerate(self.test_prompts, 1):
                print(f"📝 Test {i}: {prompt[:50]}...")
                
                inference_start = time.time()
                
                # Generate content
                inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
                if device != "cpu":
                    inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=100,  # Longer for content generation
                        temperature=0.8,     # Higher creativity for content
                        do_sample=True,
                        pad_token_id=tokenizer.pad_token_id,
                        eos_token_id=tokenizer.eos_token_id
                    )
                
                response = tokenizer.decode(outputs[0], skip_special_tokens=True)
                generated_content = response[len(prompt):].strip()
                
                inference_time_ms = (time.time() - inference_start) * 1000
                
                # Business metrics
                content_quality_score = self._assess_content_quality(prompt, generated_content)
                
                result = {
                    "prompt_type": self._categorize_prompt(prompt),
                    "prompt": prompt,
                    "generated_content": generated_content,
                    "inference_time_ms": inference_time_ms,
                    "tokens_generated": len(generated_content.split()),
                    "content_quality_score": content_quality_score,
                    "device": device
                }
                
                content_results.append(result)
                print(f"   ⚡ {inference_time_ms:.0f}ms, Quality: {content_quality_score:.1f}/10")
            
            # Calculate business metrics
            social_media_results = [r for r in content_results if r["prompt_type"] in ["twitter", "linkedin", "social"]]
            technical_results = [r for r in content_results if r["prompt_type"] in ["technical", "dev_article"]]
            
            avg_latency = sum(r["inference_time_ms"] for r in content_results) / len(content_results)
            avg_quality = sum(r["content_quality_score"] for r in content_results) / len(content_results)
            total_tokens = sum(r["tokens_generated"] for r in content_results)
            tokens_per_second = total_tokens / (sum(r["inference_time_ms"] for r in content_results) / 1000)
            
            test_result.update({
                "success": True,
                "load_time_seconds": load_time,
                "memory_usage_gb": memory_gb,
                "device": device,
                "content_results": content_results,
                "business_metrics": {
                    "average_latency_ms": avg_latency,
                    "average_content_quality": avg_quality,
                    "tokens_per_second": tokens_per_second,
                    "social_media_performance": {
                        "test_count": len(social_media_results),
                        "avg_latency_ms": sum(r["inference_time_ms"] for r in social_media_results) / max(len(social_media_results), 1),
                        "avg_quality": sum(r["content_quality_score"] for r in social_media_results) / max(len(social_media_results), 1)
                    },
                    "technical_content_performance": {
                        "test_count": len(technical_results), 
                        "avg_latency_ms": sum(r["inference_time_ms"] for r in technical_results) / max(len(technical_results), 1),
                        "avg_quality": sum(r["content_quality_score"] for r in technical_results) / max(len(technical_results), 1)
                    }
                }
            })
            
            print(f"📊 DialoGPT-Medium Results:")
            print(f"   Average latency: {avg_latency:.0f}ms")
            print(f"   Content quality: {avg_quality:.1f}/10")
            print(f"   Tokens/second: {tokens_per_second:.1f}")
            print(f"   Memory usage: {memory_gb:.1f}GB")
            print("")
            
            # Compare with baseline if available
            if self.baseline_results:
                await self._compare_with_baseline(test_result)
            
            return test_result
            
        except Exception as e:
            print(f"❌ DialoGPT test failed: {e}")
            test_result.update({"success": False, "error": str(e)})
            return test_result
    
    def _categorize_prompt(self, prompt: str) -> str:
        """Categorize prompt by content type."""
        prompt_lower = prompt.lower()
        if "twitter" in prompt_lower:
            return "twitter"
        elif "linkedin" in prompt_lower:
            return "linkedin"
        elif "dev.to" in prompt_lower or "technical" in prompt_lower:
            return "technical"
        elif "documentation" in prompt_lower:
            return "dev_article"
        else:
            return "social"
    
    def _assess_content_quality(self, prompt: str, content: str) -> float:
        """Simple content quality assessment (0-10 scale)."""
        score = 5.0  # Base score
        
        # Length appropriateness
        if 50 <= len(content.split()) <= 200:
            score += 1.0
        
        # Content relevance
        prompt_words = set(prompt.lower().split())
        content_words = set(content.lower().split())
        relevance = len(prompt_words & content_words) / len(prompt_words)
        score += relevance * 2.0
        
        # Professional tone for business content
        professional_words = ["professional", "strategy", "optimization", "implementation", "analysis"]
        if any(word in content.lower() for word in professional_words):
            score += 1.0
        
        # Penalize very short or very long responses
        if len(content.split()) < 10:
            score -= 2.0
        elif len(content.split()) > 300:
            score -= 1.0
            
        return min(10.0, max(0.0, score))
    
    async def _compare_with_baseline(self, dialogpt_result: dict):
        """Compare DialoGPT results with TinyLlama baseline."""
        print("📊 BUSINESS COMPARISON: DialoGPT vs TinyLlama")
        print("=" * 50)
        
        baseline_latency = self.baseline_results["performance_metrics"]["average_latency_ms"]
        baseline_throughput = self.baseline_results["performance_metrics"]["tokens_per_second"]
        baseline_memory = self.baseline_results["memory_usage"]["rss_gb"]
        
        dialogpt_latency = dialogpt_result["business_metrics"]["average_latency_ms"]
        dialogpt_throughput = dialogpt_result["business_metrics"]["tokens_per_second"]
        dialogpt_memory = dialogpt_result["memory_usage_gb"]
        
        # Performance comparison
        latency_change = ((dialogpt_latency - baseline_latency) / baseline_latency) * 100
        throughput_change = ((dialogpt_throughput - baseline_throughput) / baseline_throughput) * 100
        memory_change = ((dialogpt_memory - baseline_memory) / baseline_memory) * 100
        
        print("📈 Performance Comparison:")
        print(f"   Latency: {dialogpt_latency:.0f}ms vs {baseline_latency:.0f}ms ({latency_change:+.1f}%)")
        print(f"   Throughput: {dialogpt_throughput:.1f} vs {baseline_throughput:.1f} tok/sec ({throughput_change:+.1f}%)")
        print(f"   Memory: {dialogpt_memory:.1f}GB vs {baseline_memory:.1f}GB ({memory_change:+.1f}%)")
        
        # Business recommendation
        print("")
        print("💼 Business Recommendation:")
        if dialogpt_latency < baseline_latency * 1.2 and dialogpt_result["business_metrics"]["average_content_quality"] > 6.0:
            print("✅ DialoGPT-medium recommended for social content")
            print("   Better specialized for social media and professional posts")
        elif dialogpt_latency > baseline_latency * 2.0:
            print("⚠️  DialoGPT-medium slower - use for high-quality content only")
        else:
            print("🔄 Mixed results - choose based on content type priority")
        
        print("")


async def main():
    """Run DialoGPT-medium testing."""
    tester = DialoGPTContentTester()
    
    try:
        results = await tester.test_dialogpt_medium()
        
        # Save results
        results_file = Path("dialogpt_medium_test_results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"📄 Results saved to: {results_file}")
        print("")
        print("🎯 BUSINESS INSIGHTS READY!")
        print("✅ Content generation model comparison data")
        print("✅ Performance vs quality tradeoff analysis") 
        print("✅ Memory scaling insights for multi-model deployment")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())