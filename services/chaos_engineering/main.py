"""
Chaos Engineering Service - FastAPI application for chaos experiments.

This service provides REST APIs for running chaos experiments with safety controls,
monitoring integration, and enterprise-grade reliability features.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import make_asgi_app, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from chaos_experiment_executor import ChaosExperimentExecutor, ExperimentResult, ExperimentState
from litmus_chaos_integration import LitmusChaosManager, ExperimentType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
chaos_executor = None
litmus_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI application."""
    global chaos_executor, litmus_manager
    
    # Startup
    logger.info("Starting Chaos Engineering Service")
    chaos_executor = ChaosExperimentExecutor(safety_threshold=0.8)
    litmus_manager = LitmusChaosManager(namespace="litmus")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Chaos Engineering Service")


# FastAPI application
app = FastAPI(
    title="Chaos Engineering Service",
    description="Enterprise-grade chaos experiments for Kubernetes with safety controls",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Pydantic models
class ExperimentRequest(BaseModel):
    name: str = Field(..., description="Name of the experiment")
    type: str = Field(..., description="Type of experiment (pod_kill, network_partition, cpu_stress, memory_pressure)")
    target: Dict[str, Any] = Field(..., description="Target configuration")
    duration: int = Field(30, description="Duration in seconds")
    safety_threshold: Optional[float] = Field(0.8, description="Safety threshold (0.0-1.0)")


class ExperimentResponse(BaseModel):
    experiment_name: str
    status: str
    execution_time: float
    safety_checks_passed: bool
    actions_performed: List[str]
    error_message: Optional[str] = None


class ExperimentStatusResponse(BaseModel):
    experiment_name: str
    phase: str
    created_at: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    return {"status": "healthy", "service": "chaos-engineering"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Kubernetes probes."""
    global chaos_executor, litmus_manager
    
    if chaos_executor is None or litmus_manager is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "ready", "service": "chaos-engineering"}


# Experiment management endpoints
@app.post("/api/v1/experiments", response_model=ExperimentResponse)
async def create_experiment(
    experiment: ExperimentRequest,
    background_tasks: BackgroundTasks
):
    """Create and run a new chaos experiment."""
    global chaos_executor
    
    if chaos_executor is None:
        raise HTTPException(status_code=503, detail="Chaos executor not initialized")
    
    try:
        # Validate experiment type
        valid_types = ['pod_kill', 'network_partition', 'cpu_stress', 'memory_pressure']
        if experiment.type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid experiment type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Build experiment configuration
        experiment_config = {
            "name": experiment.name,
            "type": experiment.type,
            "target": experiment.target,
            "duration": experiment.duration
        }
        
        # Update safety threshold if provided
        if experiment.safety_threshold:
            chaos_executor.safety_threshold = experiment.safety_threshold
        
        logger.info(f"Starting chaos experiment: {experiment.name}")
        
        # Execute experiment
        result = await chaos_executor.execute_experiment(experiment_config)
        
        return ExperimentResponse(
            experiment_name=result.experiment_name,
            status=result.status.value,
            execution_time=result.execution_time,
            safety_checks_passed=result.safety_checks_passed,
            actions_performed=result.actions_performed,
            error_message=result.error_message
        )
        
    except Exception as e:
        logger.error(f"Failed to create experiment {experiment.name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create experiment: {str(e)}")


@app.get("/api/v1/experiments", response_model=List[ExperimentStatusResponse])
async def list_experiments():
    """List all chaos experiments."""
    global litmus_manager
    
    if litmus_manager is None:
        raise HTTPException(status_code=503, detail="LitmusChaos manager not initialized")
    
    try:
        experiments = await litmus_manager.list_experiments()
        
        result = []
        for item in experiments.get("items", []):
            metadata = item.get("metadata", {})
            status = item.get("status", {})
            
            result.append(ExperimentStatusResponse(
                experiment_name=metadata.get("name", "unknown"),
                phase=status.get("phase", "unknown"),
                created_at=metadata.get("creationTimestamp"),
                results=status.get("experimentStatus")
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list experiments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list experiments: {str(e)}")


@app.get("/api/v1/experiments/{experiment_name}", response_model=ExperimentStatusResponse)
async def get_experiment_status(experiment_name: str):
    """Get the status of a specific chaos experiment."""
    global litmus_manager
    
    if litmus_manager is None:
        raise HTTPException(status_code=503, detail="LitmusChaos manager not initialized")
    
    try:
        experiment = await litmus_manager.get_experiment_status(experiment_name)
        
        metadata = experiment.get("metadata", {})
        status = experiment.get("status", {})
        
        return ExperimentStatusResponse(
            experiment_name=metadata.get("name", experiment_name),
            phase=status.get("phase", "unknown"),
            created_at=metadata.get("creationTimestamp"),
            results=status.get("experimentStatus")
        )
        
    except Exception as e:
        logger.error(f"Failed to get experiment status {experiment_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get experiment status: {str(e)}")


@app.delete("/api/v1/experiments/{experiment_name}")
async def delete_experiment(experiment_name: str):
    """Delete a chaos experiment."""
    global litmus_manager
    
    if litmus_manager is None:
        raise HTTPException(status_code=503, detail="LitmusChaos manager not initialized")
    
    try:
        await litmus_manager.delete_experiment(experiment_name)
        logger.info(f"Deleted chaos experiment: {experiment_name}")
        
        return {"message": f"Experiment {experiment_name} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete experiment {experiment_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete experiment: {str(e)}")


@app.post("/api/v1/experiments/{experiment_name}/stop")
async def emergency_stop_experiment(experiment_name: str):
    """Trigger emergency stop for a running experiment."""
    global chaos_executor
    
    if chaos_executor is None:
        raise HTTPException(status_code=503, detail="Chaos executor not initialized")
    
    try:
        await chaos_executor.emergency_stop()
        logger.info(f"Emergency stop triggered for experiment: {experiment_name}")
        
        return {"message": f"Emergency stop triggered for experiment {experiment_name}"}
        
    except Exception as e:
        logger.error(f"Failed to stop experiment {experiment_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop experiment: {str(e)}")


# System information endpoints
@app.get("/api/v1/system/health")
async def get_system_health():
    """Get current system health metrics."""
    global chaos_executor
    
    if chaos_executor is None:
        raise HTTPException(status_code=503, detail="Chaos executor not initialized")
    
    try:
        health_score = await chaos_executor._check_system_health()
        
        return {
            "health_score": health_score,
            "safety_threshold": chaos_executor.safety_threshold,
            "status": "healthy" if health_score >= chaos_executor.safety_threshold else "degraded"
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)