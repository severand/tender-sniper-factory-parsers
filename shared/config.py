"""Application configuration management"""

import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings

# Получаем путь к базовой директории (backend)
BASE_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    """Application settings"""

    # FastAPI
    fastapi_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Database - используем абсолютный путь
    database_url: str = "sqlite:///C:/Users/Vlad/PycharmProjects/tender-sniper/backend/factory_parsers.db"
    database_echo: bool = False
    sqlalchemy_pool_size: int = 5
    sqlalchemy_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # AI
    openai_api_key: str = ""
    llm_model: str = "gpt-4"
    llm_max_tokens: int = 2000

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # Logging
    log_format: str = "json"
    log_output: str = "stdout"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
