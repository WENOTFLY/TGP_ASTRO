from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject


class AntiFloodMiddleware(BaseMiddleware):
    """Simple anti-flood middleware limiting messages rate."""

    def __init__(self, rate: float = 1.0) -> None:
        super().__init__()
        self.rate = rate
        self._last_message: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        from_user = data.get("event_from_user")
        if from_user:
            now = time.monotonic()
            last_time = self._last_message.get(from_user.id, 0.0)
            if now - last_time < self.rate:
                return None
            self._last_message[from_user.id] = now
        return await handler(event, data)


class UserParallelLimitMiddleware(BaseMiddleware):
    """Limit number of parallel tasks per user."""

    def __init__(self, limit: int = 2) -> None:
        super().__init__()
        self.limit = limit
        self._locks: Dict[int, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(limit)
        )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        from_user = data.get("event_from_user")
        if from_user:
            lock = self._locks[from_user.id]
            async with lock:
                return await handler(event, data)
        return await handler(event, data)
