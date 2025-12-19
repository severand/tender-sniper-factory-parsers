# 📋 Дополнительные парсеры (EIS, RTS, Sberbank)

## Обзор

Этот документ описывает интеграцию дополнительных парсеров государственных площадок, которые должны быть интегрированы в систему **factory_parsers** без конфликтов с основной архитектурой.

Листа парсеров:
- **EIS Parser** (`eis_parser.py`)
- **RTS Parser** (`rts_parser.py`)
- **Sberbank Parser** (`sberbank_parser.py`)

---

## Архитектурные принципы интеграции

### 1. Модульность

Каждый парсер должен быть реализован как **независимый модуль** в `backend/factory_parsers/web_scraper_service/spiders/`:

```
backend/factory_parsers/
├── web_scraper_service/
│   ├── spiders/
│   │   ├── base_spider.py          # Базовый класс для всех спайдеров
│   │   ├── e_tender_spider.py
│   │   ├── zakupki_spider.py
│   │   ├── planfact_spider.py
│   │   ├── eis_spider.py           # NEW: EIS парсер
│   │   ├── rts_spider.py           # NEW: RTS парсер
│   │   └── sberbank_spider.py      # NEW: Sberbank парсер
│   ├── settings.py
│   └── middlewares.py
```

### 2. Единые интерфейсы

Все парсеры должны наследоваться от **BaseSpider** (или специализированных базовых классов):

```python
from backend.factory_parsers.web_scraper_service.spiders.base_spider import BaseSpider

class EISSpider(BaseSpider):
    name = "eis_parser"
    platform_id = "eis"
    allowed_domains = ["eis.zakupki.gov.ru"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform_config = self.load_platform_config("eis")
    
    def start_requests(self):
        # Генерирует запросы согласно конфигурации
        pass
    
    def parse_tender_list(self, response):
        # Парсит список тендеров
        pass
    
    def parse_tender_detail(self, response):
        # Парсит детали тендера
        pass
```

### 3. Конфигурация через Admin Service

Для каждого парсера должна быть запись в таблице `Platform` с конфигурацией:

```json
{
  "platform_id": "eis",
  "platform_name": "ЕИС (Единая информационная система)",
  "base_url": "https://eis.zakupki.gov.ru",
  "api_endpoint": "https://eis.zakupki.gov.ru/api/v1",
  "scrape_method": "web_scraper",  // или "api"
  "rate_limit": {
    "requests_per_minute": 30,
    "timeout_seconds": 10
  },
  "search_rules": [
    {
      "search_rule_id": "eis_default",
      "query_pattern": "?query={query}&sort=date&order=desc",
      "pagination": {"type": "offset", "param": "offset", "step": 25}
    }
  ],
  "field_mappings": [
    {"source_field": "notice_number", "target_field": "tender_id"},
    {"source_field": "title", "target_field": "title"},
    ...
  ],
  "enabled": true
}
```

### 4. Логирование и мониторинг

Все парсеры должны использовать единую систему логирования из `shared/logger.py`:

```python
from backend.factory_parsers.shared.logger import setup_logging

logger = setup_logging(service="web_scraper_service", worker="eis_spider")

logger.info(
    "tender_fetched",
    event_type="success",
    platform_id="eis",
    tender_id=tender_id,
    duration_ms=elapsed_time,
    http_status=200
)

logger.error(
    "parse_error",
    event_type="error",
    platform_id="eis",
    error_code="403",
    error_message="Access forbidden",
    proxy_id=proxy_id
)
```

### 5. Обработка ошибок и retry-логика

Для каждого парсера должна быть собственная стратегия обработки ошибок:

```python
class EISSpider(BaseSpider):
    custom_settings = {
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 429, 403],
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
    }
    
    def errback(self, failure):
        # Специализированная обработка ошибок для EIS
        if failure.check(HttpError) and failure.value.response.status == 403:
            # EIS частит возвращает 403 при доступе без прокси
            self.logger.warning("EIS blocked, rotating proxy", proxy_id=self.current_proxy)
            # Запросить новый прокси
        elif failure.check(HttpError) and failure.value.response.status == 429:
            # Rate limit
            self.logger.warning("Rate limited by EIS, increasing delay")
```

---

## Спецификации каждого парсера

### EIS Parser (eis_parser.py)

**Платформа:** ЕИС (Единая информационная система) - https://eis.zakupki.gov.ru

**Характеристики:**
- Поддерживает как Web-scraping (для каталога), так и API (рекомендуется)
- Часто блокирует по IP, нужна ротация прокси
- Требует User-Agent и Referer headers
- Динамическая загрузка данных (JavaScript)
- Pagination: offset-based

**Поля для парсинга:**
- `notice_number` (номер закупки)
- `title` (название)
- `description` (описание)
- `customer_name` (заказчик)
- `start_date` (дата начала)
- `end_date` (дата окончания)
- `nmck` (начальная максимальная цена контракта)
- `procurement_method` (способ закупки)
- `status` (статус)
- `files` (прикреплённые документы)

**Особенности:**
- Anti-bot protection: Cloudflare
- Динамическая рендеринг: Да (Playwright)
- API доступен: Да
- Рекомендуемый метод: API + Web-scraper как fallback

---

### RTS Parser (rts_parser.py)

**Платформа:** РТС (Российская торговая система) - https://www.rts-tender.ru

**Характеристики:**
- Чистый REST API с хорошей документацией
- Меньше блокировок, чем EIS
- Возвращает JSON
- Pagination: page-based

**Поля для парсинга:**
- `tender_id` (идентификатор тендера)
- `name` (название)
- `summary` (краткое описание)
- `customer` (заказчик)
- `published_on` (дата публикации)
- `application_deadline` (крайний срок подачи)
- `estimated_cost` (стоимость)
- `lots` (лоты)
- `attachments` (вложения)
- `status` (статус)

**Особенности:**
- Anti-bot protection: Минимальная
- Динамическая рендеринг: Нет
- API доступен: Да (рекомендуется)
- Рекомендуемый метод: API

---

### Sberbank Parser (sberbank_parser.py)

**Платформа:** Закупки Сбербанка - https://zakupki.sber.ru

**Характеристики:**
- Корпоративная платформа Сбербанка
- Частично открытый доступ (без регистрации)
- JavaScript-based frontend
- Pagination: infinite scroll (требует JavaScript)

**Поля для парсинга:**
- `request_number` (номер запроса)
- `title` (название)
- `description` (описание)
- `budget` (бюджет)
- `deadline` (срок подачи)
- `categories` (категории)
- `terms` (условия)
- `attachments` (документы)
- `status` (статус закупки)

**Особенности:**
- Anti-bot protection: Да (требует рендеринга)
- Динамическая рендеринг: Да (обязательно Playwright)
- API доступен: Нет (только web-scraping)
- Рекомендуемый метод: Web-scraper с Playwright

---

## Интеграция в Pipeline

### Этап 1: Admin Configuration (Sprint 24)

При создании конфигурации в admin_service нужно добавить платформы:

```python
# backend/factory_parsers/admin_service/fixtures/platforms.py

PLATFORMS = [
    # Существующие платформы
    {...},
    # Новые платформы
    {
        "platform_id": "eis",
        "platform_name": "ЕИС",
        "base_url": "https://eis.zakupki.gov.ru",
        "scrape_method": "web_scraper",
        "enabled": False,  # Активируется вручную
    },
    {
        "platform_id": "rts",
        "platform_name": "РТС",
        "base_url": "https://www.rts-tender.ru",
        "scrape_method": "api",
        "enabled": False,
    },
    {
        "platform_id": "sberbank",
        "platform_name": "Закупки Сбербанка",
        "base_url": "https://zakupki.sber.ru",
        "scrape_method": "web_scraper",
        "enabled": False,
    },
]
```

### Этап 2: Spider Implementation (Sprint 41+)

Реализовать каждый парсер как отдельный Spider, следуя базовым интерфейсам.

### Этап 3: Testing & Validation (Sprint 41+)

Для каждого парсера:
- Unit-тесты на парсинг полей
- Integration-тесты на реальные запросы (в sandboxed окружении)
- Валидация схемы выходных данных

### Этап 4: Deployment (Sprint 41+)

- Включить парсер в конфигурацию через admin_service
- Запустить в режиме тестирования (10-20 запросов)
- Мониторить логи и метрики
- Если OK → запустить в production

---

## Требования к коду

### Структура класса Spider

```python
from scrapy import Spider
from typing import Generator, Dict, Any
from backend.factory_parsers.shared.logger import setup_logging
from backend.factory_parsers.shared.metrics import track_http_request

class EISSpider(Spider):
    """Spider для парсинга ЕИС (Единая информационная система)"""
    
    name = "eis_parser"
    platform_id = "eis"
    allowed_domains = ["eis.zakupki.gov.ru"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = setup_logging(
            service="web_scraper_service",
            worker="eis_spider"
        )
    
    def start_requests(self) -> Generator:
        """Генерирует начальные запросы"""
        # Реализация
        pass
    
    def parse_list(self, response) -> Generator[Dict[str, Any], None, None]:
        """Парсит список тендеров"""
        # Реализация
        pass
    
    def parse_detail(self, response) -> Dict[str, Any]:
        """Парсит детали тендера"""
        # Реализация
        pass
```

### Требования к логированию

- Все HTTP-запросы должны логироваться с полями: `platform_id`, `http_status`, `duration_ms`, `proxy_id`
- Ошибки парсинга: `error_code`, `error_message`, `tender_id`
- Успешные парсы: `tender_id`, `title`, `duration_ms`

### Требования к обработке ошибок

- Все исключения должны быть перехвачены и залогированы
- Использовать retry-механизм для временных ошибок (429, 503, 504)
- Для постоянных ошибок (403, 404): пропускать и логировать как warning
- Для неизвестных ошибок: логировать как error и отправить alert

---

## Конфликты и как их избежать

### 1. Конфликт имён классов

**Проблема:** Если парсеры уже используют классы с тем же именем в основном кодовой базе.

**Решение:** Используйте полные пути импорта и не переопределяйте существующие классы.

```python
# ✅ Правильно
from backend.factory_parsers.web_scraper_service.spiders.base_spider import BaseSpider

class EISSpider(BaseSpider):
    pass

# ❌ Неправильно
from base_spider import BaseSpider  # Неоднозначный импорт
```

### 2. Конфликт конфигурации

**Проблема:** Новые парсеры могут перезаписать конфигурацию существующих.

**Решение:** Использовать ID платформы как уникальный ключ и проверять дубликаты перед добавлением.

```python
# backend/factory_parsers/admin_service/platforms.py

def add_platform(platform_config: Dict) -> None:
    platform_id = platform_config["platform_id"]
    if Platform.query.filter_by(platform_id=platform_id).first():
        raise ValueError(f"Platform {platform_id} already exists")
    # Добавить платформу
```

### 3. Конфликт метрик

**Проблема:** Метрики для новых парсеров могут перекрыть существующие.

**Решение:** Всегда использовать `platform_id` как label в метриках.

```python
# ✅ Правильно
from prometheus_client import Counter

http_requests = Counter(
    'factory_parsers_http_requests_total',
    'Total HTTP requests',
    ['platform_id', 'status_code']
)

http_requests.labels(platform_id="eis", status_code=200).inc()
http_requests.labels(platform_id="rts", status_code=200).inc()
```

### 4. Конфликт логирования

**Проблема:** Логи от разных парсеров могут перемешаться.

**Решение:** Всегда передавайте `worker` и `platform_id` в logger.

```python
# ✅ Правильно
logger = setup_logging(
    service="web_scraper_service",
    worker="eis_spider"
)

logger.info(
    "tender_parsed",
    platform_id="eis",
    tender_id=tender_id,
    event_type="success"
)
```

---

## Checklist перед интеграцией нового парсера

- [ ] Spider класс создан и наследуется от BaseSpider
- [ ] Все поля парсера отображены в `FieldMapping`
- [ ] Platform конфигурация добавлена в admin_service
- [ ] Логирование интегрировано с `shared/logger.py`
- [ ] Метрики экспортируются в `shared/metrics.py`
- [ ] Unit-тесты написаны и проходят
- [ ] Integration-тесты написаны и проходят
- [ ] Документация обновлена (README, spec)
- [ ] Code review пройден
- [ ] Запущено в staging окружении
- [ ] Запущено в production с мониторингом

---

## Ссылки

- **EIS API docs:** https://eis.zakupki.gov.ru/api/
- **RTS API docs:** https://www.rts-tender.ru/api-docs
- **Sberbank закупки:** https://zakupki.sber.ru
- **Логирование:** `backend/factory_parsers/LOGGING_MONITORING.md`
- **Спринты:** `backend/factory_parsers/SPRINTS.md`
- **Спецификация:** `backend/factory_parsers/specs/00_TECHNICAL_SPECIFICATIONS.md`
