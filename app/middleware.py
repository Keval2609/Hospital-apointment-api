"""
HTTP middleware stack.

- **RequestLoggingMiddleware** – logs every request with method, path, status
  code, and round-trip duration.
- **CorrelationIdMiddleware** – ensures every request/response carries a unique
  ``X-Request-ID`` header for distributed tracing.
- ``register_middleware`` wires everything (including CORS) onto the app.
"""

import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger("middleware")
settings = get_settings()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log method, path, status, and latency for every HTTP request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Propagate or generate an ``X-Request-ID`` header."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def register_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI *app* instance."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
