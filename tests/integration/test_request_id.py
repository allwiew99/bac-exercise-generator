from uuid import UUID

from fastapi.testclient import TestClient

from bac_generator.main import app

client = TestClient(app)


def test_request_id_is_preserved_when_provided() -> None:
    request_id = "test-request-123"

    response = client.get(
        "/health",
        headers={
            "X-Request-ID": request_id,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_request_id_is_generated_when_missing() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers["X-Request-ID"]

    assert request_id
    UUID(request_id)


def test_invalid_request_id_is_replaced() -> None:
    response = client.get(
        "/health",
        headers={"X-Request-ID": "attacker\nforged-log-line"},
    )

    assert response.status_code == 200
    generated_request_id = response.headers["X-Request-ID"]
    assert generated_request_id != "attacker\nforged-log-line"
    UUID(generated_request_id)


def test_oversized_request_id_is_replaced() -> None:
    response = client.get(
        "/health",
        headers={"X-Request-ID": "a" * 129},
    )

    assert response.status_code == 200
    UUID(response.headers["X-Request-ID"])
