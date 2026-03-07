from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.referral import Referral


class ReferralRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, referrer_id: int, referred_id: int) -> Referral:
        referral = Referral(
            referrer_id=referrer_id,
            referred_id=referred_id,
        )
        self.session.add(referral)
        await self.session.commit()
        await self.session.refresh(referral)
        return referral

    async def get_by_referrer(self, referrer_id: int) -> list[Referral]:
        result = await self.session.execute(
            select(Referral).where(Referral.referrer_id == referrer_id)
        )
        return list(result.scalars().all())

    async def get_by_referred(self, referred_id: int) -> Referral | None:
        result = await self.session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        return result.scalar_one_or_none()
