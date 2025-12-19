"""Logging configuration (Sprint 37)"""

import os
from factory_parsers.shared.logging_service import LoggingService


def setup_logging():
    """Initialize logging system"""
    
    service_name = os.getenv('SERVICE_NAME', 'tender-sniper')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', '/var/log/tender-sniper/app.log')
    enable_console = os.getenv('LOG_CONSOLE', 'true').lower() == 'true'
    enable_file = os.getenv('LOG_FILE_ENABLED', 'true').lower() == 'true'
    
    LoggingService.configure(
        service_name=service_name,
        log_level=log_level,
        log_file=log_file if enable_file else None,
        enable_console=enable_console,
        enable_file=enable_file,
    )
    
    # Get root logger
    logger = LoggingService.get_logger(service_name)
    logger.info(f"Logging initialized: level={log_level}, console={enable_console}, file={enable_file}")
    
    return logger
