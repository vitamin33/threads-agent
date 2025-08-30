#!/usr/bin/env python3
"""
Configuration Tests - Validate Evaluation Setup

Tests configuration loading, model registry, and environment setup.
"""

import pytest
import yaml
from pathlib import Path


def test_experiment_config_valid():
    """Test that experiment.yml is valid and complete."""
    config_path = Path("evalsuite/configs/experiment.yml")
    assert config_path.exists(), "experiment.yml not found"
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Required top-level keys
    required_keys = ["models", "sampling", "seeds", "power", "cloud_baseline", "mlflow"]
    for key in required_keys:
        assert key in config, f"Missing required config key: {key}"
    
    # Model configuration validation
    assert len(config["models"]) > 0, "No models configured"
    
    for model in config["models"]:
        required_model_keys = ["id", "hf_model", "stack", "license"]
        for key in required_model_keys:
            assert key in model, f"Model missing required key: {key}"
    
    # Sampling parameters
    sampling = config["sampling"]
    assert "temperature" in sampling
    assert "top_p" in sampling
    assert "max_new_tokens" in sampling
    assert isinstance(sampling["max_new_tokens"], list)


def test_judge_prompt_exists():
    """Test that judge prompt is available."""
    prompt_path = Path("evalsuite/configs/judge_prompt.txt")
    assert prompt_path.exists(), "judge_prompt.txt not found"
    
    with open(prompt_path) as f:
        content = f.read()
    
    assert len(content) > 100, "Judge prompt too short"
    assert "criteria" in content.lower(), "Judge prompt missing criteria"


def test_dataset_prompts_complete():
    """Test that all prompt datasets are complete."""
    dataset_dir = Path("evalsuite/data/prompts")
    assert dataset_dir.exists(), "Dataset directory not found"
    
    required_tasks = ["linkedin", "cold_email", "product_blurb", "tech_summary"]
    
    for task in required_tasks:
        task_file = dataset_dir / f"{task}.jsonl"
        assert task_file.exists(), f"Task file not found: {task}.jsonl"
        
        # Count prompts
        with open(task_file) as f:
            prompts = [line for line in f if line.strip()]
        
        assert len(prompts) >= 10, f"Task {task} has insufficient prompts: {len(prompts)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])