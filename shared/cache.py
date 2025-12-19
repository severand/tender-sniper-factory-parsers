"""Caching layer for Tender Sniper"""

from typing import Any, Optional
from redis import Redis

from factory_parsers.shared.config import get_settings


class Cache:
    """Simple Redis-based cache"""

    def __init__(self, namespace: str = "tender-sniper"):
        settings = get_settings()
        self.redis = Redis.from_url(settings.redis_url)
        self.namespace = namespace

    def _key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    def get(self, key: str) -> Optional[Any]:
        data = self.redis.get(self._key(key))
        if not data:
            return None
        try:
            import json
            return json.loads(data)
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        import json
        self.redis.setex(self._key(key), ttl, json.dumps(value))

    def invalidate(self, key: str) -> None:
        self.redis.delete(self._key(key))
