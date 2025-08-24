from __future__ import annotations

import asyncio
from pathlib import Path

from aiogram import Bot
from alembic import command
from alembic.config import Config

from app.api.main import ALLOWED_UPDATES
from app.config import get_settings
from app.core.assets.loader import load_assets
from app.db.session import SessionLocal


def run_migrations() -> None:
    settings = get_settings()
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


def ingest_assets() -> None:
    assets_root = Path("assets")
    if not assets_root.exists():
        return
    with SessionLocal() as session:
        load_assets(assets_root, session)


async def register_webhook() -> None:
    settings = get_settings()
    token = settings.telegram_token
    url = settings.telegram_webhook_url
    if not token or not url:
        return
    bot = Bot(token)
    await bot.set_webhook(url, allowed_updates=ALLOWED_UPDATES)


def main() -> None:
    run_migrations()
    ingest_assets()
    asyncio.run(register_webhook())


if __name__ == "__main__":
    main()
