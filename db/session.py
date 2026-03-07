import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from core.config import settings

if os.environ.get("USE_NULL_POOL"):
    engine = create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
    )

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
