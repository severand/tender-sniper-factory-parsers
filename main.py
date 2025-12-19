"""FastAPI application entry point with comprehensive OpenAPI documentation and monitoring"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import PlainTextResponse

from shared.config import get_settings
from shared.logger import logger
from admin_service.routes import router as admin_router
from web_scraper_service.routes import router as scraper_router
#from normalizer_service.routes import router as normalizer_router
#from search_service.routes import router as search_router
#from analytics_service.routes import router as analytics_router
#from monitoring.routes import router as monitoring_router

settings = get_settings()

app = FastAPI(
    title="Tender Sniper - Factory Parsers API",
    description="""Unified tender parsing system with administration, web scraping, 
    data normalization, full-text search, analytics, and monitoring capabilities.
    
    ## Key Features
    
    - **Admin Service**: Manage tender platforms and search rules
    - **Web Scraper**: Static HTML and JavaScript-rendered content extraction
    - **Data Normalizer**: Text extraction and field standardization
    - **Search Engine**: Full-text search with Elasticsearch
    - **Analytics**: System metrics and tender data analysis
    - **Monitoring**: Prometheus metrics and health checks
    
    ## Quick Start
    
    1. Create a platform via `/admin/platforms`
    2. Add search rules via `/admin/platforms/{id}/search-rules`
    3. Run scrapers via `/scrapers/run`
    4. Search normalized tenders via `/search/query`
    5. View analytics via `/analytics/overview`
    
    ## Monitoring
    
    - Health checks: `/monitoring/health`
    - Prometheus metrics: `/monitoring/metrics`
    - Grafana dashboards: http://localhost:3000
    
    ## Architecture
    
    ```
    Admin → Scheduler → Scraper(Static+Dynamic) → Normalizer → Search Engine → Analytics
                                                                                  ↓
                                                                            Monitoring
    ```
    
    ## API Endpoints by Service
    
    - **Admin**: Platform and search rule management
    - **Scrapers**: Web scraping orchestration
    - **Normalizers**: Normalized tender data access
    - **Search**: Full-text search and filtering
    - **Analytics**: System metrics and reports
    - **Monitoring**: Health checks and Prometheus metrics
    """,
    version="1.0.0",
    debug=settings.debug,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with tags for organization
app.include_router(
    admin_router,
    tags=["admin"],
)
app.include_router(
    scraper_router,
    tags=["scrapers"],
)
#app.include_router(
    #normalizer_router,
    #tags=["normalizers"],
#)
#app.include_router(
   # search_router,
   # tags=["search"],
#)
#app.include_router(
    #analytics_router,
    #tags=["analytics"],
#)
#app.include_router(
    #monitoring_router,
    #tags=["monitoring"],
#)


@app.get("/")
def read_root():
    """Root endpoint with system information"""
    return {
        "name": "Tender Sniper - Factory Parsers",
        "version": "1.0.0",
        "status": "operational",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "health_url": "/health",
        "metrics_url": "/metrics",
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


def custom_openapi():
    """Generate custom OpenAPI schema with additional documentation"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Tender Sniper API",
        version="1.0.0",
        description="Unified tender parsing and search system",
        routes=app.routes,
    )
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
        {
            "url": "https://api.tender-sniper.com",
            "description": "Production server",
        },
    ]
    
    # Add info
    openapi_schema["info"]["contact"] = {
        "name": "Tender Sniper Support",
        "url": "https://tender-sniper.com",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
async def startup_event():
    """Application startup handler"""
    
    # Создаём таблицы БД при старте (для SQLAlchemy)
    from shared.database import engine, Base
    from admin_service.models import Platform, SearchRule, FieldMapping
    
    # Импортируем модели, чтобы они зарегистрировались в Base.metadata
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database tables created successfully")
    logger.info("Tender Sniper application started")
    logger.info("API documentation available at /docs")
    logger.info("Monitoring dashboard available at http://localhost:3000")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("Tender Sniper application stopped")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )