import logging
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as firebase_auth

from bac_generator.core.logging_config import log_event

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    uid: str
    email: str | None = None


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
        )

    try:
        decoded_token = firebase_auth.verify_id_token(
            credentials.credentials
        )
    except Exception as exc:
        log_event(
            logger,
            "authentication_failed",
            level=logging.WARNING,
            exception_type=type(exc).__name__,
            safe_error_message="Firebase token verification failed.",
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc

    uid = decoded_token.get("uid")

    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token does not contain a valid user id.",
        )

    return CurrentUser(
        uid=uid,
        email=decoded_token.get("email"),
    )
