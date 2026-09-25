import asyncio
from collections.abc import AsyncGenerator

import pytest
from fastapi.testclient import TestClient

from bac_generator.api.routes import health as health_routes
from bac_generator.core.config import settings
from bac_generator.db.session import get_db_session
from bac_generator.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


class HealthySession:
    async def execute(self, _statement: object) -> None:
        return None


class UnhealthySession:
    async def execute(self, _statement: object) -> None:
        raise RuntimeError("private database detail")


class StalledSession:
    async def execute(self, _statement: object) -> None:
        await asyncio.sleep(1)


async def healthy_session() -> AsyncGenerator[HealthySession, None]:
    yield HealthySession()


async def unhealthy_session() -> AsyncGenerator[UnhealthySession, None]:
    yield UnhealthySession()


async def stalled_session() -> AsyncGenerator[StalledSession, None]:
    yield StalledSession()


def test_ready_returns_200_when_database_is_reachable() -> None:
    app.dependency_overrides[get_db_session] = healthy_session
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_returns_safe_503_when_database_is_unreachable() -> None:
    app.dependency_overrides[get_db_session] = unhealthy_session
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "detail": "A critical dependency is unavailable.",
    }
    assert "private database detail" not in response.text


def test_ready_checks_configured_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    async def unavailable_redis() -> None:
        raise RuntimeError("private redis detail")

    monkeypatch.setattr(settings, "rate_limiter_provider", "redis")
    monkeypatch.setattr(health_routes, "_check_configured_redis", unavailable_redis)
    app.dependency_overrides[get_db_session] = healthy_session
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert "private redis detail" not in response.text


def test_ready_has_an_overall_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "readiness_timeout_seconds", 0.01)
    app.dependency_overrides[get_db_session] = stalled_session
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
