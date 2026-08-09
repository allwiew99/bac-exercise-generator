from fastapi.testclient import TestClient

from bac_generator.main import app

client = TestClient(app)


def test_cors_allows_configured_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:3000"
    )


def test_cors_rejects_unconfigured_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "https://not-allowed.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert (
        "access-control-allow-origin"
        not in response.headers
    )