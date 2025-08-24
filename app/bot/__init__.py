from __future__ import annotations

from pathlib import Path
from subprocess import run

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware

from .handlers import router
from .middlewares import AntiFloodMiddleware, UserParallelLimitMiddleware

__all__ = ["dp", "i18n"]

# Internationalization
locales_dir = Path(__file__).parent / "locales"
for po_file in locales_dir.glob("*/LC_MESSAGES/*.po"):
    mo_file = po_file.with_suffix(".mo")
    if not mo_file.exists():
        run(["msgfmt", str(po_file), "-o", str(mo_file)], check=True)
i18n = I18n(path=locales_dir, default_locale="en", domain="bot")

# Dispatcher with FSM storage and middlewares
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

i18n_middleware = SimpleI18nMiddleware(i18n)
# Register middlewares
for m in (
    AntiFloodMiddleware(),
    UserParallelLimitMiddleware(limit=2),
    i18n_middleware,
):
    dp.update.middleware.register(m)

# Include handlers
dp.include_router(router)
