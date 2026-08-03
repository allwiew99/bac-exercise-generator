from fastapi.testclient import TestClient

from bac_generator.main import app

client = TestClient(app)


def test_generate_exercise_returns_valid_response() -> None:
    response = client.post(
        "/exercises/generate",
        json={
            "topic": "vectori",
            "difficulty": "medium",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["topic"] == "vectori"
    assert body["difficulty"] == "medium"
    assert body["statement"]
    assert body["solution"]
    assert body["explanation"]