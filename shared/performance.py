"""Performance monitoring and optimization"""

import time
import functools
from typing import Any, Callable

from factory_parsers.shared.logger import logger


def timer(func: Callable) -> Callable:
    """Measure function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start) * 1000
        logger.info(f"{func.__name__} took {duration_ms:.2f}ms")
        return result
    return wrapper


class PerformanceMonitor:
    """Monitor system performance"""
    
    @staticmethod
    def measure_query_time(query_func: Callable) -> Callable:
        """Measure database query time"""
        @functools.wraps(query_func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            result = query_func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            logger.debug(f"Query executed in {duration_ms:.2f}ms")
            return result
        return wrapper
    
    @staticmethod
    def measure_api_response(route_func: Callable) -> Callable:
        """Measure API response time"""
        @functools.wraps(route_func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            result = route_func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            logger.info(f"API response: {duration_ms:.2f}ms")
            return result
        return wrapper
