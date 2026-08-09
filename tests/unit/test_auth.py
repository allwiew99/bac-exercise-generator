from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from bac_generator.api.dependencies.auth import get_current_user


@pytest.mark.asyncio
async def test_get_current_user_returns_401_without_credentials() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Missing or invalid authentication credentials."
    )


@pytest.mark.asyncio
async def test_get_current_user_returns_401_for_invalid_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_verify_id_token(token: str) -> dict[str, Any]:
        raise ValueError("Invalid token")

    monkeypatch.setattr(
        "bac_generator.api.dependencies.auth.firebase_auth.verify_id_token",
        fake_verify_id_token,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication token."


@pytest.mark.asyncio
async def test_get_current_user_returns_authenticated_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_verify_id_token(token: str) -> dict[str, Any]:
        return {
            "uid": "firebase-user-123",
            "email": "test@example.com",
        }

    monkeypatch.setattr(
        "bac_generator.api.dependencies.auth.firebase_auth.verify_id_token",
        fake_verify_id_token,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid-token",
    )

    user = await get_current_user(credentials)

    assert user.uid == "firebase-user-123"
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_returns_401_when_uid_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_verify_id_token(token: str) -> dict[str, Any]:
        return {
            "email": "test@example.com",
        }

    monkeypatch.setattr(
        "bac_generator.api.dependencies.auth.firebase_auth.verify_id_token",
        fake_verify_id_token,
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid-token-without-uid",
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Authentication token does not contain a valid user id."
    )