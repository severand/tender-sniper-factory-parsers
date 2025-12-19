# 📊 Factory Parsers - Система логирования и мониторинга

## 🎯 Оглавление

1. [Обзор](#обзор)
2. [Структурированные логи (JSON)](#структурированные-логи-json)
3. [Централизованный сбор логов](#централизованный-сбор-логов)
4. [Метрики Prometheus](#метрики-prometheus)
5. [Алерты](#алерты)
6. [Grafana дашборды](#grafana-дашборды)
7. [Имплементация](#имплементация)
8. [Примеры запросов](#примеры-запросов)

---

## 🎯 Обзор

### Архитектура логирования

```
factory_parsers services (13 modules)
        ↓
    structlog (JSON formatter)
        ↓
    ┌───────────────────────────────┐
    │   Centralized Log Collector   │
    │  (ELK Stack или EFK или Loki) │
    └───────────────────────────────┘
        ↙              ↓              ↖
   Elasticsearch   PostgreSQL    Prometheus
        ↓              ↓              ↓
   Kibana UI    Grafana Logs    Grafana Metrics
```

### Трёхуровневая система

1. **Структурированные логи (JSON)** → все сервисы пишут JSON
2. **Централизованный сбор** → ELK/EFK/Loki собирает в одном месте
3. **Метрики & Алерты** → Prometheus + Grafana для KPI и срабатывания триггеров

---

## 📝 Структурированные логи (JSON)

### Обязательные поля

Все логи содержат:

```json
{
  "timestamp": "2025-12-16T20:30:45.123Z",
  "service": "web_scraper_service",
  "worker": "scrapy-worker-1",
  "environment": "production",
  "version": "1.0.0",
  
  "platform_id": "e-tender-kz",
  "tender_id": "uuid-123",
  "file_id": "uuid-456",
  "task_id": "celery-task-789",
  "request_id": "req-999",
  
  "event_type": "success",
  "message": "Tender parsed successfully",
  "level": "info",
  
  "http_status": 200,
  "proxy_id": "proxy-rotation-12",
  "captcha_used": false,
  "captcha_type": null,
  "duration_ms": 1234,
  
  "retry_count": 0,
  "error_code": null,
  "error_message": null,
  "stack_trace": null,
  
  "metadata": {
    "url": "https://example.com/tender/123",
    "page_number": 1,
    "selector_used": "div.tender-item",
    "items_count": 50,
    "js_rendered": true,
    "cloudflare_detected": false,
    "rate_limited": false
  }
}
```

### Типы событий (event_type)

| Тип | Используется | Пример |
|-----|---|---|
| **start** | Начало операции | Запуск парсинга тендера |
| **success** | Успешно завершено | Тендер распарсен, данные сохранены |
| **retry** | Повторная попытка | 3-я попытка после timeout |
| **error** | Ошибка (логируется, операция может продолжиться) | HTTP 429, капча не решена |
| **circuit_breaker** | Срабатывание circuit breaker | Много ошибок от площадки, отключаем на N сек |
| **warning** | Предупреждение | Rate limit скоро, нужно замедлиться |
| **metrics** | Метрика (не ошибка, не событие, просто мера) | Обработано 1000 тендеров, среднее время 2.5s |

### Примеры структурированных логов

#### ✅ Успешный парсинг

```json
{
  "timestamp": "2025-12-16T20:30:45.123Z",
  "service": "web_scraper_service",
  "worker": "scrapy-worker-5",
  "platform_id": "e-tender-kz",
  "tender_id": "ETK-2025-001234",
  "task_id": "task-abc123",
  "event_type": "success",
  "message": "Tender parsed and saved",
  "level": "info",
  "http_status": 200,
  "proxy_id": "proxy-rotation-3",
  "captcha_used": false,
  "duration_ms": 2150,
  "metadata": {
    "url": "https://www.etender.kz/tender/2025-001234",
    "items_found": 1,
    "js_rendered": true,
    "cloudflare_detected": false
  }
}
```

#### ⚠️ Капча срабатила, но решена

```json
{
  "timestamp": "2025-12-16T20:31:12.456Z",
  "service": "web_scraper_service",
  "worker": "scrapy-worker-7",
  "platform_id": "zakupki-gov-ru",
  "tender_id": "ZAKUPKI-2025-005678",
  "task_id": "task-def456",
  "event_type": "success",
  "message": "Tender fetched after captcha",
  "level": "warning",
  "http_status": 403,
  "proxy_id": "proxy-rotation-8",
  "captcha_used": true,
  "captcha_type": "recaptcha_v3",
  "duration_ms": 8500,
  "retry_count": 1,
  "metadata": {
    "url": "https://zakupki.gov.ru/223/purchase/562345",
    "captcha_solve_time_ms": 5000,
    "captcha_attempts": 1,
    "captcha_cost_usd": 0.003
  }
}
```

#### ❌ Ошибка (429 - Rate Limited)

```json
{
  "timestamp": "2025-12-16T20:32:05.789Z",
  "service": "web_scraper_service",
  "worker": "scrapy-worker-2",
  "platform_id": "e-tender-kz",
  "tender_id": "ETK-2025-009999",
  "task_id": "task-ghi789",
  "event_type": "retry",
  "message": "Rate limited, retrying in 60s",
  "level": "warning",
  "http_status": 429,
  "proxy_id": "proxy-rotation-5",
  "captcha_used": false,
  "duration_ms": 350,
  "retry_count": 2,
  "error_code": "HTTP_429",
  "error_message": "Too Many Requests",
  "metadata": {
    "url": "https://www.etender.kz/tender/2025-009999",
    "retry_after_seconds": 60,
    "requests_per_minute": 45,
    "rate_limit_per_minute": 30
  }
}
```

#### 🔴 Критическая ошибка (circuit breaker)

```json
{
  "timestamp": "2025-12-16T20:33:02.012Z",
  "service": "web_scraper_service",
  "worker": "scheduler",
  "platform_id": "unknown-platform",
  "task_id": "task-jkl012",
  "event_type": "circuit_breaker",
  "message": "Circuit breaker triggered for platform",
  "level": "error",
  "http_status": null,
  "error_code": "CIRCUIT_BREAKER_OPEN",
  "error_message": "Platform returned 10 consecutive errors (5xx) in 5 minutes",
  "metadata": {
    "platform": "unknown-platform",
    "consecutive_errors": 10,
    "error_types": ["503", "503", "500", "503", "502", "503", "500", "503", "503", "503"],
    "circuit_open_duration_seconds": 300,
    "notify_admin": true
  }
}
```

#### 📊 Метрика (метаданные о работе)

```json
{
  "timestamp": "2025-12-16T20:35:00.000Z",
  "service": "scheduler_service",
  "event_type": "metrics",
  "message": "Hourly statistics",
  "level": "info",
  "metadata": {
    "period_minutes": 60,
    "tenders_processed": 1234,
    "tenders_success": 1180,
    "tenders_failed": 54,
    "success_rate_percent": 95.6,
    "avg_processing_time_ms": 2340,
    "captchas_solved": 78,
    "captcha_success_rate_percent": 94.2,
    "proxies_used": 12,
    "platforms_active": 4,
    "platform_stats": {
      "e-tender-kz": {"count": 580, "errors": 15, "rate_limit_hits": 8},
      "zakupki-gov-ru": {"count": 350, "errors": 22, "rate_limit_hits": 18},
      "planfact-kz": {"count": 200, "errors": 10, "rate_limit_hits": 3},
      "sberbank-ru": {"count": 104, "errors": 7, "rate_limit_hits": 2}
    }
  }
}
```

---

## 🌐 Централизованный сбор логов

### Вариант 1: ELK Stack (Elasticsearch + Logstash + Kibana)

**Преимущества:**
- Мощный полнотекстовый поиск
- Огромное сообщество
- Enterprise-ready

**docker-compose.yml:**

```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch_data:
```

**logstash.conf:**

```
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  if [service] {
    mutate {
      add_field => { "[@metadata][index_name]" => "%{service}-%{+YYYY.MM.dd}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "%{[@metadata][index_name]}"
  }
}
```

### Вариант 2: EFK Stack (Elasticsearch + Fluent Bit + Kibana)

**Преимущества:**
- Легче чем Logstash
- Меньше памяти
- Быстрее для высоконагруженных систем

**fluent-bit.conf:**

```
[SERVICE]
    Flush        5
    Daemon       Off
    Log_Level    info

[INPUT]
    Name              tail
    Path              /var/log/factory_parsers/*.json
    Parser            json
    Tag               factory_parsers.*
    Refresh_Interval  5

[FILTER]
    Name    modify
    Match   *
    Add     cluster_id my-cluster
    Add     environment production

[OUTPUT]
    Name            es
    Match           *
    Host            elasticsearch
    Port            9200
    Logstash_Format On
    Logstash_Prefix factory_parsers
    Type            _doc
```

### Вариант 3: Loki (Grafana Loki)

**Преимущества:**
- Меньше памяти, чем Elasticsearch
- Встроена в Grafana
- Отличный для контейнеризованных систем

**loki-config.yml:**

```yaml
auth_enabled: false

ingester:
  chunk_idle_period: 3m
  chunk_retain_period: 1m
  max_chunk_age: 1h
  chunk_encoding: gzip

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema:
        version: v11
        index:
          prefix: index_
          period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

server:
  http_listen_port: 3100

# http_server_read_timeout: 600s
# http_server_write_timeout: 600s
```

### Настройка логирования в Python (structlog)

**factory_parsers/shared/logger.py:**

```python
import json
import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime, timezone

import structlog
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with required fields."""
    
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Ensure required fields exist
        log_record.setdefault('service', 'factory_parsers')
        log_record.setdefault('worker', 'unknown')
        log_record.setdefault('environment', 'production')
        log_record.setdefault('version', '1.0.0')
        log_record.setdefault('event_type', 'log')
        log_record.setdefault('duration_ms', None)
        log_record.setdefault('retry_count', 0)


def setup_logging(service_name: str, worker_name: str = "default"):
    """Setup structured logging with JSON output."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup Python logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # JSON handler to stdout
    json_handler = logging.StreamHandler(sys.stdout)
    json_handler.setLevel(logging.DEBUG)
    formatter = CustomJsonFormatter('%(service)s %(event_type)s %(message)s')
    json_handler.setFormatter(formatter)
    root_logger.addHandler(json_handler)
    
    # Get structlog logger
    logger = structlog.get_logger(service_name)
    
    # Bind context
    logger = logger.bind(
        service=service_name,
        worker=worker_name,
        environment="production"
    )
    
    return logger


# Usage in services
logger = setup_logging("web_scraper_service", "scrapy-worker-1")

# Log success
logger.info(
    "tender_parsed",
    event_type="success",
    tender_id="ETK-2025-001",
    platform_id="e-tender-kz",
    http_status=200,
    proxy_id="proxy-5",
    captcha_used=False,
    duration_ms=2150,
    metadata={
        "url": "https://example.com/tender/123",
        "items_count": 1
    }
)

# Log error with retry
logger.warning(
    "rate_limited",
    event_type="retry",
    tender_id="ETK-2025-002",
    platform_id="e-tender-kz",
    http_status=429,
    proxy_id="proxy-7",
    retry_count=2,
    duration_ms=450,
    error_code="HTTP_429",
    error_message="Too Many Requests"
)
```

---

## 📊 Метрики Prometheus

### Конфигурация Prometheus

**prometheus.yml:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'factory_parsers'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Метрики (Python код)

**factory_parsers/shared/metrics.py:**

```python
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest,
    CollectorRegistry, REGISTRY
)
import time

# Registries
registry = REGISTRY

# Counters - кумулятивные счётчики
tasks_total = Counter(
    'factory_parsers_tasks_total',
    'Total tasks processed',
    ['service', 'task_type', 'status'],
    registry=registry
)

tasks_retried = Counter(
    'factory_parsers_tasks_retried_total',
    'Total task retries',
    ['service', 'reason'],
    registry=registry
)

http_requests_total = Counter(
    'factory_parsers_http_requests_total',
    'Total HTTP requests',
    ['service', 'platform', 'status_code'],
    registry=registry
)

http_errors_total = Counter(
    'factory_parsers_http_errors_total',
    'Total HTTP errors by type',
    ['service', 'platform', 'error_code'],
    registry=registry
)

captchas_solved_total = Counter(
    'factory_parsers_captchas_solved_total',
    'Total captchas solved',
    ['service', 'captcha_type', 'status'],
    registry=registry
)

proxy_failures_total = Counter(
    'factory_parsers_proxy_failures_total',
    'Total proxy failures',
    ['service', 'proxy_id', 'reason'],
    registry=registry
)

# Histograms - распределение времени
task_duration_seconds = Histogram(
    'factory_parsers_task_duration_seconds',
    'Task processing duration',
    ['service', 'task_type'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
    registry=registry
)

api_response_time_seconds = Histogram(
    'factory_parsers_api_response_time_seconds',
    'API response time',
    ['service', 'platform', 'endpoint'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=registry
)

file_processing_time_seconds = Histogram(
    'factory_parsers_file_processing_time_seconds',
    'File processing time (extract/AI)',
    ['service', 'file_type'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=registry
)

# Gauges - текущее значение
active_tasks = Gauge(
    'factory_parsers_active_tasks',
    'Currently active tasks',
    ['service'],
    registry=registry
)

proxy_health = Gauge(
    'factory_parsers_proxy_health',
    'Proxy health status (1=healthy, 0=unhealthy)',
    ['proxy_id'],
    registry=registry
)

crawler_queue_size = Gauge(
    'factory_parsers_crawler_queue_size',
    'Size of crawler queue',
    ['service', 'queue_name'],
    registry=registry
)

# Rate - процент ошибок
error_rate = Gauge(
    'factory_parsers_error_rate_percent',
    'Error rate percentage',
    ['service', 'period'],
    registry=registry
)

captcha_rate_per_thousand = Gauge(
    'factory_parsers_captcha_rate_per_thousand',
    'Captchas per 1000 requests',
    ['service', 'platform'],
    registry=registry
)

# Usage examples

def track_task(service: str, task_type: str, success: bool, duration_ms: float):
    """Track task execution."""
    status = 'success' if success else 'error'
    tasks_total.labels(service=service, task_type=task_type, status=status).inc()
    task_duration_seconds.labels(service=service, task_type=task_type).observe(duration_ms / 1000)

def track_http_request(service: str, platform: str, status_code: int, duration_ms: float):
    """Track HTTP request."""
    http_requests_total.labels(service=service, platform=platform, status_code=status_code).inc()
    api_response_time_seconds.labels(service=service, platform=platform, endpoint="/").observe(duration_ms / 1000)
    
    if status_code >= 400:
        if status_code == 429:
            http_errors_total.labels(service=service, platform=platform, error_code="RATE_LIMITED").inc()
        elif status_code == 403:
            http_errors_total.labels(service=service, platform=platform, error_code="FORBIDDEN").inc()
        elif status_code >= 500:
            http_errors_total.labels(service=service, platform=platform, error_code="SERVER_ERROR").inc()

def track_captcha(service: str, captcha_type: str, solved: bool):
    """Track captcha attempt."""
    status = 'solved' if solved else 'failed'
    captchas_solved_total.labels(service=service, captcha_type=captcha_type, status=status).inc()

def set_active_tasks(service: str, count: int):
    """Set number of active tasks."""
    active_tasks.labels(service=service).set(count)
```

### Метрики по типам

| Метрика | Type | Назначение |
|---------|------|----------|
| `tasks_total` | Counter | Количество задач (успешно/ошибка/отклонено) |
| `tasks_retried_total` | Counter | Количество ретраев |
| `http_requests_total` | Counter | Количество HTTP запросов по status |
| `http_errors_total` | Counter | Количество ошибок (429, 403, 5xx) |
| `captchas_solved_total` | Counter | Количество решённых капч |
| `proxy_failures_total` | Counter | Количество сбоев прокси |
| `task_duration_seconds` | Histogram | Распределение времени задач |
| `api_response_time_seconds` | Histogram | Время ответа от API площадок |
| `file_processing_time_seconds` | Histogram | Время обработки файлов |
| `active_tasks` | Gauge | Текущее количество активных задач |
| `proxy_health` | Gauge | Здоровье каждого прокси (1/0) |
| `crawler_queue_size` | Gauge | Размер очереди парсера |
| `error_rate_percent` | Gauge | Процент ошибок |
| `captcha_rate_per_thousand` | Gauge | Капч на 1000 запросов |

---

## 🚨 Алерты

### Конфигурация алертов Prometheus

**alert-rules.yml:**

```yaml
groups:
  - name: factory_parsers_alerts
    interval: 30s
    rules:
      # Резкий рост 429/403 ошибок
      - alert: HighRateLimitErrors
        expr: |
          rate(factory_parsers_http_errors_total{
            error_code=~"RATE_LIMITED|FORBIDDEN"
          }[5m]) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate limiting on {{ $labels.platform }}"
          description: "Platform {{ $labels.platform }} returning 429/403 at {{ $value }} errors/sec"

      # Падение throughput
      - alert: LowThroughput
        expr: |
          rate(factory_parsers_tasks_total{
            status="success"
          }[5m]) < 1.0
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Low throughput on {{ $labels.service }}"
          description: "Task success rate fell below 1/sec"

      # Рост времени обработки файлов
      - alert: HighFileProcessingTime
        expr: |
          histogram_quantile(0.95,
            rate(factory_parsers_file_processing_time_seconds_bucket[5m])
          ) > 60
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High file processing time"
          description: "95th percentile of file processing time is {{ $value }}s"

      # Высокий процент ошибок (>10%)
      - alert: HighErrorRate
        expr: |
          (
            rate(factory_parsers_tasks_total{
              status="error"
            }[5m])
            /
            rate(factory_parsers_tasks_total[5m])
          ) * 100 > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"
          description: "Error rate is {{ $value | humanizePercentage }}"

      # Слишком много капч (>100 на 1000 запросов)
      - alert: ExcessiveCaptchaRate
        expr: |
          factory_parsers_captcha_rate_per_thousand > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Excessive captcha rate on {{ $labels.platform }}"
          description: "Captcha rate is {{ $value }} per 1000 requests"

      # Платформа вернула 10+ ошибок 5xx подряд
      - alert: PlatformServerErrors
        expr: |
          increase(factory_parsers_http_errors_total{
            error_code="SERVER_ERROR"
          }[5m]) > 10
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Platform {{ $labels.platform }} returning many 5xx errors"
          description: "{{ $value }} server errors in last 5 minutes"

      # Отказ прокси
      - alert: ProxyDown
        expr: |
          factory_parsers_proxy_health == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Proxy {{ $labels.proxy_id }} is down"
          description: "Proxy health is 0 for more than 2 minutes"

      # Переполнение очереди
      - alert: QueueBacklog
        expr: |
          factory_parsers_crawler_queue_size > 10000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Crawler queue backlog"
          description: "Queue size is {{ $value }} items"

      # Ретраи вループе
      - alert: HighRetryRate
        expr: |
          rate(factory_parsers_tasks_retried_total[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High retry rate on {{ $labels.service }}"
          description: "Retry rate is {{ $value }} per second"
```

### Интеграция алертов

**Отправка в Slack:**

```yaml
alert_manager_config:
  route:
    group_by: ['alertname', 'cluster']
    group_wait: 10s
    group_interval: 10s
    repeat_interval: 1h
    receiver: 'slack'
  receivers:
    - name: 'slack'
      slack_configs:
        - api_url: '${SLACK_WEBHOOK_URL}'
          channel: '#factory-parsers-alerts'
          title: 'Alert: {{ .GroupLabels.alertname }}'
          text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

---

## 📈 Grafana Дашборды

### Дашборд 1: System Overview (общая статистика)

```json
{
  "dashboard": {
    "title": "Factory Parsers - System Overview",
    "panels": [
      {
        "title": "Tasks Per Second",
        "targets": [
          {
            "expr": "rate(factory_parsers_tasks_total[1m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate %",
        "targets": [
          {
            "expr": "(rate(factory_parsers_tasks_total{status='error'}[5m]) / rate(factory_parsers_tasks_total[5m])) * 100"
          }
        ],
        "type": "gauge",
        "thresholds": "5,10"
      },
      {
        "title": "HTTP Status Codes",
        "targets": [
          {
            "expr": "rate(factory_parsers_http_requests_total[1m])",
            "legendFormat": "{{ status_code }}"
          }
        ],
        "type": "piechart"
      },
      {
        "title": "Captcha Rate per 1000 Requests",
        "targets": [
          {
            "expr": "factory_parsers_captcha_rate_per_thousand",
            "legendFormat": "{{ platform }}"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

### Дашборд 2: Platform Performance (по площадкам)

```json
{
  "dashboard": {
    "title": "Factory Parsers - Platform Performance",
    "templating": {
      "list": [
        {
          "name": "platform",
          "type": "query",
          "datasource": "Prometheus",
          "query": "label_values(factory_parsers_http_requests_total, platform)",
          "multi": true
        }
      ]
    },
    "panels": [
      {
        "title": "{{ platform }} - Requests/sec",
        "targets": [
          {
            "expr": "rate(factory_parsers_http_requests_total{platform=\"$platform\"}[1m])"
          }
        ]
      },
      {
        "title": "{{ platform }} - Error Types",
        "targets": [
          {
            "expr": "rate(factory_parsers_http_errors_total{platform=\"$platform\"}[5m])",
            "legendFormat": "{{ error_code }}"
          }
        ]
      },
      {
        "title": "{{ platform }} - Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(factory_parsers_api_response_time_seconds_bucket{platform=\"$platform\"}[5m]))"
          }
        ]
      },
      {
        "title": "{{ platform }} - Captcha Usage",
        "targets": [
          {
            "expr": "rate(factory_parsers_captchas_solved_total{platform=\"$platform\"}[5m])",
            "legendFormat": "{{ captcha_type }}"
          }
        ]
      }
    ]
  }
}
```

### Дашборд 3: Proxy & Network Health (прокси)

```json
{
  "dashboard": {
    "title": "Factory Parsers - Proxy & Network",
    "panels": [
      {
        "title": "Proxy Health Status",
        "targets": [
          {
            "expr": "factory_parsers_proxy_health",
            "legendFormat": "{{ proxy_id }}"
          }
        ],
        "type": "table"
      },
      {
        "title": "Proxy Failure Rate",
        "targets": [
          {
            "expr": "rate(factory_parsers_proxy_failures_total[5m])",
            "legendFormat": "{{ proxy_id }} - {{ reason }}"
          }
        ]
      },
      {
        "title": "Rate Limit Hits by Proxy",
        "targets": [
          {
            "expr": "rate(factory_parsers_http_errors_total{error_code='RATE_LIMITED'}[5m])",
            "legendFormat": "{{ platform }}"
          }
        ]
      }
    ]
  }
}
```

### Дашборд 4: Logs (Kibana/Loki)

**Kibana Queries:**

```
# Все ошибки за последний час
service.keyword:"web_scraper_service" AND event_type:"error" AND timestamp:[now-1h TO now]

# Капчи, которые не решены
service.keyword:"web_scraper_service" AND captcha_used:true AND event_type:"error"

# 429 ошибки по платформам
http_status:429 | stats count() by platform_id

# Среднее время обработки по типам задач
| stats avg(duration_ms) by task_type

# Прокси, которые чаще блокируются
http_status:"403" | stats count() by proxy_id | sort - count
```

---

## 💻 Имплементация

### 1. Добавить в shared/logger.py

```python
# factory_parsers/shared/logger.py
# (см. выше структурированные логи и инициализацию)
```

### 2. Добавить в shared/metrics.py

```python
# factory_parsers/shared/metrics.py
# (см. выше Prometheus метрики)
```

### 3. Интегрировать в каждый сервис

```python
# factory_parsers/web_scraper_service/run_worker.py

from factory_parsers.shared.logger import setup_logging
from factory_parsers.shared.metrics import track_task, track_http_request

logger = setup_logging("web_scraper_service", "scrapy-worker-1")

# В обработчике задачи:
try:
    start_time = time.time()
    result = process_tender(tender_data)
    duration_ms = (time.time() - start_time) * 1000
    
    logger.info(
        "tender_processed",
        event_type="success",
        tender_id=tender_data['id'],
        duration_ms=int(duration_ms),
        http_status=200
    )
    track_task("web_scraper", "tender_parse", True, duration_ms)
except Exception as e:
    logger.error(
        "tender_processing_failed",
        event_type="error",
        tender_id=tender_data['id'],
        error_code=str(type(e).__name__),
        error_message=str(e)
    )
    track_task("web_scraper", "tender_parse", False, duration_ms)
```

### 4. Docker Compose для всей стека

```yaml
version: '3.9'

services:
  # Elasticsearch + Logstash + Kibana
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert-rules.yml:/etc/prometheus/alert-rules.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  # Grafana
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

  # Alert Manager
  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"

volumes:
  elasticsearch_data:
  prometheus_data:
  grafana_data:
```

---

## 🔍 Примеры запросов

### Kibana/Loki queries

```bash
# Найти все ошибки 429 по площадкам за последний час
service="web_scraper_service" AND http_status=429 AND timestamp>=now-1h
| stats count() by platform_id

# Какие прокси чаще блокируются?
http_status=403 | stats count() by proxy_id | sort -count
| limit 10

# Когда срабатывают капчи?
captcha_used=true | stats count() by platform_id, captcha_type

# Где самое длительное время обработки?
| stats avg(duration_ms), max(duration_ms), percentile(duration_ms, 95) by service

# Все retry события
event_type="retry" | stats count() by service, error_code

# Circuit breaker срабатывания
event_type="circuit_breaker" | table timestamp, platform_id, error_message, metadata.circuit_open_duration_seconds
```

### Prometheus queries

```promql
# TPS (tasks per second) по статусам
rate(factory_parsers_tasks_total[1m])

# Процент ошибок
(rate(factory_parsers_tasks_total{status="error"}[5m]) / rate(factory_parsers_tasks_total[5m])) * 100

# P95 время обработки файлов
histogram_quantile(0.95, rate(factory_parsers_file_processing_time_seconds_bucket[5m]))

# 429 ошибки по платформам
rate(factory_parsers_http_errors_total{error_code="RATE_LIMITED"}[5m])

# Капч на 1000 запросов
(rate(factory_parsers_captchas_solved_total[1m]) / rate(factory_parsers_http_requests_total[1m])) * 1000

# Размер очереди
factory_parsers_crawler_queue_size
```

---

## 🎯 Админ-дашборд для быстрого анализа

**Что видит админ в реальном времени:**

1. **System Overview**
   - Текущий TPS (tasks/sec)
   - Error rate %
   - Active tasks
   - Queue backlog

2. **Alerts**
   - Все срабатившие алерты
   - Почему срабатили (ссылка на логи)
   - Рекомендуемое действие

3. **Per-Platform Stats**
   - Requests/sec
   - Error rate (и их типы)
   - Response time (p50/p95/p99)
   - Captcha rate
   - Last 10 errors (с ссылкой на полный лог)

4. **Proxy Health**
   - Статус каждого прокси
   - Success rate
   - Блокировки (403/429)
   - Рекомендация: ротировать/заменить

5. **Logs with Filters**
   - По сервису, платформе, ошибке
   - Drill-down: из метрики в лог
   - Полный контекст: URL, proxy, UA, captcha attempt

---

**Версия:** 1.0.0  
**Последнее обновление:** 2025-12-16  
**Статус:** Production-ready
