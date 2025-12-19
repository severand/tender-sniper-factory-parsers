"""Metrics collection"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from factory_parsers.shared.logger import logger
from factory_parsers.analytics_service.models import DailyMetrics, ScraperMetrics, SearchMetrics
from factory_parsers.normalizer_service.repositories import NormalizedTenderRepository
from factory_parsers.search_service.elasticsearch_client import ElasticsearchClient


class MetricsCollector:
    """Collect system metrics"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tender_repo = NormalizedTenderRepository(db)
        self.es_client = ElasticsearchClient()
    
    def collect_daily_metrics(self, date: datetime = None) -> DailyMetrics:
        """Collect daily metrics
        
        Args:
            date: Date for metrics (default: today)
        
        Returns:
            DailyMetrics record
        """
        if not date:
            date = datetime.utcnow()
        
        logger.info(f"Collecting metrics for {date.date()}")
        
        # Get totals
        total_tenders = self.tender_repo.count()
        
        # Get ES stats
        es_stats = self.es_client.get_stats()
        indexed_tenders = es_stats.get('count', 0)
        
        # Create metrics
        metrics = DailyMetrics(
            date=date,
            total_tenders=total_tenders,
            tenders_indexed=indexed_tenders,
            platforms_active=0,  # TODO: count from Platform
        )
        
        self.db.add(metrics)
        self.db.commit()
        
        logger.info(f"Collected metrics: {total_tenders} tenders, {indexed_tenders} indexed")
        return metrics
    
    def record_scraper_run(
        self,
        platform_id: int,
        platform_name: str,
        success: bool,
        runtime_seconds: float,
        items_count: int,
    ) -> ScraperMetrics:
        """Record scraper run
        
        Args:
            platform_id: Platform ID
            platform_name: Platform name
            success: Success status
            runtime_seconds: Runtime in seconds
            items_count: Items scraped
        
        Returns:
            ScraperMetrics record
        """
        # Get or create metrics
        query = self.db.query(ScraperMetrics).filter(
            ScraperMetrics.platform_id == platform_id
        )
        metrics = query.first()
        
        if not metrics:
            metrics = ScraperMetrics(
                platform_id=platform_id,
                platform_name=platform_name,
            )
            self.db.add(metrics)
        
        # Update counts
        metrics.total_runs += 1
        if success:
            metrics.successful_runs += 1
            metrics.last_success_at = datetime.utcnow()
        else:
            metrics.failed_runs += 1
        
        # Update performance
        metrics.total_items_scraped += items_count
        metrics.avg_runtime_seconds = (
            (metrics.avg_runtime_seconds * (metrics.total_runs - 1) + runtime_seconds)
            / metrics.total_runs
        )
        metrics.success_rate = metrics.successful_runs / metrics.total_runs * 100
        metrics.last_run_at = datetime.utcnow()
        
        self.db.commit()
        logger.info(f"Recorded scraper run: {platform_name} - {'success' if success else 'failed'}")
        
        return metrics
    
    def record_search(self, query_time_ms: float, results_count: int, query: str = None):
        """Record search metrics
        
        Args:
            query_time_ms: Query time in milliseconds
            results_count: Number of results
            query: Search query
        """
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get or create today's metrics
        search_metrics = self.db.query(SearchMetrics).filter(
            SearchMetrics.date >= today
        ).first()
        
        if not search_metrics:
            search_metrics = SearchMetrics(date=today)
            self.db.add(search_metrics)
        
        # Update counts
        search_metrics.total_searches += 1
        search_metrics.avg_query_time_ms = (
            (search_metrics.avg_query_time_ms * (search_metrics.total_searches - 1) + query_time_ms)
            / search_metrics.total_searches
        )
        search_metrics.total_results_returned += results_count
        
        self.db.commit()
        logger.debug(f"Recorded search: {query_time_ms}ms, {results_count} results")
