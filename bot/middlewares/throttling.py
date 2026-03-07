from __future__ import annotations
from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
import time


class ThrottlingMiddleware(BaseMiddleware):
    """
    Антиспам middleware.
    Хранит время последнего запроса каждого юзера в памяти.
    Если запросы идут слишком часто — игнорируем.
    """

    def __init__(self, rate_limit: float = 0.5):
        """
        rate_limit — минимальный интервал между запросами в секундах.
        0.5 = не чаще раза в полсекунды.
        """
        self.rate_limit = rate_limit
        self._last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = None
        if hasattr(event, "from_user"):
            from_user = event.from_user  # type: ignore

        if not from_user:
            return await handler(event, data)

        user_id = from_user.id
        now = time.monotonic()
        last = self._last_call.get(user_id, 0)

        if now - last < self.rate_limit:
            # Слишком часто — игнорируем
            return None

        self._last_call[user_id] = now
        return await handler(event, data)
