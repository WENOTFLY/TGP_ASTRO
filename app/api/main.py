from __future__ import annotations

import os

from aiogram import Bot
from aiogram.types import Update
from fastapi import APIRouter, FastAPI

from app.bot import dp

ALLOWED_UPDATES = [
    "message",
    "callback_query",
    "my_chat_member",
    "pre_checkout_query",
]

router = APIRouter()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot: Bot | None = Bot(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/tg/webhook")
async def tg_webhook(update: Update) -> dict[str, str]:
    if bot is not None:
        await dp.feed_update(bot, update)
    return {"status": "ok"}


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.on_event("startup")
    async def on_startup() -> None:
        if bot is not None:
            webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
            if webhook_url:
                await bot.set_webhook(webhook_url, allowed_updates=ALLOWED_UPDATES)

    return app


app = create_app()
