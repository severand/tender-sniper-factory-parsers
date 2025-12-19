# 🛠️ Factory Parsers - Технические спецификации для разработчиков

## Оглавление

1. [Требования к девюпер](#%D1%82%D1%80%D0%B5%D0%B1%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D1%8F-%D0%BA-%D0%B4%D0%B5%D0%B2%D0%B5%D0%BB%D0%BE%D0%BF%D0%B5%D1%80%D1%83)
2. [Кодовые стандарты](#%D0%BA%D043e%D0%B4%D043e%D0%B2%D044b%D0%B5-%D1%81%D1%82%D0%B0%D043d%D0%B4%D0%B0%D1%80%D1%82%D044b)
3. [Основные чтение и обычай](#%D043e%D0%B1%D044b%D0%B7%D0%B0%D1%82%D0%B5%D043b%D043d%D044b%D0%B5-%D043f%D0%B0%D1%82%D1%82%D0%B5%D1%80%D043d%D044b)
4. [Датабазы](#%D0%B4%D0%B0%D1%82%D0%B0%D0%B1%D0%B0%D0%B7%D044b)
5. [Асинхронные процессы](#%D0%B0%D1%81%D0%B8%D043d%D1%85%D1%80%D043e%D043d%D043d%D044b%D0%B5-%D0%BF%D1%80%D043e%D1%86%D0%B5%D1%81%D1%81%D044b)
6. [Логирование и мониторинг](#%D043b%D043e%D0%B3%D0%B8%D1%80%D043e%D0%B2%D0%B0%D043d%D0%B8%D0%B5-%D0%B8-%D043c%D043e%D043d%D0%B8%D1%82%D043e%D1%80%D0%B8%D043d%D0%B3)
7. [Нажуты и готэкв](#%D0%BF%D0%BE%D0%BF%D044b%D1%82%D043a%D0%B8-%D0%B8-%D0%BD%D043e%D0%B3%D043e%D1%82%D043e%D0%B2%D043a%D0%B8)
8. [Тестирование](#%D1%82%D0%B5%D1%81%D1%82%D0%B8%D1%80%D043e%D0%B2%D0%B0%D043d%D0%B8%D0%B5)
9. [Деплоймент](#%D0%B4%D0%B5%D043f%D043b%D043e%D0%B9%D043c%D0%B5%D043d%D1%82)
10. [Примеры](#%D043f%D1%80%D0%B8%D043c%D0%B5%D1%80%D044b)

---

## Требования к девелоперу

### Знания

- ✅ **Python 3.11+** (type hints, dataclasses, walrus operator)
- ✅ **SQLAlchemy 2.0+** (ORM, async support)
- ✅ **FastAPI** (async web framework)
- ✅ **Scrapy** (web scraping framework)
- ✅ **Playwright** (browser automation)
- ✅ **Celery** (task queue)
- ✅ **PostgreSQL** (SQL database)
- ✅ **Redis** (cache & message broker)
- ✅ **Elasticsearch/OpenSearch** (full-text search)
- ✅ **pytest** (testing framework)

### Наружные нармами

```bash
Python:        3.11+
pip:           latest
poetry:        optional (prefer pip + requirements.txt)
Docker:        latest
Git:           2.30+
```

### Основные тоолы

```bash
pylint              # Linting
black               # Code formatter
isort               # Import sorter
pytest              # Testing
pytest-cov          # Coverage
mypy                # Type checker
pydantic            # Data validation
structlog           # Structured logging
alembic             # Database migrations
```

---

## Кодовые стандарты

### 1. Type Hints (MANDATORY)

Пример:

```python
from typing import Optional, List, Dict, Tuple
from pydantic import BaseModel

class TenderFilters(BaseModel):
    """Tender filter criteria."""
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    platforms: List[str] = []
    region: Optional[str] = None

async def fetch_tenders(
    filters: TenderFilters,
    page: int = 1,
    limit: int = 50
) -> Tuple[List[Dict], int]:
    """Fetch tenders matching filters.
    
    Args:
        filters: Filter criteria
        page: Page number (1-indexed)
        limit: Items per page
        
    Returns:
        Tuple of (tender_list, total_count)
    """
    # Implementation
    pass
```

### 2. Docstrings (Google format)

```python
def process_tender(
    raw_data: Dict[str, Any],
    platform_id: str
) -> Tender:
    """Process raw tender data into normalized format.
    
    Validates input, applies field mapping, and saves to database.
    
    Args:
        raw_data: Raw tender dict from API/scraper
        platform_id: Source platform identifier
        
    Returns:
        Normalized Tender model
        
    Raises:
        ValueError: If data fails validation
        DatabaseError: If save fails
        
    Examples:
        >>> tender = process_tender({...}, "e-tender-kz")
        >>> print(tender.id)
    """
    pass
```

### 3. Naming Conventions

```python
# Classes: PascalCase
class TenderNormalizer:
    pass

class APIClientFactory:
    pass

# Functions: snake_case
async def fetch_tender_list():
    pass

def calculate_budget():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
CACHE_TTL_SECONDS = 3600

# Private: _leading_underscore
def _validate_url(url: str) -> bool:
    pass

class _InternalHelper:
    pass
```

### 4. Line Length & Formatting

```bash
# Use black for formatting
black factory_parsers/

# Max line length: 100 chars (black default)
# Use multiline for long expressions
result = (
    query
    .filter(Tender.budget > min_budget)
    .filter(Tender.platform_id == platform_id)
    .limit(page_size)
    .offset((page - 1) * page_size)
)
```

### 5. Import Organization

```python
# Use isort to auto-format
# isort factory_parsers/

# Standard library
import asyncio
import json
from typing import List, Dict
from pathlib import Path

# Third-party
import sqlalchemy as sa
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException

# Local
from factory_parsers.shared.logger import get_logger
from factory_parsers.storage_layer.models import Tender
from factory_parsers.admin_service.repository import PlatformRepo
```

### 6. Error Handling

```python
# Use custom exceptions
from factory_parsers.shared.exceptions import (
    PlatformNotFound,
    ParseError,
    RateLimitExceeded,
)

try:
    platform = await platform_repo.get_by_id(platform_id)
except PlatformNotFound as e:
    logger.warning(f"Platform not found: {platform_id}")
    raise HTTPException(status_code=404, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Обязательные паттерны

### Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import Optional, List

class BaseRepository(ABC):
    """Abstract repository for data access."""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 50) -> List[Any]:
        pass
    
    @abstractmethod
    async def create(self, data: Dict) -> Any:
        pass

class PlatformRepository(BaseRepository):
    """Platform data access layer."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def get_by_id(self, id: str) -> Optional[Platform]:
        return await self.db_session.get(Platform, id)
```

### Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db_session() -> AsyncSession:
    """Provide database session."""
    async with async_session() as session:
        yield session

async def get_platform_repo(
    db_session: AsyncSession = Depends(get_db_session)
) -> PlatformRepository:
    """Provide platform repository."""
    return PlatformRepository(db_session)

@router.get("/platforms/{id}")
async def get_platform(
    id: str,
    repo: PlatformRepository = Depends(get_platform_repo)
):
    return await repo.get_by_id(id)
```

### Pydantic Models for Validation

```python
from pydantic import BaseModel, Field, validator

class PlatformCreate(BaseModel):
    """Schema for creating a platform."""
    name: str = Field(..., min_length=1, max_length=100)
    base_url: str = Field(..., regex=r'^https?://')
    mode: str = Field(default="auto", regex=r'^(auto|api_only|web_only)$')
    rate_limit_rps: int = Field(default=5, ge=1, le=100)
    
    @validator('base_url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Must be a valid HTTP URL')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "e-tender.kz",
                "base_url": "https://www.etender.kz",
                "mode": "auto"
            }
        }
```

---

## Датабазы

### PostgreSQL Setup

```bash
# В docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: factory_parsers
      POSTGRES_USER: parser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### Alembic Migrations

```bash
# Initialize migration
alembic revision --autogenerate -m "Add Platform table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Connection String

```python
# .env
DATABASE_URL=postgresql+asyncpg://parser:password@localhost:5432/factory_parsers

# config.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    os.getenv("DATABASE_URL"),
    echo=False,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,  # Verify connections before use
)
```

---

## Асинхронные процессы

### Celery Configuration

```python
# factory_parsers/shared/celery_app.py
from celery import Celery

app = Celery(
    'factory_parsers',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)
```

### Task Definition

```python
from factory_parsers.shared.celery_app import app
from factory_parsers.shared.logger import get_logger

logger = get_logger(__name__)

@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def process_tender_task(self, raw_tender_id: str):
    """Process raw tender.
    
    Args:
        raw_tender_id: ID of raw tender to process
    """
    try:
        logger.info(f"Processing tender: {raw_tender_id}")
        # Implementation
    except Exception as exc:
        logger.error(f"Error processing tender: {exc}")
        raise self.retry(exc=exc)
```

### Periodic Tasks

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'schedule-tenders-every-hour': {
        'task': 'factory_parsers.scheduler_service.tasks.schedule_tenders',
        'schedule': crontab(minute=0),  # Every hour
    },
    'cleanup-cache-every-day': {
        'task': 'factory_parsers.cache_layer.tasks.cleanup_cache',
        'schedule': crontab(hour=2, minute=0),  # Every day at 2 AM
    },
}
```

---

## Логирование и мониторинг

### Structured Logging with structlog

```python
# factory_parsers/shared/logger.py
import structlog

logger = structlog.get_logger(__name__)

# Usage
logger.info(
    "tender_processed",
    tender_id="uuid",
    platform="e-tender",
    duration_ms=1234,
    status="success"
)

# Output
{
  "timestamp": "2025-12-16T12:00:00Z",
  "level": "info",
  "logger": "factory_parsers.web_scraper",
  "event": "tender_processed",
  "tender_id": "uuid",
  "platform": "e-tender",
  "duration_ms": 1234,
  "status": "success"
}
```

### Metrics with Prometheus

```python
from prometheus_client import Counter, Histogram

tenders_processed = Counter(
    'tenders_processed_total',
    'Total tenders processed',
    ['platform', 'status']
)

processing_time = Histogram(
    'tender_processing_seconds',
    'Time to process tender',
    ['service']
)

# Usage
tenders_processed.labels(platform='e-tender', status='success').inc()
with processing_time.labels(service='normalizer').time():
    # Do work
    pass
```

---

## Напуты и готэкв

### Нрент ретрай

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
async def fetch_url(url: str) -> str:
    """Fetch URL with retry logic."""
    # Implementation
    pass
```

### Circuit Breaker

```python
from pybreaker import CircuitBreaker

api_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    exclude=[ValueError],  # Don't break on validation errors
)

@api_breaker
async def call_external_api(url: str):
    """Call external API with circuit breaker."""
    pass
```

### Rate Limiting

```python
from ratelimit import limits, sleep_and_retry
import time

@sleep_and_retry
@limits(calls=5, period=60)  # 5 calls per 60 seconds
async def api_call(platform_id: str):
    """API call with rate limiting."""
    pass
```

---

## Тестирование

### pytest Structure

```
factory_parsers/
├── admin_service/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_models.py
│   │   ├── test_repository.py
│   │   ├── test_routes.py
│   │   └── test_service.py
tests/
├── conftest.py
├── test_integration.py
└── test_e2e.py
```

### Test Examples

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.fixture
async def db_session():
    """Provide test database session."""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session

# tests/test_admin.py
@pytest.mark.asyncio
async def test_create_platform(db_session):
    """Test platform creation."""
    repo = PlatformRepository(db_session)
    
    # Create
    platform = await repo.create({
        'name': 'Test Platform',
        'base_url': 'https://test.com'
    })
    
    # Assert
    assert platform.id is not None
    assert platform.name == 'Test Platform'
    
    # Retrieve
    retrieved = await repo.get_by_id(platform.id)
    assert retrieved.name == 'Test Platform'
```

### Coverage

```bash
# Run tests with coverage
pytest --cov=factory_parsers --cov-report=html

# Minimum coverage: 80%
# Critical paths: 95%
```

---

## Деплоймент

### Docker Compose

```yaml
# docker-compose.yml
version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: factory_parsers
      POSTGRES_USER: parser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  scheduler:
    build:
      context: .
      dockerfile: docker/Dockerfile.scheduler
    environment:
      DATABASE_URL: ${DATABASE_URL}
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    environment:
      DATABASE_URL: ${DATABASE_URL}
      CELERY_BROKER_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
```

### Start Commands

```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Local development
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m pytest
```

---

## Примеры

### Пример: Admin Service - Create Platform

```python
# factory_parsers/admin_service/routes.py
from fastapi import APIRouter, Depends, HTTPException
from factory_parsers.admin_service.models import PlatformCreate, Platform
from factory_parsers.admin_service.repository import PlatformRepository

router = APIRouter(prefix="/api/admin/platforms", tags=["admin"])

@router.post("/", response_model=Platform)
async def create_platform(
    platform_data: PlatformCreate,
    repo: PlatformRepository = Depends(get_platform_repo)
):
    """Create a new platform."""
    try:
        # Check if already exists
        existing = await repo.get_by_name(platform_data.name)
        if existing:
            raise HTTPException(status_code=409, detail="Platform already exists")
        
        # Create
        platform = await repo.create(platform_data.dict())
        return platform
    except Exception as e:
        logger.error(f"Error creating platform: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### Пример: Celery Task - Process Tender

```python
# factory_parsers/normalizer_service/worker.py
from factory_parsers.shared.celery_app import app
from factory_parsers.normalizer_service.normalizer import TenderNormalizer
from factory_parsers.storage_layer.db_client import get_db_client

@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def normalize_tender(self, raw_tender_id: str, ai_extraction_id: str):
    """Normalize raw tender with AI extraction."""
    try:
        db = get_db_client()
        normalizer = TenderNormalizer(db)
        
        # Process
        tender = await normalizer.normalize(
            raw_tender_id=raw_tender_id,
            ai_extraction_id=ai_extraction_id
        )
        
        # Log success
        logger.info(
            "tender_normalized",
            tender_id=tender.id,
            platform=tender.platform_id,
        )
        
        return {"tender_id": tender.id, "status": "success"}
        
    except Exception as exc:
        logger.error(f"Normalization failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

---

## От разработчика

💡 **При резолюции вопросов**:
1. Найти аналогичные онти в tests/
2. Присмотреться к другим модулям (shared/, storage_layer/)
3. Консультируясь с PM в Slack

💀 **Кодекс**:
- Не модифицируй от код без ресирвации PM
- Не трони основэй тякту (Celery, Scrapy settings)
- Всегда делай новые витки: git checkout -b feature/
- Пуш в фич ветки для PR и Коне ривью

---

**Ревизия**: 1.0.0  
**От рачяла**: 2025-12-16  
**Ласт упдейт**: 2025-12-16
