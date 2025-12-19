"""Logging configuration and utilities"""

import json
import logging
from typing import Optional


class JSONFormatter(logging.Formatter):
    """Format logs as JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str,
    level: str = "INFO",
    handler: Optional[logging.Handler] = None
) -> logging.Logger:
    """Setup logger with JSON formatter
    
    Args:
        name: Logger name
        level: Logging level (INFO, DEBUG, WARNING, ERROR)
        handler: Custom handler (optional)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create console handler if not provided
    if handler is None:
        handler = logging.StreamHandler()
    
    # Set formatter
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger(__name__)
