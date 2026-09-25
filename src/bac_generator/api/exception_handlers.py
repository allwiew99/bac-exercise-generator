import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bac_generator.core.exceptions import (
    CodeCompilationError,
    ExerciseGenerationError,
    ExerciseValidationError,
    LLMResponseError,
    RateLimiterUnavailableError,
    RateLimitExceededError,
    SolutionLockedError,
)
from bac_generator.core.logging_config import log_event

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ExerciseValidationError)
    async def exercise_validation_exception_handler(
        _request: Request,
        exc: ExerciseValidationError,
    ) -> JSONResponse:
        log_event(
            logger,
            "validation_failed",
            level=logging.WARNING,
            exception_type=type(exc).__name__,
            safe_error_message="Generated exercise validation failed.",
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "exercise_validation_error",
                "detail": "Generated exercise failed validation.",
            },
        )

    @app.exception_handler(CodeCompilationError)
    async def code_compilation_exception_handler(
        _request: Request,
        exc: CodeCompilationError,
    ) -> JSONResponse:
        log_event(
            logger,
            "sandbox_failed",
            level=logging.WARNING,
            exception_type=type(exc).__name__,
            safe_error_message="Generated code validation failed.",
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "code_compilation_error",
                "detail": "Generated code failed validation.",
            },
        )

    @app.exception_handler(LLMResponseError)
    async def llm_response_exception_handler(
        _request: Request,
        exc: LLMResponseError,
    ) -> JSONResponse:
        log_event(
            logger,
            "generation_failed",
            level=logging.ERROR,
            exception_type=type(exc).__name__,
            safe_error_message="Model response could not be processed.",
        )
        return JSONResponse(
            status_code=502,
            content={
                "error": "llm_response_error",
                "detail": "The generation provider returned an unusable response.",
            },
        )

    @app.exception_handler(ExerciseGenerationError)
    async def exercise_generation_exception_handler(
        _request: Request,
        exc: ExerciseGenerationError,
    ) -> JSONResponse:
        log_event(
            logger,
            "generation_failed",
            level=logging.ERROR,
            exception_type=type(exc).__name__,
            safe_error_message="Exercise generation failed.",
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "exercise_generation_error",
                "detail": "Exercise generation failed.",
            },
        )

    @app.exception_handler(SolutionLockedError)
    async def solution_locked_exception_handler(
        _request: Request,
        exc: SolutionLockedError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={
                "error": "solution_locked",
                "detail": "Submit a solution before viewing the official solution.",
            },
        )

    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_exceeded_exception_handler(
        _request: Request,
        exc: RateLimitExceededError,
    ) -> JSONResponse:
        log_event(
            logger,
            "rate_limited",
            level=logging.WARNING,
            exception_type=type(exc).__name__,
            safe_error_message="Request rate limit exceeded.",
        )
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "detail": "Too many requests. Please try again shortly.",
            },
        )

    @app.exception_handler(RateLimiterUnavailableError)
    async def rate_limiter_unavailable_exception_handler(
        _request: Request,
        exc: RateLimiterUnavailableError,
    ) -> JSONResponse:
        log_event(
            logger,
            "rate_limiter_failed_closed",
            level=logging.ERROR,
            exception_type=type(exc).__name__,
            safe_error_message="Rate limiting is temporarily unavailable.",
        )
        return JSONResponse(
            status_code=503,
            content={
                "error": "rate_limiter_unavailable",
                "detail": "Rate limiting is temporarily unavailable.",
            },
        )
