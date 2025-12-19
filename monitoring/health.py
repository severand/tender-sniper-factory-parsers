"""Health check endpoints"""

from typing import Dict, Any
import psycopg2
from redis import Redis
from elasticsearch import Elasticsearch

from factory_parsers.shared.database import SessionLocal
from factory_parsers.search_service.elasticsearch_client import ElasticsearchClient
from factory_parsers.shared.logger import logger


class HealthCheck:
    """Health check for all system components"""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            return {"status": "healthy", "service": "database"}
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {"status": "unhealthy", "service": "database", "error": str(e)}
    
    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            from factory_parsers.shared.config import get_settings
            settings = get_settings()
            redis = Redis.from_url(settings.redis_url)
            redis.ping()
            return {"status": "healthy", "service": "redis"}
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {"status": "unhealthy", "service": "redis", "error": str(e)}
    
    @staticmethod
    def check_elasticsearch() -> Dict[str, Any]:
        """Check Elasticsearch connectivity"""
        try:
            es_client = ElasticsearchClient()
            stats = es_client.get_stats()
            return {"status": "healthy", "service": "elasticsearch", "stats": stats}
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {str(e)}")
            return {"status": "unhealthy", "service": "elasticsearch", "error": str(e)}
    
    @staticmethod
    def check_all() -> Dict[str, Any]:
        """Check all services"""
        checks = [
            HealthCheck.check_database(),
            HealthCheck.check_redis(),
            HealthCheck.check_elasticsearch(),
        ]
        
        all_healthy = all(check["status"] == "healthy" for check in checks)
        
        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "checks": checks,
        }
