"""Loki logging handler for centralized log aggregation (Sprint 38)"""

import logging
import json
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from urllib.parse import urljoin


class LokiHandler(logging.Handler):
    """Send logs to Grafana Loki"""
    
    def __init__(self, 
                 url: str,
                 job_name: str,
                 labels: Optional[Dict[str, str]] = None,
                 batch_size: int = 100):
        """Initialize Loki handler
        
        Args:
            url: Loki API URL (e.g., http://localhost:3100)
            job_name: Job name label
            labels: Additional labels
            batch_size: Batch size for sending
        """
        super().__init__()
        self.url = url
        self.job_name = job_name
        self.labels = labels or {}
        self.labels['job'] = job_name
        self.batch_size = batch_size
        self.batch = []
    
    def emit(self, record: logging.LogRecord):
        """Send log record to Loki"""
        try:
            # Format log entry
            timestamp_ns = int(record.created * 1e9)
            message = self.format(record)
            
            # Add to batch
            self.batch.append({
                'ts': timestamp_ns,
                'line': message,
            })
            
            # Send if batch full
            if len(self.batch) >= self.batch_size:
                self.flush()
        except Exception:
            self.handleError(record)
    
    def flush(self):
        """Send batch to Loki"""
        if not self.batch:
            return
        
        try:
            # Build Loki request
            streams = [{
                'stream': self.labels,
                'values': self.batch,
            }]
            
            payload = {'streams': streams}
            
            # Send to Loki
            response = requests.post(
                urljoin(self.url, '/loki/api/v1/push'),
                json=payload,
                timeout=5,
            )
            
            if response.status_code == 204:
                self.batch.clear()
            else:
                # Log error but don't fail
                logging.warning(f"Loki push failed: {response.status_code}")
        except Exception as e:
            logging.warning(f"Failed to send logs to Loki: {e}")
    
    def close(self):
        """Flush before closing"""
        self.flush()
        super().close()


class LokiLogstashFormatter(logging.Formatter):
    """Format logs for Loki as logstash JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': record.name.split('.')[0] if '.' in record.name else record.name,
        }
        
        # Add exception info
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
            }
        
        # Add custom attributes
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'getMessage']:
                log_data[key] = value
        
        return json.dumps(log_data)
