from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.models.generation import Generation


class GenerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        model: str,
        prompt: str,
        quality: str,
        count: int,
        tokens_spent: int,
        preference: str | None = None,
    ) -> Generation:
        generation = Generation(
            user_id=user_id,
            model=model,
            prompt=prompt,
            preference=preference,
            quality=quality,
            count=count,
            tokens_spent=tokens_spent,
            status="pending",
        )
        self.session.add(generation)
        await self.session.commit()
        await self.session.refresh(generation)
        return generation

    async def update_status(self, generation_id: int, status: str) -> None:
        generation = await self.get_by_id(generation_id)
        if generation:
            generation.status = status
            await self.session.commit()

    async def get_by_id(self, generation_id: int) -> Generation | None:
        result = await self.session.execute(
            select(Generation).where(Generation.id == generation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int) -> list[Generation]:
        result = await self.session.execute(
            select(Generation)
            .where(Generation.user_id == user_id)
            .order_by(Generation.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_model(self) -> dict[str, int]:
        result = await self.session.execute(
            select(Generation.model, func.count(Generation.id)).group_by(
                Generation.model
            )
        )
        return {model: count for model, count in result.all()}
