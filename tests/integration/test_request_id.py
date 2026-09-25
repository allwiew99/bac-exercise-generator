from uuid import UUID

from fastapi.testclient import TestClient

from bac_generator.main import app

client = TestClient(app)


@app.get("/_test/unhandled-error", include_in_schema=False)
def unhandled_error() -> None:
    raise RuntimeError("provider-secret-value")


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


def test_unhandled_error_is_contained_and_correlated() -> None:
    response = client.get(
        "/_test/unhandled-error",
        headers={"X-Request-ID": "failure-request-123"},
    )

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "failure-request-123"
    assert response.json() == {
        "error": "internal_server_error",
        "detail": "Request processing failed.",
    }
    assert "provider-secret-value" not in response.text
