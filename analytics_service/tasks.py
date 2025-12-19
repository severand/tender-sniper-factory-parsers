"""Celery tasks for analytics"""

from factory_parsers.scheduler_service.celery_app import task
from factory_parsers.shared.database import SessionLocal
from factory_parsers.shared.logger import logger
from factory_parsers.analytics_service.collector import MetricsCollector
from factory_parsers.analytics_service.analyzer import TenderAnalyzer


@task(name="collect_daily_metrics")
def collect_daily_metrics_task() -> dict:
    """Collect daily metrics
    
    Returns:
        Collection result
    """
    db = SessionLocal()
    try:
        logger.info("Collecting daily metrics")
        collector = MetricsCollector(db)
        metrics = collector.collect_daily_metrics()
        return {
            "status": "success",
            "total_tenders": metrics.total_tenders,
            "indexed": metrics.tenders_indexed,
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise
    finally:
        db.close()


@task(name="generate_daily_report")
def generate_daily_report_task() -> dict:
    """Generate daily report
    
    Returns:
        Report data
    """
    db = SessionLocal()
    try:
        logger.info("Generating daily report")
        analyzer = TenderAnalyzer(db)
        collector = MetricsCollector(db)
        
        # Collect metrics
        metrics = collector.collect_daily_metrics()
        
        # Get stats
        platform_stats = analyzer.get_platform_stats()
        category_stats = analyzer.get_category_stats()
        top_customers = analyzer.get_customer_stats(limit=10)
        
        return {
            "status": "success",
            "total_tenders": metrics.total_tenders,
            "platforms": len(platform_stats),
            "categories": len(category_stats),
            "top_customers_count": len(top_customers),
        }
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise
    finally:
        db.close()
