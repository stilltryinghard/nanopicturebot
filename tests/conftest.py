import os
import sys
from unittest.mock import MagicMock

# asyncpg не установлен локально — мокаем чтобы db/session.py не падал при импорте
sys.modules.setdefault("asyncpg", MagicMock())

# Устанавливаем env vars ДО импорта любых модулей проекта
os.environ.setdefault("BOT_TOKEN", "123456789:AAAaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
os.environ.setdefault("BOT_USERNAME", "test_bot")
os.environ.setdefault("OWNER_ID", "8159682416")
os.environ.setdefault("ADMIN_IDS", "[8159682416]")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("YUKASSA_SHOP_ID", "test_shop")
os.environ.setdefault("YUKASSA_SECRET_KEY", "test_secret")
os.environ.setdefault("WAVESPEED_API_KEY", "test_wavespeed_key")
os.environ.setdefault("MIDJOURNEY_API_KEY", "test_mj_key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession  # noqa: E402
from db.base import Base  # noqa: E402
from db.models import *  # noqa: F401, F403, E402 — нужно чтобы все модели зарегистрировались


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def user(db_session):
    from db.repositories.user import UserRepository

    repo = UserRepository(db_session)
    return await repo.create(user_id=111, username="testuser", full_name="Test User")
