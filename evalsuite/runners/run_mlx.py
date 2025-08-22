#!/usr/bin/env python3
"""
MLX Runner - Apple Silicon Native Framework

Runs models using MLX framework for optimal Apple Silicon
performance and memory efficiency.
"""

from typing import Dict, Any, Optional


class MLXModelRunner:
    """MLX model runner for Apple Silicon native performance."""
    
    def __init__(self, model_id: str, hf_model: str):
        """Initialize MLX model runner."""
        self.model_id = model_id
        self.hf_model = hf_model
        self.model = None
        self.tokenizer = None
        
    def load_model(self) -> bool:
        """Load model with MLX framework."""
        try:
            # Try to import MLX
            try:
                import mlx.core as mx
                import mlx.nn as nn
                from mlx_lm import load, generate
                
                print(f"📦 Loading {self.model_id} with MLX framework...")
                
                # Load model and tokenizer with MLX
                self.model, self.tokenizer = load(self.hf_model)
                
                print(f"   ✅ MLX model loaded successfully")
                return True
                
            except ImportError:
                print(f"   ❌ MLX framework not available")
                print(f"   💡 Install with: pip install mlx-lm")
                return False
                
        except Exception as e:
            print(f"   ❌ MLX loading failed: {e}")
            return False
    
    def generate(self, prompt: str, sampling_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using MLX framework."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("MLX model not loaded")
        
        try:
            # MLX generation
            from mlx_lm import generate
            
            response = generate(
                self.model,
                self.tokenizer, 
                prompt=prompt,
                max_tokens=sampling_params.get("max_new_tokens", 128),
                temp=sampling_params.get("temperature", 0.2),
                top_p=sampling_params.get("top_p", 0.9)
            )
            
            # Extract generated content
            if isinstance(response, str):
                generated_content = response[len(prompt):].strip()
            else:
                generated_content = str(response).strip()
            
            return {
                "content": generated_content,
                "prompt": prompt,
                "device": "apple_silicon_mlx",
                "stack": "mlx", 
                "model_id": self.model_id
            }
            
        except Exception as e:
            raise RuntimeError(f"MLX generation failed: {e}")
    
    def cleanup(self):
        """Cleanup MLX resources."""
        self.model = None
        self.tokenizer = None
        
        # MLX automatic memory management
        try:
            import mlx.core as mx
            mx.metal.clear_cache()
        except:
            pass


def create_mlx_runner(model_config: Dict[str, Any]) -> MLXModelRunner:
    """Create MLX runner for model configuration."""
    return MLXModelRunner(
        model_id=model_config["id"],
        hf_model=model_config["hf_model"]
    )