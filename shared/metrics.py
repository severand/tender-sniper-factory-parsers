"""Application metrics - Prometheus (Sprint 39)"""

from prometheus_client import Counter, Histogram, Gauge

# HTTP metrics
http_requests_total = Counter(
    "ts_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "ts_http_request_duration_seconds",
    "HTTP request latency (seconds)",
    ["method", "path"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5),
)

# Scraper metrics
scraped_tenders_total = Counter(
    "ts_scraped_tenders_total",
    "Total scraped tenders",
    ["platform"],
)

scraper_errors_total = Counter(
    "ts_scraper_errors_total",
    "Total scraper errors",
    ["platform", "error_type"],
)

# Normalizer metrics
normalized_tenders_total = Counter(
    "ts_normalized_tenders_total",
    "Total normalized tenders",
    ["platform"],
)

normalization_failures_total = Counter(
    "ts_normalization_failures_total",
    "Total normalization failures",
    ["reason"],
)

# Queue metrics
celery_queue_length = Gauge(
    "ts_celery_queue_length",
    "Celery queue length",
    ["queue"],
)

celery_task_duration_seconds = Histogram(
    "ts_celery_task_duration_seconds",
    "Celery task duration (seconds)",
    ["task_name"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
)
