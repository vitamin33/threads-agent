#!/usr/bin/env python3
"""
MLflow Wrapper - Professional Experiment Tracking

Standardized MLflow logging for Apple Silicon model evaluation
with comprehensive metrics and artifact management.
"""

import mlflow
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class MLflowExperimentTracker:
    """Professional MLflow experiment tracking."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MLflow tracking."""
        self.config = config
        mlflow_config = config["mlflow"]
        
        # Set tracking URI
        mlflow.set_tracking_uri(mlflow_config["tracking_uri"])
        
        # Create or get experiment
        experiment_name = mlflow_config["experiment"]
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment:
                self.experiment_id = experiment.experiment_id
            else:
                self.experiment_id = mlflow.create_experiment(
                    experiment_name,
                    tags={
                        "evaluation_type": "apple_silicon_local_lm",
                        "methodology": "pairwise_llm_judge_bootstrap_ci",
                        "platform": "apple_silicon_m4_max",
                        "stacks": "mlx_llamacpp_mps"
                    }
                )
        except Exception:
            self.experiment_id = mlflow.create_experiment(experiment_name)
        
        mlflow.set_experiment(experiment_name)
        
        print(f"✅ MLflow experiment: {experiment_name}")
    
    def start_evaluation_run(
        self, 
        model_id: str, 
        stack: str,
        run_type: str = "full_evaluation"
    ) -> str:
        """Start MLflow run for model evaluation."""
        
        run_name = f"{model_id}_{stack}_{run_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        mlflow.start_run(run_name=run_name)
        
        # Log basic parameters
        mlflow.log_param("model_id", model_id)
        mlflow.log_param("stack", stack)
        mlflow.log_param("evaluation_type", run_type)
        mlflow.log_param("platform", "apple_silicon_m4_max")
        mlflow.log_param("commit_hash", self._get_git_commit())
        
        # Log configuration
        mlflow.log_param("temperature", self.config["sampling"]["temperature"])
        mlflow.log_param("top_p", self.config["sampling"]["top_p"])
        mlflow.log_param("max_new_tokens", str(self.config["sampling"]["max_new_tokens"]))
        mlflow.log_param("seeds", str(self.config["seeds"]))
        
        # Log dataset hash for reproducibility
        dataset_hash = self._calculate_dataset_hash()
        mlflow.log_param("dataset_hash", dataset_hash)
        
        return mlflow.active_run().info.run_id
    
    def log_performance_metrics(self, metrics: Any):
        """Log performance metrics."""
        mlflow.log_metric("p50_latency_ms", metrics.p50_latency_ms)
        mlflow.log_metric("p95_latency_ms", metrics.p95_latency_ms)
        mlflow.log_metric("tokens_per_second", metrics.tokens_per_second)
        mlflow.log_metric("peak_rss_mb", metrics.peak_rss_mb)
        mlflow.log_metric("context_length", metrics.context_length)
        
        mlflow.log_param("device", metrics.device)
        mlflow.log_param("warmup_runs", metrics.warmup_runs)
        mlflow.log_param("timed_runs", metrics.timed_runs)
    
    def log_elo_ranking(self, elo_result: Any):
        """Log Elo ranking results."""
        mlflow.log_metric("elo_score", elo_result.elo_score)
        mlflow.log_metric("elo_ci_lower", elo_result.ci_lower)
        mlflow.log_metric("elo_ci_upper", elo_result.ci_upper)
        mlflow.log_metric("win_rate", elo_result.win_rate)
        mlflow.log_metric("total_comparisons", elo_result.total_comparisons)
    
    def log_cost_analysis(self, cost_analysis: Dict[int, Any]):
        """Log cost analysis results."""
        for output_length, analysis in cost_analysis.items():
            mlflow.log_metric(f"local_cost_per_request_{output_length}t", analysis.local_cost_per_request)
            mlflow.log_metric(f"cloud_cost_per_request_{output_length}t", analysis.cloud_cost_per_request)
            mlflow.log_metric(f"savings_percent_{output_length}t", analysis.savings_percent)
            mlflow.log_metric(f"annual_savings_{output_length}t", analysis.annual_savings_1k_requests)
    
    def log_artifact(self, local_path: str, artifact_path: str):
        """Log artifact to MLflow."""
        try:
            mlflow.log_artifact(local_path, artifact_path)
        except Exception as e:
            print(f"⚠️  Failed to log artifact {artifact_path}: {e}")
    
    def log_artifacts_from_dict(self, data: Dict[str, Any], filename: str):
        """Save and log dictionary as JSON artifact."""
        artifact_path = Path("temp_artifacts") / filename
        artifact_path.parent.mkdir(exist_ok=True)
        
        with open(artifact_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.log_artifact(str(artifact_path), "")
    
    def end_run(self):
        """End current MLflow run."""
        if mlflow.active_run():
            mlflow.end_run()
    
    def _get_git_commit(self) -> str:
        """Get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
        except:
            return "unknown"
    
    def _calculate_dataset_hash(self) -> str:
        """Calculate hash of dataset for reproducibility."""
        try:
            dataset_dir = Path(self.config["dataset_dir"])
            content = ""
            
            for jsonl_file in dataset_dir.glob("*.jsonl"):
                with open(jsonl_file) as f:
                    content += f.read()
            
            return hashlib.md5(content.encode()).hexdigest()[:8]
        except:
            return "unknown"


def create_mlflow_tracker(config: Dict[str, Any]) -> MLflowExperimentTracker:
    """Create MLflow experiment tracker."""
    return MLflowExperimentTracker(config)