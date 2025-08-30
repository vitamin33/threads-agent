#!/usr/bin/env python3
"""
Model Download Automation Script for vLLM Service.

Downloads all 5 models for MacBook M4 Max deployment:
1. Llama-3.1-8B-Instruct (16GB)
2. Qwen2.5-7B-Instruct (14GB)
3. Mistral-7B-Instruct-v0.3 (14GB)
4. Llama-3.1-3B-Instruct (6GB)
5. Phi-3.5-Mini-Instruct (8GB)

Features:
- Progressive download with resumption
- Storage optimization for M4 Max
- Integrity verification
- Progress reporting

Usage:
    python download_models.py
    python download_models.py --model llama_8b
    python download_models.py --content-type twitter
    python download_models.py --verify-only
"""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.vllm_service.model_downloader import (
    get_model_downloader,
    DownloadProgress,
)
from services.vllm_service.cache_manager import get_cache_manager, get_m4_max_optimizer
from services.vllm_service.model_registry import get_model_registry, ContentType

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DownloadOrchestrator:
    """Orchestrates model downloads with progress reporting."""

    def __init__(self):
        """Initialize download orchestrator."""
        self.downloader = get_model_downloader()
        self.cache_manager = get_cache_manager()
        self.registry = get_model_registry()
        self.optimizer = get_m4_max_optimizer()

        # Progress tracking
        self.download_start_time = None
        self.completed_downloads = 0
        self.total_downloads = 0

    def progress_callback(self, model_id: str, progress: DownloadProgress):
        """Callback for download progress updates."""
        print(
            f"  {model_id}: {progress.progress_percent:.1f}% ({progress.downloaded_gb:.1f}/{progress.total_size_gb:.1f}GB)"
        )

        if progress.eta_seconds:
            eta_min = progress.eta_seconds / 60
            print(f"    ETA: {eta_min:.1f} minutes")

    async def download_all_models(self) -> Dict[str, bool]:
        """Download all models from registry."""
        print("🚀 Starting download of all registry models...")
        print(f"📁 Cache directory: {self.downloader.cache_dir}")
        print(f"💾 Max cache size: {self.downloader.max_cache_size_gb}GB")
        print("")

        self.download_start_time = time.time()
        models = list(self.registry.models.keys())
        self.total_downloads = len(models)

        results = {}

        for model_id in models:
            config = self.registry.get_model_config(model_id)
            print(f"📦 Downloading {model_id}: {config.name}")
            print(
                f"   Priority: {config.priority}, Memory: {config.memory_requirements.base_gb:.1f}GB"
            )

            try:
                cache_info = await self.downloader.download_model(
                    model_id, lambda p: self.progress_callback(model_id, p)
                )

                results[model_id] = True
                self.completed_downloads += 1

                print(f"   ✅ Downloaded: {cache_info.size_gb:.1f}GB")
                print(f"   📍 Location: {cache_info.cache_path}")
                print("")

            except Exception as e:
                results[model_id] = False
                print(f"   ❌ Failed: {e}")
                print("")

        # Summary
        total_time = time.time() - self.download_start_time
        success_count = sum(1 for success in results.values() if success)

        print("🏁 Download Summary:")
        print(f"   Successful: {success_count}/{self.total_downloads}")
        print(f"   Total time: {total_time:.1f} seconds")
        print(f"   Cache size: {await self.cache_manager._get_cache_size_gb():.1f}GB")

        return results

    async def download_for_content_type(
        self, content_type: ContentType
    ) -> Dict[str, bool]:
        """Download models for specific content type."""
        print(f"🎯 Downloading models for content type: {content_type.value}")

        models = self.registry.get_models_by_content_type(content_type)
        model_ids = [model.model_id for model in models]

        print(f"📋 Models needed: {model_ids}")
        print("")

        results = {}
        for model_id in model_ids:
            config = self.registry.get_model_config(model_id)
            print(f"📦 Downloading {model_id}: {config.name}")

            try:
                cache_info = await self.downloader.download_model(
                    model_id, lambda p: self.progress_callback(model_id, p)
                )
                results[model_id] = True
                print(f"   ✅ Downloaded: {cache_info.size_gb:.1f}GB")

            except Exception as e:
                results[model_id] = False
                print(f"   ❌ Failed: {e}")

            print("")

        return results

    async def verify_all_models(self) -> Dict[str, bool]:
        """Verify integrity of all cached models."""
        print("🔍 Verifying cached model integrity...")

        verification_results = await self.downloader.verify_all_models()

        print("📊 Verification Results:")
        for model_id, is_valid in verification_results.items():
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"   {model_id}: {status}")

        valid_count = sum(1 for valid in verification_results.values() if valid)
        print(f"\nValid models: {valid_count}/{len(verification_results)}")

        return verification_results

    async def optimize_cache(self) -> None:
        """Run cache optimization for M4 Max."""
        print("⚡ Running M4 Max cache optimization...")

        # Run M4 Max specific optimizations
        m4_max_results = await self.optimizer.optimize_for_m4_max()

        print("🍎 Apple Silicon M4 Max Optimizations:")
        for optimization in m4_max_results["cache_optimizations"]:
            print(f"   • {optimization['optimization']}: {optimization['description']}")

        print(f"   Memory efficiency: {m4_max_results['memory_efficiency']:.1%}")

        # Run general cache optimization
        cleanup_results = await self.cache_manager.intelligent_cleanup()

        print("🧹 Cache Cleanup Results:")
        print(f"   Models removed: {cleanup_results.models_removed}")
        print(f"   Space freed: {cleanup_results.space_freed_gb:.1f}GB")
        print(
            f"   Hit rate improvement: +{cleanup_results.cache_hit_rate_improvement:.1%}"
        )

        if cleanup_results.recommended_actions:
            print("💡 Recommendations:")
            for action in cleanup_results.recommended_actions:
                print(f"   • {action}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Download and manage vLLM models")
    parser.add_argument("--model", help="Download specific model ID")
    parser.add_argument("--content-type", help="Download models for content type")
    parser.add_argument(
        "--verify-only", action="store_true", help="Only verify existing models"
    )
    parser.add_argument(
        "--optimize", action="store_true", help="Run cache optimization"
    )
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")

    args = parser.parse_args()

    orchestrator = DownloadOrchestrator()

    try:
        if args.stats:
            # Show cache statistics
            stats = await orchestrator.cache_manager.get_cache_stats()
            print("📊 Cache Statistics:")
            print(f"   Total models in registry: {stats.total_models}")
            print(f"   Cached models: {stats.cached_models}")
            print(f"   Cache size: {stats.total_size_gb:.1f}GB")
            print(f"   Available space: {stats.available_space_gb:.1f}GB")
            print(f"   Cache hit rate: {stats.cache_hit_rate:.1%}")
            print(f"   Redis available: {stats.redis_available}")

        elif args.verify_only:
            # Verify existing models
            await orchestrator.verify_all_models()

        elif args.optimize:
            # Run optimization
            await orchestrator.optimize_cache()

        elif args.model:
            # Download specific model
            model_id = args.model
            config = orchestrator.registry.get_model_config(model_id)
            if not config:
                print(f"❌ Model not found in registry: {model_id}")
                return

            print(f"📦 Downloading single model: {model_id}")
            cache_info = await orchestrator.downloader.download_model(
                model_id, lambda p: orchestrator.progress_callback(model_id, p)
            )
            print(f"✅ Downloaded: {cache_info.size_gb:.1f}GB")

        elif args.content_type:
            # Download for content type
            try:
                content_type = ContentType(args.content_type)
                await orchestrator.download_for_content_type(content_type)
            except ValueError:
                print(f"❌ Invalid content type: {args.content_type}")
                print(f"Available: {[ct.value for ct in ContentType]}")
                return

        else:
            # Download all models
            await orchestrator.download_all_models()

    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
