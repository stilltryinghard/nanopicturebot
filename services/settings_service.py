from __future__ import annotations
import json
import redis.asyncio as aioredis
from core.config import settings


class BotSettings:
    def __init__(self):
        self.redis = aioredis.from_url(settings.REDIS_URL)

    async def get_token_packages(self) -> list[dict]:
        data = await self.redis.get("settings:token_packages")
        if data:
            return json.loads(data)
        return [
            {"tokens": 100, "amount": 99},
            {"tokens": 300, "amount": 249},
            {"tokens": 700, "amount": 499},
            {"tokens": 1500, "amount": 999},
        ]

    async def set_token_packages(self, packages: list[dict]) -> None:
        await self.redis.set("settings:token_packages", json.dumps(packages))

    async def get_subscription_plans(self) -> list[dict]:
        data = await self.redis.get("settings:subscription_plans")
        if data:
            return json.loads(data)
        return [
            {"plan": "basic", "amount": 299, "label": "🥉 Базовый"},
            {"plan": "standard", "amount": 599, "label": "🥈 Стандарт"},
            {"plan": "pro", "amount": 999, "label": "🥇 Про"},
        ]

    async def set_subscription_plans(self, plans: list[dict]) -> None:
        await self.redis.set("settings:subscription_plans", json.dumps(plans))

    async def get_generation_costs(self) -> dict:
        data = await self.redis.get("settings:generation_costs")
        if data:
            return json.loads(data)
        return {
            "2K": settings.TOKENS_2K,
            "4K": settings.TOKENS_4K,
        }

    async def set_generation_costs(self, costs: dict) -> None:
        await self.redis.set("settings:generation_costs", json.dumps(costs))


bot_settings = BotSettings()
