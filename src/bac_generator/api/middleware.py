from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from bac_generator.core.request_context import (
    reset_request_id,
    set_request_id,
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(
            "X-Request-ID",
            str(uuid4()),
        )

        token = set_request_id(request_id)

        try:
            response: Response = await call_next(request)
        finally:
            reset_request_id(token)

        response.headers["X-Request-ID"] = request_id

        return response