# Production Configuration for SaaS Deployment
# Pragmatic approach: Start simple, scale when needed

import os
from typing import Dict, Any


class ProductionConfig:
    """
    Production configuration with pragmatic defaults.

    Philosophy:
    - Don't over-optimize before you have customers
    - Make it stable first, fast second, cheap third
    - Monitor everything so you know when to optimize
    """

    # Database Configuration
    DATABASE = {
        # Start with 10 connections (2x default, handles 100 concurrent users)
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": 30,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    }

    # Rate Limiting (Prevent crashes, not optimize yet)
    RATE_LIMITS = {
        # Per IP limits (prevent abuse)
        "requests_per_minute": int(os.getenv("RATE_LIMIT_PER_MIN", "60")),
        "burst_size": int(os.getenv("RATE_LIMIT_BURST", "10")),
        # Global limits (protect your service)
        "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT", "100")),
        "queue_size": int(os.getenv("QUEUE_SIZE", "500")),
    }

    # Caching (Simple for now, expand when you see patterns)
    CACHE = {
        "enabled": os.getenv("CACHE_ENABLED", "false").lower() == "true",
        "ttl_seconds": int(os.getenv("CACHE_TTL", "300")),  # 5 minutes
        "max_size": int(os.getenv("CACHE_MAX_SIZE", "1000")),
    }

    # Cost Optimization (Only when you're spending >$1000/month)
    OPTIMIZATION = {
        "batch_requests": os.getenv("BATCH_ENABLED", "false").lower() == "true",
        "batch_size": int(os.getenv("BATCH_SIZE", "5")),
        "batch_wait_ms": int(os.getenv("BATCH_WAIT_MS", "100")),
    }

    # Monitoring (Essential from day 1)
    MONITORING = {
        "metrics_enabled": True,
        "trace_sample_rate": float(os.getenv("TRACE_SAMPLE_RATE", "0.1")),  # 10%
        "slow_query_threshold_ms": int(os.getenv("SLOW_QUERY_MS", "100")),
        "alert_on_error_rate": float(os.getenv("ALERT_ERROR_RATE", "0.01")),  # 1%
    }

    # SaaS Features (Add when you have paying customers)
    SAAS = {
        "multi_tenancy": False,  # Add when you have 2+ customers
        "billing_enabled": False,  # Add when someone wants to pay
        "audit_logging": False,  # Add when you have enterprise customers
        "sla_monitoring": False,  # Add when you sign SLAs
    }

    @classmethod
    def get_stage(cls) -> str:
        """Determine current stage of SaaS journey."""
        if not cls.SAAS["multi_tenancy"]:
            return "MVP"
        elif not cls.SAAS["billing_enabled"]:
            return "BETA"
        elif not cls.SAAS["sla_monitoring"]:
            return "GROWTH"
        else:
            return "SCALE"

    @classmethod
    def get_optimization_level(cls) -> Dict[str, Any]:
        """Get current optimization recommendations."""
        stage = cls.get_stage()

        if stage == "MVP":
            return {
                "focus": "Stability & Basic Functionality",
                "db_pool": 10,
                "cache": False,
                "batching": False,
                "monitoring": "Basic metrics only",
                "estimated_capacity": "100 concurrent users",
                "monthly_cost": "$200-500",
            }
        elif stage == "BETA":
            return {
                "focus": "User Experience & Feedback",
                "db_pool": 20,
                "cache": True,
                "batching": False,
                "monitoring": "APM + Error tracking",
                "estimated_capacity": "500 concurrent users",
                "monthly_cost": "$500-2000",
            }
        elif stage == "GROWTH":
            return {
                "focus": "Cost Optimization & Scale",
                "db_pool": 50,
                "cache": True,
                "batching": True,
                "monitoring": "Full observability",
                "estimated_capacity": "5000 concurrent users",
                "monthly_cost": "$2000-10000",
            }
        else:
            return {
                "focus": "Enterprise Features & SLAs",
                "db_pool": 100,
                "cache": True,
                "batching": True,
                "monitoring": "Enterprise APM",
                "estimated_capacity": "50000+ concurrent users",
                "monthly_cost": "$10000+",
            }

    @classmethod
    def should_optimize(cls, metric: str, current_value: float) -> bool:
        """Determine if optimization is needed based on current metrics."""
        thresholds = {
            "error_rate": 0.01,  # Optimize if >1% errors
            "p95_latency_ms": 500,  # Optimize if >500ms
            "cost_per_request": 0.01,  # Optimize if >$0.01/request
            "db_pool_exhaustion": 0.8,  # Optimize if >80% pool used
        }

        return current_value > thresholds.get(metric, float("inf"))


# Interview talking points
PRODUCTION_PHILOSOPHY = """
SaaS Production Strategy:

1. **MVP Phase (Now)**: 
   - Focus: "Make it work reliably"
   - Investment: Minimal ($200/month)
   - Capacity: 100 concurrent users
   - Good enough for demos and first customers

2. **Growth Phase (At $10k MRR)**:
   - Focus: "Make it fast"
   - Investment: ~$2000/month
   - Capacity: 5000 concurrent users
   - Add caching, better monitoring

3. **Scale Phase (At $50k MRR)**:
   - Focus: "Make it cheap"
   - Investment: ~$10000/month
   - Capacity: 50000+ concurrent users
   - Optimize everything

Key Insight: "Premature optimization is the root of all evil"
- Don't build for 10,000 users when you have 10
- Don't optimize costs when you're spending $200/month
- Don't add complexity before you understand usage patterns
"""
