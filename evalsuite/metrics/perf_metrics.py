#!/usr/bin/env python3
"""
Performance Metrics Module - Apple Silicon Optimization

Measures p50/p95 latency, tokens/sec, peak RSS, and context usage
with consistent sampling and warmups for Apple Silicon models.
"""

import time
import psutil
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance metrics for model evaluation."""
    p50_latency_ms: float
    p95_latency_ms: float
    tokens_per_second: float
    peak_rss_mb: float
    context_length: int
    warmup_runs: int
    timed_runs: int
    device: str
    stack: str


class PerformanceProfiler:
    """Profile model performance with Apple Silicon optimization."""
    
    def __init__(self, warmup_runs: int = 5, timed_runs: int = 20):
        """Initialize performance profiler."""
        self.warmup_runs = warmup_runs
        self.timed_runs = timed_runs
        self.process = psutil.Process()
    
    def measure_model_performance(
        self, 
        model_runner,
        test_prompt: str,
        sampling_params: Dict[str, Any],
        stack: str
    ) -> PerformanceMetrics:
        """Measure comprehensive model performance."""
        
        print(f"🔧 Profiling {stack} performance...")
        
        # Baseline memory
        baseline_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        peak_memory = baseline_memory
        
        # Warmup runs
        print(f"   🔥 Warmup: {self.warmup_runs} runs...")
        for i in range(self.warmup_runs):
            try:
                _ = model_runner.generate(test_prompt, sampling_params)
                current_memory = self.process.memory_info().rss / (1024 * 1024)
                peak_memory = max(peak_memory, current_memory)
            except Exception as e:
                print(f"   ⚠️  Warmup {i+1} failed: {e}")
        
        # Timed runs
        print(f"   ⏱️  Timed runs: {self.timed_runs} iterations...")
        latencies = []
        token_counts = []
        
        for i in range(self.timed_runs):
            try:
                start_time = time.perf_counter()
                
                # Generate with timing
                result = model_runner.generate(test_prompt, sampling_params)
                
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                
                # Track tokens generated
                if isinstance(result, dict) and 'content' in result:
                    tokens = len(result['content'].split())
                else:
                    tokens = len(str(result).split())
                
                latencies.append(latency_ms)
                token_counts.append(tokens)
                
                # Update peak memory
                current_memory = self.process.memory_info().rss / (1024 * 1024)
                peak_memory = max(peak_memory, current_memory)
                
                if (i + 1) % 5 == 0:
                    print(f"      Progress: {i+1}/{self.timed_runs}")
                
            except Exception as e:
                print(f"   ❌ Timed run {i+1} failed: {e}")
        
        if not latencies:
            raise RuntimeError("No successful performance measurements")
        
        # Calculate performance statistics
        p50_latency = statistics.median(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        
        total_tokens = sum(token_counts)
        total_time_s = sum(latencies) / 1000
        tokens_per_second = total_tokens / total_time_s if total_time_s > 0 else 0
        
        # Context length estimation
        context_length = len(test_prompt.split()) + statistics.mean(token_counts)
        
        # Device detection
        device = self._detect_device()
        
        metrics = PerformanceMetrics(
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            tokens_per_second=tokens_per_second,
            peak_rss_mb=peak_memory - baseline_memory,
            context_length=int(context_length),
            warmup_runs=self.warmup_runs,
            timed_runs=len(latencies),
            device=device,
            stack=stack
        )
        
        print(f"   📊 Performance: {p50_latency:.0f}ms p50, {tokens_per_second:.1f} tok/s")
        
        return metrics
    
    def _detect_device(self) -> str:
        """Detect the computation device."""
        try:
            import torch
            if torch.backends.mps.is_available():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        except ImportError:
            return "unknown"


def profile_model_stack(model_runner, sampling_params: Dict[str, Any], stack: str) -> PerformanceMetrics:
    """Profile a model with specific stack."""
    
    profiler = PerformanceProfiler()
    
    # Standard test prompt for consistent measurement
    test_prompt = "Write a professional LinkedIn post about AI infrastructure optimization:"
    
    return profiler.measure_model_performance(
        model_runner, 
        test_prompt, 
        sampling_params, 
        stack
    )