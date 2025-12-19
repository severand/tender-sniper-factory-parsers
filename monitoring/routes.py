"""Monitoring and observability routes"""

from fastapi import APIRouter
from prometheus_client import generate_latest, REGISTRY

from .health import HealthCheck

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
def health_check():
    """System health check"""
    return HealthCheck.check_all()


@router.get("/health/database")
def health_database():
    """Database health check"""
    return HealthCheck.check_database()


@router.get("/health/redis")
def health_redis():
    """Redis health check"""
    return HealthCheck.check_redis()


@router.get("/health/elasticsearch")
def health_elasticsearch():
    """Elasticsearch health check"""
    return HealthCheck.check_elasticsearch()


@router.get("/metrics")
def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(REGISTRY)
