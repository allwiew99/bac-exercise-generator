import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from bac_generator.core.logging_config import log_event
from bac_generator.db.session import get_db_session

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=None)
async def readiness_check(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JSONResponse:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        log_event(
            logger,
            "readiness_failed",
            level=logging.ERROR,
            exception_type=type(exc).__name__,
            safe_error_message="A critical dependency is unavailable.",
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "detail": "A critical dependency is unavailable.",
            },
        )

    return JSONResponse(
        status_code=200,
        content={"status": "ready"},
    )
