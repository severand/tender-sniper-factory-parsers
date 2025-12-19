"""Structured logging configuration (Sprint 35)"""

import logging
import json
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with required fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add required fields
        log_record['service'] = record.name.split('.')[0]
        log_record['timestamp'] = self.formatTime(record, self.datefmt)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name


def setup_logging(service_name: str, log_level: str = "INFO"):
    """Setup structured logging
    
    Args:
        service_name: Service name
        log_level: Log level
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Console handler with JSON formatter
    console_handler = logging.StreamHandler()
    formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(service)s %(logger)s %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
