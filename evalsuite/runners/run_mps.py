#!/usr/bin/env python3
"""
PyTorch MPS Runner - Apple Silicon Optimization

Runs models using PyTorch with Metal Performance Shaders
for optimal Apple Silicon M4 Max performance.
"""

import time
import torch
from typing import Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForCausalLM


class MPSModelRunner:
    """PyTorch MPS model runner for Apple Silicon."""
    
    def __init__(self, model_id: str, hf_model: str):
        """Initialize MPS model runner."""
        self.model_id = model_id
        self.hf_model = hf_model
        self.model = None
        self.tokenizer = None
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        
    def load_model(self) -> bool:
        """Load model with Apple Silicon optimization."""
        try:
            print(f"📦 Loading {self.model_id} with MPS optimization...")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.hf_model, trust_remote_code=True)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model with Apple Silicon optimization
            self.model = AutoModelForCausalLM.from_pretrained(
                self.hf_model,
                torch_dtype=torch.float16 if self.device == "mps" else torch.float32,
                device_map=self.device if self.device != "cpu" else None,
                low_cpu_mem_usage=True,
                trust_remote_code=True  # Allow custom code for enterprise models
            )
            
            if self.device != "cpu":
                self.model = self.model.to(self.device)
            
            print(f"   ✅ Loaded on {self.device}")
            return True
            
        except Exception as e:
            print(f"   ❌ Loading failed: {e}")
            return False
    
    def generate(self, prompt: str, sampling_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content with MPS acceleration."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")
        
        # Tokenize input
        inputs = self.tokenizer(
            prompt, 
            return_tensors="pt", 
            padding=True, 
            truncation=True
        )
        
        if self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate with specified parameters
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=sampling_params.get("max_new_tokens", 128),
                temperature=sampling_params.get("temperature", 0.2),
                top_p=sampling_params.get("top_p", 0.9),
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id
            )
        
        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated_content = response[len(prompt):].strip()
        
        return {
            "content": generated_content,
            "prompt": prompt,
            "device": self.device,
            "stack": "mps",
            "model_id": self.model_id
        }
    
    def cleanup(self):
        """Clean up model resources."""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        
        if self.device == "mps":
            torch.mps.empty_cache()
        
        import gc
        gc.collect()


def create_mps_runner(model_config: Dict[str, Any]) -> MPSModelRunner:
    """Create MPS runner for model configuration."""
    return MPSModelRunner(
        model_id=model_config["id"],
        hf_model=model_config["hf_model"]
    )