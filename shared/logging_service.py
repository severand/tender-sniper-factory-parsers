"""Complete logging service foundation (Sprint 37)"""

import logging
import json
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger


class LogContext:
    """Thread-local log context"""
    _context = {}
    
    @classmethod
    def set(cls, **kwargs):
        """Set context variables"""
        cls._context.update(kwargs)
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get context variable"""
        return cls._context.get(key, default)
    
    @classmethod
    def clear(cls):
        """Clear context"""
        cls._context.clear()


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Production-grade JSON formatter with context"""
    
    def add_fields(self, log_record: Dict, record: logging.LogRecord, message_dict: Dict):
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Core fields
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['service'] = record.name.split('.')[0] if '.' in record.name else record.name
        
        # Add context
        if LogContext._context:
            log_record['context'] = LogContext._context.copy()
        
        # Exception info
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
            }
        
        # Performance metrics
        if hasattr(record, 'duration_ms'):
            log_record['duration_ms'] = record.duration_ms
        if hasattr(record, 'items_processed'):
            log_record['items_processed'] = record.items_processed


class LoggingService:
    """Centralized logging service"""
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def configure(cls, 
                  service_name: str,
                  log_level: str = "INFO",
                  log_file: Optional[str] = None,
                  enable_console: bool = True,
                  enable_file: bool = True):
        """Configure logging system
        
        Args:
            service_name: Service name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for logging
            enable_console: Log to console
            enable_file: Log to file
        """
        if cls._configured:
            return
        
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        formatter = StructuredFormatter(
            '%(timestamp)s %(level)s %(service)s %(logger)s %(message)s'
        )
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if enable_file and log_file:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=100 * 1024 * 1024,  # 100MB
                backupCount=10
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create logger"""
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
        return cls._loggers[name]
    
    @classmethod
    def set_context(cls, **kwargs):
        """Set logging context"""
        LogContext.set(**kwargs)
    
    @classmethod
    def clear_context(cls):
        """Clear logging context"""
        LogContext.clear()


def log_performance(func):
    """Decorator for performance logging"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start) * 1000
            
            # Add performance metrics to log record
            record = logging.LogRecord(
                name=logger.name,
                level=logging.INFO,
                pathname='',
                lineno=0,
                msg=f"{func.__name__} completed",
                args=(),
                exc_info=None
            )
            record.duration_ms = duration_ms
            logger.handle(record)
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.exception(f"{func.__name__} failed in {duration_ms:.2f}ms")
            raise
    
    return wrapper
