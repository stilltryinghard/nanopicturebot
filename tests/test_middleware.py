from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch


def _make_message(user_id: int, text: str = "/start"):
    user = MagicMock()
    user.id = user_id
    user.username = "testuser"
    user.full_name = "Test User"

    message = AsyncMock()
    message.from_user = user
    message.text = text
    message.answer = AsyncMock()
    return message


def _make_callback(user_id: int):
    user = MagicMock()
    user.id = user_id

    callback = AsyncMock()
    callback.from_user = user
    callback.answer = AsyncMock()
    return callback


class TestAuthMiddleware:
    async def test_new_user_is_created(self, db_session):
        from bot.middlewares.auth import AuthMiddleware

        middleware = AuthMiddleware()
        handler = AsyncMock(return_value=None)
        message = _make_message(user_id=5001)

        with patch("bot.middlewares.auth.async_session_maker") as mock_sm:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=db_session)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_sm.return_value = mock_ctx

            with patch("bot.middlewares.auth.settings") as mock_settings:
                mock_settings.OWNER_ID = 999999
                mock_settings.REDIS_URL = "redis://localhost"

                with patch("bot.middlewares.auth.UserRepository") as MockRepo:
                    mock_repo = AsyncMock()
                    mock_repo.get_or_create = AsyncMock(
                        return_value=(MagicMock(is_blocked=False), True)
                    )
                    MockRepo.return_value = mock_repo

                    data = {"event_update": MagicMock()}
                    await middleware(handler, message, data)

                    mock_repo.get_or_create.assert_called_once()

    async def test_blocked_user_is_rejected(self):
        from bot.middlewares.auth import AuthMiddleware

        middleware = AuthMiddleware()
        handler = AsyncMock()
        message = _make_message(user_id=5002)

        with patch("bot.middlewares.auth.async_session_maker") as mock_sm:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_sm.return_value = mock_ctx

            with patch("bot.middlewares.auth.settings") as mock_settings:
                mock_settings.OWNER_ID = 999999
                mock_settings.REDIS_URL = "redis://localhost"

                with patch("bot.middlewares.auth.UserRepository") as MockRepo:
                    blocked_user = MagicMock()
                    blocked_user.is_blocked = True
                    mock_repo = AsyncMock()
                    mock_repo.get_or_create = AsyncMock(
                        return_value=(blocked_user, False)
                    )
                    MockRepo.return_value = mock_repo

                    data = {"event_update": MagicMock()}
                    result = await middleware(handler, message, data)

                    # Handler не должен был вызваться
                    handler.assert_not_called()
                    assert result is None

    async def test_maintenance_mode_blocks_non_owner(self):
        from bot.middlewares.auth import AuthMiddleware
        import fakeredis.aioredis

        middleware = AuthMiddleware()
        handler = AsyncMock()
        message = _make_message(user_id=5003)

        fake_redis = fakeredis.aioredis.FakeRedis()
        await fake_redis.set("maintenance_mode", "1")

        with patch("bot.middlewares.auth.settings") as mock_settings:
            mock_settings.OWNER_ID = 999999
            mock_settings.REDIS_URL = "redis://localhost"

            # aioredis импортируется внутри функции — патчим на уровне пакета
            with patch("redis.asyncio.from_url", return_value=fake_redis):
                data = {"event_update": MagicMock()}
                result = await middleware(handler, message, data)

        # Главное: хэндлер не вызван — пользователь заблокирован режимом обслуживания
        handler.assert_not_called()
        assert result is None

    async def test_maintenance_mode_allows_owner(self):
        from bot.middlewares.auth import AuthMiddleware

        middleware = AuthMiddleware()
        handler = AsyncMock(return_value=None)
        owner_id = 999999
        message = _make_message(user_id=owner_id)

        with patch("bot.middlewares.auth.settings") as mock_settings:
            mock_settings.OWNER_ID = owner_id
            mock_settings.REDIS_URL = "redis://localhost"

            with patch("bot.middlewares.auth.async_session_maker") as mock_sm:
                mock_ctx = MagicMock()
                mock_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
                mock_ctx.__aexit__ = AsyncMock(return_value=False)
                mock_sm.return_value = mock_ctx

                with patch("bot.middlewares.auth.UserRepository") as MockRepo:
                    mock_repo = AsyncMock()
                    mock_repo.get_or_create = AsyncMock(
                        return_value=(MagicMock(is_blocked=False), False)
                    )
                    MockRepo.return_value = mock_repo

                    data = {"event_update": MagicMock()}
                    await middleware(handler, message, data)

                    # Владелец должен пройти даже в режиме обслуживания
                    handler.assert_called_once()


class TestThrottlingMiddleware:
    async def test_allows_first_request(self):
        from bot.middlewares.throttling import ThrottlingMiddleware

        middleware = ThrottlingMiddleware(rate_limit=1.0)
        handler = AsyncMock(return_value="ok")
        message = _make_message(user_id=6001)

        result = await middleware(handler, message, {})
        assert result == "ok"
        handler.assert_called_once()

    async def test_blocks_rapid_requests(self):
        from bot.middlewares.throttling import ThrottlingMiddleware

        middleware = ThrottlingMiddleware(rate_limit=10.0)  # 10 секунд между запросами
        handler = AsyncMock(return_value="ok")
        message = _make_message(user_id=6002)

        # Первый запрос — проходит
        await middleware(handler, message, {})
        # Второй сразу — должен быть заблокирован
        await middleware(handler, message, {})

        assert handler.call_count == 1
