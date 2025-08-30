#!/usr/bin/env python3
"""
Standardized Generation Parameters - Equalized Decoding Across Models

Ensures all models use identical generation parameters to eliminate
decoding bias and enable fair comparison.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class StandardizedParams:
    """Standardized generation parameters for fair comparison."""
    temperature: float = 0.2
    top_p: float = 0.9
    max_new_tokens: int = 128
    max_context_length: int = 2048  # Fixed KV-cache size
    stop_tokens: List[str] = None
    seed: Optional[int] = None
    
    def __post_init__(self):
        if self.stop_tokens is None:
            self.stop_tokens = ["</s>", "<|endoftext|>", "\n\n\n"]


class ParameterEqualizer:
    """Ensures identical generation parameters across all model frameworks."""
    
    def __init__(self, base_params: Optional[StandardizedParams] = None):
        """Initialize with standardized parameters."""
        self.base_params = base_params or StandardizedParams()
    
    def get_mlx_params(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Get MLX-compatible generation parameters."""
        # MLX has limited parameter support
        return {
            'max_tokens': self.base_params.max_new_tokens,
            'verbose': False,
            # Note: MLX doesn't support temperature/top_p in current version
            # This is a framework limitation, not our implementation
        }
    
    def get_mps_params(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Get PyTorch MPS generation parameters."""
        params = {
            'max_new_tokens': self.base_params.max_new_tokens,
            'temperature': self.base_params.temperature,
            'top_p': self.base_params.top_p,
            'do_sample': True,
            'pad_token_id': None,  # Set by runner based on tokenizer
        }
        
        if seed is not None:
            params['seed'] = seed
            
        return params
    
    def get_llamacpp_params(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """Get llama.cpp generation parameters."""
        params = {
            'max_tokens': self.base_params.max_new_tokens,
            'temperature': self.base_params.temperature,
            'top_p': self.base_params.top_p,
            'stop': self.base_params.stop_tokens,
        }
        
        if seed is not None:
            params['seed'] = seed
            
        return params
    
    def standardize_context_length(self, content: str) -> str:
        """
        Standardize context length to equalize KV-cache impact.
        
        Args:
            content: Input content that may be longer than context limit
            
        Returns:
            Truncated content within context limit
        """
        # Simple word-based truncation (rough approximation)
        words = content.split()
        
        # Approximate: 1 token ≈ 0.75 words for most models
        max_words = int(self.base_params.max_context_length * 0.75)
        
        if len(words) > max_words:
            truncated_words = words[:max_words]
            return ' '.join(truncated_words)
        
        return content
    
    def validate_parameters_equality(self) -> Dict[str, Any]:
        """
        Validate that all frameworks use equivalent parameters.
        
        Returns:
            Report of parameter equality across frameworks
        """
        
        mlx_params = self.get_mlx_params()
        mps_params = self.get_mps_params()
        llamacpp_params = self.get_llamacpp_params()
        
        report = {
            'base_params': {
                'temperature': self.base_params.temperature,
                'top_p': self.base_params.top_p,
                'max_new_tokens': self.base_params.max_new_tokens,
                'max_context_length': self.base_params.max_context_length
            },
            'framework_params': {
                'mlx': mlx_params,
                'mps': mps_params,
                'llamacpp': llamacpp_params
            },
            'equality_analysis': {
                'max_tokens_equal': (
                    mlx_params.get('max_tokens') == 
                    mps_params.get('max_new_tokens') ==
                    llamacpp_params.get('max_tokens')
                ),
                'temperature_support': {
                    'mlx': 'limited',  # MLX doesn't support temperature
                    'mps': 'full',
                    'llamacpp': 'full'
                },
                'framework_limitations': [
                    "MLX: Limited sampling parameter support",
                    "MPS: Full parameter control",
                    "llama.cpp: Full parameter control"
                ]
            }
        }
        
        return report


class FairComparisonManager:
    """Manages fair comparison setup across different model frameworks."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with evaluation configuration."""
        self.config = config
        self.equalizer = ParameterEqualizer()
    
    def prepare_fair_comparison(
        self,
        models: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prepare models for fair comparison.
        
        Args:
            models: List of model configurations
            
        Returns:
            Fair comparison setup report
        """
        
        setup_report = {
            'models_prepared': len(models),
            'parameter_standardization': self.equalizer.validate_parameters_equality(),
            'framework_distribution': {},
            'limitations_identified': []
        }
        
        # Analyze framework distribution
        framework_counts = {}
        for model in models:
            framework = model.get('stack', 'unknown')
            framework_counts[framework] = framework_counts.get(framework, 0) + 1
        
        setup_report['framework_distribution'] = framework_counts
        
        # Identify potential comparison limitations
        if 'mlx' in framework_counts and framework_counts['mlx'] > 0:
            setup_report['limitations_identified'].append(
                "MLX models use simplified parameters (no temperature/top_p)"
            )
        
        return setup_report


def test_parameter_equalization():
    """Test parameter equalization functionality."""
    equalizer = ParameterEqualizer()
    
    print("🧪 Parameter Equalization Test:")
    print("=" * 40)
    
    # Test different framework parameters
    mlx = equalizer.get_mlx_params(seed=42)
    mps = equalizer.get_mps_params(seed=42)
    llamacpp = equalizer.get_llamacpp_params(seed=42)
    
    print(f"MLX params: {mlx}")
    print(f"MPS params: {mps}")  
    print(f"llama.cpp params: {llamacpp}")
    
    # Test equality validation
    validation = equalizer.validate_parameters_equality()
    print(f"\nParameter equality: {validation['equality_analysis']['max_tokens_equal']}")


if __name__ == "__main__":
    test_parameter_equalization()