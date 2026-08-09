from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from bac_generator.core.exceptions import (
    CodeCompilationError,
    ExerciseGenerationError,
    ExerciseValidationError,
    LLMResponseError,
    RateLimitExceededError,
    SolutionLockedError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ExerciseValidationError)
    async def exercise_validation_exception_handler(
        _request: Request,
        exc: ExerciseValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "exercise_validation_error",
                "detail": str(exc),
            },
        )

    @app.exception_handler(CodeCompilationError)
    async def code_compilation_exception_handler(
        _request: Request,
        exc: CodeCompilationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "code_compilation_error",
                "detail": str(exc),
            },
        )

    @app.exception_handler(LLMResponseError)
    async def llm_response_exception_handler(
        _request: Request,
        exc: LLMResponseError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={
                "error": "llm_response_error",
                "detail": str(exc),
            },
        )

    @app.exception_handler(ExerciseGenerationError)
    async def exercise_generation_exception_handler(
        _request: Request,
        exc: ExerciseGenerationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": "exercise_generation_error",
                "detail": str(exc),
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
                "detail": str(exc),
            },
        )

    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_exceeded_exception_handler(
        _request: Request,
        exc: RateLimitExceededError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "detail": str(exc),
            },
        )