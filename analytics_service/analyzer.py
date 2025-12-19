"""Tender data analysis"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from factory_parsers.shared.logger import logger
from factory_parsers.normalizer_service.repositories import NormalizedTenderRepository
from factory_parsers.normalizer_service.models import NormalizedTender


class TenderAnalyzer:
    """Analyze tender data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tender_repo = NormalizedTenderRepository(db)
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """Get statistics by platform
        
        Returns:
            Platform statistics
        """
        query = self.db.query(
            NormalizedTender.platform,
            func.count(NormalizedTender.id).label('count'),
            func.avg(NormalizedTender.budget).label('avg_budget'),
            func.sum(NormalizedTender.budget).label('total_budget'),
        ).group_by(NormalizedTender.platform)
        
        stats = {}
        for row in query.all():
            stats[row[0]] = {
                'count': row[1],
                'avg_budget': float(row[2]) if row[2] else 0,
                'total_budget': float(row[3]) if row[3] else 0,
            }
        
        logger.info(f"Platform stats: {len(stats)} platforms")
        return stats
    
    def get_category_stats(self) -> Dict[str, Any]:
        """Get statistics by category
        
        Returns:
            Category statistics
        """
        query = self.db.query(
            NormalizedTender.category,
            func.count(NormalizedTender.id).label('count'),
            func.avg(NormalizedTender.budget).label('avg_budget'),
        ).filter(
            NormalizedTender.category != None
        ).group_by(NormalizedTender.category)
        
        stats = {}
        for row in query.all():
            stats[row[0]] = {
                'count': row[1],
                'avg_budget': float(row[2]) if row[2] else 0,
            }
        
        logger.info(f"Category stats: {len(stats)} categories")
        return stats
    
    def get_customer_stats(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top customers
        
        Args:
            limit: Max results
        
        Returns:
            Top customers
        """
        query = self.db.query(
            NormalizedTender.customer,
            func.count(NormalizedTender.id).label('count'),
            func.sum(NormalizedTender.budget).label('total_budget'),
        ).filter(
            NormalizedTender.customer != None
        ).group_by(
            NormalizedTender.customer
        ).order_by(
            func.count(NormalizedTender.id).desc()
        ).limit(limit)
        
        stats = []
        for row in query.all():
            stats.append({
                'customer': row[0],
                'count': row[1],
                'total_budget': float(row[2]) if row[2] else 0,
            })
        
        logger.info(f"Top customers: {len(stats)} results")
        return stats
    
    def get_date_range_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get statistics for date range
        
        Args:
            days: Number of days back
        
        Returns:
            Date range statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(
            func.date(NormalizedTender.start_date).label('date'),
            func.count(NormalizedTender.id).label('count'),
            func.sum(NormalizedTender.budget).label('total_budget'),
        ).filter(
            NormalizedTender.start_date >= start_date
        ).group_by(
            func.date(NormalizedTender.start_date)
        ).order_by('date')
        
        stats = {}
        for row in query.all():
            if row[0]:
                stats[str(row[0])] = {
                    'count': row[1],
                    'total_budget': float(row[2]) if row[2] else 0,
                }
        
        logger.info(f"Date range stats: {len(stats)} days")
        return stats
    
    def get_budget_distribution(self, buckets: int = 10) -> List[Dict[str, Any]]:
        """Get budget distribution
        
        Args:
            buckets: Number of buckets
        
        Returns:
            Budget distribution
        """
        # Get min and max budget
        result = self.db.query(
            func.min(NormalizedTender.budget),
            func.max(NormalizedTender.budget),
        ).filter(NormalizedTender.budget > 0).first()
        
        if not result or not result[0]:
            return []
        
        min_budget = result[0]
        max_budget = result[1]
        
        bucket_size = (max_budget - min_budget) / buckets
        distribution = []
        
        for i in range(buckets):
            bucket_min = min_budget + (i * bucket_size)
            bucket_max = bucket_min + bucket_size
            
            count = self.db.query(NormalizedTender).filter(
                NormalizedTender.budget >= bucket_min,
                NormalizedTender.budget < bucket_max,
            ).count()
            
            distribution.append({
                'bucket': f"{bucket_min:.0f}-{bucket_max:.0f}",
                'count': count,
            })
        
        logger.info(f"Budget distribution: {buckets} buckets")
        return distribution
