"""Repositories for analytics data"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .models import DailyMetrics, ScraperMetrics, SearchMetrics


class MetricsRepository:
    """Repository for analytics metrics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_daily_metrics(self, date: datetime) -> Optional[DailyMetrics]:
        """Get daily metrics"""
        return self.db.query(DailyMetrics).filter(
            DailyMetrics.date.cast(Date) == date.date()
        ).first()
    
    def get_metrics_range(self, start_date: datetime, end_date: datetime) -> List[DailyMetrics]:
        """Get metrics for date range"""
        return self.db.query(DailyMetrics).filter(
            DailyMetrics.date >= start_date,
            DailyMetrics.date <= end_date,
        ).order_by(DailyMetrics.date).all()
    
    def get_scraper_metrics(self, platform_id: int) -> Optional[ScraperMetrics]:
        """Get scraper metrics"""
        return self.db.query(ScraperMetrics).filter(
            ScraperMetrics.platform_id == platform_id
        ).first()
    
    def get_all_scraper_metrics(self) -> List[ScraperMetrics]:
        """Get all scraper metrics"""
        return self.db.query(ScraperMetrics).all()
    
    def get_search_metrics(self, date: datetime) -> Optional[SearchMetrics]:
        """Get search metrics for date"""
        return self.db.query(SearchMetrics).filter(
            SearchMetrics.date.cast(Date) == date.date()
        ).first()
