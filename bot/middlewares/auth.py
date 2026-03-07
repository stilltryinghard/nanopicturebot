from __future__ import annotations
from typing import Any, Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from db.session import async_session_maker
from db.repositories.user import UserRepository
from core.config import settings
from core.i18n import t
from core.logger import logger

# Callback-данные, разрешённые до завершения онбординга
_ONBOARDING_CALLBACKS = {"accept_terms", "decline_terms", "language_select"}


def _is_onboarding_allowed(event: TelegramObject) -> bool:
    """True если апдейт относится к /start или шагам онбординга."""
    if isinstance(event, Message):
        return bool(event.text and event.text.startswith("/start"))
    if isinstance(event, CallbackQuery):
        data = event.data or ""
        return (
            data.startswith("lang:")
            or data.startswith("read_doc:")
            or data in _ONBOARDING_CALLBACKS
        )
    return False


class AuthMiddleware(BaseMiddleware):
    """
    Middleware авторизации.
    При каждом запросе:
    1. Достаём юзера из БД или создаём нового
    2. Если заблокирован — не пускаем
    3. Кладём юзера в data — чтобы handler мог получить его без запроса в БД
    """

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

        # Режим обслуживания — пропускаем только владельца
        if from_user.id != settings.OWNER_ID:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.REDIS_URL)
            is_maintenance = await r.get("maintenance_mode")
            await r.aclose()
            if is_maintenance:
                if isinstance(event, Message):
                    await event.answer(
                        "🔧 <b>Бот на техническом обслуживании.</b>\n\nСкоро вернёмся!",
                        parse_mode="HTML",
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "🔧 Бот на техническом обслуживании", show_alert=True
                    )
                return None

        # Проверяем реферала из data если есть
        referred_by = data.get("referred_by")

        async with async_session_maker() as session:
            repo = UserRepository(session)
            user, is_new = await repo.get_or_create(
                user_id=from_user.id,
                username=from_user.username,
                full_name=from_user.full_name,
                referred_by=referred_by,
            )

            if is_new:
                logger.info(f"Новый юзер: {from_user.id} (@{from_user.username})")

            # Заблокированных не пускаем
            if user.is_blocked:
                return None

            # Онбординг не пройден — пускаем только в /start и onboarding callbacks
            if not user.terms_accepted and not _is_onboarding_allowed(event):
                lang = user.language or "ru"
                msg = t("not_onboarded", lang)
                if isinstance(event, Message):
                    await event.answer(msg)
                elif isinstance(event, CallbackQuery):
                    await event.answer(msg, show_alert=True)
                return None

            # Кладём юзера в data — handler получит его через аргумент
            data["user"] = user

        return await handler(event, data)
