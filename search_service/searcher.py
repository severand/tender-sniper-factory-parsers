"""Tender searcher using Elasticsearch"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from factory_parsers.shared.logger import logger
from factory_parsers.search_service.elasticsearch_client import ElasticsearchClient


class TenderSearcher:
    """Search tenders using Elasticsearch"""
    
    def __init__(self):
        self.es_client = ElasticsearchClient()
    
    def search(
        self,
        query: str,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        customer: Optional[str] = None,
        status: Optional[str] = None,
        budget_min: Optional[float] = None,
        budget_max: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        size: int = 20,
        from_: int = 0,
    ) -> Dict[str, Any]:
        """Search tenders with filters
        
        Args:
            query: Search query
            platform: Filter by platform
            category: Filter by category
            customer: Filter by customer
            status: Filter by status
            budget_min: Minimum budget
            budget_max: Maximum budget
            start_date: Filter start date (ISO format)
            end_date: Filter end date (ISO format)
            size: Results per page
            from_: Pagination offset
        
        Returns:
            Search results
        """
        logger.info(f"Searching: {query}")
        
        # Build filters
        filters = {}
        if platform:
            filters['platform'] = platform
        if category:
            filters['category'] = category
        if customer:
            filters['customer'] = customer
        if status:
            filters['status'] = status
        
        # Build range filters
        range_filters = {}
        if budget_min or budget_max:
            budget_filter = {}
            if budget_min:
                budget_filter['gte'] = budget_min
            if budget_max:
                budget_filter['lte'] = budget_max
            range_filters['budget'] = budget_filter
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter['gte'] = start_date
            if end_date:
                date_filter['lte'] = end_date
            range_filters['end_date'] = date_filter
        
        # Execute search
        results = self.es_client.search(
            query=query,
            filters=filters,
            size=size,
            from_=from_,
        )
        
        # Parse results
        return self._parse_results(results)
    
    def search_by_customer(self, customer: str, size: int = 50) -> List[Dict[str, Any]]:
        """Search all tenders for customer
        
        Args:
            customer: Customer name
            size: Max results
        
        Returns:
            List of tenders
        """
        logger.info(f"Searching tenders by customer: {customer}")
        results = self.search(
            query="*",
            customer=customer,
            size=size,
        )
        return results['items']
    
    def search_by_category(self, category: str, size: int = 50) -> List[Dict[str, Any]]:
        """Search all tenders in category
        
        Args:
            category: Category name
            size: Max results
        
        Returns:
            List of tenders
        """
        logger.info(f"Searching tenders by category: {category}")
        results = self.search(
            query="*",
            category=category,
            size=size,
        )
        return results['items']
    
    def get_trending(self, days: int = 7, size: int = 20) -> List[Dict[str, Any]]:
        """Get trending tenders
        
        Args:
            days: Days back to search
            size: Max results
        
        Returns:
            List of trending tenders
        """
        logger.info(f"Fetching trending tenders from last {days} days")
        
        # Calculate date range
        from datetime import timedelta
        end_date = datetime.utcnow().isoformat()
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        results = self.search(
            query="*",
            start_date=start_date,
            end_date=end_date,
            size=size,
        )
        return results['items']
    
    def _parse_results(self, es_results: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Elasticsearch results
        
        Args:
            es_results: Raw Elasticsearch response
        
        Returns:
            Parsed results
        """
        hits = es_results.get('hits', {})
        total = hits.get('total', {})
        
        if isinstance(total, dict):
            total_count = total.get('value', 0)
        else:
            total_count = total
        
        items = []
        for hit in hits.get('hits', []):
            item = hit['_source']
            item['_id'] = hit['_id']
            item['_score'] = hit['_score']
            items.append(item)
        
        return {
            'total': total_count,
            'items': items,
            'query_time_ms': es_results.get('took', 0),
        }
