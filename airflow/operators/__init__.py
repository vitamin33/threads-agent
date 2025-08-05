"""
Custom Airflow Operators for Viral Learning Flywheel (CRA-284)

This package contains custom operators for integrating with the Threads-Agent Stack services:
- ViralScraperOperator: Rate-limited content scraping operations
- ViralEngineOperator: Pattern extraction and viral analysis
- ThompsonSamplingOperator: Parameter optimization for content variants
- MetricsCollectorOperator: Performance monitoring and KPI collection
- HealthCheckOperator: Service health monitoring

Epic: E7 - Viral Learning Flywheel
"""

from airflow.operators.viral_scraper_operator import ViralScraperOperator
from airflow.operators.viral_engine_operator import ViralEngineOperator
from airflow.operators.thompson_sampling_operator import ThompsonSamplingOperator
from airflow.operators.metrics_collector_operator import MetricsCollectorOperator
from airflow.operators.health_check_operator import HealthCheckOperator

__version__ = "1.0.0"
__all__ = [
    "ViralScraperOperator",
    "ViralEngineOperator",
    "ThompsonSamplingOperator",
    "MetricsCollectorOperator",
    "HealthCheckOperator",
]
