"""Analytics data models"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float, JSON, BigInteger

from factory_parsers.shared.database import Base


class DailyMetrics(Base):
    """Daily metrics snapshot"""
    
    __tablename__ = "daily_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True, nullable=False)
    
    # Counts
    total_tenders = Column(Integer, default=0)
    tenders_scraped = Column(Integer, default=0)
    tenders_normalized = Column(Integer, default=0)
    tenders_indexed = Column(Integer, default=0)
    
    # Platform stats
    platforms_active = Column(Integer, default=0)
    search_rules_active = Column(Integer, default=0)
    
    # Quality metrics
    normalization_success_rate = Column(Float, default=0.0)
    extraction_success_rate = Column(Float, default=0.0)
    
    # Financial
    total_budget = Column(Float, default=0.0)
    avg_budget = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class ScraperMetrics(Base):
    """Per-scraper performance metrics"""
    
    __tablename__ = "scraper_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    platform_id = Column(Integer, index=True, nullable=False)
    platform_name = Column(String(100), nullable=False)
    
    # Scraping stats
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    
    # Performance
    avg_runtime_seconds = Column(Float, default=0.0)
    total_items_scraped = Column(Integer, default=0)
    
    # Success rate
    success_rate = Column(Float, default=0.0)
    
    # Timestamps
    last_run_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SearchMetrics(Base):
    """Search activity metrics"""
    
    __tablename__ = "search_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, index=True, default=datetime.utcnow)
    
    # Search stats
    total_searches = Column(Integer, default=0)
    avg_query_time_ms = Column(Float, default=0.0)
    total_results_returned = Column(BigInteger, default=0)
    
    # Popular searches
    top_queries = Column(JSON, nullable=True)  # List of top search terms
    
    # Filter usage
    filters_used = Column(JSON, nullable=True)  # Dict of filter usage
    
    created_at = Column(DateTime, default=datetime.utcnow)
