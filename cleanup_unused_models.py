#!/usr/bin/env python3
"""
Safe Model Cleanup Script - Remove Unused/Failed Models

Safely removes failed downloads and poor quality models while protecting:
- OPT-2.7B: 8.40 ± 0.78/10 (Quality Leader) ✅ KEEP
- BLOOM-560M: 7.70 ± 0.59/10 (Reliable Alternative) ✅ KEEP  
- TinyLlama-1.1B: 5.20 ± 0.10/10 (Baseline) ✅ KEEP

Removes safely:
- FLAN-T5 models: 2.9/10 quality (poor performance)
- GODEL: 5.2/10 quality (disappointing)
- Failed downloads: Incomplete/corrupted models
- Temporary caches: Experimental downloads

Estimated space savings: ~25GB
"""

import shutil
import os
from pathlib import Path


class SafeModelCleanup:
    """Safe cleanup of unused models while protecting validated leaders."""
    
    def __init__(self):
        """Initialize safe cleanup."""
        # PROTECTED MODELS (DO NOT REMOVE)
        self.protected_models = {
            "facebook/opt-2.7b": "Quality leader 8.40/10",
            "bigscience/bloom-560m": "Reliable alternative 7.70/10", 
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0": "Baseline 5.20/10"
        }
        
        # MODELS TO REMOVE (Poor quality/failed)
        self.models_to_remove = {
            "google/flan-t5-xl": "Poor quality 2.9/10",
            "google/flan-t5-large": "Poor quality", 
            "microsoft/GODEL-v1_1-large-seq2seq": "Low quality 5.2/10",
            "nvidia/NVIDIA-Nemotron-Nano-9B-v2": "Dependency issues",
            "gpt2": "Test model only"
        }
        
        # Cache directories to clean
        self.cache_locations = [
            Path.home() / ".cache" / "huggingface" / "hub",
            Path.home() / ".cache" / "bloom_3b_fixed",
            Path.home() / ".cache" / "robust_model_testing"
        ]
        
        self.dry_run = True  # Safety: preview before actual deletion
        self.total_saved_gb = 0
    
    def analyze_cleanup_candidates(self):
        """Analyze what can be safely removed."""
        
        print("🔍 ANALYZING CLEANUP CANDIDATES")
        print("=" * 60)
        
        cleanup_candidates = []
        
        for cache_location in self.cache_locations:
            if cache_location.exists():
                print(f"\\n📁 Analyzing: {cache_location}")
                
                for item in cache_location.iterdir():
                    if item.is_dir():
                        try:
                            # Calculate size
                            size_bytes = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                            size_gb = size_bytes / (1024**3)
                            
                            if size_gb > 0.1:  # Only consider directories > 100MB
                                # Check if it's a model to remove
                                model_name = self._extract_model_name(item.name)
                                
                                is_protected = any(protected in model_name.lower() 
                                                 for protected in ["opt-2.7b", "bloom-560m", "tinyllama"])
                                
                                is_removable = any(removable in model_name.lower() 
                                                 for removable in ["flan-t5", "godel", "nemotron", "gpt2"])
                                
                                status = "PROTECTED" if is_protected else "REMOVABLE" if is_removable else "REVIEW"
                                
                                candidate = {
                                    "path": item,
                                    "model_name": model_name,
                                    "size_gb": size_gb,
                                    "status": status,
                                    "reason": self._get_removal_reason(model_name)
                                }
                                
                                cleanup_candidates.append(candidate)
                                
                                status_icon = "🛡️ " if status == "PROTECTED" else "🗑️ " if status == "REMOVABLE" else "❓"
                                print(f"   {status_icon} {model_name}: {size_gb:.1f}GB ({status})")
                        
                        except Exception as e:
                            print(f"   ❌ Error analyzing {item.name}: {e}")
        
        return cleanup_candidates
    
    def _extract_model_name(self, dir_name: str) -> str:
        """Extract clean model name from directory."""
        # Handle HuggingFace format: models--facebook--opt-2.7b
        if dir_name.startswith("models--"):
            return dir_name.replace("models--", "").replace("--", "/")
        else:
            return dir_name
    
    def _get_removal_reason(self, model_name: str) -> str:
        """Get reason for removal."""
        if "flan-t5" in model_name.lower():
            return "Poor quality (2.9/10)"
        elif "godel" in model_name.lower():
            return "Low quality (5.2/10)"
        elif "nemotron" in model_name.lower():
            return "Dependency issues, incomplete"
        elif "gpt2" in model_name.lower():
            return "Test model only"
        elif "bloom-3b" in model_name.lower():
            return "Failed download"
        else:
            return "Review required"
    
    def preview_cleanup(self):
        """Preview what will be removed (safe mode)."""
        
        print("\\n🔍 CLEANUP PREVIEW (DRY RUN)")
        print("=" * 60)
        
        candidates = self.analyze_cleanup_candidates()
        
        protected_models = [c for c in candidates if c["status"] == "PROTECTED"]
        removable_models = [c for c in candidates if c["status"] == "REMOVABLE"]
        review_models = [c for c in candidates if c["status"] == "REVIEW"]
        
        print("\\n🛡️  PROTECTED (WILL KEEP):")
        protected_size = 0
        for model in protected_models:
            print(f"   ✅ {model['model_name']}: {model['size_gb']:.1f}GB - {self.protected_models.get(model['model_name'], 'Validated model')}")
            protected_size += model['size_gb']
        
        print("\\n🗑️  REMOVABLE (SAFE TO DELETE):")
        removable_size = 0
        for model in removable_models:
            print(f"   ❌ {model['model_name']}: {model['size_gb']:.1f}GB - {model['reason']}")
            removable_size += model['size_gb']
        
        if review_models:
            print("\\n❓ REVIEW REQUIRED:")
            for model in review_models:
                print(f"   ⚠️  {model['model_name']}: {model['size_gb']:.1f}GB - Manual decision needed")
        
        print("\\n📊 CLEANUP SUMMARY:")
        print(f"   Protected models: {len(protected_models)} ({protected_size:.1f}GB)")
        print(f"   Removable models: {len(removable_models)} ({removable_size:.1f}GB)")
        print(f"   Space savings: {removable_size:.1f}GB")
        print(f"   Retention: Essential models preserved")
        
        return removable_models, protected_models
    
    def safe_cleanup_execution(self, removable_models):
        """Execute safe cleanup of unused models."""
        
        print("\\n🧹 EXECUTING SAFE CLEANUP")
        print("=" * 60)
        
        if not removable_models:
            print("✅ No models marked for removal")
            return
        
        print("🗑️  Removing poor quality/failed models:")
        
        for model in removable_models:
            try:
                model_path = model["path"]
                model_name = model["model_name"]
                size_gb = model["size_gb"]
                reason = model["reason"]
                
                print(f"   Removing {model_name} ({size_gb:.1f}GB) - {reason}")
                
                if not self.dry_run:
                    shutil.rmtree(model_path)
                    self.total_saved_gb += size_gb
                    print(f"   ✅ Removed: {model_path}")
                else:
                    print(f"   📋 Would remove: {model_path}")
                    self.total_saved_gb += size_gb
                
            except Exception as e:
                print(f"   ❌ Failed to remove {model_name}: {e}")
        
        print(f"\\n💾 CLEANUP COMPLETE:")
        print(f"   Space saved: {self.total_saved_gb:.1f}GB")
        print(f"   Models removed: {len(removable_models)}")
        print(f"   Protected models: Preserved safely")


def main():
    """Run safe model cleanup."""
    print("🧹 SAFE MODEL CLEANUP - PROTECTING VALIDATED LEADERS")
    print("=" * 70)
    print("🛡️  PROTECTED: OPT-2.7B, BLOOM-560M, TinyLlama")
    print("🗑️  REMOVING: Poor quality, failed downloads, unused models")
    print("")
    
    cleanup = SafeModelCleanup()
    
    try:
        # Preview cleanup (safe)
        removable_models, protected_models = cleanup.preview_cleanup()
        
        print("\\n💡 CLEANUP RECOMMENDATION:")
        if removable_models:
            print(f"✅ Safe to remove {len(removable_models)} unused models")
            print(f"💾 Space savings: {sum(m['size_gb'] for m in removable_models):.1f}GB")
            print("🛡️  All validated leaders will be preserved")
            
            # Ask for confirmation
            print("\\n🔧 EXECUTION OPTIONS:")
            print("1. Run cleanup.dry_run = False to actually remove models")
            print("2. Review candidates and remove manually")
            print("3. Keep everything for now")
            
        else:
            print("✅ No cleanup needed - all models are being used")
        
        print("\\n🎯 ESSENTIAL MODELS PRESERVED:")
        for model in protected_models:
            print(f"   ✅ {model['model_name']}: {model['size_gb']:.1f}GB")
            
    except Exception as e:
        print(f"❌ Cleanup analysis failed: {e}")


if __name__ == "__main__":
    main()