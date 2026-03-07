from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        referred_by: int | None = None,
    ) -> User:
        user = User(
            id=user_id,
            username=username,
            full_name=full_name,
            referred_by=referred_by,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username.lstrip("@"))
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        user_id: int,
        username: str | None,
        full_name: str,
        referred_by: int | None = None,
    ) -> tuple[User, bool]:
        user = await self.get_by_id(user_id)
        if user:
            return user, False
        user = await self.create(user_id, username, full_name, referred_by)
        return user, True

    async def update_tokens(self, user_id: int, amount: int) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.tokens += amount
            await self.session.commit()

    async def update_referral_count(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.referral_count += 1
            await self.session.commit()

    async def block(self, user_id: int, blocked: bool) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.is_blocked = blocked
            await self.session.commit()

    async def get_all(self) -> list[User]:
        result = await self.session.execute(select(User))
        return list(result.scalars().all())

    async def set_language(self, user_id: int, language: str) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.language = language
            await self.session.commit()

    async def accept_terms(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.terms_accepted = True
            await self.session.commit()

    async def get_low_balance_users(
        self, threshold: int, limit: int = 100, offset: int = 0
    ) -> list[User]:
        result = await self.session.execute(
            select(User)
            .where(User.tokens <= threshold, User.is_blocked == False)  # noqa: E712
            .order_by(User.id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
