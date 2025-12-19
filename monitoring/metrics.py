"""Prometheus metrics collection"""

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Scraper metrics
scraper_runs = Counter(
    'scraper_runs_total',
    'Total scraper runs',
    ['platform', 'status']
)

scraper_items = Counter(
    'scraper_items_total',
    'Total items scraped',
    ['platform']
)

# Search metrics
search_queries = Counter(
    'search_queries_total',
    'Total search queries',
    ['status']
)

search_duration = Histogram(
    'search_duration_seconds',
    'Search query duration',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

# Database metrics
db_connections = Gauge(
    'database_connections',
    'Active database connections'
)

db_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

# Elasticsearch metrics
es_index_size = Gauge(
    'elasticsearch_index_size_bytes',
    'Elasticsearch index size',
    ['index']
)

es_doc_count = Gauge(
    'elasticsearch_documents_total',
    'Total documents in index',
    ['index']
)

# Task queue metrics
celery_tasks = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration',
    ['task_name']
)


class MetricsExporter:
    """Export metrics for Prometheus"""
    
    @staticmethod
    def record_request(method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request"""
        request_count.labels(method=method, endpoint=endpoint, status=status).inc()
        request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def record_scraper_run(platform: str, success: bool, items: int):
        """Record scraper run"""
        status = 'success' if success else 'failed'
        scraper_runs.labels(platform=platform, status=status).inc()
        scraper_items.labels(platform=platform).inc(items)
    
    @staticmethod
    def record_search(success: bool, duration: float):
        """Record search query"""
        status = 'success' if success else 'failed'
        search_queries.labels(status=status).inc()
        search_duration.observe(duration)
    
    @staticmethod
    def record_celery_task(task_name: str, success: bool, duration: float):
        """Record Celery task"""
        status = 'success' if success else 'failed'
        celery_tasks.labels(task_name=task_name, status=status).inc()
        celery_task_duration.labels(task_name=task_name).observe(duration)
