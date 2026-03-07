from __future__ import annotations
import json
import pytest
from aioresponses import aioresponses

from services.ai.base import GenerationRequest, GenerationResult
from services.ai.nano_banana import NanoBananaService
from services.ai.seedream import SeedreamService
from services.ai.midjourney import MidjourneyService


FAKE_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


# ─── NanoBanana ───────────────────────────────────────────────────────────────


class TestNanoBananaService:
    def test_get_token_cost_2k(self):
        svc = NanoBananaService()
        assert svc.get_token_cost("2K", 1) == 10
        assert svc.get_token_cost("2K", 3) == 30

    def test_get_token_cost_4k(self):
        svc = NanoBananaService()
        assert svc.get_token_cost("4K", 1) == 20
        assert svc.get_token_cost("4K", 4) == 80

    async def test_generate_single(self):
        svc = NanoBananaService()
        request = GenerationRequest(prompt="a cat", quality="2K", count=1)

        with aioresponses() as m:
            m.post(
                NanoBananaService.BASE_URL,
                payload={
                    "code": 200,
                    "data": {"outputs": ["https://img.example.com/1.png"]},
                },
            )
            m.get("https://img.example.com/1.png", body=FAKE_IMAGE)

            result = await svc.generate(request)

        assert isinstance(result, GenerationResult)
        assert result.model == "nano_banana"
        assert len(result.images) == 1
        assert result.images[0] == FAKE_IMAGE

    async def test_generate_multiple(self):
        svc = NanoBananaService()
        request = GenerationRequest(prompt="a dog", quality="4K", count=3)

        with aioresponses() as m:
            for i in range(3):
                m.post(
                    NanoBananaService.BASE_URL,
                    payload={
                        "code": 200,
                        "data": {"outputs": [f"https://img.example.com/{i}.png"]},
                    },
                )
                m.get(f"https://img.example.com/{i}.png", body=FAKE_IMAGE)

            result = await svc.generate(request)

        assert len(result.images) == 3

    async def test_generate_with_preference(self):
        svc = NanoBananaService()
        request = GenerationRequest(
            prompt="a cat", quality="2K", count=1, preference="cinematic"
        )

        with aioresponses() as m:
            m.post(
                NanoBananaService.BASE_URL,
                payload={
                    "code": 200,
                    "data": {"outputs": ["https://img.example.com/1.png"]},
                },
            )
            m.get("https://img.example.com/1.png", body=FAKE_IMAGE)
            result = await svc.generate(request)

        assert len(result.images) == 1

    async def test_generate_api_error(self):
        svc = NanoBananaService()
        request = GenerationRequest(prompt="a cat", quality="2K", count=1)

        with aioresponses() as m:
            m.post(
                NanoBananaService.BASE_URL,
                payload={"code": 400, "message": "Bad request"},
            )

            with pytest.raises(Exception, match="NanoBanana error"):
                await svc.generate(request)


# ─── Seedream ─────────────────────────────────────────────────────────────────


class TestSeedreamService:
    def test_get_token_cost_2k(self):
        svc = SeedreamService()
        assert svc.get_token_cost("2K", 2) == 20

    def test_get_token_cost_4k(self):
        svc = SeedreamService()
        assert svc.get_token_cost("4K", 2) == 40

    async def test_generate_2k_uses_correct_size(self):
        svc = SeedreamService()
        request = GenerationRequest(prompt="sky", quality="2K", count=1)

        with aioresponses() as m:
            m.post(
                SeedreamService.BASE_URL,
                payload={
                    "code": 200,
                    "data": {"outputs": ["https://img.example.com/s.png"]},
                },
            )
            m.get("https://img.example.com/s.png", body=FAKE_IMAGE)
            result = await svc.generate(request)

        assert result.model == "seedream"
        assert len(result.images) == 1

    async def test_generate_api_error(self):
        svc = SeedreamService()
        request = GenerationRequest(prompt="sky", quality="2K", count=1)

        with aioresponses() as m:
            m.post(
                SeedreamService.BASE_URL,
                payload={"code": 500, "message": "Server error"},
            )

            with pytest.raises(Exception, match="Seedream error"):
                await svc.generate(request)


# ─── Midjourney ───────────────────────────────────────────────────────────────

POLL_URL = "https://api.midapi.ai/api/v1/mj/record-info"
GENERATE_URL = "https://api.midapi.ai/api/v1/mj/generate"


class TestMidjourneyService:
    def test_get_token_cost_2k(self):
        svc = MidjourneyService()
        assert svc.get_token_cost("2K", 1) == 10
        assert svc.get_token_cost("2K", 4) == 40

    def test_get_token_cost_4k(self):
        svc = MidjourneyService()
        assert svc.get_token_cost("4K", 2) == 40

    async def test_generate_success(self):
        svc = MidjourneyService()
        request = GenerationRequest(prompt="a cat", quality="2K", count=1)

        result_info = json.dumps(
            {"resultUrls": [{"resultUrl": "https://img.example.com/mj1.jpg"}]}
        )

        with aioresponses() as m:
            m.post(GENERATE_URL, payload={"code": 200, "data": {"taskId": "task_abc"}})
            m.get(
                f"{POLL_URL}?taskId=task_abc",
                payload={
                    "code": 200,
                    "data": {"successFlag": 1, "resultInfoJson": result_info},
                },
            )
            m.get("https://img.example.com/mj1.jpg", body=FAKE_IMAGE)

            result = await svc.generate(request)

        assert result.model == "midjourney"
        assert len(result.images) == 1
        assert result.images[0] == FAKE_IMAGE

    async def test_generate_respects_count(self):
        """Возвращает только запрошенное количество из 4 доступных"""
        svc = MidjourneyService()
        request = GenerationRequest(prompt="a cat", quality="2K", count=2)

        result_info = json.dumps(
            {
                "resultUrls": [
                    {"resultUrl": "https://img.example.com/mj1.jpg"},
                    {"resultUrl": "https://img.example.com/mj2.jpg"},
                    {"resultUrl": "https://img.example.com/mj3.jpg"},
                    {"resultUrl": "https://img.example.com/mj4.jpg"},
                ]
            }
        )

        with aioresponses() as m:
            m.post(GENERATE_URL, payload={"code": 200, "data": {"taskId": "task_xyz"}})
            m.get(
                f"{POLL_URL}?taskId=task_xyz",
                payload={
                    "code": 200,
                    "data": {"successFlag": 1, "resultInfoJson": result_info},
                },
            )
            m.get("https://img.example.com/mj1.jpg", body=FAKE_IMAGE)
            m.get("https://img.example.com/mj2.jpg", body=FAKE_IMAGE)

            result = await svc.generate(request)

        assert len(result.images) == 2

    async def test_generate_success_flag_2_raises(self):
        svc = MidjourneyService()
        request = GenerationRequest(prompt="a cat", quality="2K", count=1)

        with aioresponses() as m:
            m.post(GENERATE_URL, payload={"code": 200, "data": {"taskId": "task_fail"}})
            m.get(
                f"{POLL_URL}?taskId=task_fail",
                payload={
                    "code": 200,
                    "data": {
                        "successFlag": 2,
                        "errorMessage": "Generation failed",
                    },
                },
            )
            with pytest.raises(Exception, match="Midjourney task failed"):
                await svc.generate(request)

    async def test_generate_success_flag_3_raises(self):
        """successFlag=3 тоже должен вызывать ошибку (не зависать)"""
        svc = MidjourneyService()
        request = GenerationRequest(prompt="a cat", quality="2K", count=1)

        with aioresponses() as m:
            m.post(
                GENERATE_URL, payload={"code": 200, "data": {"taskId": "task_fail3"}}
            )
            m.get(
                f"{POLL_URL}?taskId=task_fail3",
                payload={
                    "code": 200,
                    "data": {
                        "successFlag": 3,
                        "errorMessage": "No response from MidJourney",
                    },
                },
            )
            with pytest.raises(Exception, match="Midjourney task failed"):
                await svc.generate(request)

    async def test_generate_submit_error(self):
        svc = MidjourneyService()
        request = GenerationRequest(prompt="a cat", quality="2K", count=1)

        with aioresponses() as m:
            m.post(GENERATE_URL, payload={"code": 400, "msg": "Invalid key"})

            with pytest.raises(Exception, match="Midjourney submit error"):
                await svc.generate(request)

    async def test_url_extraction_from_objects(self):
        """resultUrls — список объектов {'resultUrl': '...'}, не строки"""
        svc = MidjourneyService()
        request = GenerationRequest(prompt="test", quality="2K", count=1)

        result_info = json.dumps(
            {"resultUrls": [{"resultUrl": "https://img.example.com/obj.jpg"}]}
        )

        with aioresponses() as m:
            m.post(GENERATE_URL, payload={"code": 200, "data": {"taskId": "t1"}})
            m.get(
                f"{POLL_URL}?taskId=t1",
                payload={
                    "code": 200,
                    "data": {"successFlag": 1, "resultInfoJson": result_info},
                },
            )
            m.get("https://img.example.com/obj.jpg", body=FAKE_IMAGE)
            result = await svc.generate(request)

        assert len(result.images) == 1

    async def test_generate_with_4k_quality(self):
        """4K добавляет --q 2 к промту"""
        svc = MidjourneyService()
        request = GenerationRequest(prompt="a cat", quality="4K", count=1)

        result_info = json.dumps(
            {"resultUrls": [{"resultUrl": "https://img.example.com/4k.jpg"}]}
        )

        with aioresponses() as m:
            m.post(GENERATE_URL, payload={"code": 200, "data": {"taskId": "t4k"}})
            m.get(
                f"{POLL_URL}?taskId=t4k",
                payload={
                    "code": 200,
                    "data": {"successFlag": 1, "resultInfoJson": result_info},
                },
            )
            m.get("https://img.example.com/4k.jpg", body=FAKE_IMAGE)
            result = await svc.generate(request)

        assert result.model == "midjourney"
