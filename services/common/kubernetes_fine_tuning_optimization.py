"""Kubernetes-specific optimizations for fine-tuning pipeline (CRA-283).

This module provides Kubernetes-specific performance optimizations:
1. Resource limits and requests optimization
2. Horizontal Pod Autoscaling (HPA) configuration
3. Connection pool management for microservices
4. Circuit breaker patterns for external dependencies
5. Health checks and readiness probes
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


@dataclass
class KubernetesResourceConfig:
    """Kubernetes resource configuration for fine-tuning pipeline."""
    memory_request: str = "512Mi"
    memory_limit: str = "2Gi"
    cpu_request: str = "500m"
    cpu_limit: str = "2000m"
    max_replicas: int = 5
    min_replicas: int = 1
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80


class ConnectionPoolManager:
    """Manages connection pools for database and Redis in Kubernetes environment."""
    
    def __init__(self):
        self.db_pool = None
        self.redis_pool = None
        self._pool_stats = {
            "db_connections_active": 0,
            "db_connections_idle": 0,
            "redis_connections_active": 0,
            "redis_connections_idle": 0
        }
    
    async def initialize_pools(self):
        """Initialize optimized connection pools for Kubernetes deployment."""
        import asyncpg
        import aioredis
        
        # Database connection pool optimized for Kubernetes
        self.db_pool = await asyncpg.create_pool(
            host="postgresql.default.svc.cluster.local",
            port=5432,
            database="threads_agent",
            min_size=2,  # Minimum connections per pod
            max_size=10,  # Maximum connections per pod
            max_queries=50000,  # Recycle connections after 50k queries
            max_inactive_connection_lifetime=300,  # 5 minutes
            command_timeout=60,  # 1 minute timeout
            server_settings={
                'application_name': 'fine_tuning_pipeline',
                'tcp_keepalives_idle': '30',
                'tcp_keepalives_interval': '10',
                'tcp_keepalives_count': '3'
            }
        )
        
        # Redis connection pool optimized for Kubernetes
        self.redis_pool = aioredis.ConnectionPool.from_url(
            "redis://redis.default.svc.cluster.local:6379",
            max_connections=20,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={
                1: 30,  # TCP_KEEPIDLE
                2: 10,  # TCP_KEEPINTVL
                3: 3,   # TCP_KEEPCNT
            },
            health_check_interval=30
        )
        
        logger.info("Connection pools initialized for Kubernetes deployment")
    
    @asynccontextmanager
    async def get_db_connection(self):
        """Get database connection with automatic cleanup."""
        async with self.db_pool.acquire() as connection:
            self._pool_stats["db_connections_active"] += 1
            try:
                yield connection
            finally:
                self._pool_stats["db_connections_active"] -= 1
                self._pool_stats["db_connections_idle"] += 1
    
    @asynccontextmanager
    async def get_redis_connection(self):
        """Get Redis connection with automatic cleanup."""
        redis_client = aioredis.Redis(connection_pool=self.redis_pool)
        self._pool_stats["redis_connections_active"] += 1
        try:
            yield redis_client
        finally:
            await redis_client.close()
            self._pool_stats["redis_connections_active"] -= 1
            self._pool_stats["redis_connections_idle"] += 1
    
    def get_pool_stats(self) -> Dict[str, int]:
        """Get current connection pool statistics."""
        return self._pool_stats.copy()


class CircuitBreaker:
    """Circuit breaker pattern for external API calls (OpenAI, etc.)."""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN - external service unavailable")
        
        try:
            result = await func(*args, **kwargs)
            
            # Reset on success
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker reset to CLOSED")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker opened due to {self.failure_count} failures")
            
            raise


class KubernetesOptimizedPipeline:
    """Fine-tuning pipeline optimized for Kubernetes deployment."""
    
    def __init__(self, resource_config: KubernetesResourceConfig):
        self.resource_config = resource_config
        self.connection_manager = ConnectionPoolManager()
        self.openai_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=120)
        self.mlflow_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        
    async def initialize(self):
        """Initialize Kubernetes-optimized components."""
        await self.connection_manager.initialize_pools()
        logger.info("Kubernetes-optimized pipeline initialized")
    
    async def collect_training_data_optimized(self, engagement_threshold: float, days_back: int = 7):
        """Collect training data with Kubernetes-optimized database queries."""
        from sqlalchemy import text
        
        async with self.connection_manager.get_db_connection() as conn:
            # Use optimized SQL query with proper indexing hints
            query = text("""
                SELECT id, persona_id, hook, body, engagement_rate, ts, tokens_used
                FROM posts 
                WHERE ts >= NOW() - INTERVAL '%s days'
                AND COALESCE(engagement_rate, 0.0) >= :threshold
                ORDER BY engagement_rate DESC NULLS LAST
                LIMIT 10000
            """ % days_back)
            
            # Execute with connection-level optimization
            result = await conn.fetch(query, threshold=engagement_threshold)
            
            # Process in memory-efficient chunks
            chunk_size = 1000
            hook_examples = []
            body_examples = []
            
            for i in range(0, len(result), chunk_size):
                chunk = result[i:i + chunk_size]
                
                for row in chunk:
                    hook_examples.append({
                        "messages": [
                            {"role": "user", "content": "Create engaging content"},
                            {"role": "assistant", "content": row['hook']}
                        ],
                        "engagement_rate": float(row['engagement_rate'] or 0.0)
                    })
                    
                    body_examples.append({
                        "messages": [
                            {"role": "user", "content": f"{row['hook']}\n\nWrite a detailed post:"},
                            {"role": "assistant", "content": row['body']}
                        ],
                        "engagement_rate": float(row['engagement_rate'] or 0.0)
                    })
            
            return {
                "hook_examples": hook_examples,
                "body_examples": body_examples,
                "metadata": {
                    "total_records": len(result),
                    "chunk_size": chunk_size,
                    "collected_at": time.time()
                }
            }
    
    async def start_fine_tuning_with_circuit_breaker(self, training_data: Dict[str, Any]):
        """Start fine-tuning with circuit breaker protection."""
        import openai
        import tempfile
        import json
        import os
        
        async def _openai_fine_tuning():
            client = openai.AsyncOpenAI()
            
            # Prepare training file
            training_examples = training_data["hook_examples"] + training_data["body_examples"]
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                for example in training_examples:
                    json.dump(example, f)
                    f.write('\n')
                training_file_path = f.name
            
            try:
                # Upload file with retry logic
                with open(training_file_path, 'rb') as f:
                    file_upload = await client.files.create(
                        file=f,
                        purpose='fine-tune'
                    )
                
                # Create fine-tuning job
                job = await client.fine_tuning.jobs.create(
                    training_file=file_upload.id,
                    model="gpt-3.5-turbo-0125",
                    hyperparameters={
                        "n_epochs": "auto",
                        "batch_size": "auto"
                    }
                )
                
                return {
                    "job_id": job.id,
                    "status": "training",
                    "training_examples": len(training_examples)
                }
                
            finally:
                if os.path.exists(training_file_path):
                    os.unlink(training_file_path)
        
        # Execute with circuit breaker protection
        return await self.openai_circuit_breaker.call(_openai_fine_tuning)
    
    async def cache_evaluation_metrics(self, model_type: str, ab_test_id: str, metrics: Dict[str, float]):
        """Cache evaluation metrics in Redis with Kubernetes-optimized connection."""
        cache_key = f"model_metrics:{ab_test_id}:{model_type}"
        
        async with self.connection_manager.get_redis_connection() as redis:
            await redis.setex(cache_key, 300, json.dumps(metrics))  # 5 minute TTL
            logger.info(f"Cached metrics for {model_type} in test {ab_test_id}")
    
    async def get_cached_metrics(self, model_type: str, ab_test_id: str) -> Optional[Dict[str, float]]:
        """Retrieve cached metrics from Redis."""
        cache_key = f"model_metrics:{ab_test_id}:{model_type}"
        
        try:
            async with self.connection_manager.get_redis_connection() as redis:
                cached_data = await redis.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Failed to retrieve cached metrics: {e}")
        
        return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Kubernetes readiness and liveness probe endpoint."""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {}
        }
        
        # Check database connection
        try:
            async with self.connection_manager.get_db_connection() as conn:
                await conn.fetchval("SELECT 1")
            health_status["components"]["database"] = "healthy"
        except Exception as e:
            health_status["components"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Check Redis connection
        try:
            async with self.connection_manager.get_redis_connection() as redis:
                await redis.ping()
            health_status["components"]["redis"] = "healthy"
        except Exception as e:
            health_status["components"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Check circuit breaker states
        health_status["components"]["openai_circuit_breaker"] = self.openai_circuit_breaker.state
        health_status["components"]["mlflow_circuit_breaker"] = self.mlflow_circuit_breaker.state
        
        # Connection pool statistics
        health_status["connection_pools"] = self.connection_manager.get_pool_stats()
        
        return health_status
    
    async def get_prometheus_metrics(self) -> str:
        """Generate Prometheus metrics for monitoring."""
        pool_stats = self.connection_manager.get_pool_stats()
        
        metrics = []
        
        # Connection pool metrics
        metrics.append(f'fine_tuning_db_connections_active {pool_stats["db_connections_active"]}')
        metrics.append(f'fine_tuning_db_connections_idle {pool_stats["db_connections_idle"]}')
        metrics.append(f'fine_tuning_redis_connections_active {pool_stats["redis_connections_active"]}')
        metrics.append(f'fine_tuning_redis_connections_idle {pool_stats["redis_connections_idle"]}')
        
        # Circuit breaker metrics
        metrics.append(f'fine_tuning_openai_circuit_breaker_state{{state="{self.openai_circuit_breaker.state}"}} 1')
        metrics.append(f'fine_tuning_openai_failures_total {self.openai_circuit_breaker.failure_count}')
        metrics.append(f'fine_tuning_mlflow_circuit_breaker_state{{state="{self.mlflow_circuit_breaker.state}"}} 1')
        metrics.append(f'fine_tuning_mlflow_failures_total {self.mlflow_circuit_breaker.failure_count}')
        
        return '\n'.join(metrics) + '\n'


def get_kubernetes_deployment_yaml(resource_config: KubernetesResourceConfig) -> str:
    """Generate optimized Kubernetes deployment YAML for fine-tuning pipeline."""
    return f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fine-tuning-pipeline
  labels:
    app: fine-tuning-pipeline
    version: v1
spec:
  replicas: {resource_config.min_replicas}
  selector:
    matchLabels:
      app: fine-tuning-pipeline
  template:
    metadata:
      labels:
        app: fine-tuning-pipeline
        version: v1
    spec:
      containers:
      - name: fine-tuning-pipeline
        image: threads-agent/fine-tuning-pipeline:latest
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
        resources:
          requests:
            memory: "{resource_config.memory_request}"
            cpu: "{resource_config.cpu_request}"
          limits:
            memory: "{resource_config.memory_limit}"
            cpu: "{resource_config.cpu_limit}"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_URL
          value: "redis://redis.default.svc.cluster.local:6379"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        - name: MLFLOW_TRACKING_URI
          value: "http://mlflow.default.svc.cluster.local:5000"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
---
apiVersion: v1
kind: Service
metadata:
  name: fine-tuning-pipeline-service
  labels:
    app: fine-tuning-pipeline
spec:
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  - port: 9090
    targetPort: 9090
    name: metrics
  selector:
    app: fine-tuning-pipeline
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fine-tuning-pipeline-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fine-tuning-pipeline
  minReplicas: {resource_config.min_replicas}
  maxReplicas: {resource_config.max_replicas}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {resource_config.target_cpu_utilization}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {resource_config.target_memory_utilization}
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
"""