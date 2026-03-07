from __future__ import annotations
import pytest
import fakeredis.aioredis


@pytest.fixture
def fake_redis():
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
def settings_svc(fake_redis):
    from services.settings_service import BotSettings

    svc = BotSettings.__new__(BotSettings)
    svc.redis = fake_redis
    return svc


class TestBotSettings:
    async def test_get_token_packages_default(self, settings_svc):
        packages = await settings_svc.get_token_packages()
        assert len(packages) == 4
        assert packages[0]["tokens"] == 100
        assert packages[0]["amount"] == 99

    async def test_set_and_get_token_packages(self, settings_svc):
        new_packages = [
            {"tokens": 50, "amount": 49},
            {"tokens": 200, "amount": 149},
        ]
        await settings_svc.set_token_packages(new_packages)
        result = await settings_svc.get_token_packages()
        assert result == new_packages

    async def test_get_subscription_plans_default(self, settings_svc):
        plans = await settings_svc.get_subscription_plans()
        assert len(plans) == 3
        plans_by_name = {p["plan"]: p for p in plans}
        assert "basic" in plans_by_name
        assert "standard" in plans_by_name
        assert "pro" in plans_by_name

    async def test_set_and_get_subscription_plans(self, settings_svc):
        new_plans = [{"plan": "ultra", "amount": 1999, "label": "Ultra"}]
        await settings_svc.set_subscription_plans(new_plans)
        result = await settings_svc.get_subscription_plans()
        assert result == new_plans

    async def test_get_generation_costs_default(self, settings_svc):
        costs = await settings_svc.get_generation_costs()
        assert "2K" in costs
        assert "4K" in costs
        assert costs["2K"] == 10
        assert costs["4K"] == 20

    async def test_set_and_get_generation_costs(self, settings_svc):
        await settings_svc.set_generation_costs({"2K": 5, "4K": 15})
        costs = await settings_svc.get_generation_costs()
        assert costs["2K"] == 5
        assert costs["4K"] == 15

    async def test_overwrite_packages(self, settings_svc):
        await settings_svc.set_token_packages([{"tokens": 100, "amount": 99}])
        await settings_svc.set_token_packages([{"tokens": 200, "amount": 199}])
        result = await settings_svc.get_token_packages()
        assert len(result) == 1
        assert result[0]["tokens"] == 200
