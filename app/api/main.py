from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

from aiogram import Bot
from aiogram.types import Update
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bot import dp  # type: ignore[import]
from app.config import get_settings
from app.core.assets import ASSET_CACHE
from app.core.telemetry import TelemetryEvent
from app.db.models import Event, User
from app.db.session import get_session

ALLOWED_UPDATES = [
    "message",
    "callback_query",
    "my_chat_member",
    "pre_checkout_query",
]

router = APIRouter()
admin_router = APIRouter(prefix="/admin")

settings = get_settings()
bot: Bot | None = Bot(settings.telegram_token) if settings.telegram_token else None


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/tg/webhook")
async def tg_webhook(update: Update) -> dict[str, str]:
    if bot is not None:
        await dp.feed_update(bot, update)
    return {"status": "ok"}


@admin_router.get("/metrics")
def admin_metrics(
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, Any]:
    now = datetime.utcnow()
    since_day = now - timedelta(days=1)
    since_month = now - timedelta(days=30)
    events = session.execute(
        select(Event.user_id, Event.event, Event.props_json, Event.ts).where(
            Event.ts >= since_month
        )
    ).all()

    dau_users: set[int] = set()
    mau_users: set[int] = set()
    start_count = writer_ok_count = 0
    durations: list[float] = []
    verifier_ok = verifier_fail = 0

    for user_id, event, props, ts in events:
        if user_id is not None:
            if ts >= since_day:
                dau_users.add(user_id)
            mau_users.add(user_id)
        if event == TelemetryEvent.START.value:
            start_count += 1
        elif event == TelemetryEvent.WRITER_OK.value:
            writer_ok_count += 1
            if isinstance(props, dict):
                dur = props.get("duration_ms")
                if isinstance(dur, (int, float)):
                    durations.append(float(dur))
        elif event == TelemetryEvent.VERIFIER_OK.value:
            verifier_ok += 1
        elif event == TelemetryEvent.VERIFIER_FAIL.value:
            verifier_fail += 1

    conversion = writer_ok_count / start_count if start_count else 0.0
    avg_duration = sum(durations) / len(durations) if durations else 0.0
    verifier_fail_pct = (
        verifier_fail / (verifier_fail + verifier_ok)
        if (verifier_fail + verifier_ok)
        else 0.0
    )

    return {
        "dau": len(dau_users),
        "mau": len(mau_users),
        "conversion_start_to_writer": conversion,
        "avg_generation_ms": avg_duration,
        "verifier_fail_pct": verifier_fail_pct,
    }


@admin_router.get("/decks")
def admin_decks() -> list[dict[str, Any]]:
    return [
        {"id": deck_id, "type": data["type"], "name": data["name"]}
        for deck_id, data in ASSET_CACHE.items()
    ]


class BroadcastRequest(BaseModel):
    message: str


@admin_router.post("/broadcast")
async def admin_broadcast(
    payload: BroadcastRequest,
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, int]:
    if bot is None:
        raise HTTPException(status_code=503, detail="Bot is not configured")
    tg_ids: Iterable[int] = (row[0] for row in session.execute(select(User.tg_id)))
    sent = 0
    for tg_id in tg_ids:
        try:
            await bot.send_message(tg_id, payload.message)
            sent += 1
        except Exception:
            continue
    return {"sent": sent}


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.include_router(admin_router)

    @app.on_event("startup")
    async def on_startup() -> None:
        if bot is not None:
            webhook_url = settings.telegram_webhook_url
            if webhook_url:
                await bot.set_webhook(webhook_url, allowed_updates=ALLOWED_UPDATES)

    return app


app = create_app()
