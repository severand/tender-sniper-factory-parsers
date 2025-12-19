"""Search service for client API"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from factory_parsers.shared.logger import logger
from factory_parsers.shared.cache import Cache
from factory_parsers.search_service.searcher import TenderSearcher


class SearchService:
    """Search service with caching and filtering"""
    
    def __init__(self, db: Session = None):
        self.searcher = TenderSearcher()
        self.cache = Cache(namespace="search")
    
    def search(self,
               query: str,
               platform: Optional[str] = None,
               category: Optional[str] = None,
               customer: Optional[str] = None,
               budget_min: Optional[float] = None,
               budget_max: Optional[float] = None,
               page: int = 1,
               size: int = 20) -> Dict[str, Any]:
        """Search tenders
        
        Args:
            query: Search query
            platform: Platform filter
            category: Category filter
            customer: Customer filter
            budget_min: Min budget
            budget_max: Max budget
            page: Page number
            size: Results per page
        
        Returns:
            Search results
        """
        # Build cache key
        cache_key = self._build_cache_key({
            'query': query,
            'platform': platform,
            'category': category,
            'customer': customer,
            'budget_min': budget_min,
            'budget_max': budget_max,
            'page': page,
            'size': size,
        })
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for query: {query}")
            return cached
        
        # Execute search
        from_offset = (page - 1) * size
        results = self.searcher.search(
            query=query,
            platform=platform,
            category=category,
            customer=customer,
            budget_min=budget_min,
            budget_max=budget_max,
            size=size,
            from_=from_offset,
        )
        
        # Cache results (60 sec)
        self.cache.set(cache_key, results, ttl=60)
        logger.info(f"Search: {query}, results: {results['total']}")
        
        return results
    
    @staticmethod
    def _build_cache_key(params: Dict[str, Any]) -> str:
        """Build cache key from params"""
        import hashlib
        import json
        payload = json.dumps(params, sort_keys=True)
        return hashlib.md5(payload.encode()).hexdigest()
