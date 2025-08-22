#!/usr/bin/env python3
"""
Llama.cpp GGUF Runner - Quantized Model Optimization

Runs quantized GGUF models via llama.cpp for memory efficiency
and Apple Silicon optimization.
"""

import subprocess
import json
from typing import Dict, Any, Optional
from pathlib import Path


class LlamaCppRunner:
    """Llama.cpp GGUF model runner for quantized models."""
    
    def __init__(self, model_id: str, gguf_path: Optional[str] = None):
        """Initialize llama.cpp runner."""
        self.model_id = model_id
        self.gguf_path = gguf_path or self._find_gguf_model(model_id)
        self.llama_cpp_path = self._find_llama_cpp()
        
    def _find_gguf_model(self, model_id: str) -> Optional[str]:
        """Find GGUF model file."""
        # Common GGUF locations
        gguf_locations = [
            Path.home() / ".cache" / "llama.cpp" / f"{model_id}.gguf",
            Path.cwd() / "models" / f"{model_id}.gguf",
            Path(f"./gguf/{model_id}.gguf")
        ]
        
        for location in gguf_locations:
            if location.exists():
                return str(location)
        
        return None
    
    def _find_llama_cpp(self) -> Optional[str]:
        """Find llama.cpp executable."""
        # Check common locations
        cpp_paths = [
            "/opt/homebrew/bin/llama-cpp",
            "/usr/local/bin/llama-cpp", 
            "./llama.cpp/main",
            "llama-cpp"
        ]
        
        for path in cpp_paths:
            try:
                result = subprocess.run([path, "--version"], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return path
            except:
                continue
        
        return None
    
    def load_model(self) -> bool:
        """Validate model and llama.cpp availability."""
        if not self.gguf_path:
            print(f"   ❌ GGUF model not found for {self.model_id}")
            return False
        
        if not self.llama_cpp_path:
            print(f"   ❌ llama.cpp executable not found")
            return False
        
        print(f"   ✅ GGUF model: {self.gguf_path}")
        print(f"   ✅ llama.cpp: {self.llama_cpp_path}")
        return True
    
    def generate(self, prompt: str, sampling_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using llama.cpp."""
        if not self.gguf_path or not self.llama_cpp_path:
            raise RuntimeError("llama.cpp not properly configured")
        
        # Build llama.cpp command
        cmd = [
            self.llama_cpp_path,
            "-m", self.gguf_path,
            "-p", prompt,
            "-n", str(sampling_params.get("max_new_tokens", 128)),
            "--temp", str(sampling_params.get("temperature", 0.2)),
            "--top-p", str(sampling_params.get("top_p", 0.9)),
            "--seed", str(sampling_params.get("seed", 42)),
            "--no-display-prompt"
        ]
        
        try:
            # Run llama.cpp with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                generated_content = result.stdout.strip()
                
                return {
                    "content": generated_content,
                    "prompt": prompt,
                    "device": "apple_silicon_cpu",
                    "stack": "llamacpp",
                    "model_id": self.model_id
                }
            else:
                raise RuntimeError(f"llama.cpp failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("llama.cpp generation timeout")
    
    def cleanup(self):
        """Cleanup resources (no-op for llama.cpp)."""
        pass


def create_llamacpp_runner(model_config: Dict[str, Any]) -> LlamaCppRunner:
    """Create llama.cpp runner for model configuration."""
    return LlamaCppRunner(
        model_id=model_config["id"]
    )