"""Scrapy middlewares for web scraping"""

import random
from typing import Optional, List
from scrapy.http import Request, Response
from scrapy.exceptions import IgnoreRequest

from factory_parsers.shared.logger import logger


class ProxyMiddleware:
    """Middleware for proxy rotation"""
    
    def __init__(self, proxy_list: Optional[List[str]] = None):
        self.proxy_list = proxy_list or []
        self.current_proxy_index = 0
    
    def process_request(self, request: Request, spider):
        """Add proxy to request"""
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            request.meta['proxy'] = proxy
            logger.debug(f"Using proxy: {proxy}")
        return None
    
    def process_exception(self, request: Request, exception, spider):
        """Handle proxy errors"""
        logger.error(f"Proxy error: {str(exception)}")
        # Retry with different proxy
        return request


class UserAgentMiddleware:
    """Middleware for User-Agent rotation"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)',
    ]
    
    def process_request(self, request: Request, spider):
        """Add random User-Agent"""
        user_agent = random.choice(self.USER_AGENTS)
        request.headers['User-Agent'] = user_agent
        logger.debug(f"Using User-Agent: {user_agent}")
        return None


class HTTPCacheMiddleware:
    """Middleware for HTTP caching"""
    
    def __init__(self, cache_dir: str = ".scrapy_cache"):
        self.cache_dir = cache_dir
        self.cache = {}
    
    def process_request(self, request: Request, spider):
        """Check cache for request"""
        cache_key = request.url
        if cache_key in self.cache:
            logger.debug(f"Cache hit: {cache_key}")
            # Return cached response
            return None
        return None
    
    def process_response(self, request: Request, response: Response, spider):
        """Cache successful responses"""
        if response.status == 200:
            self.cache[request.url] = response
            logger.debug(f"Cached: {request.url}")
        return response


class RateLimitMiddleware:
    """Middleware for rate limiting"""
    
    def __init__(self, rate_limit: int = 100, window: int = 3600):
        """Initialize rate limiter
        
        Args:
            rate_limit: Max requests per window
            window: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.window = window
        self.requests = []
    
    def process_request(self, request: Request, spider):
        """Check rate limit before request"""
        import time
        current_time = time.time()
        
        # Remove old requests outside window
        self.requests = [req_time for req_time in self.requests 
                        if current_time - req_time < self.window]
        
        if len(self.requests) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded: {len(self.requests)}/{self.rate_limit}")
            raise IgnoreRequest("Rate limit exceeded")
        
        self.requests.append(current_time)
        return None


class RetryMiddleware:
    """Middleware for request retry"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
    
    def process_exception(self, request: Request, exception, spider):
        """Retry failed requests"""
        retry_count = request.meta.get('retry_count', 0)
        
        if retry_count < self.max_retries:
            logger.warning(f"Retrying request {request.url} (attempt {retry_count + 1})")
            request.meta['retry_count'] = retry_count + 1
            return request
        
        logger.error(f"Max retries exceeded for {request.url}")
        return None
