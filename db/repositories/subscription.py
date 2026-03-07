from __future__ import annotations
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.subscription import Subscription


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: int) -> Subscription | None:
        result = await self.session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, user_id: int, plan: str, expires_at: datetime
    ) -> Subscription:
        subscription = Subscription(
            user_id=user_id,
            plan=plan,
            expires_at=expires_at,
            is_active=True,
        )
        self.session.add(subscription)
        await self.session.commit()
        await self.session.refresh(subscription)
        return subscription

    async def upsert(
        self, user_id: int, plan: str, expires_at: datetime
    ) -> Subscription:
        subscription = await self.get_by_user_id(user_id)
        if subscription:
            subscription.plan = plan
            subscription.expires_at = expires_at
            subscription.is_active = True
            await self.session.commit()
            await self.session.refresh(subscription)
            return subscription
        return await self.create(user_id=user_id, plan=plan, expires_at=expires_at)

    async def deactivate(self, user_id: int) -> None:
        subscription = await self.get_by_user_id(user_id)
        if subscription:
            subscription.is_active = False
            await self.session.commit()

    async def is_active(self, user_id: int) -> bool:
        subscription = await self.get_by_user_id(user_id)
        if not subscription:
            return False
        if subscription.expires_at < datetime.now():
            await self.deactivate(user_id)
            return False
        return subscription.is_active

    async def get_active_count(self) -> int:
        result = await self.session.execute(
            select(Subscription).where(
                Subscription.is_active.is_(True),
                Subscription.expires_at > datetime.now(),
            )
        )
        return len(result.scalars().all())
