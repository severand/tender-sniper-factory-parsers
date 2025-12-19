"""FastAPI routes for analytics"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from factory_parsers.shared.database import get_db
from factory_parsers.analytics_service.collector import MetricsCollector
from factory_parsers.analytics_service.analyzer import TenderAnalyzer
from factory_parsers.analytics_service.repositories import MetricsRepository

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    """Get system overview"""
    analyzer = TenderAnalyzer(db)
    collector = MetricsCollector(db)
    
    # Collect current metrics
    metrics = collector.collect_daily_metrics()
    
    return {
        "total_tenders": metrics.total_tenders,
        "indexed_tenders": metrics.tenders_indexed,
        "normalization_success_rate": metrics.normalization_success_rate,
    }


@router.get("/platform-stats")
def get_platform_stats(db: Session = Depends(get_db)):
    """Get statistics by platform"""
    analyzer = TenderAnalyzer(db)
    return analyzer.get_platform_stats()


@router.get("/category-stats")
def get_category_stats(db: Session = Depends(get_db)):
    """Get statistics by category"""
    analyzer = TenderAnalyzer(db)
    return analyzer.get_category_stats()


@router.get("/top-customers")
def get_top_customers(limit: int = Query(20, le=100), db: Session = Depends(get_db)):
    """Get top customers"""
    analyzer = TenderAnalyzer(db)
    return {"customers": analyzer.get_customer_stats(limit=limit)}


@router.get("/date-range")
def get_date_range(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Get statistics for date range"""
    analyzer = TenderAnalyzer(db)
    return analyzer.get_date_range_stats(days=days)


@router.get("/budget-distribution")
def get_budget_distribution(buckets: int = Query(10, ge=5, le=50), db: Session = Depends(get_db)):
    """Get budget distribution"""
    analyzer = TenderAnalyzer(db)
    return {"distribution": analyzer.get_budget_distribution(buckets=buckets)}


@router.get("/scraper-metrics")
def get_scraper_metrics(db: Session = Depends(get_db)):
    """Get all scraper metrics"""
    repo = MetricsRepository(db)
    metrics = repo.get_all_scraper_metrics()
    return {
        "metrics": [
            {
                "platform": m.platform_name,
                "success_rate": m.success_rate,
                "avg_runtime": m.avg_runtime_seconds,
                "total_items": m.total_items_scraped,
            }
            for m in metrics
        ]
    }


@router.get("/daily-metrics/{date_str}")
def get_daily_metrics(date_str: str, db: Session = Depends(get_db)):
    """Get daily metrics"""
    date = datetime.fromisoformat(date_str)
    repo = MetricsRepository(db)
    metrics = repo.get_daily_metrics(date)
    if not metrics:
        return {"error": "No metrics for this date"}
    return {
        "total_tenders": metrics.total_tenders,
        "scraped": metrics.tenders_scraped,
        "normalized": metrics.tenders_normalized,
        "indexed": metrics.tenders_indexed,
    }
