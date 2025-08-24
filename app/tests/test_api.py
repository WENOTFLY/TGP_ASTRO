from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tg_webhook() -> None:
    response = client.post("/tg/webhook", json={"message": {}})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
