"""Search optimizations (caching, pagination defaults)"""

from typing import Dict, Any
from factory_parsers.shared.cache import Cache
from factory_parsers.search_service.searcher import TenderSearcher


class OptimizedSearchService:
    """Search service with caching and sane defaults"""

    def __init__(self):
        self.searcher = TenderSearcher()
        self.cache = Cache(namespace="search")

    def search_with_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        key = self._build_cache_key(params)
        cached = self.cache.get(key)
        if cached:
            return cached

        results = self.searcher.search(**params)
        self.cache.set(key, results, ttl=60)  # 1 minute cache
        return results

    @staticmethod
    def _build_cache_key(params: Dict[str, Any]) -> str:
        import hashlib
        import json
        payload = json.dumps(params, sort_keys=True)
        return hashlib.md5(payload.encode("utf-8")).hexdigest()
