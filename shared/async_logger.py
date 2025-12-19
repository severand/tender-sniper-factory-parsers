"""Asynchronous logging queue for high-performance logging"""

import logging
import queue
import threading
from typing import Optional
from datetime import datetime


class AsyncLogHandler(logging.Handler):
    """Asynchronous log handler using queue"""
    
    def __init__(self, target_handler: logging.Handler, queue_size: int = 10000):
        super().__init__()
        self.target_handler = target_handler
        self.log_queue = queue.Queue(maxsize=queue_size)
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def emit(self, record: logging.LogRecord):
        """Queue log record"""
        try:
            self.log_queue.put_nowait(record)
        except queue.Full:
            # Drop oldest if queue full
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(record)
            except queue.Empty:
                pass
    
    def _worker(self):
        """Process log queue"""
        while True:
            try:
                record = self.log_queue.get(timeout=1)
                if record is None:  # Shutdown signal
                    break
                self.target_handler.emit(record)
            except queue.Empty:
                continue
            except Exception:
                pass
    
    def shutdown(self):
        """Shutdown async handler"""
        self.log_queue.put(None)
        self.worker_thread.join(timeout=5)


class MetricsLogger:
    """Logger for metrics and performance data"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_metric(self, name: str, value: float, tags: Optional[dict] = None):
        """Log metric"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'metric': name,
            'value': value,
        }
        if tags:
            log_data['tags'] = tags
        
        self.logger.info(f"METRIC: {log_data}")
    
    def log_event(self, event_name: str, details: Optional[dict] = None):
        """Log event"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': event_name,
        }
        if details:
            log_data['details'] = details
        
        self.logger.info(f"EVENT: {log_data}")
