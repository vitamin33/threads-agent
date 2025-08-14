"""
Test integration of MultiModelManager with existing vLLM service architecture
This ensures backward compatibility while adding multi-model support
"""

import pytest
from .multi_model_manager import MultiModelManager


class TestMultiModelServiceIntegration:
    """Test integration with existing service patterns"""

    @pytest.mark.asyncio
    async def test_backward_compatibility_single_model(self):
        """Test that MultiModelManager can replace vLLMModelManager for single-model use case"""
        manager = MultiModelManager()
        
        # Load a single model (existing behavior)
        result = await manager.load_model("meta-llama/Llama-3.1-8B-Instruct", "general")
        assert result.success is True
        assert result.model_id == "llama_8b"
        
        # Test is_ready() compatibility
        assert manager.is_model_loaded("llama_8b") is True
        
        # Test generate() compatibility - should work with the loaded model
        response = await manager.generate("llama_8b", [{"role": "user", "content": "Hi"}])
        assert response.content is not None
        
        # Test memory usage compatibility
        memory = manager.get_total_memory_usage()
        assert memory > 0
        
        # Test performance stats compatibility
        perf_stats = manager.get_performance_stats("llama_8b")
        assert perf_stats.average_latency_ms >= 0
        assert perf_stats.success_rate > 0

    @pytest.mark.asyncio 
    async def test_multi_model_enhancement(self):
        """Test that MultiModelManager adds multi-model capabilities"""
        manager = MultiModelManager()
        
        # Load multiple models (new capability)
        models = [
            ("meta-llama/Llama-3.1-8B-Instruct", "general"),
            ("meta-llama/Llama-3.1-3B-Instruct", "speed")
        ]
        
        for model_name, content_type in models:
            result = await manager.load_model(model_name, content_type)
            assert result.success is True
        
        # Test that both models are loaded
        assert manager.get_loaded_model_count() == 2
        assert manager.is_model_loaded("llama_8b")
        assert manager.is_model_loaded("llama_3b")
        
        # Test concurrent generation (new capability)
        import asyncio
        tasks = [
            manager.generate("llama_8b", [{"role": "user", "content": "Task 1"}]),
            manager.generate("llama_3b", [{"role": "user", "content": "Task 2"}])
        ]
        
        responses = await asyncio.gather(*tasks)
        assert len(responses) == 2
        for response in responses:
            assert response.content is not None

    @pytest.mark.asyncio
    async def test_service_health_check_compatibility(self):
        """Test compatibility with service health check patterns"""
        manager = MultiModelManager()
        
        # Load model
        await manager.load_model("meta-llama/Llama-3.1-8B-Instruct", "general")
        
        # Test patterns used in health check
        assert manager.is_model_loaded("llama_8b") is True  # Equivalent to model_manager.is_ready()
        
        memory_usage = manager.get_total_memory_usage()
        assert isinstance(memory_usage, float)
        assert memory_usage > 0
        
        # Test performance tracking patterns
        perf_stats = manager.get_performance_stats("llama_8b")
        assert perf_stats.average_latency_ms >= 0

    @pytest.mark.asyncio
    async def test_cleanup_compatibility(self):
        """Test that cleanup works like existing vLLMModelManager"""
        manager = MultiModelManager()
        
        # Load models
        await manager.load_model("meta-llama/Llama-3.1-8B-Instruct", "general")
        await manager.load_model("meta-llama/Llama-3.1-3B-Instruct", "speed")
        assert manager.get_loaded_model_count() == 2
        
        # Test cleanup all (new feature)
        cleanup_result = await manager.cleanup_all_models()
        assert cleanup_result.success is True
        assert manager.get_loaded_model_count() == 0
        
        # Test individual unload (new feature)
        await manager.load_model("meta-llama/Llama-3.1-8B-Instruct", "general")
        unload_result = await manager.unload_model("llama_8b")
        assert unload_result.success is True
        assert not manager.is_model_loaded("llama_8b")