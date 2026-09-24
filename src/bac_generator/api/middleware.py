import logging
import re
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from bac_generator.core.logging_config import log_event
from bac_generator.core.request_context import (
    reset_request_id,
    set_request_id,
)

logger = logging.getLogger(__name__)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _request_id_from_header(value: str | None) -> str:
    if value is not None and REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _request_id_from_header(
            request.headers.get("X-Request-ID")
        )

        token = set_request_id(request_id)
        started_at = time.perf_counter()
        log_event(
            logger,
            "request_received",
            method=request.method,
            path=request.url.path,
        )

        try:
            response: Response = await call_next(request)
        except Exception:
            log_event(
                logger,
                "request_failed",
                level=logging.ERROR,
                method=request.method,
                path=request.url.path,
                total_latency_ms=round(
                    (time.perf_counter() - started_at) * 1000,
                    2,
                ),
                exception_type="unhandled_exception",
                safe_error_message="Request processing failed.",
            )
            reset_request_id(token)
            raise

        log_event(
            logger,
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            total_latency_ms=round(
                (time.perf_counter() - started_at) * 1000,
                2,
            ),
        )
        reset_request_id(token)

        response.headers["X-Request-ID"] = request_id

        return response
