"""Request logging middleware — logs method, path, status code, and response time as JSON."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

SKIP_PATHS = {"/api/health", "/docs", "/openapi.json"}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs each HTTP request as structured JSON to stdout."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
