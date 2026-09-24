from collections.abc import AsyncGenerator

from fastapi.testclient import TestClient

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


async def healthy_session() -> AsyncGenerator[HealthySession, None]:
    yield HealthySession()


async def unhealthy_session() -> AsyncGenerator[UnhealthySession, None]:
    yield UnhealthySession()


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
