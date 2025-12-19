"""Request tracing with unique trace IDs"""

import uuid
import contextvars

from fastapi import Request
from factory_parsers.shared.logging_service import LogContext

# Context variable for trace ID
trace_id_var = contextvars.ContextVar('trace_id', default=None)


def get_trace_id() -> str:
    """Get current trace ID"""
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str):
    """Set trace ID"""
    trace_id_var.set(trace_id)
    LogContext.set(trace_id=trace_id)


async def trace_id_middleware(request: Request, call_next):
    """FastAPI middleware for trace ID injection"""
    # Get or create trace ID
    trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))
    set_trace_id(trace_id)
    
    # Add to response headers
    response = await call_next(request)
    response.headers['X-Trace-ID'] = trace_id
    
    return response
