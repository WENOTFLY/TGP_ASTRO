from importlib import reload
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import app.api.main as main

client = TestClient(main.app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tg_webhook() -> None:
    response = client.post(
        "/tg/webhook",
        json={
            "update_id": 1,
            "message": {
                "message_id": 1,
                "date": 0,
                "chat": {"id": 1, "type": "private"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_TOKEN", "42:TESTTOKEN")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "https://example.com")
    reload(main)

    assert main.bot is not None
    main.bot.set_webhook = AsyncMock()
    main.dp.feed_update = AsyncMock()

    app = main.create_app()

    with TestClient(app) as test_client:
        test_client.post(
            "/tg/webhook",
            json={
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                },
            },
        )

    main.bot.set_webhook.assert_called_once_with(
        "https://example.com", allowed_updates=main.ALLOWED_UPDATES
    )
    main.dp.feed_update.assert_called_once()
