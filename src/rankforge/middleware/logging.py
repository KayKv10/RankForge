# src/rankforge/middleware/logging.py

"""Request/response logging middleware for RankForge API."""

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("rankforge.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses.

    Logs request method, path, and query parameters on entry.
    Logs response status code and duration on completion.
    Adds X-Request-ID header to responses for tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())[:8]

        # Record start time
        start_time = time.time()

        # Log request
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            "[%s] %s %s%s",
            request_id,
            request.method,
            request.url.path,
            f"?{request.query_params}" if request.query_params else "",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": client_host,
            },
        )

        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                "[%s] %s %s -> %d (%.2fms)",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response  # type: ignore[no-any-return]

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "[%s] %s %s -> ERROR (%.2fms): %s",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
                str(e),
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True,
            )
            raise
